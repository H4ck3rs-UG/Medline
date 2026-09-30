"""The med-intake backend's phone callback, driven through FastAPI's test client.

The backend's .env is never loaded here and every provider key is blanked, so
tests send no SMS and make no network calls. Sunbird is replaced by a fake.
"""

import importlib
import sys
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")
pytest.importorskip("httpx")

from triage import prompts  # noqa: E402
from triage.dtmf import FOLLOW_UP_QUESTIONS, recording_script  # noqa: E402
from triage.followup.bank import BY_SYMPTOM, DANGER_SIGNS  # noqa: E402

BACKEND = Path(__file__).resolve().parents[1] / "med-intake" / "backend"
PROVIDER_KEYS = ("AT_API_KEY", "ELEVENLABS_API_KEY", "GROQ_API_KEY", "WISPRFLOW_API_KEY",
                 "SUNBIRD_API_TOKEN", "LLM_BASE_URL", "LLM_MODEL", "PUBLIC_URL")


def load_backend(tmp_path, monkeypatch, **env):
    monkeypatch.setenv("MED_INTAKE_SKIP_DOTENV", "1")
    for var in PROVIDER_KEYS:
        monkeypatch.setenv(var, "")
    monkeypatch.setenv("DB_URL", f"sqlite:///{tmp_path / 'tickets.db'}")
    monkeypatch.setenv("TTS_CACHE_DIR", str(tmp_path / "tts_cache"))
    monkeypatch.setenv("AUDIO_BASE_URL", "https://cdn.example/audio")
    monkeypatch.setenv("RECORDED_LANGS", "lg,nyn")
    for var, value in env.items():
        monkeypatch.setenv(var, value)
    monkeypatch.syspath_prepend(str(BACKEND))
    for name in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[name]
    main = importlib.import_module("app.main")
    from fastapi.testclient import TestClient

    return TestClient(main.app), main


@pytest.fixture
def backend(tmp_path, monkeypatch):
    client, _ = load_backend(tmp_path, monkeypatch)
    return client


class FakeSunbird:
    """Stands in for triage.adapters.SunbirdClient."""

    voices = {"lug": "salt_lug_0001", "swa": "waxal_swa_0006", "nyn": "salt_nyn_0001"}

    def __init__(self):
        self.heard = {}  # language -> transcript to return
        self.spoken = []  # (text, language)
        self.translated = []  # (text, source, target)
        self.fail_translation = False

    def transcribe(self, audio, language, **kwargs):
        self.stt_kwargs = kwargs
        return self.heard.get(language, "")

    def translate(self, text, source, target):
        self.translated.append((text, source, target))
        if self.fail_translation:
            raise RuntimeError("translation down")
        return {"omwana alina omusujja": "the child has a fever"}.get(text, f"[{target}] {text}")

    def speak(self, text, language, **_):
        self.spoken.append((text, language))
        n = len(self.spoken)
        return {"audio_url": f"https://sb.example/{language}/{n}.wav", "audio_url_expires_at": "2999-01-01T00:00:00Z"}

    def download(self, url):
        return b"RIFF-fake-wav"


@pytest.fixture
def sunbird(tmp_path, monkeypatch):
    """Backend with Sunbird on (fake client) and recordings downloadable."""
    client, main = load_backend(tmp_path, monkeypatch, SUNBIRD_API_TOKEN="test-token")
    fake = FakeSunbird()
    monkeypatch.setattr(main.speech, "_client", fake)

    class Download:
        content = b"ID3-fake-mp3"

        def raise_for_status(self):
            pass

    monkeypatch.setattr("requests.get", lambda url, timeout=None: Download())
    return client, fake


def call(client, sid, **form):
    response = client.post("/voice", data={"sessionId": sid, "callerNumber": "+256700000000", **form})
    assert response.status_code == 200
    return response.text


def tickets(client):
    return client.get("/api/tickets").json()


DANGER_IDS = [BY_SYMPTOM[s].id for s in DANGER_SIGNS]


