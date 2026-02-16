# Start/Stop Spickzettel (Lokal) + Cloud-Migration

## 1) Lokalbetrieb: App + Supabase Full Stack

### Empfehlung (Hybrid)
- App-Services über Docker Compose
- Supabase-Services über Supabase CLI (ebenfalls Docker-basiert)

So hast du lokal Auth (`auth.users`), Keys (`anon`, `service_role`) und Studio im Browser.

---

## 2) Einmaliges Setup

### Supabase CLI installieren (macOS)
`brew install supabase/tap/supabase`

### Im Projekt initialisieren
`cd /Users/A743293/workspace/playground/mb_langgraph_v3`

`supabase init`

---

## 3) Start-Reihenfolge (Daily)

### A) App starten (Compose)
`docker compose up -d`

### B) Lokalen Supabase Full Stack starten (CLI)
`supabase start`

### C) Status prüfen
`docker compose ps`

`supabase status`

---

## 4) Wichtige URLs und Keys (lokal)

Nach `supabase status -o env` bekommst du typischerweise:
- API URL: `http://127.0.0.1:54321`
- Studio URL: `http://127.0.0.1:54323`
- `PUBLISHABLE_KEY` (entspricht lokal dem bisherigen `anon key`)
- `SECRET_KEY` (entspricht lokal dem bisherigen `service_role key`)
- `ANON_KEY`
- `SERVICE_ROLE_KEY`
- `JWT_SECRET`

Diese Werte setzen in:
- Root `.env`: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`
- `frontend/web/.env.local`: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

Danach Frontend neu starten:
`docker compose up -d --force-recreate frontend-web`

---

## 5) Testnutzer anlegen (`auth.users`)

1. Studio öffnen: `http://127.0.0.1:54323`
2. Authentication → Users
3. User anlegen (E-Mail + Passwort)
4. Login im Frontend testen: `http://localhost:3000`

---

## 6) Stop-Reihenfolge

### A) Supabase Full Stack stoppen
`supabase stop`

### B) App-Services stoppen
`docker compose down`

Optional Volumes mit löschen:
`docker compose down -v`

---

## 7) Häufige Stolperfallen

- `http://localhost:54322` im Browser geht nicht: das ist Postgres-Port, kein Webserver.
- Wenn `supabase start` Portkonflikte meldet, läuft meist bereits ein lokaler Dienst auf den Supabase-Ports (z. B. 54321/54322/54323). Den fremden Dienst stoppen und `supabase start` erneut ausführen.
- Nach Key-Änderungen Frontend immer neu starten (`--force-recreate`).

---

## 8) Kurz: Wie kommt das später in die Cloud?

### Zielbild
- Frontend als Web-App deployen (z. B. Vercel/Netlify)
- Backend als API deployen (z. B. Render/Fly/Container-Host)
- Supabase als gehostetes Projekt (Cloud)

### Minimaler Migrationspfad
1. Cloud-Supabase-Projekt erstellen
2. DB-Schema/Migrationen aus `supabase/migrations` anwenden
3. Auth in Supabase Cloud aktivieren (Users, Policies)
4. Cloud-Werte in Env setzen:
   - Frontend: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
   - Backend: `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, ggf. `SUPABASE_SERVICE_ROLE_KEY`
5. Frontend + Backend deployen
6. E2E testen: Login → Chat-Request → Antwort → Persistenz

### Was bleibt gleich?
- Auth-Flow (JWT)
- API-Vertrag (`POST /api/v1/chat`)
- Task-basierte Testlogik/Runbooks
