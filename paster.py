"""Incolla testo nella finestra che aveva il focus: appunti + Ctrl+V (Windows) o Cmd+V (Mac)."""
import sys
import time

from PySide6.QtCore import QMimeData, QTimer
from PySide6.QtGui import QGuiApplication

if sys.platform == "darwin":
    from paster_mac import (accessibility_trusted, focus_window, foreground_window, send_paste,
                            track_frontmost, wait_modifiers_released)
else:
    from paster_win import focus_window, foreground_window, send_paste, wait_modifiers_released

    def track_frontmost():
        """Su Windows il widget non prende mai il focus: niente da tracciare."""

    def accessibility_trusted(prompt=False):
        return True

__all__ = ["Paster", "accessibility_trusted", "focus_window", "foreground_window", "track_frontmost"]


def _snapshot(mime):
    copy = QMimeData()
    if mime is None:
        return copy
    for fmt in mime.formats():
        copy.setData(fmt, mime.data(fmt))
    if mime.hasImage():
        copy.setImageData(mime.imageData())
    return copy


class Paster:
    """Da usare nel thread principale Qt (gli appunti sono accessibili solo da lì)."""

    def __init__(self, restore_clipboard=True, paste_delay_ms=60, restore_after_ms=600):
        self.restore_clipboard = restore_clipboard
        self.paste_delay_ms = paste_delay_ms
        self.restore_after_ms = restore_after_ms

    def paste(self, text, target=None):
        """target: finestra (Windows) o app (Mac) salvata all'inizio della registrazione."""
        clipboard = QGuiApplication.clipboard()
        saved = _snapshot(clipboard.mimeData()) if self.restore_clipboard else None
        clipboard.setText(text)

        if target:
            focus_window(target)
        wait_modifiers_released()
        time.sleep(self.paste_delay_ms / 1000)
        send_paste()

        # ripristina gli appunti solo se l'utente non ha copiato altro nel frattempo
        if saved is not None and saved.formats():
            def restore():
                if clipboard.text() == text:
                    clipboard.setMimeData(saved)
            QTimer.singleShot(self.restore_after_ms, restore)
