import functions_framework
from firebase_admin import initialize_app, storage
import smtplib
import os
import json
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.utils import formataddr
import requests
from io import BytesIO

# Initialiser Firebase Admin
initialize_app()

# Configuration SMTP
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.zeptomail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "noreply@athena-event.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "athena-event-prod")

# Templates HTML mappés par numéro
TEMPLATES = {
    1: "template_1.html",  # Corporate Élégant
    2: "template_2.html",  # Modern Professional
    3: "template_3.html",  # Business Professional
    4: "template_4.html",  # Confirmation d'inscription événementielle
    5: "email_remerciement.html"  # Remerciement post-événement
}


def load_template(template_num):
    """Charge le template HTML depuis le fichier"""
    template_file = TEMPLATES.get(template_num)
    if not template_file:
        raise ValueError(f"Template numéro {template_num} non trouvé. Utilisez 1, 2, 3, 4 ou 5.")
    
    template_path = os.path.join(os.path.dirname(__file__), "templates", template_file)
    
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def render_template(template_html, data):
    """Remplace les variables {{variable}} dans le template"""
    rendered = template_html
    
    # Remplacer les variables simples
    rendered = rendered.replace("{{firstName}}", data.get("firstName", ""))
    rendered = rendered.replace("{{lastName}}", data.get("lastName", ""))
    rendered = rendered.replace("{{company_name}}", data.get("company_name", ""))
    rendered = rendered.replace("{{company_email}}", data.get("company_email", ""))
    
    # Gérer customContent (peut être null ou vide)
    # APRÈS
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

    # ── Grille des partenaires (section retirée si aucun partenaire) ──
    import re as _re
    partners = data.get("partners") or []
    if partners and "{{PARTNERS_BLOCK}}" in rendered:
        rendered = rendered.replace("{{PARTNERS_BLOCK}}", build_partners_block(partners))
    else:
        pattern = r'<!-- PARTNERS_SECTION_START -->.*?<!-- PARTNERS_SECTION_END -->'
        rendered = _re.sub(pattern, '', rendered, flags=_re.DOTALL)

    # 🔍 DEBUG : Voir le HTML final autour de customContent
    import re
    match = re.search(r'.{100}\{\{customContent\}\}.{100}', rendered)
    if not match:
        # Chercher après remplacement
        match = re.search(r'.{100}' + re.escape(custom_content[:50]) + r'.{100}', rendered)
        if match:
            print(f"🔍 HTML final autour de customContent:\n{match.group()}")
    
    # Remplacer les URLs d'attachments (peut être null ou vide)
    attachment_urls = data.get("attachmentUrls")
    if attachment_urls is None:
        attachment_urls = []


    # Si on a des PDFs OU pas d'attachments, cacher la section visuelle
    hide_section = data.get("_hide_attachments_section", False) or not attachment_urls or len(attachment_urls) == 0

    if hide_section:
        # Supprimer toute la section pièces jointes du HTML
        import re
        # Pattern pour trouver la section entre les marqueurs
        pattern = r'<!-- ATTACHMENTS_SECTION_START -->.*?<!-- ATTACHMENTS_SECTION_END -->'
        rendered = re.sub(pattern, '', rendered, flags=re.DOTALL)
    else:
        # Garder la section mais ne pas mettre de placeholders
        # Les images seront chargées directement depuis les URLs
        for i in range(10):
            placeholder = f"{{{{attachmentUrls[{i}]}}}}"
            if i < len(attachment_urls) and attachment_urls[i]:
                # Utiliser l'URL directement (pour les images)
                # Pour les PDFs, on met juste un texte car ils seront en pièces jointes
                if is_pdf_url(attachment_urls[i]):
                    # Data URI d'une icône PDF grise
                    pdf_placeholder = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='400' viewBox='0 0 600 400'%3E%3Crect width='600' height='400' fill='%23f3f4f6'/%3E%3Ctext x='300' y='200' font-family='Arial' font-size='20' fill='%236b7280' text-anchor='middle'%3EDocument PDF%3C/text%3E%3C/svg%3E"
                    rendered = rendered.replace(placeholder, pdf_placeholder)
                else:
                    # Pour les images, utiliser l'URL directement
                    rendered = rendered.replace(placeholder, attachment_urls[i])
            else:
                # Utiliser une data URI vide
                empty_placeholder = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='600' height='400'/%3E"
                rendered = rendered.replace(placeholder, empty_placeholder)
    
    # Remplacer company_logo (URL directe, pas d'inline)
    company_logo = data.get("company_logo", "")
    if company_logo is None or company_logo.strip() == "":
        company_logo = "https://via.placeholder.com/140x40/2563eb/ffffff?text=Logo"
    rendered = rendered.replace("{{company_logo}}", company_logo)

    # Générer la liste HTML des PDFs dynamiquement
    if attachment_urls and len(attachment_urls) > 0:
        pdf_list_html = ""
        pdf_count = 0
        
        for i, url in enumerate(attachment_urls):
            if is_pdf_url(url):
                pdf_count += 1
                # Extraire le nom du fichier depuis l'URL
                filename = url.split('/')[-1].split('?')[0]
                if not filename.endswith('.pdf'):
                    filename = f"Document_{pdf_count}.pdf"
                
                # Icône selon le template
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
        
        # Remplacer le placeholder dans le template
        rendered = rendered.replace("{{PDF_LIST}}", pdf_list_html)
    else:
        rendered = rendered.replace("{{PDF_LIST}}", "")
    
    return rendered

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


