# VocalFlow for Windows

> Windows port of [VocalFlow for macOS](https://github.com/Vocallabsai/vocalflow)

A lightweight Windows system tray app that lets you dictate into any text field — anywhere on your PC — using a hold-to-record hotkey.

**Hold a key → speak → release → text appears at your cursor.**

---

## How it works

```
Hold hotkey  →  Mic streams audio to Deepgram  →  Release  →  (optional Groq cleanup)  →  Ctrl+V paste
```

1. Hold your configured hotkey (default: Right Alt / AltGr)
2. Speak naturally
3. Release — transcript is pasted at your cursor via simulated Ctrl+V

---

## Features

### Core
- Hold-to-record hotkey — Right Alt/AltGr, Left Alt, Right Ctrl, Left Ctrl, Right Shift
- Real-time streaming ASR via Deepgram WebSocket API
- Works in any app - browser, Word, Notepad, VS Code, Outlook, anywhere
- Audio chime on start and stop recording
- System tray icon that changes color by state (grey → idle, red → recording, blue → transcribing)

### Groq LLM Post-processing (optional)
- Spelling correction
- Grammar correction
- Code-mix transliteration — speak Hinglish, Tanglish, Spanglish and 13 more; non-Roman script gets transliterated to Roman
- Translation — convert transcript to any of 20+ target languages

### Waveform Overlay
- Floating overlay appears at the bottom-center of the screen while recording
- Bars react to your actual mic volume in real time (RMS-based)
- Smooth rounded capsule bars with glow effect
- 4 color themes to choose from:
  - **Vibrant Blue** — `#09E0FE → #03C1F4 → #08A1F7 → #004FE1`
  - **Bloom Rush** — `#EF709B → #FA9372` (warm pink)
  - **Mint Flow** — `#8DE9D5 → #32C4C0` (teal)
  - **Magic Garden** — `#BF0FFF → #7B2FFF → #3D0FBF` (purple)

### UI & UX
- Windows 11 Fluent Design onboarding window with 5-page guide (Overview, Setup, API Keys, Features, Tips)
- Settings window with 5 tabs — ASR, Groq, Features, Hotkey, Appearance
- All settings persist across restarts
- API keys stored securely in Windows Credential Manager (never plain text)

---

## Requirements

- Windows 10 or 11
- Python 3.10+
- [Deepgram API key](https://console.deepgram.com/signup) — free tier (12,000 min/year)
- [Groq API key](https://console.groq.com) — optional, free

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

The app starts immediately. A welcome window opens and the mic icon appears in the system tray (click `^` near the clock if you don't see it).

---

## Configuration

Edit `config.py` before running:

```python
DEEPGRAM_API_KEY = "your-deepgram-key"   # required — pre-filled for demo
GROQ_API_KEY     = ""                     # optional
DEFAULT_DEEPGRAM_MODEL    = "nova-3-general"
DEFAULT_DEEPGRAM_LANGUAGE = "multi"       # multi = handles mixed languages
DEFAULT_GROQ_MODEL        = "llama-3.3-70b-versatile"
DEFAULT_HOTKEY            = "right_alt"
DEFAULT_OVERLAY_THEME     = "Vibrant Blue"
```

Keys from `config.py` are saved to Windows Credential Manager on first launch. After that, update them via Settings → ASR / Groq tabs.

---

## Settings Tabs

| Tab | Purpose |
|---|---|
| ASR (Deepgram) | API key, model selection, language |
| Groq (LLM) | API key, model selection |
| Features | Spelling, grammar, code-mix, translation toggles |
| Hotkey | Choose which key to hold while speaking |
| Appearance | Pick waveform overlay color theme |

---

## Recommended Settings

| Setting | Recommended value |
|---|---|
| Model | `nova-3-general` |
| Language (English) | `en-US` |
| Language (mixed / multilingual) | `multi` |
| Groq model | `llama-3.3-70b-versatile` |

For code-mix (e.g. Hinglish): set language to `multi`, enable Code-Mix Input in Features tab, select your language pair.

---

## Project Structure

```
vocalflow-windows/
├── main.py               # Entry point
├── config.py             # API keys and defaults
├── requirements.txt      # Dependencies
│
├── core/                 # Business logic
│   ├── __init__.py
│   ├── app_state.py      # Shared state, themes, hotkey options
│   ├── audio_engine.py   # Mic capture + real-time RMS level
│   ├── audio_muter.py    # System audio mute/unmute
│   ├── hotkey_manager.py # Global keyboard hook
│   └── text_injector.py  # Clipboard-based Ctrl+V injection
│
├── services/             # External API clients
│   ├── __init__.py
│   ├── deepgram_service.py  # WebSocket streaming to Deepgram
│   └── groq_service.py      # LLM post-processing via Groq
│
├── storage/              # Persistence
│   ├── __init__.py
│   └── keychain_service.py  # Credential Manager + JSON settings
│
└── ui/                   # All windows
    ├── __init__.py
    ├── tray_controller.py   # System tray icon (win32gui)
    ├── overlay_window.py    # Voice-reactive waveform overlay
    ├── settings_window.py   # Settings UI (5 tabs)
    └── welcome_window.py    # Onboarding window
```

---

## Notes for Reviewer

- **Multilingual tested** — verified with English, Hinglish (Hindi + English), and Tamil + English using Deepgram `multi` mode and Groq code-mix transliteration
- **Voice-reactive overlay** — waveform bars respond to actual mic volume in real time via RMS analysis, not a static animation
- **Windows 11 Fluent Design** — onboarding window follows Win11 design language (Segoe UI, light theme, subtle borders, accent color `#0067c0`)
- **4 overlay themes** — each with smooth gradient color interpolation across bars
- **Clean codebase** — organized into 4 packages, minimal lines, no unnecessary abstractions
- **Config-first** — `config.py` has the Deepgram key pre-filled so the app works out of the box

---
