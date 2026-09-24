#!/bin/bash
# Avvia ScriVoice su Mac (doppio clic). Dopo l'avvio puoi chiudere questa finestra del Terminale.
cd "$(dirname "$0")" || exit 1

if [ ! -x .venv/bin/python ]; then
  echo "ScriVoice non è ancora installato: fai prima doppio clic su «install.command»."
  read -r -p "Premi Invio per chiudere…"
  exit 1
fi

mkdir -p "$HOME/Library/Logs"
nohup .venv/bin/python main.py < /dev/null > "$HOME/Library/Logs/ScriVoice.log" 2>&1 &
disown

echo "✅ ScriVoice avviato: trovi l'icona di ScriVoice (il fumetto sorridente) nella barra dei menu in alto."
echo "Puoi chiudere questa finestra (se il Terminale chiede conferma, scegli «Termina»: ScriVoice resta attivo)."
