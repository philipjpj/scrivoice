#!/bin/bash
# Firma ad-hoc dell'app e creazione del DMG (eseguito sul Mac di GitHub Actions).
# Uso (dalla cartella del progetto, dopo PyInstaller):  packaging/mac/build_dmg.sh 1.0.0
set -euo pipefail
VERSION="${1:?versione mancante}"
APP="dist/ScriVoice.app"
DMG="dist/ScriVoice-${VERSION}-mac-AppleSilicon.dmg"

# Firma "ad-hoc" (gratuita): indispensabile per avviare app su Mac con chip Apple.
# Non sostituisce la notarizzazione Apple: al primo avvio serve "Apri comunque".
codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict "$APP"

STAGE="$(mktemp -d)"
cp -R "$APP" "$STAGE/"
cp "packaging/mac/LEGGIMI - READ ME.txt" "$STAGE/"
make_dmg() {
  rm -f "$DMG"
  create-dmg \
    --volname "ScriVoice" \
    --window-size 620 400 \
    --icon-size 110 \
    --icon "ScriVoice.app" 150 170 \
    --app-drop-link 470 170 \
    --icon "LEGGIMI - READ ME.txt" 310 320 \
    --hide-extension "ScriVoice.app" \
    --no-internet-enable \
    "$@" "$DMG" "$STAGE"
}
# la disposizione delle icone usa il Finder, che sui Mac delle build automatiche a volte non
# risponde: in quel caso creo un DMG semplice (stessi contenuti, con il collegamento ad Applicazioni)
make_dmg || make_dmg --skip-jenkins
hdiutil verify "$DMG"
echo "Creato $DMG"
