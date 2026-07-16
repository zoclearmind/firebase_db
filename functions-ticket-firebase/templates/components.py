# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║   ZONE DESIGN — COMPOSANTS VISUELS                          ║
# ║                                                              ║
# ║   Identité Athena Event : navy #163057 / doré #c7a253,      ║
# ║   titres Georgia, corps Arial.                               ║
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

def _hero(title: str, subtitle: str, email_type_label: str = "", hero_image_url: str = "") -> str:
    """
    Bandeau hero navy : logo + marque à gauche, badge doré à droite,
    filet doré, titre Georgia et sous-titre.

    email_type_label : texte affiché dans le badge en haut à droite du hero.
    hero_image_url   : image de fond personnalisée (ex: image de l'événement).
                       Si vide, utilise HERO_IMAGE_URL par défaut.

    Technique image de fond :
      - background-image CSS avec voile navy → Gmail, Apple Mail, Samsung Mail
        (le voile foncé garantit la lisibilité et l'unité de marque)
      - Outlook Windows → fond navy uni via les commentaires conditionnels
        (pas d'image : le texte reste toujours lisible)
    """
    bg_url = hero_image_url or HERO_IMAGE_URL
    badge_col = ""
    if email_type_label:
        badge_col = f"""
            <td class="ref-badge-td" valign="middle" align="right"
                style="vertical-align:middle;padding-left:12px;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0"
                     align="right">
                <tr>
                  <td class="ref-badge-inner"
                      style="background-color:#122748;border:1px solid #c7a253;
                             border-radius:20px;padding:7px 16px;text-align:right;">
                    <div style="font-family:Arial,sans-serif;font-size:10px;
                                font-weight:700;color:#d9b979;letter-spacing:1.5px;
                                text-transform:uppercase;line-height:1.3;">
                      {email_type_label}
                    </div>
                  </td>
                </tr>
              </table>
            </td>"""

    cols = 2 if email_type_label else 1

    return f"""
    <!--[if mso | IE]>
    <tr><td style="background-color:#163057;padding:32px 36px 30px 36px;">
    <![endif]-->
    <!--[if !mso]><!-->
    <tr>
      <td class="hero-td"
          style="background-color:#163057;
                 background-image:linear-gradient(rgba(22,48,87,0.78),rgba(18,39,72,0.86)),url('{bg_url}');
                 background-size:cover;background-position:center center;
                 background-repeat:no-repeat;
                 padding:32px 36px 30px 36px;">
    <!--<![endif]-->

        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">

          <!-- Ligne 1 : Logo + marque + badge type email -->
          <tr>
            <td class="logo-brand-td" valign="middle" style="vertical-align:middle;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <td valign="middle" style="padding-right:12px;vertical-align:middle;">
                    <img class="logo-img" src="{LOGO_URL}" alt="Athena Event"
                         width="40" height="40"
                         style="width:40px;height:40px;border-radius:10px;
                                border:1px solid #c7a253;display:block;" />
                  </td>
                  <td valign="middle" style="vertical-align:middle;">
                    <div class="brand-name"
                         style="font-family:Georgia,'Times New Roman',serif;
                                font-size:19px;color:#ffffff;
                                line-height:1.2;margin:0;letter-spacing:.5px;">
                      Athena Event
                    </div>
                    <div class="brand-sub"
                         style="font-family:Arial,sans-serif;font-size:9px;
                                color:#9fb0c9;letter-spacing:2.5px;
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
            <td colspan="{cols}" style="height:24px;font-size:1px;line-height:1px;">&nbsp;</td>
          </tr>

          <!-- Ligne 2 : Filet doré + titre + sous-titre -->
          <tr>
            <td colspan="{cols}">
              <div style="width:44px;height:2px;background-color:#c7a253;
                          margin-bottom:14px;font-size:0;line-height:2px;">&nbsp;</div>
              <div class="hero-title"
                   style="font-family:Georgia,'Times New Roman',serif;
                          font-size:25px;color:#ffffff;
                          line-height:31px;margin:0;">
                {title}
              </div>
              <div class="hero-sub"
                   style="font-family:Arial,sans-serif;font-size:13px;
                          color:#d7deea;margin-top:8px;letter-spacing:.3px;
                          line-height:1.5;">
                {subtitle}
              </div>
            </td>
          </tr>

        </table>

    <!--[if mso | IE]></td></tr><![endif]-->
    <!--[if !mso]><!-->
      </td>
    </tr>
    <!--<![endif]-->

    <!-- Filet doré accent sous le hero -->
    <tr>
      <td style="height:3px;font-size:3px;line-height:3px;
                 background-color:#c7a253;">&nbsp;</td>
    </tr>
"""


