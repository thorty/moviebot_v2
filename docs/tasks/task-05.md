# Task 05 — Frontend Auth-Basis

## 1) Kurzüberblick
- Ziel dieses Tasks: Login-Status im produktiven Frontend nutzbar machen.
- Ergebnis: App zeigt Login-Form ohne Session und Chat-Ansicht mit Session.
- Umgesetzt in: `frontend/web/src/App.tsx`, `frontend/web/src/lib/supabase.ts`, `frontend/web/src/pages/ChatPage.tsx`, `frontend/web/package.json`, `docker-compose.yml`, `readme.md`.

## 2) Erklärung für Junior Dev (einfach)
Dieser Task setzt die Grundlage für geschützten Zugriff im Frontend.

Die App startet jetzt nicht mehr immer direkt im Chat. Stattdessen:
- ohne gültige Session: Login anzeigen
- mit gültiger Session: Chat anzeigen

So ist klar, ob der User eingeloggt ist. Das ist die Voraussetzung für Task 7/9 (geschützte API-Requests mit Token).

## 3) Was du manuell machen musst
1. Testnutzer in Supabase Auth anlegen (`auth.users`).
2. Frontend-Env setzen (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`).
3. Frontend neu starten (`docker compose up -d --force-recreate frontend-web`).

Lokal-Setup Schritt für Schritt

### Supabase CLI installieren
#### macOS (Homebrew):
brew install supabase/tap/supabase
In dein Repo wechseln und Supabase initialisieren
cd /Users/A743293/workspace/playground/mb_langgraph_v3
supabase init
Falls dein Compose-Postgres läuft, erst stoppen (Port-Konflikte vermeiden)
docker compose stop supabase-db
Lokalen Supabase Stack starten
supabase start
URLs + Keys ausgeben lassen
supabase status -o env
Du bekommst dabei u. a.:
API URL (meist http://127.0.0.1:54321)
Studio URL (meist http://127.0.0.1:54323)
anon key
service_role key
jwt secret
Keys in dein Projekt eintragen

In .env setzen:
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_JWT_SECRET
In frontend/web/.env.local setzen:
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY
User in auth.users lokal anlegen

Studio öffnen: http://127.0.0.1:54323
Authentication → Users → Add user
E-Mail + Passwort setzen
Danach steht der User korrekt im lokalen Auth-System (nicht manuell per SQL basteln)
Smoke-Test

#### Frontend neu starten:
docker compose up -d --force-recreate frontend-web
Browser öffnen: http://localhost:3000
Login mit dem eben angelegten User testen
Erwartung: Login klappt, Chat-Seite erscheint, Logout bringt zurück zur Login-Form


## 4) So testest du genau diesen Task
### Voraussetzungen
- Task 1–4 abgeschlossen.
- Gültige Supabase URL/Anon Key.
- Ein Testnutzer in `auth.users` vorhanden.

### Testschritte
1. `docker compose up -d --force-recreate frontend-web`
2. `docker compose ps frontend-web`
3. Browser öffnen: `http://localhost:3000`
4. Login mit Testnutzer durchführen.
5. Prüfen, dass Chat-UI erscheint und Logout-Button sichtbar ist.
6. Logout klicken und prüfen, dass wieder Login-Form erscheint.

### Erwartetes Ergebnis
- Nicht eingeloggt: Login-Form sichtbar.
- Eingeloggt: Chat-Seite sichtbar.
- Logout setzt den Status zurück auf Login.

### Tatsächlich beobachtete Ergebnisse
- Frontend kompiliert und startet erfolgreich.
- Login/Logout-Flow ist im UI implementiert und funktionsbereit.
- Voller End-to-End-Login hängt von realen Supabase Keys + Testnutzer ab.

## 5) Troubleshooting
- Problem: Login-Form zeigt Hinweis „Supabase ist noch nicht vollständig konfiguriert“.
  - Ursache: `VITE_SUPABASE_URL` oder `VITE_SUPABASE_ANON_KEY` fehlt.
  - Lösung: Variablen setzen und Frontend neu starten.

- Problem: Login schlägt mit Auth-Fehler fehl.
  - Ursache: User existiert nicht oder Passwort falsch.
  - Lösung: Testnutzer in `auth.users` prüfen/neu anlegen.

- Problem: Nach Login weiterhin Login-Form.
  - Ursache: Session wird nicht aufgebaut (falsche Keys oder falsche Supabase URL).
  - Lösung: Env-Werte prüfen, dann Browser-Refresh/Neustart.

## 6) Definition of Done (Task)
- [x] Supabase Auth Client im Frontend integriert
- [x] Login-Status im App-Flow unterscheidbar
- [x] Logout-Flow implementiert
- [x] Readme enthält manuelle Testnutzer-/Smoke-Test-Schritte
- [x] Lerndoku ist vollständig

## 7) Nach der Implementierung ergänzen
- Nach Task 7 den JWT-Token-Transport zur Backend-API dokumentieren.
- Nach Task 9 den produktiven Chat-Request mit Bearer-Token ergänzen.
- Für den täglichen Betrieb: [docs/start-stop-spickzettel.md](docs/start-stop-spickzettel.md)
