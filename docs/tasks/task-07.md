# Task 07 — JWT-Guard pro Request (Subtask 7.1)

## 1) Kurzüberblick
- Ziel dieses Subtasks: Requests ohne gültiges JWT zuverlässig blockieren.
- Ergebnis: FastAPI prüft bei `POST /api/v1/chat` den Bearer-Token pro Request.
- Fehlerverhalten ist klar getrennt:
  - `401`: kein/kaputter Auth-Header
  - `403`: Token ungültig oder abgelaufen
- Umgesetzt in: `main.py`, `backend/utils/helper.py`, `backend/utils/setupenv.py`, `tests/test_auth_guard.py`.

## 2) Erklärung für Junior Dev (einfach)
Der JWT-Guard ist wie eine Eingangskontrolle.

Ablauf pro Request:
1. API liest den `Authorization`-Header.
2. Fehlt der Bearer-Token, wird sofort mit `401` geantwortet.
3. Ist ein Token da, wird er mit `SUPABASE_JWT_SECRET` validiert.
4. Ist der Token ungültig/abgelaufen, antwortet die API mit `403`.

Warum wichtig?
- Ohne Guard könnte jede Person anonym auf geschützte Endpunkte zugreifen.
- Der Guard ist die Grundlage, damit wir in Subtask 7.2 den echten User-Kontext zuverlässig durchreichen können.

## 3) Was du manuell machen musst
1. Sicherstellen, dass `.env` vorhanden ist (`cp .env.example .env`).
2. `SUPABASE_JWT_SECRET` in `.env` setzen.
3. Backend starten: `uvicorn main:app --reload`.

## 4) So testest du genau diesen Task
### Voraussetzungen
- Python-Umgebung mit Abhängigkeiten installiert.
- `SUPABASE_JWT_SECRET` ist in der lokalen Umgebung verfügbar (für Laufzeit).

### Testschritte
1. `pytest tests/test_auth_guard.py -v`
2. Optional manuell ohne Token:
   - `curl -i -X POST http://localhost:8000/api/v1/chat -H "Content-Type: application/json" -d '{"message":"hi"}'`
3. Optional manuell mit ungültigem Token:
   - `curl -i -X POST http://localhost:8000/api/v1/chat -H "Authorization: Bearer invalid.token.value" -H "Content-Type: application/json" -d '{"message":"hi"}'`

### Erwartetes Ergebnis
- Test `without_token` liefert `401` mit `Missing bearer token`.
- Test `invalid_token` liefert `403` mit `Invalid or expired token`.
- Manuelle Calls zeigen dasselbe Verhalten.

## 5) Troubleshooting
- Problem: `500 Missing required environment variable: SUPABASE_JWT_SECRET`
  - Ursache: Secret nicht gesetzt.
  - Lösung: `SUPABASE_JWT_SECRET` in `.env` ergänzen und Backend neu starten.

- Problem: Test kann `main` nicht importieren.
  - Ursache: Tests nicht aus Repo-Root gestartet.
  - Lösung: `cd` ins Projekt-Root und `pytest` erneut ausführen.

- Problem: `ModuleNotFoundError: jwt`
  - Ursache: Abhängigkeit `PyJWT` nicht installiert.
  - Lösung: Abhängigkeiten neu installieren (`pip install -e .` oder entsprechender Projekt-Install).

## 6) Definition of Done (Subtask 7.1)
- [x] JWT-Verifikation im FastAPI-Requestpfad implementiert
- [x] Fehlende/ungültige Tokens werden zuverlässig mit `401/403` beantwortet
- [x] Negativtests für beide Fälle vorhanden und ausführbar
- [x] Lerndoku vollständig
