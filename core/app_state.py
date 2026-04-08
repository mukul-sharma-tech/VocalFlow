"""
Central state container for VocalFlow.
Everything that needs to be shared across services lives here.
"""
import threading
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, List, Optional


class RecordingState(Enum):
    IDLE         = auto()  # waiting for hotkey
    RECORDING    = auto()  # mic is live, audio streaming to Deepgram
    TRANSCRIBING = auto()  # key released, waiting for final transcript
    ERROR        = auto()  # something went wrong


# Keys the user can hold to trigger recording
HOTKEY_OPTIONS = {
    "right_alt":   {"display": "Right Alt / AltGr", "key": "alt gr"},
    "left_alt":    {"display": "Left Alt",           "key": "alt"},
    "right_ctrl":  {"display": "Right Ctrl",         "key": "right ctrl"},
    "left_ctrl":   {"display": "Left Ctrl",          "key": "ctrl"},
    "right_shift": {"display": "Right Shift",        "key": "right shift"},
}

# Waveform overlay color themes — each is a list of (R, G, B) stops
# that get interpolated across the bars as they animate
OVERLAY_THEMES = {
    "Vibrant Blue": [(0x09,0xE0,0xFE),(0x03,0xC1,0xF4),(0x08,0xA1,0xF7),(0x00,0x4F,0xE1)],
    "Bloom Rush":   [(0xEF,0x70,0x9B),(0xFA,0x93,0x72)],
    "Mint Flow":    [(0x8D,0xE9,0xD5),(0x32,0xC4,0xC0)],
    "Magic Garden": [(0xBF,0x0F,0xFF),(0x7B,0x2F,0xFF),(0x3D,0x0F,0xBF)],
}


@dataclass
class DeepgramModel:
    canonical_name: str
    display_name: str
    languages: List[str]


@dataclass
class GroqModel:
    id: str
    display_name: str


class AppState:
    def __init__(self):
        self._lock = threading.Lock()
        self._state_callbacks: List[Callable] = []

        self.recording_state: RecordingState = RecordingState.IDLE
        self.last_transcript: str = ""

        # Deepgram settings
        self.deepgram_api_key: str = ""
        self.available_models: List[DeepgramModel] = []
        self.selected_model: str = "nova-3-general"
        self.selected_language: str = "en-US"

        # Groq settings
        self.groq_api_key: str = ""
        self.available_groq_models: List[GroqModel] = []
        self.selected_groq_model: str = ""
        self.correction_mode_enabled: bool = False
        self.grammar_correction_enabled: bool = False
        self.code_mix_enabled: bool = False
        self.selected_code_mix: str = ""
        self.target_language_enabled: bool = False
        self.selected_target_language: str = "English"

        # UI preferences
        self.selected_hotkey: str = "right_alt"
        self.selected_overlay_theme: str = "Vibrant Blue"

    def set_recording_state(self, state: RecordingState):
        """Update state and notify all listeners (tray icon, overlay, etc.)."""
        self.recording_state = state
        for cb in self._state_callbacks:
            try:
                cb(state)
            except Exception:
                pass

    def on_state_change(self, callback: Callable):
        """Register a callback to be called whenever recording state changes."""
        self._state_callbacks.append(callback)
