# Frontend 

## Features
    - login 1 user (for security)
    - simple chat interface
    - streaming provider selection 
    - loaading animation when searching (no streaming)    
    - use cookie for provider selection    
    - example questions 
    
- architecture descisions: 
    - frontend react 
    - backend python 
    - using superbase framework for, database, login and usermngmnt, logging,...
    - run in docker  


## Implementierungsplan

#### High-Level Copilot Plan: Moviebot Fullstack-MVP

##### Phase 1: Setup & Supabase
- Supabase lokal Docker-Stack klonen und starten
- Copilot-Prompts: Schema für Users/Chats mit RLS, Env-Vars konfigurieren
- Dashboard-Tabellen und Policies testen

##### Phase 2: Backend FastAPI
- FastAPI-Projekt initialisieren, Supabase/LangGraph-Abhängigkeiten hinzufügen
- Copilot-Prompts: Auth-Dependencies, Chat-Endpoint mit LangGraph-Integration, Logging in DB
- Swagger-Docs und lokale Tests (uvicorn)

##### Phase 3: React Frontend
- Vite/React-Projekt mit TypeScript + Supabase-Client erstellen
- Copilot-Prompts: Auth-Komponenten (Login/Register), Chat-UI mit Realtime, API-Calls zu Backend
- Styling mit shadcn/ui oder Tailwind

##### Phase 4: Integration & Docker
- Frontend-Backend-Supabase verbinden (CORS, Env-Switch local/cloud)
- Copilot-Prompts: Dockerfiles/Compose für Stack, Multi-Env-Konfig
- End-to-End-Tests: Login, Chat, Logs

##### Phase 5: Deploy & Polish
- Local Docker-Prod-Sim, Cloud-Env (Supabase Cloud + Render/Vercel)
- Copilot-Prompts: Error-Handling, Loading-States, Responsive Design
- Präsentations-Features: User-Management, Share-Links

**Priorisiere Auth/Chat, iteriere mit Tests. Track in GitHub-Issue.**