def answer_questions(client, sid, yes=(), keys=None, limit=30):
    """Answer the interview until the call ends: "1" for question ids in ``yes``,
    ``keys`` for the others (duration/severity/pregnant defaults), else "2" (no).
    Returns the last response and the question ids in the order asked."""
    voice = sys.modules["app.main"].V
    keys = {"duration": "2", "severity": "1", "pregnant": "2", **(keys or {})}
    asked = []
    for _ in range(limit):
        qid = voice.get(sid)["q"]
        asked.append(qid)
        xml = call(client, sid, dtmfDigits="1" if qid in yes else keys.get(qid, "2"))
        if "<GetDigits" not in xml:
            return xml, asked
    raise AssertionError(f"call didn't end: {asked}")


def choose_language(client, sid, key, sex="1", age="3"):
    """Language menu, new visit, then the sex and age questions every new caller answers."""
    call(client, sid)
    call(client, sid, dtmfDigits=key)
    call(client, sid, dtmfDigits="1")  # new visit
    call(client, sid, dtmfDigits=sex)
    return call(client, sid, dtmfDigits=age)


# --- language menu, visit type, bio questions ----------------------------------


def test_language_menu_plays_shared_clip(backend):
    xml = call(backend, "s1")
    assert '<Play url="https://cdn.example/audio/all/language_menu.mp3"/>' in xml
    assert "<GetDigits" in xml


def test_swahili_caller_hears_swahili(backend):
    call(backend, "s2")
    xml = call(backend, "s2", dtmfDigits="2")
    assert "Kwa ziara mpya, bonyeza 1" in xml
    xml = call(backend, "s2", dtmfDigits="1")
    assert "Mgonjwa ni wa jinsia gani" in xml and "<GetDigits" in xml
    xml = call(backend, "s2", dtmfDigits="2")
    assert "Nani anaumwa" in xml  # the keypad menu's age question, in Swahili
    xml = call(backend, "s2", dtmfDigits="3")
    assert "Tafadhali eleza dalili" in xml and "<Record" in xml
    assert "<Play" not in xml  # Sunbird is off and Swahili isn't recorded, so <Say> reads it


def test_bio_questions_play_recorded_clips(backend):
    call(backend, "s8")
    assert "https://cdn.example/audio/lg/visit_type.mp3" in call(backend, "s8", dtmfDigits="3")
    assert "https://cdn.example/audio/lg/bio_sex.mp3" in call(backend, "s8", dtmfDigits="1")
    assert "https://cdn.example/audio/lg/age_group.mp3" in call(backend, "s8", dtmfDigits="1")


def test_invalid_bio_key_reprompts_with_keypad_not_recording(backend):
    call(backend, "s9")
    call(backend, "s9", dtmfDigits="1")
    call(backend, "s9", dtmfDigits="1")
    xml = call(backend, "s9", dtmfDigits="7")
    assert "Sorry, that key is not an option" in xml and "<GetDigits" in xml and "<Record" not in xml


def test_spoken_sex_and_age_answers(backend):
    voice = sys.modules["app.main"].V
    for text, sex in [("ni mwanamke", "F"), ("mwanaume", "M"), ("a woman", "F"), ("my boy", "M")]:
        s, _, _ = voice.start("+256700000000")
        voice.turn(s, digits="2")
        voice.turn(s, digits="1")
        voice.turn(s, text=text)
        assert s["sex"] == sex, text
    voice.turn(s, text="he is 70 years old")
    assert s["age"] == 70 and s["age_band"] == "elderly"


def test_nurse_key_transfers_in_callers_language(backend):
    call(backend, "s7")
    call(backend, "s7", dtmfDigits="2")
    xml = call(backend, "s7", dtmfDigits="0")  # at the visit-type question
    assert "Tunakuunganisha na muuguzi" in xml and "<Dial" in xml


# --- speech path (no Sunbird) -------------------------------------------------------


