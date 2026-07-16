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


def _cta_button(url: str, label: str) -> str:
    """
    Bouton call-to-action centré : navy, texte blanc, coins arrondis.
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
                       arcsize="16%" strokecolor="#163057" strokeweight="1pt"
                       fillcolor="#163057">
            <w:anchorlock/>
            <center style="color:#ffffff;font-family:Arial,sans-serif;
                           font-size:15px;font-weight:bold;">
              {label}
            </center>
          </v:roundrect>
          <![endif]-->
          <!--[if !mso]><!-->
          <a href="{url}" class="cta-link" target="_blank"
             style="display:inline-block;background-color:#163057;
                    color:#ffffff;font-family:Arial,sans-serif;font-size:15px;
                    font-weight:700;letter-spacing:.5px;text-decoration:none;
                    border-radius:8px;padding:15px 40px;mso-hide:all;">
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
           width="100%" style="margin:10px 0 0 0;">
      <tr>
        <td align="center">
          <a href="{url}" target="_blank"
             style="font-family:Arial,sans-serif;font-size:13px;
                    color:#5a6577;text-decoration:underline;">
            {label}
          </a>
        </td>
      </tr>
    </table>
"""


def _alert(content: str, variant: str = "warning") -> str:
    """
    Encadré discret.
    variant = "warning" → fond ivoire (note, conseil)
    variant = "danger"  → fond rosé (sécurité, vigilance)
    """
    styles = {
        "warning": ("#faf6ec", "#6d5a35"),
        "danger":  ("#fbf1f0", "#8c4640"),
    }
    bg, color = styles.get(variant, styles["warning"])
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin:20px 0;">
      <tr>
        <td style="background-color:{bg};border-radius:8px;padding:14px 18px;">
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
    Bloc navy profond avec un code en grand centré.
    Réutilisé pour l'activation de compte ET le reset password.
    label : texte au-dessus du code (modifiable selon le contexte)
    """
    return f"""
    <table role="presentation" border="0" cellpadding="0" cellspacing="0"
           width="100%" style="margin:28px 0;">
      <tr>
        <td class="code-block-td" align="center"
            style="background-color:#122748;border-radius:12px;
                   padding:28px 32px;text-align:center;">
          <p style="margin:0 0 6px 0;font-family:Arial,sans-serif;font-size:10px;
                     font-weight:700;color:#c7a253;text-transform:uppercase;
                     letter-spacing:3px;">
            {label}
          </p>
          <table role="presentation" border="0" cellpadding="0" cellspacing="0" align="center">
            <tr><td style="width:36px;height:2px;background-color:#c7a253;
                            font-size:0;line-height:2px;">&nbsp;</td></tr>
          </table>
          <p class="code-val"
             style="margin:14px 0 0 0;font-family:'Courier New',Courier,monospace;
                    font-size:38px;font-weight:700;color:#ffffff;
                    letter-spacing:12px;line-height:1;">
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
            <td valign="top" width="38" style="vertical-align:top;padding-top:1px;">
              <table role="presentation" border="0" cellpadding="0" cellspacing="0">
                <tr>
                  <td width="28" height="28" align="center" valign="middle"
                      style="width:28px;height:28px;border-radius:50%;
                             background-color:#163057;text-align:center;
                             font-family:Georgia,'Times New Roman',serif;font-size:14px;
                             color:#ffffff;line-height:28px;">
                    {i}
                  </td>
                </tr>
              </table>
            </td>
            <td valign="top"
                style="font-family:Arial,sans-serif;font-size:14px;
                       color:#5a6577;line-height:1.6;vertical-align:top;
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
            style="background-color:#ffffff;border:1px solid #e6e9ef;
                   border-radius:10px;padding:20px 22px;">
          <p style="margin:0 0 16px 0;font-family:Arial,sans-serif;font-size:11px;
                     font-weight:700;color:#c7a253;text-transform:uppercase;
                     letter-spacing:2px;">
            Comment participer
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
