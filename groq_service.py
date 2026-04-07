import threading
from dataclasses import dataclass
from typing import Callable, List, Optional
import httpx


@dataclass
class GroqModel:
    id: str
    display_name: str


CODE_MIX_STYLES = {
    "Hinglish", "Tanglish", "Benglish", "Kanglish", "Tenglish",
    "Minglish", "Punglish", "Spanglish", "Franglais", "Portuñol",
    "Chinglish", "Japlish", "Konglish", "Arabizi", "Sheng", "Camfranglais",
}

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

TARGET_LANGUAGES = [
    "English", "Hindi", "Spanish", "French", "German",
    "Portuguese", "Japanese", "Korean", "Arabic", "Bengali",
    "Tamil", "Telugu", "Kannada", "Marathi", "Punjabi",
    "Russian", "Chinese (Simplified)", "Italian", "Dutch", "Swahili",
    "Hinglish", "Tanglish", "Benglish", "Kanglish", "Tenglish",
    "Minglish", "Punglish", "Spanglish", "Franglais", "Portuñol",
    "Chinglish", "Japlish", "Konglish", "Arabizi", "Sheng", "Camfranglais",
]


class GroqService:
    def fetch_models(self, api_key: str, callback: Callable[[List[GroqModel]], None]):
        def _fetch():
            try:
                r = httpx.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10,
                )
                print(f"[DEBUG] Groq models status: {r.status_code}")
                body = r.json()
                print(f"[DEBUG] Groq models response keys: {list(body.keys())}")
                data = body.get("data", [])
                print(f"[DEBUG] Groq raw model count: {len(data)}")
                models = [
                    GroqModel(id=m["id"], display_name=m["id"])
                    for m in data if m.get("object") == "model"
                ]
                models.sort(key=lambda m: m.id)
                print(f"[DEBUG] Groq filtered models: {[m.id for m in models]}")
                callback(models)
            except Exception as e:
                print(f"[DEBUG] Groq fetch error: {e}")
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
        callback: Callable[[str], None] = None,
    ):
        has_any = fix_spelling or fix_grammar or code_mix or target_language
        if not api_key or not model or not has_any:
            if callback:
                callback(text)
            return

        def _process():
            instructions = []
            step = 1
            if code_mix:
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
                    instructions.append(
                        f"{step}. Rewrite in {target_language} style: keep English words as-is, "
                        f"transliterate non-Roman script to Roman. Do not translate."
                    )
                else:
                    instructions.append(
                        f"{step}. Translate the entire text to {target_language}."
                    )

            system_prompt = (
                "Process the following text by applying these steps in order:\n"
                + "\n".join(instructions)
                + "\nReturn only the final processed text with no explanation."
            )

            try:
                r = httpx.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user",   "content": text},
                        ],
                        "temperature": 0,
                    },
                    timeout=15,
                )
                result = r.json()["choices"][0]["message"]["content"].strip()
                if callback:
                    callback(result if result else text)
            except Exception:
                if callback:
                    callback(text)

        threading.Thread(target=_process, daemon=True).start()
