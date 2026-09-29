"""Keypress path for languages without reliable speech recognition.

A native speaker records one audio prompt per question below. The caller
answers with the keypad, and the answers become the same ``SymptomReport`` the
LLM path produces, so both paths go through the same rules engine.

Adding a language means adding a script to ``MenuQuestion.translations`` (or
just recording from the English script) and dropping the clips at
``audio_path(language, prompt_id)``. ``recording_script`` lists every clip a
language needs. The keypresses never change between languages.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from triage import prompts
from triage.schema import AgeGroup, Severity, Symptom, SymptomReport

YES, NO = "1", "2"

# Languages served by the recorded keypad menu, with display names.
KEYPAD_LANGUAGES = {
    "en": "English",
    "sw": "Swahili",
    "lg": "Luganda",
    "nyn": "Runyankole",
}
AUDIO_FORMAT = "mp3"
ALL_LANGUAGES = "all"  # audio folder for clips shared by every language
LANGUAGE_MENU = "language_menu"


@dataclass(frozen=True)
class MenuQuestion:
    id: str
    prompt: str  # English script for the recording
    options: dict[str, object]  # keypress -> value
    # Reviewed scripts in other languages, keyed by language code. A language
    # missing here is recorded by a native speaker from the English script.
    translations: dict[str, str] = field(default_factory=dict)

    def text(self, language: str = "en") -> str:
        """The script in ``language``, or English if there is no written one yet."""
        return self.translations.get(language, self.prompt)


def _yes_no(question_id: str, prompt: str, sw: str) -> MenuQuestion:
    return MenuQuestion(
        question_id,
        f"{prompt} Press 1 for yes, 2 for no.",
        {YES: True, NO: False},
        {"sw": f"{sw} Bonyeza 1 kwa ndiyo, 2 kwa hapana."},
    )


# Asked in this order. Danger signs come first so an emergency is caught early.
MENU: list[MenuQuestion] = [
    MenuQuestion(
        "age_group",
        "Who is sick? Press 1 for a baby under one year, 2 for a child, 3 for an adult, "
        "4 for an older person over 65.",
        {"1": AgeGroup.INFANT, "2": AgeGroup.CHILD, "3": AgeGroup.ADULT, "4": AgeGroup.ELDERLY},
        {
            "sw": "Nani anaumwa? Bonyeza 1 kwa mtoto mchanga chini ya mwaka mmoja, 2 kwa mtoto, "
            "3 kwa mtu mzima, 4 kwa mzee zaidi ya miaka 65."
        },
    ),
    _yes_no("convulsions", "Is the patient having fits or convulsions?", "Je, mgonjwa ana degedege au kifafa?"),
    _yes_no(
        "unconscious",
        "Is the patient unconscious or very hard to wake?",
        "Je, mgonjwa amepoteza fahamu au ni vigumu sana kumwamsha?",
    ),
    _yes_no("difficulty_breathing", "Is the patient struggling to breathe?", "Je, mgonjwa anashindwa kupumua?"),
    _yes_no("severe_bleeding", "Is the patient bleeding heavily?", "Je, mgonjwa anatokwa na damu nyingi?"),
    _yes_no(
        "unable_to_drink",
        "Is the patient unable to drink or breastfeed?",
        "Je, mgonjwa hawezi kunywa au kunyonya?",
    ),
    _yes_no("chest_pain", "Does the patient have chest pain?", "Je, mgonjwa ana maumivu ya kifua?"),
    _yes_no("pregnant", "Is the patient pregnant?", "Je, mgonjwa ni mjamzito?"),
    _yes_no("fever", "Does the patient have a fever or feel hot?", "Je, mgonjwa ana homa au mwili una joto?"),
    _yes_no("cough", "Does the patient have a cough?", "Je, mgonjwa anakohoa?"),
    _yes_no("diarrhoea", "Does the patient have diarrhoea?", "Je, mgonjwa anaharisha?"),
    _yes_no("blood_in_stool", "Is there blood in the stool?", "Je, kuna damu kwenye kinyesi?"),
    _yes_no("vomiting", "Is the patient vomiting?", "Je, mgonjwa anatapika?"),
    _yes_no("rash", "Does the patient have a rash?", "Je, mgonjwa ana vipele mwilini?"),
    MenuQuestion(
        "duration",
        "How long has the patient been sick? Press 1 for less than a day, 2 for one to two days, "
        "3 for three to six days, 4 for one to two weeks, 5 for more than two weeks.",
        # Each band maps to its upper bound so duration rules err towards caution.
        {"1": 0, "2": 2, "3": 6, "4": 14, "5": 15},
        {
            "sw": "Mgonjwa ameumwa kwa muda gani? Bonyeza 1 kwa chini ya siku moja, 2 kwa siku moja "
            "hadi mbili, 3 kwa siku tatu hadi sita, 4 kwa wiki moja hadi mbili, 5 kwa zaidi ya wiki mbili."
        },
    ),
    MenuQuestion(
        "severity",
        "How bad is it? Press 1 for mild, 2 for moderate, 3 for severe.",
        {"1": Severity.MILD, "2": Severity.MODERATE, "3": Severity.SEVERE},
        {"sw": "Hali ni mbaya kiasi gani? Bonyeza 1 kwa kidogo, 2 kwa wastani, 3 kwa mbaya sana."},
    ),
]

_BY_ID = {q.id: q for q in MENU}

# Lines around the questions. Same shape as MENU entries: English script plus
# written translations. The Swahili is a draft that needs native-speaker review.
SYSTEM_PROMPTS: dict[str, dict[str, str]] = {
    "language_menu": {
        # Each option is announced in its own language, so this clip is recorded
        # by several speakers and joined; there is no single-language version.
        "en": "For English, press 1. Kwa Kiswahili, bonyeza 2. For Luganda, press 3. "
        "For Runyankole, press 4.",
    },
    "welcome": {
        "en": "Welcome to the community health line. Please answer each question with your keypad.",
        "sw": "Karibu kwenye simu ya afya ya jamii. Tafadhali jibu kila swali kwa kubonyeza namba.",
    },
    "invalid_key": {
        "en": "Sorry, that key is not an option. Please listen again.",
        "sw": "Samahani, namba hiyo si chaguo. Tafadhali sikiliza tena.",
    },
    "describe_symptoms": {
        "en": "Please describe the patient's symptoms after the beep, then press the hash key.",
        "sw": "Tafadhali eleza dalili za mgonjwa baada ya mlio, kisha bonyeza kitufe cha reli.",
    },
    "connecting_nurse": {
        "en": "Connecting you to a nurse. Please hold.",
        "sw": "Tunakuunganisha na muuguzi. Tafadhali subiri.",
    },
}


def audio_path(language: str, prompt_id: str) -> str:
    """Where the recorded clip for a menu question or system prompt lives,
    relative to the audio base URL. Closing lines use ``closing_<tier>``."""
    return f"{language}/{prompt_id}.{AUDIO_FORMAT}"


def system_text(prompt_id: str, language: str = "en") -> str:
    texts = SYSTEM_PROMPTS[prompt_id]
    return texts.get(language) or texts["en"]


def recording_script(language: str) -> list[dict[str, object]]:
    """Every clip ``language`` needs for the keypad path, in call order.

    ``text`` is the written script in that language when one exists; otherwise
    it is the English source and ``needs_translation`` is true, so the recording
    speaker (or a translator) works from English.

    The language menu is shared by every language, so it is only listed under
    ``recording_script(ALL_LANGUAGES)``.
    """
    rows: list[tuple[str, str | None, str]] = []
    if language == ALL_LANGUAGES:
        rows.append((LANGUAGE_MENU, SYSTEM_PROMPTS[LANGUAGE_MENU]["en"], SYSTEM_PROMPTS[LANGUAGE_MENU]["en"]))
        return _rows(language, rows)
    for prompt_id, texts in SYSTEM_PROMPTS.items():
        if prompt_id != LANGUAGE_MENU:
            rows.append((prompt_id, texts.get(language), texts["en"]))
    for question in MENU:
        written = question.prompt if language == "en" else question.translations.get(language)
        rows.append((question.id, written, question.prompt))
    for key in ("closing_emergency", "closing_urgent", "closing_self_care"):
        rows.append((key, prompts.CANNED.get(language, {}).get(key), prompts.CANNED["en"][key]))
    return _rows(language, rows)


def _rows(language: str, rows: list[tuple[str, str | None, str]]) -> list[dict[str, object]]:
    return [
        {
            "id": prompt_id,
            "audio_file": audio_path(language, prompt_id),
            "english": english,
            "text": text or english,
            "needs_translation": text is None,
        }
        for prompt_id, text, english in rows
    ]


def next_question(answers: dict[str, str]) -> MenuQuestion | None:
    """The first menu question not yet answered, or None when the menu is done."""
    return next((q for q in MENU if q.id not in answers), None)


def report_from_keypresses(answers: dict[str, str]) -> SymptomReport:
    """Build a report from ``{question_id: key}``. Missing questions are unknown."""
    report = SymptomReport()
    for question_id, key in answers.items():
        question = _BY_ID.get(question_id)
        if question is None:
            report.other_notes.append(f"unknown menu question {question_id!r}")
            continue
        value = question.options.get(str(key).strip())
        if value is None:
            report.other_notes.append(f"invalid keypress {key!r} for {question_id}")
            continue
        if question_id == "age_group":
            report.age_group = value
        elif question_id == "duration":
            report.duration_days = value
        elif question_id == "severity":
            report.severity = value
        elif question_id == "pregnant":
            report.pregnant = value
        elif value is True:
            report.add_symptoms([Symptom(question_id)])

    report.intake_complete = all(q.id in answers for q in MENU) and not report.other_notes
    if report.pregnant and report.has(Symptom.SEVERE_BLEEDING):
        report.add_symptoms([Symptom.BLEEDING_IN_PREGNANCY])
    return report
