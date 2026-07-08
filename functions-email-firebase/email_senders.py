# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║   CONTENU DES EMAILS                                         ║
# ║                                                              ║
# ║   C'est ici que tu modifies les textes, l'ordre des blocs,  ║
# ║   et les données affichées dans chaque type d'email.         ║
# ║                                                              ║
# ╚══════════════════════════════════════════════════════════════╝

import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import SMTP_USER, APP_BASE_URL
from sender import _send_email, _format_expiry
from templates.components import (
    _hero,
    _body_open,
    _body_close,
    _info_card,
    _info_row,
    _cta_button,
    _cta_secondary,
    _alert,
    _code_block,
    _steps_card,
    _build_html,
)


# ──────────────────────────────────────────────────────────────
# EMAILS D'AUTHENTIFICATION
# ──────────────────────────────────────────────────────────────

def send_activation_code(email: str, first_name: str, code: str, expires_at: str) -> None:
    expiry_date = expires_at

    rows = (
        _hero(
            title="Vérification de votre compte",
            subtitle="Utilisez le code ci-dessous pour activer votre accès",
            email_type_label="Activation de compte",
        )
        + _body_open(
            greeting=f"Bonjour {first_name},",
            intro=(
                "Merci de vous être inscrit sur <strong>Athena Event</strong>. "
                "Pour activer votre compte, saisissez le code de vérification "
                "ci-dessous dans l'application :"
            )
        )
        + _code_block(code, label="Votre code d'activation")
        + _info_card(
            _info_row("", "Expire dans", f"<strong>{expiry_date} minutes</strong>"),
            label="EXPIRATION"
        )
        + _alert(
            "<strong>Ne partagez jamais ce code.</strong> "
            "L'équipe Athena Event ne vous demandera jamais votre code "
            "par email ou par téléphone.",
            variant="warning"
        )
        + _body_close()
    )

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Code d'activation Athena Event : {code}"
    msg['From']    = f"Athena Event <{SMTP_USER}>"
    msg['To']      = email
    msg.attach(MIMEText(
        f"Bonjour {first_name},\n\n"
        f"Votre code d'activation : {code}\n"
        f"Expire le : {expiry_date}\n\n"
        "Ne partagez jamais ce code.\n\n-- Athena Event",
        'plain', 'utf-8'
    ))
    msg.attach(MIMEText(
        _build_html(rows, preheader=f"Votre code d'activation Athena Event : {code}"),
        'html', 'utf-8'
    ))

    _send_email(msg)
    logging.info(f"Email code activation envoyé à {email}")


