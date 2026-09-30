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


def choose_language(client, sid, key, sex="1", age="3"):
    """Language menu, then the sex and age questions every caller answers first."""
    call(client, sid)
    call(client, sid, dtmfDigits=key)
    call(client, sid, dtmfDigits=sex)
    return call(client, sid, dtmfDigits=age)


def test_swahili_caller_hears_swahili(backend):
    call(backend, "s2")
    xml = call(backend, "s2", dtmfDigits="2")
    assert "Mgonjwa ni wa jinsia gani" in xml and "<GetDigits" in xml
    xml = call(backend, "s2", dtmfDigits="2")
    assert "Nani anaumwa" in xml  # the keypad menu's age question, in Swahili
    xml = call(backend, "s2", dtmfDigits="3")
    assert "Tafadhali eleza dalili" in xml and "<Record" in xml
    assert "<Play" not in xml  # Swahili is not in RECORDED_LANGS, so TTS reads it


def test_swahili_keyword_fallback_and_closing(backend, monkeypatch):
    main = sys.modules["app.main"]
    monkeypatch.setattr(main.V, "extract_symptoms", lambda text: {"symptoms": ["cough"], "severe": False})
    choose_language(backend, "s3", "2", sex="2", age="3")
    xml = call(backend, "s3", recordingUrl="https://rec.example/1.wav")
    assert prompts.CANNED["sw"]["closing_urgent"] in xml
    [ticket] = tickets(backend)
    assert ticket["lang"] == "sw" and ticket["tier"] == "urgent"
    assert ticket["sex"] == "F" and ticket["age_group"] == "adult"
    assert ticket["summary"].startswith("URGENT: F adult sw")


def test_swahili_keywords_are_extracted():
    sys.path.insert(0, str(BACKEND))
    try:
        voice = importlib.import_module("app.voice")
    finally:
        sys.path.remove(str(BACKEND))
    found = voice.extract_symptoms("mtoto ana homa na kikohozi sana")
    assert {"fever", "cough"} <= set(found["symptoms"]) and found["severe"]


def test_spoken_sex_and_age_answers(backend):
    voice = sys.modules["app.main"].V
    for text, sex in [("ni mwanamke", "F"), ("mwanaume", "M"), ("a woman", "F"), ("my boy", "M")]:
        s, _, _ = voice.start("+256700000000")
        voice.turn(s, digits="2")
        voice.turn(s, text=text)
        assert s["sex"] == sex, text
    voice.turn(s, text="he is 70 years old")
    assert s["age"] == 70 and s["age_group"] == "elderly"


def test_bio_questions_play_recorded_clips(backend):
    call(backend, "s8")
    assert "https://cdn.example/audio/lg/bio_sex.mp3" in call(backend, "s8", dtmfDigits="3")
    assert "https://cdn.example/audio/lg/age_group.mp3" in call(backend, "s8", dtmfDigits="1")


def test_invalid_bio_key_reprompts_with_keypad_not_recording(backend):
    call(backend, "s9")
    call(backend, "s9", dtmfDigits="1")
    xml = call(backend, "s9", dtmfDigits="7")
    assert "Sorry, that key is not an option" in xml and "<GetDigits" in xml and "<Record" not in xml


def test_luganda_keypad_menu_asks_age_once_and_runs_rules_engine(backend):
    xml = choose_language(backend, "s4", "3", sex="1", age="3")
    assert "https://cdn.example/audio/lg/welcome.mp3" in xml
    assert "https://cdn.example/audio/lg/convulsions.mp3" in xml  # age_group already answered

    answers = {"fever": "1", "duration": "2", "severity": "1"}
    for question in MENU[1:]:
        xml = call(backend, "s4", dtmfDigits=answers.get(question.id, "2"))
    assert "https://cdn.example/audio/lg/closing_urgent.mp3" in xml  # fever for 2 days
    [ticket] = tickets(backend)
    assert ticket["lang"] == "lg" and ticket["tier"] == "urgent" and ticket["symptoms"] == "fever"
    assert backend.get("/api/stats").json()["by_age_band"] == {"adult": 1}


def test_keypad_danger_sign_ends_menu_early(backend):
    choose_language(backend, "s5", "4", age="2")  # Runyankole, child
    xml = call(backend, "s5", dtmfDigits="1")  # convulsions: yes
    assert "https://cdn.example/audio/nyn/closing_emergency.mp3" in xml
    assert tickets(backend)[0]["tier"] == "emergency"


def test_keypad_invalid_keys_repeat_then_fail_safe(backend):
    choose_language(backend, "s6", "3")
    xml = call(backend, "s6", dtmfDigits="9")
    assert "lg/invalid_key.mp3" in xml and "lg/convulsions.mp3" in xml
    call(backend, "s6", dtmfDigits="9")
    xml = call(backend, "s6", dtmfDigits="9")
    assert "lg/closing_urgent.mp3" in xml  # unfinished menu is never self-care
    assert tickets(backend)[0]["tier"] == "urgent"


def test_nurse_key_transfers_in_callers_language(backend):
    call(backend, "s7")
    call(backend, "s7", dtmfDigits="2")
    xml = call(backend, "s7", dtmfDigits="0")  # during the bio questions
    assert "Tunakuunganisha na muuguzi" in xml and "<Dial" in xml


def test_bio_sex_clip_is_in_every_recording_script():
    from triage.dtmf import recording_script

    for language in ("lg", "nyn"):
        assert f"{language}/bio_sex.mp3" in {row["audio_file"] for row in recording_script(language)}
    assert not any(row["needs_translation"] for row in recording_script("sw"))
