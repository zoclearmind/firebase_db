import os

from google.cloud import storage as gcs_storage

# "K_SERVICE" est positionnée automatiquement par Cloud Run / Cloud Functions
# (Gen2) sur l'environnement déployé — absente en local. Sert à distinguer
# prod (vrai client GCS) de dev local (émulateur Firebase Storage).
if os.environ.get("K_SERVICE"):
    # Production — vrai client GCS avec les credentials par défaut
    storage_client = gcs_storage.Client()
else:
    # Développement local — émulateur Firebase Storage
    os.environ["STORAGE_EMULATOR_HOST"] = "http://127.0.0.1:9199"
    storage_client = gcs_storage.Client.create_anonymous_client()
    storage_client.project = "demo-event-app"
