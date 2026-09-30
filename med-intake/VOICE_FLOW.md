# Voice Call Flow

```
INCOMING CALL (POST /voice, isActive=1)
│
├─ isActive=0 → return empty XML (call ended)
│
└─ new session? (no sid match)
   ├─ YES → START
   │   └─ Play: all/language_menu.mp3 (or TTS)
   │       "Press 1 English, 2 Kiswahili, 3 Luganda, 4 Runyankole"
   │       → action=menu (GetDigits 1 digit)
   │
   └─ NO → TURN
       │
       ├─ lang NOT set yet?
       │   ├─ key=1 → lang=en → SPEECH path
       │   ├─ key=2 → lang=sw → SPEECH path
       │   ├─ key=3 → lang=lg → DTMF path
       │   ├─ key=4 → lang=nyn → DTMF path
       │   └─ invalid → replay language menu
       │
       ├─ key=0 at any point → TRANSFER
       │   └─ Play: connecting_nurse → <Dial +256700300001>
       │
       ├─ SPEECH PATH (en / sw)
       │   ├─ Play: describe_symptoms → action=listen (Record 15s)
       │   ├─ STT text → extract_symptoms()
       │   │   ├─ LLM set? → POST LLM_BASE_URL/chat/completions → {symptoms[], severe, duration_days}
       │   │   └─ else → keyword fallback (INTENTS + SW_SYMPTOMS + SEVERE_WORDS)
       │   └─ → TRIAGE → triage(symptoms, flags)
       │       ├─ emergency → Play closing_emergency → hangup + ticket
       │       ├─ urgent → Play closing_urgent → hangup + ticket
       │       └─ self_care → Play closing_self_care → hangup + ticket
       │
       └─ DTMF PATH (lg / nyn)
           ├─ Play: welcome + Q1 (danger signs first) → action=menu
           ├─ per callback:
           │   ├─ key invalid?
           │   │   ├─ <3 fails → Play invalid_key + repeat Q → menu
           │   │   └─ ≥3 fails → incomplete report → TRIAGE as urgent (CHW callback, never self_care)
           │   ├─ key valid → save answers[q.id]=key
           │   ├─ decide(report).tier == EMERGENCY? → YES → stop early → TRIAGE
           │   ├─ more questions? → YES → Play next Q → menu
           │   └─ NO → TRIAGE → decide(full report)
           │       ├─ emergency → closing_emergency → hangup + ticket
           │       ├─ urgent → closing_urgent → hangup + ticket
           │       └─ self_care → closing_self_care → hangup + ticket
```

## Audio rule

```
lang in RECORDED_LANGS + AUDIO_BASE_URL set?
├─ YES → <Play url="AUDIO_BASE_URL/<lang>/<prompt_id>.mp3">
└─ NO → <Say voice="woman">text</Say>
```

## Ticket write

```
TRIAGE → Ticket(caller=phone, lang, symptoms, tier, reason, confidence)
→ GET /api/tickets shows it, sorted emergency first
```

## Keys

- `LANG_KEYS`: 1=en, 2=sw, 3=lg, 4=nyn
- `NURSE_KEY`: 0 = transfer
- `MAX_INVALID_KEYS`: 3
- Speech langs: en, sw. Keypad langs: lg, nyn.
