"""
Point d'entrée principal pour la fonction Cloud Function brochure.
Décodage du message Pub/Sub et orchestration de l'envoi d'email.
"""
from firebase_functions import pubsub_fn, options
from firebase_admin import initialize_app
import json
import base64

# Initialiser Firebase Admin
initialize_app()

# Importer les modules métier
from email_sender import send_brochure_email_smtp



@pubsub_fn.on_message_published(
    topic="prod-event-ended",
    region="us-central1",
    memory=options.MemoryOption.MB_512,
    timeout_sec=540
)
def send_brochure_email(event: pubsub_fn.CloudEvent[pubsub_fn.MessagePublishedData]) -> None:
    """
    Fonction Cloud pubsub déclenchée pour envoyer des emails brochure.
    
    Workflow:
    1. Décoder le message Pub/Sub (base64 + JSON)
    2. Valider le type = "BROCHURE"
    3. Orchestrer l'envoi d'email avec pièces jointes
    """
    try:
        # 1. Décoder le message Pub/Sub (base64)
        message_data = event.data.message.data
        
        if isinstance(message_data, bytes):
            decoded_data = base64.b64decode(message_data).decode("utf-8")
        elif isinstance(message_data, str):
            try:
                decoded_data = base64.b64decode(message_data).decode("utf-8")
            except Exception:
                decoded_data = message_data
        else:
            decoded_data = str(message_data)
        
        print(f"📦 Message base64 décodé")
        
        # 2. Parser le JSON
        data = json.loads(decoded_data)
        
        event_type = data.get("type")
        print(f"📨 Message reçu: {data.get('subject', 'Sans objet')}")
        print(f"   • Entreprise: {data.get('company_name', 'N/A')}")
        print(f"   • Type: {event_type}")
        print(f"   • Template: {data.get('staticTemplateNum', 'N/A')}")
        print(f"   • Pièces jointes: {len(data.get('attachmentUrls', [])) if data.get('attachmentUrls') else 0}")
        
        # 3. Valider le type
        if event_type == "BROCHURE":
            pass
        elif event_type == "EVENT_REGISTRATION_REQUEST_SECOND_CONFIRMATION":
            print("   • Nouveau type de confirmation détecté")
            data.setdefault("staticTemplateNum", 4)
            data.setdefault("_hide_attachments_section", True)
            # Le backend n'envoie pas ces champs pour ce type : valeurs en dur
            data["subject"] = "L'événement affiche complet – confirmez votre place | Athena Event"
            data.setdefault("company_name", "Athena Event")
            data.setdefault("company_email", "noreply@athena-event.com")
        else:
            print(f"⚠️ Type incorrect: {event_type}, attendu: BROCHURE ou EVENT_REGISTRATION_REQUEST_SECOND_CONFIRMATION")
            return
        
        # 4. Envoyer l'email (orchéstrer validation + template + envoi)
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
