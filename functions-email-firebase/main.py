import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote

from firebase_admin import initialize_app
from firebase_functions import pubsub_fn

# Initialiser Firebase Admin
initialize_app()


# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║   ZONE DESIGN — MODIFIABLE LIBREMENT                        ║
# ║                                                              ║
# ║   Tout ce qui concerne l'apparence visuelle des emails      ║
# ║   se trouve ICI, entre ce bloc et le bloc LOGIQUE.          ║
# ║                                                              ║
# ║   Pour modifier :                                            ║
# ║     • Logo / image hero    → section CONFIG VISUELLE        ║
# ║     • Couleurs, polices    → fonction _base_styles()        ║
# ║     • Structure du header  → fonction _hero()               ║
# ║     • Footer               → fonction _footer()             ║
# ║     • Cards, boutons       → fonctions _info_card(),        ║
# ║                              _cta_button(), _alert()        ║
# ║     • Contenu d'un email   → fonctions send_xxx() en bas,   ║
# ║                              partie "rows = (...)"          ║
# ║                                                              ║
# ╚══════════════════════════════════════════════════════════════╝


# ──────────────────────────────────────────────────────────────
# CONFIG VISUELLE
# Les deux seules valeurs à changer quand tu as tes vrais assets
# ──────────────────────────────────────────────────────────────

# Image de fond du hero — recommandé : 1200×400px, hébergée sur GCS/Firebase
HERO_IMAGE_URL = "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=600&q=80&auto=format&fit=crop"

# Logo Athena Event — recommandé : PNG 96×96px (retina), fond transparent
LOGO_URL = "https://athena-event.com/logo.png"


# ──────────────────────────────────────────────────────────────
# CONFIG SMTP & APP
# Centralisées ici — ne pas redéclarer dans chaque fonction
# ──────────────────────────────────────────────────────────────

