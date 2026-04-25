import os

# ──────────────────────────────────────────────────────────────
# CONFIG VISUELLE
# Les deux seules valeurs à changer quand tu as tes vrais assets
# ──────────────────────────────────────────────────────────────

# Image de fond du hero — recommandé : 1200×400px, hébergée sur GCS/Firebase
HERO_IMAGE_URL = "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=600&q=80&auto=format&fit=crop"

# Logo Athena Event — recommandé : PNG 96×96px (retina), fond transparent
LOGO_URL = "https://athena-event.com/logo.png"


# ──────────────────────────────────────────────────────────────
# CONFIG SMTP
# ──────────────────────────────────────────────────────────────

SMTP_HOST     = os.environ.get("SMTP_HOST", "smtp.zeptomail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER     = os.environ.get("SMTP_USER", "noreply@athena-event.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
