"""Scorciatoie globali con pynput: usato su macOS (dove la libreria "keyboard" richiede root).

Funziona anche su Windows, così la logica si può provare lì. Su macOS le combinazioni registrate
con suppress=True non arrivano all'app in primo piano (darwin_intercept) e servono i permessi
"Monitoraggio input" e "Accessibilità".
"""
import sys
import threading

from pynput import keyboard as kb

IS_MAC = sys.platform == "darwin"

MODIFIER_KEYS = {
    kb.Key.ctrl: "ctrl", kb.Key.ctrl_l: "ctrl", kb.Key.ctrl_r: "ctrl",
    kb.Key.alt: "alt", kb.Key.alt_l: "alt", kb.Key.alt_r: "alt",
    kb.Key.shift: "shift", kb.Key.shift_l: "shift", kb.Key.shift_r: "shift",
    kb.Key.cmd: "cmd", kb.Key.cmd_l: "cmd", kb.Key.cmd_r: "cmd",
}
if hasattr(kb.Key, "alt_gr"):
    MODIFIER_KEYS[kb.Key.alt_gr] = "alt"
MODIFIERS = ("ctrl", "alt", "shift", "cmd")
# sinonimi accettati nelle combinazioni salvate
ALIASES = {"control": "ctrl", "option": "alt", "command": "cmd", "windows": "cmd", "escape": "esc",
           "return": "enter", "maiusc": "shift"}

# Codici fisici dei tasti su Mac (tastiera ANSI): servono perché con Option premuto il carattere cambia
MAC_KEYCODES = {
    0: "a", 1: "s", 2: "d", 3: "f", 4: "h", 5: "g", 6: "z", 7: "x", 8: "c", 9: "v", 11: "b", 12: "q",
    13: "w", 14: "e", 15: "r", 16: "y", 17: "t", 18: "1", 19: "2", 20: "3", 21: "4", 22: "6", 23: "5",
    25: "9", 26: "7", 28: "8", 29: "0", 31: "o", 32: "u", 34: "i", 35: "p", 37: "l", 38: "j", 40: "k",
    45: "n", 46: "m", 36: "enter", 48: "tab", 49: "space", 51: "backspace", 53: "esc",
    122: "f1", 120: "f2", 99: "f3", 118: "f4", 96: "f5", 97: "f6", 98: "f7", 100: "f8", 101: "f9",
    109: "f10", 103: "f11", 111: "f12",
}
KNOWN_KEYS = set(MAC_KEYCODES.values()) | set(MODIFIERS) | {f"f{i}" for i in range(13, 21)}


def key_name(key):
    """Nome standard (es. "ctrl", "space", "k") di un tasto pynput, o None se sconosciuto."""
    if key in MODIFIER_KEYS:
        return MODIFIER_KEYS[key]
    if isinstance(key, kb.Key):
        return ALIASES.get(key.name, key.name)
    vk = getattr(key, "vk", None)
    if IS_MAC and vk in MAC_KEYCODES:
        return MAC_KEYCODES[vk]
    if not IS_MAC and vk is not None and (0x30 <= vk <= 0x39 or 0x41 <= vk <= 0x5A):
        return chr(vk).lower()  # su Windows con Ctrl premuto .char è un carattere di controllo
    char = getattr(key, "char", None)
    return char.lower() if char else None


def parse(combo):
    """'ctrl+shift+space' -> (frozenset modificatori, tasto principale). ValueError se non valida."""
    names = [ALIASES.get(k.strip().lower(), k.strip().lower()) for k in combo.split("+") if k.strip()]
    if not names or any(n not in KNOWN_KEYS for n in names):
        raise ValueError(f"combinazione non valida: {combo}")
    mods = frozenset(n for n in names if n in MODIFIERS)
    keys = [n for n in names if n not in MODIFIERS]
    if len(keys) > 1:
        raise ValueError(f"combinazione non valida: {combo}")
    trigger = keys[0] if keys else names[-1]
    return mods - {trigger}, trigger


def is_valid(combo):
    try:
        parse(combo)
        return True
    except ValueError:
        return False


class PynputHotkeys:
    """Più combinazioni su un solo listener. on_down alla pressione, on_up al rilascio del tasto
    principale; con suppress=True (solo Mac) la combinazione non arriva all'app in primo piano."""

    def __init__(self):
        self._bindings = []  # (modificatori, tasto, on_down, on_up, suppress)
        self._pressed = set()
        self._swallowed = set()  # codici tasto la cui pressione è stata bloccata (solo Mac)
        self._listener = None

    def add(self, combo, on_down, on_up=None, suppress=False):
        mods, trigger = parse(combo)
        self._bindings.append((mods, trigger, on_down, on_up, suppress))

    def start(self):
        kwargs = {}
        if IS_MAC and any(b[4] for b in self._bindings):
            kwargs["darwin_intercept"] = self._intercept
        self._listener = kb.Listener(on_press=self._on_press, on_release=self._on_release, **kwargs)
        self._listener.start()

    def stop(self):
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        self._pressed.clear()

    def is_pressed(self, name):
        return name in self._pressed

    def _active_mods(self):
        return frozenset(n for n in self._pressed if n in MODIFIERS)

    def _on_press(self, key):
        name = key_name(key)
        if name is None:
            return
        repeat = name in self._pressed  # autorepeat del tasto tenuto premuto
        self._pressed.add(name)
        if repeat:
            return
        for mods, trigger, on_down, _on_up, _sup in self._bindings:
            if name == trigger and self._active_mods() == mods:
                on_down()

    def _on_release(self, key):
        name = key_name(key)
        if name is None:
            return
        self._pressed.discard(name)
        for _mods, trigger, _on_down, on_up, _sup in self._bindings:
            if name == trigger and on_up is not None:
                on_up()

    def _intercept(self, event_type, event):
        """Solo Mac: scarta gli eventi dei tasti delle combinazioni soppresse."""
        import Quartz
        if event_type not in (Quartz.kCGEventKeyDown, Quartz.kCGEventKeyUp):
            return event
        code = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
        name = MAC_KEYCODES.get(code)
        flags = Quartz.CGEventGetFlags(event)
        mods = frozenset(n for n, mask in (("ctrl", Quartz.kCGEventFlagMaskControl),
                                           ("alt", Quartz.kCGEventFlagMaskAlternate),
                                           ("shift", Quartz.kCGEventFlagMaskShift),
                                           ("cmd", Quartz.kCGEventFlagMaskCommand)) if flags & mask)
        if event_type == Quartz.kCGEventKeyUp:
            # il rilascio va bloccato solo se era stata bloccata anche la pressione
            if code in self._swallowed:
                self._swallowed.discard(code)
                return None
            return event
        for b_mods, trigger, _on_down, _on_up, suppress in self._bindings:
            if suppress and name == trigger and mods == b_mods:
                self._swallowed.add(code)
                return None
        return event


def capture_async(callback, timeout=15):
    """Attende una combinazione (completa al primo rilascio) e la passa a callback(str) da un thread."""
    keys = []
    done = threading.Event()

    def on_press(key):
        name = key_name(key)
        if name and name not in keys:
            keys.append(name)

    def on_release(_key):
        if keys:
            done.set()
            return False  # ferma il listener

    def run():
        listener = kb.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        done.wait(timeout)
        listener.stop()
        mods = [m for m in MODIFIERS if m in keys]
        others = [k for k in keys if k not in MODIFIERS]
        callback("+".join(mods + others))
    threading.Thread(target=run, name="hotkey-capture", daemon=True).start()
