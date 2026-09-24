"""Crea legal/THIRD_PARTY_LICENSES.txt con le licenze di tutti i componenti inclusi nell'app.

Legge i file di licenza dei pacchetti Python installati nell'ambiente di build (diverso tra Windows
e Mac, per questo va eseguito su ciascuna piattaforma prima di PyInstaller) e aggiunge i componenti
che non sono pacchetti Python (modello Whisper, librerie native incluse nelle ruote).
"""
import importlib.metadata as md
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "legal", "THIRD_PARTY_LICENSES.txt")
# strumenti usati solo per costruire i pacchetti: non finiscono nell'app
BUILD_ONLY = {"pip", "setuptools", "wheel", "pyinstaller", "pyinstaller-hooks-contrib", "altgraph",
              "pefile", "pywin32-ctypes", "macholib", "pillow", "pyflakes"}
LICENSE_NAMES = ("license", "licence", "copying", "notice", "authors")

HEADER = """ScriVoice is free software under the MIT License (see LICENSE). It includes the following
third-party components, each distributed under its own license.

LGPL notice: Qt (via PySide6/shiboken6), pynput and libsndfile are used under the GNU Lesser General
Public License v3. They are shipped as separate, unmodified library files inside the application
folder (Windows: the "_internal" folder; Mac: ScriVoice.app/Contents/Frameworks) and can be replaced
with compatible versions. The source code of these libraries is available from their projects:
https://code.qt.io, https://pypi.org/project/PySide6/, https://github.com/moses-palmer/pynput,
https://github.com/libsndfile/libsndfile. The exact versions used are listed below.

Speech recognition model: "faster-whisper-small" (https://huggingface.co/Systran/faster-whisper-small),
a CTranslate2 conversion of OpenAI Whisper "small" (https://github.com/openai/whisper), MIT License,
Copyright (c) 2022 OpenAI.

Native libraries bundled inside Python packages: PortAudio (MIT, in "sounddevice"), libsndfile
(LGPL-2.1+, in "soundfile"), FFmpeg (LGPL-2.1+, in "av"), OpenBLAS / other runtime libraries in
numpy and scipy (BSD-style). Their license texts are included below with the packages that ship them
when available.
"""


def license_texts(dist):
    texts = []
    for f in dist.files or []:
        name = os.path.basename(str(f)).lower()
        if name.startswith(LICENSE_NAMES) and not name.endswith((".py", ".pyc")):
            try:
                texts.append((str(f), f.locate().read_text(encoding="utf-8", errors="replace")))
            except (OSError, UnicodeDecodeError):
                pass
    return texts


def main():
    dists = {}
    for dist in md.distributions():
        name = (dist.metadata["Name"] or "").strip()
        if name and name.lower() not in BUILD_ONLY:
            dists[name.lower()] = dist
    parts = [HEADER]
    for key in sorted(dists):
        dist = dists[key]
        meta = dist.metadata
        lic = meta.get("License-Expression") or meta.get("License") or ""
        if len(lic) > 200:  # alcuni pacchetti mettono qui il testo intero
            lic = lic.splitlines()[0]
        classifiers = [c.split("::")[-1].strip() for c in meta.get_all("Classifier") or []
                       if c.startswith("License ::")]
        parts.append("\n" + "=" * 78 + f"\n{meta['Name']} {meta['Version']}\n"
                     f"License: {lic or ', '.join(classifiers) or 'see below'}\n"
                     f"Home: {meta.get('Home-page') or ''}\n" + "=" * 78)
        for path, text in license_texts(dist):
            parts.append(f"\n--- {path} ---\n{text.strip()}\n")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"{len(dists)} componenti -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
