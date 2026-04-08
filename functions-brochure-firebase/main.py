from firebase_functions import pubsub_fn, options
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
    3: "template_3.html"   # Business Professional
}


def load_template(template_num):
    """Charge le template HTML depuis le fichier"""
    template_file = TEMPLATES.get(template_num)
    if not template_file:
        raise ValueError(f"Template numéro {template_num} non trouvé. Utilisez 1, 2 ou 3.")
    
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
        event_name = data.get("event_name", "l'événement")
        custom_content = f"Merci pour cet échange enrichissant lors de {event_name} ! N'hésitez pas à nous contacter pour toute question ou besoin d'information complémentaire."
    

    rendered = rendered.replace("{{customContent}}", custom_content)

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
    event_name = data.get('event_name', 'Athena Event')
    company_name = data.get('company_name', '')
    
    # Créer le message MIME
    msg = MIMEMultipart("mixed")
    # Format: "Nom Entreprise <email@domain.com>"
    
    # APRÈS
    msg["From"] = formataddr((f"{company_name} via {event_name}", SMTP_USER))
    msg["To"] = recipients if isinstance(recipients, str) else ", ".join(recipients)
    msg["Subject"] = subject
    
    # Partie "related" pour le HTML + images inline (logo)
    msg_related = MIMEMultipart("related")
    msg.attach(msg_related)
    
    # Ajouter le corps HTML
    msg_alternative = MIMEMultipart("alternative")
    msg_related.attach(msg_alternative)
    
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

@pubsub_fn.on_message_published(
    topic="prod-event-ended",
    region="us-central1",
    memory=options.MemoryOption.MB_512,
    timeout_sec=540
)
def send_brochure_email(event: pubsub_fn.CloudEvent[pubsub_fn.MessagePublishedData]) -> None:
    """
    Fonction Firebase déclenchée par Pub/Sub pour envoyer des emails brochure
    """
    try:
        # Décoder le message Pub/Sub (il est en base64)
        message_data = event.data.message.data
        
        # Vérifier si c'est déjà une string ou des bytes
        if isinstance(message_data, bytes):
            decoded_data = base64.b64decode(message_data).decode("utf-8")
        elif isinstance(message_data, str):
            try:
                decoded_data = base64.b64decode(message_data).decode("utf-8")
            except Exception:
                decoded_data = message_data
        else:
            decoded_data = str(message_data)
        
        print(f"📦 Message brut décodé: {decoded_data[:200]}...")
        
        # Parser le JSON
        data = json.loads(decoded_data)
        
        print(f"📨 Réception message brochure: {data.get('subject', 'Sans objet')}")
        print(f"📋 Données reçues:")
        print(f"   - firstName: {data.get('firstName', 'N/A')}")
        print(f"   - lastName: {data.get('lastName', 'N/A')}")
        print(f"   - company_name: {data.get('company_name', 'N/A')}")
        print(f"   - company_logo: {data.get('company_logo', 'N/A')}")
        print(f"   - customContent: {'Fourni' if data.get('customContent') else 'Non fourni (null/vide)'}")
        print(f"   - attachmentUrls: {len(data.get('attachmentUrls', [])) if data.get('attachmentUrls') else 0} fichier(s)")
        
        # Vérifier le type
        if data.get("type") != "BROCHURE":
            print(f"⚠️ Type incorrect: {data.get('type')}, attendu: BROCHURE")
            return
        
        # Envoyer l'email
        send_brochure_email_smtp(data)
        
        print("✅ Email brochure traité avec succès")
    
    except json.JSONDecodeError as e:
        print(f"❌ Erreur décodage JSON: {e}")
        print(f"📦 Données reçues (raw): {event.data.message.data}")
        raise
    
    except Exception as e:
        print(f"❌ Erreur traitement message brochure: {e}")
        import traceback
        traceback.print_exc()
        raise