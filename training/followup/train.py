"""Train the follow-up question model and write triage/followup/model.json.

    pip install -r training/followup/requirements.txt
    python training/followup/download_datasets.py
    python training/followup/train.py

1. Load both datasets and map their symptoms onto the app's symptom codes
   (symptom_map.py). Rows with no mapped symptom are dropped. Each dataset gets
   the same total weight, so the small tropical-disease set isn't drowned out.
   The mapped rows are saved to data/processed/symptom_patterns.csv.
2. Train two candidate models of P(symptom | other symptoms answered yes /
   answered no / not asked), hiding answers at random during training because in
   a real call most symptoms haven't been asked yet:
   - "logistic": one small logistic regression per symptom (readable weights)
   - "mlp": one small neural network scoring all symptoms at once (can learn
     combinations, shares what it learns across rare symptoms)
3. Evaluate on held-out rows: AUC per code, and a simulated intake where the
   caller names one symptom, the danger signs are asked, then K follow-ups are
   chosen by (a) the trained policy, (b) the same policy with base rates instead
   of the trained model (shows what training itself adds), (c) most-common-first,
   (d) random. Scored against the tier the rules engine gives with every symptom known.
4. Keep the model that agrees with the full-information tier more often (on a
   tie, the logistic one, because clinicians can audit its weights) and export
   it as plain JSON with both models' metrics and the dataset checksums. No ML
   libraries are needed at runtime.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.neural_network import MLPClassifier

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from symptom_map import DHIVYESHRK, ITACHI  # noqa: E402

from triage.followup.bank import BANK, BY_SYMPTOM, DANGER_SIGNS  # noqa: E402
from triage.followup.model import DEFAULT_PATH, SymptomModel  # noqa: E402
from triage.followup.policy import FollowUpPolicy  # noqa: E402
from triage.rules.engine import decide  # noqa: E402
from triage.schema import AgeGroup, Symptom, SymptomReport  # noqa: E402

RAW = HERE / "data" / "raw"
PROCESSED = HERE / "data" / "processed"
CODES = [s for s in Symptom]
INDEX = {s: i for i, s in enumerate(CODES)}
MIN_POSITIVE_PATTERNS = 20  # fewer distinct examples than this: use the base rate only


# --- 1. data -------------------------------------------------------------------------


def load_dhivyeshrk(path: Path) -> Counter:
    patterns: Counter = Counter()
    with path.open(newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        cols = [(i, DHIVYESHRK[name.strip()]) for i, name in enumerate(header) if name.strip() in DHIVYESHRK]
        for row in reader:
            codes = frozenset(code for i, code in cols if i < len(row) and row[i] == "1")
            if codes:
                patterns[codes] += 1
    return patterns


def load_itachi(path: Path) -> Counter:
    patterns: Counter = Counter()
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            names = (s.strip() for s in row["symptoms"].split(","))
            codes = frozenset(ITACHI[n] for n in names if n in ITACHI)
            if codes:
                patterns[codes] += 1
    return patterns


def load_all() -> tuple[np.ndarray, np.ndarray, dict]:
    sources = {
        "diseases_and_symptoms": load_dhivyeshrk(RAW / "dhivyeshrk_diseases_symptoms.csv"),
        "disease_symptom_description": load_itachi(RAW / "itachi_disease_symptoms.csv"),
    }
    rows, weights, stats = [], [], {}
    PROCESSED.mkdir(parents=True, exist_ok=True)
    with (PROCESSED / "symptom_patterns.csv").open("w", newline="") as f:
        out = csv.writer(f)
        out.writerow(["dataset", "count", "symptoms"])
        for name, patterns in sources.items():
            total = sum(patterns.values())
            stats[name] = {"rows_with_mapped_symptoms": total, "distinct_patterns": len(patterns)}
            for codes, count in patterns.items():
                vec = np.zeros(len(CODES), dtype=bool)
                vec[[INDEX[c] for c in codes]] = True
                rows.append(vec)
                weights.append(0.5 * count / total)  # each dataset sums to 0.5
                out.writerow([name, count, ";".join(sorted(c.value for c in codes))])
    return np.array(rows), np.array(weights), stats


# --- 2. training ---------------------------------------------------------------------


def masked_copies(patterns: np.ndarray, weights: np.ndarray, copies: int, rng: np.random.Generator):
    """Each copy hides a random share (30-95%) of the answers, like a call in progress."""
    reps = np.repeat(patterns, copies, axis=0)
    w = np.repeat(weights, copies)
    w = w / w.mean()  # mean 1, so regularisation strength doesn't depend on the weighting
    hidden_share = rng.uniform(0.3, 0.95, size=(len(reps), 1))
    known = rng.random(reps.shape) > hidden_share
    return reps, reps & known, ~reps & known, w


def prior_of(patterns, weights) -> dict:
    return {c.value: round(float(np.average(patterns[:, i], weights=weights)), 5) for c, i in INDEX.items()}


def train_logistic(patterns, weights, rng, copies: int):
    truth, yes, no, w = masked_copies(patterns, weights, copies, rng)
    models, skipped = {}, []
    for c, i in INDEX.items():
        others = [j for j in range(len(CODES)) if j != i]
        if len({tuple(p) for p in patterns[patterns[:, i]]}) < MIN_POSITIVE_PATTERNS:
            skipped.append(c.value)
            continue
        X = np.hstack([yes[:, others], no[:, others]]).astype(np.float32)
        clf = LogisticRegression(C=1.0, max_iter=2000)
        clf.fit(X, truth[:, i], sample_weight=w)
        coef = clf.coef_[0]
        models[c.value] = {
            "bias": round(float(clf.intercept_[0]), 4),
            "yes": {CODES[j].value: round(float(coef[k]), 4) for k, j in enumerate(others) if abs(coef[k]) > 1e-3},
            "no": {CODES[j].value: round(float(coef[k + len(others)]), 4)
                   for k, j in enumerate(others) if abs(coef[k + len(others)]) > 1e-3},
        }
    return {"type": "logistic", "prior": prior_of(patterns, weights), "models": models}, skipped


def train_mlp(patterns, weights, rng, copies: int, hidden: int, seed: int):
    truth, yes, no, w = masked_copies(patterns, weights, copies, rng)
    clf = MLPClassifier(hidden_layer_sizes=(hidden,), activation="relu", alpha=1e-4, batch_size=512,
                        learning_rate_init=1e-3, max_iter=40, random_state=seed)
    clf.fit(np.hstack([yes, no]).astype(np.float32), truth, sample_weight=w)
    r = lambda a: [round(float(v), 4) for v in a]  # noqa: E731
    return {
        "type": "mlp",
        "prior": prior_of(patterns, weights),
        "mlp": {
            "inputs": [["yes", c.value] for c in CODES] + [["no", c.value] for c in CODES],
            "outputs": [c.value for c in CODES],
            "w1_by_unit": [r(col) for col in clf.coefs_[0].T],
            "b1": r(clf.intercepts_[0]),
            "w2_by_output": [r(col) for col in clf.coefs_[1].T],
            "b2": r(clf.intercepts_[1]),
        },
    }


# --- 3. evaluation -------------------------------------------------------------------


def auc_per_code(model: SymptomModel, patterns, weights, rng) -> dict:
    truth, yes, no, w = masked_copies(patterns, weights, 2, rng)
    out = {}
    for c, i in INDEX.items():
        if (model.kind == "logistic" and c.value not in model.models) or truth[:, i].all() or not truth[:, i].any():
            continue
        p = [model.p_yes(c, {CODES[j] for j in np.flatnonzero(y) if j != i}, {CODES[j] for j in np.flatnonzero(n) if j != i})
             for y, n in zip(yes, no)]
        out[c.value] = round(float(roc_auc_score(truth[:, i], p, sample_weight=w)), 3)
    return out


def simulate(policy_name, pick, cases, k):
    agree = under = found = 0
    for truth, age, days, complaint, seed in cases:
        report = SymptomReport(symptoms=[complaint], age_group=age, duration_days=days)
        asked = set()
        for s in DANGER_SIGNS:  # always asked first, as in the real policy
            asked.add(BY_SYMPTOM[s].id)
            if s in truth:
                report.add_symptoms([s])
        for _ in range(k):
            q = pick(report, asked, random.Random(seed + len(asked)))
            if q is None:
                break
            asked.add(q.id)
            if q.symptom in truth:
                report.add_symptoms([q.symptom])
                found += 1
        full = decide(SymptomReport(symptoms=list(truth), age_group=age, duration_days=days)).tier.rank
        got = decide(report).tier.rank
        agree += got == full
        under += got < full
    n = len(cases)
    return {"policy": policy_name, "followups": k, "tier_agreement": round(agree / n, 4),
            "under_triage": round(under / n, 4), "extra_symptoms_found_per_call": round(found / n, 3)}


def evaluate_policies(model: SymptomModel, prior: dict, patterns, weights, n_cases: int, seed: int):
    rng = random.Random(seed)
    idx = rng.choices(range(len(patterns)), weights=weights, k=n_cases)
    cases = []
    for i in idx:
        truth = {CODES[j] for j in np.flatnonzero(patterns[i])}
        non_danger = sorted(truth - set(DANGER_SIGNS), key=lambda s: s.value) or sorted(truth, key=lambda s: s.value)
        cases.append((truth, rng.choice(list(AgeGroup)), rng.choice([1, 3, 8, 15]), rng.choice(non_danger), rng.randrange(10**9)))

    trained = FollowUpPolicy(model, max_followups=99)
    base_rate = FollowUpPolicy(SymptomModel({"prior": prior, "models": {}}), max_followups=99)
    by_prior = [q for q in sorted(BANK, key=lambda q: -prior.get(q.symptom.value, 0)) if q.symptom not in DANGER_SIGNS]

    def pick_trained(report, asked, _):
        ranked = trained.rank(report, asked)
        return ranked[0].question if ranked else None

    def pick_base_rate(report, asked, _):
        ranked = base_rate.rank(report, asked)
        return ranked[0].question if ranked else None

    def pick_common(report, asked, _):
        return next((q for q in by_prior if q.id not in asked and q.symptom not in report.symptoms), None)

    def pick_random(report, asked, r):
        left = [q for q in BANK if q.symptom not in DANGER_SIGNS and q.id not in asked and q.symptom not in report.symptoms]
        return r.choice(left) if left else None

    results = []
    for k in (0, 1, 2, 3, 5):
        for name, pick in (("trained", pick_trained), ("rules_+_base_rate", pick_base_rate),
                           ("most_common_first", pick_common), ("random", pick_random)):
            if k == 0 and name != "trained":
                continue
            results.append(simulate("danger_signs_only" if k == 0 else name, pick, cases, k))
    return results


# --- 4. main -----------------------------------------------------------------------------


def report(name, auc, sim):
    print(f"  [{name}] AUC per symptom:", ", ".join(f"{k} {v}" for k, v in sorted(auc.items(), key=lambda x: -x[1])))
    print(f"  {'policy':<20}{'follow-ups':>11}{'tier agreement':>16}{'under-triage':>14}{'found/call':>12}")
    for r in sim:
        print(f"  {r['policy']:<20}{r['followups']:>11}{r['tier_agreement']:>16.1%}{r['under_triage']:>14.1%}"
              f"{r['extra_symptoms_found_per_call']:>12}")


def score(sim) -> float:
    """Tier agreement of the trained policy with 3 follow-ups: what the phone line uses."""
    return next(r["tier_agreement"] for r in sim if r["policy"] == "trained" and r["followups"] == 3)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_PATH))
    parser.add_argument("--model", choices=["best", "logistic", "mlp"], default="best",
                        help="which model to export (best = compare both on held-out data)")
    parser.add_argument("--hidden", type=int, default=32, help="hidden units for the mlp")
    parser.add_argument("--copies", type=int, default=4, help="masked copies per pattern")
    parser.add_argument("--cases", type=int, default=3000, help="simulated calls for evaluation")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    rng = np.random.default_rng(args.seed)

    print("loading datasets...")
    patterns, weights, stats = load_all()
    order = rng.permutation(len(patterns))
    split = int(0.8 * len(order))
    train_idx, test_idx = order[:split], order[split:]
    print(f"  {len(patterns):,} distinct symptom patterns ({len(train_idx):,} train / {len(test_idx):,} test)")

    candidates, skipped = {}, []
    if args.model in ("best", "logistic"):
        print("training logistic (one per symptom)...")
        candidates["logistic"], skipped = train_logistic(patterns[train_idx], weights[train_idx], rng, args.copies)
        print(f"  base rate only (too few examples): {', '.join(skipped) or 'none'}")
    if args.model in ("best", "mlp"):
        print(f"training mlp (one network, {args.hidden} hidden units)...")
        candidates["mlp"] = train_mlp(patterns[train_idx], weights[train_idx], rng, args.copies, args.hidden, args.seed)

    print("evaluating on held-out patterns...")
    metrics = {}
    for name, data in candidates.items():
        model = SymptomModel(data)
        auc = auc_per_code(model, patterns[test_idx], weights[test_idx], np.random.default_rng(args.seed))
        sim = evaluate_policies(model, data["prior"], patterns[test_idx], weights[test_idx], args.cases, args.seed)
        metrics[name] = {"auc": auc, "simulation": sim}
        report(name, auc, sim)

    # The mlp must beat the logistic model by more than a point (well above the
    # simulation's noise) to replace it; otherwise keep the auditable one.
    chosen = "logistic" if "logistic" in candidates else "mlp"
    if "mlp" in candidates and "logistic" in candidates and \
            score(metrics["mlp"]["simulation"]) > score(metrics["logistic"]["simulation"]) + 0.01:
        chosen = "mlp"
    print(f"exporting {chosen} (trained policy, 3 follow-ups: "
          + ", ".join(f"{n} {score(m['simulation']):.1%}" for n, m in metrics.items()) + ")")

    lock = RAW / "datasets.lock.json"
    data = candidates[chosen]
    data.update({
        "version": 1,
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "features": "per symptom: answered yes / answered no (unasked = neither)",
        "training": {"datasets": json.loads(lock.read_text()) if lock.exists() else {}, "stats": stats,
                     "distinct_patterns": len(patterns), "masked_copies": args.copies, "seed": args.seed,
                     "sklearn": sklearn.__version__, "base_rate_only": skipped if chosen == "logistic" else []},
        "metrics": {"chosen": chosen, "simulated_calls": args.cases, **metrics},
    })
    Path(args.out).write_text(json.dumps(data, indent=1) + "\n")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
