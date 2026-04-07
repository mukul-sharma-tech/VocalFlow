"""
VocalFlow for Windows
Hold a hotkey → speak → release → text appears at your cursor.
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
        self.keychain = KeychainService()
        self.settings = SettingsService()

        self.state = AppState()
        self._load_persisted_state()

        self.audio_engine = AudioEngine()
        self.deepgram = DeepgramService()
        self.groq = GroqService()
        self.injector = TextInjector()
        self.muter = AudioMuter()
        self.overlay = OverlayWindow(self.state)

        self.settings_win = SettingsWindow(self.state, self.keychain, self.settings)
        self.tray = TrayController(self.state, self._open_settings, self._quit)

        self.hotkey_mgr = HotkeyManager(
            self.state,
            on_press=self._start_recording,
            on_release=self._stop_and_transcribe,
        )

    # ------------------------------------------------------------------ #
    # Persistence                                                          #
    # ------------------------------------------------------------------ #

    def _load_persisted_state(self):
        s = self.state
        s.deepgram_api_key   = self.keychain.retrieve("deepgram_api_key")
        s.groq_api_key       = self.keychain.retrieve("groq_api_key")
        s.selected_model     = self.settings.get("selected_model",     "nova-3-general")
        s.selected_language  = self.settings.get("selected_language",  "en-US")
        s.selected_hotkey    = self.settings.get("selected_hotkey",    "right_alt")
        s.selected_groq_model           = self.settings.get("selected_groq_model",           "")
        s.correction_mode_enabled       = self.settings.get("correction_mode_enabled",       False)
        s.grammar_correction_enabled    = self.settings.get("grammar_correction_enabled",    False)
        s.code_mix_enabled              = self.settings.get("code_mix_enabled",              False)
        s.selected_code_mix             = self.settings.get("selected_code_mix",             "")
        s.target_language_enabled       = self.settings.get("target_language_enabled",       False)
        s.selected_target_language      = self.settings.get("selected_target_language",      "English")
        s.selected_overlay_theme        = self.settings.get("selected_overlay_theme",        "Vibrant Blue")

    # ------------------------------------------------------------------ #
    # Recording flow                                                       #
    # ------------------------------------------------------------------ #

    def _start_recording(self):
        print(f"[DEBUG] Start recording | api_key set: {bool(self.state.deepgram_api_key)} | model: {self.state.selected_model} | lang: {self.state.selected_language}")
        self.state.set_recording_state(RecordingState.RECORDING)
        self.deepgram.connect(
            api_key=self.state.deepgram_api_key,
            model=self.state.selected_model,
            language=self.state.selected_language,
        )
        self.overlay.show()
        self.muter.mute()
        winsound.Beep(400, 200)
        self.deepgram.wait_until_ready()
        self.audio_engine.start_capture(self.deepgram.send_audio)

    def _stop_and_transcribe(self):
        print("[DEBUG] Stop recording — waiting for transcript...")
        self.state.set_recording_state(RecordingState.TRANSCRIBING)
        self.audio_engine.stop_capture()
        self.muter.unmute()
        winsound.Beep(5000, 100)
        self.overlay.hide()

        def on_transcript(transcript: str):
            print(f"[DEBUG] Transcript received: {transcript!r}")
            if not transcript.strip():
                self.state.set_recording_state(RecordingState.IDLE)
                return

            def inject(text: str):
                print(f"[DEBUG] Injecting text: {text!r}")
                self.state.last_transcript = text
                self.injector.inject(text)
                self.state.set_recording_state(RecordingState.IDLE)

            has_groq = self.state.groq_api_key and self.state.selected_groq_model
            code_mix = self.state.selected_code_mix if self.state.code_mix_enabled else None
            target_lang = self.state.selected_target_language if self.state.target_language_enabled else None

            if has_groq and any([
                self.state.correction_mode_enabled,
                self.state.grammar_correction_enabled,
                code_mix,
                target_lang,
            ]):
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
                inject(transcript)

        self.deepgram.close_stream(on_transcript)

    # ------------------------------------------------------------------ #
    # UI helpers                                                           #
    # ------------------------------------------------------------------ #

    def _open_settings(self):
        # Called from tray thread — schedule on tkinter main thread
        if hasattr(self, "_tk_root") and self._tk_root:
            self._tk_root.after(0, self.settings_win.open)

    def _quit(self):
        self.hotkey_mgr.stop_listening()
        if hasattr(self, "_tk_root") and self._tk_root:
            self._tk_root.quit()
        sys.exit(0)

    # ------------------------------------------------------------------ #
    # Entry                                                                #
    # ------------------------------------------------------------------ #

    def run(self):
        import tkinter as tk

        # Hidden root window — keeps tkinter's main loop alive
        self._tk_root = tk.Tk()
        self._tk_root.withdraw()

        self.hotkey_mgr.start_listening()

        # Tray runs in background thread
        self.tray.run_in_thread()

        print("VocalFlow running. Check the system tray.")

        # tkinter main loop on main thread (required on Windows)
        self._tk_root.mainloop()


if __name__ == "__main__":
    app = VocalFlowApp()
    app.run()
