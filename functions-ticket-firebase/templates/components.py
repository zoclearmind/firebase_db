# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║   ZONE DESIGN — COMPOSANTS VISUELS                          ║
# ║                                                              ║
# ║   Pour modifier :                                            ║
# ║     • Logo / image hero    → config.py                      ║
# ║     • Couleurs, polices    → templates/base.py              ║
# ║     • Structure du header  → _hero()                        ║
# ║     • Footer               → _footer()                      ║
# ║     • Cards, alertes       → _info_card(), _alert(),        ║
# ║                              _security_card()               ║
# ║     • Bloc QR code         → _qr_block()                    ║
# ║     • Textes de l'email    → email_sender.py                ║
# ║                                                              ║
# ╚══════════════════════════════════════════════════════════════╝

from datetime import datetime

from config import HERO_IMAGE_URL, LOGO_URL
from templates.base import _email_open, _email_close


# ──────────────────────────────────────────────────────────────
# COMPOSANTS VISUELS
# ──────────────────────────────────────────────────────────────

def _hero(title: str, subtitle: str, email_type_label: str = "") -> str:
    """
    Bandeau hero avec image de fond, logo, nom de marque.

    email_type_label : texte affiché dans le badge en haut à droite du hero.
                       Décrit explicitement le type d'email.
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