def test_swahili_speech_then_keypad_questions_then_rules_engine(backend, monkeypatch):
    main = sys.modules["app.main"]
    monkeypatch.setattr(main, "_transcribe", lambda url, lang: "mtoto ana kikohozi")
    choose_language(backend, "s3", "2", sex="2", age="3")
    xml = call(backend, "s3", recordingUrl="https://rec.example/1.mp3")
    assert "Je, mgonjwa ana degedege au kifafa?" in xml and "<GetDigits" in xml  # danger signs next
    xml, asked = answer_questions(backend, "s3", keys={"duration": "4"})  # 1-2 weeks
    n = len(DANGER_IDS)
    assert asked[:n] == DANGER_IDS and asked[n:n + 3] == ["duration", "pregnant", "severity"]
    assert len(asked) <= n + 3 + 2  # danger signs + facts + at most 2 follow-ups (no emergency checks for a cough)
    assert prompts.CANNED["sw"]["closing_urgent"] in xml  # cough for 14 days -> rules: urgent
    assert "Namba yako ya kumbukumbu ni</Say>" in xml and ">M E D, 1.</Say>" in xml
    [ticket] = tickets(backend)
    assert ticket["lang"] == "sw" and ticket["tier"] == "urgent" and ticket["reference"] == "MED-1"
    assert ticket["sex"] == "F" and ticket["age_band"] == "adult" and ticket["symptoms"] == "cough"
    assert ticket["summary"].startswith("URGENT: F adult sw")
    assert "UR_LONG_DURATION" in ticket["transcript"]  # the rule ids that fired are logged


def test_spoken_danger_sign_skips_the_questions(backend, monkeypatch):
    main = sys.modules["app.main"]
    monkeypatch.setattr(main, "_transcribe", lambda url, lang: "he had a fit and now he is not breathing")
    choose_language(backend, "s11", "1")
    xml = call(backend, "s11", recordingUrl="https://rec.example/1.mp3")
    assert "<GetDigits" not in xml and prompts.CANNED["en"]["closing_emergency"] in xml
    assert tickets(backend)[0]["tier"] == "emergency"


def test_fever_gets_the_stiff_neck_question(backend, monkeypatch):
    main = sys.modules["app.main"]
    monkeypatch.setattr(main, "_transcribe", lambda url, lang: "she has a high fever")
    choose_language(backend, "s12", "1", sex="2", age="2")  # girl
    call(backend, "s12", recordingUrl="https://rec.example/1.mp3")
    xml, asked = answer_questions(backend, "s12", yes={"fu_stiff_neck"}, keys={"duration": "1"})
    assert "pregnant" not in asked  # a child
    assert asked[asked.index("severity") + 1] == "fu_stiff_neck"  # emergency check: fever + stiff neck
    assert "fu_bleeding_in_pregnancy" not in asked  # never for a child
    assert tickets(backend)[0]["tier"] == "emergency"


def test_symptoms_are_extracted_in_english_and_swahili():
    sys.path.insert(0, str(BACKEND))
    try:
        voice = importlib.import_module("app.voice")
    finally:
        sys.path.remove(str(BACKEND))
    codes = lambda text: {c.value for c in voice.extract_codes(text)}  # noqa: E731
    assert codes("mtoto ana homa na kikohozi sana") == {"fever", "cough"}
    assert codes("hana homa lakini anatapika") == {"vomiting"}  # "hana homa": no fever
    assert codes("My son has a cough, no rash, and is vomiting everything") >= {"cough", "vomiting_everything"}
    assert "rash" not in codes("My son has a cough, no rash")


def test_unheard_speech_twice_falls_back_to_keypad_not_self_care(backend, monkeypatch):
    main = sys.modules["app.main"]
    monkeypatch.setattr(main, "_transcribe", lambda url, lang: None)
    choose_language(backend, "s10", "1", age="2")
    xml = call(backend, "s10", recordingUrl="https://rec.example/1.mp3")
    assert "could not hear you clearly" in xml and "<Record" in xml
    xml = call(backend, "s10", recordingUrl="https://rec.example/2.mp3")
    assert "answer the next questions with your keypad" in xml and "<GetDigits" in xml
    assert "fits or convulsions" in xml  # age already answered, so the danger signs come next
    xml = call(backend, "s10", dtmfDigits="1")  # convulsions: yes
    assert tickets(backend)[0]["tier"] == "emergency"


def test_speech_provider_order():
    sys.path.insert(0, str(BACKEND))
    try:
        main = importlib.import_module("app.main")
    finally:
        sys.path.remove(str(BACKEND))
    names = lambda lang: [f.__name__.removeprefix("_transcribe_") for f in main._stt_chain(lang)]
    assert names("lg") == names("nyn") == ["sunbird"]  # others don't support these languages
    assert names("sw")[0] == "sunbird"
    assert names("en")[:2] == ["eleven", "sunbird"]


