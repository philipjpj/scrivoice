"""Scorciatoie globali su Windows con RegisterHotKey.

È Windows stesso a riconoscere la combinazione e ad avvisare il programma: nessun hook sulla
tastiera, quindi gli altri tasti (Ctrl, Fn, Ctrl+rotellina, ecc.) non vengono mai toccati.
La combinazione registrata non arriva all'app in primo piano.
"""
import ctypes
import queue
import threading
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WM_HOTKEY = 0x0312
WM_APP = 0x8000
WM_QUIT = 0x0012
PM_NOREMOVE = 0x0000
MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x8, 0x4000
VK_MENU_MASK = 0xE8  # codice tasto non assegnato
KEYEVENTF_KEYUP = 0x2

MODIFIERS = {"ctrl": MOD_CONTROL, "alt": MOD_ALT, "shift": MOD_SHIFT, "cmd": MOD_WIN}
ALIASES = {
    "control": "ctrl", "left ctrl": "ctrl", "right ctrl": "ctrl", "ctrl_l": "ctrl", "ctrl_r": "ctrl",
    "left alt": "alt", "right alt": "alt", "alt_l": "alt", "alt_r": "alt", "option": "alt",
    "maiusc": "shift", "left shift": "shift", "right shift": "shift", "shift_l": "shift", "shift_r": "shift",
    "windows": "cmd", "win": "cmd", "left windows": "cmd", "right windows": "cmd", "command": "cmd",
    "escape": "esc", "return": "enter",
}
VK_CODES = {
    "space": 0x20, "esc": 0x1B, "enter": 0x0D, "tab": 0x09, "backspace": 0x08, "pause": 0x13,
    "insert": 0x2D, "delete": 0x2E, "home": 0x24, "end": 0x23, "page_up": 0x21, "page_down": 0x22,
    "page up": 0x21, "page down": 0x22, "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
}
VK_CODES.update({f"f{i}": 0x6F + i for i in range(1, 25)})          # F1 = 0x70
VK_CODES.update({chr(c).lower(): c for c in range(0x41, 0x5B)})      # A-Z
VK_CODES.update({chr(c): c for c in range(0x30, 0x3A)})              # 0-9

user32.RegisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT)
user32.UnregisterHotKey.argtypes = (wintypes.HWND, ctypes.c_int)
user32.PostThreadMessageW.argtypes = (wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
user32.GetAsyncKeyState.restype = ctypes.c_short


def parse(combo):
    """'ctrl+alt+space' -> (modificatori MOD_*, codice VK del tasto). ValueError se non valida."""
    names = [k.strip().lower() for k in combo.split("+") if k.strip()]
    names = [ALIASES.get(n, n) for n in names]
    if "alt gr" in names:  # AltGr = Ctrl+Alt
        names = [n for n in names if n != "alt gr"] + ["ctrl", "alt"]
    mods = 0
    keys = []
    for name in names:
        if name in MODIFIERS:
            mods |= MODIFIERS[name]
        elif name in VK_CODES:
            keys.append(VK_CODES[name])
        else:
            raise ValueError(f"tasto non supportato: {name}")
    if len(keys) != 1:
        raise ValueError(f"combinazione non valida: {combo}")
    return mods, keys[0]


def is_valid(combo):
    try:
        parse(combo)
        return True
    except ValueError:
        return False


def _send_menu_mask():
    """Il tasto principale della combinazione non arriva alle app: se l'utente poi rilascia Alt
    (o Win) "da solo", Windows aprirebbe la barra dei menu della finestra (o il menu Start) e
    l'incolla finirebbe lì. Un tasto neutro (VK 0xE8, non assegnato) glielo impedisce."""
    user32.keybd_event(VK_MENU_MASK, 0, 0, 0)
    user32.keybd_event(VK_MENU_MASK, 0, KEYEVENTF_KEYUP, 0)


def is_key_down(vk):
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


class WinHotkeys:
    """Registra più combinazioni in un thread con la sua coda di messaggi Windows.
    Le callback vengono chiamate da quel thread (usare segnali Qt per tornare alla UI)."""

    def __init__(self):
        self._bindings = {}  # id -> [combo, mods, vk, callback, enabled]
        self._ops = queue.Queue()
        self._thread = None
        self._thread_id = None
        self._started = threading.Event()
        self.failed = []  # combinazioni che Windows ha rifiutato (già usate da un'altra app)

    def add(self, combo, callback, enabled=True):
        mods, vk = parse(combo)
        hid = len(self._bindings) + 1
        self._bindings[hid] = [combo, mods, vk, callback, enabled]
        return hid

    def start(self):
        self._thread = threading.Thread(target=self._run, name="hotkeys", daemon=True)
        self._thread.start()
        self._started.wait(2)

    def stop(self):
        if self._thread_id is not None:
            user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            self._thread.join(2)
        self._thread = self._thread_id = None
        self._started.clear()

    def set_enabled(self, hid, enabled):
        """Attiva/disattiva una combinazione (es. Esc solo durante la registrazione)."""
        if hid is None or self._thread_id is None:
            return
        self._ops.put((hid, enabled))
        user32.PostThreadMessageW(self._thread_id, WM_APP, 0, 0)

    def _register(self, hid):
        combo, mods, vk, _cb, _enabled = self._bindings[hid]
        if not user32.RegisterHotKey(None, hid, mods | MOD_NOREPEAT, vk):
            self.failed.append(combo)

    def _run(self):
        self._thread_id = kernel32.GetCurrentThreadId()
        msg = wintypes.MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_NOREMOVE)  # crea la coda di messaggi
        self.failed = []
        for hid, binding in self._bindings.items():
            if binding[4]:
                self._register(hid)
        self._started.set()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY and msg.wParam in self._bindings:
                    if self._bindings[msg.wParam][1] & (MOD_ALT | MOD_WIN):
                        _send_menu_mask()
                    self._bindings[msg.wParam][3]()
                elif msg.message == WM_APP:
                    while not self._ops.empty():
                        hid, enabled = self._ops.get()
                        binding = self._bindings.get(hid)
                        if binding is None or binding[4] == enabled:
                            continue
                        binding[4] = enabled
                        if enabled:
                            self._register(hid)
                        else:
                            user32.UnregisterHotKey(None, hid)
        finally:
            for hid in self._bindings:
                user32.UnregisterHotKey(None, hid)
