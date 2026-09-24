"""Parte Windows dell'incolla: finestra in primo piano, focus e Ctrl+V simulato (SendInput)."""
import ctypes
import time
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL, VK_MENU, VK_SHIFT, VK_LWIN, VK_RWIN, VK_V = 0x11, 0x12, 0x10, 0x5B, 0x5C, 0x56
SW_RESTORE = 9

ULONG_PTR = ctypes.c_size_t


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
user32.BringWindowToTop.argtypes = (wintypes.HWND,)
user32.IsWindow.argtypes = (wintypes.HWND,)
user32.IsIconic.argtypes = (wintypes.HWND,)
user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.AttachThreadInput.argtypes = (wintypes.DWORD, wintypes.DWORD, wintypes.BOOL)
user32.GetAsyncKeyState.argtypes = (ctypes.c_int,)
user32.GetAsyncKeyState.restype = ctypes.c_short


def foreground_window():
    return user32.GetForegroundWindow()


def _key(vk, up=False):
    inp = INPUT(type=INPUT_KEYBOARD)
    inp.u.ki = KEYBDINPUT(wVk=vk, wScan=0, dwFlags=KEYEVENTF_KEYUP if up else 0, time=0, dwExtraInfo=0)
    return inp


def send_paste():
    seq = (INPUT * 4)(_key(VK_CONTROL), _key(VK_V), _key(VK_V, up=True), _key(VK_CONTROL, up=True))
    sent = user32.SendInput(4, seq, ctypes.sizeof(INPUT))
    if sent != 4:
        raise ctypes.WinError(ctypes.get_last_error())


def wait_modifiers_released(timeout=1.5):
    """Se l'utente tiene ancora premuti Alt/Shift/Win, Ctrl+V diventerebbe un'altra combinazione."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not any(user32.GetAsyncKeyState(vk) & 0x8000
                   for vk in (VK_CONTROL, VK_MENU, VK_SHIFT, VK_LWIN, VK_RWIN)):
            return True
        time.sleep(0.02)
    return False


def focus_window(hwnd):
    """Riporta in primo piano hwnd (se nel frattempo il focus è cambiato)."""
    if not hwnd or not user32.IsWindow(hwnd):
        return False
    fg = user32.GetForegroundWindow()
    if fg == hwnd:
        return True
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    cur = kernel32.GetCurrentThreadId()
    fg_thread = user32.GetWindowThreadProcessId(fg, None) if fg else 0
    attached = bool(fg_thread and fg_thread != cur and user32.AttachThreadInput(cur, fg_thread, True))
    try:
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
    finally:
        if attached:
            user32.AttachThreadInput(cur, fg_thread, False)
    time.sleep(0.05)
    return user32.GetForegroundWindow() == hwnd