# --- keypad path ------------------------------------------------------------------


def test_luganda_keypad_interview_runs_rules_engine(backend):
    xml = choose_language(backend, "s4", "3", sex="1", age="3")
    assert "https://cdn.example/audio/lg/welcome.mp3" in xml
    assert "https://cdn.example/audio/lg/convulsions.mp3" in xml  # age already answered
    xml, asked = answer_questions(backend, "s4", yes={"cough"})
    # danger signs, then screening stops at the first yes, then the facts the rules need
    n = len(DANGER_IDS)
    assert asked[:n] == DANGER_IDS and asked[n:n + 2] == ["fever", "cough"]
    assert "diarrhoea" not in asked and "pregnant" not in asked and "age_group" not in asked
    assert asked[n + 2:n + 4] == ["duration", "severity"] and len(asked) <= n + 6
    assert "https://cdn.example/audio/lg/closing_self_care.mp3" in xml  # a mild cough for 2 days
    [ticket] = tickets(backend)
    assert ticket["lang"] == "lg" and ticket["tier"] == "self_care" and ticket["symptoms"] == "cough"
    assert backend.get("/api/stats").json()["by_age_band"] == {"adult": 1}


def test_keypad_caller_with_no_symptom_found_goes_to_a_health_worker(backend):
    choose_language(backend, "s13", "4")  # Runyankole: keypad
    xml, asked = answer_questions(backend, "s13")  # "no" to everything
    assert asked[len(DANGER_IDS):] == ["fever", "cough", "diarrhoea", "vomiting"]  # screening capped at 4
    assert "nyn/closing_urgent.mp3" in xml


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


# --- follow-up visits -----------------------------------------------------------------


def test_follow_up_reuses_details_and_is_translated(backend):
    choose_language(backend, "f1", "3", sex="2", age="1")  # Luganda, baby under 1
    call(backend, "f1", dtmfDigits="1")  # convulsions: yes -> emergency, MED-1
    call(backend, "f2")
    call(backend, "f2", dtmfDigits="3")
    assert "lg/ref_prompt.mp3" in call(backend, "f2", dtmfDigits="9")
    xml = call(backend, "f2", dtmfDigits="1#")
    assert "lg/welcome_back.mp3" in xml and "lg/convulsions.mp3" in xml  # sex and age reused
    call(backend, "f2", dtmfDigits="1")
    follow_up = next(t for t in tickets(backend) if t["parent_id"] == 1)
    assert follow_up["sex"] == "F" and follow_up["age_band"] == "infant"


def test_unknown_reference_goes_back_to_visit_menu(backend):
    call(backend, "f3")
    call(backend, "f3", dtmfDigits="2")
    call(backend, "f3", dtmfDigits="9")
    xml = call(backend, "f3", dtmfDigits="77#")
    assert "Hatukuipata namba hiyo" in xml and "Kwa ziara mpya, bonyeza 1" in xml


def test_new_prompts_are_in_every_recording_script():
    for language in ("lg", "nyn"):
        files = {row["audio_file"] for row in recording_script(language)}
        for prompt_id in ("bio_sex", "visit_type", "ref_prompt", "ref_not_found", "welcome_back",
                          "your_reference", "not_heard", "use_keypad", *(q.id for q in FOLLOW_UP_QUESTIONS)):
            assert f"{language}/{prompt_id}.mp3" in files
    assert not any(row["needs_translation"] for row in recording_script("sw"))


# --- Sunbird ------------------------------------------------------------------------


def test_sunbird_turns_luganda_into_a_speech_language(sunbird):
    client, fake = sunbird
    fake.heard["lg"] = "omwana alina omusujja"
    main = sys.modules["app.main"]
    assert "lg" in main.V.SPEECH_LANGS
    call(client, "b1")
    call(client, "b1", dtmfDigits="3")
    call(client, "b1", dtmfDigits="1")
    call(client, "b1", dtmfDigits="1")
    xml = call(client, "b1", dtmfDigits="3")
    # AUDIO_BASE_URL recordings still win for fixed prompts
    assert "<Record" in xml and "https://cdn.example/audio/lg/describe_symptoms.mp3" in xml
    xml = call(client, "b1", recordingUrl="https://rec.example/1.mp3")
    assert "https://cdn.example/audio/lg/convulsions.mp3" in xml  # then the keypad questions
    xml, _ = answer_questions(client, "b1")
    assert "https://cdn.example/audio/lg/closing_urgent.mp3" in xml  # fever for 2 days
    assert "https://cdn.example/audio/lg/your_reference.mp3" in xml and ">M E D, 1.</Say>" in xml
    assert "sb.example" not in xml  # nothing per-call is synthesised at hang-up
    [ticket] = tickets(client)
    assert ticket["lang"] == "lg" and ticket["symptoms"] == "fever"
    assert "caller: omwana alina omusujja" in ticket["transcript"]
    assert "caller (English, machine translation): the child has a fever" in ticket["transcript"]


