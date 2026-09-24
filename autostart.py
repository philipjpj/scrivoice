"""Avvio automatico di ScriVoice all'accensione del computer.

Windows: valore "ScriVoice" in HKCU\\...\\Run (lo stesso che imposta l'installer).
Mac: LaunchAgent ~/Library/LaunchAgents/com.scrivoice.app.plist.
"""
import os
import plistlib
import sys

import paths

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "ScriVoice"
MAC_AGENT = os.path.expanduser("~/Library/LaunchAgents/com.scrivoice.app.plist")


def _launch_args():
    """Comando che avvia ScriVoice: l'eseguibile dell'app installata, oppure python + main.py."""
    if paths.FROZEN:
        if sys.platform == "darwin":
            # .../ScriVoice.app/Contents/MacOS/ScriVoice -> apro il bundle, come fa il Finder
            bundle = os.path.abspath(os.path.join(os.path.dirname(sys.executable), "..", ".."))
            return ["/usr/bin/open", "-a", bundle]
        return [sys.executable]
    python = sys.executable
    if sys.platform == "win32":
        pythonw = os.path.join(os.path.dirname(python), "pythonw.exe")
        python = pythonw if os.path.exists(pythonw) else python
    return [python, os.path.join(paths.SOURCE_DIR, "main.py")]


def is_supported():
    return sys.platform in ("win32", "darwin")


def is_enabled():
    if sys.platform == "win32":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                winreg.QueryValueEx(key, VALUE_NAME)
                return True
        except OSError:
            return False
    if sys.platform == "darwin":
        return os.path.exists(MAC_AGENT)
    return False


def set_enabled(enabled):
    if sys.platform == "win32":
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                command = " ".join(f'"{a}"' for a in _launch_args())
                winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, VALUE_NAME)
                except FileNotFoundError:
                    pass
    elif sys.platform == "darwin":
        if enabled:
            os.makedirs(os.path.dirname(MAC_AGENT), exist_ok=True)
            with open(MAC_AGENT, "wb") as f:
                plistlib.dump({"Label": "com.scrivoice.app", "ProgramArguments": _launch_args(),
                               "RunAtLoad": True}, f)
        elif os.path.exists(MAC_AGENT):
            os.remove(MAC_AGENT)
