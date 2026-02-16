# Frontend Web (Produktiver Pfad)

Dieses Verzeichnis ist ab Task 4 der einzige produktive Frontend-Pfad (`frontend/web`).

## Status in Task 4
- React/TypeScript App-Grundgerüst mit Vite ist initialisiert.
- Zentrale Chat-UI-Struktur wurde aus dem Prototyp portiert (`ChatPage`, `ChatInput`, `ChatMessages`, `ExamplePrompts`, `FilterPanel`).
- Es gibt bewusst noch keine produktive API-Integration und keine Auth-Integration (folgt in späteren Tasks).

## Wichtige Abgrenzung
- Der Prototyp unter `plans/moviebot-web-app` ist nur Quelle für UI/UX.
- Der Prototyp wird nicht als Laufzeit-App betrieben.
- Die Prototyp-Route `plans/moviebot-web-app/app/api/chat/route.ts` wird nicht produktiv verwendet.

## Start
- Lokal: `npm install && npm run dev -- --host 0.0.0.0 --port 3000`
- Via Docker Compose: Service `frontend-web`
