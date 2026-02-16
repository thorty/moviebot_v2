# Task 03 — FastAPI-Grundgerüst + Health

## 1) Kurzüberblick
- Ziel dieses Tasks: Backend auf echtes FastAPI-Fundament umstellen.
- Ergebnis: `GET /health` ist stabil erreichbar.
- Umgesetzt in: `main.py`, `docker-compose.yml`, `pyproject.toml`, `readme.md`.

## 2) Erklärung für Junior Dev (einfach)
Bisher lief im Backend nur ein Platzhalter-Server. Für die nächsten Tasks brauchen wir aber eine echte API-App.

Dieser Task macht genau das:
- Es gibt jetzt eine FastAPI-App als Startpunkt.
- Mit `/health` gibt es einen klaren „lebt der Server?“ Check.
- Compose startet direkt diese App.

Das ist die Basis für Auth (Task 7) und den späteren produktiven Chat-Endpoint.

## 3) Was du manuell machen musst
1. Sicherstellen, dass Docker läuft.
2. Backend neu starten: `docker compose up -d --build backend`
3. Health prüfen: `curl http://localhost:8000/health`

## 4) So testest du genau diesen Task
### Voraussetzungen
- Task 1 (Compose) und Task 2 (Env-Basis) sind abgeschlossen.
- `docker-compose.yml` enthält den Backend-Service.

### Testschritte
1. `docker compose up -d --build backend`
2. `docker compose ps`
3. `curl -sS http://localhost:8000/health`

### Erwartetes Ergebnis
- Backend-Container ist `Up` und `healthy`.
- `/health` liefert JSON mit `status: "ok"`.

### Tatsächlich beobachtete Ergebnisse
- Backend wurde erfolgreich neu gestartet.
- `docker compose ps` zeigte `moviebot-backend` als `Up (healthy)`.
- `/health` lieferte: `{"status":"ok","service":"moviebot-backend",...}`.

## 5) Troubleshooting
- Problem: `curl /health` liefert keinen Response.
  - Ursache: Backend-Container nicht gestartet oder Port-Konflikt.
  - Lösung: `docker compose ps` prüfen, dann `docker compose logs backend`.

- Problem: Container startet, aber wird nicht healthy.
  - Ursache: Uvicorn startet nicht korrekt.
  - Lösung: Logs prüfen, ob `main:app` importierbar ist.

- Problem: `fastapi`/`uvicorn` fehlen.
  - Ursache: Abhängigkeiten nicht installiert.
  - Lösung: Compose-Backend neu starten (installiert im Container), Projektabhängigkeiten in `pyproject.toml` prüfen.

## 6) Definition of Done (Task)
- [x] `main.py` enthält eine echte FastAPI-App
- [x] `GET /health` ist lokal erreichbar
- [x] Compose startet Backend als FastAPI (`uvicorn main:app`)
- [x] Lerndoku ist vollständig

## 7) Nach der Implementierung ergänzen
- Sobald API-Router hinzukommen, Runbook um konkrete Endpoint-Checks erweitern.
- Nach Task 7 Auth-Status (`401/403`) in Health-/Smoke-Doku ergänzen.