def send_hostess_activation_link(
    email: str,
    first_name: str,
    last_name: str,
    default_password: str,
    activation_link: str,
    user_id: str,
) -> None:
    creds_rows = (
        _info_row("&#128231;", "Email", email)
        + _info_row(
            "&#128273;", "Mot de passe provisoire",
            f"<code style='background-color:#f5f0e0;padding:2px 7px;"
            f"border-radius:4px;font-family:Courier New,monospace;"
            f"font-size:13px;color:#44403c;'>{default_password}</code>"
        )
        + _info_row("&#128100;", "ID utilisateur", user_id)
    )

    rows = (
        _hero(
            title=f"Bienvenue, {first_name} !",
            subtitle="Votre compte hôtesse Athena Event a été créé",
            email_type_label="Compte hôtesse",
        )
        + _body_open(
            greeting=f"Bonjour {first_name} {last_name},",
            intro=(
                "Nous avons le plaisir de vous inviter à rejoindre notre équipe d'hôtesses "
                "pour les événements <strong>Athena Event</strong>. Votre compte est prêt "
                "— il ne vous reste qu'à l'activer."
            )
        )
        + _info_card(creds_rows, label="Vos identifiants de connexion")
        + """
        <p style="margin:0 0 4px 0;font-family:Arial,sans-serif;font-size:15px;
                   color:#57534e;line-height:1.75;">
          Cliquez sur le bouton ci-dessous pour activer votre compte
          et définir votre propre mot de passe :
        </p>
        """
        + _cta_button(activation_link, "Activer mon compte")
        + _alert(
            "<strong>Sécurité :</strong> Vous devrez changer ce mot de passe "
            "provisoire lors de votre première connexion. "
            "Ne partagez jamais vos identifiants avec qui que ce soit.",
            variant="warning"
        )
        + _body_close("Nous sommes ravis de vous compter parmi notre équipe.<br>Cordialement,")
    )

    msg = MIMEMultipart('alternative')
    msg['Subject']    = f"Bienvenue dans l'équipe Athena Event — {first_name} {last_name}"
    msg['From']       = f"Athena Event <{SMTP_USER}>"
    msg['To']         = email
    msg['Reply-To']   = SMTP_USER
    msg['Message-ID'] = f"<{user_id}@athena-event.com>"
    msg['X-Mailer']   = "Athena Event Platform"
    msg.attach(MIMEText(
        f"Athena Event — Invitation Hôtesse\n\n"
        f"Bonjour {first_name} {last_name},\n\n"
        f"Email : {email}\n"
        f"Mot de passe provisoire : {default_password}\n"
        f"ID utilisateur : {user_id}\n\n"
        f"Activer mon compte : {activation_link}\n\n"
        "Changez votre mot de passe à la première connexion.\n\n"
        "Cordialement,\nL'équipe Athena Event",
        'plain', 'utf-8'
    ))
    msg.attach(MIMEText(
        _build_html(
            rows,
            preheader=f"Bienvenue dans l'équipe Athena Event, {first_name} — activez votre compte"
        ),
        'html', 'utf-8'
    ))

    _send_email(msg)
    logging.info(f"Email hôtesse envoyé à {email}")


def send_reset_password_email(
    email: str, first_name: str, token: str, expires_at: str,
) -> None:
    expiry_date = expires_at

    rows = (
        _hero(
            title="Réinitialisation du mot de passe",
            subtitle="Utilisez le code ci-dessous pour créer un nouveau mot de passe",
            email_type_label="Sécurité du compte",
        )
        + _body_open(
            greeting=f"Bonjour {first_name},",
            intro=(
                "Nous avons reçu une demande de réinitialisation de mot de passe "
                "pour votre compte <strong>Athena Event</strong>. "
                "Saisissez le code ci-dessous dans l'application pour continuer :"
            )
        )
        + _code_block(token, label="Votre code de réinitialisation")
        + _info_card(
            _info_row("", "Expire le", f"<strong>{expiry_date}</strong>"),
            label="EXPIRATION"
        )
        + _alert(
            "<strong>Consignes de sécurité :</strong><br>"
            "Ne partagez jamais ce code. "
            "L'équipe Athena Event ne vous demandera jamais votre code par email ou téléphone. "
            "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email — "
            "votre mot de passe restera inchangé.",
            variant="danger"
        )
        + _body_close()
    )

    msg = MIMEMultipart('alternative')
    msg['Subject']    = f"Code de réinitialisation — Athena Event : {token}"
    msg['From']       = f"Athena Event <{SMTP_USER}>"
    msg['To']         = email
    msg['Reply-To']   = SMTP_USER
    msg['Message-ID'] = f"<reset-{token}@athena-event.com>"
    msg['X-Mailer']   = "Athena Event Platform"
    msg.attach(MIMEText(
        f"Athena Event — Réinitialisation de mot de passe\n\n"
        f"Bonjour {first_name},\n\n"
        f"Votre code de réinitialisation : {token}\n"
        f"Expire le : {expiry_date}\n\n"
        "Ne partagez jamais ce code.\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.\n\n"
        "Cordialement,\nL'équipe Athena Event",
        'plain', 'utf-8'
    ))
    msg.attach(MIMEText(
        _build_html(
            rows,
            preheader=f"Votre code de réinitialisation Athena Event : {token}"
        ),
        'html', 'utf-8'
    ))

    _send_email(msg)
    logging.info(f"Email reset password envoyé à {email}")


