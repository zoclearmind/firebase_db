import os

from google.cloud import storage as gcs_storage

# Configuration Storage Emulator
os.environ["STORAGE_EMULATOR_HOST"] = "http://127.0.0.1:9199"

# Client Storage
storage_client = gcs_storage.Client.create_anonymous_client()
storage_client.project = "demo-event-app"
