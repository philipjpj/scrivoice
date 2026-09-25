"""Pannello impostazioni: lingue, scorciatoie, microfono, trascrizione, sostituzioni, aspetto."""
import math
import random
import re

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QCheckBox, QColorDialog, QComboBox,
                               QDialog, QDialogButtonBox, QFormLayout, QFrame, QGroupBox,
                               QHBoxLayout, QHeaderView, QLabel, QPlainTextEdit, QPushButton,
                               QSlider, QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget,
                               QToolButton, QVBoxLayout, QWidget)

import autostart
import i18n
from hotkey import capture_async, is_valid, pretty
from i18n import tr
from recorder import list_input_devices, refresh_devices
from widget import ACCENTS, RECORDING, SIZES, THEMES, FloatingWidget

MODELS = [
    ("small", "Veloce: small (consigliato su questo PC)"),
    ("medium", "Più preciso: medium (lento, circa 1,5 GB di RAM)"),
    ("large-v3-turbo", "Massima precisione: large-v3-turbo (molto lento, circa 2 GB di RAM)"),
]
MODIFIERS = {"ctrl", "alt", "shift", "cmd", "windows", "left windows", "right windows", "alt gr",
             "right ctrl", "left ctrl", "right alt", "left alt", "right shift", "left shift"}


class HotkeyField(QWidget):
    """Pulsante che registra una combinazione di tasti quando viene cliccato."""
    changed = Signal()
    _captured = Signal(str)

    def __init__(self, combo, optional=False, placeholder="Nessuna"):
        super().__init__()
        self.combo = combo or ""
        self.placeholder = placeholder
        self.button = QPushButton()
        self.button.setMinimumWidth(190)
        self.button.clicked.connect(self._capture)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.button, 1)
        if optional:
            clear = QToolButton(text="✕", toolTip=tr("Rimuovi"))
            clear.clicked.connect(lambda: self._set(""))
            lay.addWidget(clear)
        self._captured.connect(self._on_captured)
        self._refresh()

    def _refresh(self):
        self.button.setText(pretty(self.combo) if self.combo else tr(self.placeholder))

    def _set(self, combo):
        self.combo = combo
        self._refresh()
        self.changed.emit()

    def _capture(self):
        self.button.setText(tr("Premi la combinazione…"))
        self.button.setEnabled(False)
        capture_async(self._captured.emit)

    def _on_captured(self, combo):
        self.button.setEnabled(True)
        if combo and is_valid(combo):
            self._set(combo)
        else:
            self._refresh()


