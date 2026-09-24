"""Crea le guide PDF per i clienti (italiano e inglese) da docs/guida_it.md e docs/guide_en.md,
con le immagini del programma disegnate nella lingua di ciascuna guida.

Uso (dalla cartella del progetto):  python docs/build_docs.py
Risultato: docs/ScriVoice-Guida-IT.pdf e docs/ScriVoice-Guide-EN.pdf
"""
import math
import os
import sys

DOCS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DOCS)
sys.path.insert(0, ROOT)

from PySide6.QtCore import QMarginsF, Qt, QUrl  # noqa: E402
from PySide6.QtGui import QColor, QImage, QPageLayout, QPageSize, QPainter, QPdfWriter, QTextDocument  # noqa: E402
from PySide6.QtWidgets import QApplication, QTabWidget  # noqa: E402

GUIDES = [("it", "guida_it.md", "ScriVoice-Guida-IT.pdf"), ("en", "guide_en.md", "ScriVoice-Guide-EN.pdf")]
CSS = """
body { font-family: 'Segoe UI', 'Helvetica Neue', Arial; font-size: 10.5pt; color: #1e1e24; }
h1 { font-size: 22pt; color: #1e1e24; }
h2 { font-size: 14pt; color: #2a2f36; margin-top: 18px; }
table { border-collapse: collapse; }
td, th { padding: 4px 10px; border: 1px solid #c8ccd2; }
"""


def render_images(lang, folder):
    import config
    import i18n
    import widget as w
    from settings_dialog import SettingsDialog
    i18n.set_language(lang)
    os.makedirs(folder, exist_ok=True)

    # widget: a riposo, in registrazione, incollato (su sfondo chiaro)
    shots = []
    for state in (w.IDLE, w.RECORDING, w.DONE):
        fw = w.FloatingWidget("Ctrl+Alt+Space", elapsed_source=lambda: 4)
        fw.set_appearance("dark", "#EB4048", 1.25, 1.0)
        fw.set_state(state)
        fw._anim.stop()
        fw._levels = [0.35 + 0.55 * abs(math.sin(i * 0.8)) for i in range(14)]
        shots.append(fw.grab().toImage())
    gap = 24
    sheet = QImage(sum(s.width() for s in shots) + gap * (len(shots) + 1), shots[0].height() + 2 * gap,
                   QImage.Format_ARGB32)
    sheet.fill(QColor("#eef0f3"))
    p = QPainter(sheet)
    x = gap
    for s in shots:
        p.drawImage(x, gap, s)
        x += s.width() + gap
    p.end()
    sheet.save(os.path.join(folder, "widget.png"))

    cfg = dict(config.DEFAULTS, language=lang, ui_language=lang)
    settings = SettingsDialog(cfg)
    settings.findChild(QTabWidget).setCurrentIndex(0)
    settings.adjustSize()
    settings.grab().save(os.path.join(folder, "settings.png"))


MAX_IMAGE_WIDTH = 560  # in pixel "logici" del documento: la pagina A4 con i margini ne misura ~660


def build_pdf(md_path, base_folder, out_path):
    doc = QTextDocument()
    doc.setDefaultStyleSheet(CSS)
    with open(md_path, encoding="utf-8") as f:
        doc.setMarkdown(f.read())
    # immagini caricate direttamente nel documento, dopo il testo (setMarkdown svuota le risorse)
    for name in ("widget.png", "settings.png"):
        img = QImage(os.path.join(base_folder, "img", name))
        if img.width() > MAX_IMAGE_WIDTH:
            img = img.scaledToWidth(MAX_IMAGE_WIDTH, Qt.SmoothTransformation)
        doc.addResource(QTextDocument.ImageResource, QUrl(f"img/{name}"), img)
    writer = QPdfWriter(out_path)
    writer.setPageLayout(QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Portrait,
                                     QMarginsF(18, 16, 18, 16), QPageLayout.Millimeter))
    writer.setResolution(300)
    writer.setTitle("ScriVoice")
    writer.setCreator("ScriVoice")
    doc.print_(writer)  # impagina da solo sul formato A4 del writer
    print("Creato", out_path)


def main():
    app = QApplication.instance() or QApplication(sys.argv)  # noqa: F841
    for lang, md, pdf in GUIDES:
        base = os.path.join(ROOT, "build", "docs", lang)
        render_images(lang, os.path.join(base, "img"))
        build_pdf(os.path.join(DOCS, md), base, os.path.join(DOCS, pdf))


if __name__ == "__main__":
    main()
