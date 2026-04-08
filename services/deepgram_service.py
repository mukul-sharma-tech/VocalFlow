"""
Handles the Deepgram WebSocket connection for real-time speech-to-text.

How it works:
  1. connect() opens a WebSocket in a background thread
  2. send_audio() streams raw PCM chunks as they come from the mic
  3. close_stream() sends an empty frame (Deepgram's flush signal) and waits
     for the final transcript to come back via callback
"""
import asyncio
import json
import threading
from dataclasses import dataclass
from typing import Callable, List, Optional

import httpx
import websockets


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
        self._accumulated: str = ""          # builds up final transcript pieces
        self._is_waiting_final = False       # True after close_stream() is called
        self._final_callback: Optional[Callable[[str], None]] = None
        self._ready = threading.Event()      # set when WebSocket handshake completes

    def connect(self, api_key: str, model: str, language: str):
        """Open a WebSocket to Deepgram. Runs the async loop in a background thread."""
        self._accumulated = ""
        self._is_waiting_final = False
        self._final_callback = None
        self._ready.clear()
        self._api_key = api_key
        self._model = model
        self._language = language

        self._loop = asyncio.new_event_loop()
        self._loop.set_exception_handler(lambda loop, ctx: None)  # suppress cleanup warnings
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def wait_until_ready(self, timeout: float = 5.0) -> bool:
        """Block the calling thread until the WebSocket is connected (or timeout)."""
        return self._ready.wait(timeout=timeout)

    def send_audio(self, pcm_bytes: bytes):
        """Forward a PCM chunk to Deepgram. Safe to call from any thread."""
        if self._loop and not self._loop.is_closed() and self._ws:
            asyncio.run_coroutine_threadsafe(self._send(pcm_bytes), self._loop)

    def close_stream(self, callback: Callable[[str], None]):
        """Signal end of audio. Deepgram will flush and return the final transcript."""
        self._final_callback = callback
        self._is_waiting_final = True
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self._flush(), self._loop)

    def fetch_balance(self, api_key: str, callback: Callable[[str], None]):
        """Fetch remaining Deepgram credit balance."""
        def _fetch():
            try:
                # Get project ID first
                r = httpx.get(
                    "https://api.deepgram.com/v1/projects",
                    headers={"Authorization": f"Token {api_key}"},
                    timeout=10,
                )
                projects = r.json().get("projects", [])
                if not projects:
                    callback("No project found")
                    return
                project_id = projects[0]["project_id"]

                # Get balance for that project
                r2 = httpx.get(
                    f"https://api.deepgram.com/v1/projects/{project_id}/balances",
                    headers={"Authorization": f"Token {api_key}"},
                    timeout=10,
                )
                balances = r2.json().get("balances", [])
                if balances:
                    amount = balances[0].get("amount", 0)
                    units  = balances[0].get("units", "")
                    callback(f"${amount:.4f} {units}".strip())
                else:
                    callback("No balance info")
            except Exception as e:
                callback(f"Error: {e}")

        threading.Thread(target=_fetch, daemon=True).start()

    def fetch_models(self, api_key: str, callback: Callable[[List[DeepgramModel]], None]):
        """Fetch available streaming models from the Deepgram API."""
        def _fetch():
            try:
                r = httpx.get(
                    "https://api.deepgram.com/v1/models",
                    headers={"Authorization": f"Token {api_key}"},
                    timeout=10,
                )
                streaming, display_names, language_map = {}, {}, {}

                for m in r.json().get("stt", []):
                    canonical = m.get("canonical_name", "")
                    if not canonical:
                        continue
                    streaming[canonical] = streaming.get(canonical, False) or m.get("streaming", False)
                    display_names.setdefault(canonical, m.get("name", canonical))
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
                    # nova-2 and nova-3 support multilingual but the API doesn't list it
                    if canonical.startswith(("nova-2", "nova-3")):
                        langs.append("multi")
                    models.append(DeepgramModel(
                        canonical_name=canonical,
                        display_name=display_names.get(canonical, canonical),
                        languages=langs,
                    ))
                callback(sorted(models, key=lambda m: m.canonical_name))
            except Exception:
                callback([])

        threading.Thread(target=_fetch, daemon=True).start()

    # -- async internals --

    def _run_loop(self):
        self._loop.run_until_complete(self._connect_and_receive())

    async def _connect_and_receive(self):
        url = (
            f"wss://api.deepgram.com/v1/listen"
            f"?encoding=linear16&sample_rate=16000&channels=1"
            f"&model={self._model}&language={self._language}"
            f"&punctuate=true&interim_results=true"
        )
        try:
            async with websockets.connect(
                url, extra_headers={"Authorization": f"Token {self._api_key}"}
            ) as ws:
                self._ws = ws
                self._ready.set()  # unblock wait_until_ready()
                async for message in ws:
                    self._handle_message(message)
        except Exception:
            pass
        finally:
            self._ws = None
            if self._is_waiting_final:
                self._deliver()

    async def _send(self, data: bytes):
        if self._ws:
            try:
                await self._ws.send(data)
            except Exception:
                pass

    async def _flush(self):
        """Send an empty binary frame — Deepgram's signal to finalize the transcript."""
        if self._ws:
            try:
                await self._ws.send(b"")
            except Exception:
                self._deliver()
        # Safety net: if Deepgram doesn't respond in 3s, deliver what we have
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
        is_final    = msg.get("is_final", False)
        speech_final = msg.get("speech_final", False)

        # Only accumulate is_final=True results — interim results are just previews
        if is_final and transcript.strip():
            self._accumulated += (" " if self._accumulated else "") + transcript

        # speech_final=True means Deepgram received our flush signal and is done
        if self._is_waiting_final and is_final and speech_final:
            self._deliver()

    def _deliver(self):
        """Hand the accumulated transcript to the callback and reset state."""
        if not self._is_waiting_final:
            return
        self._is_waiting_final = False
        cb, self._final_callback = self._final_callback, None
        if cb:
            cb(self._accumulated)
