# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║   ZONE DESIGN — COMPOSANTS VISUELS                          ║
# ║                                                              ║
# ║   Pour modifier :                                            ║
# ║     • Logo / image hero    → config.py                      ║
# ║     • Couleurs, polices    → templates/base.py              ║
# ║     • Structure du header  → _hero()                        ║
# ║     • Footer               → _footer()                      ║
# ║     • Cards, boutons       → _info_card(), _cta_button(),   ║
# ║                              _alert()                       ║
# ║     • Contenu d'un email   → email_senders.py               ║
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
    Bandeau hero avec image de fond, logo, nom de marque.

    email_type_label : texte affiché dans le badge en haut à droite du hero.
    hero_image_url   : image de fond personnalisée (ex: image de l'événement).
                       Si vide, utilise HERO_IMAGE_URL par défaut.

    Technique image de fond :
      - background-image CSS  → Gmail, Apple Mail, Samsung Mail
      - attribut background=  → clients anciens
      - VML v:rect            → Outlook Windows (commentaires conditionnels)
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
          background="{bg_url}"
          style="background-color:#1a1a2e;
                 background-image:linear-gradient(rgba(0,0,0,0.55),rgba(0,0,0,0.55)),url('{bg_url}');
                 background-size:cover;background-position:center center;
                 background-repeat:no-repeat;
                 padding:28px 32px;height:200px;vertical-align:middle;">

        <!--[if mso | IE]>
        <v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false"
                style="width:680px;height:200px;position:absolute;">
          <v:fill type="frame" src="{bg_url}" color="#1a1a2e"/>
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
                   border:1px solid #fde68a;padding:20px 22px;">
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
    icon_cell = f"""
        <td valign="top" width="22"
            style="font-family:Arial,sans-serif;font-size:14px;
                   color:#57534e;padding-top:1px;vertical-align:top;">
          {icon}
        </td>""" if icon else ""
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin-bottom:10px;">
      <tr>
        {icon_cell}
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
        <td style="background-color:{bg};border-radius:8px;padding:14px 16px;">
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
                   border:1px solid #fde68a;padding:20px 22px;">
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
              <a href="mailto:sales@athena-event.com" style="color:#78716c;text-decoration:none;">sales@athena-event.com</a>
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
