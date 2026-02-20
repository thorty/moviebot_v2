# Moviebot auf Render deployen (Backend + Frontend)

Dieses Howto ist ein kompletter Ablauf für euer aktuelles Repo.

Zielbild:
- Backend (FastAPI) als Render Web Service
- Frontend (Vite/React) als Render Static Site
- Supabase als externes Cloud-Projekt (nicht Docker lokal)

## 1) Voraussetzungen

- GitHub-Repo ist aktuell (inkl. `render.yaml`)
- Render Account + Zugriff auf das Repo
- Supabase Cloud Projekt erstellt
- Folgende Secrets vorhanden:
  - `OPENAI_API_KEY`
  - `TAVILY_API_KEY`
  - `TMDB_BEARER`
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `SUPABASE_JWT_SECRET`

## 2) Supabase Cloud vorbereiten

1. Öffne dein Supabase-Projekt.
2. Führe alle SQL-Migrationen aus `supabase/migrations/` in Reihenfolge aus:
   - `20260216173000_task6_conversations_message_logs.sql`
   - `20260217123000_task8_single_active_conversation_rpc.sql`
   - `20260217140000_task11_start_new_active_conversation_rpc.sql`
3. Prüfe, dass die Tabellen/RPCs existieren:
   - `public.conversations`
   - `public.message_logs`
   - RPC `get_or_create_active_conversation`
   - RPC `start_new_active_conversation`
4. Erstelle einen Test-User in Supabase Auth.

Hinweis: Für euren aktuellen JWT-Verify-Pfad muss `SUPABASE_JWT_SECRET` zum Projekt passen.

## 3) Render Blueprint deployen

1. In Render: **New +** → **Blueprint**.
2. Repo auswählen und Branch `render-deployment` (oder euren Ziel-Branch) wählen.
3. Render erkennt `render.yaml` im Repo-Root.
4. Blueprint erstellen.

Es werden zwei Services angelegt:
- `moviebot-backend` (Web Service)
- `moviebot-frontend` (Static Site)

## 4) Backend konfigurieren (Render Service: `moviebot-backend`)

### Build/Start (aus `render.yaml`)
- Build: `pip install --upgrade pip && pip install -r requirements-docker.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health: `/health`

### Environment Variables setzen

Setze im Backend-Service diese Variablen:

- `OPENAI_API_KEY`
- `TAVILY_API_KEY`
- `TMDB_BEARER`
- `SUPABASE_URL` = `https://<your-project-ref>.supabase.co`
- `SUPABASE_ANON_KEY` = Supabase anon key
- `SUPABASE_SERVICE_ROLE_KEY` = Supabase service role key
- `SUPABASE_JWT_SECRET` = JWT Secret des Supabase Projekts
- `SUPABASE_JWT_AUDIENCE` = `authenticated`
- `FRONTEND_WEB_URL` = URL der Render Static Site (z. B. `https://moviebot-frontend.onrender.com`)
- `BACKEND_API_URL` = URL dieses Backend-Services (z. B. `https://moviebot-backend.onrender.com`)

## 5) Frontend konfigurieren (Render Service: `moviebot-frontend`)

### Build/Publish (aus `render.yaml`)
- Root: `frontend/web`
- Build: `npm ci && npm run build`
- Publish: `dist`

### Environment Variables setzen

- `VITE_SUPABASE_URL` = `https://<your-project-ref>.supabase.co`
- `VITE_SUPABASE_ANON_KEY` = Supabase anon key
- `VITE_BACKEND_API_URL` = Backend-URL, z. B. `https://moviebot-backend.onrender.com`

Wichtig: `VITE_BACKEND_API_URL` muss exakt auf den Render-Backend-Service zeigen.

## 6) Richtige Deploy-Reihenfolge

1. Supabase Migrationen abschließen.
2. Backend env vars setzen und Backend deployen.
3. Backend-Health prüfen: `GET /health`.
4. Frontend env vars setzen und Frontend deployen.
5. Frontend öffnen und Login testen.

## 7) Smoke-Tests nach Deployment

### Backend
- `GET https://<backend-url>/health` → `status: ok`
- `POST /api/v1/chat` ohne Bearer Token → `401`

### Frontend
- Login mit Supabase-User funktioniert.
- Chat-Anfrage liefert Antwort.
- Neuer Chat (`/api/v1/chat/new`) funktioniert.

## 8) Typische Fehler und Fixes

### 401/403 bei Chat trotz Login
- Prüfe `SUPABASE_JWT_SECRET` im Backend.
- Prüfe `SUPABASE_JWT_AUDIENCE` (`authenticated`).
- Stelle sicher, dass Frontend wirklich gegen dasselbe Supabase-Projekt läuft (`VITE_SUPABASE_URL`).

### CORS-Fehler im Browser
- Prüfe `FRONTEND_WEB_URL` im Backend auf die exakte Frontend-URL.
- Nach Env-Änderung Backend neu deployen.

### Frontend erreicht Backend nicht
- Prüfe `VITE_BACKEND_API_URL`.
- Prüfe, ob Backend-Service auf Render gesund ist.

## 9) Go-Live Checkliste

- [ ] Alle Supabase Migrationen ausgeführt
- [ ] Backend-Env vollständig gesetzt
- [ ] Frontend-Env vollständig gesetzt
- [ ] `/health` ist grün
- [ ] Login funktioniert
- [ ] Chat-Endpunkte antworten korrekt
- [ ] Keine sensiblen Secrets im Repo committed

## 10) Betrieb danach

- Änderungen auf den Deploy-Branch pushen (Auto-Deploy ist aktiv).
- Bei Änderungen an Secrets/URLs immer Backend und Frontend redeployen.
- Optional: eigenes Custom Domain Mapping in Render für Frontend und Backend einrichten.