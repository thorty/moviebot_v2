# Moviebot

## Überblick
Moviebot ist ein LLM-basierter Film- und Serienberater.

Aktuell läuft ein POC mit LangGraph + Gradio. Parallel ist die Migration zu einem Fullstack-MVP geplant (FastAPI + React + Supabase, lokal via Docker Compose).

## Aktueller Stand (POC)
- Backend: LangGraph
- Frontend: Gradio
- Laufender Einstieg: `gradio frontend/gradio/app.py`

## Zielbild (Fullstack MVP)
- Backend: FastAPI + LangGraph
- Frontend: React/TypeScript (shadcn/Tailwind)
- Auth/DB: Supabase (inkl. RLS)
- Betrieb zuerst lokal End-to-End via Docker Compose

## Verbindliche MVP-Entscheidungen
- Supabase Auth + JWT-Verifikation im Backend pro Request
- Persistenz speichert alle User-Eingaben und Bot-Antworten append-only (kein Überschreiben)
- Genau 1 aktive Conversation pro User
- Keine Zusatzfeatures außerhalb der Plan-Dokumente

## Wichtige Planungsdokumente
- Sprint-Übersicht: [plans/sprint-cut-overview.md](plans/sprint-cut-overview.md)
- Sprint-Deliverables: [plans/sprint-cut-deliverables.md](plans/sprint-cut-deliverables.md)
- Prototyp-Mapping: [plans/prototype-component-mapping.md](plans/prototype-component-mapping.md)

## Design-Prototyp Frontend
Unter [plans/moviebot-web-app](plans/moviebot-web-app) liegt ein vollständiger UI-Prototyp (ohne Login-Seite).

Einordnung:
- Verwendbar als UI/UX-Basis
- Nicht direkt produktiv nutzbar
- Muss vor Einsatz ergänzt/angepasst werden: Login/Auth, produktive Backend-API-Anbindung, Provider-Mapping

## Verwendete APIs (POC)
- LLM: OpenAI
- Search: Tavily
- Metadata/Provider: TMDB
- Tracing: LangSmith

## Funktionsweise (POC)
- InterviewAgent
- ContentResearcher (Tool-Nutzung)
- State + Memory/Checkpoint
- Session-Handling

### Graph
![alt text](graph.png)

## Feature-Status (POC)
- Clarification Questions ✅
- Streaming-Provider-Filter ✅
- Payment-Type-Filter ✅
- Film/Serie als Filterkriterium ✅
- Ein-Provider-Optimierung in Suche ✅
- Fallback-Message verbessert ✅
- Out-of-scope Handling ✅
- Mediatheken-Suche (ARD/ZDF) ✅
- Direktlinks zu Streaming-Providern (offen)
- Cover Artwork (offen)

## Nächste Schritte
1. FastAPI-API-Layer vor bestehende LangGraph-Logik setzen
2. Supabase Auth/JWT-Verifikation integrieren
3. React-Frontend auf Basis Prototyp + Login/Auth ergänzen
4. Lokales E2E-Setup via Docker Compose stabilisieren

## Startkommandos
- POC: `gradio frontend/gradio/app.py`
- Backend (Zielpfad): `uvicorn main:app --reload`
- Frontend (Zielpfad): `npm run dev`
- Docker: `docker compose up`

## Task 1 Runbook (lokale Infrastruktur)

### Enthaltene Services in `docker-compose.yml`
- `backend` auf Port `8000` (Task-1 Platzhalter-Service)
- `frontend-web` auf Port `3000` (läuft als Platzhalter bis Task 4)
- `supabase-db` auf Port `54322`

### Start
1. `docker compose up -d`
2. `docker compose ps`
3. `docker compose logs --tail=100`

### Restart-Ablauf (reproduzierbar)
1. `docker compose down`
2. `docker compose up -d`
3. Falls nötig mit frischem Volume-Start: `docker compose down -v && docker compose up -d`

### Health-/Status-Checks
- Backend erreichbar: `curl http://localhost:8000`
- Containerstatus prüfen: `docker compose ps`

### Hinweis für Task 4
Der Service `frontend-web` bleibt in Task 1 absichtlich als Platzhalter aktiv. Sobald `frontend/web/package.json` existiert, startet derselbe Service automatisch die echte Web-App.

## Task 2 Runbook (Env-Standardisierung)

### Ziel
Eine zentrale und reproduzierbare Env-Konfiguration ohne versteckte Defaults.

### Datei-Standard
- Vorlage: `.env.example`
- Lokal aktiv: `.env` (nicht committen)

### Setup
1. `cp .env.example .env`
2. Fehlende Secrets in `.env` ergänzen

### Pflichtvariablen (MVP)
- `OPENAI_API_KEY`
- `TAVILY_API_KEY`
- `TMDB_BEARER`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_JWT_SECRET`
- `BACKEND_API_URL`
- `FRONTEND_WEB_URL`

### Zentraler Ladepfad
- Env wird über `backend/utils/setupenv.py` geladen.
- Legacy-Key `tmdb_bearer` bleibt kompatibel und wird auf `TMDB_BEARER` gespiegelt.

### Verifikation
1. `.env.example` enthält alle Pflichtvariablen.
2. Nach `cp .env.example .env` startet Compose weiter ohne zusätzliche implizite Werte.

## Task 3 Runbook (FastAPI + Health)

### Ziel
Backend als echte FastAPI-App mit stabilem Health-Endpoint bereitstellen.

### Umsetzung
- `main.py` enthält `app = FastAPI(...)`
- Health-Route: `GET /health`
- Compose-Backend startet via `uvicorn main:app --host 0.0.0.0 --port 8000`

### Start/Update
1. `docker compose up -d --build backend`
2. `docker compose ps`

### Verifikation
1. `curl http://localhost:8000/health`
2. Erwartung: JSON mit `status=ok` und `service=moviebot-backend`

## Task 4 Runbook (Produktives Frontend-Grundgerüst)

### Ziel
`frontend/web` als produktiven Frontend-Pfad bereitstellen und Prototyp klar als UI-Quelle abgrenzen.

### Umsetzung
- `frontend/web` enthält eine lauffähige React/TypeScript-App (Vite).
- Kern-Chat-UI aus Prototyp portiert: Layout, Input, Message-Liste, Beispiel-Prompts, Filterpanel.
- Kein produktiver Laufzeitpfad über `plans/moviebot-web-app`.

### Start/Update
1. `docker compose up -d --force-recreate frontend-web`
2. `docker compose ps`

### Verifikation
1. `curl http://localhost:3000`
2. Erwartung: HTML-Antwort (Frontend erreichbar)
3. Optional: im Browser `http://localhost:3000` öffnen und UI prüfen

### Klare Abgrenzung
- Prototyp (`plans/moviebot-web-app`) ist Referenz.
- Produktive Laufzeit-App ist ausschließlich `frontend/web`.