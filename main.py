"""
VocalFlow for Windows
Hold a key → speak → release → text appears wherever your cursor is.
"""
import sys
import threading


def _load_app():
    """
    Load all heavy dependencies in a background thread while the
    welcome window is already visible. This makes startup feel instant.
    """
    import winsound
    from core import AppState, RecordingState, AudioEngine, AudioMuter, HotkeyManager, TextInjector
    from services import DeepgramService, GroqService
    from storage import KeychainService, SettingsService
    from ui import TrayController, OverlayWindow, SettingsWindow

    return (winsound, AppState, RecordingState, AudioEngine, AudioMuter,
            HotkeyManager, TextInjector, DeepgramService, GroqService,
            KeychainService, SettingsService, TrayController, OverlayWindow, SettingsWindow)


def main():
    # Load all heavy deps (blocks briefly but only once)
    (winsound, AppState, RecordingState, AudioEngine, AudioMuter,
     HotkeyManager, TextInjector, DeepgramService, GroqService,
     KeychainService, SettingsService, TrayController, OverlayWindow, SettingsWindow) = _load_app()

    app = VocalFlowApp(
        winsound, AppState, RecordingState, AudioEngine, AudioMuter,
        HotkeyManager, TextInjector, DeepgramService, GroqService,
        KeychainService, SettingsService, TrayController, OverlayWindow, SettingsWindow
    )
    app.run()  # shows welcome window non-blocking, starts tray + hotkey immediately


class VocalFlowApp:
    def __init__(self, winsound, AppState, RecordingState, AudioEngine, AudioMuter,
                 HotkeyManager, TextInjector, DeepgramService, GroqService,
                 KeychainService, SettingsService, TrayController, OverlayWindow, SettingsWindow):
        self._winsound       = winsound
        self._RecordingState = RecordingState

        self.keychain = KeychainService()
        self.settings = SettingsService()
        self.state    = AppState()
        self._load_settings()

        self.audio_engine = AudioEngine()
        self.deepgram     = DeepgramService()
        self.groq         = GroqService()
        self.injector     = TextInjector()
        self.muter        = AudioMuter()

        self.overlay      = OverlayWindow(self.state)
        self.settings_win = SettingsWindow(self.state, self.keychain, self.settings)
        self.tray         = TrayController(self.state, self._open_settings, self._quit)
        self.hotkey_mgr   = HotkeyManager(
            self.state,
            on_press=self._start_recording,
            on_release=self._stop_and_transcribe,
        )

    def _load_settings(self):
        """Pull saved settings into app state on startup.
        Falls back to config.py defaults if nothing is saved yet."""
        import config
        s = self.state

        # API keys: use saved keychain value, fall back to config.py hardcoded key
        saved_dg  = self.keychain.retrieve("deepgram_api_key")
        saved_groq = self.keychain.retrieve("groq_api_key")
        s.deepgram_api_key = saved_dg  if saved_dg  else config.DEEPGRAM_API_KEY
        s.groq_api_key     = saved_groq if saved_groq else config.GROQ_API_KEY

        # If we loaded from config (first run), persist it to keychain
        if not saved_dg and config.DEEPGRAM_API_KEY:
            self.keychain.store("deepgram_api_key", config.DEEPGRAM_API_KEY)
        if not saved_groq and config.GROQ_API_KEY:
            self.keychain.store("groq_api_key", config.GROQ_API_KEY)

        s.selected_model             = self.settings.get("selected_model",             config.DEFAULT_DEEPGRAM_MODEL)
        s.selected_language          = self.settings.get("selected_language",          config.DEFAULT_DEEPGRAM_LANGUAGE)
        s.selected_hotkey            = self.settings.get("selected_hotkey",            config.DEFAULT_HOTKEY)
        s.selected_groq_model        = self.settings.get("selected_groq_model",        config.DEFAULT_GROQ_MODEL)
        s.correction_mode_enabled    = self.settings.get("correction_mode_enabled",    False)
        s.grammar_correction_enabled = self.settings.get("grammar_correction_enabled", False)
        s.code_mix_enabled           = self.settings.get("code_mix_enabled",           False)
        s.selected_code_mix          = self.settings.get("selected_code_mix",          "")
        s.target_language_enabled    = self.settings.get("target_language_enabled",    False)
        s.selected_target_language   = self.settings.get("selected_target_language",   "English")
        s.selected_overlay_theme     = self.settings.get("selected_overlay_theme",     config.DEFAULT_OVERLAY_THEME)

    def _start_recording(self):
        RS = self._RecordingState
        if self.state.recording_state == RS.RECORDING:
            return
        self.state.set_recording_state(RS.RECORDING)
        self.deepgram.connect(
            api_key=self.state.deepgram_api_key,
            model=self.state.selected_model,
            language=self.state.selected_language,
        )
        self.overlay.show()
        self._winsound.Beep(400, 150)
        # Note: audio muting disabled — it caused issues with some hotkeys
        self.deepgram.wait_until_ready()
        self.audio_engine.start_capture(self.deepgram.send_audio)

    def _stop_and_transcribe(self):
        RS = self._RecordingState
        if self.state.recording_state != RS.RECORDING:
            return
        self.state.set_recording_state(RS.TRANSCRIBING)
        self.audio_engine.stop_capture()
        self._winsound.Beep(300, 150)
        self.overlay.hide()
        self.deepgram.close_stream(self._on_transcript)

    def _on_transcript(self, transcript: str):
        RS = self._RecordingState
        if not transcript.strip():
            self.state.set_recording_state(RS.IDLE)
            return

        def inject(text: str):
            self.state.last_transcript = text
            self.injector.inject(text)
            self.state.set_recording_state(RS.IDLE)

        has_groq    = bool(self.state.groq_api_key and self.state.selected_groq_model)
        code_mix    = self.state.selected_code_mix if self.state.code_mix_enabled else None
        target_lang = self.state.selected_target_language if self.state.target_language_enabled else None
        use_groq    = has_groq and any([
            self.state.correction_mode_enabled,
            self.state.grammar_correction_enabled,
            code_mix, target_lang,
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
            inject(transcript)

    def _open_settings(self):
        if hasattr(self, "_tk_root") and self._tk_root:
            self._tk_root.after(0, self.settings_win.open)

    def _quit(self):
        self.hotkey_mgr.stop_listening()
        if hasattr(self, "_tk_root") and self._tk_root:
            self._tk_root.quit()
        sys.exit(0)

    def run(self):
        import tkinter as tk

        # Hidden root keeps tkinter's main loop alive
        self._tk_root = tk.Tk()
        self._tk_root.withdraw()

        # Keep alive even when no windows are open
        def _keep_alive():
            self._tk_root.after(500, _keep_alive)
        _keep_alive()

        # Start everything immediately — don't wait for welcome window
        self.hotkey_mgr.start_listening()
        self.tray.run_in_thread()

        # Show welcome window as a non-blocking info screen
        self._tk_root.after(100, self._show_welcome)

        print("VocalFlow running!! Please check the system tray.")
        self._tk_root.mainloop()

    def _show_welcome(self):
        from ui.welcome_window import WelcomeWindow
        WelcomeWindow(self._tk_root)


if __name__ == "__main__":
    main()
