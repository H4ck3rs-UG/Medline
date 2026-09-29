# Med-Intake (Next.js + FastAPI) — ported from SavaWatch
Stack: FastAPI + SQLite/Postgres tickets, Next.js dashboard, AT Voice `/voice`, rules engine decides tier.
Run BE: `pip install -r requirements.txt && uvicorn app.main:app --reload --app-dir backend` (port 8000)
Run FE: `cd frontend && npm i && NEXT_PUBLIC_API=http://localhost:8000 npm run dev`
AT Voice callback -> `https://<tunnel>/voice`. Endpoints: POST /api/intake, GET /api/tickets, POST /api/tickets/{id}, POST /voice.
Languages: keypress 1 English, 2 Kiswahili (speech path), 3 Luganda, 4 Runyankole (keypad menu from `triage.dtmf`, run through `triage` rules engine). Set `AUDIO_BASE_URL` to where the recorded clips live (`<lang>/<id>.mp3`, `all/language_menu.mp3`; list them with `python examples/export_recording_script.py`); languages in `RECORDED_LANGS` play clips, others use TTS. The backend imports the `triage` package from the repo root (or `pip install -e .` there). Dashboard has an English/Kiswahili switch.
