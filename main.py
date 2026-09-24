"""ScriVoice: registra la voce, la trascrive in locale con Whisper e incolla il testo
nella finestra che aveva il focus (es. il terminale di Claude Code)."""
import multiprocessing
import os
import sys

if __name__ == "__main__":
    # Nell'app impacchettata alcune librerie (es. il lock di tqdm su Mac) avviano processi di
    # supporto rilanciando l'eseguibile stesso: senza questa riga partirebbe un secondo ScriVoice
    # completo. Deve stare prima di qualsiasi altro codice.
    multiprocessing.freeze_support()
import tempfile
import threading
import time

import applog
import paths
import winfix

log = applog.setup()  # prima di tutto: nell'app installata non c'è una console

winfix.preload_msvc_runtime()  # deve avvenire prima di caricare ctranslate2 (faster-whisper)

from PySide6.QtCore import QLockFile, QObject, QPoint, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices, QGuiApplication, QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

import autostart
import config
import i18n
import version
from hotkey import HotkeyInUse, HotkeyManager, pretty
from i18n import tr
from paster import Paster, accessibility_trusted, foreground_window, track_frontmost
from recorder import Recorder, save_wav
from settings_dialog import SettingsDialog
from textfix import apply_replacements
from transcriber import Transcriber
from widget import (C_BLUE, C_MUTED, DONE, ERROR, IDLE, LOADING, RECORDING, TRANSCRIBING,
                    FloatingWidget, make_icon)

RECORDINGS_DIR = paths.RECORDINGS_DIR
LOGO_PATH = paths.APP_ICON  # creato da setup_shortcut.py
INSTANCE_SERVER = "scrivoice_instance"
MIN_SECONDS = 0.3
IS_MAC = sys.platform == "darwin"


class Bridge(QObject):
    """Porta i risultati dei thread di lavoro nel thread principale Qt."""
    model_loaded = Signal(object)
    transcribed = Signal(str, object)


