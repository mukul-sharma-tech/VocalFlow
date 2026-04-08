"""
Mutes the default Windows audio output while recording so the mic
doesn't pick up system sounds (notifications, music, etc.).
Restores the previous mute state when recording stops.
"""
from ctypes import POINTER, cast

from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume


class AudioMuter:
    def __init__(self):
        self._was_muted = False  # remember what state we found it in

    def mute(self):
        try:
            vol = self._get_volume()
            self._was_muted = bool(vol.GetMute())
            vol.SetMute(True, None)
        except Exception:
            pass  # if we can't mute, just continue — not critical

    def unmute(self):
        try:
            # Restore to whatever it was before, not just "unmute"
            self._get_volume().SetMute(self._was_muted, None)
        except Exception:
            pass

    def _get_volume(self):
        device = AudioUtilities.GetSpeakers()
        interface = device.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
