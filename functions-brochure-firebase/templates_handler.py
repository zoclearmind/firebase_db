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
        raise ValueError(f"Template numéro {template_num} non trouvé. Utilisez un numéro de 1 à 6.")
    
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

    # ── Champs du template remerciement (EVENT_THANK_YOU) ──
    thank_you_fields = {
        "greetingPrefix": data.get("greetingPrefix", "Bonjour"),
        "toFirstName": data.get("toFirstName", ""),
        "toLastName": data.get("toLastName", ""),
        "title": data.get("title", ""),
        "bodyParagraph1": data.get("bodyParagraph1", ""),
        "bodyParagraph2": data.get("bodyParagraph2", ""),
        "eventDateRange": data.get("eventDateRange", ""),
        "eventLocation": data.get("eventLocation", ""),
        "footerQuote": data.get("footerQuote", ""),
        "footerOrganizers": data.get("footerOrganizers", ""),
        "footerOrganizations": data.get("footerOrganizations", ""),
        "footerPatronage": data.get("footerPatronage", ""),
        "websiteUrl": data.get("websiteUrl", "#"),
        "contactEmail": data.get("contactEmail", ""),
        "unsubscribeUrl": data.get("unsubscribeUrl", "#"),
    }
    for key, value in thank_you_fields.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value or ""))

    # ── Champs du template mise en relation (CONTACT_REQUEST) ──
    dest_name = " ".join(
        part for part in (
            (data.get("destFirstName") or "").strip(),
            (data.get("destLastName") or "").strip(),
        ) if part
    )
    contact_fields = {
        "destFirstName": data.get("destFirstName", ""),
        "destLastName": data.get("destLastName", ""),
        # Espace inclus pour que "Bonjour{{destFullName}}," reste correct sans nom
        "destFullName": f" {dest_name}" if dest_name else "",
    }
    for key, value in contact_fields.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(value or ""))

    requesters = data.get("requesters") or []
    if "{{REQUESTERS_BLOCK}}" in rendered:
        rendered = rendered.replace("{{REQUESTERS_BLOCK}}", build_requesters_block(requesters))

    # ── Grille des partenaires (section retirée si aucun partenaire) ──
    partners = data.get("partners") or []
    if partners and "{{PARTNERS_BLOCK}}" in rendered:
        rendered = rendered.replace("{{PARTNERS_BLOCK}}", build_partners_block(partners))
    else:
        pattern = r'<!-- PARTNERS_SECTION_START -->.*?<!-- PARTNERS_SECTION_END -->'
        rendered = re.sub(pattern, '', rendered, flags=re.DOTALL)

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


def build_requesters_block(requesters):
    """Construit la liste élégante des demandes de contact (une carte par demandeur).
    Chaque demandeur : {"requesterFirstName", "requesterLastName", "requesterEmail", "note"}.
    La note est omise si vide."""
    import html as _html
    cards = []
    for requester in requesters:
        first = _html.escape((requester.get("requesterFirstName") or "").strip())
        last = _html.escape((requester.get("requesterLastName") or "").strip())
        email = _html.escape((requester.get("requesterEmail") or "").strip())
        profession = _html.escape((requester.get("requesterProfession") or "").strip())
        company = _html.escape((requester.get("requesterCompany") or "").strip())
        acceptation_link = _html.escape((requester.get("acceptationLink") or "").strip(), quote=True)
        note = _html.escape((requester.get("note") or "").strip())
        name = " ".join(part for part in (first, last) if part) or email
        # Ligne "Profession · Entreprise" (seuls les champs fournis apparaissent)
        role_html = ""
        if profession or company:
            role = ' <span style="color:#c7a253;">&middot;</span> '.join(
                part for part in (profession, company) if part
            )
            role_html = (
                '<div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;'
                f'line-height:19px;color:#5a6577;padding-top:2px;">{role}</div>'
            )
        note_html = ""
        if note:
            note_html = (
                '<div style="border-top:1px solid #eef1f5;margin-top:12px;padding-top:10px;'
                'font-family:Georgia,\'Times New Roman\',serif;font-style:italic;'
                'font-size:14px;line-height:21px;color:#5a6577;">'
                f'&laquo;&nbsp;{note}&nbsp;&raquo;</div>'
            )
        # Bouton "Accepter" à droite des informations (omis si le lien est absent)
        button_html = ""
        if acceptation_link:
            button_html = (
                '<td align="right" valign="middle" style="padding-left:24px;white-space:nowrap;">'
                '<table role="presentation" cellpadding="0" cellspacing="0">'
                '<tr><td bgcolor="#163057" style="border-radius:8px;">'
                f'<a href="{acceptation_link}" target="_blank" '
                'style="display:inline-block;padding:10px 22px;font-family:Arial,Helvetica,sans-serif;'
                'font-size:13px;font-weight:bold;letter-spacing:.5px;color:#ffffff;text-decoration:none;'
                'border-radius:8px;">Accepter</a>'
                '</td></tr></table></td>'
            )
        cards.append(
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 14px 0;">'
            '<tr><td style="background:#ffffff;border:1px solid #e6e9ef;border-left:3px solid #c7a253;'
            'border-radius:10px;padding:18px 22px;">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            '<td valign="middle">'
            '<div style="font-family:Georgia,\'Times New Roman\',serif;font-size:17px;'
            f'line-height:24px;color:#163057;">{name}</div>'
            f'{role_html}'
            '<div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:20px;padding-top:3px;">'
            f'<a href="mailto:{email}" style="color:#a3823c;text-decoration:none;">{email}</a></div>'
            '</td>'
            f'{button_html}'
            '</tr></table>'
            f'{note_html}'
            '</td></tr></table>'
        )
    return "\n".join(cards)


def build_partners_block(partners):
    """Construit la grille HTML des partenaires (3 par ligne).
    Chaque partenaire : {"name": str, "logoUrl": str}.
    Logo affiché seulement si l'URL est absolue (http...), sinon nom en texte."""
    cells = []
    for partner in partners:
        name = (partner.get("name") or "").strip()
        logo = (partner.get("logoUrl") or "").strip()
        if logo.startswith("http"):
            inner = (
                f'<img src="{logo}" alt="{name}" height="72" '
                'style="max-height:72px;max-width:190px;display:inline-block;" />'
            )
        else:
            inner = (
                '<div style="font-family:Georgia,\'Times New Roman\',serif;font-size:19px;'
                'line-height:24px;color:#163057;font-weight:bold;letter-spacing:.3px;">'
                f'{name}</div>'
            )
        cells.append(
            '<td class="logo-cell" width="33.33%" style="padding:6px;">'
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            'style="background:#ffffff;border:1px solid #edeff3;border-radius:8px;">'
            f'<tr><td height="96" align="center" valign="middle" style="padding:10px;">{inner}</td></tr>'
            '</table></td>'
        )
    rows = []
    for i in range(0, len(cells), 3):
        row_cells = cells[i:i + 3]
        while len(row_cells) < 3:
            row_cells.append('<td class="logo-cell" width="33.33%" style="padding:6px;">&nbsp;</td>')
        rows.append(
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
            + "".join(row_cells) + '</tr></table>'
        )
    return "".join(rows)


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
