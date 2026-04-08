"""
Watches for the configured hotkey globally across all apps.
Uses the `keyboard` library which hooks into Windows low-level keyboard events.

Note: AltGr on non-US keyboards fires both 'alt gr' AND 'right ctrl' simultaneously.
The _key_down guard prevents double-triggering from that.
"""
import threading

import keyboard

from core.app_state import AppState, HOTKEY_OPTIONS


class HotkeyManager:
    def __init__(self, app_state: AppState, on_press, on_release):
        self._app_state = app_state
        self._on_press = on_press
        self._on_release = on_release
        self._key_down = False  # tracks whether we're currently in a "held" state
        self._hook = None

    def start_listening(self):
        self._hook = keyboard.hook(self._handle_event, suppress=False)

    def stop_listening(self):
        if self._hook:
            keyboard.unhook(self._hook)
            self._hook = None

    def _handle_event(self, event: keyboard.KeyboardEvent):
        target = HOTKEY_OPTIONS.get(self._app_state.selected_hotkey, {}).get("key", "")
        if not target or event.name != target:
            return

        if event.event_type == keyboard.KEY_DOWN and not self._key_down:
            self._key_down = True
            threading.Thread(target=self._on_press, daemon=True).start()
        elif event.event_type == keyboard.KEY_UP and self._key_down:
            self._key_down = False
            threading.Thread(target=self._on_release, daemon=True).start()
