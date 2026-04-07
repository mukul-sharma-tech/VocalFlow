import time
import pyperclip
import pyautogui


class TextInjector:
    def inject(self, text: str):
        # Save current clipboard
        try:
            saved = pyperclip.paste()
        except Exception:
            saved = ""

        # Write transcript to clipboard
        pyperclip.copy(text)
        time.sleep(0.05)  # let clipboard settle

        # Simulate Ctrl+V (Windows paste)
        pyautogui.hotkey("ctrl", "v")

        # Restore original clipboard after paste has been processed
        def _restore():
            time.sleep(0.3)
            try:
                pyperclip.copy(saved)
            except Exception:
                pass

        import threading
        threading.Thread(target=_restore, daemon=True).start()
