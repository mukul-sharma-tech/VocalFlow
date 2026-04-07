import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Callable


class RecordingState(Enum):
    IDLE = auto()
    RECORDING = auto()
    TRANSCRIBING = auto()
    ERROR = auto()


HOTKEY_OPTIONS = {
    "right_alt":     {"display": "Right Alt / AltGr", "key": "alt gr"},
    "left_alt":      {"display": "Left Alt",           "key": "left alt"},
    "right_ctrl":    {"display": "Right Ctrl",         "key": "right ctrl"},
    "left_ctrl":     {"display": "Left Ctrl",          "key": "left ctrl"},
    "right_shift":   {"display": "Right Shift",        "key": "right shift"},
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

        # Deepgram
        self.deepgram_api_key: str = ""
        self.available_models: List[DeepgramModel] = []
        self.selected_model: str = "nova-3-general"
        self.selected_language: str = "en-US"

        # Groq
        self.groq_api_key: str = ""
        self.available_groq_models: List[GroqModel] = []
        self.selected_groq_model: str = ""
        self.correction_mode_enabled: bool = False
        self.grammar_correction_enabled: bool = False
        self.code_mix_enabled: bool = False
        self.selected_code_mix: str = ""
        self.target_language_enabled: bool = False
        self.selected_target_language: str = "English"

        # Hotkey
        self.selected_hotkey: str = "right_alt"

    def set_recording_state(self, state: RecordingState):
        self.recording_state = state
        for cb in self._state_callbacks:
            try:
                cb(state)
            except Exception:
                pass

    def on_state_change(self, callback: Callable):
        self._state_callbacks.append(callback)
