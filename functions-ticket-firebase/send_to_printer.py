import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from google.cloud import storage as gcs_storage

# ── CONFIG IMPRIMANTE ─────────────────────────────────────────────
# MODE "com"     → câble USB ou Bluetooth via port série (COM3, COM6...)
# MODE "windows" → imprimante installée dans Windows (Paramètres → Imprimantes)
PRINTER_MODE    = "windows"                            # ← "com" ou "windows"
COM_PORT        = "COM6"                               # ← utilisé si MODE = "com"
WINDOWS_PRINTER = "iDPRT iT4S (300 dpi) - ZPL"       # ← utilisé si MODE = "windows"

BUCKET_NAME = "demo-event-app.appspot.com"

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

    # ── Envoi à l'imprimante ──────────────────────────────────────
    if PRINTER_MODE == "com":
        with open(COM_PORT, "wb") as port:
            port.write(zpl_content.encode("utf-8"))
        print(f"✅ Envoyé via port COM ({COM_PORT})")

    elif PRINTER_MODE == "windows":
        try:
            import win32print
        except ImportError:
            print("❌ Module win32print manquant — installe-le avec : pip install pywin32")
            sys.exit(1)
        handle = win32print.OpenPrinter(WINDOWS_PRINTER)
        try:
            job = win32print.StartDocPrinter(handle, 1, ("Badge ZPL", None, "RAW"))
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, zpl_content.encode("utf-8"))
            win32print.EndPagePrinter(handle)
            win32print.EndDocPrinter(handle)
            print(f"✅ Envoyé via imprimante Windows ({WINDOWS_PRINTER})")
        finally:
            win32print.ClosePrinter(handle)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_to_printer.py QR-TOKEN-ABC123")
        sys.exit(1)

    send_zpl_from_gcs(sys.argv[1])
