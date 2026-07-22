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
    event_image_url: str = None,
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
        _info_row("", "Participant",  badge_owner_full)
        + _info_row("", "Événement",  f"<strong>{event_title}</strong>")
        + _info_row("", "Date",        event_start)
        + _info_row("", "Lieu",        event_location)
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
            hero_image_url=event_image_url or "",
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
                   color:#3b4453;line-height:1.6;">
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
+261 38 32 046 13
sales@athena-event.com
www.athena-event.com

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
        logging.info(f"Email billet invité envoyé à {email} (billet: {badge_owner_full})")
    except Exception as e:
        logging.error(f"Erreur envoi email : {e}")
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
    qr_token: str,
    event_image_url: str = None,
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
        _info_row("", "Participant", f"{first_name} {last_name}")
        + _info_row("", "Email",      email)
        + _info_row("", "Événement",  f"<strong>{event_title}</strong>")
        + _info_row("", "Date",       event_start)
        + _info_row("", "Lieu",       event_location)
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
            hero_image_url=event_image_url or "",
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
                   color:#3b4453;line-height:1.6;">
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
+261 38 32 046 13
sales@athena-event.com
www.athena-event.com

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
        logging.info(f"Email billet envoyé à {email}")
    except Exception as e:
        logging.error(f"Erreur envoi email : {e}")
        raise


def send_ticket_email_multiticket(
    email: str,
    first_name: str,
    last_name: str,
    event_title: str,
    event_start: str,
    event_location: str,
    qr_base64_list: list,
    qr_tokens: list,
    registration_id: str,
    event_image_url: str = None,
):
    """
    Email de confirmation groupé : plusieurs billets (donc plusieurs QR codes,
    un par personne) envoyés dans un seul email à un même destinataire.
    Un bloc QR distinct est affiché par billet, chacun avec son propre
    Content-ID (qrcode1, qrcode2, ...) pour éviter tout conflit d'image inline.
    """
    SMTP_HOST     = os.environ.get("SMTP_HOST", "smtp.zeptomail.com")
    SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER     = os.environ.get("SMTP_USER", "noreply@athena-event.com")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

    if not all([SMTP_USER, SMTP_PASSWORD]):
        logging.error("Variables SMTP manquantes")
        raise ValueError("Configuration SMTP incomplète")

    ticket_count = len(qr_tokens)

    # ── Infos inscription ──
    info_rows = (
        _info_row("", "Participant",       f"{first_name} {last_name}")
        + _info_row("", "Email",           email)
        + _info_row("", "Événement",       f"<strong>{event_title}</strong>")
        + _info_row("", "Date",            event_start)
        + _info_row("", "Lieu",            event_location)
        + _info_row("", "Nombre de billets", str(ticket_count))
    )

    # ── Consignes de sécurité ──
    security_items = [
        f"Vous disposez de <strong>{ticket_count} billets</strong>, chacun avec son propre QR code",
        "<strong>Ne partagez jamais un QR code</strong> avec qui que ce soit en dehors de son destinataire",
        "Chaque code est <strong>strictement personnel</strong> et identifie un participant de manière unique",
        "Toute personne en possession d'un code peut accéder à l'événement à la place du participant concerné",
        "Ne publiez pas ces billets sur les réseaux sociaux",
        "En cas de perte ou de vol, <strong>contactez-nous immédiatement</strong>",
    ]

    # ── Un bloc QR par billet, chacun avec un Content-ID unique ──
    qr_blocks = ""
    for i, token in enumerate(qr_tokens, start=1):
        qr_blocks += _qr_block(
            token,
            cid=f"qrcode{i}",
            ticket_label=f"Billet {i} / {ticket_count}",
        )

    # ── Assemblage des blocs visuels ──
    rows = (
        _hero(
            title="Confirmation d'inscription",
            subtitle=f"Vos {ticket_count} billets pour {event_title}",
            email_type_label="Billets événement",
            hero_image_url=event_image_url or "",
        )
        + _body_open(
            greeting=f"Bonjour {first_name} {last_name},",
            intro=(
                f"Nous avons le plaisir de confirmer votre inscription pour "
                f"<strong>{ticket_count} billets</strong>. Chaque billet ci-dessous "
                "dispose de son propre code d'accès — merci de conserver cet email "
                "précieusement et de présenter séparément chaque code à l'entrée "
                "de l'événement."
            )
        )
        + _info_card(info_rows, label="Détails de l'inscription")
        + qr_blocks
        + _security_card(security_items)
        + """
        <p style="margin:20px 0 0 0;font-family:Arial,sans-serif;font-size:14px;
                   color:#3b4453;line-height:1.6;">
          Nous vous remercions pour votre confiance et restons &#224; votre disposition
          pour toute question.
        </p>
        """
        + _body_close()
    )

    html_content = _build_html(
        rows,
        preheader=f"Vos {ticket_count} billets sont confirmés — {event_title}"
    )

    tokens_text = "\n".join(
        f"Billet {i}/{ticket_count} — code : {token}"
        for i, token in enumerate(qr_tokens, start=1)
    )

    text_content = f"""Athena Event - Confirmation d'inscription

Bonjour {first_name} {last_name},

Nous avons le plaisir de confirmer votre inscription pour {ticket_count} billets
à l'événement suivant.

DÉTAILS DE L'INSCRIPTION

Participant      : {first_name} {last_name}
Email            : {email}
Événement        : {event_title}
Date             : {event_start}
Lieu             : {event_location}
Nombre de billets: {ticket_count}

VOS BILLETS
{tokens_text}

CONSIGNES DE SÉCURITÉ :
- Vous disposez de {ticket_count} billets, chacun avec son propre QR code
- Ne partagez jamais un QR code avec qui que ce soit en dehors de son destinataire
- Chaque code est strictement personnel et identifie un participant de manière unique
- Toute personne en possession d'un code peut accéder à l'événement à la place du participant concerné
- Ne publiez pas ces billets sur les réseaux sociaux
- En cas de perte ou de vol, contactez-nous immédiatement

Cordialement,
L'équipe Athena Event

---
+261 38 32 046 13
sales@athena-event.com
www.athena-event.com

© {datetime.now().year} Athena Event by Clearmind Analytics
Antananarivo, Madagascar
"""

    # ── Construction MIME — structure : related > alternative + N images CID ──
    msg             = MIMEMultipart('related')
    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)

    msg_alternative.attach(MIMEText(text_content, 'plain', 'utf-8'))
    msg_alternative.attach(MIMEText(html_content, 'html',  'utf-8'))

    for i, qr_base64 in enumerate(qr_base64_list, start=1):
        qr_bytes = base64.b64decode(qr_base64)
        qr_image = MIMEBase('image', 'png')
        qr_image.set_payload(qr_bytes)
        encoders.encode_base64(qr_image)
        qr_image.add_header('Content-ID', f'<qrcode{i}>')
        qr_image.add_header('Content-Disposition', 'inline', filename=f'qrcode{i}.png')
        msg.attach(qr_image)

    msg['Subject']    = f"Confirmation de vos {ticket_count} billets — {event_title}"
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
        logging.info(f"Email multi-billets ({ticket_count}) envoyé à {email}")
    except Exception as e:
        logging.error(f"Erreur envoi email multi-billets : {e}")
        raise
