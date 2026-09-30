# Medical Logic — how Med-Intake classifies callers

> **Hackathon demo content.** Rules are loosely modelled on WHO IMCI general
> danger signs. A clinician must review and sign off before any real-world use.
> The engine never diagnoses — it only routes: **emergency / urgent / self-care**.

## Pipeline

```
speech path:  caller describes the problem → STT (→ translation) → symptoms found ─┐
keypad path:  ──────────────────────────────────────────────────────────────────────┴→ interview (keypad) → rules engine → tier → routing
```

| Stage | Speech langs (en, sw; lg, nyn when Sunbird is on) | Keypad langs (lg, nyn without Sunbird) |
|---|---|---|
| Capture | Free speech, Record 15s, STT (Sunbird first for sw/lg/nyn) | — |
| Extract | lg/nyn: Sunbird machine translation to English first. `triage.keywords.symptoms_in` (danger-sign + EN/SW keyword patterns, negation-aware), plus an LLM's reading if `LLM_BASE_URL` is set | — |
| Interview | `triage.followup.Interview`: danger signs → (screening if no symptom yet) → how long / pregnant / how bad → emergency checks → up to 2 model-chosen follow-ups | same |
| Decide | `triage.rules.engine.decide()` (rule list) | same |
| Fail-safe | Empty STT → re-ask once → **switch to the keypad questions** (same for a failed translation) | ≥3 invalid keys → incomplete report → **urgent min, never self-care** |

**Neither the LLM nor the trained model decides the tier.** Extraction only finds
a starting point; the trained model (`triage/followup/`) only picks which fixed,
pre-translated question to ask next. All tier boundaries are the rules below.

## The interview (`triage/followup/interview.py`)

1. **Danger signs**, one question each, in IMCI order: convulsions, unconscious,
   difficulty breathing, severe bleeding, unable to drink, vomits everything,
   chest pain. Skipped if already said. Stops at the first emergency.
2. **Screening** (only if no symptom is known yet): fever, cough, diarrhoea,
   vomiting, until one is a yes (max 4). None found → the rules send it to a
   health worker.
3. **What the rules need:** how long (duration rules), pregnant (women of adult
   or unknown age), how bad (severity rule).
4. **Emergency checks:** any question a yes to which would make it an emergency,
   however unlikely: fever → stiff neck, pregnant → bleeding.
5. **Up to 2 follow-ups** chosen by the trained policy: expected change to the
   outcome, P(yes) × (1 + 100 × tiers raised), then likely symptoms.

A call takes about 2.5-2.7 minutes on average (`scripts/estimate_call_time.py`).

## Engine A — `/api/intake` and simulated data only (`backend/app/triage_engine.py`)

Phone calls no longer use this engine. It still backs the `/api/intake` endpoint
and the simulated tickets (`/api/sim/seed`). Flat sets, first match wins:

- `EMERGENCY = {chest pain, difficulty breathing, severe bleeding, unconscious, labour, seizure, stroke}`
- `URGENT = {high fever, dehydration, persistent vomiting, severe pain, fever, cough, diarrhea}`

## Engine B — every phone call (`triage/rules/`)

`decide(report)`: evaluates **every** rule, returns highest tier matched, lists
**all** matched rule ids + reasons (audit trail). Adding a rule can only make
decisions more cautious. No match → `SC_DEFAULT` self-care.

Emergency rules (any one fires): convulsions, unconscious, difficulty
breathing, chest pain, severe bleeding, bleeding in pregnancy, unable to
drink/breastfeed, vomiting everything, fever + stiff neck.

Urgent rules: infant fever, fever ≥2d, fever + rash, elderly fever, blood in
stool, diarrhoea ≥14d, child diarrhoea + vomiting (dehydration), fast
breathing, caller says severe, any symptoms in pregnancy, symptoms ≥7d.

Fail-safe rules (bias to human review): no data, incomplete intake, or
unrecognised symptoms → **urgent** (CHW callback), never self-care.

Early exit: the interview stops at the first EMERGENCY decision instead of asking the rest.

## Tier → action

| Tier | Voice | SMS | Ops |
|---|---|---|---|
| emergency | Closing msg + hangup, ref spoken | Ref SMS immediately | Nearest facility + alert, front of queue |
| urgent | Closing msg + hangup, ref spoken | Ref SMS | CHW callback ticket, facility queue by severity |
| self_care | TTS self-care advice + hangup, ref spoken | Ref SMS | No queue slot; advice logged |

## Follow-up linkage

Every ticket gets `MED-{id}`. Caller quoting a ref on next call preloads
bio + prior summary; new ticket stores `parent_id`. Clinicians see the chain
in the inspector (patient map).
