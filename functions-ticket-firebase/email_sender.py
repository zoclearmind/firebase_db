# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║   CONTENU DE L'EMAIL                                         ║
# ║                                                              ║
# ║   C'est ici que tu modifies les textes, l'ordre des blocs,  ║
# ║   et les données affichées dans l'email de confirmation.     ║
# ║                                                              ║
# ╚══════════════════════════════════════════════════════════════╝

import base64
import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from templates.components import (
    _hero,
    _body_open,
    _body_close,
    _info_card,
    _info_row,
    _qr_block,
    _security_card,
    _build_html,
)


def send_ticket_email_invited(
    email: str,
    destinateur_first_name: str,
    destinateur_last_name: str,
    badge_owner_first_name: str,
    badge_owner_last_name: str,
    event_title: str,
    event_start: str,
    event_location: str,
    qr_base64: str,
    registration_id: str,
    qr_token: str,
):
    """
    Email envoyé au commanditaire (emailDestinateur) pour un billet
    appartenant à une autre personne (userPropretaireBadge...).

    - greeting         → Bonjour {destinateur}
    - Participant card → badge_owner (la personne qui utilisera le billet)
    """
    SMTP_HOST     = os.environ.get("SMTP_HOST", "smtp.zeptomail.com")
    SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER     = os.environ.get("SMTP_USER", "noreply@athena-event.com")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

    if not all([SMTP_USER, SMTP_PASSWORD]):
        logging.error("Variables SMTP manquantes")
        raise ValueError("Configuration SMTP incomplète")

    badge_owner_full = f"{badge_owner_first_name} {badge_owner_last_name}"

    # ── Infos inscription ──
    info_rows = (
        _info_row("&#128100;", "Participant",  badge_owner_full)
        + _info_row("&#127881;", "Événement",  f"<strong>{event_title}</strong>")
        + _info_row("&#128197;", "Date",        event_start)
        + _info_row("&#128205;", "Lieu",        event_location)
    )

    # ── Consignes de sécurité ──
    security_items = [
        f"Ce billet est au nom de <strong>{badge_owner_full}</strong>",
        "<strong>Ne partagez pas ce QR code</strong> en dehors de la personne concernée",
        "Ce code est <strong>strictement personnel</strong> et identifie le participant de manière unique",
        "Toute personne en possession de ce code peut accéder à l'événement à sa place",
        "En cas de perte ou de vol, <strong>contactez-nous immédiatement</strong>",
    ]

    # ── Assemblage des blocs visuels ──
    rows = (
        _hero(
            title="Confirmation d'inscription",
            subtitle=f"Billet pour {event_title}",
            email_type_label="Billet événement",
        )
        + _body_open(
            greeting=f"Bonjour {destinateur_first_name} {destinateur_last_name},",
            intro=(
                f"Nous avons le plaisir de vous confirmer l'inscription de "
                f"<strong>{badge_owner_full}</strong>. "
                "Veuillez lui transmettre cet email — "
                "il contient son code d'accès personnel à l'événement."
            )
        )
        + _info_card(info_rows, label="Détails de l'inscription")
        + _qr_block(qr_token)
        + _security_card(security_items)
        + f"""
        <p style="margin:20px 0 0 0;font-family:Arial,sans-serif;font-size:14px;
                   color:#57534e;line-height:1.6;">
          Nous vous remercions pour votre confiance et restons &#224; votre disposition
          pour toute question.
        </p>
        """
        + _body_close()
    )

    html_content = _build_html(
        rows,
        preheader=f"Billet de {badge_owner_full} confirmé — {event_title}"
    )

    text_content = f"""Athena Event - Confirmation d'inscription

Bonjour {destinateur_first_name} {destinateur_last_name},

Nous avons le plaisir de vous confirmer l'inscription de {badge_owner_full}
à l'événement suivant.

DÉTAILS DE L'INSCRIPTION

Participant : {badge_owner_full}
Événement   : {event_title}
Date        : {event_start}
Lieu        : {event_location}

{qr_token}

CONSIGNES DE SÉCURITÉ :
- Ce billet est au nom de {badge_owner_full}
- Ne partagez pas ce QR code en dehors de la personne concernée
- Ce code est strictement personnel et identifie le participant de manière unique
- Toute personne en possession de ce code peut accéder à l'événement à sa place
- En cas de perte ou de vol, contactez-nous immédiatement

Cordialement,
L'équipe Athena Event

---
📞 +261 38 32 046 13
📧 contact@clearmind-analytics.com
🌐 www.athena-event.com

© {datetime.now().year} Athena Event by Clearmind Analytics
Antananarivo, Madagascar
"""

    msg             = MIMEMultipart('related')
    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)

    msg_alternative.attach(MIMEText(text_content, 'plain', 'utf-8'))
    msg_alternative.attach(MIMEText(html_content, 'html',  'utf-8'))

    qr_bytes = base64.b64decode(qr_base64)
    qr_image = MIMEBase('image', 'png')
    qr_image.set_payload(qr_bytes)
    encoders.encode_base64(qr_image)
    qr_image.add_header('Content-ID', '<qrcode>')
    qr_image.add_header('Content-Disposition', 'inline', filename='qrcode.png')
    msg.attach(qr_image)

    msg['Subject']    = f"Billet de {badge_owner_full} — {event_title}"
    msg['From']       = f"Athena Event <{SMTP_USER}>"
    msg['To']         = email
    msg['Reply-To']   = SMTP_USER
    msg['Message-ID'] = f"<{registration_id}@athena-event.com>"
    msg['X-Mailer']   = "Athena Event Platform"

    try:
        with smtplib.SMTP(SMTP_HOST, 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logging.info(f"✅ Email billet invité envoyé à {email} (billet: {badge_owner_full})")
    except Exception as e:
        logging.error(f"❌ Erreur envoi email : {e}")
        raise


def send_ticket_email_with_qr(
    email: str,
    first_name: str,
    last_name: str,
    event_title: str,
    event_start: str,
    event_location: str,
    qr_base64: str,
    registration_id: str,
    qr_token: str
):
    SMTP_HOST     = os.environ.get("SMTP_HOST", "smtp.zeptomail.com")
    SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER     = os.environ.get("SMTP_USER", "noreply@athena-event.com")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

    if not all([SMTP_USER, SMTP_PASSWORD]):
        logging.error("Variables SMTP manquantes")
        raise ValueError("Configuration SMTP incomplète")

    # ── Infos inscription ──
    info_rows = (
        _info_row("&#128100;", "Participant", f"{first_name} {last_name}")
        + _info_row("&#128231;", "Email",      email)
        + _info_row("&#127881;", "Événement",  f"<strong>{event_title}</strong>")
        + _info_row("&#128197;", "Date",       event_start)
        + _info_row("&#128205;", "Lieu",       event_location)
    )

    # ── Consignes de sécurité ──
    security_items = [
        "<strong>Ne partagez jamais ce QR code</strong> avec qui que ce soit",
        "Ce code est <strong>strictement personnel</strong> et vous identifie de manière unique",
        "Toute personne en possession de ce code peut accéder à l'événement à votre place",
        "Ne publiez pas ce billet sur les réseaux sociaux",
        "En cas de perte ou de vol, <strong>contactez-nous immédiatement</strong>",
    ]

    # ── Assemblage des blocs visuels ──
    rows = (
        _hero(
            title="Confirmation d'inscription",
            subtitle=f"Votre billet pour {event_title}",
            email_type_label="Billet événement",
        )
        + _body_open(
            greeting=f"Bonjour {first_name} {last_name},",
            intro=(
                "Nous avons le plaisir de confirmer votre inscription. "
                "Veuillez conserver cet email précieusement — "
                "il contient votre code d'accès personnel à l'événement."
            )
        )
        + _info_card(info_rows, label="Détails de votre inscription")
        + _qr_block(qr_token)
        + _security_card(security_items)
        + """
        <p style="margin:20px 0 0 0;font-family:Arial,sans-serif;font-size:14px;
                   color:#57534e;line-height:1.6;">
          Nous vous remercions pour votre confiance et restons &#224; votre disposition
          pour toute question.
        </p>
        """
        + _body_close()
    )

    html_content = _build_html(
        rows,
        preheader=f"Votre billet est confirmé — {event_title}"
    )

    text_content = f"""Athena Event - Confirmation d'inscription

Bonjour {first_name} {last_name},

Nous avons le plaisir de confirmer votre inscription à l'événement suivant.

DÉTAILS DE VOTRE INSCRIPTION

Participant : {first_name} {last_name}
Email       : {email}
Événement   : {event_title}
Date        : {event_start}
Lieu        : {event_location}

{qr_token}

CONSIGNES DE SÉCURITÉ :
- Ne partagez jamais ce QR code avec qui que ce soit
- Ce code est strictement personnel et vous identifie de manière unique
- Toute personne en possession de ce code peut accéder à l'événement à votre place
- Ne publiez pas ce billet sur les réseaux sociaux
- En cas de perte ou de vol, contactez-nous immédiatement

Cordialement,
L'équipe Athena Event

---
📞 +261 38 32 046 13
📧 contact@clearmind-analytics.com
🌐 www.athena-event.com

© {datetime.now().year} Athena Event by Clearmind Analytics
Antananarivo, Madagascar
"""

    # ── Construction MIME — structure : related > alternative + image CID ──
    # NOTE TECHNIQUE : MIMEMultipart('related') est nécessaire pour embarquer
    # le QR code inline via Content-ID sans qu'il apparaisse comme pièce jointe.
    msg             = MIMEMultipart('related')
    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)

    msg_alternative.attach(MIMEText(text_content, 'plain', 'utf-8'))
    msg_alternative.attach(MIMEText(html_content, 'html',  'utf-8'))

    qr_bytes = base64.b64decode(qr_base64)
    qr_image = MIMEBase('image', 'png')
    qr_image.set_payload(qr_bytes)
    encoders.encode_base64(qr_image)
    qr_image.add_header('Content-ID', '<qrcode>')
    qr_image.add_header('Content-Disposition', 'inline', filename='qrcode.png')
    msg.attach(qr_image)

    msg['Subject']    = f"Confirmation d'inscription — {event_title}"
    msg['From']       = f"Athena Event <{SMTP_USER}>"
    msg['To']         = email
    msg['Reply-To']   = SMTP_USER
    msg['Message-ID'] = f"<{registration_id}@athena-event.com>"
    msg['X-Mailer']   = "Athena Event Platform"

    # NOTE : SMTP simple + starttls port 587
    try:
        with smtplib.SMTP(SMTP_HOST, 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logging.info(f"✅ Email billet envoyé à {email}")
    except Exception as e:
        logging.error(f"❌ Erreur envoi email : {e}")
        raise
