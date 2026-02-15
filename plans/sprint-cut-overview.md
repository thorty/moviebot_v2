# Sprint Cut Overview (POC → Fullstack MVP)

## Zielbild (3 Arbeitstage)
In 3 Tagen wird der POC auf ein lokal lauffähiges Fullstack-MVP geschnitten (Docker Compose, E2E), mit minimalem Umfang und klarer Abnahmebasis.

## Verbindliche Entscheidungen
- Supabase Auth im Frontend + JWT-Verifikation im Backend bei jeder Request
- Logging nur von User-Query und finaler Antwort
- Genau 1 aktive Conversation pro User
- Lokaler End-to-End-Betrieb via Docker Compose zuerst

## Timeline
- Tag 1: Fundament für lokale Fullstack-Lauffähigkeit + Auth-Flow + Basis-DB
- Tag 2: Backend-Integration (JWT-Guard, 1 aktive Conversation, minimales Logging)
- Tag 3: E2E-Härtung, Abnahme, Dokumentation und Übergabe

## MVP-Ziele
- Login-geschützter Zugriff auf Chat
- Backend akzeptiert nur valide Supabase JWTs
- Pro User nur eine aktive Conversation in Persistenz und API-Verhalten
- Logging auf Minimalumfang (Query + final answer)
- Reproduzierbares lokales Setup mit einem Startkommando

## Non-Goals (explizit außerhalb Scope)
- Kein Multi-Conversation-Management/UI
- Kein erweitertes Analytics/Tracing-Dashboard
- Keine Rollen-/Rechte-Matrix über Basis-RLS hinaus
- Kein Cloud-Deployment, keine CI/CD-Erweiterung
- Keine zusätzlichen Produktfeatures am Chat-UX

## Abhängigkeiten
- Gültige Supabase-Konfiguration (lokal via Docker)
- API Keys/Secrets in lokaler Env-Konfiguration
- Bestehender FastAPI- und Frontend-Startpfad bleibt nutzbar
- Team-Review-Slot am Ende von Tag 3

## Design-Prototyp (plans/moviebot-web-app)
- Status: verwendbar als UI/UX-Basis für das Frontend
- Scope im Prototyp: Chat-Layout, Filterpanel, Example-Prompts, Loading-State
- Wichtige Lücken: keine Login-Seite, keine Supabase-Auth-Integration, keine Anbindung an das bestehende FastAPI/LangGraph-Backend
- Technische Abweichung: Prototyp ist Next.js-App-Router mit eigener API-Route (`app/api/chat/route.ts`) und nicht der geplante produktive API-Pfad
- Entscheidung für MVP: Komponenten und Styling übernehmen, API-Transport auf Backend-Endpoint umstellen, Auth-Gate ergänzen

## Definition of Done (Sprint-Ebene)
- `docker compose up` startet alle MVP-relevanten Services lokal
- Authentifizierte User können den Chat nutzen; unauthentifizierte Requests werden blockiert
- Genau eine aktive Conversation pro User ist technisch erzwungen
- Logs enthalten nur User-Query + finale Antwort
- Review-Checkliste vollständig mit “ok” markiert
