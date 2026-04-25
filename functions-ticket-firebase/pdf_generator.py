# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║   ZONE LOGIQUE — GÉNÉRATION BADGE ZPL & UPLOAD GCS          ║
# ║                                                              ║
# ║   Génère un fichier ZPL pour l'imprimante Zebra iT4S.       ║
# ║   Le QR code est rendu nativement par l'imprimante via ^BQ. ║
# ║                                                              ║
# ║   Pour modifier la mise en page du badge → _build_zpl()     ║
# ║   Pour modifier les dimensions → PW (largeur) / LL (hauteur)║
# ║   Pour modifier les polices → paramètres ^A0N,h,w           ║
# ║                                                              ║
# ╚══════════════════════════════════════════════════════════════╝

import logging

from storage import storage_client


# ──────────────────────────────────────────────────────────────
# DIMENSIONS DU BADGE — 10×5.5cm à 300 DPI (11.81 dots/mm)
# ──────────────────────────────────────────────────────────────
# Largeur  : 10cm  = 1181 dots → ^PW1181
# Hauteur  : 5.5cm =  650 dots → ^LL650
#
# Colonne gauche (texte)  : x=44  jusqu'à x≈700
# Colonne droite (QR)     : x=700 jusqu'à x≈1181
# ──────────────────────────────────────────────────────────────

LABEL_WIDTH  = 1181  # dots — 10cm à 300 DPI
LABEL_HEIGHT = 650   # dots — ~5.5cm à 300 DPI

# Limites de caractères par champ (approximation police Zebra ^A0)
# Police 88×82 : ~53 dots/char → 656 dots (44→700) → ~12 chars max
# Police 80×72 : ~48 dots/char → 656 dots           → ~13 chars max
# Police 52×52 : ~31 dots/char → 656 dots           → ~21 chars max
MAX_CHARS_PRENOM     = 12   # ligne 1 — police 88×82 (grande)
MAX_CHARS_NOM        = 13   # ligne 2 — police 80×72
MAX_CHARS_ENTREPRISE = 21
MAX_CHARS_POSTE      = 21


def _truncate(text: str, max_chars: int) -> str:
    """Tronque le texte avec '...' si trop long pour la colonne."""
    if len(text) > max_chars:
        return text[:max_chars - 3] + "..."
    return text


def _build_zpl(
    qr_token: str,
    user_first_name: str,
    user_last_name: str,
    company_name: str,
    user_role: str,
) -> str:
    """
    Construit le ZPL du badge 10×5cm.

    Mise en page :
      Colonne gauche  — Nom (gras), Prénom, Entreprise, Poste
      Colonne droite  — QR code natif Zebra + token sous le QR

    Commandes clés :
      ^PW / ^LL     — dimensions du label
      ^CI28         — encodage UTF-8
      ^A0N,h,w      — police interne Zebra (h=hauteur, w=largeur en dots)
      ^FO x,y       — position du champ (origine haut-gauche)
      ^FD...^FS     — données du champ
      ^BQN,2,8      — QR code, modèle 2, taille module 8 dots (≈1mm)
      ^FDQA,...^FS  — données QR : Q=correction level, A=model, puis le token
    """

    # ── Colonne gauche : texte ────────────────────────────────────
    nom     = _truncate(user_last_name.upper(), MAX_CHARS_NOM)
    prenom  = _truncate(user_first_name, MAX_CHARS_PRENOM)
    company = _truncate(company_name.strip().upper(), MAX_CHARS_ENTREPRISE) if company_name and company_name.strip() and company_name.strip() != "N/A" else ""
    role    = _truncate(user_role.strip(), MAX_CHARS_POSTE)                 if user_role    and user_role.strip()    and user_role.strip()    != "N/A" else ""

    # Lignes optionnelles (affichées seulement si non vides)
    company_line = f"\n^FO44,338^A0N,52,52^FD{company}^FS" if company else ""
    role_line    = f"\n^FO44,400^A0N,52,52^FD{role}^FS"    if role    else ""

    # ── Colonne droite : QR code ──────────────────────────────────
    # ^BQN,2,20 → QR modèle 2, module 20 dots (~1.7mm), orientation normale
    # Token centré sous le QR via ^FB (Field Block, justification C)
    # ^FB[largeur],1,0,C → centre le texte dans une boîte de [largeur] dots
    y_qr    = 60
    y_token = 560

    return (
        f"^XA"
        f"^PW{LABEL_WIDTH}"
        f"^LL{LABEL_HEIGHT}"
        f"^CI28"
        f"^FO44,100^A0N,88,82^FD{prenom}^FS"           # Prénom — en haut
        f"^FO44,220^A0N,80,72^FD{nom}^FS"              # Nom — en dessous
        f"{company_line}"                               # Entreprise (optionnel)
        f"{role_line}"                                  # Poste (optionnel)
        f"^FO700,{y_qr}^BQN,2,20^FDQA,{qr_token}^FS"  # QR code natif — module 20 dots
        f"^FO700,{y_token}^A0N,34,34^FB437,1,0,C^FD{qr_token}^FS"  # Token centré sous QR
        f"^XZ"
    )


def generate_and_upload_badge(
    qr_token: str,
    user_first_name: str,
    user_last_name: str,
    company_name: str,
    user_role: str,
) -> None:
    """
    Génère le badge ZPL et l'uploade sur GCS.
    Appelé uniquement pour le premier envoi (EVENT_REGISTRATION_CONFIRMED).
    Le QR code est rendu par l'imprimante Zebra iT4S — pas besoin de PIL/ReportLab.
    """

    zpl_content = _build_zpl(
        qr_token=qr_token,
        user_first_name=user_first_name,
        user_last_name=user_last_name,
        company_name=company_name,
        user_role=user_role,
    )

    logging.info("✅ Badge ZPL généré")

    # ── Upload GCS ────────────────────────────────────────────────
    try:
        bucket = storage_client.bucket("demo-event-app.appspot.com")
        blob   = bucket.blob(f"tickets/badge_{qr_token}.zpl")
        blob.upload_from_string(zpl_content.encode("utf-8"), content_type="text/plain; charset=utf-8")
        logging.info(f"📦 Badge ZPL uploadé: tickets/badge_{qr_token}.zpl")
    except Exception as e:
        logging.error(f"❌ Échec upload: {e}")
