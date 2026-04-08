"""
Captures microphone audio and streams it as raw PCM bytes.
Also computes real-time RMS level so the overlay can react to voice volume.
Deepgram expects: 16kHz, mono, 16-bit signed little-endian PCM.
"""
import threading
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS    = 1
BLOCK_SIZE  = 2048   # smaller block = more responsive RMS updates
DTYPE       = "int16"


class AudioEngine:
    def __init__(self):
        self._stream: Optional[sd.InputStream] = None
        self._callback: Optional[Callable[[bytes], None]] = None
        self._capturing = False
        self.rms_level: float = 0.0   # 0.0 (silence) → 1.0 (loud speech)

    def start_capture(self, callback: Callable[[bytes], None]):
        self._callback = callback
        self._capturing = True
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=BLOCK_SIZE,
            callback=self._on_audio,
        )
        self._stream.start()

    def stop_capture(self):
        self._capturing = False
        self.rms_level = 0.0
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _on_audio(self, indata: np.ndarray, frames: int, time, status):
        if not self._capturing:
            return

        # Compute RMS and normalize to 0.0–1.0
        # int16 max is 32768, typical loud speech ~3000–8000
        rms = float(np.sqrt(np.mean(indata.astype(np.float32) ** 2)))
        normalized = min(rms / 5000.0, 1.0)

        # Smooth: fast attack, slow decay
        if normalized > self.rms_level:
            self.rms_level = self.rms_level * 0.2 + normalized * 0.8  # fast attack
        else:
            self.rms_level = self.rms_level * 0.7 + normalized * 0.3  # slow decay

        if self._callback:
            try:
                self._callback(indata.tobytes())
            except Exception:
                pass