def _body_open(greeting: str, intro: str) -> str:
    """Ouvre la zone de contenu : salutation + paragraphe d'introduction."""
    return f"""
    <tr>
      <td class="body-td" style="padding:36px 40px 0 40px;">
        <p style="margin:0 0 10px 0;font-family:Georgia,'Times New Roman',serif;
                  font-size:20px;color:#163057;line-height:1.35;">
          {greeting}
        </p>
        <p style="margin:0 0 24px 0;font-family:Arial,sans-serif;
                  font-size:15px;color:#3b4453;line-height:1.75;">
          {intro}
        </p>
"""


def _body_close(sign_off: str = "Cordialement,") -> str:
    """Ferme la zone de contenu : filet doré + signature."""
    return f"""
        <table role="presentation" border="0" cellpadding="0" cellspacing="0"
               width="100%" style="margin-top:32px;">
          <tr>
            <td width="44" style="height:2px;background-color:#c7a253;
                                   font-size:1px;line-height:1px;">&nbsp;</td>
            <td style="height:1px;background-color:#ffffff;
                       font-size:1px;line-height:1px;">&nbsp;</td>
          </tr>
        </table>
        <p style="margin:18px 0 0 0;font-family:Arial,sans-serif;
                  font-size:15px;color:#3b4453;line-height:1.7;">
          {sign_off}
        </p>
        <p style="margin:4px 0 0 0;font-family:Georgia,'Times New Roman',serif;
                  font-size:16px;color:#163057;">
          L'équipe Athena Event
        </p>
      </td>
    </tr>
    <tr><td style="height:36px;font-size:1px;line-height:1px;">&nbsp;</td></tr>
"""


def _info_card(rows_html: str, label: str = "DÉTAILS") -> str:
    """
    Carte blanche à liseré doré (même langage visuel que les cartes
    de mise en relation Athena).
    rows_html : lignes générées par _info_row()
    label     : titre de la card en petites capitales dorées
    """
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin:24px 0;">
      <tr>
        <td class="card-td"
            style="background-color:#ffffff;border:1px solid #e6e9ef;
                   border-radius:10px;padding:20px 22px;">
          <p style="margin:0 0 14px 0;font-family:Arial,sans-serif;font-size:11px;
                     font-weight:700;color:#c7a253;text-transform:uppercase;
                     letter-spacing:2px;">
            {label}
          </p>
          {rows_html}
        </td>
      </tr>
    </table>
"""


def _info_row(icon: str, label: str, value: str) -> str:
    """
    Ligne d'information "Label : valeur".
    Utilise une table pour l'alignement (flex non supporté dans tous les clients email).
    icon : conservé pour compatibilité — laisser vide de préférence
           (les emojis se rendent différemment selon les clients).
    """
    icon_cell = f"""
        <td valign="top" width="22"
            style="font-family:Arial,sans-serif;font-size:14px;
                   color:#5a6577;padding-top:1px;vertical-align:top;">
          {icon}
        </td>""" if icon else ""
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin-bottom:10px;">
      <tr>
        {icon_cell}
        <td valign="top" style="font-family:Arial,sans-serif;font-size:14px;
                                 color:#3b4453;line-height:1.55;vertical-align:top;">
          <strong style="color:#163057;">{label}&nbsp;:</strong> {value}
        </td>
      </tr>
    </table>
"""


