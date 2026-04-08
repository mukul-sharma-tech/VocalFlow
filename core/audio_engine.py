from typing import Callable, Optional
import numpy as np
import sounddevice as sd

class AudioEngine:
    def __init__(self):
        self._stream: Optional[sd.InputStream] = None
        self._cb: Optional[Callable] = None
        self._on = False
        self.rms_level = 0.0  # 0.0 = silence, 1.0 = loud — drives overlay animation

    def start_capture(self, cb: Callable[[bytes], None]):
        self._cb, self._on = cb, True
        self._stream = sd.InputStream(samplerate=16000, channels=1, dtype="int16",
                                      blocksize=2048, callback=self._handle)
        self._stream.start()

    def stop_capture(self):
        self._on = False; self.rms_level = 0.0
        if self._stream:
            try: self._stream.stop(); self._stream.close()
            except Exception: pass
            self._stream = None

    def _handle(self, indata: np.ndarray, *_):
        if not self._on: return
        # Normalize RMS to 0–1 (int16 loud speech ≈ 3000–8000)
        rms = min(float(np.sqrt(np.mean(indata.astype(np.float32)**2))) / 5000.0, 1.0)
        # Fast attack, slow decay for smooth animation
        self.rms_level = self.rms_level * (0.2 if rms > self.rms_level else 0.7) + rms * (0.8 if rms > self.rms_level else 0.3)
        if self._cb:
            try: self._cb(indata.tobytes())
            except Exception: pass
