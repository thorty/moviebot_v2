# Task 02 — Env-Standardisierung

## 1) Kurzüberblick
- Ziel dieses Tasks: Einheitliche Env-Konfiguration für lokale Entwicklung sicherstellen.
- Ergebnis: Es gibt eine verbindliche Env-Vorlage und einen zentralen Ladepfad im Backend.
- Umgesetzt in: `.env.example`, `backend/utils/setupenv.py`, `backend/tools.py`, `readme.md`.

## 2) Erklärung für Junior Dev (einfach)
Ohne festen Env-Standard hat jede Person andere lokale Einstellungen. Das führt zu Fehlern, die schwer nachzuvollziehen sind.

Dieser Task sorgt dafür, dass:
- alle mit denselben Variablennamen arbeiten,
- Env-Werte an einer zentralen Stelle geladen werden,
- alte Namen (z. B. `tmdb_bearer`) trotzdem noch funktionieren.

So wird das Setup stabiler und reproduzierbar.

## 3) Was du manuell machen musst
1. `cp .env.example .env`
2. In `.env` die fehlenden Secrets eintragen (z. B. API Keys).
3. Optional Legacy-Wert nutzen: Wenn nur `tmdb_bearer` gesetzt ist, wird er auf `TMDB_BEARER` gespiegelt.

## 4) So testest du genau diesen Task
### Voraussetzungen
- Projekt liegt lokal vor.
- `docker-compose.yml` existiert aus Task 1.

### Testschritte
1. `grep -E '^(OPENAI_API_KEY|TAVILY_API_KEY|TMDB_BEARER|SUPABASE_URL|SUPABASE_ANON_KEY|SUPABASE_JWT_SECRET|BACKEND_API_URL|FRONTEND_WEB_URL)=' .env.example`
2. `docker compose config >/dev/null && echo "compose_config_ok"`
3. `docker compose ps`

### Erwartetes Ergebnis
- Alle Pflichtvariablen sind in `.env.example` vorhanden.
- Compose-Konfiguration bleibt gültig.
- Bereits laufende Services bleiben stabil.

### Tatsächlich beobachtete Ergebnisse
- Pflichtvariablen in `.env.example` vorhanden (Check erfolgreich).
- `compose_config_ok` wurde ausgegeben.
- `docker compose ps` zeigte weiterhin alle Task-1 Services im Status `Up`.

## 5) Troubleshooting
- Problem: App startet, aber einzelne Tools melden fehlende Keys.
  - Ursache: `.env` wurde nicht aus `.env.example` erstellt oder Secrets fehlen.
  - Lösung: `cp .env.example .env` ausführen und Werte ergänzen.

- Problem: TMDB funktioniert trotz gesetztem `tmdb_bearer` nicht.
  - Ursache: Alte Schlüsselbezeichnung wird in manchen Pfaden nicht geladen.
  - Lösung: `TMDB_BEARER` in `.env` setzen (oder Loader verwenden, der Legacy-Key spiegelt).

- Problem: Unterschiedliches Verhalten zwischen Modulen.
  - Ursache: Uneinheitliches Laden mit `load_dotenv(...)` an mehreren Stellen.
  - Lösung: Zentralen Loader aus `backend/utils/setupenv.py` verwenden.

## 6) Definition of Done (Task)
- [x] `.env.example` enthält alle MVP-Pflichtvariablen
- [x] Env-Ladepfad ist in `backend/utils/setupenv.py` zentralisiert
- [x] Readme dokumentiert Setup und Pflichtvariablen
- [x] Lerndoku ist vollständig

## 7) Nach der Implementierung ergänzen
- Finaler Satz an Pflichtvariablen nach Task 7/9 API-Vertrag prüfen.
- Bei Bedarf weitere Gruppen in `REQUIRED_ENV_GROUPS` ergänzen.
