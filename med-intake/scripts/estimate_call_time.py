"""Estimate how long a call takes, by running the real interview on simulated callers.

    python med-intake/scripts/estimate_call_time.py            # 2,000 simulated calls per path

Callers are drawn from the follow-up model's training data
(training/followup/data/processed/symptom_patterns.csv, made by train.py), so
the mix of symptoms is realistic for that data, not for Uganda. Every prompt the
caller would hear is timed from its real text. Assumptions (edit to taste):
"""

from __future__ import annotations

import csv
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from triage import dtmf, prompts  # noqa: E402
from triage.followup import FollowUpPolicy, Interview  # noqa: E402
from triage.followup.interview import QUESTIONS  # noqa: E402
from triage.rules.engine import decide  # noqa: E402
from triage.schema import AgeGroup, Symptom  # noqa: E402

# Speaking time. English <Say>: ~150 words/min. Luganda: measured from 29 Sunbird
# clips (0.44 s per word of the English script). Swahili: assumed like Luganda.
SECONDS_PER_WORD = {"en": 0.40, "sw": 0.44, "lg": 0.44, "nyn": 0.44}
KEYPRESS = 2.0  # caller presses a key after the prompt ends
CALLBACK = 0.7  # Africa's Talking -> our backend -> XML back, with cached audio
DESCRIBE = 12.0  # caller describes the problem, then presses # (or 5 s of silence)
# Waiting after the description: speech-to-text (+ translation for lg/nyn).
# Sunbird measured: ~5 s STT + ~3 s translation. ElevenLabs for en: assumed ~3 s.
SPEECH_PROCESSING = {"en": 3.0, "sw": 5.0, "lg": 8.0, "nyn": 8.0}
PATTERNS = ROOT / "training" / "followup" / "data" / "processed" / "symptom_patterns.csv"


def speak(text: str, lang: str) -> float:
    # Scripts are timed on the English wording, the unit the Luganda rate was measured in.
    return len(text.split()) * SECONDS_PER_WORD[lang]


def load_callers(n: int, rng: random.Random) -> list[dict]:
    if PATTERNS.exists():
        rows = list(csv.DictReader(PATTERNS.open()))
        totals: dict[str, int] = {}
        for r in rows:
            totals[r["dataset"]] = totals.get(r["dataset"], 0) + int(r["count"])
        weights = [0.5 * int(r["count"]) / totals[r["dataset"]] for r in rows]
        picks = rng.choices(rows, weights=weights, k=n)
        truths = [{Symptom(x) for x in r["symptoms"].split(";")} for r in picks]
    else:  # no training data yet: a few typical presentations
        common = [{Symptom.FEVER}, {Symptom.COUGH, Symptom.FEVER}, {Symptom.DIARRHOEA, Symptom.VOMITING},
                  {Symptom.HEADACHE}, {Symptom.ABDOMINAL_PAIN}, {Symptom.COUGH}]
        truths = [rng.choice(common) for _ in range(n)]
    callers = []
    for truth in truths:
        age = rng.choices(list(AgeGroup), weights=[10, 35, 45, 10])[0]
        sex = rng.choice("MF")
        callers.append({
            "truth": truth, "age": age, "sex": sex,
            "duration": rng.choice(["1", "2", "3", "4", "5"]), "severity": rng.choice(["1", "2", "3"]),
            "pregnant": "1" if sex == "F" and age == AgeGroup.ADULT and rng.random() < 0.2 else "2",
        })
    return callers


def run_call(c: dict, lang: str, speech_path: bool, policy: FollowUpPolicy, rng: random.Random) -> dict:
    t = {"listening": 0.0, "answering": 0.0, "waiting": 0.0}

    def ask(text, answer_seconds=KEYPRESS):
        t["listening"] += speak(text, lang if lang != "all" else "en")
        t["answering"] += answer_seconds
        t["waiting"] += CALLBACK

    ask(dtmf.system_text("language_menu"))
    ask(dtmf.system_text("visit_type"))
    ask(dtmf.system_text("bio_sex"))
    ask(next(q for q in dtmf.MENU if q.id == "age_group").prompt)
    iv = Interview(policy, sex=c["sex"], age_group=c["age"])
    if speech_path:
        ask(dtmf.system_text("describe_symptoms"), DESCRIBE)
        t["waiting"] += SPEECH_PROCESSING[lang]
        said = [s for s in c["truth"] if rng.random() < 0.7] or [next(iter(c["truth"]))]  # caller mentions most
        iv.add_mentioned(said)
    else:
        t["listening"] += speak(dtmf.system_text("welcome"), lang)
    questions = 0
    while (q := iv.next_question()) is not None:
        ask(QUESTIONS[q.id].prompt)
        questions += 1
        key = c.get(q.id) if q.id in ("duration", "severity", "pregnant") else ("1" if q.symptom in c["truth"] else "2")
        iv.answer(q.id, key)
    tier = decide(iv.finish()).tier
    t["listening"] += speak(prompts.closing_line(tier), lang) + speak(dtmf.system_text("your_reference") + " M E D 4 2", lang)
    return {**t, "total": sum(t.values()), "questions": questions, "tier": tier.value}


def summarise(label: str, calls: list[dict]) -> None:
    totals = sorted(c["total"] for c in calls)
    p90 = totals[int(0.9 * len(totals))]
    mean = {k: statistics.mean(c[k] for c in calls) for k in ("listening", "answering", "waiting", "questions")}
    emergency = sum(c["tier"] == "emergency" for c in calls) / len(calls)
    print(f"  {label:<30} mean {statistics.mean(totals) / 60:4.1f} min | median {statistics.median(totals) / 60:4.1f} "
          f"| 90% under {p90 / 60:4.1f} | {mean['questions']:4.1f} questions | listening {mean['listening']:3.0f}s, "
          f"answering {mean['answering']:3.0f}s, waiting {mean['waiting']:3.0f}s | {emergency:.0%} emergencies")


def main() -> None:
    rng = random.Random(11)
    policy = FollowUpPolicy()
    callers = load_callers(2000, rng)
    print(f"{len(callers):,} simulated callers ({'training data mix' if PATTERNS.exists() else 'built-in examples'})")
    for label, lang, speech_path in [
        ("English, speaks", "en", True),
        ("Swahili, speaks", "sw", True),
        ("Luganda, speaks (Sunbird)", "lg", True),
        ("Luganda/Runyankole, keypad", "lg", False),
    ]:
        summarise(label, [run_call(c, lang, speech_path, policy, rng) for c in callers])


if __name__ == "__main__":
    main()
