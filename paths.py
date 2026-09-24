"""Percorsi dell'app.

- Dati dell'utente (impostazioni, registrazioni, log): nell'app installata stanno nella cartella
  dati dell'utente, perché la cartella del programma può essere in sola lettura. Eseguendo dai sorgenti
  restano nella cartella del progetto, come sempre.
- Risorse (icona, modello incluso): dentro il pacchetto creato da PyInstaller (sys._MEIPASS).
"""
import os
import sys

APP_NAME = "ScriVoice"
FROZEN = getattr(sys, "frozen", False)
SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = getattr(sys, "_MEIPASS", SOURCE_DIR)


def _user_data_dir():
    if not FROZEN:
        return SOURCE_DIR
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, APP_NAME)


DATA_DIR = _user_data_dir()
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
RECORDINGS_DIR = os.path.join(DATA_DIR, "recordings")
LOG_DIR = os.path.join(DATA_DIR, "logs")


def resource(*parts):
    return os.path.join(RESOURCE_DIR, *parts)


APP_ICON = resource("assets", "app_icon.png")


def bundled_model(name):
    """Cartella del modello Whisper incluso nel pacchetto, oppure None se non c'è."""
    path = resource("models", f"faster-whisper-{name}")
    return path if os.path.isfile(os.path.join(path, "model.bin")) else None
