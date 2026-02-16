# Sprint Cut Overview (POC → Fullstack MVP)

## Zielbild (3 Arbeitstage)
In 3 Tagen wird der POC auf ein lokal lauffähiges Fullstack-MVP geschnitten (Docker Compose, E2E), mit minimalem Umfang und klarer Abnahmebasis.

Hinweis zur Planung: Die Umsetzung wird task-basiert geführt (nicht tag-basiert), damit jeder Schritt einzeln validiert werden kann.

## Verbindliche Entscheidungen
- Supabase Auth im Frontend + JWT-Verifikation im Backend bei jeder Request
- Persistenz speichert alle User-Eingaben und Bot-Antworten append-only (kein Überschreiben)
- Genau 1 aktive Conversation pro User
- Lokaler End-to-End-Betrieb via Docker Compose zuerst

## Festgelegt für die Umsetzung
- Produktives Frontend wird unter `frontend/web` aufgebaut; der Prototyp unter `plans/moviebot-web-app` ist reine UI/UX-Quelle.
- Das Fundament liefert ein echtes FastAPI-Grundgerüst in `main.py` inklusive Health-Endpoint.
- DB-Basisschema wird als SQL-Migrationen im Repository versioniert (keine rein manuelle Dashboard-Konfiguration).
- Für lokale Infrastruktur wird der offizielle Supabase-Local-Stack in Docker Compose integriert.

## Timeline
- Task-Block A (Fundament): Compose, Env-Standardisierung, FastAPI-Health, Frontend-Zielpfad, DB-Grundschema
- Task-Block B (Regeln): JWT-Guard je Request, User-Kontext, 1 aktive Conversation, vollständige append-only Nachrichtenpersistenz
- Task-Block C (Integration): produktiver Frontend-Transport, E2E-Härtung, Negativtests, Übergabe

## MVP-Ziele
- Login-geschützter Zugriff auf Chat
- Backend akzeptiert nur valide Supabase JWTs
- Pro User nur eine aktive Conversation in Persistenz und API-Verhalten
- Persistenz enthält vollständige Chat-Nachrichtenhistorie pro Conversation (append-only)
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
- Zielpfade für MVP sind fest: `main.py` als FastAPI-Entry, `frontend/web` als produktives Frontend
- Team-Review-Slot am Ende von Task-Block C

## Design-Prototyp (plans/moviebot-web-app)
- Status: verwendbar als UI/UX-Basis für das Frontend
- Scope im Prototyp: Chat-Layout, Filterpanel, Example-Prompts, Loading-State
- Wichtige Lücken: keine Login-Seite, keine Supabase-Auth-Integration, keine Anbindung an das bestehende FastAPI/LangGraph-Backend
- Technische Abweichung: Prototyp ist Next.js-App-Router mit eigener API-Route (`app/api/chat/route.ts`) und nicht der geplante produktive API-Pfad
- Entscheidung für MVP: Komponenten und Styling übernehmen, API-Transport auf Backend-Endpoint umstellen, Auth-Gate ergänzen; Next-internal API-Route wird nicht produktiv genutzt

## Definition of Done (Sprint-Ebene)
- `docker compose up` startet alle MVP-relevanten Services lokal
- Authentifizierte User können den Chat nutzen; unauthentifizierte Requests werden blockiert
- Genau eine aktive Conversation pro User ist technisch erzwungen
- Persistenz enthält alle User-Eingaben und Bot-Antworten ohne Überschreiben bestehender Einträge
- Frontend spricht den produktiven Backend-Endpoint und nicht `app/api/chat/route.ts`
- Review-Checkliste vollständig mit “ok” markiert

## Qualitätsprinzip
- Jeder Task hat einen eigenen Validierungs-Gate (Go/No-Go), bevor der nächste Task startet.
- Reihenfolge ist bewusst sequentiell, um Integrationsfehler früh zu isolieren.
