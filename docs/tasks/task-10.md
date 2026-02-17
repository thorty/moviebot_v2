# Task 10 — E2E-Härtung + Übergabe

## 1) Kurzüberblick
- Ziel dieses Tasks: Review-fähige Endabnahme mit dokumentiertem Happy Path und Negativtests.
- Ergebnis:
  - E2E-Kernpfad ist als reproduzierbarer lokaler Ablauf dokumentiert.
  - Negativfälle (ohne Token, ungültiger Token, paralleler Conversation-Start) sind testbar und abgedeckt.
  - Übergabe-Artefakte (`tests/`, `readme.md`, `todos.md`) sind finalisiert, ohne Scope-Erweiterung.
- Umgesetzt in:
  - `tests/test_auth_guard.py`
  - `tests/test_conversations_service.py`
  - `tests/test_message_logs_service.py`
  - `readme.md`
  - `todos.md`

## 2) Erklärung für Junior Dev (einfach)
Task 10 ist der Abschluss-Task:

1. Wir prüfen, ob der komplette Produktfluss wirklich zusammen funktioniert:
   - Login/Auth
   - Chat-Request
   - Backend-Antwort
   - Persistenz in Conversations und Message-Logs
2. Zusätzlich prüfen wir Fehlerfälle, damit das System robust ist:
   - Kein Token
   - Defekter Token
   - Mehrere fast gleichzeitige Starts derselben User-Conversation
3. Danach dokumentieren wir den Endstand so, dass Product und Engineering denselben reproduzierbaren Testpfad haben.

Warum wichtig?
- Einzelne Features können grün sein, aber Integration kann trotzdem brechen.
- Task 10 stellt sicher, dass das MVP als Ganzes review- und übergabefähig ist.

## 3) Was du manuell machen musst
1. Lokale Services starten:
   - `docker compose up -d`
   - `supabase start`
2. Migrationen synchronisieren:
   - `supabase db reset`
3. Optional lokal statt Docker:
   - Backend: `uvicorn main:app --reload`
   - Frontend: `cd frontend/web && npm run dev -- --host 0.0.0.0 --port 3000`
4. Mit lokalem Supabase-Testuser im Frontend einloggen (`http://localhost:3000`).

## 4) So testest du genau diesen Task
### A) Technische Negativ-/Kernfälle (automatisiert)
`pytest tests/test_auth_guard.py tests/test_conversations_service.py tests/test_message_logs_service.py -v`

Erwartung:
- fehlender Token → `401`
- ungültiger Token → `403`
- valider Token → Chat akzeptiert, User-Kontext gesetzt
- aktive Conversation wird pro User konsistent wiederverwendet
- Logs werden in Reihenfolge `user` → `assistant` append-only geschrieben

### B) Manueller E2E-Happy-Path
1. Frontend öffnen und einloggen
2. Chat-Nachricht senden
3. Prüfen, dass Request an `POST /api/v1/chat` mit Bearer-Token geht
4. Prüfen, dass Antwort im UI erscheint
5. In Supabase prüfen, dass Conversation + Message-Logs persistiert sind

Erwartung:
- Auth → Chat → Antwort → Persistenz funktioniert als kompletter Flow reproduzierbar.

## 5) Troubleshooting
- Problem: `401 Missing bearer token`
  - Ursache: Frontend-Request ohne `Authorization`-Header.
  - Lösung: Session/JWT im Frontend prüfen und neu einloggen.

- Problem: `403 Invalid or expired token`
  - Ursache: Abgelaufener oder ungültig signierter JWT.
  - Lösung: Neu einloggen, `SUPABASE_JWT_SECRET` und lokale Supabase-Keys prüfen.

- Problem: `Failed to get or create active conversation`
  - Ursache: Supabase-RPC/Migration fehlt oder Supabase nicht korrekt gestartet.
  - Lösung: `supabase start` + `supabase db reset`, dann Backend neu starten.

- Problem: Chat antwortet, aber keine Persistenz sichtbar
  - Ursache: Falsches Projekt/Schema oder Prüfung im falschen Environment.
  - Lösung: Lokale Supabase-Instanz/Studio prüfen und denselben User-Kontext verwenden.

## 6) Definition of Done (Task 10)
- [x] E2E-Kernpfad (Auth → Chat → Antwort → Persistenz/Logging) reproduzierbar dokumentiert
- [x] Negativfälle ohne Token und mit ungültigem Token testbar und nachgewiesen
- [x] Verhalten für parallelen Conversation-Start durch Persistenz-/Service-Logik abgesichert
- [x] Übergabe-Artefakte (`tests/`, `readme.md`, `todos.md`) finalisiert
- [x] Lerndoku vollständig
