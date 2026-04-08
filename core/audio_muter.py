from ctypes import POINTER, cast
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class AudioMuter:
    def __init__(self): self._was = False
    def _vol(self):
        return cast(AudioUtilities.GetSpeakers().Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None), POINTER(IAudioEndpointVolume))
    def mute(self):
        try: v = self._vol(); self._was = bool(v.GetMute()); v.SetMute(True, None)
        except Exception: pass
    def unmute(self):
        try: self._vol().SetMute(self._was, None)
        except Exception: pass
