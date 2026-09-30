# Med-Intake Test Plan

## 1. Backend health

- [ ] `GET /health` -> `{"ok":true}`
```bash
curl http://localhost:8000/health
```

## 2. Intake API

- [ ] Emergency symptoms -> tier `emergency`
```bash
curl -X POST http://localhost:8000/api/intake -H "Content-Type: application/json" \
  -d '{"caller":"+256700000001","lang":"en","symptoms":["chest_pain"],"flags":{"severe":true}}'
```
- [ ] Mild symptoms -> tier `self_care`
```bash
curl -X POST http://localhost:8000/api/intake -H "Content-Type: application/json" \
  -d '{"caller":"+256700000002","lang":"en","symptoms":["cough"],"flags":{}}'
```
- [ ] Empty body -> defaults, no 500
```bash
curl -X POST http://localhost:8000/api/intake -H "Content-Type: application/json" -d '{}'
```

## 3. Tickets API

- [ ] `GET /api/tickets` sorted emergency > urgent > self_care
- [ ] `POST /api/tickets/{id}` `{status:"closed"}` -> `{"ok":true}`
- [ ] Bad id -> 404 `"no ticket"`
```bash
curl http://localhost:8000/api/tickets
curl -X POST http://localhost:8000/api/tickets/1 -H "Content-Type: application/json" -d '{"status":"closed"}'
curl -X POST http://localhost:8000/api/tickets/99999 -H "Content-Type: application/json" -d '{"status":"closed"}'
```

## 4. Voice callback

- [ ] New call (no sid) -> language menu XML
```bash
curl -X POST http://localhost:8000/voice -d 'sessionId=&callerNumber=%2B256700000001&isActive=1'
```
- [ ] Press 1 -> English -> `describe_symptoms` + Record
```bash
curl -X POST http://localhost:8000/voice -d 'sessionId=<SID>&dtmfDigits=1&isActive=1'
```
- [ ] Press 3 -> Luganda -> keypad menu, no Record
```bash
curl -X POST http://localhost:8000/voice -d 'sessionId=<SID2>&dtmfDigits=3&isActive=1'
```
- [ ] Press 0 anytime -> transfer XML with `<Dial`
- [ ] Invalid key x3 -> still triages (never hangs, never self_care on incomplete)
- [ ] `isActive=0` -> empty Response, no crash
- [ ] Response `Content-Type: application/xml`

## 5. Triage engine

- [ ] Danger signs -> `EMERGENCY`, stops DTMF early
- [ ] Incomplete DTMF report -> `urgent` minimum, never `self_care`
- [ ] Keyword fallback maps `homa`->fever, `kikohozi`->cough without LLM
- [ ] LLM down/slow -> fallback fires, call continues (check logs for `llm extract fail`)

## 6. Frontend dashboard

- [ ] Loads at http://localhost:3000, no 500
- [ ] Table/List shows tickets, grouped emergency first
- [ ] Emergency row has pulsing StatusDot
- [ ] Tier filter (All/Emergency/Urgent/Self-care) filters rows
- [ ] EN/SW switch persists after reload (localStorage)
- [ ] Close button -> status flips, row moves/token changes
- [ ] Polls every 3s: create ticket via curl -> appears without refresh
- [ ] Empty DB -> EmptyState, no crash
- [ ] BE down -> page still renders (no infinite spinner)
- [ ] Narrow viewport (<=1024px) -> inspector hides, rows full width

## 7. Theme / styling

- [ ] Light-blue clinic bg visible (`#eaf3fe` body)
- [ ] No unstyled flash on load (reset.css + astryx.css + neutral.css)
- [ ] `pnpm exec tsc --noEmit` clean
- [ ] `pnpm exec astryx doctor` peers satisfied
- [ ] No raw `<div>` layout, no hex/px in page code (except breakpoint string)
- [ ] Rebuilt theme after any `neutralTheme.ts` edit: `pnpm exec astryx theme build src/themes/neutral/neutralTheme.ts`

## 8. Voice E2E (sandbox, needs tunnel)

- [ ] `PUBLIC_URL` set, tunnel live
- [ ] AT callback = `https://<tunnel>/voice`, POST
- [ ] Call 1 (English): speak symptoms -> ticket appears with lang `en`
- [ ] Call 2 (Luganda): keypad answers -> ticket appears with lang `lg`
- [ ] Hangup mid-menu -> no orphan crash, session stays safe
- [ ] Dashboard updates within ~3s of hangup

## 9. Regression (run every change)

```bash
cd backend && python -m pytest 2>&1 | tail -5  # if tests exist
cd ../frontend && pnpm exec tsc --noEmit
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/intake -H "Content-Type: application/json" -d '{"caller":"smoke","lang":"en","symptoms":["cough"],"flags":{}}'
```
