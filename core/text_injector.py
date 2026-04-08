import threading, time
import pyautogui, pyperclip

class TextInjector:
    def inject(self, text: str):
        try: saved = pyperclip.paste()
        except Exception: saved = ""
        pyperclip.copy(text); time.sleep(0.05); pyautogui.hotkey("ctrl", "v")
        def _restore(): time.sleep(0.3); pyperclip.copy(saved)
        threading.Thread(target=_restore, daemon=True).start()
