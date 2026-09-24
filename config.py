"""Caricamento e salvataggio della configurazione (config.json nella cartella dati, vedi paths.py)."""
import json
import os
import sys

import paths

CONFIG_PATH = paths.CONFIG_PATH
DICTATION_LANGUAGES = ("it", "en", "es")

# Frase di contesto salvata nei config della prima versione: ora è scelta in base alla lingua
LEGACY_PROMPT = (
    "Trascrizione di istruzioni in italiano per Claude Code, un assistente di programmazione. "
    "Termini frequenti: Claude Code, Python, JavaScript, TypeScript, React, API, file, "
    "commit, branch, pull request, bug, refactoring, test, frontend, backend, database."
)

DEFAULTS = {
    # Lingua dell'interfaccia: it | en | es | null (= lingua del sistema)
    "ui_language": None,
    # Scorciatoia globale: tap breve = avvia/ferma, tenuta premuta = push-to-talk.
    # Su Mac Ctrl+Option+Spazio cambia la lingua della tastiera: uso Ctrl+Shift+Spazio
    "hotkey": "ctrl+shift+space" if sys.platform == "darwin" else "ctrl+alt+space",
    # Scorciatoia opzionale solo per fermare ("" = si ferma con la scorciatoia di avvio)
    "stop_hotkey": "",
    # Annulla la registrazione in corso ("" = disattivato)
    "cancel_hotkey": "esc",
    # Oltre questa durata (secondi) la pressione è considerata push-to-talk
    "hold_threshold": 0.4,
    # Modello faster-whisper: tiny, base, small, medium, large-v3-turbo, large-v3
    # (small = veloce; large-v3-turbo = più preciso ma ~4x più lento su CPU e ~2 GB di RAM)
    "model": "small",
    "compute_type": "int8",
    # Lingua della dettatura: it | en | es | auto (rileva tra le tre); None = lingua del sistema
    "language": None,
    # 1 = più veloce; 5 = più preciso
    "beam_size": 5,
    # 0 = automatico (numero di core fisici)
    "cpu_threads": 0,
    # Frase di contesto per Whisper; vuota = quella predefinita della lingua (transcriber.PROMPTS)
    "initial_prompt": "",
    # Parole che usi spesso: aiutano Whisper a riconoscerle
    "vocabulary": ["Claude Code", "ChatGPT", "prompt", "commit", "branch", "pull request", "bug",
                   "deploy", "shortcut", "task", "widget"],
    # Sostituzioni automatiche locali: [parola sbagliata, parola giusta]
    "replacements": [],
    "sample_rate": 48000,
    # Nome del microfono (come appare nelle impostazioni); null = predefinito del sistema
    "input_device": None,
    # spento per i clienti: la voce viene salvata su disco solo se lo scelgono
    "keep_recordings": False,
    "max_recordings": 200,
    # Rimette negli appunti il contenuto precedente dopo l'incolla
    "restore_clipboard": True,
    "paste_delay_ms": 60,
    # Aspetto del widget: tema dark | light | neon, colore di accento, dimensione, opacità
    "theme": "dark",
    "accent": "#EB4048",
    "widget_size": 1.0,
    "opacity": 0.95,
    "widget_x": None,
    "widget_y": None,
}


def load():
    cfg = dict(DEFAULTS)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg.update(saved)
            # config della prima versione: beam 1 era il vecchio predefinito veloce
            if "vocabulary" not in saved:
                cfg["beam_size"] = DEFAULTS["beam_size"]
            # opzioni di versioni precedenti non più usate (es. la correzione con Claude, rimossa)
            for key in ("ai_correction", "ai_model", "ai_min_words"):
                cfg.pop(key, None)
            # la vecchia frase fissa in italiano peggiorerebbe la dettatura nelle altre lingue
            if cfg.get("initial_prompt") == LEGACY_PROMPT:
                cfg["initial_prompt"] = ""
        except (OSError, ValueError) as e:
            print(f"config.json non leggibile, uso i valori predefiniti: {e}", file=sys.stderr)
    if cfg.get("language") is None:
        cfg["language"] = system_language()
    if not os.path.exists(CONFIG_PATH):
        save(cfg)
    return cfg


def system_language():
    """Lingua di dettatura iniziale: quella del sistema, se è tra quelle supportate."""
    from PySide6.QtCore import QLocale
    code = QLocale.system().name()[:2]
    return code if code in DICTATION_LANGUAGES else "en"


def save(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Impossibile salvare config.json: {e}", file=sys.stderr)