SMTP_HOST     = os.environ.get("SMTP_HOST", "smtp.zeptomail.com")
SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER     = os.environ.get("SMTP_USER", "noreply@athena-event.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

APP_BASE_URL  = os.environ.get("APP_BASE_URL", "https://app.athena-event.com")


# ──────────────────────────────────────────────────────────────
# STYLES CSS
# Modifier ici pour changer couleurs, tailles, espacements
# ──────────────────────────────────────────────────────────────

def _base_styles() -> str:
    # NOTE TECHNIQUE : pas de @import Google Fonts (bloqué par Gmail)
    # → on utilise Georgia (serif) et Arial (sans-serif), universellement supportés
    # NOTE TECHNIQUE : pas de rgba() dans les attributs HTML → hex solides uniquement
    return """
        /* Reset email — ne pas modifier */
        body, table, td, a { -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; }
        table, td           { mso-table-lspace:0pt; mso-table-rspace:0pt; }
        img                 { -ms-interpolation-mode:bicubic; border:0; display:block; }
        .ReadMsgBody        { width:100%; }
        .ExternalClass      { width:100%; }
        .ExternalClass, .ExternalClass p, .ExternalClass span,
        .ExternalClass font, .ExternalClass td, .ExternalClass div { line-height:100%; }

        /* ── Overrides mobile (max 600px) ──
           Chaque classe correspond à un élément identifiable dans le HTML ci-dessous */
        @media only screen and (max-width:600px) {

            /* Email pleine largeur sur mobile, sans border-radius */
            .email-outer-td { padding:0 !important; }
            .email-shell    { width:100% !important; min-width:100% !important;
                               border-radius:0 !important; }

            /* Hero plus compact */
            .hero-td        { height:185px !important; padding:20px 16px !important; }

            /* Logo + nom de marque : empilés verticalement */
            .logo-brand-td  { display:block !important; width:100% !important; }
            .logo-img       { width:36px !important; height:36px !important; }
            .brand-name     { font-size:17px !important; }
            .brand-sub      { font-size:9px !important; }

            /* Badge type email : passe sous le logo, aligné à gauche */
            .ref-badge-td    { display:block !important; width:100% !important;
                               text-align:left !important;
                               padding-top:10px !important; padding-left:0 !important; }
            .ref-badge-inner { text-align:left !important; }

            /* Titres hero plus petits */
            .hero-title     { font-size:17px !important; }
            .hero-sub       { font-size:11px !important; }

            /* Corps de l'email : padding réduit */
            .body-td        { padding:24px 16px 0 16px !important; }

            /* Cards : padding réduit */
            .card-td        { padding:16px !important; }

            /* Bouton CTA */
            .cta-td         { padding:14px 24px !important; }
            .cta-link       { font-size:14px !important; }

            /* Bloc code */
            .code-block-td  { padding:20px 14px !important; }
            .code-val       { font-size:30px !important; letter-spacing:8px !important; }

            /* Footer */
            .footer-td      { padding:22px 16px !important; }

            /* Footer : deux colonnes → empilées verticalement */
            .footer-col-l   { display:block !important; width:100% !important; }
            .footer-col-r   { display:block !important; width:100% !important;
                               text-align:left !important; padding-top:14px !important; }

            /* Note légale sous l'email */
            .below-note     { padding:0 16px !important; }
        }
    """


# ──────────────────────────────────────────────────────────────
# STRUCTURE HTML — ENVELOPPE
# ──────────────────────────────────────────────────────────────

def _preheader(text: str) -> str:
    """Texte affiché dans l'aperçu de la boîte de réception (invisible dans l'email)."""
    filler = "&nbsp;&#8204;" * 60
    return (
        f'<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;'
        f'font-size:1px;color:#fafafa;line-height:1px;">{text}{filler}</div>'
    )


def _email_open(preheader_text: str = "") -> str:
    """Ouvre le document HTML, injecte les styles et la table wrapper principale."""
    return f"""<!DOCTYPE html>
<html lang="fr" xmlns="http://www.w3.org/1999/xhtml"
      xmlns:v="urn:schemas-microsoft-com:vml"
      xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light">
    <meta name="supported-color-schemes" content="light">
    <title>Athena Event</title>
    <!--[if mso]>
    <noscript><xml><o:OfficeDocumentSettings>
        <o:PixelsPerInch>96</o:PixelsPerInch>
    </o:OfficeDocumentSettings></xml></noscript>
    <![endif]-->
    <style>{_base_styles()}</style>
</head>
<body style="margin:0;padding:0;background-color:#ede9de;word-spacing:normal;">
{_preheader(preheader_text)}
<!--[if mso | IE]>
<table role="presentation" border="0" cellpadding="0" cellspacing="0"
       width="100%" style="background-color:#ede9de;"><tr><td>
<![endif]-->
<table role="presentation" border="0" cellpadding="0" cellspacing="0"
       width="100%" style="background-color:#ede9de;">
  <tr>
    <td class="email-outer-td" align="center" style="padding:32px 16px;">
      <table role="presentation" border="0" cellpadding="0" cellspacing="0"
             class="email-shell"
             style="width:600px;max-width:600px;background-color:#ffffff;
                    border-radius:16px;overflow:hidden;
                    box-shadow:0 8px 40px rgba(0,0,0,0.13);">
"""


def _email_close() -> str:
    """Ferme la table shell, ajoute la note légale, ferme le body."""
    return """
      </table><!-- /email-shell -->

      <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
        <tr>
          <td class="below-note" align="center"
              style="padding:14px 32px 0;font-family:Arial,sans-serif;
                     font-size:11px;color:#a8a29e;line-height:1.6;">
            Cet email a été envoyé automatiquement par la plateforme Athena Event.<br>
            Merci de ne pas y répondre directement.
          </td>
        </tr>
      </table>

    </td>
  </tr>
</table>
<!--[if mso | IE]></td></tr></table><![endif]-->
</body>
</html>"""


# ──────────────────────────────────────────────────────────────
# COMPOSANTS VISUELS
# ──────────────────────────────────────────────────────────────

def _hero(title: str, subtitle: str, email_type_label: str = "") -> str:
    """
    Bandeau hero avec image de fond, logo, nom de marque.

    email_type_label : texte affiché dans le badge en haut à droite du hero.
                       Décrit explicitement le type d'email, ex :
                       "Activation de compte", "Invitation événement", etc.
                       Laisser vide pour ne pas afficher de badge.

    Technique image de fond :
      - background-image CSS  → Gmail, Apple Mail, Samsung Mail
      - attribut background=  → clients anciens
      - VML v:rect            → Outlook Windows (commentaires conditionnels)
    """
    badge_col = ""
    if email_type_label:
        badge_col = f"""
            <td class="ref-badge-td" valign="middle" align="right"
                style="vertical-align:middle;padding-left:12px;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0"
                     align="right">
                <tr>
                  <td class="ref-badge-inner"
                      style="background-color:#0a0a14;border:1px solid #4d3f00;
                             border-radius:8px;padding:8px 14px;text-align:right;">
                    <div style="font-family:Arial,sans-serif;font-size:11px;
                                font-weight:600;color:#fde047;letter-spacing:0.5px;
                                line-height:1.3;">
                      {email_type_label}
                    </div>
                  </td>
                </tr>
              </table>
            </td>"""

    cols = 2 if email_type_label else 1

    return f"""
    <!--[if mso | IE]><tr><td style="background-color:#1a1a2e;padding:0;"><![endif]-->
    <tr>
      <td class="hero-td"
          background="{HERO_IMAGE_URL}"
          style="background-color:#1a1a2e;
                 background-image:url('{HERO_IMAGE_URL}');
                 background-size:cover;background-position:center center;
                 background-repeat:no-repeat;
                 padding:28px 32px;height:200px;vertical-align:middle;">

        <!--[if mso | IE]>
        <v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false"
                style="width:600px;height:200px;position:absolute;">
          <v:fill type="frame" src="{HERO_IMAGE_URL}" color="#1a1a2e"/>
          <v:textbox inset="0,0,0,0">
        <![endif]-->

        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">

          <!-- Ligne 1 : Logo + marque + badge type email -->
          <tr>
            <td class="logo-brand-td" valign="middle" style="vertical-align:middle;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <td valign="middle" style="padding-right:12px;vertical-align:middle;">
                    <img class="logo-img" src="{LOGO_URL}" alt="Athena Event"
                         width="44" height="44"
                         style="width:44px;height:44px;border-radius:10px;
                                border:1.5px solid #7a6500;display:block;" />
                  </td>
                  <td valign="middle" style="vertical-align:middle;">
                    <div class="brand-name"
                         style="font-family:Georgia,'Times New Roman',serif;
                                font-size:21px;font-weight:700;color:#ffffff;
                                line-height:1.2;margin:0;">
                      Athena Event
                    </div>
                    <div class="brand-sub"
                         style="font-family:Arial,sans-serif;font-size:10px;
                                color:#c9a800;letter-spacing:2.5px;
                                text-transform:uppercase;margin-top:3px;">
                      by Clearmind Analytics
                    </div>
                  </td>
                </tr>
              </table>
            </td>
            {badge_col}
          </tr>

          <!-- Spacer -->
          <tr>
            <td colspan="{cols}" style="height:18px;font-size:1px;line-height:1px;">&nbsp;</td>
          </tr>

          <!-- Ligne 2 : Titre + sous-titre -->
          <tr>
            <td colspan="{cols}">
              <div style="width:36px;height:2px;background-color:#fde047;
                          margin-bottom:10px;"></div>
              <div class="hero-title"
                   style="font-family:Georgia,'Times New Roman',serif;
                          font-size:20px;font-weight:700;color:#ffffff;
                          line-height:1.3;margin:0;">
                {title}
              </div>
              <div class="hero-sub"
                   style="font-family:Arial,sans-serif;font-size:12px;
                          color:#cccccc;margin-top:6px;letter-spacing:0.3px;">
                {subtitle}
              </div>
            </td>
          </tr>

        </table>

        <!--[if mso | IE]></v:textbox></v:rect><![endif]-->
      </td>
    </tr>
    <!--[if mso | IE]></td></tr><![endif]-->

    <!-- Bande dorée accent sous le hero -->
    <tr>
      <td style="height:4px;font-size:4px;line-height:4px;
                 background-color:#fbbf24;">&nbsp;</td>
    </tr>
"""


def _body_open(greeting: str, intro: str) -> str:
    """Ouvre la zone de contenu : salutation + paragraphe d'introduction."""
    return f"""
    <tr>
      <td class="body-td" style="padding:36px 36px 0 36px;">
        <p style="margin:0 0 8px 0;font-family:Georgia,'Times New Roman',serif;
                  font-size:19px;font-weight:700;color:#1c1917;line-height:1.3;">
          {greeting}
        </p>
        <p style="margin:0 0 24px 0;font-family:Arial,sans-serif;
                  font-size:15px;color:#57534e;line-height:1.75;">
          {intro}
        </p>
"""


def _body_close(sign_off: str = "Cordialement,") -> str:
    """Ferme la zone de contenu : séparateur doré + signature."""
    return f"""
        <table role="presentation" border="0" cellpadding="0" cellspacing="0"
               width="100%" style="margin-top:32px;">
          <tr>
            <td width="80" style="height:1px;background-color:#fde047;
                                   font-size:1px;line-height:1px;">&nbsp;</td>
            <td style="height:1px;background-color:#f0e8c0;
                       font-size:1px;line-height:1px;">&nbsp;</td>
          </tr>
        </table>
        <p style="margin:20px 0 0 0;font-family:Arial,sans-serif;
                  font-size:15px;color:#44403c;line-height:1.7;">
          {sign_off}<br>
          <strong style="color:#1c1917;">L'équipe Athena Event</strong>
        </p>
      </td>
    </tr>
    <tr><td style="height:36px;font-size:1px;line-height:1px;">&nbsp;</td></tr>
"""


def _info_card(rows_html: str, label: str = "DÉTAILS") -> str:
    """
    Encadré jaune avec bordure left dorée.
    rows_html : lignes générées par _info_row()
    label     : titre de la card en petites capitales
    """
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin:24px 0;">
      <tr>
        <td class="card-td"
            style="background-color:#fffbeb;border-radius:10px;
                   border:1px solid #fde68a;border-left-width:4px;
                   border-left-color:#fbbf24;padding:20px 22px;">
          <p style="margin:0 0 14px 0;font-family:Arial,sans-serif;font-size:10px;
                     font-weight:700;color:#b45309;text-transform:uppercase;
                     letter-spacing:2.5px;">
            {label}
          </p>
          {rows_html}
        </td>
      </tr>
    </table>
"""


def _info_row(icon: str, label: str, value: str) -> str:
    """
    Ligne d'information avec icône.
    Utilise une table pour l'alignement (flex non supporté dans tous les clients email).
    """
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin-bottom:10px;">
      <tr>
        <td valign="top" width="22"
            style="font-family:Arial,sans-serif;font-size:14px;
                   color:#57534e;padding-top:1px;vertical-align:top;">
          {icon}
        </td>
        <td valign="top" style="font-family:Arial,sans-serif;font-size:14px;
                                 color:#57534e;line-height:1.5;vertical-align:top;">
          <strong style="color:#44403c;">{label}&nbsp;:</strong> {value}
        </td>
      </tr>
    </table>
"""


def _cta_button(url: str, label: str) -> str:
    """
    Bouton call-to-action centré.
    Technique double :
      - VML v:roundrect pour Outlook Windows (commentaires conditionnels)
      - <a> inline-block pour tous les autres clients
    """
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin:28px 0 8px 0;">
      <tr>
        <td align="center">
          <!--[if mso | IE]>
          <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml"
                       xmlns:w="urn:schemas-microsoft-com:office:word"
                       href="{url}"
                       style="height:50px;v-text-anchor:middle;width:280px;"
                       arcsize="20%" strokecolor="#fde047" strokeweight="1pt"
                       fillcolor="#1a1a2e">
            <w:anchorlock/>
            <center style="color:#fde047;font-family:Arial,sans-serif;
                           font-size:15px;font-weight:bold;">
              {label}
            </center>
          </v:roundrect>
          <![endif]-->
          <!--[if !mso]><!-->
          <a href="{url}" class="cta-link" target="_blank"
             style="display:inline-block;background-color:#1a1a2e;
                    color:#fde047;font-family:Arial,sans-serif;font-size:15px;
                    font-weight:700;text-decoration:none;border-radius:10px;
                    padding:16px 40px;mso-hide:all;border:1px solid #3a3a00;">
            {label}
          </a>
          <!--<![endif]-->
        </td>
      </tr>
    </table>
"""


def _cta_secondary(url: str, label: str) -> str:
    """Lien secondaire centré sous le bouton principal (ex: Décliner l'invitation)."""
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin:8px 0 0 0;">
      <tr>
        <td align="center">
          <a href="{url}" target="_blank"
             style="font-family:Arial,sans-serif;font-size:13px;
                    color:#9ca3af;text-decoration:underline;">
            {label}
          </a>
        </td>
      </tr>
    </table>
"""


def _alert(content: str, variant: str = "warning") -> str:
    """
    Encadré d'alerte avec bordure left colorée.
    variant = "warning" → fond jaune pâle, bordure dorée
    variant = "danger"  → fond rouge pâle, bordure rouge
    """
    styles = {
        "warning": ("#fffbeb", "#fbbf24", "#92400e"),
        "danger":  ("#fff5f5", "#ef4444", "#7f1d1d"),
    }
    bg, border, color = styles.get(variant, styles["warning"])
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin:20px 0;">
      <tr>
        <td style="background-color:{bg};border-left:3px solid {border};
                    border-radius:0 8px 8px 0;padding:14px 16px;">
          <p style="margin:0;font-family:Arial,sans-serif;font-size:13px;
                     color:{color};line-height:1.65;">
            {content}
          </p>
        </td>
      </tr>
    </table>
"""


def _code_block(code: str, label: str = "Code d'activation") -> str:
    """
    Bloc fond sombre avec un code en grand centré.
    Réutilisé pour l'activation de compte ET le reset password.
    label : texte au-dessus du code (modifiable selon le contexte)
    """
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin:28px 0;">
      <tr>
        <td class="code-block-td" align="center"
            style="background-color:#1a1a2e;border-radius:14px;
                   padding:28px 32px;text-align:center;border:1px solid #2d2d4a;">
          <p style="margin:0 0 10px 0;font-family:Arial,sans-serif;font-size:10px;
                     color:#b89000;text-transform:uppercase;letter-spacing:3px;">
            {label}
          </p>
          <p class="code-val"
             style="margin:0;font-family:'Courier New',Courier,monospace;
                    font-size:40px;font-weight:700;color:#fde047;
                    letter-spacing:14px;line-height:1;">
            {code}
          </p>
        </td>
      </tr>
    </table>
"""


def _steps_card(steps: list) -> str:
    """
    Card avec étapes numérotées.
    steps : liste de chaînes HTML décrivant chaque étape.
    Utilise des tables pour les puces numérotées (pas de <ol> — mal supporté).
    """
    rows_html = ""
    for i, step in enumerate(steps, 1):
        margin = "style='margin-bottom:14px;'" if i < len(steps) else ""
        rows_html += f"""
        <table role="presentation" border="0" cellpadding="0" cellspacing="0"
               width="100%" {margin}>
          <tr>
            <td valign="top" width="36" style="vertical-align:top;padding-top:2px;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <td width="28" height="28" align="center" valign="middle"
                      style="width:28px;height:28px;border-radius:50%;
                             background-color:#fde047;text-align:center;
                             font-family:Arial,sans-serif;font-size:13px;
                             font-weight:700;color:#92400e;line-height:28px;">
                    {i}
                  </td>
                </tr>
              </table>
            </td>
            <td valign="top"
                style="font-family:Arial,sans-serif;font-size:14px;
                       color:#78716c;line-height:1.6;vertical-align:top;
                       padding-top:4px;">
              {step}
            </td>
          </tr>
        </table>
"""
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin:24px 0;">
      <tr>
        <td class="card-td"
            style="background-color:#fffbeb;border-radius:10px;
                   border:1px solid #fde68a;border-left-width:4px;
                   border-left-color:#fbbf24;padding:20px 22px;">
          <p style="margin:0 0 16px 0;font-family:Arial,sans-serif;font-size:10px;
                     font-weight:700;color:#b45309;text-transform:uppercase;
                     letter-spacing:2.5px;">
            &#9733;&nbsp; Comment participer
          </p>
          {rows_html}
        </td>
      </tr>
    </table>
"""


def _footer() -> str:
    """
    Pied de page : logo mini + séparateur doré + contacts + copyright.
    """
    year = datetime.now().year
    return f"""
    <tr>
      <td class="footer-td"
          style="background-color:#fafaf5;border-top:1px solid #f0e8c0;padding:28px 36px;">

        <!-- Logo mini -->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0"
               width="100%" style="margin-bottom:18px;">
          <tr>
            <td valign="middle" style="vertical-align:middle;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <td valign="middle" style="padding-right:10px;vertical-align:middle;">
                    <img src="{LOGO_URL}" alt="AE" width="28" height="28"
                         style="width:28px;height:28px;border-radius:7px;display:block;" />
                  </td>
                  <td valign="middle" style="vertical-align:middle;">
                    <span style="font-family:Georgia,'Times New Roman',serif;
                                 font-size:14px;font-weight:700;color:#1a1a2e;">
                      Athena Event
                    </span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>

        <!-- Séparateur -->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0"
               width="100%" style="margin-bottom:18px;">
          <tr>
            <td width="80" style="height:1px;background-color:#fde047;
                                   font-size:1px;line-height:1px;">&nbsp;</td>
            <td style="height:1px;background-color:#f0e8c0;
                       font-size:1px;line-height:1px;">&nbsp;</td>
          </tr>
        </table>

        <!-- Contacts -->
        <table role="presentation" border="0" cellpadding="0" cellspacing="0">
          <tr>
            <td width="20" valign="top" style="font-size:13px;padding-top:1px;">&#128222;</td>
            <td style="font-family:Arial,sans-serif;font-size:13px;color:#78716c;padding-bottom:6px;">
              <a href="tel:+261383204613" style="color:#78716c;text-decoration:none;">+261 38 32 046 13</a>
            </td>
          </tr>
          <tr>
            <td width="20" valign="top" style="font-size:13px;padding-top:1px;">&#128231;</td>
            <td style="font-family:Arial,sans-serif;font-size:13px;color:#78716c;padding-bottom:6px;">
              <a href="mailto:contact@clearmind-analytics.com" style="color:#78716c;text-decoration:none;">contact@clearmind-analytics.com</a>
            </td>
          </tr>
          <tr>
            <td width="20" valign="top" style="font-size:13px;padding-top:1px;">&#127760;</td>
            <td style="font-family:Arial,sans-serif;font-size:13px;color:#78716c;">
              <a href="https://www.athena-event.com" style="color:#78716c;text-decoration:none;">www.athena-event.com</a>
            </td>
          </tr>
        </table>

        <p style="margin:18px 0 0 0;font-family:Arial,sans-serif;font-size:11px;
                   color:#a8a29e;line-height:1.7;">
          &copy; {year} Athena Event by Clearmind Analytics — Antananarivo, Madagascar
        </p>

      </td>
    </tr>
"""


def _build_html(rows: str, preheader: str = "") -> str:
    """Assemble l'email complet : open + contenu + footer + close."""
    return _email_open(preheader) + rows + _footer() + _email_close()


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
    logging.info("🔔 MESSAGE REÇU SUR PUB/SUB - prod-registration-confirmed")
    logging.info("=" * 80)

    try:
        data = event.data.message.json

        logging.info("🔍 DONNÉES BRUTES REÇUES:")
        logging.info(f"   Type: {type(data)}, Champs: {len(data)}")
        logging.info("📋 TOUS LES CHAMPS:")
        for key, value in data.items():
            logging.info(f"   '{key}': '{value}' (type: {type(value).__name__})")
        logging.info("=" * 80)

    except (ValueError, AttributeError) as e:
        logging.error(f"❌ Message invalide: {e}")
        return

    email_type = data.get("type")

    if not email_type:
        logging.error("❌ Champ 'type' manquant")
        return

    logging.info(f"✅ Type détecté: {email_type}")

    # ── Validation dynamique selon le type d'email ──
    if email_type == "ACTIVATION_CODE":
        required_fields = ["type", "firstName", "code", "expiresAt", "template"]
        email_field = data.get("email", "")

    elif email_type == "ACTIVATION_LINK":
        required_fields = ["type", "userId", "email", "firstName", "lastName", "default_password", "link"]
        email_field = data.get("email", "")
        logging.info(f"📧 Email hôtesse: '{email_field}'")

    elif email_type == "RESET_PASSWORD":
        required_fields = ["type", "email", "firstName", "token", "expiresAt", "template"]
        email_field = data.get("email", "")
        logging.info(f"📧 Reset password: '{email_field}'")

    # ✅ AJOUT : Support EVENT_AWAITING_APPROVAL
    elif email_type == "EVENT_AWAITING_APPROVAL":
        email_field = data.get("adminEmail", "")
        required_fields = ["eventId", "eventTitle", "companyName", "createdAt"]

    # ✅ AJOUT : Support EVENT_APPROVED
    elif email_type == "EVENT_APPROVED":
        email_field = data.get("companyEmail", "")
        required_fields = ["companyName", "eventId", "eventTitle", "eventStartDate", "eventLocation", "approvedAt"]

    elif email_type in ["PARTICIPANT_INVITATION_KNOWN", "PARTICIPANT_INVITATION_UNKNOWN"]:
        required_fields = ["type", "companyName", "eventId", "token", "url", "template"]
        email_field = data.get("email") or data.get("companyEmail") or data.get("userEmail") or ""
        logging.info(f"📧 Email extrait: '{email_field}'")

    else:
        logging.warning(f"⚠ Type inconnu: {email_type}")
        return

    missing = [f for f in required_fields if f not in data]
    if missing:
        logging.error(f"❌ Champs manquants: {missing}")
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

    elif email_type == "RESET_PASSWORD":
        send_reset_password_email(
            email_field,
            data["firstName"],
            data["token"],
            data["expiresAt"]
        )
    # ✅ AJOUT : Dispatch EVENT_AWAITING_APPROVAL
    elif email_type == "EVENT_AWAITING_APPROVAL":
        send_event_awaiting_approval(
            email_field,
            data["eventId"],
            data["eventTitle"],
            data["companyName"],
            data["createdAt"]
        )

    # ✅ AJOUT : Dispatch EVENT_APPROVED
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


# ──────────────────────────────────────────────────────────────
# CONTENU DES EMAILS
# C'est ici que tu modifies les textes, l'ordre des blocs,
# et les données affichées dans chaque type d'email.
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
            _info_row("&#9200;", "Expire le", f"<strong>{expiry_date}</strong>"),
            label="EXPIRATION"
        )
        + _alert(
            "&#9888;&#65039; <strong>Ne partagez jamais ce code.</strong> "
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
    logging.info(f"✅ Email code activation envoyé à {email}")


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
        + _cta_button(activation_link, "&#8594; Activer mon compte")
        + _alert(
            "&#9888;&#65039; <strong>Sécurité :</strong> Vous devrez changer ce mot de passe "
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
    logging.info(f"✅ Email hôtesse envoyé à {email}")


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
            _info_row("&#9200;", "Expire le", f"<strong>{expiry_date}</strong>"),
            label="EXPIRATION"
        )
        + _alert(
            "&#128274; <strong>Consignes de sécurité :</strong><br>"
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
    logging.info(f"✅ Email reset password envoyé à {email}")


def send_event_awaiting_approval(
    admin_email: str,
    event_id: str,
    event_title: str,
    company_name: str,
    created_at: str
) -> None:
    """Envoie un email à l'admin pour notifier qu'un événement attend approbation"""
    
    info_rows = (
        _info_row("&#127881;", "Événement", f"<strong>{event_title}</strong>")
        + _info_row("&#127970;", "Organisateur", company_name)
        + _info_row("&#128197;", "Créé le", created_at)
        + _info_row("&#128278;", "Référence", f"#{event_id}")
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
            "&#9200; <strong>Action requise :</strong> Veuillez traiter cette demande "
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
    logging.info(f"✅ Email notification admin envoyé à {admin_email} pour événement {event_id}")

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
        _info_row("&#127881;", "Événement", f"<strong>{event_title}</strong>")
        + _info_row("&#128197;", "Date", event_start_date)
        + _info_row("&#128205;", "Lieu", event_location)
        + _info_row("&#9989;", "Approuvé le", approved_at)
        + _info_row("&#128278;", "Référence", f"#{event_id}")
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
            "&#127775; <strong>Prochaines étapes :</strong> Connectez-vous à votre espace "
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
    logging.info(f"✅ Email approbation événement envoyé à {company_email} pour {event_id}")


def send_participant_invitation_known(
    company_email: str, company_name: str, event_id: str, token: str, url: str
) -> None:
    confirm_url = url
    decline_url = f"{APP_BASE_URL}/api/events/{event_id}/participants/decline?token={token}"

    info_rows = (
        _info_row("&#127970;", "Entreprise invitée", f"<strong>{company_name}</strong>")
        + _info_row("&#128197;", "Date de l'invitation", datetime.now().strftime('%d %B %Y'))
        + _info_row("&#128278;", "Référence événement", f"#{event_id}")
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
        + _cta_button(confirm_url, "&#8594; Confirmer ma participation")
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
    logging.info(f"✅ Email invitation (known) envoyé à {company_email}")


def send_participant_invitation_unknown(
    company_email: str, company_name: str, event_id: str, token: str, url: str
) -> None:
    if not company_email or '@' not in company_email:
        logging.error(f"❌ Email invalide: '{company_email}'")
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
        + _cta_button(signup_url, "&#8594; Créer mon compte gratuit")
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
    logging.info(f"✅ Email invitation (unknown) envoyé à {company_email}")