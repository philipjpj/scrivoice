"""Parte macOS dell'incolla: app in primo piano, riattivazione e Cmd+V simulato (Quartz).

Richiede il permesso "Accessibilità" (Impostazioni di Sistema → Privacy e sicurezza) per l'app
che avvia ScriVoice (di solito il Terminale).
"""
import os
import time

import Quartz
from AppKit import NSApplicationActivateIgnoringOtherApps, NSWorkspace

KVK_ANSI_V = 9  # codice fisico del tasto V
MODIFIER_MASK = (Quartz.kCGEventFlagMaskCommand | Quartz.kCGEventFlagMaskAlternate
                 | Quartz.kCGEventFlagMaskShift | Quartz.kCGEventFlagMaskControl)

_own_pid = os.getpid()
_last_external_app = None


def track_frontmost():
    """Ricorda l'ultima app in primo piano diversa da ScriVoice. Va chiamata periodicamente:
    su Mac cliccare il widget può attivare ScriVoice, e l'incolla deve tornare all'app giusta."""
    global _last_external_app
    app = NSWorkspace.sharedWorkspace().frontmostApplication()
    if app is not None and app.processIdentifier() != _own_pid:
        _last_external_app = app


def foreground_window():
    track_frontmost()
    return _last_external_app


def focus_window(app):
    if app is None or app.isTerminated():
        return False
    front = NSWorkspace.sharedWorkspace().frontmostApplication()
    if front is not None and front.processIdentifier() == app.processIdentifier():
        return True
    app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
    time.sleep(0.15)  # lascia a macOS il tempo di passare all'app
    return True


def send_paste():
    source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)
    for key_down in (True, False):
        event = Quartz.CGEventCreateKeyboardEvent(source, KVK_ANSI_V, key_down)
        Quartz.CGEventSetFlags(event, Quartz.kCGEventFlagMaskCommand)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        time.sleep(0.01)


def wait_modifiers_released(timeout=1.5):
    """Se l'utente tiene ancora premuti Ctrl/Option/Shift/Cmd, Cmd+V diventerebbe un'altra combinazione."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateHIDSystemState)
        if not flags & MODIFIER_MASK:
            return True
        time.sleep(0.02)
    return False


def accessibility_trusted(prompt=False):
    """True se l'app ha il permesso Accessibilità (necessario per incollare).
    Con prompt=True macOS mostra la richiesta e aggiunge l'app all'elenco delle impostazioni."""
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt
        return bool(AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: prompt}))
    except Exception:  # noqa: BLE001 - senza il modulo non posso verificarlo: non blocco nulla
        return True
