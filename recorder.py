"""Registrazione dal microfono ad alta qualità (float32, 48 kHz) e salvataggio WAV a 24 bit."""
import os
import threading
import time
from datetime import datetime

import numpy as np
import sounddevice as sd
import soundfile as sf


class Recorder:
    def __init__(self, sample_rate=48000, device=None):
        self.requested_rate = sample_rate
        self.device = device  # nome del microfono (None = predefinito di Windows)
        self.sample_rate = sample_rate
        self._chunks = []
        self._lock = threading.Lock()
        self._stream = None
        self.level = 0.0  # livello RMS 0..1 per il VU meter
        self.started_at = None

    @property
    def is_recording(self):
        return self._stream is not None

    def _callback(self, indata, frames, time_info, status):
        mono = indata[:, 0].copy()
        with self._lock:
            self._chunks.append(mono)
        rms = float(np.sqrt(np.mean(mono * mono))) if len(mono) else 0.0
        # scala logaritmica approssimata: -60 dB -> 0, 0 dB -> 1
        db = 20 * np.log10(max(rms, 1e-6))
        self.level = min(1.0, max(0.0, (db + 60) / 60))

    def start(self):
        if self._stream is not None:
            return
        refresh_devices()
        device = resolve_device(self.device)
        with self._lock:
            self._chunks = []
        self.level = 0.0
        rate = self.requested_rate
        try:
            sd.check_input_settings(device=device, channels=1, dtype="float32", samplerate=rate)
        except Exception:
            # il dispositivo non supporta la frequenza richiesta: uso quella nativa
            info = sd.query_devices(device, "input")
            rate = int(info["default_samplerate"])
        self.sample_rate = rate
        self._stream = sd.InputStream(
            samplerate=rate, channels=1, dtype="float32", device=device,
            callback=self._callback, blocksize=0, latency="low",
        )
        self._stream.start()
        self.started_at = time.monotonic()

    def stop(self):
        """Ferma la registrazione e restituisce (audio float32 mono, sample_rate)."""
        stream, self._stream = self._stream, None
        if stream is not None:
            stream.stop()
            stream.close()
        self.level = 0.0
        with self._lock:
            audio = np.concatenate(self._chunks) if self._chunks else np.zeros(0, np.float32)
            self._chunks = []
        return audio, self.sample_rate

    def elapsed(self):
        return time.monotonic() - self.started_at if self.started_at and self.is_recording else 0.0


def refresh_devices():
    """Rilegge l'elenco dei dispositivi (es. AirPods collegati dopo l'avvio). Solo senza stream attivi."""
    try:
        sd._terminate()
        sd._initialize()
    except Exception:  # noqa: BLE001
        pass


def list_input_devices():
    """Nomi dei microfoni disponibili (API audio predefinita di Windows, senza duplicati)."""
    try:
        hostapi = sd.default.hostapi if sd.default.hostapi >= 0 else 0
        names = [d["name"] for d in sd.query_devices()
                 if d["max_input_channels"] > 0 and d["hostapi"] == hostapi]
    except Exception:  # noqa: BLE001
        return []
    # "Mapper" è un alias del dispositivo predefinito
    return [n for n in dict.fromkeys(names) if "mapper" not in n.lower()]


def resolve_device(name):
    """Nome salvato nel config -> indice sounddevice (None = microfono predefinito)."""
    if name is None or name == "":
        return None
    if isinstance(name, int):
        return name
    hostapi = sd.default.hostapi if sd.default.hostapi >= 0 else 0
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0 and d["hostapi"] == hostapi and d["name"] == name:
            return i
    return None  # microfono scollegato: uso il predefinito


def save_wav(audio, sample_rate, folder, max_files=None):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, datetime.now().strftime("rec_%Y%m%d_%H%M%S.wav"))
    sf.write(path, audio, sample_rate, subtype="PCM_24")
    if max_files:
        _prune(folder, max_files)
    return path


def _prune(folder, max_files):
    # ogni registrazione ha .wav (+ .txt); il nome col timestamp ordina cronologicamente
    bases = sorted({os.path.join(folder, os.path.splitext(f)[0])
                    for f in os.listdir(folder) if f.startswith("rec_")})
    for base in bases[:max(0, len(bases) - max_files)]:
        for ext in (".wav", ".txt"):
            try:
                os.remove(base + ext)
            except OSError:
                pass
