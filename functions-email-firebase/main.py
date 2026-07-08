import logging

from firebase_admin import initialize_app
from firebase_functions import pubsub_fn

from email_senders import (
    send_activation_code,
    send_hostess_activation_link,
    send_activation_link_organizer,
    send_reset_password_email,
    send_event_awaiting_approval,
    send_event_approved,
    send_participant_invitation_known,
    send_participant_invitation_unknown,
    send_request_otp,
)

# Initialiser Firebase Admin
initialize_app()


# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║   ZONE LOGIQUE — NE PAS MODIFIER SAUF DEV CONFIRMÉ          ║
# ║                                                              ║
# ║   Contient : écoute Pub/Sub Firebase, validation,           ║
# ║              dispatch par type, SMTP.                       ║
# ║   Modifier ici peut casser la livraison des emails.         ║
# ║                                                              ║
# ╚══════════════════════════════════════════════════════════════╝


# ──────────────────────────────────────────────────────────────
# POINT D'ENTRÉE FIREBASE FUNCTION
# ──────────────────────────────────────────────────────────────

@pubsub_fn.on_message_published(topic="prod-registration-confirmed")
def process_email(event: pubsub_fn.CloudEvent[pubsub_fn.MessagePublishedData]) -> None:

    logging.info("=" * 80)
    logging.info("MESSAGE REÇU SUR PUB/SUB - prod-registration-confirmed")
    logging.info("=" * 80)

    try:
        data = event.data.message.json

        logging.info("DONNÉES BRUTES REÇUES:")
        logging.info(f"   Type: {type(data)}, Champs: {len(data)}")
        logging.info("TOUS LES CHAMPS:")
        for key, value in data.items():
            logging.info(f"   '{key}': '{value}' (type: {type(value).__name__})")
        logging.info("=" * 80)

    except (ValueError, AttributeError) as e:
        logging.error(f"Message invalide: {e}")
        return

    email_type = data.get("type")

    if not email_type:
        logging.error("Champ 'type' manquant")
        return

    logging.info(f"Type détecté: {email_type}")

    # ── Validation dynamique selon le type d'email ──
    if email_type == "ACTIVATION_CODE":
        required_fields = ["type", "firstName", "code", "expiresAt", "template"]
        email_field = data.get("email", "")

    elif email_type == "ACTIVATION_LINK":
        required_fields = ["type", "userId", "email", "firstName", "lastName", "default_password", "link"]
        email_field = data.get("email", "")
        logging.info(f"Email hôtesse: '{email_field}'")

    elif email_type == "ACTIVATION_LINK_ORGANIZER":
        required_fields = ["type", "email", "firstName", "lastName", "default_password", "company_name", "link"]
        email_field = data.get("email", "")
        logging.info(f"Email organisateur: '{email_field}'")

    elif email_type == "RESET_PASSWORD":
        required_fields = ["type", "email", "firstName", "token", "expiresAt", "template"]
        email_field = data.get("email", "")
        logging.info(f"Reset password: '{email_field}'")

    elif email_type == "EVENT_AWAITING_APPROVAL":
        email_field = data.get("adminEmail", "")
        required_fields = ["eventId", "eventTitle", "companyName", "createdAt"]

    elif email_type == "EVENT_APPROVED":
        email_field = data.get("companyEmail", "")
        required_fields = ["companyName", "eventId", "eventTitle", "eventStartDate", "eventLocation", "approvedAt"]

    elif email_type in ["PARTICIPANT_INVITATION_KNOWN", "PARTICIPANT_INVITATION_UNKNOWN"]:
        required_fields = ["type", "companyName", "eventId", "token", "url", "template"]
        email_field = data.get("email") or data.get("companyEmail") or data.get("userEmail") or ""
        logging.info(f"Email extrait: '{email_field}'")

    elif email_type == "REQUEST_OTP":
        email_field = data.get("destinataire", "")
        required_fields = ["otp"]

    else:
        logging.warning(f"Type inconnu: {email_type}")
        return

    missing = [f for f in required_fields if f not in data]
    if missing:
        logging.error(f"Champs manquants: {missing}")
        return

    # ── Dispatch selon le type ────────────────────────────────
    if email_type == "ACTIVATION_CODE":
        send_activation_code(email_field, data["firstName"], data["code"], data["expiresAt"])

    elif email_type == "ACTIVATION_LINK":
        send_hostess_activation_link(
            email_field,
            data["firstName"],
            data["lastName"],
            data["default_password"],
            data["link"],
            data["userId"]
        )

    elif email_type == "ACTIVATION_LINK_ORGANIZER":
        send_activation_link_organizer(
            email_field,
            data["firstName"],
            data["lastName"],
            data["default_password"],
            data["company_name"],
            data["link"]
        )

    elif email_type == "RESET_PASSWORD":
        send_reset_password_email(
            email_field,
            data["firstName"],
            data["token"],
            data["expiresAt"]
        )

    elif email_type == "EVENT_AWAITING_APPROVAL":
        send_event_awaiting_approval(
            email_field,
            data["eventId"],
            data["eventTitle"],
            data["companyName"],
            data["createdAt"]
        )

    elif email_type == "EVENT_APPROVED":
        send_event_approved(
            email_field,
            data["companyName"],
            data["eventId"],
            data["eventTitle"],
            data["eventStartDate"],
            data["eventLocation"],
            data["approvedAt"]
        )

    elif email_type == "PARTICIPANT_INVITATION_KNOWN":
        send_participant_invitation_known(
            email_field, data["companyName"], data["eventId"], data["token"], data["url"]
        )

    elif email_type == "PARTICIPANT_INVITATION_UNKNOWN":
        send_participant_invitation_unknown(
            email_field, data["companyName"], data["eventId"], data["token"], data["url"]
        )

    elif email_type == "REQUEST_OTP":
        send_request_otp(email_field, data["otp"], event_image_url=data.get("eventImageUrl"))
