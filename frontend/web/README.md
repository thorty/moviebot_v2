# Frontend Web (Produktiver Pfad)

Dieses Verzeichnis ist ab Task 4 der einzige produktive Frontend-Pfad (`frontend/web`).

## Status in Task 4
- React/TypeScript App-Grundgerüst mit Vite ist initialisiert.
- Zentrale Chat-UI-Struktur wurde aus dem Prototyp portiert (`ChatPage`, `ChatInput`, `ChatMessages`, `ExamplePrompts`, `FilterPanel`).

## Status in Task 5
- Supabase Auth-Basis ist integriert (Session-Check, Login-Form, Logout).
- App-Flow unterscheidet klar: nicht eingeloggt (`Login`) vs. eingeloggt (`ChatPage`).
- Für lokale npm-Starts werden `VITE_SUPABASE_URL` und `VITE_SUPABASE_ANON_KEY` über `.env.local` gesetzt.

## Wichtige Abgrenzung
- Der Prototyp unter `plans/moviebot-web-app` ist nur Quelle für UI/UX.
- Der Prototyp wird nicht als Laufzeit-App betrieben.
- Die Prototyp-Route `plans/moviebot-web-app/app/api/chat/route.ts` wird nicht produktiv verwendet.

## Start
- Lokal: `npm install && npm run dev -- --host 0.0.0.0 --port 3000`
- Via Docker Compose: Service `frontend-web`

## Env für Auth
1. `cp .env.example .env.local`
2. `VITE_SUPABASE_URL` und `VITE_SUPABASE_ANON_KEY` setzen

## Status in Task 9 (Produktiver API-Transport)
- Produktiver Chat-Transport läuft direkt gegen Backend: `POST /api/v1/chat`
- Header für geschützte Requests: `Authorization: Bearer <JWT>`
- Frontend nutzt **nicht** die Prototyp-Route `plans/moviebot-web-app/app/api/chat/route.ts`

### Zusätzliche Env-Variable
- `VITE_BACKEND_API_URL` (z. B. `http://localhost:8000`)

### Request-Format (Frontend → Backend)
```json
{
	"message": "Ich suche einen Sci-Fi Thriller",
	"userstreamingproviders": ["Netflix", "Disney Plus"],
	"paymenttypes": ["flatrate", "rent"]
}
```

### Response-Format (Backend → Frontend)
```json
{
	"status": "accepted",
	"user_id": "<jwt-sub>",
	"conversation_id": "<uuid>",
	"reply": "..."
}
```