def download_file_from_url(url):
    """Télécharge un fichier depuis une URL"""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        print(f"❌ Erreur téléchargement fichier {url}: {e}")
        return None


def download_from_storage(file_path):
    """Télécharge un fichier depuis Firebase Storage"""
    try:
        bucket = storage.bucket(BUCKET_NAME)
        blob = bucket.blob(file_path)
        return BytesIO(blob.download_as_bytes())
    except Exception as e:
        print(f"❌ Erreur téléchargement depuis Storage {file_path}: {e}")
        return None


def is_pdf_url(url):
    """Vérifie si l'URL est un PDF"""
    return url.lower().endswith('.pdf') or 'pdf' in url.lower()

def _embed_base64_images(html_content, related_part):
    """
    Remplace chaque <img src="data:image/...;base64,..."> du HTML par une
    référence cid: et attache l'image en pièce jointe inline (multipart/related).
    Nécessaire car Gmail, Outlook et la plupart des clients mail bloquent les
    data: URI, alors qu'ils affichent les images inline CID.
    Les images identiques sont dédupliquées (un seul CID).
    """
    import re
    pattern = re.compile(r'data:image/([a-zA-Z0-9+.-]+);base64,([A-Za-z0-9+/=]+)')
    cid_map = {}  # payload base64 -> (cid, bytes, subtype)

    def _to_cid(match):
        subtype = match.group(1).lower()
        payload = match.group(2)
        if subtype == "svg+xml":
            return match.group(0)  # SVG non supporté par les clients mail
        entry = cid_map.get(payload)
        if entry is None:
            try:
                img_bytes = base64.b64decode(payload)
            except Exception:
                return match.group(0)
            cid = f"embimg{len(cid_map) + 1}"
            cid_map[payload] = (cid, img_bytes, subtype)
        else:
            cid = entry[0]
        return f"cid:{cid}"

    new_html = pattern.sub(_to_cid, html_content)

    for cid, img_bytes, subtype in cid_map.values():
        mime_subtype = "jpeg" if subtype == "jpg" else subtype
        img_part = MIMEImage(img_bytes, _subtype=mime_subtype)
        img_part.add_header("Content-ID", f"<{cid}>")
        img_part.add_header("Content-Disposition", "inline", filename=f"{cid}.{mime_subtype}")
        related_part.attach(img_part)

    if cid_map:
        print(f"🖼️ {len(cid_map)} image(s) base64 converties en pièces jointes inline (CID)")
    return new_html


