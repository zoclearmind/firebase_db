import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from google.cloud import storage as gcs_storage

COM_PORT    = "COM6"                                   # ← change selon ton port
BUCKET_NAME = "demo-event-app.appspot.com"             # ← même bucket que pdf_generator.py

# Client Storage — Firebase Storage Emulator
import os
os.environ["STORAGE_EMULATOR_HOST"] = "http://127.0.0.1:9199"
storage_client = gcs_storage.Client.create_anonymous_client()
storage_client.project = "demo-event-app"


def send_zpl_from_gcs(qr_token: str):
    blob_path = f"tickets/badge_{qr_token}.zpl"

    # ── Téléchargement depuis GCS ─────────────────────────────────
    bucket = storage_client.bucket(BUCKET_NAME)
    blob   = bucket.blob(blob_path)

    if not blob.exists():
        print(f"❌ Badge introuvable dans GCS : {blob_path}")
        sys.exit(1)

    zpl_content = blob.download_as_text(encoding="utf-8")
    print(f"📦 ZPL récupéré depuis GCS ({len(zpl_content)} caractères)")

    # ── Envoi à l'imprimante via port COM Bluetooth ───────────────
    with open(COM_PORT, "wb") as port:
        port.write(zpl_content.encode("utf-8"))
        print(f"✅ Envoyé à l'imprimante ({COM_PORT})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_to_printer.py QR-TOKEN-ABC123")
        sys.exit(1)

    send_zpl_from_gcs(sys.argv[1])
