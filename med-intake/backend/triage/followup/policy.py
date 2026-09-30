"""Which follow-up question to ask next.

1. The IMCI danger signs, in a fixed order, unless already answered.
2. Then up to ``max_followups`` questions chosen by value of information:
   for each unasked symptom, the trained model gives P(yes); the rules engine
   (``triage.rules.engine.decide``) says whether a yes would raise the urgency
   tier. Score = P(yes) x (1 + escalation_weight x tiers raised): the expected
   change to the outcome, so a question that could change it (fever -> stiff
   neck, fever -> rash) beats one that just enriches the ticket, and between two
   that could, likelihood still counts. A question that could raise the tier is
   never dropped for being unlikely; the others need P(yes) >= min_probability.
   (Simulated calls: weight 100 with that rule gave 99.4% tier agreement with 2
   follow-ups, vs 99.2% for lower weights or a likelihood floor on every question.
   Ranking strictly by tiers raised, ignoring likelihood, asked absurd questions,
   such as pregnancy bleeding for a child.)

The rules engine still makes the decision; the policy only chooses questions,
and every question is a fixed line from ``bank.BANK``.
"""

from __future__ import annotations

from dataclasses import dataclass

from triage.followup.bank import BANK, BY_SYMPTOM, DANGER_SIGNS, FollowUpQuestion
from triage.followup.model import SymptomModel
from triage.rules.engine import decide
from triage.schema import Symptom, SymptomReport


@dataclass
class Ranked:
    question: FollowUpQuestion
    score: float
    p_yes: float
    tiers_raised: int


class FollowUpPolicy:
    def __init__(
        self,
        model: SymptomModel | None = None,
        *,
        max_followups: int = 3,
        danger_first: bool = True,
        min_probability: float = 0.05,
        escalation_weight: float = 100.0,
    ):
        self.model = model if model is not None else SymptomModel.load()
        self.max_followups = max_followups
        self.danger_first = danger_first
        self.min_probability = min_probability
        self.escalation_weight = escalation_weight

    def next_question(self, report: SymptomReport, asked: set[str]) -> FollowUpQuestion | None:
        """The next question, or None when there's nothing worth asking.
        ``asked`` holds question ids already put to the caller; an asked symptom
        that isn't in ``report.symptoms`` counts as answered no."""
        if self.danger_first:
            for symptom in DANGER_SIGNS:
                q = BY_SYMPTOM[symptom]
                if q.id not in asked and symptom not in report.symptoms:
                    return q
        danger_ids = {BY_SYMPTOM[s].id for s in DANGER_SIGNS}
        if len(asked - danger_ids) >= self.max_followups:
            return None
        ranked = self.rank(report, asked)
        return ranked[0].question if ranked else None

    def rank(self, report: SymptomReport, asked: set[str]) -> list[Ranked]:
        """All candidate questions, best first (useful for logging why a question was asked)."""
        yes = set(report.symptoms)
        no = {q.symptom for q in BANK if q.id in asked and q.symptom not in yes}
        current = decide(report).tier.rank
        out = []
        for q in BANK:
            if q.id in asked or q.symptom in yes or q.symptom in DANGER_SIGNS:
                continue
            p = self.model.p_yes(q.symptom, yes, no) if self.model else 0.0
            raised = max(decide(_with(report, q.symptom)).tier.rank - current, 0)
            if not raised and p < self.min_probability:
                continue
            out.append(Ranked(q, p * (1 + self.escalation_weight * raised), p, raised))
        return sorted(out, key=lambda r: r.score, reverse=True)


def _with(report: SymptomReport, symptom: Symptom) -> SymptomReport:
    hypothetical = report.model_copy(deep=True)
    hypothetical.add_symptoms([symptom])
    return hypothetical
