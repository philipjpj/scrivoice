"""Scorciatoie globali: avvio (con pressione/rilascio per toggle + push-to-talk), stop e annulla.

Windows usa RegisterHotKey (hotkey_win.py): nessun hook sulla tastiera, gli altri tasti non vengono
mai toccati. macOS usa pynput (hotkey_pynput.py). La registrazione di una nuova combinazione nel
pannello impostazioni usa pynput su entrambi, solo per il tempo della cattura.
"""
import sys
import threading
import time

from PySide6.QtCore import QObject, Signal

import hotkey_pynput

IS_MAC = sys.platform == "darwin"

if not IS_MAC:
    import hotkey_win

MAC_LABELS = {"cmd": "⌘ Cmd", "alt": "⌥ Option", "ctrl": "⌃ Ctrl", "shift": "⇧ Shift"}
WIN_LABELS = {"cmd": "Win", "esc": "Esc"}


class HotkeyInUse(RuntimeError):
    """Windows ha rifiutato una combinazione perché è già usata da un'altra app."""

    def __init__(self, combos):
        super().__init__(", ".join(combos))
        self.combos = combos


def pretty(combo):
    """'ctrl+alt+space' -> 'Ctrl+Alt+Space' (su Mac con i simboli dei modificatori)."""
    if not combo:
        return ""
    keys = [k.strip() for k in combo.split("+")]
    if IS_MAC:
        return " ".join(MAC_LABELS.get(k, k.title()) for k in keys)
    keys.sort(key=lambda k: k != "cmd")  # su Windows il tasto Win si scrive per primo
    return "+".join(WIN_LABELS.get(k, k.title()) for k in keys)


def is_valid(combo):
    return hotkey_pynput.is_valid(combo) if IS_MAC else hotkey_win.is_valid(combo)


def capture_async(callback, timeout=15):
    """Attende che l'utente prema una combinazione e la passa a callback(str) da un thread."""
    hotkey_pynput.capture_async(callback, timeout)


class HotkeyManager(QObject):
    """start_pressed/start_released portano l'istante (time.monotonic) in cui il tasto è stato
    davvero premuto/rilasciato: se il programma è occupato (es. carica il modello) i segnali possono
    arrivare in ritardo, ma la durata della pressione (tocco o push-to-talk) resta corretta."""
    start_pressed = Signal(float)
    start_released = Signal(float)
    stop_pressed = Signal()
    cancel_pressed = Signal()

    def __init__(self, start_combo, stop_combo="", cancel_combo="esc"):
        super().__init__()
        self.configure(start_combo, stop_combo, cancel_combo)
        self._down = False
        self._engine = None
        self._stop_id = self._cancel_id = None
        self._trigger_vk = None
        self.active = False

    def configure(self, start_combo, stop_combo="", cancel_combo="esc"):
        self.start_combo = start_combo
        # uno stop uguale all'avvio è ridondante: il tasto di avvio ferma già la registrazione
        self.stop_combo = stop_combo if stop_combo and stop_combo != start_combo else ""
        self.cancel_combo = cancel_combo or ""
        # il tasto "principale" è l'ultimo della combinazione (es. space in ctrl+alt+space)
        self.trigger_key = start_combo.split("+")[-1].strip()

    def start(self):
        self._down = False
        if IS_MAC:
            engine = hotkey_pynput.PynputHotkeys()
            engine.add(self.start_combo, self._on_down, on_up=self._on_up, suppress=True)
            if self.stop_combo:
                engine.add(self.stop_combo, self.stop_pressed.emit, suppress=True)
            if self.cancel_combo:
                # non soppresso: se non sto registrando, Esc deve continuare a funzionare nelle app
                engine.add(self.cancel_combo, self.cancel_pressed.emit)
            engine.start()
        else:
            engine = hotkey_win.WinHotkeys()
            engine.add(self.start_combo, self._on_win_down)
            # stop e annulla vengono "prenotati" solo durante la registrazione (set_recording),
            # così negli altri momenti Esc e la combinazione di stop funzionano normalmente
            self._stop_id = engine.add(self.stop_combo, self.stop_pressed.emit, enabled=False) \
                if self.stop_combo else None
            self._cancel_id = engine.add(self.cancel_combo, self.cancel_pressed.emit, enabled=False) \
                if self.cancel_combo else None
            self._trigger_vk = hotkey_win.parse(self.start_combo)[1]
            engine.start()
            if engine.failed:
                engine.stop()
                raise HotkeyInUse([pretty(c) for c in engine.failed])
        self._engine = engine
        self.active = True

    def stop(self):
        if self._engine is not None:
            self._engine.stop()
            self._engine = None
        self.active = False

    def set_recording(self, recording):
        """Su Windows attiva stop e annulla solo mentre si registra."""
        if IS_MAC or self._engine is None:
            return
        self._engine.set_enabled(self._stop_id, recording)
        self._engine.set_enabled(self._cancel_id, recording)

    def is_trigger_held(self):
        try:
            if IS_MAC:
                return self._engine is not None and self._engine.is_pressed(self.trigger_key)
            return self._trigger_vk is not None and hotkey_win.is_key_down(self._trigger_vk)
        except Exception:  # noqa: BLE001
            return False

    def reset_down(self):
        self._down = False

    def _on_win_down(self):
        """Thread delle scorciatoie di Windows: Windows avvisa solo della pressione, il rilascio
        (per il push-to-talk) lo controlla un thread dedicato che non viene rallentato dalla UI."""
        if self._down:
            return
        self._on_down()
        threading.Thread(target=self._watch_release, name="hotkey-release", daemon=True).start()

    def _watch_release(self):
        while self._down and self.is_trigger_held():
            time.sleep(0.01)
        self._on_up()

    def _on_down(self):
        if self._down:  # autorepeat del tasto tenuto premuto
            return
        self._down = True
        self.start_pressed.emit(time.monotonic())

    def _on_up(self, _event=None):
        if not self._down:
            return
        self._down = False
        self.start_released.emit(time.monotonic())
