# ╔══════════════════════════════════════════════════════════════╗
# ║                                                              ║
# ║   ZONE DESIGN — STRUCTURE HTML & STYLES CSS                 ║
# ║                                                              ║
# ║   Contient l'enveloppe HTML de tous les emails :            ║
# ║     • Styles CSS (_base_styles)                             ║
# ║     • Preheader invisible (_preheader)                      ║
# ║     • Ouverture / fermeture du document (_email_open/close) ║
# ║                                                              ║
# ╚══════════════════════════════════════════════════════════════╝


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
