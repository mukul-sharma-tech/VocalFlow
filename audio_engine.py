import threading
import numpy as np
import sounddevice as sd
from typing import Callable, Optional

# Deepgram expects: 16kHz, mono, 16-bit signed PCM
TARGET_SAMPLE_RATE = 16000
CHANNELS = 1
BLOCK_SIZE = 4096  # frames per callback (~256ms at 16kHz)
DTYPE = "int16"


class AudioEngine:
    def __init__(self):
        self._stream: Optional[sd.InputStream] = None
        self._callback: Optional[Callable] = None
        self._capturing = False

    def start_capture(self, callback: Callable[[bytes], None]):
        """Start mic capture. callback receives raw 16-bit PCM bytes."""
        self._callback = callback
        self._capturing = True

        self._stream = sd.InputStream(
            samplerate=TARGET_SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            blocksize=BLOCK_SIZE,
            callback=self._on_audio,
        )
        self._stream.start()

    def _on_audio(self, indata: np.ndarray, frames: int, time, status):
        if not self._capturing or self._callback is None:
            return
        # indata shape: (frames, channels) — flatten to bytes
        pcm_bytes = indata.tobytes()
        try:
            self._callback(pcm_bytes)
        except Exception:
            pass

    def stop_capture(self):
        self._capturing = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
