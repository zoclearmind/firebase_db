"""
Gestion des pièces jointes : téléchargement, validation, détection de types.
"""
import requests
from firebase_admin import storage
from io import BytesIO
from config import BUCKET_NAME


def is_pdf_url(url):
    """Vérifie si l'URL pointe vers un PDF"""
    return url.lower().endswith('.pdf') or 'pdf' in url.lower()


def download_file_from_url(url):
    """Télécharge un fichier depuis une URL publique"""
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


def process_attachment(url):
    """
    Traite une pièce jointe (URL ou GCS).
    Retourne (BytesIO, is_pdf) ou (None, False) si erreur.
    """
    # Vérifier si c'est vide ou placeholder
    if not url or url.strip() == "":
        print(f"⚠️ Pièce jointe vide, ignorée")
        return None, False
    
    if url.startswith("https://via.placeholder.com"):
        print(f"⚠️ Pièce jointe est un placeholder, ignorée")
        return None, False
    
    # Télécharger de GCS ou URL
    if url.startswith("gs://"):
        file_path = url.replace(f"gs://{BUCKET_NAME}/", "")
        file_data = download_from_storage(file_path)
    else:
        file_data = download_file_from_url(url)
    
    if file_data:
        return file_data, is_pdf_url(url)
    
    return None, False
