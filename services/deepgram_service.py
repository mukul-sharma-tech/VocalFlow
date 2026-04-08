import asyncio, json, threading
from dataclasses import dataclass
from typing import Callable, List, Optional
import httpx, websockets

@dataclass
class DeepgramModel:
    canonical_name: str; display_name: str; languages: List[str]

class DeepgramService:
    def __init__(self):
        self._ws = None; self._loop = None; self._accumulated = ""
        self._waiting = False; self._cb = None
        self._ready = threading.Event()  # set when WebSocket handshake completes

    def connect(self, api_key, model, language):
        self._accumulated = ""; self._waiting = False; self._cb = None; self._ready.clear()
        self._api_key = api_key; self._model = model; self._language = language
        self._loop = asyncio.new_event_loop()
        self._loop.set_exception_handler(lambda *_: None)
        threading.Thread(target=lambda: self._loop.run_until_complete(self._run()), daemon=True).start()

    def wait_until_ready(self, timeout=5.0):
        return self._ready.wait(timeout=timeout)  # block until WS is open

    def send_audio(self, data: bytes):
        if self._loop and not self._loop.is_closed() and self._ws:
            asyncio.run_coroutine_threadsafe(self._send(data), self._loop)

    def close_stream(self, cb: Callable[[str], None]):
        # Send empty frame — Deepgram's signal to flush and finalize
        self._cb = cb; self._waiting = True
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._flush(), self._loop)

    def fetch_models(self, api_key, cb):
        def _f():
            try:
                r = httpx.get("https://api.deepgram.com/v1/models",
                              headers={"Authorization": f"Token {api_key}"}, timeout=10)
                streaming, names, langs = {}, {}, {}
                for m in r.json().get("stt", []):
                    c = m.get("canonical_name", "")
                    if not c: continue
                    streaming[c] = streaming.get(c, False) or m.get("streaming", False)
                    names.setdefault(c, m.get("name", c))
                    existing = langs.get(c, [])
                    langs[c] = existing + [l for l in m.get("languages", []) if l not in existing]
                models = []
                for c, s in streaming.items():
                    if not s: continue
                    ls = sorted(langs.get(c, []))
                    if c.startswith(("nova-2", "nova-3")): ls.append("multi")  # API doesn't list this
                    models.append(DeepgramModel(c, names.get(c, c), ls))
                cb(sorted(models, key=lambda m: m.canonical_name))
            except Exception: cb([])
        threading.Thread(target=_f, daemon=True).start()

    async def _run(self):
        url = (f"wss://api.deepgram.com/v1/listen?encoding=linear16&sample_rate=16000"
               f"&channels=1&model={self._model}&language={self._language}&punctuate=true&interim_results=true")
        try:
            async with websockets.connect(url, extra_headers={"Authorization": f"Token {self._api_key}"}) as ws:
                self._ws = ws; self._ready.set()
                async for msg in ws: self._handle(msg)
        except Exception: pass
        finally:
            self._ws = None
            if self._waiting: self._deliver()

    async def _send(self, data):
        if self._ws:
            try: await self._ws.send(data)
            except Exception: pass

    async def _flush(self):
        if self._ws:
            try: await self._ws.send(b"")  # empty frame = flush signal
            except Exception: self._deliver()
        await asyncio.sleep(3.0)  # safety timeout
        if self._waiting: self._deliver()

    def _handle(self, raw):
        try: msg = json.loads(raw)
        except Exception: return
        t = msg.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
        if msg.get("is_final") and t.strip():  # skip interim results
            self._accumulated += (" " if self._accumulated else "") + t
        if self._waiting and msg.get("is_final") and msg.get("speech_final"):
            self._deliver()

    def _deliver(self):
        if not self._waiting: return
        self._waiting = False; cb, self._cb = self._cb, None
        if cb: cb(self._accumulated)
