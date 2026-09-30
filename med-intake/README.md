# Med-Intake

Voice triage intake. Caller dials -> AT Voice -> rules engine tiers -> ticket -> dashboard.

Stack: FastAPI + SQLite + Next.js 14 + Africa's Talking Voice.

## What it does

- `/voice` handles call: lang select (1=en, 2=sw, 3=lg, 4=nyn), symptom capture (speech or DTMF keypad), triage, closing msg, hangup.
- `POST /api/intake` creates ticket programmatically.
- `GET /api/tickets` lists tickets sorted: emergency > urgent > self_care.
- Dashboard polls every 3s, EN/SW switch, close ticket button.
- Langs in `RECORDED_LANGS` play mp3 clips from `AUDIO_BASE_URL`, others use TTS.

## Prereqs

- Python 3.11+, Node 18+, `pip`, `npm`
- Optional: ngrok/cloudflared for public `/voice` URL, AT sandbox account

## Quick run (local, no voice)

1. Backend:
```bash
cd med-intake/backend
cp .env.example .env   # edit if needed
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# check: http://localhost:8000/health -> {"ok":true}
```

2. Frontend (new terminal):
```bash
cd med-intake/frontend
npm i
NEXT_PUBLIC_API=http://localhost:8000 npm run dev
# open: http://localhost:3000
```

3. Test intake:
```bash
curl -X POST http://localhost:8000/api/intake \
  -H "Content-Type: application/json" \
  -d '{"caller":"+256700000001","lang":"en","symptoms":["chest_pain"],"flags":{}}'
curl http://localhost:8000/api/tickets
```

## Full run (with voice)

1. Expose backend:
```bash
ngrok http 8000
# copy https URL -> set PUBLIC_URL=https://<you>.ngrok.io in backend/.env
```

2. AT dashboard -> Voice -> callback URL: `https://<you>.ngrok.io/voice`, method POST.

3. Call sandbox number, press 1-4, answer prompts. Ticket appears in dashboard.

4. Recorded audio (optional):
```bash
python examples/export_recording_script.py  # lists clips needed
# host clips at AUDIO_BASE_URL/<lang>/<id>.mp3 + all/language_menu.mp3
# set AUDIO_BASE_URL=... , RECORDED_LANGS=lg,nyn in backend/.env
```

## Config

Backend reads `backend/.env` (see `.env.example`). Keys:
- `AT_USERNAME`, `AT_API_KEY` — blank = dry-run, no SMS sent
- `DB_URL` — default `sqlite:///./tickets.db`
- `PORT` — default `8000`
- `PUBLIC_URL` — tunnel URL for AT callbacks
- `AUDIO_BASE_URL`, `RECORDED_LANGS` — recorded prompts vs TTS
- `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL` — optional, fallback = builtin intent engine

Frontend env: `NEXT_PUBLIC_API=http://localhost:8000`

## Endpoints

| Method | Path | Use |
|---|---|---|
| GET | `/health` | BE alive check |
| POST | `/api/intake` | body: `{caller, lang, symptoms[], flags{}}` -> `{id, tier, reason, confidence, action}` |
| GET | `/api/tickets` | list, tier-sorted |
| POST | `/api/tickets/{id}` | body: `{status:"closed"}` |
| POST | `/voice` | AT callback, form: `sessionId, callerNumber, dtmfDigits, recordingUrl, isActive` -> XML |

Tiers: `emergency` = refer facility + alert, `urgent` = CHW callback, `self_care` = TTS advice.

## Troubleshoot

- FE empty table -> BE down or wrong `NEXT_PUBLIC_API`. Check `/health`.
- CORS fail -> BE must run with CORS `*` (already in `main.py:24-25`).
- DB locked -> SQLite single-writer. Restart uvicorn, delete `tickets.db` to reset.
- `/voice` 404 from AT -> tunnel dead or wrong callback path. Must end `/voice`, POST.
- No audio clips -> `AUDIO_BASE_URL` unset -> falls back TTS. Expected.
- `triage` import error -> run from `med-intake/backend` with `--app-dir backend` equivalent, or `pip install -e .` at repo root containing `triage/` package.