def _qr_block(qr_token: str = "") -> str:
    """
    Bloc QR code centré sur fond navy profond.
    L'image est injectée via Content-ID (src="cid:qrcode") — pas une URL externe.
    La frame blanche autour du QR est nécessaire pour le contraste sur fond sombre.
    Taille réduite à 160px sur mobile via .qr-img.
    """
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin:28px 0;">
      <tr>
        <td class="qr-td" align="center"
            style="background-color:#122748;border-radius:12px;
                   padding:28px 24px;text-align:center;">

          <!-- Label au-dessus du QR -->
          <p style="margin:0 0 6px 0;font-family:Arial,sans-serif;font-size:10px;
                     font-weight:700;color:#c7a253;text-transform:uppercase;
                     letter-spacing:3px;">
            Votre code d'acc&#232;s personnel
          </p>
          <table role="presentation" border="0" cellpadding="0" cellspacing="0" align="center">
            <tr><td style="width:36px;height:2px;background-color:#c7a253;
                            font-size:0;line-height:2px;">&nbsp;</td></tr>
          </table>

          <!-- Frame blanche avec liseré doré autour du QR -->
          <table role="presentation" border="0" cellpadding="0" cellspacing="0"
                 align="center" style="margin-top:16px;">
            <tr>
              <td class="qr-frame-td"
                  style="background-color:#ffffff;border-radius:10px;
                         padding:14px;border:1px solid #c7a253;">
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
                     color:#d7deea;line-height:1.6;">
            {qr_token}
          </p>

        </td>
      </tr>
    </table>
"""


def _security_card(items: list) -> str:
    """
    Card sécurité : fond rosé discret, puces assorties.
    items : liste de chaînes HTML décrivant chaque consigne.
    Utilise des <div> pour les puces (pas de <ul><li> — mal supportés dans Gmail).
    """
    rows_html = ""
    for item in items:
        rows_html += f"""
        <table role="presentation" border="0" cellpadding="0" cellspacing="0"
               width="100%" style="margin-bottom:8px;">
          <tr>
            <!-- Puce brique -->
            <td valign="top" width="14"
                style="vertical-align:top;padding-top:6px;padding-right:8px;">
              <div style="width:5px;height:5px;background-color:#b3564d;
                          border-radius:50%;font-size:0;line-height:5px;">&nbsp;</div>
            </td>
            <!-- Texte de la consigne -->
            <td class="sec-text-td" valign="top"
                style="font-family:Arial,sans-serif;font-size:13px;
                       color:#8c4640;line-height:1.65;vertical-align:top;">
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
            style="background-color:#fbf1f0;border-radius:10px;
                   padding:20px 22px;">
          <p style="margin:0 0 14px 0;font-family:Arial,sans-serif;font-size:11px;
                     font-weight:700;color:#b3564d;text-transform:uppercase;
                     letter-spacing:2px;">
            Consignes de s&#233;curit&#233; importantes
          </p>
          {rows_html}
        </td>
      </tr>
    </table>
"""


def _footer() -> str:
    """
    Pied de page navy : devise, contacts, copyright — centrés.
    """
    year = datetime.now().year
    return f"""
    <tr>
      <td class="footer-td"
          style="background-color:#122748;padding:28px 36px;text-align:center;">

        <div style="font-family:Georgia,'Times New Roman',serif;font-style:italic;
                    font-size:14px;color:#c7d0df;padding-bottom:14px;">
          Connect. Measure. Grow.
        </div>

        <table role="presentation" border="0" cellpadding="0" cellspacing="0" align="center">
          <tr><td style="width:36px;height:1px;background-color:#c7a253;
                          font-size:0;line-height:1px;">&nbsp;</td></tr>
        </table>

        <div style="font-family:Arial,sans-serif;font-size:12px;color:#8ea0bb;
                    padding-top:14px;padding-bottom:12px;line-height:1.9;">
          <a href="tel:+261383204613" style="color:#c7d0df;text-decoration:none;">+261 38 32 046 13</a>
          &nbsp;<span style="color:#c7a253;">&middot;</span>&nbsp;
          <a href="mailto:sales@athena-event.com" style="color:#c7d0df;text-decoration:none;">sales@athena-event.com</a>
          &nbsp;<span style="color:#c7a253;">&middot;</span>&nbsp;
          <a href="https://www.athena-event.com" style="color:#c7d0df;text-decoration:none;">www.athena-event.com</a>
        </div>

        <div style="font-family:Arial,sans-serif;font-size:11px;line-height:16px;
                    color:#6f83a0;">
          &copy; {year} Athena Event by Clearmind Analytics &mdash; Antananarivo, Madagascar
        </div>

      </td>
    </tr>
"""


def _build_html(rows: str, preheader: str = "") -> str:
    """Assemble l'email complet : open + contenu + footer + close."""
    return _email_open(preheader) + rows + _footer() + _email_close()
