"""
Optional LLM post-processing via Groq.
Takes the raw Deepgram transcript and cleans it up before it gets pasted.

Supported operations (applied in order):
  1. Code-mix transliteration  - e.g. Hinglish Devanagari → Roman script
  2. Spelling correction
  3. Grammar correction
  4. Translation / style conversion
"""
import threading
from dataclasses import dataclass
from typing import Callable, List, Optional

import httpx


@dataclass
class GroqModel:
    id: str
    display_name: str


# These are "style" targets, not pure languages — they get transliterated, not translated
CODE_MIX_STYLES = {
    "Hinglish", "Tanglish", "Benglish", "Kanglish", "Tenglish",
    "Minglish", "Punglish", "Spanglish", "Franglais", "Portuñol",
    "Chinglish", "Japlish", "Konglish", "Arabizi", "Sheng", "Camfranglais",
}

# Shown in the Features tab dropdown
CODE_MIX_OPTIONS = [
    ("Hinglish",     "Hindi + English"),
    ("Tanglish",     "Tamil + English"),
    ("Benglish",     "Bengali + English"),
    ("Kanglish",     "Kannada + English"),
    ("Tenglish",     "Telugu + English"),
    ("Minglish",     "Marathi + English"),
    ("Punglish",     "Punjabi + English"),
    ("Spanglish",    "Spanish + English"),
    ("Franglais",    "French + English"),
    ("Portuñol",     "Portuguese + Spanish"),
    ("Chinglish",    "Chinese + English"),
    ("Japlish",      "Japanese + English"),
    ("Konglish",     "Korean + English"),
    ("Arabizi",      "Arabic + English"),
    ("Sheng",        "Swahili + English"),
    ("Camfranglais", "French + English + local languages"),
]

# Shown in the "Convert to Language" dropdown
TARGET_LANGUAGES = [
    # Pure languages
    "English", "Hindi", "Spanish", "French", "German",
    "Portuguese", "Japanese", "Korean", "Arabic", "Bengali",
    "Tamil", "Telugu", "Kannada", "Marathi", "Punjabi",
    "Russian", "Chinese (Simplified)", "Italian", "Dutch", "Swahili",
    # Code-mix styles (transliterate rather than translate)
    "Hinglish", "Tanglish", "Benglish", "Kanglish", "Tenglish",
    "Minglish", "Punglish", "Spanglish", "Franglais", "Portuñol",
    "Chinglish", "Japlish", "Konglish", "Arabizi", "Sheng", "Camfranglais",
]


class GroqService:
    def fetch_models(self, api_key: str, callback: Callable[[List[GroqModel]], None]):
        """Fetch available models from Groq's API."""
        def _fetch():
            try:
                r = httpx.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10,
                )
                models = [
                    GroqModel(id=m["id"], display_name=m["id"])
                    for m in r.json().get("data", [])
                    if m.get("object") == "model"
                ]
                callback(sorted(models, key=lambda m: m.id))
            except Exception:
                callback([])

        threading.Thread(target=_fetch, daemon=True).start()

    def process_text(
        self,
        text: str,
        api_key: str,
        model: str,
        fix_spelling: bool = False,
        fix_grammar: bool = False,
        code_mix: Optional[str] = None,
        target_language: Optional[str] = None,
        callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Send the transcript to Groq for cleanup.
        Falls back to the original text if anything goes wrong.
        """
        if not api_key or not model or not any([fix_spelling, fix_grammar, code_mix, target_language]):
            if callback:
                callback(text)
            return

        def _process():
            instructions, step = [], 1

            if code_mix:
                # Transliterate non-Roman script to Roman — don't translate
                instructions.append(
                    f"{step}. The input is in {code_mix}. Transliterate any non-Roman script "
                    f"to Roman script. Keep English words as-is. Do not translate."
                )
                step += 1
            if fix_spelling:
                instructions.append(f"{step}. Fix any spelling mistakes. Do not change meaning.")
                step += 1
            if fix_grammar:
                instructions.append(f"{step}. Fix any grammar mistakes. Do not change meaning.")
                step += 1
            if target_language:
                if target_language in CODE_MIX_STYLES:
                    # Style conversion — transliterate, don't translate
                    instructions.append(
                        f"{step}. Rewrite in {target_language} style: keep English words as-is, "
                        f"transliterate non-Roman script to Roman. Do not translate."
                    )
                else:
                    # Full translation to a target language
                    instructions.append(f"{step}. Translate the entire text to {target_language}.")

            system_prompt = (
                "Process the following text by applying these steps in order:\n"
                + "\n".join(instructions)
                + "\nReturn only the final processed text with no explanation."
            )

            try:
                r = httpx.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user",   "content": text},
                        ],
                        "temperature": 0,  # deterministic output
                    },
                    timeout=15,
                )
                result = r.json()["choices"][0]["message"]["content"].strip()
                if callback:
                    callback(result or text)
            except Exception:
                # If Groq fails for any reason, fall back to the raw transcript
                if callback:
                    callback(text)

        threading.Thread(target=_process, daemon=True).start()
