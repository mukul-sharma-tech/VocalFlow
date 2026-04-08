import threading
import keyboard
from core.app_state import HOTKEY_OPTIONS

class HotkeyManager:
    def __init__(self, app_state, on_press, on_release):
        self._state = app_state; self._press = on_press; self._release = on_release
        self._down = False; self._hook = None

    def start_listening(self): self._hook = keyboard.hook(self._handle, suppress=False)
    def stop_listening(self):
        if self._hook: keyboard.unhook(self._hook); self._hook = None

    def _handle(self, e: keyboard.KeyboardEvent):
        target = HOTKEY_OPTIONS.get(self._state.selected_hotkey, {}).get("key", "")
        if not target or e.name != target: return
        if e.event_type == keyboard.KEY_DOWN and not self._down:
            self._down = True; threading.Thread(target=self._press, daemon=True).start()
        elif e.event_type == keyboard.KEY_UP and self._down:
            self._down = False; threading.Thread(target=self._release, daemon=True).start()
