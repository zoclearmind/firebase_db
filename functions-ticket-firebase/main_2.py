import base64
import json
import logging
import sys
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO

import qrcode
import functions_framework
from google.cloud import storage as gcs_storage

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(levelname)s %(asctime)s %(message)s",
    force=True
)

# Configuration Storage
storage_client = gcs_storage.Client()


# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║   ZONE DESIGN — MODIFIABLE LIBREMENT                        ║
# ║                                                              ║
# ║   Tout ce qui concerne l'apparence visuelle de l'email      ║
# ║   se trouve ICI, entre ce bloc et le bloc LOGIQUE.          ║
# ║                                                              ║
# ║   Pour modifier :                                            ║
# ║     • Logo / image hero    → section CONFIG VISUELLE        ║
# ║     • Couleurs, polices    → fonction _base_styles()        ║
# ║     • Structure du header  → fonction _hero()               ║
# ║     • Footer               → fonction _footer()             ║
# ║     • Cards, alertes       → fonctions _info_card(),        ║
# ║                              _alert(), _security_card()     ║
# ║     • Bloc QR code         → fonction _qr_block()           ║
# ║     • Textes de l'email    → fonction send_ticket_email_    ║
# ║                              with_qr(), partie "rows = ..."  ║
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
            .email-outer-td  { padding:0 !important; }
            .email-shell     { width:100% !important; min-width:100% !important;
                                border-radius:0 !important; }

            /* Hero plus compact */
            .hero-td         { height:185px !important; padding:20px 16px !important; }

            /* Logo + nom de marque : empilés verticalement */
            .logo-brand-td   { display:block !important; width:100% !important; }
            .logo-img        { width:36px !important; height:36px !important; }
            .brand-name      { font-size:17px !important; }
            .brand-sub       { font-size:9px !important; }

            /* Badge type email : passe sous le logo, aligné à gauche */
            .ref-badge-td    { display:block !important; width:100% !important;
                                text-align:left !important;
                                padding-top:10px !important; padding-left:0 !important; }
            .ref-badge-inner { text-align:left !important; }

            /* Titres hero plus petits */
            .hero-title      { font-size:17px !important; }
            .hero-sub        { font-size:11px !important; }

            /* Corps de l'email : padding réduit */
            .body-td         { padding:24px 16px 0 16px !important; }

            /* Cards : padding réduit */
            .card-td         { padding:16px !important; }

            /* Footer */
            .footer-td       { padding:22px 16px !important; }

            /* Footer : deux colonnes → empilées verticalement */
            .footer-col-l    { display:block !important; width:100% !important; }
            .footer-col-r    { display:block !important; width:100% !important;
                                text-align:left !important; padding-top:14px !important; }

            /* Note légale sous l'email */
            .below-note      { padding:0 16px !important; }

            /* QR code : taille réduite sur mobile */
            .qr-td           { padding:20px 14px !important; }
            .qr-img          { width:160px !important; height:160px !important; }
            .qr-frame-td     { padding:10px !important; }

            /* Texte des consignes de sécurité */
            .sec-text-td     { font-size:12px !important; }
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
                       Doit décrire explicitement le type d'email, ex :
                       "Confirmation d'inscription", "Billet événement", etc.
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


def _qr_block(qr_token: str = "") -> str:
    """
    Bloc QR code centré sur fond sombre.
    L'image est injectée via Content-ID (src="cid:qrcode") — pas une URL externe.
    La frame blanche autour du QR est nécessaire pour le contraste sur fond dark.
    Taille réduite à 160px sur mobile via .qr-img.
    """
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin:28px 0;">
      <tr>
        <td class="qr-td" align="center"
            style="background-color:#1a1a2e;border-radius:14px;
                   padding:28px 24px;text-align:center;border:1px solid #2d2d4a;">

          <!-- Label au-dessus du QR -->
          <p style="margin:0 0 16px 0;font-family:Arial,sans-serif;font-size:10px;
                     color:#b89000;text-transform:uppercase;letter-spacing:3px;">
            Votre code d'acc&#232;s personnel
          </p>

          <!-- Frame blanche avec bordure dorée autour du QR -->
          <table role="presentation" border="0" cellpadding="0" cellspacing="0"
                 align="center">
            <tr>
              <td class="qr-frame-td"
                  style="background-color:#ffffff;border-radius:10px;
                         padding:14px;border:2px solid #fbbf24;">
                <img class="qr-img"
                     src="cid:qrcode"
                     alt="QR Code d'acc&#232;s"
                     width="190" height="190"
                     style="width:190px;height:190px;display:block;" />
              </td>
            </tr>
          </table>

          <!-- Instruction sous le QR -->
          <p style="margin:16px 0 0 0;font-family:Arial,sans-serif;font-size:13px;
                     color:#c9a800;line-height:1.6;">
            {qr_token}
          </p>

        </td>
      </tr>
    </table>
