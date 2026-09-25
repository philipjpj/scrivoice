"""Trascrizione locale con faster-whisper. Il modello viene caricato una volta in background."""
import os
import threading

import numpy as np
from scipy.signal import resample_poly

import paths

WHISPER_RATE = 16000
LANGUAGES = ("it", "en", "es")  # lingue di dettatura supportate; "auto" = rileva tra queste

# Frase di contesto per lingua: orienta Whisper su dettature tecniche con termini inglesi
PROMPTS = {
    "it": ("Trascrizione di istruzioni in italiano per Claude Code, un assistente di programmazione. "
           "Termini frequenti: Claude Code, Python, JavaScript, TypeScript, React, API, file, "
           "commit, branch, pull request, bug, refactoring, test, frontend, backend, database."),
    "en": ("Transcription of spoken instructions in English for Claude Code, a coding assistant. "
           "Frequent terms: Claude Code, Python, JavaScript, TypeScript, React, API, file, "
           "commit, branch, pull request, bug, refactoring, test, frontend, backend, database."),
    "es": ("Transcripción de instrucciones en español para Claude Code, un asistente de programación. "
           "Términos frecuentes: Claude Code, Python, JavaScript, TypeScript, React, API, archivo, "
           "commit, branch, pull request, bug, refactoring, test, frontend, backend, base de datos."),
}


class Transcriber:
    def __init__(self, model_name, compute_type="int8", language="en", beam_size=5, initial_prompt=None,
                 cpu_threads=0, vocabulary=()):
        self.model_name = model_name
        self.compute_type = compute_type
        self.language = language or "auto"
        self.beam_size = beam_size
        # prompt personalizzato dal config; vuoto = frase di contesto della lingua
        self.initial_prompt = initial_prompt or None
        self.vocabulary = list(vocabulary)
        # i thread logici (hyperthreading) rallentano: uso un thread per core fisico
        self.cpu_threads = cpu_threads or max(1, (os.cpu_count() or 4) // 2)
        self._model = None
        self._error = None
        self._ready = threading.Event()
        self._lock = threading.Lock()  # una trascrizione alla volta

    def load_async(self, on_done=None):
        def run():
            try:
                from faster_whisper import WhisperModel
                # modello incluso nel pacchetto installato, altrimenti scaricato per nome (dai sorgenti)
                source = paths.bundled_model(self.model_name) or self.model_name
                self._model = WhisperModel(
                    source, device="cpu", compute_type=self.compute_type,
                    cpu_threads=self.cpu_threads,
                )
            except Exception as e:  # noqa: BLE001 - riportato alla UI
                self._error = e
            finally:
                self._ready.set()
                if on_done:
                    on_done(self._error)
        threading.Thread(target=run, name="whisper-load", daemon=True).start()

    @property
    def ready(self):
        return self._ready.is_set() and self._model is not None

    def _run(self, audio, language):
        return self._model.transcribe(
            audio,
            language=language,
            beam_size=self.beam_size,
            # in automatico niente frase di contesto: spingerebbe il rilevamento verso la sua lingua
            initial_prompt=self.initial_prompt or PROMPTS.get(language),
            # parole dell'utente: spingono Whisper a riconoscerle (es. shortcut, task)
            hotwords=", ".join(self.vocabulary) or None,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            condition_on_previous_text=False,
        )

    def transcribe(self, audio, sample_rate):
        """Blocca finché il modello è pronto, poi restituisce il testo trascritto."""
        self._ready.wait()
        if self._model is None:
            raise RuntimeError(f"Modello Whisper non caricato: {self._error}")
        audio = to_whisper_audio(audio, sample_rate)
        with self._lock:
            language = self.language if self.language in LANGUAGES else None
            segments, info = self._run(audio, language)
            if language is None and info.language not in LANGUAGES:
                # rilevata un'altra lingua (es. portoghese al posto dello spagnolo):
                # uso la più probabile tra quelle supportate
                probs = dict(info.all_language_probs or [])
                best = max(LANGUAGES, key=lambda code: probs.get(code, 0.0))
                segments, info = self._run(audio, best)
            text = " ".join(s.text.strip() for s in segments)
        return " ".join(text.split())


def to_whisper_audio(audio, sample_rate):
    audio = np.asarray(audio, dtype=np.float32)
    if sample_rate != WHISPER_RATE:
        g = np.gcd(int(sample_rate), WHISPER_RATE)
        audio = resample_poly(audio, WHISPER_RATE // g, int(sample_rate) // g).astype(np.float32)
    # normalizzazione leggera: registrazioni molto basse vengono riconosciute peggio
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if 0 < peak < 0.5:
        audio = audio * (0.9 / peak)
    return audio
