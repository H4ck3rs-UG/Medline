"""The questions the follow-up policy can ask: one yes/no question per symptom code.

Each question is a fixed, reviewable line with an English script and a Swahili
draft, so it can be recorded, translated and cached exactly like the keypad menu
(``triage.dtmf``). The model only chooses *which* question comes next; it never
writes the words, so there is nothing to machine-translate or guard live.

Questions for codes already in the keypad menu reuse its wording.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from triage.dtmf import FOLLOW_UP_QUESTIONS, MENU, NO, YES
from triage.schema import Symptom

# IMCI general danger signs: asked first, in this order, never left to the model.
DANGER_SIGNS: tuple[Symptom, ...] = (
    Symptom.CONVULSIONS,
    Symptom.UNCONSCIOUS,
    Symptom.DIFFICULTY_BREATHING,
    Symptom.SEVERE_BLEEDING,
    Symptom.UNABLE_TO_DRINK,
    Symptom.VOMITING_EVERYTHING,
    Symptom.CHEST_PAIN,
)


@dataclass(frozen=True)
class FollowUpQuestion:
    id: str  # prompt id for recordings / cached clips
    symptom: Symptom
    prompt: str  # English script
    translations: dict[str, str] = field(default_factory=dict)
    options: dict[str, bool] = field(default_factory=lambda: {YES: True, NO: False})

    def text(self, language: str = "en") -> str:
        return self.translations.get(language, self.prompt)


def _from_script(questions) -> list[FollowUpQuestion]:
    out = []
    for q in questions:
        try:
            symptom = Symptom(q.id.removeprefix("fu_"))
        except ValueError:  # age_group, duration, severity, pregnant: context, not symptoms
            continue
        out.append(FollowUpQuestion(q.id, symptom, q.prompt, dict(q.translations)))
    return out


# Wording lives in triage.dtmf with the other scripted prompts, so every question
# is in the recording scripts and the Sunbird warm-up.
NEW_PROMPTS: list[FollowUpQuestion] = _from_script(FOLLOW_UP_QUESTIONS)
BANK: list[FollowUpQuestion] = _from_script(MENU) + NEW_PROMPTS
BY_SYMPTOM: dict[Symptom, FollowUpQuestion] = {q.symptom: q for q in BANK}
