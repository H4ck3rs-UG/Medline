"""Symptom codes from what a caller said, without an LLM (English + Swahili).

Used on the phone line after speech-to-text (and after machine translation for
Luganda/Runyankole). Danger signs come from the red-flag patterns in
``triage.guardrails``. A symptom counts as negated only when the negation comes
right before it ("no rash", "hana homa"), same as the red flags.

This only has to find a starting point: the interview then asks the danger signs
and the key facts on the keypad, which works however well speech was understood.
The Swahili keywords need native-speaker review.
"""

from __future__ import annotations

import re

from triage.guardrails import _NEGATED, check_input
from triage.schema import Symptom as S


def _compile(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


KEYWORDS: dict[S, list[re.Pattern[str]]] = {
    S.FEVER: _compile([r"\bfevers?\b", r"\bfeverish\b", r"\bhigh temperature\b",
                       r"\b(body|he|she|it) (is|feels) (very )?hot\b", r"\bhoma\b", r"\bjoto\b"]),
    S.COUGH: _compile([r"\bcough\w*", r"\bkikohozi\b", r"\b\w*kohoa\b"]),
    S.DIARRHOEA: _compile([r"\bdiarrh\w*", r"\bloose (stools?|motions?)\b", r"\brunning stomach\b",
                           r"\b\w*harisha\b", r"\bkuhara\b"]),
    S.VOMITING: _compile([r"\bvomit\w*", r"\bthrow\w* up\b", r"\bthrew up\b", r"\b\w*tapika\b"]),
    S.VOMITING_EVERYTHING: _compile([r"\bvomit\w* everything\b", r"\bcan'?t keep anything down\b",
                                     r"\b\w*tapika kila kitu\b"]),
    S.UNABLE_TO_DRINK: _compile([r"\b(can'?t|cannot|unable to|not able to|won'?t) (drink|breastfeed|feed|suck)\b",
                                 r"\bhawezi (kunywa|kunyonya)\b"]),
    S.RASH: _compile([r"\brash\w*", r"\bspots on (the|his|her|my) (skin|body)\b", r"\bvipele\b", r"\bupele\b"]),
    S.HEADACHE: _compile([r"\bheadaches?\b", r"\bhead (hurts|pains?|is paining)\b",
                          r"\bmaumivu ya kichwa\b", r"\bkichwa kinauma\b"]),
    S.ABDOMINAL_PAIN: _compile([r"\b(stomach|belly|abdominal|tummy) ?(pains?|aches?)\b",
                                r"\bpain in (the|his|her|my) (stomach|belly|abdomen)\b",
                                r"\bmaumivu ya tumbo\b", r"\btumbo (linauma|kuuma)\b"]),
    S.SORE_THROAT: _compile([r"\bsore throat\b", r"\bthroat (hurts|pains?)\b", r"\bmaumivu ya koo\b"]),
    S.RUNNY_NOSE: _compile([r"\brunny nose\b", r"\bblocked nose\b", r"\bcatarrh\b", r"\bmafua\b"]),
    S.BODY_ACHES: _compile([r"\bbody (aches?|pains?)\b", r"\baching\b", r"\bjoint pains?\b",
                            r"\bmaumivu ya (mwili|viungo)\b"]),
    S.EAR_PAIN: _compile([r"\bear ?(aches?|pains?)\b", r"\bears? (hurts?|pains?)\b", r"\bmaumivu ya sikio\b"]),
    S.PAINFUL_URINATION: _compile([r"\b(pain|burning|hurts?) (when|while) (passing urine|urinating|peeing)\b",
                                   r"\bpainful urination\b", r"\bmaumivu (wakati wa )?kukojoa\b"]),
    S.BLOOD_IN_STOOL: _compile([r"\bblood (in|with) (the |his |her |my )?(stool|poo|faeces|feces)\b",
                                r"\bbloody (stools?|diarrh\w*)\b", r"\bdamu (kwenye|katika) kinyesi\b"]),
    S.STIFF_NECK: _compile([r"\bstiff neck\b", r"\bneck is stiff\b", r"\bshingo ngumu\b"]),
    S.FAST_BREATHING: _compile([r"\bbreathing (very )?fast\b", r"\bfast breathing\b", r"\banapumua haraka\b"]),
    S.INJURY: _compile([r"\binjur\w*", r"\bwound\w*", r"\b(fell|fallen|accident|burn(ed|t))\b",
                        r"\bameumia\b", r"\bajali\b", r"\bjeraha\b"]),
}


def symptoms_in(text: str) -> list[S]:
    """Every symptom code the text mentions and doesn't negate, danger signs first."""
    checked = check_input(text or "")
    found = list(checked.red_flags)
    for symptom, patterns in KEYWORDS.items():
        if symptom in found:
            continue
        for pattern in patterns:
            if any(not _NEGATED.search(checked.text[: m.start()]) for m in pattern.finditer(checked.text)):
                found.append(symptom)
                break
    return found
