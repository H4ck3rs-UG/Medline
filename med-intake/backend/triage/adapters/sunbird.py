"""Client for the Sunbird AI API (https://docs.sunbird.ai): speech-to-text,
text-to-speech and translation for Ugandan and other African languages.

Standard library only. The app uses short language codes ("lg", "sw"); Sunbird
wants ISO 639-3 ("lug", "swa"), so ``CODES`` maps between them. The client also
satisfies ``triage.translation.Translator``, so it can back a ``TranslatingSession``.

Calls are made while a caller waits on the phone, so retries are few and short:
a 429/5xx is retried once after at most ``max_retry_wait`` seconds, then raised.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
import uuid

BASE_URL = "https://api.sunbird.ai"

# App language code -> Sunbird ISO 639-3 code.
CODES = {"en": "eng", "sw": "swa", "lg": "lug", "nyn": "nyn"}

# Default text-to-speech speaker per language (GET /tasks/voice/speakers lists them all).
# Audition these before a demo; quality varies by speaker.
VOICES = {
    "eng": "salt_eng_0001",
    "swa": "waxal_swa_0006",
    "lug": "salt_lug_0001",
    "nyn": "salt_nyn_0001",
}

_RETRY_STATUS = {429, 502, 503, 504}


class SunbirdError(RuntimeError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def code(language: str) -> str:
    """Sunbird code for an app language code (unknown codes pass through)."""
    return CODES.get(language, language)


class SunbirdClient:
    def __init__(
        self,
        token: str,
        *,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        retries: int = 1,
        max_retry_wait: float = 2.0,
        voices: dict[str, str] | None = None,
    ):
        if not token:
            raise ValueError("a Sunbird API token is required")
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.max_retry_wait = max_retry_wait
        self.voices = {**VOICES, **(voices or {})}

    # --- endpoints -----------------------------------------------------------

    def transcribe(
        self,
        audio: bytes,
        language: str,
        *,
        filename: str = "call.mp3",
        content_type: str = "audio/mpeg",
        timeout: float | None = None,
        retries: int | None = None,
    ) -> str:
        """POST /tasks/audio/transcriptions. ``language`` is required by Sunbird.
        Usually 4-5 s, but it has taken 30+ s, so pass a short ``timeout`` on a live call."""
        body, ctype = _multipart(
            {"language": code(language)}, {"audio": (filename, audio, content_type)}
        )
        data = self._request("/tasks/audio/transcriptions", body, ctype, timeout, retries)
        return (data.get("audio_transcription") or "").strip()

    def speak(
        self,
        text: str,
        language: str,
        *,
        voice: str | None = None,
        timeout: float | None = None,
        retries: int | None = None,
    ) -> dict:
        """POST /tasks/audio/speech. Returns the response: ``audio_url`` is a signed
        WAV link valid for about 30 minutes (``audio_url_expires_at``). Synthesis can
        take 10+ seconds, so pass a short ``timeout`` while a caller is waiting."""
        lang = code(language)
        payload = {
            "text": text,
            "language": lang,
            "voice": voice or self.voices.get(lang),
            "response_mode": "url",
        }
        data = self._request(
            "/tasks/audio/speech", json.dumps(payload).encode(), "application/json", timeout, retries
        )
        if not data.get("audio_url"):
            raise SunbirdError("text-to-speech returned no audio_url")
        return data

    def translate(self, text: str, source: str, target: str) -> str:
        """POST /tasks/translate (sunflower-9b). Satisfies ``Translator``."""
        if source == target or not text.strip():
            return text
        payload = {"source_language": code(source), "target_language": code(target), "text": text}
        data = self._request("/tasks/translate", json.dumps(payload).encode(), "application/json")
        translated = ((data.get("output") or {}).get("translated_text") or "").strip()
        if not translated:
            raise SunbirdError("translation returned no text")
        return translated

    def download(self, url: str) -> bytes:
        """Fetch a signed audio URL returned by ``speak``."""
        with urllib.request.urlopen(url, timeout=self.timeout) as response:
            return response.read()

    # --- transport -----------------------------------------------------------

    def _request(
        self,
        path: str,
        body: bytes,
        content_type: str,
        timeout: float | None = None,
        retries: int | None = None,
    ) -> dict:
        timeout = self.timeout if timeout is None else timeout
        retries = self.retries if retries is None else retries
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": content_type,
            "Accept": "application/json",
        }
        for attempt in range(retries + 1):
            request = urllib.request.Request(
                self.base_url + path, data=body, headers=headers, method="POST"
            )
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    return json.loads(response.read().decode())
            except urllib.error.HTTPError as exc:
                detail = exc.read()[:300].decode(errors="replace")
                if exc.code in _RETRY_STATUS and attempt < retries:
                    time.sleep(_retry_after(exc, self.max_retry_wait))
                    continue
                raise SunbirdError(f"{path} failed with HTTP {exc.code}: {detail}", exc.code) from None
        raise SunbirdError(f"{path} failed")  # unreachable


def _retry_after(exc: urllib.error.HTTPError, cap: float) -> float:
    try:
        return min(float(exc.headers.get("Retry-After", 1)), cap)
    except (TypeError, ValueError):
        return min(1.0, cap)


def _multipart(fields: dict[str, str], files: dict[str, tuple[str, bytes, str]]) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    for name, (filename, content, ctype) in files.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
            f"Content-Type: {ctype}\r\n\r\n".encode()
            + content
            + b"\r\n"
        )
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"
