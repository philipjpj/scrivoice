"""Widget flottante sempre in primo piano che non ruba mai il focus alla finestra attiva."""
import ctypes
import math
import sys

from PySide6.QtCore import QPoint, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from i18n import tr

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"

if IS_WIN:
    GWL_EXSTYLE = -20
    WS_EX_TOPMOST = 0x00000008
    WS_EX_TOOLWINDOW = 0x00000080
    WS_EX_NOACTIVATE = 0x08000000

    _user32 = ctypes.WinDLL("user32")
    _user32.GetWindowLongPtrW.restype = ctypes.c_ssize_t
    _user32.GetWindowLongPtrW.argtypes = (ctypes.c_void_p, ctypes.c_int)
    _user32.SetWindowLongPtrW.restype = ctypes.c_ssize_t
    _user32.SetWindowLongPtrW.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t)


def _make_non_activating(widget):
    """La finestra non deve mai prendere il focus alla finestra in cui l'utente sta scrivendo."""
    if IS_WIN:
        hwnd = int(widget.winId())
        style = _user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        _user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE,
                                  style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_TOPMOST)
    elif IS_MAC:
        try:
            import objc
            from AppKit import (NSWindowCollectionBehaviorCanJoinAllSpaces,
                                NSWindowCollectionBehaviorFullScreenAuxiliary)
            window = objc.objc_object(c_void_p=int(widget.winId())).window()
            window.setStyleMask_(window.styleMask() | (1 << 7))  # NSWindowStyleMaskNonactivatingPanel
            window.setHidesOnDeactivate_(False)
            # visibile su tutte le scrivanie e sopra le app a schermo intero (es. il Terminale)
            window.setCollectionBehavior_(NSWindowCollectionBehaviorCanJoinAllSpaces
                                          | NSWindowCollectionBehaviorFullScreenAuxiliary)
        except Exception as e:  # noqa: BLE001 - il widget funziona comunque
            print(f"Impostazioni finestra macOS non applicate: {e}", file=sys.stderr)

IDLE, LOADING, RECORDING, TRANSCRIBING, DONE, ERROR = (
    "idle", "loading", "recording", "transcribing", "done", "error")

# Colori fissi con significato (usati anche per le icone della tray)
C_MUTED = QColor(150, 152, 160)
C_RED = QColor(235, 64, 72)
C_BLUE = QColor(90, 150, 255)
C_GREEN = QColor(60, 200, 120)
C_ORANGE = QColor(245, 160, 50)

# None = usa il colore di accento. *_alpha = opacità 0-255 del colore. Le etichette passano da tr().
THEMES = {
    "dark": {
        "label": "Scuro", "bg": "#1C1D22", "bg_alpha": 240, "border": "#FFFFFF", "border_alpha": 28,
        "text": "#EBEBF0", "muted": "#9698A0", "badge": "#FFFFFF", "badge_alpha": 18,
        "spinner": "#5A96FF", "glow": False,
    },
    "light": {
        "label": "Chiaro", "bg": "#FAFAFC", "bg_alpha": 245, "border": "#000000", "border_alpha": 38,
        "text": "#1E1E24", "muted": "#6E7078", "badge": "#000000", "badge_alpha": 14,
        "spinner": "#2F6FEB", "glow": False,
    },
    "neon": {
        "label": "Neon", "bg": "#07070D", "bg_alpha": 240, "border": None, "border_alpha": 230,
        "text": "#E9FEFF", "muted": "#9FB3C8", "badge": None, "badge_alpha": 38,
        "spinner": None, "glow": True,
    },
}
ACCENTS = [("Rosso", "#EB4048"), ("Blu", "#3B82F6"), ("Verde", "#22C55E"), ("Viola", "#8B5CF6"),
           ("Arancio", "#F59E0B"), ("Ciano", "#00E5FF"), ("Magenta", "#FF2BD6")]
SIZES = [("Piccolo", 0.85), ("Medio", 1.0), ("Grande", 1.25)]
DEFAULT_ACCENT = "#EB4048"


