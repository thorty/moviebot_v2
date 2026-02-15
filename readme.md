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
- Logging nur User-Query + finale Antwort
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