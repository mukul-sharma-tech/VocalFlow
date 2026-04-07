"""
Captures microphone audio and streams it as raw PCM bytes.
Deepgram expects: 16kHz, mono, 16-bit signed little-endian PCM.
"""
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000  # Hz — Deepgram's required sample rate
CHANNELS    = 1      # mono
BLOCK_SIZE  = 4096   # frames per callback (~256ms of audio)
DTYPE       = "int16"


class AudioEngine:
    def __init__(self):
        self._stream: Optional[sd.InputStream] = None
        self._callback: Optional[Callable[[bytes], None]] = None
        self._capturing = False

    def start_capture(self, callback: Callable[[bytes], None]):
        """Open the mic and start sending PCM chunks to the callback."""
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
        """Stop the mic and clean up."""
        self._capturing = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _on_audio(self, indata: np.ndarray, frames: int, time, status):
        # indata shape is (frames, channels) — flatten to raw bytes and forward
        if self._capturing and self._callback:
            try:
                self._callback(indata.tobytes())
            except Exception:
                pass