def draw_mic(p, cx, cy, s, color):
    """Icona microfono centrata in (cx, cy), alta circa s."""
    pen = QPen(color, max(1.5, s * 0.1), Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(color)
    w, h = s * 0.36, s * 0.52
    p.drawRoundedRect(QRectF(cx - w / 2, cy - s * 0.5, w, h), w / 2, w / 2)
    p.setBrush(Qt.NoBrush)
    arc_w = s * 0.62
    p.drawArc(QRectF(cx - arc_w / 2, cy - s * 0.3, arc_w, s * 0.55), 180 * 16, 180 * 16)
    p.drawLine(QPoint(round(cx), round(cy + s * 0.25)), QPoint(round(cx), round(cy + s * 0.45)))


def screen_area(point):
    """Area utile (senza barra delle applicazioni) dello schermo che contiene point,
    oppure dello schermo più vicino se point è fuori da tutti gli schermi."""
    screen = QGuiApplication.screenAt(point)
    if screen is None:
        def distance(s):
            r = s.availableGeometry()
            dx = max(r.left() - point.x(), 0, point.x() - r.right())
            dy = max(r.top() - point.y(), 0, point.y() - r.bottom())
            return dx * dx + dy * dy
        screen = min(QGuiApplication.screens(), key=distance)
    return screen.availableGeometry()


def make_icon(color=C_MUTED, bg=QColor(28, 29, 34)):
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(Qt.NoPen)
    p.setBrush(bg)
    p.drawEllipse(2, 2, 60, 60)
    draw_mic(p, 32, 32, 36, color)
    p.end()
    return QIcon(pm)


class FloatingWidget(QWidget):
    clicked = Signal()
    context_requested = Signal(QPoint)
    moved = Signal(int, int)

    # dimensioni della pillola a scala 1; MARGIN lascia spazio al bagliore del tema Neon
    W, H, MARGIN = 196, 46, 8

    def __init__(self, hotkey_label, level_source=None, elapsed_source=None, parent=None):
        if parent is None:
            super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
                             | Qt.WindowDoesNotAcceptFocus)
            self.setAttribute(Qt.WA_ShowWithoutActivating)
            self.setAttribute(Qt.WA_MacAlwaysShowToolWindow)  # su Mac resta visibile anche fuori focus
            self.setCursor(Qt.PointingHandCursor)
        else:  # anteprima dentro il pannello impostazioni
            super().__init__(parent)
            self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.hotkey_label = hotkey_label
        self.level_source = level_source or (lambda: 0.0)
        self.elapsed_source = elapsed_source or (lambda: 0.0)
        self.state = IDLE
        self.message = ""
        self._phase = 0.0
        self._levels = [0.0] * 14
        self._press_pos = None
        self._dragging = False

        self._anim = QTimer(self, interval=33, timeout=self._tick)
        self._revert = QTimer(self, singleShot=True, timeout=lambda: self.set_state(IDLE))
        self.set_appearance()

    # ---- aspetto ------------------------------------------------------------------------
    def set_appearance(self, theme="dark", accent=DEFAULT_ACCENT, scale=1.0, opacity=0.95):
        self.theme = THEMES.get(theme, THEMES["dark"])
        self.accent = QColor(accent) if QColor.isValidColorName(accent or "") else QColor(DEFAULT_ACCENT)
        self.scale_f = min(2.0, max(0.5, float(scale)))
        self.opacity = min(1.0, max(0.3, float(opacity)))
        self.setFixedSize(round((self.W + 2 * self.MARGIN) * self.scale_f),
                          round((self.H + 2 * self.MARGIN) * self.scale_f))
        self.update()

    def clamped(self, pos, ref=None):
        """Posizione più vicina a pos che tiene il widget interamente dentro uno schermo.
        ref sceglie lo schermo (durante il trascinamento: il punto sotto il mouse)."""
        if ref is None:
            ref = QRect(pos, self.size()).center()
        area = screen_area(ref)
        x = min(max(pos.x(), area.left()), area.right() - self.width() + 1)
        y = min(max(pos.y(), area.top()), area.bottom() - self.height() + 1)
        return QPoint(x, y)

    def _color(self, key):
        value = self.theme[key]
        color = QColor(value) if value else QColor(self.accent)
        alpha = self.theme.get(key + "_alpha")
        if alpha is not None:
            color.setAlpha(alpha)
        return color

    # ---- stato -------------------------------------------------------------------------
    def set_state(self, state, message="", revert_ms=0):
        self.state = state
        self.message = message
        self._levels = [0.0] * len(self._levels)
        animated = state in (LOADING, RECORDING, TRANSCRIBING)
        if animated and not self._anim.isActive():
            self._anim.start()
        elif not animated:
            self._anim.stop()
        self._revert.stop()
        if revert_ms:
            self._revert.start(revert_ms)
        self.update()

    def _tick(self):
        self._phase = (self._phase + 0.033) % 1000
        if self.state == RECORDING:
            self._levels = self._levels[1:] + [self.level_source()]
        self.update()

    # ---- finestra senza focus ------------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        if self.isWindow():
            _make_non_activating(self)

    # ---- mouse: click = toggle, trascinamento = sposta -----------------------------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._press_pos = e.globalPosition().toPoint()
            self._win_start = self.pos()
            self._dragging = False
        elif e.button() == Qt.RightButton:
            self.context_requested.emit(e.globalPosition().toPoint())

    def mouseMoveEvent(self, e):
        if self._press_pos is None:
            return
        delta = e.globalPosition().toPoint() - self._press_pos
        if self._dragging or delta.manhattanLength() > 4:
            self._dragging = True
            # segue il mouse anche tra più schermi, ma non esce mai dai bordi dello schermo
            self.move(self.clamped(self._win_start + delta, e.globalPosition().toPoint()))

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.LeftButton or self._press_pos is None:
            return
        if self._dragging:
            self.moved.emit(self.x(), self.y())
        else:
            self.clicked.emit()
        self._press_pos = None
        self._dragging = False

    # ---- disegno (in coordinate a scala 1, poi scalate) -----------------------------------
    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setOpacity(self.opacity)
        p.scale(self.scale_f, self.scale_f)
        p.translate(self.MARGIN, self.MARGIN)

        r = QRectF(0.5, 0.5, self.W - 1, self.H - 1)
        radius = r.height() / 2
        if self.theme["glow"]:
            self._paint_glow(p, r, radius)
        p.setPen(QPen(self._color("border"), 1.5 if self.theme["glow"] else 1))
        p.setBrush(self._color("bg"))
        p.drawRoundedRect(r, radius, radius)

        cx, cy, rad = self.H / 2, self.H / 2, 15
        self._paint_badge(p, cx, cy, rad)

        text_x = self.H + 2
        text_rect = QRectF(text_x, 0, self.W - text_x - 14, self.H)
        f = QFont("Segoe UI", 9)
        p.setFont(f)

        if self.state == RECORDING:
            secs = int(self.elapsed_source())
            f.setBold(True)
            p.setFont(f)
            p.setPen(self._color("text"))
            p.drawText(QRectF(text_x, 0, 40, self.H), Qt.AlignVCenter | Qt.AlignLeft,
                       f"{secs // 60}:{secs % 60:02d}")
            self._paint_levels(p, text_x + 42, self.W - 16)
        else:
            label, color = {
                IDLE: (self.hotkey_label, self._color("muted")),
                LOADING: (tr("Carico il modello…"), self._color("muted")),
                TRANSCRIBING: (self.message or tr("Trascrivo…"), self._color("text")),
                DONE: (self.message or tr("Incollato"), self._color("text")),
                ERROR: (self.message or tr("Errore"), C_ORANGE),
            }[self.state]
            p.setPen(color)
            elided = p.fontMetrics().elidedText(label, Qt.ElideRight, int(text_rect.width()))
            p.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, elided)
        p.end()

    def _paint_glow(self, p, r, radius):
        # bagliore neon: anelli sempre più larghi e trasparenti; pulsa durante la registrazione
        strength = 1.0
        if self.state == RECORDING:
            strength = 1.3 + 0.5 * math.sin(self._phase * 2 * math.pi * 1.2)
        p.setBrush(Qt.NoBrush)
        for i in range(self.MARGIN - 1, 0, -1):
            c = QColor(self.accent)
            c.setAlpha(min(255, int(strength * 70 * (1 - i / self.MARGIN) ** 2)))
            p.setPen(QPen(c, 2))
            p.drawRoundedRect(r.adjusted(-i, -i, i, i), radius + i, radius + i)

    def _paint_badge(self, p, cx, cy, rad):
        circle = QRectF(cx - rad, cy - rad, 2 * rad, 2 * rad)
        p.setPen(Qt.NoPen)
        if self.state == RECORDING:
            pulse = 0.5 + 0.5 * math.sin(self._phase * 2 * math.pi * 1.2)
            halo = QColor(self.accent)
            halo.setAlpha(int(40 + 60 * pulse))
            p.setBrush(halo)
            p.drawEllipse(QRectF(cx - rad - 3, cy - rad - 3, 2 * rad + 6, 2 * rad + 6))
            p.setBrush(self.accent)
            p.drawEllipse(circle)
            draw_mic(p, cx, cy, 16, QColor("white"))
        elif self.state in (TRANSCRIBING, LOADING):
            p.setBrush(self._color("badge"))
            p.drawEllipse(circle)
            color = self._color("spinner") if self.state == TRANSCRIBING else self._color("muted")
            color.setAlpha(255)
            p.setPen(QPen(color, 2.5, Qt.SolidLine, Qt.RoundCap))
            start = int(-self._phase * 360 * 1.5 * 16) % (360 * 16)
            p.drawArc(QRectF(cx - rad + 4, cy - rad + 4, 2 * rad - 8, 2 * rad - 8), start, 100 * 16)
        elif self.state == DONE:
            p.setBrush(C_GREEN)
            p.drawEllipse(circle)
            path = QPainterPath(QPoint(round(cx - 6), round(cy)))
            path.lineTo(cx - 1.5, cy + 4.5)
            path.lineTo(cx + 6.5, cy - 4.5)
            p.setPen(QPen(QColor("white"), 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.setBrush(Qt.NoBrush)
            p.drawPath(path)
        elif self.state == ERROR:
            p.setBrush(C_ORANGE)
            p.drawEllipse(circle)
            p.setPen(QColor("white"))
            f = QFont("Segoe UI", 11)
            f.setBold(True)
            p.setFont(f)
            p.drawText(circle, Qt.AlignCenter, "!")
        else:
            p.setBrush(self._color("badge"))
            p.drawEllipse(circle)
            mic = self.accent if self.theme["glow"] else self._color("muted")
            draw_mic(p, cx, cy, 16, mic)

    def _paint_levels(self, p, x0, x1):
        n = len(self._levels)
        step = (x1 - x0) / n
        bar_w = max(2.0, step * 0.55)
        p.setPen(Qt.NoPen)
        p.setBrush(self.accent)
        max_h = self.H * 0.5
        for i, lv in enumerate(self._levels):
            h = max(3.0, lv * max_h)
            x = x0 + i * step
            p.drawRoundedRect(QRectF(x, self.H / 2 - h / 2, bar_w, h), bar_w / 2, bar_w / 2)
