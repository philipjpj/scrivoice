"""Prepara quello che serve per costruire i pacchetti (Windows e Mac):

- scarica il modello Whisper "small" in models/faster-whisper-small (verrà incluso nell'app);
- crea le icone build/icon.ico (Windows) e build/icon.icns (Mac) da assets/app_icon.png;
- crea legal/THIRD_PARTY_LICENSES.txt con le licenze dei componenti inclusi.

Uso (dalla cartella del progetto):  python packaging/prepare.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(ROOT, "models", "faster-whisper-small")
BUILD_DIR = os.path.join(ROOT, "build")


def fetch_model():
    if os.path.isfile(os.path.join(MODEL_DIR, "model.bin")):
        print("Modello già presente:", MODEL_DIR)
        return
    from faster_whisper.utils import download_model
    download_model("small", output_dir=MODEL_DIR)
    print("Modello scaricato:", MODEL_DIR)


def make_icons():
    from PIL import Image
    os.makedirs(BUILD_DIR, exist_ok=True)
    icon = Image.open(os.path.join(ROOT, "assets", "app_icon.png")).convert("RGBA")
    icon.save(os.path.join(BUILD_DIR, "icon.ico"),
              sizes=[(s, s) for s in (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)])
    icon.resize((1024, 1024), Image.LANCZOS).save(os.path.join(BUILD_DIR, "icon.icns"))
    print("Icone create in", BUILD_DIR)


if __name__ == "__main__":
    sys.path.insert(0, ROOT)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    fetch_model()
    make_icons()
    import collect_licenses
    collect_licenses.main()
