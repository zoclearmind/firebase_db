import base64
import json
import logging
from io import BytesIO

import qrcode
from firebase_admin import initialize_app
from firebase_functions import pubsub_fn

from storage import storage_client  # noqa: F401 — déclenche la config de l'émulateur
from pdf_generator import generate_and_upload_badge
from email_sender import send_ticket_email_with_qr, send_ticket_email_invited

# Initialiser Firebase Admin
initialize_app()


# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║   ZONE LOGIQUE — NE PAS MODIFIER SAUF DEV CONFIRMÉ          ║
# ║                                                              ║
# ║   Contient : écoute Pub/Sub Firebase, validation,           ║
# ║              génération PDF, upload GCS, SMTP.              ║
# ║   Modifier ici peut casser la livraison des emails          ║
# ║   ou la génération des badges PDF.                          ║
# ║                                                              ║
# ╚══════════════════════════════════════════════════════════════╝


# ──────────────────────────────────────────────────────────────
# POINT D'ENTRÉE FIREBASE FUNCTION
# ──────────────────────────────────────────────────────────────

@pubsub_fn.on_message_published(topic="prod-email-notifications")
def send_event_ticket(event: pubsub_fn.CloudEvent[pubsub_fn.MessagePublishedData]) -> None:

    logging.info("=" * 80)
    logging.info("🎫 MESSAGE REÇU - event-registration-confirmed")
    logging.info("=" * 80)

    try:
        data = event.data.message.json
        logging.info(f"Contenu: {json.dumps(data, indent=2)}")
    except (ValueError, AttributeError) as e:
        logging.error(f"❌ Message invalide: {e}")
        return

    if "type" not in data:
        logging.error("❌ Champ 'type' manquant")
        return

    # ✅ ACCEPTER LES TROIS TYPES
    ACCEPTED_TYPES = [
        "EVENT_REGISTRATION_CONFIRMED",
        "RESEND_REGISTRATION_CONFIRMED",
        "RESEND_REGISTRATION_CONFIRMED_INVITED",
    ]
    if data["type"] not in ACCEPTED_TYPES:
        logging.warning(f"⚠ Type incorrect: {data['type']}")
        return

    # ── Dispatch : billet invité ──────────────────────────────────
    if data["type"] == "RESEND_REGISTRATION_CONFIRMED_INVITED":
        invited_required = [
            "registrationId", "emailDestinateur",
            "userDestinateurFirstName", "userDestinateurLastName",
            "userPropretaireBadgeLastName", "userPropretaireBadgeFistName",
            "eventTitle", "eventStartDate", "eventLocation", "qrCodeToken",
        ]
        missing_invited = [f for f in invited_required if f not in data]
        if missing_invited:
            logging.error(f"❌ Champs manquants (invited): {missing_invited}")
            return

        qr_token = data["qrCodeToken"]

        try:
            qr_img = qrcode.make(qr_token, box_size=10, border=2)
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format="PNG")
            qr_buffer.seek(0)
            qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

            logging.info(f"🎫 Billet invité → {data['emailDestinateur']} (badge: {data['userPropretaireBadgeFistName']} {data['userPropretaireBadgeLastName']})")

            send_ticket_email_invited(
                email=data["emailDestinateur"],
                destinateur_first_name=data["userDestinateurFirstName"],
                destinateur_last_name=data["userDestinateurLastName"],
                badge_owner_first_name=data["userPropretaireBadgeFistName"],
                badge_owner_last_name=data["userPropretaireBadgeLastName"],
                event_title=data["eventTitle"],
                event_start=data["eventStartDate"],
                event_location=data["eventLocation"],
                qr_base64=qr_base64,
                registration_id=data["registrationId"],
                qr_token=qr_token,
            )
        except Exception as e:
            logging.error(f"❌ Échec traitement billet invité: {e}")
        return

    # ── Extraction (types classiques) ────────────────────────────
    classic_required = [
        "registrationId", "userId", "eventId",
        "userEmail", "userFirstName", "userLastName",
        "eventTitle", "eventStartDate", "eventLocation", "qrCodeToken",
    ]
    missing_classic = [f for f in classic_required if f not in data]
    if missing_classic:
        logging.error(f"❌ Champs manquants: {missing_classic}")
        return

    registration_id = data["registrationId"]
    user_email      = data["userEmail"]
    user_first_name = data["userFirstName"]
    user_last_name  = data["userLastName"]
    event_title     = data["eventTitle"]
    event_start     = data["eventStartDate"]
    event_location  = data["eventLocation"]
    qr_token        = data["qrCodeToken"]
    company_name    = data.get("companyName", "N/A")
    user_role       = data.get("userRole", "Participant")

    logging.info(f"🎫 Billet pour {user_email} - {event_title}")

    try:
        # ── Génération QR code ────────────────────────────────────
        qr_img = qrcode.make(qr_token, box_size=10, border=2)
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')
        qr_buffer.seek(0)

        # ── EVENT_REGISTRATION_CONFIRMED : génère le badge ZPL ───
        if data["type"] == "EVENT_REGISTRATION_CONFIRMED":
            logging.info("📄 Premier envoi → Génération badge ZPL")
            generate_and_upload_badge(
                qr_token=qr_token,
                user_first_name=user_first_name,
                user_last_name=user_last_name,
                company_name=company_name,
                user_role=user_role,
            )

        # ── RESEND_REGISTRATION_CONFIRMED : skip badge, email seul 
        elif data["type"] == "RESEND_REGISTRATION_CONFIRMED":
            logging.info("🔄 Renvoi détecté → Skip génération badge")

        # ── Envoi email (commun aux deux types classiques) ────────
        send_ticket_email_with_qr(
            user_email, user_first_name, user_last_name,
            event_title, event_start, event_location,
            qr_base64, registration_id, qr_token
        )

    except Exception as e:
        logging.error(f"❌ Échec traitement billet ({data['type']}): {e}")