class SettingsDialog(QDialog):
    def __init__(self, cfg, parent=None):
        super().__init__(parent)
        self.cfg = dict(cfg)
        self.setWindowTitle(tr("ScriVoice: impostazioni"))
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(560)

        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs)
        pages = {}
        for key, title in (("general", "Generale"), ("keys", "Scorciatoie"), ("quality", "Trascrizione"),
                           ("fix", "Correzioni"), ("look", "Aspetto")):
            page = QWidget()
            tabs.addTab(page, tr(title))
            pages[key] = QVBoxLayout(page)

        self._build_general_tab(pages["general"], cfg)
        self._build_keys_tab(pages["keys"], cfg)
        self._build_quality_tab(pages["quality"], cfg)
        self._build_fix_tab(pages["fix"], cfg)
        self._build_look_tab(pages["look"], cfg)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Save).setText(tr("Salva"))
        self.buttons.button(QDialogButtonBox.Cancel).setText(tr("Annulla"))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)
        self._validate()

    # ---- scheda Generale ---------------------------------------------------------------
    def _build_general_tab(self, lay, cfg):
        box = QGroupBox(tr("Lingua"))
        form = QFormLayout(box)
        self.ui_lang = QComboBox()
        for code, name in i18n.LANGUAGES:
            self.ui_lang.addItem(name, code)
        self.ui_lang.setCurrentIndex(max(0, self.ui_lang.findData(cfg.get("ui_language") or i18n.language())))
        form.addRow(tr("Lingua dell'interfaccia:"), self.ui_lang)
        self.dict_lang = QComboBox()
        for code, name in i18n.LANGUAGES:
            self.dict_lang.addItem(name, code)
        self.dict_lang.addItem(tr("Automatico (rileva la lingua)"), "auto")
        self.dict_lang.setCurrentIndex(max(0, self.dict_lang.findData(cfg.get("language", "en"))))
        form.addRow(tr("Lingua della dettatura:"), self.dict_lang)
        form.addRow(self._hint(tr("La lingua in cui parli. «Automatico» riconosce da solo italiano, "
                                  "inglese o spagnolo, ma sbaglia più spesso con frasi molto corte.")))
        lay.addWidget(box)

        box = QGroupBox(tr("Altro"))
        inner = QVBoxLayout(box)
        self.restore_cb = QCheckBox(tr("Dopo l'incolla ripristina il contenuto precedente degli appunti"))
        self.restore_cb.setChecked(cfg["restore_clipboard"])
        self.keep_rec = QCheckBox(tr("Salva le registrazioni (WAV + testo) nella cartella recordings"))
        self.keep_rec.setChecked(cfg["keep_recordings"])
        self.autostart_cb = QCheckBox(tr("Avvia ScriVoice all'accensione del computer"))
        self.autostart_cb.setVisible(autostart.is_supported())
        self.autostart_cb.setChecked(autostart.is_supported() and autostart.is_enabled())
        inner.addWidget(self.restore_cb)
        inner.addWidget(self.keep_rec)
        inner.addWidget(self.autostart_cb)
        lay.addWidget(box)
        lay.addStretch(1)

    # ---- scheda Scorciatoie ------------------------------------------------------------
    def _build_keys_tab(self, lay, cfg):
        box = QGroupBox(tr("Scorciatoie da tastiera"))
        form = QFormLayout(box)
        self.hk_start = HotkeyField(cfg["hotkey"])
        self.hk_stop = HotkeyField(cfg.get("stop_hotkey", ""), optional=True, placeholder="Uguale ad avvio")
        self.hk_cancel = HotkeyField(cfg.get("cancel_hotkey", "esc"), optional=True,
                                     placeholder="Disattivata")
        form.addRow(tr("Avvia / ferma:"), self.hk_start)
        form.addRow(self._hint(tr("Tocco breve: avvia e poi ferma. Tenuta premuta: registra finché "
                                  "non rilasci.")))
        form.addRow(tr("Solo ferma:"), self.hk_stop)
        form.addRow(tr("Annulla registrazione:"), self.hk_cancel)
        self.hold = QSpinBox(minimum=150, maximum=2000, singleStep=50, suffix=" ms")
        self.hold.setValue(int(cfg["hold_threshold"] * 1000))
        form.addRow(tr("Push-to-talk dopo:"), self.hold)
        self.hk_warning = self._hint("")
        self.hk_warning.setStyleSheet("color: #d97706;")
        form.addRow(self.hk_warning)
        for f in (self.hk_start, self.hk_stop, self.hk_cancel):
            f.changed.connect(self._validate)
        lay.addWidget(box)
        lay.addStretch(1)

    # ---- scheda Trascrizione -----------------------------------------------------------
    def _build_quality_tab(self, lay, cfg):
        box = QGroupBox(tr("Microfono"))
        form = QFormLayout(box)
        self.mic = QComboBox()
        self.mic.addItem(tr("Predefinito del sistema"), None)
        refresh_devices()
        for name in list_input_devices():
            self.mic.addItem(name, name)
        self.mic.setCurrentIndex(max(0, self.mic.findData(cfg.get("input_device"))))
        form.addRow(tr("Dispositivo:"), self.mic)
        form.addRow(self._hint(tr("Gli auricolari Bluetooth (es. AirPods) registrano in bassa qualità "
                                  "(16 kHz): se sei in un luogo silenzioso, il microfono del PC spesso "
                                  "è più preciso.")))
        lay.addWidget(box)

        box = QGroupBox(tr("Qualità della trascrizione"))
        form = QFormLayout(box)
        self.model = QComboBox()
        for key, label in MODELS:
            self.model.addItem(tr(label), key)
        self.model.setCurrentIndex(max(0, self.model.findData(cfg["model"])))
        form.addRow(tr("Modello:"), self.model)
        self.beam = QComboBox()
        self.beam.addItem(tr("Precisa (consigliata)"), 5)
        self.beam.addItem(tr("Veloce"), 1)
        self.beam.setCurrentIndex(0 if cfg["beam_size"] > 1 else 1)
        form.addRow(tr("Ricerca:"), self.beam)
        self.vocab = QPlainTextEdit(", ".join(cfg.get("vocabulary", [])))
        self.vocab.setFixedHeight(64)
        self.vocab.setPlaceholderText(tr("es. shortcut, task, React, nomi dei tuoi progetti…"))
        form.addRow(tr("Vocabolario personale:"), self.vocab)
        form.addRow(self._hint(tr("Parole, nomi e termini tecnici che usi spesso, separati da virgola.")))
        lay.addWidget(box)
        lay.addStretch(1)

    # ---- scheda Correzioni -------------------------------------------------------------
    def _build_fix_tab(self, lay, cfg):
        box = QGroupBox(tr("Sostituzioni automatiche (locali, gratuite)"))
        inner = QVBoxLayout(box)
        inner.addWidget(self._hint(tr("Quando Whisper sbaglia sempre la stessa parola, aggiungila qui: "
                                      "verrà sostituita su ogni trascrizione, solo se è una parola intera.")))
        self.repl = QTableWidget(0, 2)
        self.repl.setHorizontalHeaderLabels([tr("Parola sbagliata"), tr("Parola giusta")])
        self.repl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.repl.verticalHeader().setVisible(False)
        self.repl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.repl.setMinimumHeight(160)
        for wrong, right in cfg.get("replacements", []):
            self._add_replacement(wrong, right)
        row = QHBoxLayout()
        add_btn = QPushButton(tr("Aggiungi"))
        add_btn.clicked.connect(lambda: self._add_replacement("", "", edit=True))
        del_btn = QPushButton(tr("Rimuovi selezionate"))
        del_btn.clicked.connect(self._remove_replacements)
        row.addWidget(add_btn)
        row.addWidget(del_btn)
        row.addStretch(1)
        inner.addWidget(self.repl)
        inner.addLayout(row)
        lay.addWidget(box)
        lay.addStretch(1)

    # ---- scheda Aspetto ----------------------------------------------------------------
    def _build_look_tab(self, lay, cfg):
        self.accent = cfg.get("accent", ACCENTS[0][1])

        # anteprima animata su sfondo sfumato scuro -> chiaro (per giudicare anche l'opacità)
        frame = QFrame()
        frame.setFixedHeight(190)
        frame.setStyleSheet("QFrame { border-radius: 8px; background: qlineargradient("
                            "x1:0, y1:0, x2:1, y2:1, stop:0 #1f2430, stop:0.5 #5b6475, stop:1 #e6e9ef); }")
        preview_lay = QVBoxLayout(frame)
        preview_lay.setAlignment(Qt.AlignCenter)
        self.previews = [
            FloatingWidget(pretty(cfg["hotkey"]), parent=frame),
            FloatingWidget(pretty(cfg["hotkey"]), parent=frame, elapsed_source=lambda: 7,
                           level_source=lambda: 0.5 + 0.45 * math.sin(random.random() * math.tau)),
        ]
        self.previews[1].set_state(RECORDING)
        for w in self.previews:
            preview_lay.addWidget(w, 0, Qt.AlignCenter)
        lay.addWidget(frame)

        box = QGroupBox(tr("Stile del widget"))
        form = QFormLayout(box)
        self.theme = QComboBox()
        for key, theme in THEMES.items():
            self.theme.addItem(tr(theme["label"]), key)
        self.theme.setCurrentIndex(max(0, self.theme.findData(cfg.get("theme", "dark"))))
        form.addRow(tr("Tema:"), self.theme)

        swatches = QHBoxLayout()
        swatches.setSpacing(6)
        self.accent_group = QButtonGroup(self)
        for name, color in ACCENTS:
            b = QToolButton(toolTip=tr(name), checkable=True)
            b.setFixedSize(26, 26)
            b.setProperty("color", color)
            b.setStyleSheet(f"QToolButton {{ background: {color}; border-radius: 13px; "
                            f"border: 2px solid transparent; }}"
                            f"QToolButton:checked {{ border: 3px solid palette(text); }}")
            self.accent_group.addButton(b)
            swatches.addWidget(b)
        self.custom_btn = QToolButton(text=tr("Altro…"), checkable=True,
                                      toolTip=tr("Scegli un colore qualsiasi"))
        self.accent_group.addButton(self.custom_btn)
        swatches.addWidget(self.custom_btn)
        swatches.addStretch(1)
        self.accent_group.buttonClicked.connect(self._on_swatch)
        form.addRow(tr("Colore:"), swatches)

        self.size_box = QComboBox()
        for label, factor in SIZES:
            self.size_box.addItem(tr(label), factor)
        wanted = cfg.get("widget_size", 1.0)
        self.size_box.setCurrentIndex(min(range(len(SIZES)), key=lambda i: abs(SIZES[i][1] - wanted)))
        form.addRow(tr("Dimensione:"), self.size_box)

        opacity_row = QHBoxLayout()
        self.opacity = QSlider(Qt.Horizontal, minimum=40, maximum=100, singleStep=5, pageStep=10)
        self.opacity.setValue(round(cfg.get("opacity", 0.95) * 100))
        self.opacity_label = QLabel()
        self.opacity_label.setMinimumWidth(40)
        opacity_row.addWidget(self.opacity, 1)
        opacity_row.addWidget(self.opacity_label)
        form.addRow(tr("Opacità:"), opacity_row)
        form.addRow(self._hint(tr("Nel tema Neon il colore scelto diventa anche il bagliore del bordo.")))
        lay.addWidget(box)
        lay.addStretch(1)

        self.theme.currentIndexChanged.connect(self._update_preview)
        self.size_box.currentIndexChanged.connect(self._update_preview)
        self.opacity.valueChanged.connect(self._update_preview)
        self._select_swatch()
        self._update_preview()

    def _select_swatch(self):
        for b in self.accent_group.buttons():
            if b.property("color") and QColor(b.property("color")) == QColor(self.accent):
                b.setChecked(True)
                self.custom_btn.setStyleSheet("")
                return
        # colore personalizzato: il pulsante "Altro…" si colora con il colore scelto
        self.custom_btn.setChecked(True)
        self.custom_btn.setStyleSheet(f"QToolButton {{ border: 2px solid {self.accent}; "
                                      f"border-radius: 4px; padding: 3px 6px; }}")

    def _on_swatch(self, button):
        if button is self.custom_btn:
            color = QColorDialog.getColor(QColor(self.accent), self, tr("Colore di accento"))
            if color.isValid():
                self.accent = color.name()
        else:
            self.accent = button.property("color")
        self._select_swatch()
        self._update_preview()

    def _update_preview(self):
        self.opacity_label.setText(f"{self.opacity.value()}%")
        for w in self.previews:
            w.set_appearance(self.theme.currentData(), self.accent, self.size_box.currentData(),
                             self.opacity.value() / 100)

    # ---- sostituzioni ------------------------------------------------------------------
    def _add_replacement(self, wrong, right, edit=False):
        r = self.repl.rowCount()
        self.repl.insertRow(r)
        self.repl.setItem(r, 0, QTableWidgetItem(wrong))
        self.repl.setItem(r, 1, QTableWidgetItem(right))
        if edit:
            self.repl.setCurrentCell(r, 0)
            self.repl.editItem(self.repl.item(r, 0))

    def _remove_replacements(self):
        for r in sorted({i.row() for i in self.repl.selectedIndexes()}, reverse=True):
            self.repl.removeRow(r)

    def _replacements(self):
        pairs = []
        for r in range(self.repl.rowCount()):
            wrong, right = (self.repl.item(r, c).text().strip() if self.repl.item(r, c) else ""
                            for c in (0, 1))
            if wrong:
                pairs.append([wrong, right])
        return pairs

    @staticmethod
    def _hint(text):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: gray; font-size: 11px;")
        return lbl

    def _validate(self):
        start, stop, cancel = self.hk_start.combo, self.hk_stop.combo, self.hk_cancel.combo
        problems = []
        if not start:
            problems.append(tr("serve una scorciatoia di avvio."))
        elif start in (stop, cancel):
            problems.append(tr("avvio, stop e annulla devono essere diverse."))
        elif stop and stop == cancel:
            problems.append(tr("stop e annulla devono essere diverse."))
        warning = ""
        keys = [k.strip() for k in start.split("+")] if start else []
        if keys and all(k in MODIFIERS for k in keys):
            problems.append(tr("la scorciatoia deve includere un tasto oltre ai modificatori."))
        elif not problems and len(keys) == 1 and not re.fullmatch(r"f\d{1,2}", keys[0]):
            warning = tr("Attenzione: «{key}» da solo verrà bloccato in tutte le app. Meglio una "
                         "combinazione con Ctrl/Alt/Shift.", key=pretty(start))
        message = tr("Non valido: {problems}", problems=" ".join(problems)) if problems else warning
        self.hk_warning.setText(message)
        self.hk_warning.setVisible(bool(message))
        self.buttons.button(QDialogButtonBox.Save).setEnabled(not problems)

    def values(self):
        vocab = [w.strip() for w in re.split(r"[,\n;]", self.vocab.toPlainText()) if w.strip()]
        new = dict(self.cfg)
        new.update({
            "ui_language": self.ui_lang.currentData(),
            "language": self.dict_lang.currentData(),
            "hotkey": self.hk_start.combo,
            "stop_hotkey": self.hk_stop.combo,
            "cancel_hotkey": self.hk_cancel.combo,
            "hold_threshold": self.hold.value() / 1000,
            "input_device": self.mic.currentData(),
            "model": self.model.currentData(),
            "beam_size": self.beam.currentData(),
            "vocabulary": list(dict.fromkeys(vocab)),
            "replacements": self._replacements(),
            "theme": self.theme.currentData(),
            "accent": self.accent,
            "widget_size": self.size_box.currentData(),
            "opacity": self.opacity.value() / 100,
            "restore_clipboard": self.restore_cb.isChecked(),
            "keep_recordings": self.keep_rec.isChecked(),
            "autostart": self.autostart_cb.isChecked(),
        })
        return new