def send_brochure_email_smtp(data):
    """Envoie l'email brochure via SMTP"""
    
    # Validation des données obligatoires
    required_fields = ["recipients", "subject", "staticTemplateNum", "company_name"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Champ obligatoire manquant: {field}")
    
    recipients = data["recipients"]
    subject = data["subject"]
    template_num = int(data["staticTemplateNum"])
    
    print(f"📧 Préparation email brochure (Template {template_num}) pour {recipients}")
    
    # Vérifier si on a des PDFs dans les attachments
    attachment_urls = data.get("attachmentUrls", [])
    has_pdfs = any(is_pdf_url(url) for url in (attachment_urls or []) if url)
    
    # Si on a des PDFs, cacher la section "Pièces jointes" visuellement dans le HTML
    if has_pdfs:
        print("📄 PDFs détectés, section visuelle cachée (PDFs en pièces jointes)")
        data["_hide_attachments_section"] = True
    
    # Charger et rendre le template
    template_html = load_template(template_num)
    html_content = render_template(template_html, data)

    # ── Tracking pixel ───────────────────────────────────────────
    email_tracker = data.get("emailTracker", "").strip()
    if email_tracker:
        tracker_pixel = (
            f'<img src="{email_tracker}" width="1" height="1" alt="" />'
        )
        if "</body>" in html_content:
            html_content = html_content.replace("</body>", f"{tracker_pixel}</body>")
        else:
            html_content += tracker_pixel

    event_title = data.get('eventTitle') or data.get('event_name') or 'Athena Event'
    company_name = data.get('company_name', '')
    
    # Créer le message MIME
    msg = MIMEMultipart("mixed")
    # Format: "Nom Entreprise <email@domain.com>"
    
    # APRÈS
    msg["From"] = formataddr((f"{event_title} via {company_name}", SMTP_USER))
    msg["To"] = recipients if isinstance(recipients, str) else ", ".join(recipients)
    msg["Subject"] = subject
    
    # Partie "related" pour le HTML + images inline (logo)
    msg_related = MIMEMultipart("related")
    msg.attach(msg_related)
    
    # Ajouter le corps HTML
    msg_alternative = MIMEMultipart("alternative")
    msg_related.attach(msg_alternative)

    # Gmail/Outlook suppriment les images "data:" base64 du HTML :
    # on les convertit en pièces jointes inline référencées par cid:
    html_content = _embed_base64_images(html_content, msg_related)

    html_part = MIMEText(html_content, "html", "utf-8")
    msg_alternative.attach(html_part)
    
    # NE PAS attacher le logo en inline - laisser juste l'URL dans le HTML
    # Gmail affichera l'image directement depuis l'URL sans l'ajouter aux pièces jointes
    company_logo_url = data.get("company_logo")
    if company_logo_url and company_logo_url.strip() != "":
        print(f"📎 Logo URL: {company_logo_url}")
        print("ℹ️  Logo NON attaché (URL directe dans HTML)")
    else:
        print("⚠️ Aucun logo fourni")
    
    # Traiter les pièces jointes (uniquement les PDFs en vrais attachments)
    if attachment_urls is None or len(attachment_urls) == 0:
        print("⚠️ Aucune pièce jointe fournie")
    else:
        print(f"📎 {len(attachment_urls)} pièce(s) jointe(s) à traiter")
        
        for i, url in enumerate(attachment_urls):
            # Ignorer les URLs vides ou null
            if not url or url.strip() == "":
                print(f"⚠️ Pièce jointe {i+1} vide, ignorée")
                continue
            
            # Ignorer les placeholders
            if url.startswith("https://via.placeholder.com"):
                print(f"⚠️ Pièce jointe {i+1} est un placeholder, ignorée")
                continue
            
            print(f"📎 Téléchargement pièce jointe {i+1}/{len(attachment_urls)}: {url}")
            
            if url.startswith("gs://"):
                file_path = url.replace(f"gs://{BUCKET_NAME}/", "")
                file_data = download_from_storage(file_path)
            else:
                file_data = download_file_from_url(url)
            
            if file_data:
                # Vérifier si c'est un PDF
                if is_pdf_url(url):
                    # Attacher comme PDF (vrai fichier téléchargeable)
                    pdf_attachment = MIMEApplication(file_data.read(), _subtype="pdf")
                    pdf_attachment.add_header(
                        "Content-Disposition", 
                        "attachment", 
                        filename=f"document_{i+1}.pdf"
                    )
                    msg.attach(pdf_attachment)
                    print(f"✅ PDF {i+1} attaché")
                else:
                    # Les images ne sont PAS attachées, juste référencées par URL dans le HTML
                    print(f"ℹ️  Image {i+1} référencée par URL (non attachée)")
            else:
                print(f"❌ Échec téléchargement {'PDF' if is_pdf_url(url) else 'fichier'} {i+1}")
    
    # Envoyer via SMTP
    try:
        print(f"📤 Envoi email via {SMTP_HOST}:{SMTP_PORT}...")
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email brochure envoyé avec succès à {recipients} (Template {template_num})")
        return True
    
    except Exception as e:
        print(f"❌ Erreur envoi SMTP: {e}")
        raise

@functions_framework.http
def send_brochure_email(request):
    """
    Fonction Google Cloud déclenchée par Pub/Sub pour envoyer des emails brochure
    """
    try:
        # Décoder l'envelope Pub/Sub
        envelope = request.get_json(silent=True)
        
        if not envelope or "message" not in envelope:
            print("❌ Envelope Pub/Sub invalide")
            return ("Bad Request: envelope invalide", 400)
        
        pubsub_message = envelope["message"]
        
        if "data" in pubsub_message:
            message_data = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        else:
            print("❌ Champ 'data' absent du message Pub/Sub")
            return ("Bad Request: data absent", 400)
        
        print(f"📦 Message brut décodé: {message_data[:200]}...")
        
        # Parser le JSON
        data = json.loads(message_data)
        
        event_type = data.get("type")
        print(f"📨 Réception message: {data.get('subject', 'Sans objet')}")
        print(f"📋 Données reçues:")
        print(f"   - firstName: {data.get('firstName', 'N/A')}")
        print(f"   - lastName: {data.get('lastName', 'N/A')}")
        print(f"   - company_name: {data.get('company_name', 'N/A')}")
        print(f"   - company_logo: {data.get('company_logo', 'N/A')}")
        print(f"   - customContent: {'Fourni' if data.get('customContent') else 'Non fourni (null/vide)'}")
        print(f"   - attachmentUrls: {len(data.get('attachmentUrls', [])) if data.get('attachmentUrls') else 0} fichier(s)")
        print(f"   - type: {event_type}")
        
        # Vérifier le type
        if event_type == "BROCHURE":
            pass
        elif event_type == "EVENT_REGISTRATION_REQUEST_SECOND_CONFIRMATION":
            print("   • Nouveau type de confirmation détecté")
            data.setdefault("staticTemplateNum", 4)
            data.setdefault("_hide_attachments_section", True)
            # Le backend n'envoie pas ces champs pour ce type : valeurs en dur
            data["subject"] = "Confirmation de votre venue à l'événement"
            data.setdefault("company_name", "Athena Event")
            data.setdefault("company_email", SMTP_USER)
        elif event_type == "EVENT_THANK_YOU":
            print("   • Email de remerciement post-événement détecté")
            data.setdefault("staticTemplateNum", 5)
            data.setdefault("_hide_attachments_section", True)
            # Le backend envoie "destinataire" au lieu de "recipients"
            if not data.get("recipients") and data.get("destinataire"):
                data["recipients"] = data["destinataire"]
            data.setdefault("company_name", "Athena Event")
            data.setdefault("company_email", data.get("contactEmail") or SMTP_USER)
        else:
            print(f"⚠️ Type incorrect: {event_type}, attendu: BROCHURE, EVENT_REGISTRATION_REQUEST_SECOND_CONFIRMATION ou EVENT_THANK_YOU")
            return ("OK: type ignoré", 200)

        # Envoyer l'email
        send_brochure_email_smtp(data)

        print("✅ Email brochure traité avec succès")
        return ("OK", 200)

    except json.JSONDecodeError as e:
        print(f"❌ Erreur décodage JSON: {e}")
        print(f"📦 Données reçues (raw): {message_data}")
        return ("Bad Request: JSON invalide", 400)

    except Exception as e:
        print(f"❌ Erreur traitement message brochure: {e}")
        import traceback
        traceback.print_exc()
        # Retourner 200 pour éviter que Pub/Sub ne relance le message en boucle
        return ("OK: erreur loggée", 200)