# ──────────────────────────────────────────────────────────────
# EMAILS ÉVÉNEMENTS
# ──────────────────────────────────────────────────────────────

def send_event_awaiting_approval(
    admin_email: str,
    event_id: str,
    event_title: str,
    company_name: str,
    created_at: str
) -> None:
    """Envoie un email à l'admin pour notifier qu'un événement attend approbation"""

    info_rows = (
        _info_row("", "Événement", f"<strong>{event_title}</strong>")
        + _info_row("", "Organisateur", company_name)
        + _info_row("", "Créé le", created_at)
    )

    rows = (
        _hero(
            title="Nouvel événement en attente",
            subtitle="Une demande d'approbation vous attend sur la plateforme",
            email_type_label="Action requise",
        )
        + _body_open(
            greeting="Bonjour,",
            intro=(
                "Un nouvel événement vient d'être créé et attend votre approbation "
                "sur la plateforme <strong>Athena Event</strong>."
            )
        )
        + _info_card(info_rows, label="RÉSUMÉ DE L'ÉVÉNEMENT")
        + """
        <p style="margin:0 0 4px 0;font-family:Arial,sans-serif;font-size:15px;
                   color:#57534e;line-height:1.75;">
          Connectez-vous à votre tableau de bord administrateur pour
          consulter les détails complets et approuver ou rejeter cet événement.
        </p>
        """
        + _alert(
            " <strong>Action requise :</strong> Veuillez traiter cette demande "
            "dans les meilleurs délais pour permettre à l'organisateur de poursuivre "
            "la préparation de son événement.",
            variant="warning"
        )
        + _body_close()
    )

    msg = MIMEMultipart('alternative')
    msg['Subject']    = f"Nouvel événement en attente — {event_title}"
    msg['From']       = f"Athena Event <{SMTP_USER}>"
    msg['To']         = admin_email
    msg['Reply-To']   = SMTP_USER
    msg['Message-ID'] = f"<event-approval-{event_id}@athena-event.com>"
    msg['X-Mailer']   = "Athena Event Platform"
    msg['X-Priority'] = "2"  # Haute priorité

    msg.attach(MIMEText(
        f"Athena Event — Nouvel événement en attente d'approbation\n\n"
        f"Événement : {event_title}\n"
        f"Organisateur : {company_name}\n"
        f"Créé le : {created_at}\n"
        f"Référence : #{event_id}\n\n"
        f"Accédez au tableau de bord admin pour approuver ou rejeter cet événement :\n"
        f"{APP_BASE_URL}/admin/events/pending\n\n"
        "Cordialement,\nL'équipe Athena Event",
        'plain', 'utf-8'
    ))
    msg.attach(MIMEText(
        _build_html(
            rows,
            preheader=f"Nouvel événement en attente — {event_title}"
        ),
        'html', 'utf-8'
    ))

    _send_email(msg)
    logging.info(f"Email notification admin envoyé à {admin_email} pour événement {event_id}")


