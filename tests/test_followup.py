from triage.followup import BANK, DANGER_SIGNS, NEW_PROMPTS, FollowUpPolicy, SymptomModel
from triage.followup.bank import BY_SYMPTOM
from triage.schema import AgeGroup, Symptom as S, SymptomReport

DANGER_IDS = {BY_SYMPTOM[s].id for s in DANGER_SIGNS}

# Hand-made model: fever makes stiff neck and headache likely; headache is the more
# likely of the two, but only stiff neck (with fever) raises the tier to emergency.
TOY = SymptomModel({
    "type": "logistic",
    "prior": {"cough": 0.3},
    "models": {
        "stiff_neck": {"bias": -3.0, "yes": {"fever": 2.5}, "no": {}},
        "headache": {"bias": -1.0, "yes": {"fever": 2.0}, "no": {"stiff_neck": -0.5}},
    },
})


def report(*symptoms, **kw):
    return SymptomReport(symptoms=list(symptoms), age_group=kw.get("age", AgeGroup.ADULT), duration_days=1)


def test_every_symptom_has_one_question_with_swahili():
    assert {q.symptom for q in BANK} == set(S)
    assert len({q.id for q in BANK}) == len(BANK)
    assert all(q.text("sw") != q.prompt for q in BANK)
    assert all(q.id.startswith("fu_") for q in NEW_PROMPTS)


def test_danger_signs_come_first_in_fixed_order():
    policy = FollowUpPolicy(TOY)
    asked = set()
    order = []
    for _ in DANGER_SIGNS:
        q = policy.next_question(report(S.FEVER), asked)
        order.append(q.symptom)
        asked.add(q.id)
    assert order == list(DANGER_SIGNS)


def test_a_symptom_that_could_change_the_tier_beats_a_more_likely_one():
    policy = FollowUpPolicy(TOY)
    ranked = policy.rank(report(S.FEVER), DANGER_IDS)
    top = ranked[0]
    headache = next(r for r in ranked if r.question.symptom == S.HEADACHE)
    assert top.question.symptom == S.STIFF_NECK and top.tiers_raised == 2
    assert headache.p_yes > top.p_yes  # more likely, but can't change the outcome


def test_no_answers_count_as_evidence():
    no_stiff = TOY.p_yes(S.HEADACHE, {S.FEVER}, {S.STIFF_NECK})
    unknown = TOY.p_yes(S.HEADACHE, {S.FEVER}, set())
    assert no_stiff < unknown


def test_stops_after_max_followups():
    policy = FollowUpPolicy(TOY, max_followups=1)
    asked = set(DANGER_IDS) | {BY_SYMPTOM[S.STIFF_NECK].id}
    assert policy.next_question(report(S.FEVER), asked) is None


def test_unlikely_questions_are_asked_only_if_they_could_change_the_tier():
    policy = FollowUpPolicy(SymptomModel({"prior": {}, "models": {}}))  # every P(yes) = 0
    ranked = policy.rank(report(S.COUGH), set(DANGER_IDS))
    assert ranked and all(r.tiers_raised > 0 for r in ranked)
    assert S.HEADACHE not in {r.question.symptom for r in ranked}  # can't change a cough's tier


def test_ranking_is_expected_change_to_the_outcome():
    ranks = lambda prior: [r.question.symptom for r in  # noqa: E731
                           FollowUpPolicy(SymptomModel({"prior": prior, "models": {}})).rank(report(S.FEVER), set(DANGER_IDS))]
    # rash (fever + rash -> urgent) vs stiff neck (fever + stiff neck -> emergency)
    assert ranks({"rash": 0.6, "stiff_neck": 0.01})[0] == S.RASH  # emergency possible but very unlikely
    assert ranks({"rash": 0.6, "stiff_neck": 0.4})[0] == S.STIFF_NECK  # both plausible: the emergency first


def test_shipped_model_loads_and_gives_probabilities():
    model = SymptomModel.load()
    assert model is not None, "run training/followup/train.py"
    for symptom in S:
        p = model.p_yes(symptom, {S.FEVER}, {S.COUGH})
        assert 0.0 <= p <= 1.0
    assert "simulation" in model.data["metrics"][model.data["metrics"]["chosen"]]


def test_mlp_format_runs_without_ml_libraries():
    codes = [s.value for s in S]
    net = SymptomModel({
        "type": "mlp",
        "prior": {},
        "mlp": {
            "inputs": [["yes", c] for c in codes] + [["no", c] for c in codes],
            "outputs": codes,
            "w1_by_unit": [[1.0 if (k == "yes" and c == "fever") else 0.0 for k, c in
                            [["yes", c] for c in codes] + [["no", c] for c in codes]]],
            "b1": [0.0],
            "w2_by_output": [[3.0] if c == "stiff_neck" else [0.0] for c in codes],
            "b2": [-2.0 if c == "stiff_neck" else -5.0 for c in codes],
        },
    })
    assert net.p_yes(S.STIFF_NECK, {S.FEVER}, set()) > net.p_yes(S.STIFF_NECK, set(), set())


def test_interview_never_asks_pregnancy_questions_when_impossible():
    from triage.followup import Interview

    for sex, age in [("M", "adult"), ("F", "child"), ("F", "elderly")]:
        iv = Interview(SymptomModel({"prior": {}, "models": {}}) and FollowUpPolicy(SymptomModel({"prior": {}, "models": {}})),
                       sex=sex, age_group=age)
        iv.add_mentioned([S.FEVER])
        while (q := iv.next_question()) is not None:
            iv.answer(q.id, {"duration": "1", "severity": "1"}.get(q.id, "2"))
        assert "pregnant" not in iv.asked and "fu_bleeding_in_pregnancy" not in iv.asked, (sex, age)


def test_pregnant_caller_gets_the_bleeding_check():
    from triage.followup import Interview

    iv = Interview(FollowUpPolicy(SymptomModel({"prior": {}, "models": {}})), sex="F", age_group="adult")
    iv.add_mentioned([S.ABDOMINAL_PAIN])
    while (q := iv.next_question()) is not None:
        iv.answer(q.id, {"duration": "1", "severity": "1", "pregnant": "1"}.get(q.id, "2"))
    assert iv.asked[iv.asked.index("pregnant") + 2] == "fu_bleeding_in_pregnancy"  # after severity
