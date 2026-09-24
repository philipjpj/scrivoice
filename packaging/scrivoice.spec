# -*- mode: python ; coding: utf-8 -*-
"""Ricetta PyInstaller di ScriVoice (Windows e Mac).

Uso (dalla cartella del progetto, dopo `python packaging/prepare.py`):
    pyinstaller --noconfirm --clean packaging/scrivoice.spec
Risultato: dist/ScriVoice/ (Windows) oppure dist/ScriVoice.app (Mac).

Modalità "cartella" (non file singolo): parte più velocemente e le librerie LGPL (Qt/PySide6,
pynput) restano file separati e sostituibili, come richiede la loro licenza.
"""
import os
import sys

from PyInstaller.utils.hooks import collect_data_files

sys.path.insert(0, os.path.abspath(os.path.join(SPECPATH, "..")))
import version  # noqa: E402

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
IS_MAC = sys.platform == "darwin"
MODEL = os.path.join(ROOT, "models", "faster-whisper-small")

datas = [
    (os.path.join(ROOT, "assets", "app_icon.png"), "assets"),
    (os.path.join(ROOT, "assets", "selftest.wav"), "assets"),
    (os.path.join(ROOT, "legal"), "legal"),
    (os.path.join(ROOT, "LICENSE"), "legal"),
]
for name in ("model.bin", "config.json", "tokenizer.json", "vocabulary.txt"):
    datas.append((os.path.join(MODEL, name), "models/faster-whisper-small"))
datas += collect_data_files("faster_whisper")  # modello VAD (silero) usato per ignorare i silenzi

if IS_MAC:
    hiddenimports = ["pynput.keyboard._darwin", "pynput.mouse._darwin"]
    excludes = ["paster_win", "hotkey_win"]
else:
    hiddenimports = ["pynput.keyboard._win32", "pynput.mouse._win32"]
    excludes = ["paster_mac"]
# PIL serve solo a creare le icone; hf_xet solo per scaricare modelli (qui sono inclusi)
excludes += ["tkinter", "matplotlib", "IPython", "pytest", "PIL", "hf_xet"]

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ScriVoice",
    console=False,
    icon=os.path.join(ROOT, "build", "icon.icns" if IS_MAC else "icon.ico"),
    target_arch="arm64" if IS_MAC else None,
    codesign_identity=None,
)
coll = COLLECT(exe, a.binaries, a.datas, name="ScriVoice")

if IS_MAC:
    app = BUNDLE(
        coll,
        name="ScriVoice.app",
        icon=os.path.join(ROOT, "build", "icon.icns"),
        bundle_identifier="com.scrivoice.app",
        version=version.__version__,
        info_plist={
            "CFBundleName": "ScriVoice",
            "CFBundleDisplayName": "ScriVoice",
            "CFBundleShortVersionString": version.__version__,
            "CFBundleVersion": version.__version__,
            "LSMinimumSystemVersion": "13.0",
            "LSUIElement": True,  # solo barra dei menu, niente icona nel Dock
            "NSHighResolutionCapable": True,
            "NSMicrophoneUsageDescription":
                "ScriVoice uses the microphone to transcribe your voice into text on this Mac.",
        },
    )