"""


def _security_card(items: list) -> str:
    """
    Card sécurité avec puces rouges.
    items : liste de chaînes HTML décrivant chaque consigne.
    Utilise des <div> pour les puces (pas de <ul><li> — mal supportés dans Gmail).
    """
    rows_html = ""
    for item in items:
        rows_html += f"""
        <table role="presentation" border="0" cellpadding="0" cellspacing="0"
               width="100%" style="margin-bottom:8px;">
          <tr>
            <!-- Puce rouge -->
            <td valign="top" width="14"
                style="vertical-align:top;padding-top:5px;padding-right:8px;">
              <div style="width:6px;height:6px;background-color:#dc2626;
                          border-radius:50%;"></div>
            </td>
            <!-- Texte de la consigne -->
            <td class="sec-text-td" valign="top"
                style="font-family:Arial,sans-serif;font-size:13px;
                       color:#7f1d1d;line-height:1.65;vertical-align:top;">
              {item}
            </td>
          </tr>
        </table>
"""
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin:24px 0;">
      <tr>
        <td class="card-td"
            style="background-color:#fff5f5;border-radius:10px;
                   border:1px solid #fecaca;border-left-width:4px;
                   border-left-color:#dc2626;padding:20px 22px;">
          <p style="margin:0 0 14px 0;font-family:Arial,sans-serif;font-size:10px;
                     font-weight:700;color:#991b1b;text-transform:uppercase;
                     letter-spacing:2.5px;">
            &#128274; Consignes de s&#233;curit&#233; importantes
          </p>
          {rows_html}
        </td>
      </tr>
    </table>
"""


def _footer() -> str:
    """
    Pied de page : logo mini + séparateur doré + contacts + copyright.
    Deux colonnes sur desktop, empilées sur mobile.
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

        <!-- Contacts (gauche) + Copyright (droite) -->
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

      </td>
    </tr>
"""


def _build_html(rows: str, preheader: str = "") -> str:
    """Assemble l'email complet : open + contenu + footer + close."""
    return _email_open(preheader) + rows + _footer() + _email_close()


# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║   ZONE LOGIQUE — NE PAS MODIFIER SAUF DEV CONFIRMÉ          ║
# ║                                                              ║
# ║   Contient : routage Pub/Sub, validation, génération PDF,   ║
# ║              upload GCS, construction MIME, envoi SMTP.     ║
# ║   Modifier ici peut casser la livraison des emails          ║
# ║   ou la génération des badges PDF.                          ║
# ║                                                              ║
# ╚══════════════════════════════════════════════════════════════╝


# ──────────────────────────────────────────────────────────────
# BADGE ZPL — Zebra iT4S 300 DPI (11.81 dots/mm)
# Largeur : 10cm = 1181 dots  |  Hauteur : ~5.5cm = 650 dots
# Colonne texte : x=44→700    |  Colonne QR : x=700→1181
# ──────────────────────────────────────────────────────────────

LABEL_WIDTH  = 1181
LABEL_HEIGHT = 650

MAX_CHARS_PRENOM     = 12   # police 88×82
MAX_CHARS_NOM        = 13   # police 80×72
MAX_CHARS_ENTREPRISE = 21   # police 52×52
MAX_CHARS_POSTE      = 21


def _truncate(text: str, max_chars: int) -> str:
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
    nom     = _truncate(user_last_name.upper(), MAX_CHARS_NOM)
    prenom  = _truncate(user_first_name, MAX_CHARS_PRENOM)
    company = _truncate(company_name.strip().upper(), MAX_CHARS_ENTREPRISE) if company_name and company_name.strip() and company_name.strip() != "N/A" else ""
    role    = _truncate(user_role.strip(), MAX_CHARS_POSTE)                 if user_role    and user_role.strip()    and user_role.strip()    != "N/A" else ""

    company_line = f"\n^FO44,338^A0N,52,52^FD{company}^FS" if company else ""
    role_line    = f"\n^FO44,400^A0N,52,52^FD{role}^FS"    if role    else ""

    return (
        f"^XA"
        f"^PW{LABEL_WIDTH}"
        f"^LL{LABEL_HEIGHT}"
        f"^CI28"
        f"^FO44,100^A0N,88,82^FD{prenom}^FS"                          # Prénom — en haut
        f"^FO44,220^A0N,80,72^FD{nom}^FS"                             # Nom — en dessous
        f"{company_line}"
        f"{role_line}"
        f"^FO700,60^BQN,2,20^FDQA,{qr_token}^FS"                     # QR code — module 20 dots
        f"^FO700,560^A0N,34,34^FB437,1,0,C^FD{qr_token}^FS"          # Token centré sous QR
        f"^XZ"
    )


