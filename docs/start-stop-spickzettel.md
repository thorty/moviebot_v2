# Start/Stop Spickzettel (Docker-only)

## 1) Setup-Prinzip

- Ein einziges `docker-compose.yml` startet alles: App + Supabase minimal + Studio.
- Kein `supabase start/stop/db reset` im Daily-Flow.
- Migrationen laufen als one-shot Service (`supabase-migrations`) non-destructive beim Start.

## 2) Einmaliges Setup

1. Root `.env` anlegen und befüllen (mindestens):
   - `POSTGRES_PASSWORD`
   - `SUPABASE_JWT_SECRET`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `SUPABASE_DASHBOARD_USERNAME`
   - `SUPABASE_DASHBOARD_PASSWORD`
2. Optional für App-Laufzeit ergänzen:
   - `OPENAI_API_KEY`
   - `TAVILY_API_KEY`
   - `TMDB_BEARER`

## 3) Start-Reihenfolge (Daily)

1. Kompletten Stack starten:
   - `docker compose up -d --build`
2. Status prüfen:
   - `docker compose ps`
3. Logs bei Bedarf:
   - `docker compose logs --tail=200`

## 4) Wichtige lokale URLs

- Frontend: `http://localhost:3000`
- Backend Health: `http://localhost:8000/health`
- Supabase API Gateway: `http://localhost:54321`
- Supabase Studio: `http://localhost:54323`

## 5) Testnutzer anlegen (`auth.users`)

1. Studio öffnen: `http://localhost:54323`
2. `Authentication` → `Users`
3. User mit E-Mail + Passwort anlegen
4. Login im Frontend testen (`http://localhost:3000`)

## 6) Stop-Reihenfolge

- Normal stoppen:
  - `docker compose down`
- Mit Datenlöschung (nur wenn bewusst gewünscht):
  - `docker compose down -v`

## 7) Daten & Migrationen

- Daten liegen im Docker-Volume (`supabase-db-data`) und bleiben über Neustarts erhalten.
- Kein automatischer Reset bei `docker compose up`.
- `supabase-migrations` wendet nur neue SQL-Dateien aus `supabase/migrations` an.

## 8) Häufige Stolperfallen

- Leere/ungültige `SUPABASE_ANON_KEY` oder `SUPABASE_JWT_SECRET` führen zu Auth-/RLS-Fehlern.
- Nach Env-Änderungen Services neu erstellen:
  - `docker compose up -d --force-recreate`
- Portkonflikte auf `3000`, `54321`, `54323`, `8000` blockieren den Start.

## 9) Serverbetrieb (kurz)

- Studio nicht öffentlich exponieren (nur intern/VPN/Ingress-Schutz).
- Secrets nicht im Repo speichern; per Host-Env/Secret-Manager injizieren.
- Für Deployments denselben Compose-Stack nutzen und Daten-Volume persistent halten.
