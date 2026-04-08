import threading
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, List

class RecordingState(Enum):
    IDLE = auto(); RECORDING = auto(); TRANSCRIBING = auto(); ERROR = auto()

# Keys the user can hold to trigger recording
HOTKEY_OPTIONS = {
    "right_alt":   {"display": "Right Alt / AltGr", "key": "alt gr"},
    "left_alt":    {"display": "Left Alt",           "key": "alt"},
    "right_ctrl":  {"display": "Right Ctrl",         "key": "right ctrl"},
    "left_ctrl":   {"display": "Left Ctrl",          "key": "ctrl"},
    "right_shift": {"display": "Right Shift",        "key": "right shift"},
}

# Waveform color themes — list of (R,G,B) stops interpolated across bars
OVERLAY_THEMES = {
    "Vibrant Blue": [(0x09,0xE0,0xFE),(0x03,0xC1,0xF4),(0x08,0xA1,0xF7),(0x00,0x4F,0xE1)],
    "Bloom Rush":   [(0xEF,0x70,0x9B),(0xFA,0x93,0x72)],
    "Mint Flow":    [(0x8D,0xE9,0xD5),(0x32,0xC4,0xC0)],
    "Magic Garden": [(0xBF,0x0F,0xFF),(0x7B,0x2F,0xFF),(0x3D,0x0F,0xBF)],
}

@dataclass
class DeepgramModel:
    canonical_name: str; display_name: str; languages: List[str]

@dataclass
class GroqModel:
    id: str; display_name: str

class AppState:
    def __init__(self):
        self._cbs: List[Callable] = []
        self.recording_state = RecordingState.IDLE
        self.last_transcript = ""
        self.deepgram_api_key = ""; self.available_models: List[DeepgramModel] = []
        self.selected_model = "nova-3-general"; self.selected_language = "en-US"
        self.groq_api_key = ""; self.available_groq_models: List[GroqModel] = []
        self.selected_groq_model = ""
        self.correction_mode_enabled = False; self.grammar_correction_enabled = False
        self.code_mix_enabled = False; self.selected_code_mix = ""
        self.target_language_enabled = False; self.selected_target_language = "English"
        self.selected_hotkey = "right_alt"; self.selected_overlay_theme = "Vibrant Blue"

    def set_recording_state(self, state: RecordingState):
        self.recording_state = state
        for cb in self._cbs:  # notify tray, overlay, etc.
            try: cb(state)
            except Exception: pass

    def on_state_change(self, cb: Callable): self._cbs.append(cb)
