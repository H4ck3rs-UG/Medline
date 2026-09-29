"""The med-intake backend's phone callback, driven through FastAPI's test client."""

import importlib
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")
pytest.importorskip("httpx")

from triage import prompts  # noqa: E402
from triage.dtmf import MENU  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1] / "med-intake" / "backend"


@pytest.fixture
def backend(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'tickets.db'}")
    monkeypatch.setenv("AUDIO_BASE_URL", "https://cdn.example/audio")
    monkeypatch.setenv("RECORDED_LANGS", "lg,nyn")
    for var in ("LLM_BASE_URL", "LLM_MODEL"):
        monkeypatch.setenv(var, "")
    monkeypatch.syspath_prepend(str(BACKEND))
    for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[name]
    main = importlib.import_module("app.main")
    from fastapi.testclient import TestClient

    return TestClient(main.app)


def call(client, sid, **form):
    response = client.post("/voice", data={"sessionId": sid, "callerNumber": "+256700000000", **form})
    assert response.status_code == 200
    return response.text


def tickets(client):
    return client.get("/api/tickets").json()


def test_language_menu_plays_shared_clip(backend):
    xml = call(backend, "s1")
    assert '<Play url="https://cdn.example/audio/all/language_menu.mp3"/>' in xml
    assert "<GetDigits" in xml


def test_swahili_caller_hears_swahili(backend):
    call(backend, "s2")
    xml = call(backend, "s2", dtmfDigits="2")
    assert "Tafadhali eleza dalili" in xml and "<Record" in xml
    assert "<Play" not in xml  # Swahili is not in RECORDED_LANGS, so TTS reads it


def test_swahili_keyword_fallback_and_closing(backend, monkeypatch):
    main = sys.modules["app.main"]
    monkeypatch.setattr(main.V, "extract_symptoms", lambda text: {"symptoms": ["cough"], "severe": False})
    call(backend, "s3")
    call(backend, "s3", dtmfDigits="2")
    xml = call(backend, "s3", recordingUrl="https://rec.example/1.wav")
    assert prompts.CANNED["sw"]["closing_urgent"] in xml
    [ticket] = tickets(backend)
    assert ticket["lang"] == "sw" and ticket["tier"] == "urgent"


def test_swahili_keywords_are_extracted():
    sys.path.insert(0, str(BACKEND))
    try:
        voice = importlib.import_module("app.voice")
    finally:
        sys.path.remove(str(BACKEND))
    found = voice.extract_symptoms("mtoto ana homa na kikohozi sana")
    assert {"fever", "cough"} <= set(found["symptoms"]) and found["severe"]


def test_luganda_keypad_menu_plays_recordings_and_runs_rules_engine(backend):
    call(backend, "s4")
    xml = call(backend, "s4", dtmfDigits="3")
    assert "https://cdn.example/audio/lg/welcome.mp3" in xml
    assert f"https://cdn.example/audio/lg/{MENU[0].id}.mp3" in xml

    answers = {"age_group": "3", "fever": "1", "duration": "2", "severity": "1"}
    for question in MENU:
        xml = call(backend, "s4", dtmfDigits=answers.get(question.id, "2"))
    assert "https://cdn.example/audio/lg/closing_urgent.mp3" in xml  # fever for 2 days
    [ticket] = tickets(backend)
    assert ticket["lang"] == "lg" and ticket["tier"] == "urgent" and ticket["symptoms"] == "fever"


def test_keypad_danger_sign_ends_menu_early(backend):
    call(backend, "s5")
    call(backend, "s5", dtmfDigits="4")  # Runyankole
    call(backend, "s5", dtmfDigits="2")  # age: child
    xml = call(backend, "s5", dtmfDigits="1")  # convulsions: yes
    assert "https://cdn.example/audio/nyn/closing_emergency.mp3" in xml
    assert tickets(backend)[0]["tier"] == "emergency"


def test_keypad_invalid_keys_repeat_then_fail_safe(backend):
    call(backend, "s6")
    call(backend, "s6", dtmfDigits="3")
    xml = call(backend, "s6", dtmfDigits="9")
    assert "lg/invalid_key.mp3" in xml and f"lg/{MENU[0].id}.mp3" in xml
    call(backend, "s6", dtmfDigits="9")
    xml = call(backend, "s6", dtmfDigits="9")
    assert "lg/closing_urgent.mp3" in xml  # unfinished menu is never self-care
    assert tickets(backend)[0]["tier"] == "urgent"


def test_nurse_key_transfers_in_callers_language(backend):
    call(backend, "s7")
    call(backend, "s7", dtmfDigits="2")
    xml = call(backend, "s7", dtmfDigits="0")
    assert "Tunakuunganisha na muuguzi" in xml and "<Dial" in xml
