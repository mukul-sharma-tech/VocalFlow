# VocalFlow for Windows

A lightweight Windows system tray app that lets you dictate into any text field — anywhere on your PC — using a hold-to-record hotkey.

**Hold a key → speak → release → text appears at your cursor.**

> Windows port of [VocalFlow for macOS](https://github.com/Vocallabsai/vocalflow)

---

## How it works

1. Hold your configured hotkey (default: Right Alt / AltGr)
2. Speak
3. Release — transcript is injected at your cursor via simulated Ctrl+V

Audio streams in real-time to [Deepgram](https://deepgram.com) for transcription. Optionally, the raw transcript passes through [Groq](https://groq.com) for spelling/grammar correction, code-mix transliteration, or translation.

---

## Features

- Hold-to-record hotkey — Right Alt/AltGr, Left Alt, Right/Left Ctrl, Right Shift
- Real-time streaming ASR via Deepgram WebSocket
- Optional Groq LLM post-processing:
  - Spelling correction
  - Grammar correction
  - Code-mix transliteration (Hinglish, Tanglish, Spanglish, and 13 more)
  - Translation to any target language
- Works in any app — text injected via Ctrl+V
- System tray app with color-coded recording state icon
- Animated waveform overlay that reacts to your voice volume
- 4 color themes for the overlay
- Deepgram balance display in Settings
- API keys stored in Windows Credential Manager

---

## Requirements

- Windows 10 or 11
- Python 3.11+
- Deepgram API key — free tier at [console.deepgram.com/signup](https://console.deepgram.com/signup)
- Groq API key — optional, free at [console.groq.com](https://console.groq.com)

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

The app starts immediately — a welcome window opens with setup instructions, and the mic icon appears in the system tray.

---

## Configuration

API keys and defaults are in `config.py`:

```python
DEEPGRAM_API_KEY = "your-key-here"   # pre-filled for demo
GROQ_API_KEY     = ""                 # optional
```

On first launch, keys from `config.py` are automatically saved to Windows Credential Manager. You can also update them anytime via Settings → ASR / Groq tabs.

---

## Setup (Settings window)

Right-click the tray icon → Settings:

| Tab | What to do |
|---|---|
| ASR (Deepgram) | Key is pre-filled → Fetch Models → pick model + language |
| Hotkey | Pick your trigger key (default: Right Alt) |
| Groq (LLM) | Optional — paste key → Fetch Models |
| Features | Enable spelling/grammar/code-mix/translation |
| Appearance | Pick waveform overlay color theme |

---

## Recommended Settings

| Setting | Value |
|---|---|
| Deepgram model | `nova-3-general` |
| Language (English) | `en-US` |
| Language (mixed) | `multi` |
| Groq model | `llama-3.3-70b-versatile` |

---

## Project Structure

```
vocalflow-windows/
├── main.py               # Entry point
├── config.py             # API keys and defaults
├── requirements.txt      # Dependencies
│
├── core/                 # Business logic
│   ├── app_state.py      # Shared state, themes, hotkey options
│   ├── audio_engine.py   # Mic capture + RMS level for visualization
│   ├── audio_muter.py    # System audio mute during recording
│   ├── hotkey_manager.py # Global keyboard hook
│   └── text_injector.py  # Clipboard-based Ctrl+V injection
│
├── services/             # External API clients
│   ├── deepgram_service.py  # WebSocket streaming + model/balance fetch
│   └── groq_service.py      # LLM post-processing
│
├── storage/              # Persistence
│   └── keychain_service.py  # Credential Manager + JSON settings
│
└── ui/                   # All windows
    ├── tray_controller.py   # System tray icon (win32gui)
    ├── overlay_window.py    # Animated waveform overlay
    ├── settings_window.py   # Settings UI (5 tabs)
    └── welcome_window.py    # Onboarding window
```

---

## Extra Features (vs macOS original)

- Voice-reactive waveform overlay - bars pulse with your actual mic volume
- Groq console link in Settings → Groq tab
- `config.py` for easy key configuration without touching the UI
- Windows 11 Fluent Design onboarding window

---
