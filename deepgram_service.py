import asyncio
import json
import threading
from typing import Callable, List, Optional
import httpx
import websockets
from dataclasses import dataclass


@dataclass
class DeepgramModel:
    canonical_name: str
    display_name: str
    languages: List[str]


class DeepgramService:
    def __init__(self):
        self._ws = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._accumulated: str = ""
        self._is_waiting_final = False
        self._final_callback: Optional[Callable[[str], None]] = None

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def connect(self, api_key: str, model: str, language: str):
        """Open WebSocket in a background thread's event loop."""
        self._accumulated = ""
        self._is_waiting_final = False
        self._final_callback = None
        self._api_key = api_key
        self._model = model
        self._language = language
        self._ready = threading.Event()

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def wait_until_ready(self, timeout=5.0) -> bool:
        """Block until WebSocket is connected or timeout."""
        return self._ready.wait(timeout=timeout)

    def send_audio(self, pcm_bytes: bytes):
        if self._loop and self._ws:
            asyncio.run_coroutine_threadsafe(self._send(pcm_bytes), self._loop)

    def close_stream(self, callback: Callable[[str], None]):
        self._final_callback = callback
        self._is_waiting_final = True
        if self._loop:
            asyncio.run_coroutine_threadsafe(self._flush(), self._loop)

    # ------------------------------------------------------------------ #
    # Async internals                                                      #
    # ------------------------------------------------------------------ #

    def _run_loop(self):
        self._loop.run_until_complete(self._connect_and_receive())

    async def _connect_and_receive(self):
        url = (
            f"wss://api.deepgram.com/v1/listen"
            f"?encoding=linear16&sample_rate=16000&channels=1"
            f"&model={self._model}&language={self._language}"
            f"&punctuate=true&interim_results=true"
        )
        headers = {"Authorization": f"Token {self._api_key}"}
        print(f"[DEBUG] Deepgram connecting: model={self._model} lang={self._language}")
        try:
            async with websockets.connect(url, extra_headers=headers) as ws:
                self._ws = ws
                print("[DEBUG] Deepgram WebSocket connected")
                self._ready.set()
                async for message in ws:
                    self._handle_message(message)
                    if not self._is_waiting_final:
                        continue
        except Exception as e:
            print(f"[DEBUG] Deepgram WebSocket error: {e}")
        finally:
            self._ws = None
            if self._is_waiting_final:
                print("[DEBUG] Delivering on disconnect")
                self._deliver()

    async def _send(self, data: bytes):
        if self._ws:
            try:
                await self._ws.send(data)
            except Exception:
                pass

    async def _flush(self):
        """Send empty frame — Deepgram's signal to finalize."""
        if self._ws:
            try:
                await self._ws.send(b"")
            except Exception:
                self._deliver()

        # Safety timeout: deliver after 3s regardless
        await asyncio.sleep(3.0)
        if self._is_waiting_final:
            self._deliver()

    def _handle_message(self, raw: str):
        try:
            msg = json.loads(raw)
        except Exception:
            return

        transcript = (
            msg.get("channel", {})
               .get("alternatives", [{}])[0]
               .get("transcript", "")
        )
        is_final = msg.get("is_final", False)
        speech_final = msg.get("speech_final", False)

        if is_final and transcript:
            if self._accumulated:
                self._accumulated += " "
            self._accumulated += transcript

        if self._is_waiting_final and is_final and speech_final:
            self._deliver()

    def _deliver(self):
        if not self._is_waiting_final:
            return
        self._is_waiting_final = False
        transcript = self._accumulated
        cb = self._final_callback
        self._final_callback = None
        if cb:
            cb(transcript)

    # ------------------------------------------------------------------ #
    # Model fetching                                                       #
    # ------------------------------------------------------------------ #

    def fetch_models(self, api_key: str, callback: Callable[[List[DeepgramModel]], None]):
        def _fetch():
            try:
                r = httpx.get(
                    "https://api.deepgram.com/v1/models",
                    headers={"Authorization": f"Token {api_key}"},
                    timeout=10,
                )
                root = r.json()
                streaming: dict = {}
                display_names: dict = {}
                language_map: dict = {}

                for m in root.get("stt", []):
                    canonical = m.get("canonical_name", "")
                    if not canonical:
                        continue
                    streaming[canonical] = streaming.get(canonical, False) or m.get("streaming", False)
                    if canonical not in display_names:
                        display_names[canonical] = m.get("name", canonical)
                    existing = language_map.get(canonical, [])
                    for lang in m.get("languages", []):
                        if lang not in existing:
                            existing.append(lang)
                    language_map[canonical] = existing

                models = []
                for canonical, is_streaming in streaming.items():
                    if not is_streaming:
                        continue
                    langs = sorted(language_map.get(canonical, []))
                    if canonical.startswith("nova-2") or canonical.startswith("nova-3"):
                        langs.append("multi")
                    models.append(DeepgramModel(
                        canonical_name=canonical,
                        display_name=display_names.get(canonical, canonical),
                        languages=langs,
                    ))
                models.sort(key=lambda m: m.canonical_name)
                callback(models)
            except Exception:
                callback([])

        threading.Thread(target=_fetch, daemon=True).start()
