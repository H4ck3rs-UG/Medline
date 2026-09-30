"""The structured part of a call: which question to ask next, on any path.

Order (each step skipped when it has nothing to ask):
1. Danger signs, one at a time. The moment the answers add up to an emergency,
   the interview stops so the caller can be told to go now.
2. Screening, when no symptom is known yet (keypad callers, or speech that
   matched nothing): the IMCI main symptoms in order (fever, cough, diarrhoea,
   vomiting, ...) until one is a yes, at most ``max_screening``. A fixed
   clinical order, because the training data's base rates don't reflect what
   callers here present with.
3. What the rules need: how long, whether the patient is pregnant (women of
   adult or unknown age only), and how bad it is.
4. Emergency checks: any question a yes to which would make this an emergency
   (fever -> stiff neck, pregnant -> bleeding), however unlikely the model thinks
   it is. Its likelihoods are too weak to be trusted to skip these.
5. Up to ``max_followups`` questions chosen by the follow-up policy.

Answers are keypresses ("1" yes / "2" no, or a menu option). The report is
rebuilt from the answers each time, and ``finish`` hands it to the rules engine.
Nothing here talks to a phone, so it is tested on its own.
"""

from __future__ import annotations

from triage.dtmf import MENU, MenuQuestion
from triage.followup.bank import BY_SYMPTOM, DANGER_SIGNS, FollowUpQuestion
from triage.followup.policy import FollowUpPolicy
from triage.rules.engine import decide
from triage.schema import AgeGroup, Symptom, SymptomReport, UrgencyTier

_MENU = {q.id: q for q in MENU}
SCREENING = (Symptom.FEVER, Symptom.COUGH, Symptom.DIARRHOEA, Symptom.VOMITING,
             Symptom.ABDOMINAL_PAIN, Symptom.RASH, Symptom.INJURY)
DURATION, PREGNANT, SEVERITY = _MENU["duration"], _MENU["pregnant"], _MENU["severity"]
QUESTIONS: dict[str, MenuQuestion | FollowUpQuestion] = {
    **{q.id: q for q in BY_SYMPTOM.values()},
    **{q.id: q for q in (DURATION, PREGNANT, SEVERITY)},
}