def send_event_approved(
    company_email: str,
    company_name: str,
    event_id: str,
    event_title: str,
    event_start_date: str,
    event_location: str,
    approved_at: str
) -> None:
    """Envoie un email à l'entreprise pour confirmer que son événement est approuvé"""

    info_rows = (
        _info_row("", "Événement", f"<strong>{event_title}</strong>")
        + _info_row("", "Date", event_start_date)
        + _info_row("", "Lieu", event_location)
        + _info_row("", "Approuvé le", approved_at)
    )

    rows = (
        _hero(
            title="Événement approuvé !",
            subtitle="Félicitations, votre événement a été validé",
            email_type_label="Approuvé",
        )
        + _body_open(
            greeting=f"Bonjour {company_name},",
            intro=(
                "Nous avons le plaisir de vous informer que votre événement "
                "<strong>" + event_title + "</strong> a été approuvé par notre équipe. "
                "Vous pouvez désormais poursuivre la gestion de votre événement "
                "sur la plateforme <strong>Athena Event</strong>."
            )
        )
        + _info_card(info_rows, label="DÉTAILS DE L'ÉVÉNEMENT")
        + """
        <p style="margin:20px 0 0 0;font-family:Arial,sans-serif;font-size:15px;
                   color:#57534e;line-height:1.75;">
          Vous pouvez maintenant inviter des participants, gérer les inscriptions
          et accéder à toutes les fonctionnalités de gestion d'événement.
        </p>
        """
        + _alert(
            "<strong>Prochaines étapes :</strong> Connectez-vous à votre espace "
            "pour commencer à inviter vos participants et suivre les inscriptions en temps réel.",
            variant="warning"
        )
        + _body_close("Nous vous souhaitons un excellent événement !")
    )

    msg = MIMEMultipart('alternative')
    msg['Subject']    = f"Événement approuvé — {event_title}"
    msg['From']       = f"Athena Event <{SMTP_USER}>"
    msg['To']         = company_email
    msg['Reply-To']   = SMTP_USER
    msg['Message-ID'] = f"<event-approved-{event_id}@athena-event.com>"
    msg['X-Mailer']   = "Athena Event Platform"

    msg.attach(MIMEText(
        f"Athena Event — Événement approuvé\n\n"
        f"Bonjour {company_name},\n\n"
        f"Félicitations ! Votre événement a été approuvé.\n\n"
        f"DÉTAILS DE L'ÉVÉNEMENT\n"
        f"Événement : {event_title}\n"
        f"Date : {event_start_date}\n"
        f"Lieu : {event_location}\n"
        f"Approuvé le : {approved_at}\n"
        f"Référence : #{event_id}\n\n"
        "Vous pouvez maintenant inviter des participants et gérer les inscriptions.\n\n"
        "Nous vous souhaitons un excellent événement !\n\n"
        "Cordialement,\nL'équipe Athena Event",
        'plain', 'utf-8'
    ))
    msg.attach(MIMEText(
        _build_html(
            rows,
            preheader=f"Félicitations ! Votre événement {event_title} a été approuvé"
        ),
        'html', 'utf-8'
    ))

    _send_email(msg)
    logging.info(f"Email approbation événement envoyé à {company_email} pour {event_id}")


# ──────────────────────────────────────────────────────────────
# EMAILS INVITATIONS PARTICIPANTS
# ──────────────────────────────────────────────────────────────

def send_participant_invitation_known(
    company_email: str, company_name: str, event_id: str, token: str, url: str
) -> None:
    confirm_url = url
    decline_url = f"{APP_BASE_URL}/api/events/{event_id}/participants/decline?token={token}"

    info_rows = (
        _info_row("&#127970;", "Entreprise invitée", f"<strong>{company_name}</strong>")
        + _info_row("&#128197;", "Date de l'invitation", datetime.now().strftime('%d %B %Y'))
    )

    rows = (
        _hero(
            title="Invitation à participer",
            subtitle="Un événement vous attend sur Athena Event",
            email_type_label="Invitation événement",
        )
        + _body_open(
            greeting="Bonjour,",
            intro=(
                "Nous espérons que vous allez bien. Nous vous contactons concernant "
                "une invitation à participer à un événement organisé sur la plateforme "
                f"<strong>Athena Event</strong> pour <strong>{company_name}</strong>."
            )
        )
        + _info_card(info_rows, label="Détails de l'invitation")
        + """
        <p style="margin:0 0 4px 0;font-family:Arial,sans-serif;font-size:15px;
                   color:#57534e;line-height:1.75;">
          Pour plus d'informations ou si vous avez des questions, n'hésitez pas
          à nous contacter. Notre équipe se tient à votre disposition.
        </p>
        """
        + _cta_button(confirm_url, "Confirmer ma participation")
        + _cta_secondary(decline_url, "Décliner l'invitation")
        + _body_close()
    )

    msg = MIMEMultipart('alternative')
    msg['Subject']    = f"Invitation à un événement — {company_name}"
    msg['From']       = f"Athena Event <{SMTP_USER}>"
    msg['To']         = company_email
    msg['Reply-To']   = SMTP_USER
    msg['Message-ID'] = f"<{token}@athena-event.com>"
    msg['X-Mailer']   = "Athena Event Platform"
    msg.attach(MIMEText(
        f"Invitation à un événement — {company_name}\n\n"
        f"Entreprise : {company_name} | Référence : #{event_id}\n\n"
        f"Confirmer : {confirm_url}\n"
        f"Décliner  : {decline_url}\n\n"
        "Cordialement,\nL'équipe Athena Event",
        'plain', 'utf-8'
    ))
    msg.attach(MIMEText(
        _build_html(
            rows,
            preheader=f"Invitation à un événement Athena Event — {company_name}"
        ),
        'html', 'utf-8'
    ))

    _send_email(msg)
    logging.info(f"Email invitation (known) envoyé à {company_email}")