def test_sunbird_voices_unrecorded_languages(tmp_path, monkeypatch):
    client, main = load_backend(tmp_path, monkeypatch, SUNBIRD_API_TOKEN="test-token", AUDIO_BASE_URL="")
    fake = FakeSunbird()
    monkeypatch.setattr(main.speech, "_client", fake)
    call(client, "b2")
    xml = call(client, "b2", dtmfDigits="3")  # Luganda, no recordings
    assert '<Play url="https://sb.example/lg/1.wav"/>' in xml and "<Say" not in xml
    english = next(row["english"] for row in recording_script("en") if row["id"] == "visit_type")
    assert fake.translated[0] == (english, "en", "lg")  # English script machine-translated first
    assert fake.spoken[0] == (f"[lg] {english}", "lg")
    call(client, "b2", dtmfDigits="0")
    call(client, "b3")
    call(client, "b3", dtmfDigits="3")
    assert len(fake.spoken) == 2  # nurse line new; the visit prompt came from the cache
    call(client, "b4")
    xml = call(client, "b4", dtmfDigits="1")
    assert "<Say" in xml and "sb.example" not in xml  # English keeps the Africa's Talking voice


def test_sunbird_translation_failure_falls_back_to_keypad(sunbird):
    client, fake = sunbird
    fake.heard["lg"] = "ebigambo ebitategeerekeka"
    fake.fail_translation = True
    choose_language(client, "b5", "3")
    xml = call(client, "b5", recordingUrl="https://rec.example/1.mp3")
    assert "lg/use_keypad.mp3" in xml and "<GetDigits" in xml


def test_sms_is_translated_for_luganda(sunbird):
    main = sys.modules["app.main"]
    sms = main._sms_copy("lg", "MED-4", "urgent")
    assert sms.startswith("Med-Intake ref MED-4. [lg] To follow up") and "Urgent" not in sms
    assert main._sms_copy("sw", "MED-4", "urgent").startswith("Med-Intake ref MED-4. Kiwango: Haraka.")


def test_failed_live_tts_falls_back_to_say_and_is_not_retried_at_once(tmp_path, monkeypatch):
    client, main = load_backend(tmp_path, monkeypatch, SUNBIRD_API_TOKEN="test-token", AUDIO_BASE_URL="")
    fake = FakeSunbird()
    calls = []

    def slow_speak(text, language, **kwargs):
        calls.append(kwargs)
        raise TimeoutError("read timed out")

    fake.speak = slow_speak
    monkeypatch.setattr(main.speech, "_client", fake)
    call(client, "t1")
    xml = call(client, "t1", dtmfDigits="2")  # Swahili: Sunbird voice fails -> <Say>
    assert "<Say" in xml and "Kwa ziara mpya" in xml
    assert calls == [{"timeout": main.speech.SUNBIRD_LIVE_TTS_TIMEOUT, "retries": 0}]
    call(client, "t2")
    call(client, "t2", dtmfDigits="2")
    assert len(calls) == 1  # the same clip is not retried while a caller waits


def test_live_speech_to_text_has_a_short_timeout(sunbird):
    client, fake = sunbird
    fake.heard["lg"] = "omwana alina omusujja"
    choose_language(client, "t3", "3")
    call(client, "t3", recordingUrl="https://rec.example/1.mp3")
    main = sys.modules["app.main"]
    assert fake.stt_kwargs == {"timeout": main.speech.SUNBIRD_LIVE_STT_TIMEOUT, "retries": 0}
    assert main.speech.SUNBIRD_LIVE_STT_TIMEOUT <= 15
