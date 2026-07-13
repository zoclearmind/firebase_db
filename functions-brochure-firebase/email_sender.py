"""
Construction et envoi d'emails SMTP avec pièces jointes.
"""
import base64
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.utils import formataddr

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
from templates_handler import load_template, render_template
from attachments import process_attachment, is_pdf_url


def send_brochure_email_smtp(data):
    """
    Envoie l'email brochure via SMTP.
    Paramètre : data (dict) contenant tous les détails de l'email
    """
    # ── Validation des données obligatoires ──
    event_type = data.get("type", "")
    required_fields = ["recipients", "subject", "company_name"]
    if event_type == "BROCHURE":
        required_fields.append("staticTemplateNum")
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Champ obligatoire manquant: {field}")
    
    recipients = data["recipients"]
    subject = data["subject"]
    if event_type == "BROCHURE":
        template_num = int(data["staticTemplateNum"])
    else:
        template_num = int(data.get("staticTemplateNum", 4))
    attachment_urls = data.get("attachmentUrls", [])
    
    print(f"📧 Préparation email type {event_type or 'UNKNOWN'} (Template {template_num}) pour {recipients}")

    if event_type == "EVENT_REGISTRATION_REQUEST_SECOND_CONFIRMATION":
        data.setdefault("_hide_attachments_section", True)
    
    # Détecter si on a des PDFs (pour cacher la section visuelle)
    has_pdfs = any(is_pdf_url(url) for url in (attachment_urls or []) if url)
    if has_pdfs:
        print("📄 PDFs détectés, section visuelle cachée (PDFs en pièces jointes)")
        data["_hide_attachments_section"] = True
    
    # ── Charger et rendre le template ──
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
    
    # ── Logging du logo ──
    company_logo_url = data.get("company_logo")
    if company_logo_url and company_logo_url.strip() != "":
        print(f"📎 Logo URL: {company_logo_url}")
        print("ℹ️  Logo NON attaché (URL directe dans HTML)")
    else:
        print("⚠️ Aucun logo fourni")
    
    # ── Construire le message MIME ──
    msg = MIMEMultipart("mixed")
    msg["From"] = formataddr((f"{event_title} via {company_name}", SMTP_USER))
    msg["To"] = recipients if isinstance(recipients, str) else ", ".join(recipients)
    msg["Subject"] = subject
    
    # Ajouter la partie related (HTML + images inline - logo)
    msg_related = MIMEMultipart("related")
    msg.attach(msg_related)
    
    msg_alternative = MIMEMultipart("alternative")
    msg_related.attach(msg_alternative)

    # Gmail/Outlook suppriment les images "data:" base64 du HTML :
    # on les convertit en pièces jointes inline référencées par cid:
    html_content = _embed_base64_images(html_content, msg_related)

    html_part = MIMEText(html_content, "html", "utf-8")
    msg_alternative.attach(html_part)

    # ── Traiter les pièces jointes ──
    _process_attachments(msg, attachment_urls)
    
    # ── Envoyer via SMTP ──
    _send_via_smtp(msg, recipients)


def _embed_base64_images(html_content, related_part):
    """
    Remplace chaque <img src="data:image/...;base64,..."> du HTML par une
    référence cid: et attache l'image en pièce jointe inline (multipart/related).
    Nécessaire car Gmail, Outlook et la plupart des clients mail bloquent les
    data: URI, alors qu'ils affichent les images inline CID.
    Les images identiques sont dédupliquées (un seul CID).
    """
    import uuid
    # Suffixe unique par envoi : sans lui, Zoho met en cache les images par
    # Content-ID et peut afficher celles d'un ancien email (logos mélangés)
    unique = uuid.uuid4().hex[:12]
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
            cid = f"embimg{len(cid_map) + 1}.{unique}@athena-event.com"
            cid_map[payload] = (cid, img_bytes, subtype)
        else:
            cid = entry[0]
        return f"cid:{cid}"

    new_html = pattern.sub(_to_cid, html_content)

    for cid, img_bytes, subtype in cid_map.values():
        mime_subtype = "jpeg" if subtype == "jpg" else subtype
        img_part = MIMEImage(img_bytes, _subtype=mime_subtype)
        img_part.add_header("Content-ID", f"<{cid}>")
        # Pas de Content-Disposition du tout (RFC 2387) : dans un multipart/related
        # cet en-tête est superflu et pousse Zoho/Thunderbird à lister
        # l'image comme pièce jointe
        related_part.attach(img_part)

    if cid_map:
        print(f"🖼️ {len(cid_map)} image(s) base64 converties en pièces jointes inline (CID)")
    return new_html


def _process_attachments(msg, attachment_urls):
    """
    Traite et attache les fichiers au message EMAIL.
    Seuls les PDFs sont attachés; les images restent en URL dans le HTML.
    """
    if not attachment_urls or len(attachment_urls) == 0:
        print("⚠️ Aucune pièce jointe fournie")
        return
    
    print(f"📎 Traitement de {len(attachment_urls)} pièce(s) jointe(s)...")
    
    pdf_count = 0
    for i, url in enumerate(attachment_urls):
        print(f"📎 Pièce jointe {i+1}/{len(attachment_urls)}: {url[:100]}...")
        
        file_data, is_pdf = process_attachment(url)
        
        if file_data:
            if is_pdf:
                # Attacher le PDF comme vrai fichier téléchargeable
                pdf_count += 1
                pdf_attachment = MIMEApplication(file_data.read(), _subtype="pdf")
                pdf_attachment.add_header(
                    "Content-Disposition", 
                    "attachment", 
                    filename=f"document_{pdf_count}.pdf"
                )
                msg.attach(pdf_attachment)
                print(f"✅ PDF {pdf_count} attaché")
            else:
                # Images ne sont PAS attachées, juste référencées par URL
                print(f"ℹ️  Image référencée par URL (non attachée)")
        else:
            print(f"❌ Échec traitement pièce jointe {i+1}")


def _send_via_smtp(msg, recipients):
    """
    Envoie le message via SMTP.
    """
    try:
        print(f"📤 Envoi email via {SMTP_HOST}:{SMTP_PORT}...")
        
        if not all([SMTP_USER, SMTP_PASSWORD]):
            raise ValueError("Configuration SMTP incomplète (SMTP_USER ou SMTP_PASSWORD manquants)")
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email brochure envoyé avec succès à {recipients}")
        return True
    
    except Exception as e:
        print(f"❌ Erreur envoi SMTP: {e}")
        raise
