# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║   ZONE LOGIQUE — ENVOI SMTP                                  ║
# ║                                                              ║
# ║   Modifier ici peut casser la livraison des emails.         ║
# ║                                                              ║
# ╚══════════════════════════════════════════════════════════════╝

import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD


def _send_email(msg: MIMEMultipart) -> None:
    """
    Envoi SMTP centralisé — SMTP simple + STARTTLS (port 587).
    Toutes les fonctions send_xxx() passent par ici.
    """
    if not SMTP_PASSWORD:
        raise ValueError("SMTP_PASSWORD manquant — vérifier les variables d'environnement")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        logging.error(f"❌ Erreur SMTP ({SMTP_HOST}:{SMTP_PORT}) : {e}")
        raise


def _format_expiry(expires_at_ms: int) -> str:
    """Convertit un timestamp en millisecondes en date lisible."""
    return datetime.fromtimestamp(expires_at_ms / 1000).strftime('%d %B %Y à %H:%M')
