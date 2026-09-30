# Medical Logic — how Med-Intake classifies callers

> **Hackathon demo content.** Rules are loosely modelled on WHO IMCI general
> danger signs. A clinician must review and sign off before any real-world use.
> The engine never diagnoses — it only routes: **emergency / urgent / self-care**.

## Pipeline

```
call audio → STT → symptom extraction → rules engine → tier → routing
```

| Stage | Speech langs (en, sw; lg, nyn when Sunbird is on) | Keypad langs (lg, nyn without Sunbird) |
|---|---|---|
| Capture | Free speech, Record 15s, STT (Sunbird first for sw/lg/nyn) | One recorded Q per callback, danger signs first |
| Extract | lg/nyn: Sunbird machine translation to English first. LLM slot fill → keyword fallback (EN + SW map) | Keypresses → `SymptomReport` |
| Decide | `triage_engine.triage()` (flat keyword sets) | `triage.rules.engine.decide()` (rule list) |
| Fail-safe | Empty STT → re-ask once → **switch to the keypad menu** (same for a failed translation) | ≥3 invalid keys → incomplete report → **urgent min, never self-care** |

**LLM never decides tier.** It only extracts `{symptoms[], severe, duration_days}`.
All tier boundaries are deterministic code.

## Engine A — speech path (`backend/app/triage_engine.py`)

Flat sets:

- `EMERGENCY = {chest pain, difficulty breathing, severe bleeding, unconscious, labour, seizure, stroke}`
- `URGENT = {high fever, dehydration, persistent vomiting, severe pain, fever, cough, diarrhea}`

Order (first match wins):

1. `emergency_flag` **or** (EMERGENCY hit **and** severe) → emergency, 95
2. EMERGENCY hit → emergency, 90
3. `urgent_flag` **or** (URGENT hit **and** (duration ≥3d **or** severe)) → urgent, 80
4. URGENT hit → urgent, 70
5. else → self_care, 60

Known gap (audit): keyword fallback emits `bleed / vomit / pain`, which match
neither set exactly (`severe bleeding / persistent vomiting / severe pain`) —
those callers fall through to step 4/5 on the generic word only. Fix: normalise
fallback outputs to set vocabulary.

## Engine B — keypad path (`triage/rules/`)

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

Early exit: menu stops at first EMERGENCY decision instead of asking the rest.

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