# ──────────────────────────────────────────────────────────────
# POINT D'ENTRÉE CLOUD FUNCTION
# ──────────────────────────────────────────────────────────────

@functions_framework.http
def process_email(request):
    logging.info("=" * 80)
    logging.info("🎫 MESSAGE REÇU SUR PUB/SUB - email-notifications")
    logging.info("=" * 80)

    try:
        envelope = request.get_json(silent=True)
        if not envelope or "message" not in envelope:
            logging.error("❌ Envelope Pub/Sub invalide")
            return ("Bad Request: envelope invalide", 400)

        pubsub_message = envelope["message"]

        if "data" in pubsub_message:
            raw = base64.b64decode(pubsub_message["data"]).decode("utf-8")
            data = json.loads(raw)
        else:
            logging.error("❌ Champ 'data' absent")
            return ("Bad Request: data absent", 400)

        logging.info(f"Contenu: {json.dumps(data, indent=2)}")

    except Exception as e:
        logging.error(f"❌ Erreur lecture données: {e}")
        return (f"Bad Request: {e}", 400)

    if "type" not in data:
        logging.error("❌ Champ 'type' manquant")
        return ("Bad Request: champ 'type' manquant", 400)

    # ✅ ACCEPTER LES TROIS TYPES
    ACCEPTED_TYPES = [
        "EVENT_REGISTRATION_CONFIRMED",
        "RESEND_REGISTRATION_CONFIRMED",
        "RESEND_REGISTRATION_CONFIRMED_INVITED",
    ]
    if data["type"] not in ACCEPTED_TYPES:
        logging.warning(f"⚠ Type incorrect: {data['type']}")
        return ("Bad Request: type incorrect", 400)

    # ── Dispatch : billet invité ──────────────────────────────────
    if data["type"] == "RESEND_REGISTRATION_CONFIRMED_INVITED":
        invited_required = [
            "registrationId", "emailDestinateur",
            "userDestinateurFirstName", "userDestinateurLastName",
            "userPropretaireBadgeLastName", "userPropretaireBadgeFistName",
            "eventTitle", "eventStartDate", "eventLocation", "qrCodeToken",
        ]
        missing_invited = [f for f in invited_required if f not in data]
        if missing_invited:
            logging.error(f"❌ Champs manquants (invited): {missing_invited}")
            return (f"Bad Request: champs manquants {missing_invited}", 400)

        try:
            qr_token = data["qrCodeToken"]
            qr_img = qrcode.make(qr_token, box_size=10, border=2)
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format="PNG")
            qr_buffer.seek(0)
            qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')

            logging.info(f"🎫 Billet invité → {data['emailDestinateur']} (badge: {data['userPropretaireBadgeFistName']} {data['userPropretaireBadgeLastName']})")

            send_ticket_email_invited(
                email=data["emailDestinateur"],
                destinateur_first_name=data["userDestinateurFirstName"],
                destinateur_last_name=data["userDestinateurLastName"],
                badge_owner_first_name=data["userPropretaireBadgeFistName"],
                badge_owner_last_name=data["userPropretaireBadgeLastName"],
                event_title=data["eventTitle"],
                event_start=data["eventStartDate"],
                event_location=data["eventLocation"],
                qr_base64=qr_base64,
                registration_id=data["registrationId"],
                qr_token=qr_token,
            )
            return ("OK", 200)
        except Exception as e:
            logging.error(f"❌ Échec billet invité: {str(e)}")
            return (f"Internal Server Error: {str(e)}", 500)

    # ── Validation (types classiques) ────────────────────────────
    classic_required = [
        "registrationId", "userId", "eventId",
        "userEmail", "userFirstName", "userLastName",
        "eventTitle", "eventStartDate", "eventLocation", "qrCodeToken"
    ]
    missing = [f for f in classic_required if f not in data]
    if missing:
        logging.error(f"❌ Champs manquants: {missing}")
        return (f"Bad Request: champs manquants {missing}", 400)

    # ── Extraction ───────────────────────────────────────────────
    registration_id = data["registrationId"]
    user_email      = data["userEmail"]
    user_first_name = data["userFirstName"]
    user_last_name  = data["userLastName"]
    event_title     = data["eventTitle"]
    event_start     = data["eventStartDate"]
    event_location  = data["eventLocation"]
    event_id = data["eventId"]  # déjà présent ✅
    qr_token        = data["qrCodeToken"]
    # company_name    = data["companyName"]
    # user_role       = data["userRole"]
    company_name    = data.get("companyName", "N/A")
    user_role       = data.get("userRole", "Participant")

    logging.info(f"🎫 Billet pour {user_email} - {event_title}")

    try:
        # Générer QR code
        qr_img = qrcode.make(qr_token, box_size=10, border=2)
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode('utf-8')
        qr_buffer.seek(0)

        # ✅ CONDITION : GÉNÉRER BADGE SEULEMENT SI PREMIER ENVOI OU BADGE ABSENT
        bucket_name = "event-athena-prod-plaform.firebasestorage.app"
        badge_blob = storage_client.bucket(bucket_name).blob(f"tickets/{event_id}/{qr_token}.zpl")
        badge_exists = badge_blob.exists()

        logging.info(f"🔍 Badge existant dans GCS: {badge_exists}")

        if data["type"] == "EVENT_REGISTRATION_CONFIRMED" or not badge_exists:
            logging.info("📄 Génération badge ZPL (premier envoi ou badge absent)...")

            zpl_content = _build_zpl(
                qr_token=qr_token,
                user_first_name=user_first_name,
                user_last_name=user_last_name,
                company_name=company_name,
                user_role=user_role,
            )
            logging.info("✅ Badge ZPL généré")

            # ── Upload GCS ────────────────────────────────────────────
            logging.info(f"🪣 Bucket cible: {bucket_name}")
            try:
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(f"tickets/{event_id}/{qr_token}.zpl")
                blob.upload_from_string(zpl_content.encode("utf-8"), content_type="text/plain; charset=utf-8")
                logging.info(f"✅ Upload OK: tickets/{event_id}/{qr_token}.zpl")
            except Exception as upload_err:
                logging.error(f"❌ Erreur upload GCS: {upload_err}")
                raise

        else:
            logging.info("🔄 Retry détecté (RESEND_REGISTRATION_CONFIRMED) → Skip génération badge")

        # ── Envoi email ───────────────────────────────────────────────
        send_ticket_email_with_qr(
            user_email, user_first_name, user_last_name,
            event_title, event_start, event_location,
            qr_base64, registration_id, qr_token
        )

        return ("OK", 200)

    except Exception as e:
        logging.error(f"❌ Échec génération/envoi billet: {str(e)}")
        return (f"Internal Server Error: {str(e)}", 500)


