"""Facility routing + queue engine. Sim data for demo map.

Routing: tier + symptoms + village -> best facility.
- emergency -> nearest hospital with emergency capability, load ignored
- urgent -> nearest capable facility with free queue slots (load-penalised distance)
- self_care -> no facility (CHW advice), facility_id=0
Queues: per-facility, emergency-first ordering, est wait = ahead * avg minutes.
"""
from __future__ import annotations
import math, random
from dataclasses import dataclass, field

@dataclass
class Facility:
    id: int
    name: str
    kind: str  # hospital | health_center | clinic
    lat: float
    lng: float
    capabilities: set[str] = field(default_factory=set)
    slots: int = 20          # queue capacity
    avg_minutes: int = 15    # per patient

# Sim facilities around Kampala (approx real locations, demo data).
FACILITIES: list[Facility] = [
    Facility(1, "Mulago National Hospital", "hospital", 0.3361, 32.5763,
             {"emergency", "surgery", "maternity", "pediatrics", "general"}, 60, 20),
    Facility(2, "Kawempe Health Centre", "health_center", 0.3792, 32.5575,
             {"maternity", "pediatrics", "general"}, 30, 15),
    Facility(3, "Kiruddu Hospital", "hospital", 0.2850, 32.5840,
             {"emergency", "general", "pediatrics"}, 40, 18),
    Facility(4, "Kisenyi Health Centre", "health_center", 0.3133, 32.5675,
             {"general", "pediatrics"}, 25, 12),
    Facility(5, "Kiswa Community Clinic", "clinic", 0.3220, 32.6100,
             {"general"}, 15, 10),
    Facility(6, "Naguru Clinic", "clinic", 0.3470, 32.6020,
             {"general", "pediatrics"}, 15, 10),
]

# Village -> approx coords (demo mapping; callers give village names freely).
VILLAGES: dict[str, tuple[float, float]] = {
    "kawempe": (0.3792, 32.5575), "kisenyi": (0.3133, 32.5675),
    "kisugu": (0.3050, 32.6000), "naguru": (0.3470, 32.6020),
    "makindye": (0.2920, 32.5800), "kasubi": (0.3300, 32.5500),
}

def _km(a: tuple[float, float], b: tuple[float, float]) -> float:
    R = 6371.0
    dLa, dLo = math.radians(b[0] - a[0]), math.radians(b[1] - a[1])
    h = math.sin(dLa / 2) ** 2 + math.cos(math.radians(a[0])) * math.cos(math.radians(b[0])) * math.sin(dLo / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))

def caller_coords(village: str) -> tuple[float, float]:
    v = (village or "").strip().lower()
    if v in VILLAGES: return VILLAGES[v]
    rnd = random.Random(sum(map(ord, v)) or 1)
    return (0.30 + rnd.random() * 0.08, 32.55 + rnd.random() * 0.06)

def _need(symptoms: list[str]) -> set[str]:
    s = " ".join(symptoms).lower()
    need = set()
    if any(w in s for w in ("labour", "pregnancy", "bleed")): need.add("maternity")
    if any(w in s for w in ("seizure", "convulsion", "unconscious", "chest", "breath", "bleed")): need.add("emergency")
    if any(w in s for w in ("fever", "cough", "diarrhea", "rash")): need.add("pediatrics")
    need.add("general")
    return need

def route(tier: str, symptoms: list[str], village: str, loads: dict[int, int]) -> tuple[int, str]:
    """Returns (facility_id, reason). facility_id=0 means no routing (self-care)."""
    if tier == "self_care": return 0, "self-care: no facility needed"
    me = caller_coords(village)
    need = _need(symptoms)
    cands = [f for f in FACILITIES if need <= f.capabilities or (tier == "urgent" and "general" in f.capabilities)]
    if "maternity" in need:  # never send pregnancy cases somewhere without maternity
        cands = [f for f in cands if "maternity" in f.capabilities] or [f for f in FACILITIES if "maternity" in f.capabilities]
    if tier == "emergency":
        cands = [f for f in cands if "emergency" in f.capabilities] or FACILITIES[:1]
        best = min(cands, key=lambda f: _km(me, (f.lat, f.lng)))
        return best.id, f"emergency: nearest emergency-capable ({best.name}, {_km(me,(best.lat,best.lng)):.1f}km)"
    scored = []
    for f in cands:
        load = loads.get(f.id, 0)
        if load >= f.slots: continue
        score = _km(me, (f.lat, f.lng)) + (load / max(f.slots, 1)) * 10.0
        if f.kind == "health_center": score -= 1.0  # prefer HC over hospital for urgent
        scored.append((score, f))
    if not scored:
        best = min(FACILITIES, key=lambda f: _km(me, (f.lat, f.lng)))
        return best.id, f"all queues full: overflow to nearest ({best.name})"
    scored.sort(key=lambda t: t[0])
    best = scored[0][1]
    return best.id, f"urgent: best fit by distance+load ({best.name})"

def order_queue(tickets: list[dict]) -> list[dict]:
    rank = {"emergency": 0, "urgent": 1, "self_care": 2}
    return sorted(tickets, key=lambda t: (rank.get(t.get("tier", "self_care"), 2), t.get("id", 0)))

FIRST = ["Amina", "Brian", "Grace", "Moses", "Sarah", "Peter", "Ruth", "James", "Agnes", "Tom"]
LAST = ["N.", "K.", "M.", "S.", "A.", "B."]
SIM_SYM = [["chest_pain"], ["fever", "cough"], ["cough"], ["diarrhea", "vomiting"], ["difficulty_breathing"],
           ["fever"], ["severe_bleeding"], ["headache"], ["rash", "fever"], ["abdominal_pain"]]

def sim_ticket(i: int) -> dict:
    rnd = random.Random(1000 + i)
    syms = rnd.choice(SIM_SYM)
    vil = rnd.choice(list(VILLAGES))
    return {"caller": f"+2567{rnd.randint(10000000, 79999999)}",
            "lang": rnd.choice(["en", "en", "sw", "lg", "nyn"]),
            "symptoms": syms, "flags": {"severe": any(s in ("chest_pain", "difficulty_breathing", "severe_bleeding") for s in syms)},
            "name": f"{rnd.choice(FIRST)} {rnd.choice(LAST)}",
            "sex": rnd.choice(["M", "F"]), "age_band": rnd.choice(["0-4", "5-17", "18-59", "18-59", "60+"]),
            "village": vil.title(), "transcript": "", "summary": ""}