class App(QObject):
    def __init__(self, qapp, cfg):
        super().__init__()
        self.qapp = qapp
        self.cfg = cfg
        self.phase = "idle"          # idle | recording | transcribing
        self.mode = None             # pending | toggle | hold
        self.press_time = 0.0
        self.ignore_release = False
        self.target_hwnd = None
        self.last_text = ""
        self.widget_visible = True

        self.bridge = Bridge()
        self.bridge.model_loaded.connect(self._on_model_loaded)
        self.bridge.transcribed.connect(self._on_transcribed)

        self.recorder = Recorder(cfg["sample_rate"], cfg["input_device"])
        self.transcriber = self._make_transcriber(cfg)
        self.paster = Paster(cfg["restore_clipboard"], cfg["paste_delay_ms"])
        self.settings_dialog = None

        self.widget = FloatingWidget(pretty(cfg["hotkey"]), lambda: self.recorder.level,
                                     self.recorder.elapsed)
        self.widget.clicked.connect(self._on_widget_click)
        self.widget.moved.connect(self._on_widget_moved)
        self.widget.context_requested.connect(lambda pos: self.menu.popup(pos))
        self._apply_appearance(cfg)
        self._place_widget()
        self._watch_screens()

        self._build_tray()

        self.hotkey = HotkeyManager(cfg["hotkey"], cfg["stop_hotkey"], cfg["cancel_hotkey"])
        self.hotkey.start_pressed.connect(self._on_hotkey_pressed)
        self.hotkey.start_released.connect(self._on_hotkey_released)
        self.hotkey.stop_pressed.connect(self._on_stop_pressed)
        self.hotkey.cancel_pressed.connect(self._on_escape)

        # rete di sicurezza per il push-to-talk: se il rilascio del tasto va perso, lo rilevo io
        self._hold_watch = QTimer(self, interval=100, timeout=self._check_hold)

    @staticmethod
    def _make_transcriber(cfg):
        return Transcriber(cfg["model"], cfg["compute_type"], cfg["language"], cfg["beam_size"],
                           cfg["initial_prompt"], cfg["cpu_threads"], cfg["vocabulary"])

    def _load_model(self):
        self.widget.set_state(LOADING)
        transcriber = self.transcriber
        # ignora il risultato di un caricamento superato da un cambio di modello
        transcriber.load_async(
            lambda err: self.bridge.model_loaded.emit(err) if transcriber is self.transcriber else None)

    def start(self):
        self.widget.show()
        self._load_model()
        self._start_hotkeys()
        if IS_MAC:
            # su Mac cliccare il widget può attivare ScriVoice: ricordo l'app in cui l'utente scrive
            self._front_timer = QTimer(self, interval=300, timeout=track_frontmost)
            self._front_timer.start()
            QTimer.singleShot(1500, self._check_mac_permissions)

    def _check_mac_permissions(self):
        """Senza il permesso Accessibilità macOS blocca il Cmd+V simulato: lo segnalo subito."""
        if accessibility_trusted(prompt=True):
            return
        # dai sorgenti il permesso va al Terminale che avvia Python, nell'app installata a ScriVoice
        msg = tr("Per incollare il testo serve il permesso Accessibilità: Impostazioni di Sistema → "
                 "Privacy e sicurezza → Accessibilità → attiva {app}, poi riavvia ScriVoice.",
                 app="ScriVoice" if paths.FROZEN else "Terminale")
        self._error(tr("Manca il permesso Accessibilità"))
        self.tray.showMessage("ScriVoice", msg, self.icons["idle"], 15000)

    def _start_hotkeys(self):
        try:
            self.hotkey.start()
        except HotkeyInUse as e:
            self._error(tr("{keys} è già usata da un'altra app: scegline un'altra nelle impostazioni",
                           keys=", ".join(e.combos)))
        except Exception as e:  # noqa: BLE001
            self._error(tr("Scorciatoia non attiva: {e}", e=e))

    # ---- UI ------------------------------------------------------------------------------
    def _place_widget(self):
        x, y = self.cfg.get("widget_x"), self.cfg.get("widget_y")
        if x is None or y is None:
            screen = QGuiApplication.primaryScreen().availableGeometry()
            x = screen.right() - self.widget.width() - 24
            y = screen.bottom() - self.widget.height() - 24
        # posizione salvata fuori schermo (es. monitor scollegato): la riporto dentro
        self.widget.move(self.widget.clamped(QPoint(x, y)))

    def _watch_screens(self):
        """Se cambiano i monitor (scollegati, risoluzione, barra delle applicazioni) il widget
        viene riportato dentro lo schermo."""
        clamp_later = lambda *_: QTimer.singleShot(300, self._clamp_widget)  # noqa: E731
        for screen in QGuiApplication.screens():
            screen.availableGeometryChanged.connect(clamp_later)
        self.qapp.screenAdded.connect(
            lambda screen: screen.availableGeometryChanged.connect(clamp_later))
        self.qapp.screenRemoved.connect(clamp_later)

    def _apply_appearance(self, cfg):
        self.widget.set_appearance(cfg["theme"], cfg["accent"], cfg["widget_size"], cfg["opacity"])
        if hasattr(self, "icons"):
            self.icons["recording"] = make_icon(self.widget.accent)
            self.tray.setIcon(self.icons[self.phase])

    def _clamp_widget(self):
        """Riporta il widget dentro lo schermo (dopo un cambio di dimensione o di monitor)."""
        pos = self.widget.clamped(self.widget.pos())
        if pos != self.widget.pos():
            self.widget.move(pos)
            self._on_widget_moved(pos.x(), pos.y())

    def _on_widget_moved(self, x, y):
        self.cfg["widget_x"], self.cfg["widget_y"] = x, y
        config.save(self.cfg)

    def _build_tray(self):
        self.icons = {
            # a riposo il logo; durante registrazione e trascrizione il microfono colorato
            "idle": QIcon(LOGO_PATH) if os.path.exists(LOGO_PATH) else make_icon(C_MUTED),
            "recording": make_icon(self.widget.accent),
            "transcribing": make_icon(C_BLUE),
        }
        self.menu = QMenu()
        self.act_toggle_widget = QAction(self.menu, triggered=self._toggle_widget_visibility)
        self.act_copy = QAction(self.menu, enabled=False,
                                triggered=lambda: QGuiApplication.clipboard().setText(self.last_text))
        self.act_recordings = QAction(self.menu, triggered=self._open_recordings)
        self.act_settings = QAction(self.menu, triggered=self.open_settings)
        self.act_about = QAction(self.menu, triggered=self._show_about)
        self.act_quit = QAction(self.menu, triggered=self.quit)
        self.menu.addAction(self.act_toggle_widget)
        self.menu.addAction(self.act_copy)
        self.menu.addSeparator()
        self.menu.addAction(self.act_recordings)
        self.menu.addAction(self.act_settings)
        self.menu.addAction(self.act_about)
        self.menu.addSeparator()
        self.menu.addAction(self.act_quit)
        self._retranslate()

        self.tray = QSystemTrayIcon(self.icons["idle"])
        self.tray.setToolTip("ScriVoice")
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(
            lambda reason: self._toggle_widget_visibility()
            if reason == QSystemTrayIcon.Trigger else None)
        self.tray.show()

    def _retranslate(self):
        self.act_toggle_widget.setText(tr("Nascondi widget") if self.widget_visible else tr("Mostra widget"))
        self.act_copy.setText(tr("Copia ultima trascrizione"))
        self.act_recordings.setText(tr("Apri cartella registrazioni"))
        self.act_settings.setText(tr("Impostazioni…"))
        self.act_about.setText(tr("Informazioni"))
        self.act_quit.setText(tr("Esci"))
        self.widget.update()

    def _toggle_widget_visibility(self):
        self.widget_visible = not self.widget_visible
        self.widget.setVisible(self.widget_visible)
        self._retranslate()

    def _open_recordings(self):
        os.makedirs(RECORDINGS_DIR, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(RECORDINGS_DIR))

    def _show_about(self):
        lines = [f"<b>ScriVoice {version.__version__}</b>",
                 tr("Dettatura vocale: la voce viene trascritta sul tuo computer e il testo incollato "
                    "dove stai scrivendo.")]
        lines.append(tr("Software libero e open source, licenza MIT."))
        lines.append(tr("Codice, aggiornamenti e segnalazioni: {link}",
                        link=f'<a href="{version.PROJECT_URL}">{version.PROJECT_URL}</a>'))
        QMessageBox.about(None, tr("Informazioni su ScriVoice"), "<br><br>".join(lines))

    # ---- impostazioni ------------------------------------------------------------------------
    def open_settings(self):
        if self.settings_dialog is not None:
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            return
        if self.phase == "recording":
            self._on_escape()
        # le scorciatoie globali restano spente mentre il pannello è aperto (servono per registrarle)
        self.hotkey.stop()
        dlg = SettingsDialog(self.cfg)
        dlg.setWindowIcon(self.qapp.windowIcon())
        self.settings_dialog = dlg
        dlg.finished.connect(self._on_settings_closed)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    def _on_settings_closed(self, result):
        dlg, self.settings_dialog = self.settings_dialog, None
        if result == SettingsDialog.Accepted:
            self.apply_settings(dlg.values())
        self._start_hotkeys()
        dlg.deleteLater()

    def apply_settings(self, new):
        # l'avvio automatico vive nel sistema operativo, non in config.json
        wanted_autostart = new.pop("autostart", None)
        if wanted_autostart is not None and autostart.is_supported():
            try:
                autostart.set_enabled(wanted_autostart)
            except OSError as e:
                log.warning("Avvio automatico non modificato: %s", e)
        old, self.cfg = self.cfg, new
        config.save(new)
        self.hotkey.configure(new["hotkey"], new["stop_hotkey"], new["cancel_hotkey"])
        self.widget.hotkey_label = pretty(new["hotkey"])
        self._apply_appearance(new)
        self._clamp_widget()
        self.recorder.device = new["input_device"]
        self.paster.restore_clipboard = new["restore_clipboard"]
        if new["model"] != old["model"]:
            self.transcriber = self._make_transcriber(new)
            self._load_model()
        else:
            self.transcriber.beam_size = new["beam_size"]
            self.transcriber.vocabulary = list(new["vocabulary"])
            self.transcriber.language = new["language"]
        if new["ui_language"] != old["ui_language"]:
            i18n.set_language(new["ui_language"])
            self._retranslate()
        self.tray.showMessage("ScriVoice", tr("Impostazioni salvate."), self.icons["idle"], 2000)

    def _set_phase(self, phase):
        self.phase = phase
        # Esc e "solo ferma" vengono presi dal programma solo mentre registra
        self.hotkey.set_recording(phase == "recording")
        self.tray.setIcon(self.icons[phase])

    def _error(self, msg):
        self.widget.set_state(ERROR, msg, revert_ms=3500)
        self.widget.setToolTip(msg)

    # ---- scorciatoia: tap = toggle, tenuta = push-to-talk ---------------------------------
    def _on_hotkey_pressed(self, when=None):
        if self.phase == "idle":
            if self._start_recording():
                self.mode = "pending"
                self.press_time = when or time.monotonic()
                self._hold_watch.start()
        elif self.phase == "recording" and self.mode == "toggle":
            self.ignore_release = True
            self._stop_and_transcribe()

    def _on_hotkey_released(self, when=None):
        if self.ignore_release:
            self.ignore_release = False
            return
        if self.phase != "recording" or self.mode != "pending":
            return
        self._hold_watch.stop()
        # durata misurata con gli istanti reali del tasto, non con il momento in cui arriva il segnale
        if (when or time.monotonic()) - self.press_time >= self.cfg["hold_threshold"]:
            self._stop_and_transcribe()      # push-to-talk
        else:
            self.mode = "toggle"             # tap: continua finché non ripremi

    def _check_hold(self):
        if self.phase != "recording" or self.mode != "pending":
            self._hold_watch.stop()
        elif not self.hotkey.active:
            # scorciatoie spente mentre si teneva premuto (es. apertura impostazioni): chiudo qui
            self.hotkey.reset_down()
            self._on_hotkey_released()

    def _on_stop_pressed(self):
        if self.phase == "recording":
            self._stop_and_transcribe()

    def _on_widget_click(self):
        if self.phase == "idle":
            if self._start_recording():
                self.mode = "toggle"
        elif self.phase == "recording":
            self._stop_and_transcribe()

    def _on_escape(self):
        if self.phase == "recording":
            self._hold_watch.stop()
            self.recorder.stop()
            self._set_phase("idle")
            self.widget.set_state(DONE, tr("Annullato"), revert_ms=1200)

    # ---- registrazione e trascrizione -----------------------------------------------------
    def _start_recording(self):
        # il widget non prende mai il focus, quindi questa è la finestra dove incollare
        self.target_hwnd = foreground_window()
        try:
            self.recorder.start()
        except Exception as e:  # noqa: BLE001
            self._error(tr("Microfono non disponibile: {e}", e=e))
            return False
        log.info("Registrazione avviata (%d Hz)", self.recorder.sample_rate)
        self._set_phase("recording")
        self.widget.set_state(RECORDING)
        return True

    def _stop_and_transcribe(self):
        self._hold_watch.stop()
        audio, rate = self.recorder.stop()
        log.info("Registrazione fermata: %.1f s", len(audio) / rate if rate else 0)
        if len(audio) < MIN_SECONDS * rate:
            self._set_phase("idle")
            self.widget.set_state(DONE, tr("Troppo breve"), revert_ms=1200)
            return
        self._set_phase("transcribing")
        self.widget.set_state(TRANSCRIBING)
        threading.Thread(target=self._transcribe_worker, args=(audio, rate),
                         name="transcribe", daemon=True).start()

    def _transcribe_worker(self, audio, rate):
        try:
            wav = None
            if self.cfg["keep_recordings"]:
                wav = save_wav(audio, rate, RECORDINGS_DIR, self.cfg["max_recordings"])
            text = self.transcriber.transcribe(audio, rate)
            text = apply_replacements(text, self.cfg["replacements"])
            if wav and text:
                with open(os.path.splitext(wav)[0] + ".txt", "w", encoding="utf-8") as f:
                    f.write(text)
            self.bridge.transcribed.emit(text, None)
        except Exception as e:  # noqa: BLE001
            log.exception("Trascrizione non riuscita")
            self.bridge.transcribed.emit("", e)

    def _on_transcribed(self, text, error):
        log.info("Trascrizione finita: %d caratteri%s", len(text), " (errore)" if error else "")
        self._set_phase("idle")
        if error is not None:
            self._error(tr("Trascrizione fallita: {e}", e=error))
            return
        if not text:
            self.widget.set_state(ERROR, tr("Nessun parlato rilevato"), revert_ms=2000)
            return
        self.last_text = text
        self.act_copy.setEnabled(True)
        self.widget.setToolTip(text)
        try:
            self.paster.paste(text, self.target_hwnd)
        except Exception as e:  # noqa: BLE001
            QGuiApplication.clipboard().setText(text)
            self._error(tr("Incolla fallito, testo negli appunti ({e})", e=e))
            return
        self.widget.set_state(DONE, tr("Incollato"), revert_ms=1500)

    def _on_model_loaded(self, error):
        log.info("Modello caricato" if error is None else f"Modello non caricato: {error}")
        if error is not None:
            self._error(tr("Modello non caricato: {e}", e=error))
        elif self.widget.state == LOADING:
            self.widget.set_state(IDLE)

    def quit(self):
        self.hotkey.stop()
        if self.recorder.is_recording:
            self.recorder.stop()
        self.tray.hide()
        self.qapp.quit()


    def show_widget(self):
        if not self.widget_visible:
            self._toggle_widget_visibility()
        self.widget.raise_()


