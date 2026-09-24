#!/bin/bash
# Installazione di ScriVoice su Mac: doppio clic su questo file.
# Scarica Python e le librerie dentro questa cartella: non serve la password e non tocca il resto del Mac.
cd "$(dirname "$0")" || exit 1

fail() {
  echo
  echo "❌ Errore: $1"
  read -r -p "Premi Invio per chiudere…"
  exit 1
}

echo "=== Installazione di ScriVoice ==="
echo

# uv installa Python e le librerie in modo automatico
export PATH="$HOME/.local/bin:$PATH"
if ! command -v uv >/dev/null 2>&1; then
  echo "▶ Scarico lo strumento di installazione…"
  curl -LsSf https://astral.sh/uv/install.sh | sh || fail "impossibile scaricare, controlla la connessione a Internet."
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "▶ Preparo Python…"
rm -rf .venv
uv venv --python 3.12 .venv || fail "impossibile preparare Python."

echo "▶ Installo le librerie (qualche minuto)…"
uv pip install --python .venv/bin/python -r requirements.txt || fail "installazione delle librerie non riuscita."

chmod +x "ScriVoice.command"

echo "▶ Scarico il modello di trascrizione (circa 500 MB, solo la prima volta)…"
.venv/bin/python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" \
  || echo "  (non riuscito ora: verrà scaricato al primo avvio)"

echo
echo "✅ Installazione completata!"
echo "Per avviare ScriVoice: doppio clic su «ScriVoice.command»."
echo
read -r -p "Premi Invio per chiudere…"
