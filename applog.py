"""Registro degli errori su file (per l'assistenza) nella cartella dati dell'utente.

Nell'app installata non esiste una console: sys.stdout/sys.stderr sono None e un semplice
traceback.print_exc() farebbe crashare il programma. Qui vengono reindirizzati nel log.
"""
import faulthandler
import logging
import logging.handlers
import os
import sys

import paths

log = logging.getLogger("scrivoice")
_crash_file = None


class _StreamToLog:
    def __init__(self, level):
        self.level = level

    def write(self, text):
        text = text.rstrip()
        if text:
            log.log(self.level, text)

    def flush(self):
        pass

    def isatty(self):
        return False


def setup():
    os.makedirs(paths.LOG_DIR, exist_ok=True)
    handler = logging.handlers.RotatingFileHandler(
        os.path.join(paths.LOG_DIR, "scrivoice.log"), maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    # crash nelle librerie native (senza eccezione Python): la traccia finisce in crash.log
    global _crash_file
    _crash_file = open(os.path.join(paths.LOG_DIR, "crash.log"), "a", encoding="utf-8")
    faulthandler.enable(file=_crash_file, all_threads=True)
    if paths.FROZEN or sys.stdout is None:
        sys.stdout = _StreamToLog(logging.INFO)
    if paths.FROZEN or sys.stderr is None:
        sys.stderr = _StreamToLog(logging.WARNING)
    return log
