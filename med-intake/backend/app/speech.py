"""Sunbird AI on the phone line: transcribe caller audio, translate, and turn
prompts into audio Africa's Talking can <Play>.

Everything here is optional. Without SUNBIRD_API_TOKEN each function returns
None (or the text unchanged) and the voice layer falls back to <Say> and the
keypad menu.

Sunbird text-to-speech takes several seconds per clip, so clips are cached:
- with PUBLIC_URL set, each clip is saved once under TTS_CACHE_DIR and served
  from /tts/<lang>/<id>.wav by this backend, so it is instant on later calls;
- otherwise the signed Sunbird URL is played directly and reused until it expires.
Machine translations are cached in TTS_CACHE_DIR/translations.json, which is
also the draft script for native speakers to review.
"""
import hashlib, json, os, threading, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from triage import dtmf, prompts
from triage.adapters.sunbird import SunbirdClient, code
from .config import (SUNBIRD_API_TOKEN, SUNBIRD_BASE_URL, SUNBIRD_TIMEOUT, SUNBIRD_LIVE_TTS_TIMEOUT,
    SUNBIRD_VOICES, TTS_CACHE_DIR, PUBLIC_URL)

_client: SunbirdClient|None = None
_lock = threading.Lock()
_translations: dict[str,str]|None = None
_signed: dict[str,tuple[str,float]] = {}  # clip id -> (signed url, expiry epoch)
_failed: dict[str,float] = {}  # clip id -> when live synthesis last failed
FAILED_RETRY_AFTER = 300  # seconds before a live call tries a failed clip again
_saver = ThreadPoolExecutor(max_workers=2)

def enabled() -> bool:
    return bool(SUNBIRD_API_TOKEN)

def client() -> SunbirdClient|None:
    global _client
    if _client is None and enabled():
        _client = SunbirdClient(SUNBIRD_API_TOKEN, base_url=SUNBIRD_BASE_URL, timeout=SUNBIRD_TIMEOUT, voices=SUNBIRD_VOICES)
    return _client

# --- speech-to-text ---------------------------------------------------------

def transcribe(raw: bytes, lang: str) -> str|None:
    c = client()
    if not c: return None
    try:
        text = c.transcribe(raw, lang)
        print(f"stt sunbird ok lang={lang} chars={len(text)}")
        return text or None
    except Exception as e:
        print("stt sunbird fail:", type(e).__name__, str(e)[:200])
        return None

# --- translation ------------------------------------------------------------

def _translations_path() -> str:
    return os.path.join(TTS_CACHE_DIR, "translations.json")

def _load_translations() -> dict[str,str]:
    global _translations
    if _translations is None:
        try:
            with open(_translations_path(), encoding="utf-8") as f: _translations = json.load(f)
        except Exception: _translations = {}
    return _translations

def translate(text: str, source: str, target: str) -> str|None:
    """Machine translation, cached. None when Sunbird is off or the call fails."""
    if source == target or not text.strip(): return text
    key = f"{source}>{target}|{text}"
    with _lock:
        hit = _load_translations().get(key)
    if hit: return hit
    c = client()
    if not c: return None
    try:
        out = c.translate(text, source, target)
    except Exception as e:
        print("translate sunbird fail:", type(e).__name__, str(e)[:200])
        return None
    with _lock:
        cache = _load_translations(); cache[key] = out
        os.makedirs(TTS_CACHE_DIR, exist_ok=True)
        tmp = _translations_path() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f: json.dump(cache, f, ensure_ascii=False, indent=1)
        os.replace(tmp, _translations_path())
    return out

# Every English script line (keypad menu, system prompts, canned lines). A line in
# this set spoken to a caller in another language has no written translation yet.
_ENGLISH_SCRIPT = ({row["english"] for row in dtmf.recording_script("en")}
    | set(prompts.CANNED["en"].values()))

def in_caller_language(text: str, lang: str) -> str:
    """The line in the caller's language: written scripts are used as they are;
    an English fallback is machine-translated when Sunbird is on."""
    if lang == "en" or text not in _ENGLISH_SCRIPT: return text
    return translate(text, "en", lang) or text

# --- text-to-speech ---------------------------------------------------------

def _clip_id(text: str, lang: str) -> str:
    c = client(); voice = c.voices.get(code(lang), "") if c else ""
    return hashlib.sha1(f"{code(lang)}|{voice}|{text}".encode()).hexdigest()[:24]

def clip_file(lang: str, clip_id: str) -> str:
    return os.path.join(TTS_CACHE_DIR, lang, f"{clip_id}.wav")

def _public(lang: str, clip_id: str) -> str:
    return f"{PUBLIC_URL}/tts/{lang}/{clip_id}.wav"

def _save(url: str, path: str) -> bool:
    try:
        wav = client().download(url)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "wb") as f: f.write(wav)
        os.replace(tmp, path)
        return True
    except Exception as e:
        print("tts save fail:", type(e).__name__, str(e)[:200])
        return False

def _expiry(value) -> float:
    try: return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception: return time.time() + 25 * 60

def tts_url(text: str, lang: str, *, live: bool = True, wait_for_save: bool = False) -> str|None:
    """A playable URL for ``text`` spoken in ``lang``, or None (caller falls back to <Say>).
    ``live`` (a caller is waiting): short timeout, no retry, and a clip that just
    failed is skipped for a few minutes. Warm-up passes live=False."""
    c = client()
    if not c or not text.strip(): return None
    clip_id = _clip_id(text, lang); path = clip_file(lang, clip_id)
    if PUBLIC_URL and os.path.exists(path): return _public(lang, clip_id)
    hit = _signed.get(clip_id)
    if hit and hit[1] - time.time() > 120: return hit[0]
    if live and time.time() - _failed.get(clip_id, 0) < FAILED_RETRY_AFTER: return None
    try:
        data = c.speak(text, lang, timeout=SUNBIRD_LIVE_TTS_TIMEOUT, retries=0) if live else c.speak(text, lang)
    except Exception as e:
        _failed[clip_id] = time.time()
        print("tts sunbird fail:", type(e).__name__, str(e)[:200])
        return None
    _failed.pop(clip_id, None)
    url = data["audio_url"]
    _signed[clip_id] = (url, _expiry(data.get("audio_url_expires_at")))
    if PUBLIC_URL:  # keep a permanent copy; this call still plays the signed URL
        if wait_for_save:
            if _save(url, path): return _public(lang, clip_id)
        else: _saver.submit(_save, url, path)
    return url

def warm(langs: list[str]) -> dict:
    """Pre-generate every fixed prompt (see triage.dtmf.recording_script) so live
    calls don't wait on text-to-speech. Also fills the translation cache."""
    report = {}
    for lang in langs:
        texts = [in_caller_language(row["text"], lang) for row in dtmf.recording_script(lang)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            urls = list(pool.map(lambda t: tts_url(t, lang, live=False, wait_for_save=True), texts))
        report[lang] = {"clips": len(texts), "failed": sum(u is None for u in urls),
            "machine_translated": {row["english"]: t for row, t in zip(dtmf.recording_script(lang), texts)
                if row["needs_translation"] and t != row["english"]}}
    return report
