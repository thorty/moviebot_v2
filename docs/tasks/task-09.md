# Task 09 — Produktiver API-Transport im Frontend

## 1) Kurzüberblick
- Ziel dieses Tasks: Das produktive Frontend sendet Chat-Requests direkt an das produktive Backend.
- Ergebnis:
  - Frontend nutzt `POST /api/v1/chat` als einzigen produktiven Chat-Endpoint.
  - Jeder Request enthält `Authorization: Bearer <JWT>`.
  - Prototyp-Route `plans/moviebot-web-app/app/api/chat/route.ts` wird nicht produktiv verwendet.
- Umgesetzt in:
  - `frontend/web/src/lib/chatApi.ts`
  - `frontend/web/src/pages/ChatPage.tsx`
  - `frontend/web/README.md`
  - `readme.md`

## 2) Erklärung für Junior Dev (einfach)
Vor Task 9 hatte das Frontend nur eine Platzhalter-Antwort im Browser.

Jetzt passiert der echte Flow:
1. User ist via Supabase eingeloggt.
2. Frontend holt das aktuelle Access Token aus der Session.
3. Frontend sendet die Chat-Nachricht an `POST /api/v1/chat`.
4. Backend antwortet mit `reply`, `conversation_id` und `user_id`.
5. Frontend zeigt diese Antwort im Chat an.

Warum wichtig?
- Erst damit arbeitet das UI wirklich mit dem produktiven Backend-Vertrag.
- Ohne diesen Schritt wären Auth, Persistenz und Conversation-Logik im Backend nicht im echten Frontend nutzbar.

## 3) Was du manuell machen musst
1. Lokalen Supabase-Stack starten: `supabase start`
2. DB/Migrationen anwenden: `supabase db reset`
3. Backend starten (Docker oder lokal):
   - Docker: `docker compose up -d backend`
   - Lokal: `uvicorn main:app --reload`
4. Frontend starten:
   - Docker: `docker compose up -d frontend-web`
   - Lokal: `cd frontend/web && npm run dev -- --host 0.0.0.0 --port 3000`
5. Sicherstellen, dass Frontend-Env gesetzt ist:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_BACKEND_API_URL` (z. B. `http://localhost:8000`)

## 4) So testest du genau diesen Task
### Voraussetzungen
- Task 1–8 sind abgeschlossen.
- Lokaler Supabase-User für Login existiert.
- Backend ist erreichbar auf Port `8000`.

### Testschritte
1. Browser öffnen: `http://localhost:3000`
2. Mit lokalem Testuser einloggen.
3. DevTools → Network öffnen.
4. Chat-Nachricht senden.
5. Request prüfen:
   - URL: `POST /api/v1/chat`
   - Header: `Authorization: Bearer <JWT>`
   - Body enthält: `message`, `userstreamingproviders`, `paymenttypes`
6. Response prüfen:
   - JSON enthält: `status`, `user_id`, `conversation_id`, `reply`

### Erwartetes Ergebnis
- Frontend sendet **nur** an den produktiven Backend-Endpoint.
- Request/Response passt zum produktiven Backend-Vertrag.
- Die Antwort aus dem Backend erscheint im Chat.

## 5) Troubleshooting
- Problem: `Failed to fetch`
  - Ursache: Backend läuft nicht oder CORS/URL passt nicht.
  - Lösung: `curl http://localhost:8000/health` prüfen und `VITE_BACKEND_API_URL` kontrollieren.

- Problem: `403 Forbidden`
  - Ursache: Ungültige/alte Session oder JWT-Validierung schlägt fehl.
  - Lösung: Neu einloggen, Browser-Session neu aufbauen, Supabase-Stack prüfen.

- Problem: Backend-Fehler `Failed to get or create active conversation`
  - Ursache: Migrationen nicht angewendet oder RPC nicht verfügbar.
  - Lösung: `supabase db reset` ausführen und Backend neu starten.

- Problem: `404` auf Supabase-RPC aus Backend
  - Ursache: Supabase-Migrationsstand veraltet.
  - Lösung: `supabase db reset` und erneuter Request.

## 6) Definition of Done (Task 9)
- [x] Frontend nutzt produktiven Backend-Pfad `POST /api/v1/chat`
- [x] Auth-Header `Authorization: Bearer <JWT>` wird im Frontend gesetzt
- [x] Kein produktiver Pfad über Prototyp-Route `app/api/chat/route.ts`
- [x] Request/Response folgt dem produktiven Backend-Vertrag
- [x] Lerndoku vollständig