def send_participant_invitation_unknown(
    company_email: str, company_name: str, event_id: str, token: str, url: str
) -> None:
    if not company_email or '@' not in company_email:
        logging.error(f"Email invalide: '{company_email}'")
        raise ValueError(f"Email invalide: {company_email}")

    # TODO : remplacer localhost par APP_BASE_URL avant le déploiement en production
    signup_url = url

    steps = [
        "Cliquez sur le bouton ci-dessous pour "
        "<strong style='color:#44403c;'>créer votre compte gratuitement</strong>",
        "Complétez les informations de "
        "<strong style='color:#44403c;'>votre entreprise</strong>",
        "Votre participation est "
        "<strong style='color:#44403c;'>automatiquement confirm&#233;e</strong> &#10003;",
    ]

    rows = (
        _hero(
            title="Rejoignez un événement",
            subtitle="Créez votre compte gratuit pour confirmer votre participation",
            email_type_label="Nouvelle inscription",
        )
        + _body_open(
            greeting="Bonjour,",
            intro=(
                "Nous vous contactons concernant une invitation à rejoindre un événement "
                f"organisé sur <strong>Athena Event</strong> pour <strong>{company_name}</strong>. "
                "La création de votre compte est gratuite et prend moins de 2 minutes."
            )
        )
        + _steps_card(steps)
        + _cta_button(signup_url, "Créer mon compte gratuit")
        + _body_close()
    )

    msg = MIMEMultipart('alternative')
    msg['Subject']    = f"Invitation à rejoindre un événement — {company_name}"
    msg['From']       = f"Athena Event <{SMTP_USER}>"
    msg['To']         = company_email
    msg['Reply-To']   = SMTP_USER
    msg['Message-ID'] = f"<{token}@athena-event.com>"
    msg['X-Mailer']   = "Athena Event Platform"
    msg.attach(MIMEText(
        f"Invitation à rejoindre un événement — {company_name}\n\n"
        "1. Créez votre compte gratuitement\n"
        "2. Complétez les informations de votre entreprise\n"
        "3. Votre participation est automatiquement confirmée\n\n"
        f"Créer mon compte : {signup_url}\n\n"
        "Cordialement,\nL'équipe Athena Event",
        'plain', 'utf-8'
    ))
    msg.attach(MIMEText(
        _build_html(
            rows,
            preheader=f"Vous êtes invité à rejoindre un événement Athena Event — {company_name}"
        ),
        'html', 'utf-8'
    ))

    _send_email(msg)
    logging.info(f"Email invitation (unknown) envoyé à {company_email}")


