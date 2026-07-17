"""
Configuration centralisée pour la fonction brochure email.
Modifier ici pour changer les paramètres globaux.
"""
import os

# Configuration SMTP
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.zeptomail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "noreply@athena-event.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

# Configuration Firebase Storage
BUCKET_NAME = os.environ.get("BUCKET_NAME", "athena-event-prod")

# Mapping des templates
TEMPLATES = {
    1: "template_1.html",  # Corporate Élégant
    2: "template_2.html",  # Modern Professional
    3: "template_3.html",  # Business Professional
    4: "template_4.html",  # Confirmation d'inscription événementielle
    5: "email_remerciement.html",  # Remerciement post-événement
    6: "email_contact_request.html",  # Demandes de mise en relation entre participants
    7: "email_contact_accepted.html",  # Acceptation d'une demande de mise en relation
    8: "email_reminder.html"  # Rappel d'événement (J-1)
}