# ──────────────────────────────────────────────────────────────
# CONTENU DE L'EMAIL
# C'est ici que tu modifies les textes, l'ordre des blocs,
# et les données affichées dans l'email de confirmation.
# ──────────────────────────────────────────────────────────────

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
        + _info_card(info_rows, label="DÉTAILS DE VOTRE INSCRIPTION")
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

Présentez votre QR code personnel à l'entrée de l'événement.

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

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logging.info(f"✅ Email billet envoyé à {email}")
    except Exception as e:
        logging.error(f"❌ Erreur envoi email : {e}")
        raise


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
    """
    SMTP_HOST     = os.environ.get("SMTP_HOST", "smtp.zeptomail.com")
    SMTP_PORT     = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER     = os.environ.get("SMTP_USER", "noreply@athena-event.com")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

    if not all([SMTP_USER, SMTP_PASSWORD]):
        logging.error("Variables SMTP manquantes")
        raise ValueError("Configuration SMTP incomplète")

    badge_owner_full = f"{badge_owner_first_name} {badge_owner_last_name}"

    info_rows = (
        _info_row("&#128100;", "Participant",  badge_owner_full)
        + _info_row("&#127881;", "Événement",  f"<strong>{event_title}</strong>")
        + _info_row("&#128197;", "Date",        event_start)
        + _info_row("&#128205;", "Lieu",        event_location)
    )

    security_items = [
        f"Ce billet est au nom de <strong>{badge_owner_full}</strong>",
        "<strong>Ne partagez pas ce QR code</strong> en dehors de la personne concernée",
        "Ce code est <strong>strictement personnel</strong> et identifie le participant de manière unique",
        "Toute personne en possession de ce code peut accéder à l'événement à sa place",
        "En cas de perte ou de vol, <strong>contactez-nous immédiatement</strong>",
    ]

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
        + _info_card(info_rows, label="DÉTAILS DE L'INSCRIPTION")
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
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logging.info(f"✅ Email billet invité envoyé à {email} (billet: {badge_owner_full})")
    except Exception as e:
        logging.error(f"❌ Erreur envoi email : {e}")
        raise