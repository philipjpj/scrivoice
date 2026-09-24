"""Precarica un runtime MSVC recente prima di ctranslate2.

ctranslate2 >= 4.x è compilato con MSVC 14.40+: se Windows ha un msvcp140.dll più vecchio
(es. 14.26) in System32, il caricamento del modello va in crash con "access violation".
PySide6 include un runtime aggiornato: caricandolo per primo, tutte le DLL successive
che chiedono "msvcp140.dll" riusano quello già in memoria.
"""
import ctypes
import os
import sys


def preload_msvc_runtime():
    if sys.platform != "win32":
        return
    try:
        import PySide6
    except ImportError:
        return
    folder = os.path.dirname(PySide6.__file__)
    for name in ("vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll",
                 "msvcp140_1.dll", "msvcp140_2.dll"):
        path = os.path.join(folder, name)
        if os.path.exists(path):
            try:
                ctypes.WinDLL(path)
            except OSError:
                pass
