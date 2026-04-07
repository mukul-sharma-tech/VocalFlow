from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


class AudioMuter:
    """Mutes/unmutes the default Windows audio output device."""

    def __init__(self):
        self._was_muted = False

    def _get_volume_interface(self):
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))

    def mute(self):
        try:
            vol = self._get_volume_interface()
            self._was_muted = bool(vol.GetMute())
            vol.SetMute(True, None)
        except Exception:
            pass

    def unmute(self):
        try:
            vol = self._get_volume_interface()
            vol.SetMute(self._was_muted, None)
        except Exception:
            pass
