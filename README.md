# VocalFlow for Windows

Hold a key → speak → release → text appears at your cursor. Windows port of [VocalFlow](../README.md).

## Requirements

- Windows 10/11
- Python 3.11+
- A [Deepgram API key](https://console.deepgram.com/signup) (free tier works)
- A [Groq API key](https://console.groq.com) (optional, for post-processing)

## Setup

```bash
cd vocalflow-windows
pip install -r requirements.txt
python main.py
```

## Usage

1. A mic icon appears in the system tray
2. Right-click → **Settings**
3. Paste your Deepgram API key → Save → Fetch Models
4. Choose a model and language
5. (Optional) Add Groq API key for spelling/grammar/translation
6. Hold **Right Alt** (or your configured key), speak, release — text is pasted at your cursor

## Features

- Hold-to-record hotkey (Right Alt, Left Alt, Right/Left Ctrl, Right Shift)
- Real-time streaming ASR via Deepgram WebSocket
- Optional Groq LLM post-processing:
  - Spelling correction
  - Grammar correction
  - Code-mix transliteration (Hinglish, Tanglish, Spanglish, and 13 more)
  - Translation to any target language
- Works in any app — text injected via Ctrl+V
- System tray icon with recording state indicator
- API keys stored in Windows Credential Manager

## Notes

- Run as administrator if the global hotkey doesn't work (some apps block low-level keyboard hooks)
- The `keyboard` library requires elevated privileges on some systems
