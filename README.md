# VocalFlow for Windows

A lightweight Windows system tray app that lets you dictate into any text field — anywhere on your PC — using a hold-to-record hotkey.

**Hold a key → speak → release → text appears at your cursor.**

> Windows port of [VocalFlow for macOS](../README.md)

---

## How it works

1. Hold your configured hotkey (default: Right Alt)
2. Speak
3. Release — the transcript is injected at your cursor via simulated Ctrl+V

Audio streams in real-time to [Deepgram](https://deepgram.com) for transcription. Optionally, the raw transcript passes through [Groq](https://groq.com) for spelling correction, grammar correction, code-mix transliteration, or translation before injection.

---

## Features

- **Hold-to-record hotkey** — Right Alt / AltGr, Left Alt, Right Ctrl, Left Ctrl, or Right Shift
- **Real-time streaming ASR** — powered by Deepgram's WebSocket API
- **Optional Groq LLM post-processing**
  - Spelling correction
  - Grammar correction
  - Code-mix transliteration (Hinglish, Tanglish, Spanglish, and 13 more)
  - Translation to any target language
- **Works in any app** — text injected via simulated Ctrl+V
- **System tray app** — no taskbar clutter, lives in the notification area
- **Animated waveform overlay** — shows while recording with 4 color themes
- **API keys stored securely** — saved in Windows Credential Manager, never plaintext

---

## Requirements

- Windows 10 or 11
- Python 3.11+
- A [Deepgram API key](https://console.deepgram.com/signup) — free tier available
- A [Groq API key](https://console.groq.com) — optional, for post-processing

---

## Setup

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Run the app**

```bash
python main.py
```

A mic icon appears in the system tray (bottom-right, near the clock).
If you don't see it, click the `^` arrow to expand hidden tray icons.

**3. Configure**

Right-click the tray icon → **Settings**

- **ASR tab** — paste your Deepgram API key → Save → Fetch Models → pick a model and language
- **Hotkey tab** — choose your preferred trigger key
- **Groq tab** *(optional)* — paste your Groq API key → Save → Fetch Models
- **Features tab** *(optional)* — enable spelling/grammar correction, code-mix, or translation
- **Appearance tab** — pick a waveform overlay color theme

**4. Dictate**

Click into any text field, hold your hotkey, speak, release. Done.

---

## Recommended Settings

| Setting | Recommended value |
|---|---|
| Deepgram model | `nova-3-general` |
| Language (English) | `en-US` |
| Language (multilingual / code-mix) | `multi` |
| Groq model | `llama-3.3-70b-versatile` |

---

## Code-Mix / Multilingual

If you speak a mix of two languages (e.g. Hindi + English), set:

1. ASR tab → Language → `multi`
2. Features tab → enable **Code-Mix Input** → select your mix (e.g. Hinglish)
3. Groq tab → make sure a model is selected

Deepgram will transcribe both languages, and Groq will transliterate any non-Roman script to Roman.

---

## Hotkey Notes

- **AltGr** on non-US keyboards maps to `Right Alt` in this app
- The global hotkey works in most apps without admin privileges
- If the hotkey doesn't fire while a UAC-elevated app is in focus (e.g. Task Manager), run the terminal as administrator

---

## Project Structure

```
vocalflow-windows/
├── main.py               # Entry point — wires everything together
├── app_state.py          # Shared state, themes, hotkey options
├── audio_engine.py       # Mic capture via sounddevice (16kHz mono PCM)
├── deepgram_service.py   # WebSocket streaming to Deepgram
├── groq_service.py       # LLM post-processing via Groq
├── hotkey_manager.py     # Global keyboard hook
├── text_injector.py      # Clipboard-based Ctrl+V injection
├── audio_muter.py        # Mutes system audio during recording
├── keychain_service.py   # API keys → Credential Manager, settings → JSON
├── tray_controller.py    # System tray icon via win32gui
├── overlay_window.py     # Animated waveform overlay (tkinter)
├── settings_window.py    # Settings UI (tkinter tabbed window)
└── requirements.txt      # Python dependencies
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `sounddevice` | Mic capture |
| `numpy` | Audio buffer handling |
| `websockets` | Deepgram WebSocket connection |
| `httpx` | HTTP requests (model fetching, Groq API) |
| `keyboard` | Global hotkey detection |
| `pyperclip` | Clipboard read/write |
| `pyautogui` | Simulate Ctrl+V |
| `Pillow` | Tray icon rendering |
| `keyring` | Windows Credential Manager |
| `pycaw` | Windows audio mute/unmute |
| `comtypes` | COM interface for pycaw |
| `pywin32` | Win32 API for system tray |

---

## License

[MIT](../LICENSE)
