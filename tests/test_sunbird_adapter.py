import io
import json
import urllib.error

import pytest

from triage import FakeLLMClient, TranslatingSession
from triage.adapters import SunbirdClient, SunbirdError


@pytest.fixture
def fake_sunbird(monkeypatch):
    requests, replies = [], []

    def urlopen(request, timeout):
        requests.append((request, timeout))
        reply = replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return io.BytesIO(json.dumps(reply).encode())

    monkeypatch.setattr("urllib.request.urlopen", urlopen)
    monkeypatch.setattr("time.sleep", lambda s: None)
    return requests, replies


def http_error(code, retry_after=None):
    headers = {"Retry-After": retry_after} if retry_after else {}
    return urllib.error.HTTPError("https://api.sunbird.ai/x", code, "err", headers, io.BytesIO(b"busy"))


def test_translate_request_and_codes(fake_sunbird):
    requests, replies = fake_sunbird
    replies.append({"output": {"translated_text": "Oli otya?"}})
    out = SunbirdClient("tok", timeout=7).translate("How are you?", "en", "lg")
    request, timeout = requests[0]
    assert out == "Oli otya?" and timeout == 7
    assert request.full_url == "https://api.sunbird.ai/tasks/translate"
    assert request.get_header("Authorization") == "Bearer tok"
    assert json.loads(request.data) == {"source_language": "eng", "target_language": "lug", "text": "How are you?"}


def test_translate_same_language_makes_no_request(fake_sunbird):
    requests, _ = fake_sunbird
    assert SunbirdClient("tok").translate("Habari", "sw", "sw") == "Habari"
    assert requests == []


def test_transcribe_sends_multipart_with_language(fake_sunbird):
    requests, replies = fake_sunbird
    replies.append({"audio_transcription": " Omwana alina omusujja "})
    text = SunbirdClient("tok").transcribe(b"ID3audio", "lg")
    request, _ = requests[0]
    assert text == "Omwana alina omusujja"
    assert request.full_url.endswith("/tasks/audio/transcriptions")
    assert request.get_header("Content-type").startswith("multipart/form-data; boundary=")
    assert b'name="language"\r\n\r\nlug\r\n' in request.data
    assert b'name="audio"; filename="call.mp3"' in request.data and b"ID3audio" in request.data


def test_speak_uses_default_voice_and_returns_url(fake_sunbird):
    requests, replies = fake_sunbird
    replies.append({"audio_url": "https://storage.example/a.wav", "audio_url_expires_at": "2026-01-01T00:00:00Z"})
    data = SunbirdClient("tok", voices={"nyn": "waxal_nyn_0003"}).speak("Oraire ota?", "nyn")
    body = json.loads(requests[0][0].data)
    assert data["audio_url"] == "https://storage.example/a.wav"
    assert body == {"text": "Oraire ota?", "language": "nyn", "voice": "waxal_nyn_0003", "response_mode": "url"}


def test_busy_service_is_retried_once_then_raised(fake_sunbird):
    requests, replies = fake_sunbird
    replies += [http_error(503, "30"), {"output": {"translated_text": "ok"}}]
    assert SunbirdClient("tok").translate("x", "en", "lg") == "ok"
    replies += [http_error(503), http_error(503)]
    with pytest.raises(SunbirdError) as err:
        SunbirdClient("tok").translate("x", "en", "lg")
    assert err.value.status == 503


def test_client_errors_are_not_retried(fake_sunbird):
    requests, replies = fake_sunbird
    replies.append(http_error(401))
    with pytest.raises(SunbirdError):
        SunbirdClient("tok").translate("x", "en", "lg")
    assert len(requests) == 1


def test_backs_a_translating_session(fake_sunbird):
    _, replies = fake_sunbird
    replies += [
        {"output": {"translated_text": "the child has a cough"}},
        {"output": {"translated_text": "Omwana amaze ennaku mmeka?"}},
    ]
    llm = FakeLLMClient([{"reply": "How many days has the child been sick?", "on_topic": True, "symptoms": ["cough"]}])
    session = TranslatingSession(llm, SunbirdClient("tok"), "lg")
    result = session.handle_utterance("omwana alina ekifuba")
    assert result.reply_text == "Omwana amaze ennaku mmeka?"
    assert "the child has a cough" in llm.calls[0][1][-1]["content"]


def test_token_required():
    with pytest.raises(ValueError):
        SunbirdClient("")
