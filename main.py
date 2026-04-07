"""
VocalFlow for Windows
Hold a key → speak → release → text appears wherever your cursor is.

Flow: hotkey held → Deepgram WebSocket opens → mic streams audio →
      key released → transcript comes back → (optional Groq cleanup) → paste
"""
import sys
import threading
import winsound

from app_state import AppState, RecordingState
from audio_engine import AudioEngine
from audio_muter import AudioMuter
from deepgram_service import DeepgramService
from groq_service import GroqService
from hotkey_manager import HotkeyManager
from keychain_service import KeychainService, SettingsService
from overlay_window import OverlayWindow
from settings_window import SettingsWindow
from text_injector import TextInjector
from tray_controller import TrayController


class VocalFlowApp:
    def __init__(self):
        # Storage: API keys go to Windows Credential Manager, everything else to a JSON file
        self.keychain = KeychainService()
        self.settings = SettingsService()

        self.state = AppState()
        self._load_settings()

        # Core services
        self.audio_engine = AudioEngine()
        self.deepgram     = DeepgramService()
        self.groq         = GroqService()
        self.injector     = TextInjector()
        self.muter        = AudioMuter()

        # UI
        self.overlay      = OverlayWindow(self.state)
        self.settings_win = SettingsWindow(self.state, self.keychain, self.settings)
        self.tray         = TrayController(self.state, self._open_settings, self._quit)

        # Hotkey watcher — fires on press and release
        self.hotkey_mgr = HotkeyManager(
            self.state,
            on_press=self._start_recording,
            on_release=self._stop_and_transcribe,
        )

    def _load_settings(self):
        """Pull saved settings into app state on startup."""
        s = self.state
        s.deepgram_api_key           = self.keychain.retrieve("deepgram_api_key")
        s.groq_api_key               = self.keychain.retrieve("groq_api_key")
        s.selected_model             = self.settings.get("selected_model",             "nova-3-general")
        s.selected_language          = self.settings.get("selected_language",          "en-US")
        s.selected_hotkey            = self.settings.get("selected_hotkey",            "right_alt")
        s.selected_groq_model        = self.settings.get("selected_groq_model",        "")
        s.correction_mode_enabled    = self.settings.get("correction_mode_enabled",    False)
        s.grammar_correction_enabled = self.settings.get("grammar_correction_enabled", False)
        s.code_mix_enabled           = self.settings.get("code_mix_enabled",           False)
        s.selected_code_mix          = self.settings.get("selected_code_mix",          "")
        s.target_language_enabled    = self.settings.get("target_language_enabled",    False)
        s.selected_target_language   = self.settings.get("selected_target_language",   "English")
        s.selected_overlay_theme     = self.settings.get("selected_overlay_theme",     "Vibrant Blue")

    # -- recording lifecycle --

    def _start_recording(self):
        # Guard against duplicate hotkey events (AltGr fires both alt gr + right ctrl)
        if self.state.recording_state == RecordingState.RECORDING:
            return

        self.state.set_recording_state(RecordingState.RECORDING)

        # Open the WebSocket early so it's ready by the time audio starts flowing
        self.deepgram.connect(
            api_key=self.state.deepgram_api_key,
            model=self.state.selected_model,
            language=self.state.selected_language,
        )

        self.overlay.show()

        # Beep before muting so the user actually hears it
        winsound.Beep(400, 150)
        self.muter.mute()

        # Wait for WebSocket handshake before sending audio
        self.deepgram.wait_until_ready()
        self.audio_engine.start_capture(self.deepgram.send_audio)

    def _stop_and_transcribe(self):
        # Guard: only stop if we're actually recording
        if self.state.recording_state != RecordingState.RECORDING:
            return

        self.state.set_recording_state(RecordingState.TRANSCRIBING)
        self.audio_engine.stop_capture()
        self.muter.unmute()

        # Lower pitch beep signals "done recording"
        winsound.Beep(300, 150)
        self.overlay.hide()

        # Tell Deepgram we're done — it'll flush and call back with the final transcript
        self.deepgram.close_stream(self._on_transcript)

    def _on_transcript(self, transcript: str):
        """Called when Deepgram delivers the final transcript."""
        if not transcript.strip():
            # Nothing was said — just go back to idle
            self.state.set_recording_state(RecordingState.IDLE)
            return

        def inject(text: str):
            self.state.last_transcript = text
            self.injector.inject(text)
            self.state.set_recording_state(RecordingState.IDLE)

        # Decide whether to run Groq post-processing
        has_groq   = bool(self.state.groq_api_key and self.state.selected_groq_model)
        code_mix   = self.state.selected_code_mix if self.state.code_mix_enabled else None
        target_lang = self.state.selected_target_language if self.state.target_language_enabled else None
        use_groq   = has_groq and any([
            self.state.correction_mode_enabled,
            self.state.grammar_correction_enabled,
            code_mix,
            target_lang,
        ])

        if use_groq:
            self.groq.process_text(
                transcript,
                api_key=self.state.groq_api_key,
                model=self.state.selected_groq_model,
                fix_spelling=self.state.correction_mode_enabled,
                fix_grammar=self.state.grammar_correction_enabled,
                code_mix=code_mix,
                target_language=target_lang,
                callback=inject,
            )
        else:
            # No Groq configured or no features enabled — paste raw transcript
            inject(transcript)

    # -- UI helpers --

    def _open_settings(self):
        # Tray runs on a background thread, so we schedule this on tkinter's main thread
        if hasattr(self, "_tk_root") and self._tk_root:
            self._tk_root.after(0, self.settings_win.open)

    def _quit(self):
        self.hotkey_mgr.stop_listening()
        if hasattr(self, "_tk_root") and self._tk_root:
            self._tk_root.quit()
        sys.exit(0)

    def run(self):
        import tkinter as tk

        # tkinter needs to own the main thread on Windows
        self._tk_root = tk.Tk()
        self._tk_root.withdraw()  # hidden — just keeps the event loop alive

        self.hotkey_mgr.start_listening()
        self.tray.run_in_thread()  # tray runs on its own thread

        print("VocalFlow running — check the system tray.")
        self._tk_root.mainloop()


if __name__ == "__main__":
    VocalFlowApp().run()
