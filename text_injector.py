"""
Pastes text at the current cursor position using the clipboard.

Strategy:
  1. Save whatever's currently on the clipboard
  2. Copy the transcript to the clipboard
  3. Simulate Ctrl+V to paste it
  4. Restore the original clipboard content after a short delay
"""
import threading
import time

import pyautogui
import pyperclip


class TextInjector:
    def inject(self, text: str):
        # Save the user's current clipboard so we can restore it after pasting
        try:
            saved = pyperclip.paste()
        except Exception:
            saved = ""

        pyperclip.copy(text)
        time.sleep(0.05)  # give the clipboard a moment to settle
        pyautogui.hotkey("ctrl", "v")

        # Restore original clipboard content after the paste has gone through
        def _restore():
            time.sleep(0.3)
            try:
                pyperclip.copy(saved)
            except Exception:
                pass

        threading.Thread(target=_restore, daemon=True).start()
