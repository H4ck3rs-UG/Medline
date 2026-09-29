from triage import FakeLLMClient, FakeTranslator, IntakeSession, TranslatingSession, prompts
from triage.dtmf import ALL_LANGUAGES, KEYPAD_LANGUAGES, MENU, audio_path, recording_script
from triage.guardrails import check_input, reply_violations
from triage.schema import CloseReason, Symptom, UrgencyTier


def turn(**fields):
    base = {"reply": "How many days has the patient been sick?", "on_topic": True, "symptoms": []}
    return {**base, **fields}


# --- canned lines and system prompt ---------------------------------------


def test_every_language_has_every_canned_line():
    for language, lines in prompts.CANNED.items():
        assert set(lines) == set(prompts.CANNED["en"]), language
        assert all(text.strip() for text in lines.values())


def test_line_falls_back_to_english():
    assert prompts.line("greeting", "lg") == prompts.CANNED["en"]["greeting"]
    assert prompts.closing_line("urgent", "sw") == prompts.CANNED["sw"]["closing_urgent"]


def test_english_aliases_unchanged():
    assert prompts.GREETING == prompts.CANNED["en"]["greeting"]
    assert prompts.CLOSING_BY_TIER[UrgencyTier.EMERGENCY] == prompts.EMERGENCY_LINE


def test_system_prompt_pins_language():
    assert "Always reply in Swahili" in prompts.build_system_prompt(language="sw")
    assert "Always reply in English" in prompts.build_system_prompt(language="xx")


# --- harness in Swahili ------------------------------------------------------


def test_swahili_session_uses_swahili_canned_lines():
    llm = FakeLLMClient([turn(reply="Ana homa kwa siku ngapi?", symptoms=["fever"]),
                         turn(reply="Asante.", duration_days=3, done=True)])
    session = IntakeSession(llm, language="sw")
    assert session.opening_line() == prompts.CANNED["sw"]["greeting"]
    assert "Always reply in Swahili" in session.system_prompt
    session.handle_utterance("mtoto ana homa")
    result = session.handle_utterance("siku tatu")
    assert result.done
    assert result.reply_text == prompts.CANNED["sw"]["closing_urgent"]
    assert session.finalize().language == "sw"


def test_swahili_red_flag_closes_with_swahili_emergency_line():
    llm = FakeLLMClient([])
    result = IntakeSession(llm, language="sw").handle_utterance("mtoto hawezi kupumua")
    assert result.emergency
    assert result.reply_text == prompts.CANNED["sw"]["closing_emergency"]
    assert llm.calls == []


def test_original_text_red_flag_is_caught_even_if_translation_drops_it():
    session = IntakeSession(FakeLLMClient([]))
    result = session.handle_utterance("the child is unwell", original_text="ana degedege")
    assert result.emergency
    assert session.finalize().transcript[0] == {
        "role": "caller", "content": "ana degedege", "translation": "the child is unwell"
    }


# --- Swahili output guard ----------------------------------------------------


def test_swahili_questions_pass_the_output_guard():
    for reply in ["Ana homa kwa siku ngapi?", "Mgonjwa ana umri gani?", "Je, amekwenda hospitali?"]:
        assert reply_violations(reply) == [], reply


def test_swahili_unsafe_replies_are_rejected():
    assert "urgency" in reply_violations("Nenda hospitali sasa hivi.")
    assert "urgency" in reply_violations("Usijali, atapona.")
    assert "medication" in reply_violations("Mpe vidonge viwili.")
    assert "diagnosis" in reply_violations("Ana kifua kikuu.")


def test_swahili_breathing_red_flags():
    assert Symptom.DIFFICULTY_BREATHING in check_input("anapumua kwa shida, hawezi kupumua").red_flags
    assert check_input("hana shida ya kupumua").red_flags == []


# --- TranslatingSession --------------------------------------------------------


def test_translating_session_round_trip():
    table = {
        ("omwana alina omusujja", "lg", "en"): "the child has a fever",
        ("How many days has the patient been sick?", "en", "lg"): "Omulwadde amaze ennaku mmeka?",
    }
    translator = FakeTranslator(table)
    llm = FakeLLMClient([turn(symptoms=["fever"], age_group="child")])
    session = TranslatingSession(llm, translator, "lg")
    result = session.handle_utterance("omwana alina omusujja")
    assert result.reply_text == "Omulwadde amaze ennaku mmeka?"
    assert "the child has a fever" in llm.calls[0][1][-1]["content"]
    assert session.session.report.symptoms == [Symptom.FEVER]


def test_translating_session_prefers_reviewed_canned_lines():
    translator = FakeTranslator()
    session = TranslatingSession(FakeLLMClient([]), translator, "sw")
    assert session.opening_line() == prompts.CANNED["sw"]["greeting"]
    assert translator.calls == []


def test_translation_failure_does_not_call_model_and_fails_safe():
    llm = FakeLLMClient([])
    session = TranslatingSession(llm, FakeTranslator(fail=True), "lg")
    first = session.handle_utterance("omwana mulwadde")
    assert not first.done
    second = session.handle_utterance("omwana mulwadde")
    assert second.done and not second.emergency
    outcome = session.finalize()
    assert outcome.closed_reason == CloseReason.MODEL_FAILURE
    assert outcome.decision.tier == UrgencyTier.URGENT
    assert outcome.language == "lg"
    assert llm.calls == []


def test_translation_failure_still_catches_red_flags_in_original():
    session = TranslatingSession(FakeLLMClient([]), FakeTranslator(fail=True), "sw")
    result = session.handle_utterance("ana degedege")
    assert result.emergency
    assert result.reply_text == prompts.CANNED["sw"]["closing_emergency"]


def test_unsafe_translated_reply_is_replaced():
    translator = FakeTranslator({
        ("How many days has the patient been sick?", "en", "xx"): "Nenda hospitali sasa.",
        (prompts.SAFE_REPLY, "en", "xx"): "safe line",
    })
    session = TranslatingSession(FakeLLMClient([turn(symptoms=["cough"])]), translator, "xx")
    assert session.handle_utterance("cough").reply_text == "safe line"


# --- keypad recording scripts ------------------------------------------------


def test_swahili_keypad_menu_is_fully_written():
    assert all("sw" in q.translations for q in MENU)
    assert not any(row["needs_translation"] for row in recording_script("sw"))


def test_untranslated_languages_are_flagged_and_use_english_source():
    rows = recording_script("lg")
    assert all(row["needs_translation"] for row in rows)
    assert rows[0]["text"] == rows[0]["english"]
    ids = [row["id"] for row in rows]
    assert "language_menu" not in ids
    assert {q.id for q in MENU} <= set(ids)
    assert {"closing_emergency", "closing_urgent", "closing_self_care"} <= set(ids)


def test_language_menu_is_one_shared_clip():
    rows = recording_script(ALL_LANGUAGES)
    assert [row["audio_file"] for row in rows] == ["all/language_menu.mp3"]


def test_audio_paths():
    assert audio_path("lg", "fever") == "lg/fever.mp3"
    assert set(KEYPAD_LANGUAGES) >= {"en", "sw", "lg", "nyn"}
