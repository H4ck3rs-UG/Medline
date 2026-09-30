"""The questions the follow-up policy can ask: one yes/no question per symptom code.

Each question is a fixed, reviewable line with an English script and a Swahili
draft, so it can be recorded, translated and cached exactly like the keypad menu
(``triage.dtmf``). The model only chooses *which* question comes next; it never
writes the words, so there is nothing to machine-translate or guard live.

Questions for codes already in the keypad menu reuse its wording.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from triage.dtmf import MENU, NO, YES
from triage.schema import Symptom

# IMCI general danger signs: asked first, in this order, never left to the model.
DANGER_SIGNS: tuple[Symptom, ...] = (
    Symptom.CONVULSIONS,
    Symptom.UNCONSCIOUS,
    Symptom.DIFFICULTY_BREATHING,
    Symptom.SEVERE_BLEEDING,
    Symptom.UNABLE_TO_DRINK,
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


def _q(symptom: Symptom, en: str, sw: str) -> FollowUpQuestion:
    return FollowUpQuestion(
        f"fu_{symptom.value}",
        symptom,
        f"{en} Press 1 for yes, 2 for no.",
        {"sw": f"{sw} Bonyeza 1 kwa ndiyo, 2 kwa hapana."},
    )


# Swahili drafts need native-speaker review, like the rest of the Swahili text.
_EXTRA = [
    _q(Symptom.FAST_BREATHING, "Is the patient breathing faster than usual?", "Je, mgonjwa anapumua haraka kuliko kawaida?"),
    _q(Symptom.VOMITING_EVERYTHING, "Does the patient vomit everything they eat or drink?", "Je, mgonjwa anatapika kila anachokula au kunywa?"),
    _q(Symptom.STIFF_NECK, "Does the patient have a stiff neck?", "Je, mgonjwa ana shingo ngumu?"),
    _q(Symptom.HEADACHE, "Does the patient have a headache?", "Je, mgonjwa ana maumivu ya kichwa?"),
    _q(Symptom.ABDOMINAL_PAIN, "Does the patient have pain in the belly?", "Je, mgonjwa ana maumivu ya tumbo?"),
    _q(Symptom.SORE_THROAT, "Does the patient have a sore throat?", "Je, mgonjwa ana maumivu ya koo?"),
    _q(Symptom.RUNNY_NOSE, "Does the patient have a runny or blocked nose?", "Je, mgonjwa ana mafua au pua iliyoziba?"),
    _q(Symptom.BODY_ACHES, "Does the patient have aches in the body or joints?", "Je, mgonjwa ana maumivu ya mwili au viungo?"),
    _q(Symptom.EAR_PAIN, "Does the patient have ear pain?", "Je, mgonjwa ana maumivu ya sikio?"),
    _q(Symptom.PAINFUL_URINATION, "Does it hurt when the patient passes urine?", "Je, mgonjwa anasikia maumivu wakati wa kukojoa?"),
    _q(Symptom.INJURY, "Has the patient been injured, for example by a fall or an accident?", "Je, mgonjwa ameumia, kwa mfano kwa kuanguka au ajali?"),
    # The keypad menu infers this from its pregnant + heavy bleeding answers.
    _q(Symptom.BLEEDING_IN_PREGNANCY, "Is the patient pregnant and bleeding from the vagina?", "Je, mgonjwa ni mjamzito na anatokwa na damu ukeni?"),
]


def _from_menu() -> list[FollowUpQuestion]:
    out = []
    for q in MENU:
        try:
            symptom = Symptom(q.id)
        except ValueError:  # age_group, duration, severity, pregnant: context, not symptoms
            continue
        out.append(FollowUpQuestion(q.id, symptom, q.prompt, dict(q.translations)))
    return out


BANK: list[FollowUpQuestion] = _from_menu() + _EXTRA
BY_SYMPTOM: dict[Symptom, FollowUpQuestion] = {q.symptom: q for q in BANK}
# Menu questions keep their clip ids; these are the ones to add to the recording scripts.
NEW_PROMPTS: list[FollowUpQuestion] = list(_EXTRA)
