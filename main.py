import sys, winsound
from core import AppState, RecordingState, AudioEngine, AudioMuter, HotkeyManager, TextInjector
from services import DeepgramService, GroqService
from storage import KeychainService, SettingsService
from ui import TrayController, OverlayWindow, SettingsWindow
import config

class VocalFlowApp:
    def __init__(self):
        self.kc = KeychainService(); self.cfg = SettingsService()
        self.state = AppState(); self._load()
        self.audio = AudioEngine(); self.dg = DeepgramService()
        self.groq = GroqService(); self.inj = TextInjector()
        self.overlay = OverlayWindow(self.state, self.audio)
        self.settings_win = SettingsWindow(self.state, self.kc, self.cfg)
        self.tray = TrayController(self.state, self._open_settings, self._quit)
        self.hk = HotkeyManager(self.state, self._start, self._stop)

    def _load(self):
        s = self.state
        # Use saved key, fall back to config.py on first run
        s.deepgram_api_key = self.kc.retrieve("deepgram_api_key") or config.DEEPGRAM_API_KEY
        s.groq_api_key     = self.kc.retrieve("groq_api_key")     or config.GROQ_API_KEY
        if not self.kc.retrieve("deepgram_api_key") and config.DEEPGRAM_API_KEY:
            self.kc.store("deepgram_api_key", config.DEEPGRAM_API_KEY)
        g = self.cfg.get
        s.selected_model             = g("selected_model",             config.DEFAULT_DEEPGRAM_MODEL)
        s.selected_language          = g("selected_language",          config.DEFAULT_DEEPGRAM_LANGUAGE)
        s.selected_hotkey            = g("selected_hotkey",            config.DEFAULT_HOTKEY)
        s.selected_groq_model        = g("selected_groq_model",        config.DEFAULT_GROQ_MODEL)
        s.correction_mode_enabled    = g("correction_mode_enabled",    False)
        s.grammar_correction_enabled = g("grammar_correction_enabled", False)
        s.code_mix_enabled           = g("code_mix_enabled",           False)
        s.selected_code_mix          = g("selected_code_mix",          "")
        s.target_language_enabled    = g("target_language_enabled",    False)
        s.selected_target_language   = g("selected_target_language",   "English")
        s.selected_overlay_theme     = g("selected_overlay_theme",     config.DEFAULT_OVERLAY_THEME)

    def _start(self):
        if self.state.recording_state == RecordingState.RECORDING: return
        self.state.set_recording_state(RecordingState.RECORDING)
        # Open WebSocket early so it's ready before audio starts
        self.dg.connect(self.state.deepgram_api_key, self.state.selected_model, self.state.selected_language)
        self.overlay.show(); winsound.Beep(400, 150)  # start chime
        self.dg.wait_until_ready(); self.audio.start_capture(self.dg.send_audio)

    def _stop(self):
        if self.state.recording_state != RecordingState.RECORDING: return
        self.state.set_recording_state(RecordingState.TRANSCRIBING)
        self.audio.stop_capture(); winsound.Beep(300, 150)  # stop chime
        self.overlay.hide(); self.dg.close_stream(self._on_transcript)

    def _on_transcript(self, text: str):
        if not text.strip(): self.state.set_recording_state(RecordingState.IDLE); return
        def inject(t):
            self.state.last_transcript = t; self.inj.inject(t)
            self.state.set_recording_state(RecordingState.IDLE)
        s = self.state
        cm = s.selected_code_mix if s.code_mix_enabled else None
        tl = s.selected_target_language if s.target_language_enabled else None
        if (s.groq_api_key and s.selected_groq_model and
                any([s.correction_mode_enabled, s.grammar_correction_enabled, cm, tl])):
            self.groq.process_text(text, s.groq_api_key, s.selected_groq_model,
                s.correction_mode_enabled, s.grammar_correction_enabled, cm, tl, inject)
        else:
            inject(text)  # no Groq — paste raw transcript

    def _open_settings(self):
        if hasattr(self, "_root"): self._root.after(0, self.settings_win.open)

    def _quit(self):
        self.hk.stop_listening()
        if hasattr(self, "_root"): self._root.quit()
        sys.exit(0)

    def run(self):
        import tkinter as tk
        self._root = tk.Tk(); self._root.withdraw()
        def _alive(): self._root.after(500, _alive)  # keep tkinter loop alive
        _alive()
        self.hk.start_listening(); self.tray.run_in_thread()
        # Show welcome window non-blocking — app is already running
        self._root.after(100, lambda: __import__("ui.welcome_window", fromlist=["WelcomeWindow"]).WelcomeWindow(self._root))
        print("VocalFlow running - check the system tray.")
        self._root.mainloop()

if __name__ == "__main__":
    VocalFlowApp().run()