def send_activation_link_organizer(
    email: str,
    first_name: str,
    last_name: str,
    default_password: str,
    company_name: str,
    activation_link: str,
) -> None:
    creds_rows = (
        _info_row("", "Email", email)
        + _info_row(
            "", "Mot de passe provisoire",
            f"<code style='background-color:#f5f0e0;padding:2px 7px;"
            f"border-radius:4px;font-family:Courier New,monospace;"
            f"font-size:13px;color:#44403c;'>{default_password}</code>"
        )
        + _info_row("", "Entreprise", f"<strong>{company_name}</strong>")
    )

    rows = (
        _hero(
            title=f"Bienvenue, {first_name} !",
            subtitle="Votre compte organisateur Athena Event a été créé",
            email_type_label="Compte organisateur",
        )
        + _body_open(
            greeting=f"Bonjour {first_name} {last_name},",
            intro=(
                f"Nous avons le plaisir de vous accueillir en tant qu'organisateur "
                f"sur <strong>Athena Event</strong>. Votre compte pour "
                f"<strong>{company_name}</strong> est prêt — activez-le pour commencer."
            )
        )
        + _info_card(creds_rows, label="Vos identifiants de connexion")
        + """
        <p style="margin:0 0 4px 0;font-family:Arial,sans-serif;font-size:15px;
                   color:#57534e;line-height:1.75;">
          Cliquez sur le bouton ci-dessous pour activer votre compte
          et définir votre propre mot de passe :
        </p>
        """
        + _cta_button(activation_link, "Activer mon compte")
        + _alert(
            "<strong>Sécurité :</strong> Vous devrez changer ce mot de passe "
            "provisoire lors de votre première connexion. "
            "Ne partagez jamais vos identifiants avec qui que ce soit.",
            variant="warning"
        )
        + _body_close("Nous sommes ravis de vous compter parmi nos organisateurs.<br>Cordialement,")
    )

    msg = MIMEMultipart('alternative')
    msg['Subject']    = f"Bienvenue sur Athena Event — {first_name} {last_name}"
    msg['From']       = f"Athena Event <{SMTP_USER}>"
    msg['To']         = email
    msg['Reply-To']   = SMTP_USER
    msg['X-Mailer']   = "Athena Event Platform"
    msg.attach(MIMEText(
        f"Athena Event — Compte Organisateur\n\n"
        f"Bonjour {first_name} {last_name},\n\n"
        f"Email : {email}\n"
        f"Mot de passe provisoire : {default_password}\n"
        f"Entreprise : {company_name}\n\n"
        f"Activer mon compte : {activation_link}\n\n"
        "Changez votre mot de passe à la première connexion.\n\n"
        "Cordialement,\nL'équipe Athena Event",
        'plain', 'utf-8'
    ))
    msg.attach(MIMEText(
        _build_html(
            rows,
            preheader=f"Bienvenue sur Athena Event, {first_name} — activez votre compte organisateur"
        ),
        'html', 'utf-8'
    ))

    _send_email(msg)
    logging.info(f"Email organisateur envoyé à {email}")


def send_request_otp(destinataire: str, otp: str, event_image_url: str = None) -> None:
    rows = (
        _hero(
            title="Votre code de connexion",
            subtitle="Utilisez ce code pour accéder à votre compte",
            email_type_label="Authentification",
            hero_image_url=event_image_url or "",
        )
        + _body_open(
            greeting="Bonjour,",
            intro=(
                "Vous avez demandé un code de connexion pour accéder à votre compte "
                "<strong>Athena Event</strong>. Saisissez le code ci-dessous dans l'application :"
            )
        )
        + _code_block(otp, label="Votre code OTP")
        + _alert(
            "<strong>Ce code est valable quelques minutes.</strong> "
            "Ne le partagez avec personne — l'équipe Athena Event ne vous le demandera jamais. "
            "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.",
            variant="danger"
        )
        + _body_close()
    )

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Votre code de connexion Athena Event : {otp}"
    msg['From']    = f"Athena Event <{SMTP_USER}>"
    msg['To']      = destinataire
    msg.attach(MIMEText(
        f"Athena Event — Code de connexion\n\n"
        f"Votre code OTP : {otp}\n\n"
        "Ce code est valable quelques minutes.\n"
        "Ne le partagez avec personne.\n\n"
        "Cordialement,\nL'équipe Athena Event",
        'plain', 'utf-8'
    ))
    msg.attach(MIMEText(
        _build_html(rows, preheader=f"Votre code de connexion Athena Event : {otp}"),
        'html', 'utf-8'
    ))

    _send_email(msg)
    logging.info(f"Email OTP envoyé à {destinataire}")
