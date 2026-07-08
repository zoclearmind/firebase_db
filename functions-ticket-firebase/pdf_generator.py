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
# Colonne gauche : x=44→700 → 656 dots disponibles
# ^A0 est une police proportionnelle — largeur réelle ≈ 65% du paramètre width
# Police 60×52 : ~34 dots/char réel → 656/34 → ~19 chars max
# Police 88×82 : ~53 dots/char réel → 656/53 → ~12 chars max
# Police 35×35 : ~22 dots/char réel → 656/22 → ~29 chars max
MAX_CHARS_PRENOM     = 19   # ligne 1 — police 60×52
MAX_CHARS_NOM        = 12   # ligne 2 — police 88×82 (grande)
MAX_CHARS_ENTREPRISE = 29   # ligne 3 — police 35×35
MAX_CHARS_POSTE      = 29   # ligne 4 — police 35×35


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
    company_line = f"\n^FO44,360^A0N,35,35^FD{company}^FS" if company else ""
    role_line    = f"\n^FO44,420^A0N,35,35^FD{role}^FS"    if role    else ""

    return (
        f"^XA"
        f"^PW{LABEL_WIDTH}"
        f"^LL{LABEL_HEIGHT}"
        f"^CI28"
        f"^FO44,100^A0N,60,52^FD{prenom}^FS"                          # Prénom — en haut (petit)
        f"^FO44,180^A0N,88,82^FD{nom}^FS"                             # Nom — en dessous (grand)
        f"{company_line}"                                              # Entreprise (optionnel)
        f"{role_line}"                                                 # Poste (optionnel)
        f"^FO700,90^BQN,2,20^FDQA,{qr_token}^FS"                      # QR code natif — module 20 dots
        f"^FO660,555^A0N,38,50^FB537,1,0,C^FD{qr_token}^FS"          # Token centré sous QR
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
