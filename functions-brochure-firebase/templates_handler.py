"""
Gestion des templates HTML : chargement, rendu, remplacement de variables.
"""
import os
import re
from config import TEMPLATES
from attachments import is_pdf_url


def load_template(template_num):
    """
    Charge le template HTML depuis le fichier.
    Paramètre : template_num (int) — 1, 2, 3 ou 4
    Retourne : string HTML
    """
    template_file = TEMPLATES.get(template_num)
    if not template_file:
        raise ValueError(f"Template numéro {template_num} non trouvé. Utilisez 1, 2, 3 ou 4.")
    
    template_path = os.path.join(os.path.dirname(__file__), "templates", template_file)
    
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def render_template(template_html, data):
    """
    Remplace les variables {{variable}} dans le template HTML.
    Paramètre : template_html (string), data (dict)
    Retourne : string HTML rendu
    """
    rendered = template_html
    
    # ── Variables simples ──
    rendered = rendered.replace("{{firstName}}", data.get("firstName", ""))
    rendered = rendered.replace("{{lastName}}", data.get("lastName", ""))
    rendered = rendered.replace("{{company_name}}", data.get("company_name", ""))
    rendered = rendered.replace("{{company_email}}", data.get("company_email", ""))
    
    # ── Contenu personnalisé (avec fallback) ──
    custom_content = data.get("customContent", "")
    if custom_content is None or custom_content.strip() == "":
        if data.get("type") == "EVENT_REGISTRATION_REQUEST_SECOND_CONFIRMATION":
            custom_content = (
                "Veuillez confirmer ou refuser votre présence à l'événement ci-dessous. "
                "Votre réponse sera enregistrée immédiatement."
            )
        else:
            event_name = data.get("event_name", "l'événement")
            custom_content = f"Merci pour cet échange enrichissant lors de {event_name} ! N'hésitez pas à nous contacter pour toute question ou besoin d'information complémentaire."
    rendered = rendered.replace("{{customContent}}", custom_content)

    # ── Valeurs par défaut pour l'image d'événement et le nom d'événement ──
    data["eventImageUrl"] = data.get("eventImageUrl") or "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=600&q=80&auto=format&fit=crop"
    data["event_name"] = data.get("event_name", "Événement Athena")

    # ── Remplacer les variables de l'événement et de confirmation ──
    extra_fields = {
        "confirmationLink": data.get("confirmationLink", "#"),
        "declineLink": data.get("declineLink", "#"),
        "event_name": data.get("event_name", ""),
        "eventTitle": data.get("eventTitle") or data.get("event_name") or "Événement Athena",
        "eventStartDate": data.get("eventStartDate", ""),
        "eventEndDate": data.get("eventEndDate", ""),
        "eventDescription": data.get("eventDescription", ""),
        "eventCapacity": data.get("eventCapacity", ""),
        "limitDaySuggestion": data.get("limitDaySuggestion", ""),
        "eventImageUrl": data.get("eventImageUrl", "")
    }
    for key, value in extra_fields.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value or ""))
    
    # ── Logo (URL directe, pas inline) ──
    company_logo = data.get("company_logo", "")
    if company_logo is None or company_logo.strip() == "":
        company_logo = "https://via.placeholder.com/140x40/2563eb/ffffff?text=Logo"
    rendered = rendered.replace("{{company_logo}}", company_logo)
    
    # ── Gestion des pièces jointes ──
    attachment_urls = data.get("attachmentUrls")
    if attachment_urls is None:
        attachment_urls = []
    
    # Décider si on cache la section visuelle des pièces jointes
    has_pdfs = any(is_pdf_url(url) for url in (attachment_urls or []) if url)
    if has_pdfs or not attachment_urls or len(attachment_urls) == 0:
        # Supprimer la section pièces jointes du HTML
        pattern = r'<!-- ATTACHMENTS_SECTION_START -->.*?<!-- ATTACHMENTS_SECTION_END -->'
        rendered = re.sub(pattern, '', rendered, flags=re.DOTALL)
    
    # Remplacer les placeholders d'URLs d'attachments (images)
    for i in range(10):
        placeholder = f"{{{{attachmentUrls[{i}]}}}}"
        if i < len(attachment_urls) and attachment_urls[i]:
            if is_pdf_url(attachment_urls[i]):
                # Data URI pour icône PDF grise
                pdf_placeholder = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='400' viewBox='0 0 600 400'%3E%3Crect width='600' height='400' fill='%23f3f4f6'/%3E%3Ctext x='300' y='200' font-family='Arial' font-size='20' fill='%236b7280' text-anchor='middle'%3EDocument PDF%3C/text%3E%3C/svg%3E"
                rendered = rendered.replace(placeholder, pdf_placeholder)
            else:
                # Pour images, utiliser l'URL directe
                rendered = rendered.replace(placeholder, attachment_urls[i])
        else:
            # Utiliser une data URI vide
            empty_placeholder = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='400'/%3E"
            rendered = rendered.replace(placeholder, empty_placeholder)
    
    # ── Générer liste HTML des PDFs ──
    if attachment_urls and len(attachment_urls) > 0:
        pdf_list_html = _build_pdf_list(attachment_urls)
        rendered = rendered.replace("{{PDF_LIST}}", pdf_list_html)
    else:
        rendered = rendered.replace("{{PDF_LIST}}", "")
    
    return rendered


def _build_pdf_list(attachment_urls):
    """
    Construit la liste HTML des PDFs dynamiquement.
    Retourne : string HTML
    """
    pdf_list_html = ""
    pdf_count = 0
    
    for i, url in enumerate(attachment_urls):
        if is_pdf_url(url):
            pdf_count += 1
            # Extraire le nom du fichier depuis l'URL
            filename = url.split('/')[-1].split('?')[0]
            if not filename.endswith('.pdf'):
                filename = f"Document_{pdf_count}.pdf"
            
            # Icône selon la position
            icon = "📄" if pdf_count == 1 else "💰"
            title = filename.replace('.pdf', '').replace('_', ' ').title()
            
            pdf_list_html += f"""
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom: 12px;">
                <tr>
                    <td style="padding: 15px 20px; background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px;">
                        <table width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td width="40" valign="middle">
                                    <div style="width: 36px; height: 36px; background-color: #2563eb; border-radius: 6px; text-align: center; line-height: 36px;">
                                        <span style="color: #ffffff; font-size: 16px;">{icon}</span>
                                    </div>
                                </td>
                                <td style="padding-left: 15px;">
                                    <div style="font-size: 15px; font-weight: 600; color: #111827;">
                                        {title}
                                    </div>
                                    <div style="font-size: 13px; color: #6b7280;">
                                        Document PDF • En pièce jointe
                                    </div>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
            """
    
    return pdf_list_html
