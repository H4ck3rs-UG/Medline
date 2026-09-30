"""The trained part: how likely each unasked symptom is, given the answers so far.

Trained on symptom co-occurrence data (see ``training/followup/``) and shipped as
plain JSON weights, so running it needs no ML libraries. It knows nothing about
diseases and never outputs one: it only estimates
P(symptom present | symptoms answered yes / answered no so far).

Two formats, chosen at training time:
- "logistic": one small logistic regression per symptom (readable weights)
- "mlp": one small neural network that scores every symptom at once
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from triage.schema import Symptom

DEFAULT_PATH = Path(__file__).resolve().parent / "model.json"


def _sigmoid(z: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(min(z, 40.0), -40.0)))


class SymptomModel:
    def __init__(self, data: dict):
        self.data = data
        self.kind = data.get("type", "logistic")
        self.models: dict[str, dict] = data.get("models", {})
        self.prior: dict[str, float] = data.get("prior", {})

    @classmethod
    def load(cls, path: str | Path | None = None) -> SymptomModel | None:
        """The shipped model, or None if it hasn't been trained yet."""
        path = Path(path) if path else DEFAULT_PATH
        if not path.exists():
            return None
        return cls(json.loads(path.read_text()))

    def p_yes(self, symptom: Symptom, yes: set[Symptom], no: set[Symptom]) -> float:
        """P(symptom present | yes answers, no answers). Falls back to the base rate
        for symptoms the data had too few examples of, and to 0 if never seen."""
        if self.kind == "mlp":
            return self._mlp(yes - {symptom}, no - {symptom}).get(symptom.value, self.prior.get(symptom.value, 0.0))
        m = self.models.get(symptom.value)
        if m is None:
            return self.prior.get(symptom.value, 0.0)
        z = m["bias"]
        z += sum(m["yes"].get(s.value, 0.0) for s in yes if s != symptom)
        z += sum(m["no"].get(s.value, 0.0) for s in no if s != symptom)
        return _sigmoid(z)

    def _mlp(self, yes: set[Symptom], no: set[Symptom]) -> dict[str, float]:
        net = self.data["mlp"]
        x = [1.0 if (kind == "yes" and code in {s.value for s in yes}) or (kind == "no" and code in {s.value for s in no})
             else 0.0 for kind, code in net["inputs"]]
        hidden = [max(0.0, b + sum(xi * w for xi, w in zip(x, col))) for b, col in zip(net["b1"], net["w1_by_unit"])]
        return {code: _sigmoid(b + sum(h * w for h, w in zip(hidden, col)))
                for code, b, col in zip(net["outputs"], net["b2"], net["w2_by_output"])}
