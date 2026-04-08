import threading
from dataclasses import dataclass
from typing import Callable, List, Optional
import httpx

@dataclass
class GroqModel:
    id: str; display_name: str

# These get transliterated (Roman script), not translated
CODE_MIX_STYLES = {"Hinglish","Tanglish","Benglish","Kanglish","Tenglish","Minglish","Punglish",
                   "Spanglish","Franglais","Portuñol","Chinglish","Japlish","Konglish","Arabizi","Sheng","Camfranglais"}

CODE_MIX_OPTIONS = [
    ("Hinglish","Hindi + English"),("Tanglish","Tamil + English"),("Benglish","Bengali + English"),
    ("Kanglish","Kannada + English"),("Tenglish","Telugu + English"),("Minglish","Marathi + English"),
    ("Punglish","Punjabi + English"),("Spanglish","Spanish + English"),("Franglais","French + English"),
    ("Portuñol","Portuguese + Spanish"),("Chinglish","Chinese + English"),("Japlish","Japanese + English"),
    ("Konglish","Korean + English"),("Arabizi","Arabic + English"),("Sheng","Swahili + English"),
    ("Camfranglais","French + English + local languages"),
]

TARGET_LANGUAGES = [
    "English","Hindi","Spanish","French","German","Portuguese","Japanese","Korean","Arabic","Bengali",
    "Tamil","Telugu","Kannada","Marathi","Punjabi","Russian","Chinese (Simplified)","Italian","Dutch","Swahili",
    "Hinglish","Tanglish","Benglish","Kanglish","Tenglish","Minglish","Punglish","Spanglish","Franglais",
    "Portuñol","Chinglish","Japlish","Konglish","Arabizi","Sheng","Camfranglais",
]

class GroqService:
    def fetch_models(self, api_key, cb):
        def _f():
            try:
                r = httpx.get("https://api.groq.com/openai/v1/models",
                              headers={"Authorization": f"Bearer {api_key}"}, timeout=10)
                cb(sorted([GroqModel(m["id"], m["id"]) for m in r.json().get("data", [])
                           if m.get("object") == "model"], key=lambda m: m.id))
            except Exception: cb([])
        threading.Thread(target=_f, daemon=True).start()

    def process_text(self, text, api_key, model, fix_spelling=False, fix_grammar=False,
                     code_mix=None, target_language=None, callback=None):
        if not api_key or not model or not any([fix_spelling, fix_grammar, code_mix, target_language]):
            if callback: callback(text); return

        def _p():
            steps, n = [], 1
            if code_mix: steps.append(f"{n}. Input is {code_mix}. Transliterate non-Roman to Roman. Keep English. No translation."); n+=1
            if fix_spelling: steps.append(f"{n}. Fix spelling. Keep meaning."); n+=1
            if fix_grammar: steps.append(f"{n}. Fix grammar. Keep meaning."); n+=1
            if target_language:
                if target_language in CODE_MIX_STYLES:
                    steps.append(f"{n}. Rewrite in {target_language} style. Transliterate non-Roman. No translation.")
                else:
                    steps.append(f"{n}. Translate to {target_language}.")
            prompt = "Apply these steps in order:\n" + "\n".join(steps) + "\nReturn only the result."
            try:
                r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": model, "temperature": 0,
                          "messages": [{"role":"system","content":prompt},{"role":"user","content":text}]},
                    timeout=15)
                result = r.json()["choices"][0]["message"]["content"].strip()
                if callback: callback(result or text)
            except Exception:
                if callback: callback(text)  # fallback to raw transcript on error
        threading.Thread(target=_p, daemon=True).start()
