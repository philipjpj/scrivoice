"""Prepara l'icona dell'app dal logo (assets/logo_transparent.png) e crea i collegamenti su Desktop
e nel menu Start.

- assets/app_icon.png: logo quadrato con l'interno del fumetto bianco, così si vede anche su sfondi
  scuri (usato da main.py per l'icona della finestra e della tray, anche su Mac);
- assets/app_icon_<codice>.ico: la stessa icona in tutte le dimensioni per i collegamenti di Windows
  (generata qui, non salvata nel progetto).

Uso:  .venv\\Scripts\\python setup_shortcut.py
"""
import glob
import hashlib
import io
import os
import struct
import subprocess
import sys

import numpy as np
from PySide6.QtCore import QBuffer, QIODevice, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from scipy import ndimage

APP_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_LOGO = os.path.join(APP_DIR, "assets", "logo_transparent.png")
APP_ICON_PNG = os.path.join(APP_DIR, "assets", "app_icon.png")
PYTHONW = os.path.join(APP_DIR, ".venv", "Scripts", "pythonw.exe")
MAIN = os.path.join(APP_DIR, "main.py")
NAME = "ScriVoice"
OLD_NAMES = ("Voice Widget", "DeltaScribe")  # nomi precedenti del programma
SIZES = (16, 20, 24, 32, 40, 48, 64, 96, 128, 256)


def _to_array(img):
    img = img.convertToFormat(QImage.Format_RGBA8888)
    rows = np.frombuffer(img.constBits(), np.uint8).reshape(img.height(), img.bytesPerLine() // 4, 4)
    return rows[:, :img.width()].copy()


def _to_image(arr):
    h, w, _ = arr.shape
    return QImage(arr.tobytes(), w, h, 4 * w, QImage.Format_RGBA8888).copy()


def fill_bubble(arr):
    """Riempie di bianco la zona trasparente al centro del logo (l'interno del fumetto): il disegno
    scuro resta visibile anche su una barra delle applicazioni o dei menu scura."""
    alpha = arr[..., 3]
    labels, _ = ndimage.label(alpha < 128)
    h, w = alpha.shape
    inside = labels == labels[h // 2, w // 2]
    inside = ndimage.binary_dilation(inside, iterations=3)  # include il bordo sfumato
    a = alpha[..., None].astype(np.float32) / 255
    out = arr.copy()
    out[..., :3] = np.where(inside[..., None], (arr[..., :3] * a + 255 * (1 - a)).astype(np.uint8), arr[..., :3])
    out[..., 3] = np.where(inside, 255, alpha)
    return out


def build_app_icon(size=512, margin=0.02):
    """Logo rettangolare -> icona quadrata con sfondo trasparente.

    Il logo è più largo che alto: occupa tutta la larghezza (margine minimo) ed è centrato sul suo
    "peso" visivo, non sul riquadro (la punta del fumetto lo farebbe sembrare spostato), senza mai
    uscire dai bordi."""
    logo = QImage(SOURCE_LOGO)
    if logo.isNull():
        raise FileNotFoundError(f"Logo non trovato: {SOURCE_LOGO}")
    arr = fill_bubble(_to_array(logo))
    ys, xs = np.nonzero(arr[..., 3] > 10)  # tolgo eventuali bordi vuoti del file
    arr = arr[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    inner = round(size * (1 - 2 * margin))
    scaled = _to_image(arr).scaled(inner, inner, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    # a metà strada tra il centro del riquadro e il baricentro del disegno, con un margine minimo
    alpha = _to_array(scaled)[..., 3].astype(np.float64)
    w, h = scaled.width(), scaled.height()
    cy = (alpha.sum(axis=1) * np.arange(h)).sum() / alpha.sum()
    cx = (alpha.sum(axis=0) * np.arange(w)).sum() / alpha.sum()
    pad = round(size * margin)
    x = min(max(round(size / 2 - (w / 2 + cx) / 2), pad), size - w - pad)
    y = min(max(round(size / 2 - (h / 2 + cy) / 2), pad), size - h - pad)

    canvas = QImage(size, size, QImage.Format_ARGB32)
    canvas.fill(Qt.transparent)
    p = QPainter(canvas)
    p.drawImage(x, y, scaled)
    p.end()
    canvas.save(APP_ICON_PNG)
    return canvas


def icon_path():
    """Nome del .ico legato al contenuto dell'icona: se il disegno cambia cambia anche il nome, e
    Windows non può mostrare quella vecchia dalla sua memoria delle icone."""
    digest = hashlib.sha1(open(APP_ICON_PNG, "rb").read()).hexdigest()[:8]
    return os.path.join(APP_DIR, "assets", f"app_icon_{digest}.ico")


def render(size):
    return QImage(APP_ICON_PNG).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def png_bytes(img):
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


def write_ico(path):
    """ICO con voci PNG (supportato da Windows Vista in poi)."""
    images = [png_bytes(render(s)) for s in SIZES]
    out = io.BytesIO()
    out.write(struct.pack("<HHH", 0, 1, len(images)))
    offset = 6 + 16 * len(images)
    for size, data in zip(SIZES, images):
        dim = 0 if size >= 256 else size
        out.write(struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    for data in images:
        out.write(data)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(out.getvalue())


def create_shortcut(lnk_path, ico):
    ps = (
        "$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:LNK);"
        "$s.TargetPath = $env:TARGET; $s.Arguments = '\"' + $env:MAIN + '\"';"
        "$s.WorkingDirectory = $env:WORKDIR; $s.IconLocation = $env:ICON + ',0';"
        "$s.Description = 'Dettatura vocale: registra, trascrive e incolla il testo'; $s.Save()"
    )
    env = dict(os.environ, LNK=lnk_path, TARGET=PYTHONW, MAIN=MAIN, WORKDIR=APP_DIR, ICON=ico)
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], env=env, check=True)


def folder(name):
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command", f"[Environment]::GetFolderPath('{name}')"],
        capture_output=True, text=True, check=True)
    return out.stdout.strip()


def main():
    if sys.platform != "win32":
        QGuiApplication(sys.argv)
        build_app_icon()
        print("Icona aggiornata. I collegamenti .lnk servono solo su Windows: su Mac usa «ScriVoice.command».")
        return
    QGuiApplication(sys.argv)
    build_app_icon()
    ico = icon_path()
    for old_ico in glob.glob(os.path.join(APP_DIR, "assets", "*.ico")):
        if os.path.normcase(old_ico) != os.path.normcase(ico):
            os.remove(old_ico)
    write_ico(ico)
    print("Icona:", ico)
    folders = [APP_DIR, folder("Desktop"), folder("Programs")]  # Programs = menu Start
    for dest in folders:
        # collegamenti con i nomi precedenti del programma
        for old_name in OLD_NAMES:
            old = os.path.join(dest, f"{old_name}.lnk")
            if os.path.exists(old):
                os.remove(old)
                print("Rimosso vecchio collegamento:", old)
        lnk = os.path.join(dest, f"{NAME}.lnk")
        create_shortcut(lnk, ico)
        print("Collegamento:", lnk)


if __name__ == "__main__":
    main()