class Interview:
    def __init__(
        self,
        policy: FollowUpPolicy | None = None,
        *,
        sex: str = "",
        age_group: AgeGroup | str | None = None,
        max_screening: int = 4,
        max_followups: int = 2,
    ):
        self.policy = policy or FollowUpPolicy()
        self.sex = (sex or "").upper()
        self.age_group = _age(age_group)
        self.max_screening = max_screening
        self.max_followups = max_followups
        self.mentioned: list[Symptom] = []  # from what the caller said
        self.answers: dict[str, str] = {}  # question id -> key pressed
        self.asked: list[str] = []  # in order
        self._stage: dict[str, str] = {}  # question id -> step it was asked in

    # --- inputs ------------------------------------------------------------------

    def add_mentioned(self, symptoms: list[Symptom]) -> None:
        """Symptoms the caller described in their own words."""
        for s in symptoms:
            if s not in self.mentioned:
                self.mentioned.append(s)

    def answer(self, question_id: str, key: str) -> bool:
        """Record a keypress. False if the key isn't an option for that question."""
        q = QUESTIONS.get(question_id)
        if q is None or str(key).strip() not in q.options:
            return False
        self.answers[question_id] = str(key).strip()
        return True

    # --- state -------------------------------------------------------------------

    def report(self, *, complete: bool = True) -> SymptomReport:
        r = SymptomReport(symptoms=list(self.mentioned), age_group=self.age_group, intake_complete=complete)
        for qid, key in self.answers.items():
            value = QUESTIONS[qid].options[key]
            if qid == DURATION.id:
                r.duration_days = value
            elif qid == SEVERITY.id:
                r.severity = value
            elif qid == PREGNANT.id:
                r.pregnant = value
            elif value is True:
                r.add_symptoms([QUESTIONS[qid].symptom])
        if r.pregnant and r.has(Symptom.SEVERE_BLEEDING):
            r.add_symptoms([Symptom.BLEEDING_IN_PREGNANCY])
        return r

    def is_emergency(self) -> bool:
        return decide(self.report()).tier == UrgencyTier.EMERGENCY

    def finish(self, *, complete: bool = True) -> SymptomReport:
        """The report for the rules engine. ``complete=False`` when the caller
        couldn't finish (e.g. kept pressing wrong keys): never self-care then."""
        return self.report(complete=complete)

    # --- planning ------------------------------------------------------------------

    def next_question(self) -> MenuQuestion | FollowUpQuestion | None:
        """The next question to ask, or None: triage now."""
        q = self._plan()
        if q is not None:
            self.asked.append(q.id)
        return q

    def _plan(self):
        report = self.report()
        if decide(report).tier == UrgencyTier.EMERGENCY:
            return None
        answered = set(self.answers)
        unasked = lambda q: q.id not in answered and q.id not in self.asked  # noqa: E731

        # 1. danger signs
        for s in DANGER_SIGNS:
            q = BY_SYMPTOM[s]
            if unasked(q) and s not in report.symptoms:
                return self._mark(q, "danger")

        symptom_ids = {q.id for q in BY_SYMPTOM.values()}
        asked_symptoms = {qid for qid in self.asked if qid in symptom_ids}

        # 2. screening: find a first symptom when none is known yet (keypad callers,
        #    or speech that couldn't be matched to a symptom)
        has_symptom = bool(report.symptoms)
        if not has_symptom:
            if self._count("screening") >= self.max_screening:
                return None  # nothing found: the rules send this to a health worker
            q = next((BY_SYMPTOM[s] for s in SCREENING if unasked(BY_SYMPTOM[s])), None)
            return self._mark(q, "screening")

        # 3. what the rules need
        if report.duration_days is None and unasked(DURATION):
            return self._mark(DURATION, "context")
        if report.pregnant is None and unasked(PREGNANT) and self._could_be_pregnant(report):
            return self._mark(PREGNANT, "context")
        if report.severity is None and unasked(SEVERITY):
            return self._mark(SEVERITY, "context")

        # 4. emergency checks
        for q in BY_SYMPTOM.values():
            if unasked(q) and q.symptom not in report.symptoms and self._eligible(q, report) and \
                    decide(_with(report, q.symptom)).tier == UrgencyTier.EMERGENCY:
                return self._mark(q, "emergency_check")

        # 5. follow-ups
        if self._count("followup") >= self.max_followups:
            return None
        return self._mark(self._best(report, asked_symptoms), "followup")

    def _best(self, report, asked_symptoms):
        skip = {q.id for q in BY_SYMPTOM.values() if not self._eligible(q, report)}
        ranked = self.policy.rank(report, asked_symptoms | set(self.asked) | skip)
        return ranked[0].question if ranked else None

    def _eligible(self, q, report) -> bool:
        return q.symptom != Symptom.BLEEDING_IN_PREGNANCY or self._could_be_pregnant(report)

    def _could_be_pregnant(self, report) -> bool:
        return self.sex != "M" and report.age_group in (AgeGroup.ADULT, None) and report.pregnant is not False

    def _mark(self, q, stage):
        if q is not None:
            self._stage[q.id] = stage
        return q

    def _count(self, stage: str) -> int:
        return sum(1 for qid in self.asked if self._stage.get(qid) == stage)


def _with(report: SymptomReport, symptom: Symptom) -> SymptomReport:
    hypothetical = report.model_copy(deep=True)
    hypothetical.add_symptoms([symptom])
    return hypothetical


def _age(value) -> AgeGroup | None:
    if isinstance(value, AgeGroup):
        return value
    try:
        return AgeGroup(value) if value else None
    except ValueError:
        return None