def notify_running_instance():
    """Chiede all'istanza già aperta di mostrare il widget (es. clic sull'icona della taskbar)."""
    sock = QLocalSocket()
    sock.connectToServer(INSTANCE_SERVER)
    if sock.waitForConnected(500):
        sock.write(b"show")
        sock.waitForBytesWritten(500)
        sock.disconnectFromServer()


def run_selftest(out_path):
    """Usato dalle build automatiche: con l'app impacchettata carica il modello incluso, trascrive
    l'audio di prova e scrive il risultato in out_path (JSON). Codice di uscita 0 se funziona."""
    import faulthandler
    import json
    import soundfile as sf
    console = sys.__stderr__  # la console vera (nelle build automatiche finisce nel registro di GitHub)

    def step(msg):
        if console is not None:
            console.write(f"[selftest] {msg}\n")
            console.flush()

    # se qualcosa si blocca, dopo 3 minuti stampo dove si trova ogni thread ed esco
    if console is not None:
        faulthandler.dump_traceback_later(180, exit=True, file=console)
    result = {"version": version.__version__, "bundled_model": paths.bundled_model("small") is not None}
    step(f"modello incluso: {paths.bundled_model('small')}")
    try:
        audio, rate = sf.read(paths.resource("assets", "selftest.wav"), dtype="float32")
        step(f"audio di prova: {len(audio) / rate:.1f} s")
        transcriber = Transcriber("small", language="en")
        transcriber.load_async()
        transcriber._ready.wait()
        step("modello caricato" if transcriber.ready else f"modello NON caricato: {transcriber._error}")
        text = transcriber.transcribe(audio, rate)
        step(f"trascritto: {text!r}")
        result.update(ok=bool(text), text=text)
    except Exception as e:  # noqa: BLE001
        log.exception("Autotest non riuscito")
        result.update(ok=False, error=repr(e))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return 0 if result["ok"] else 1


def main():
    if "--selftest" in sys.argv:
        idx = sys.argv.index("--selftest")
        out = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else os.path.join(paths.DATA_DIR, "selftest.json")
        return run_selftest(out)

    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)
    qapp.setApplicationName("ScriVoice")
    if IS_MAC:
        try:  # app della barra dei menu: niente icona nel Dock
            from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
            NSApplication.sharedApplication().setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        except Exception:  # noqa: BLE001
            pass
    if os.path.exists(LOGO_PATH):
        qapp.setWindowIcon(QIcon(LOGO_PATH))

    lock = QLockFile(os.path.join(tempfile.gettempdir(), "scrivoice.lock"))
    if not lock.tryLock(100):
        notify_running_instance()
        return 0

    log.info("ScriVoice %s avviato (%s)", version.__version__, sys.platform)
    cfg = config.load()
    i18n.set_language(cfg["ui_language"])
    app = App(qapp, cfg)
    server = QLocalServer()
    QLocalServer.removeServer(INSTANCE_SERVER)
    server.listen(INSTANCE_SERVER)
    server.newConnection.connect(lambda: (server.nextPendingConnection(), app.show_widget()))
    app.start()
    return qapp.exec()


if __name__ == "__main__":
    sys.exit(main())
