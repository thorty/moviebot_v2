---
name: Moviebot Frontend Agent
description: Frontend-specific guidance for the React/Vite/Supabase web app and legacy clients
---

## Frontend Scope
The production-target frontend is `frontend/web`. `frontend/terminal` is a legacy/POC client; do not update it unless the task explicitly mentions it.

## Web App Stack
- React 18 + TypeScript + Vite.
- Tailwind CSS with small local components, not a full shadcn installation yet.
- Supabase JS client for auth.
- `react-markdown` renders assistant responses.
- `lucide-react` is available for icons.

## Core Files
- `web/src/pages/ChatPage.tsx`: main chat screen, auth state, API calls, filter state.
- `web/src/components/chat/FilterPanel.tsx`: streaming providers, payment/media filters, mediatheken toggle.
- `web/src/components/chat/ChatMessages.tsx`: assistant/user message rendering.
- `web/src/components/chat/ChatInput.tsx`: prompt input and speech-input integration.
- `web/src/lib/chatApi.ts`: backend API types and calls.
- `web/src/lib/supabase.ts`: Supabase client setup.

## Frontend Principles
- Build the actual app workflow, not marketing pages.
- Keep UI quiet, utilitarian, and optimized for repeated chat/filter use.
- Preserve backend payload compatibility. When adding request fields, update `chatApi.ts` types and `ChatPage.tsx` request construction together.
- Keep filter state names clear: frontend camelCase, backend snake_case at the API boundary.
- Mediatheken are an additional availability source, not a replacement for streaming providers unless the user explicitly selects mediathek-only behavior.
- Render Markdown links safely through existing markdown rendering; do not manually inject HTML for assistant content.

## Design Rules
- Use existing Tailwind patterns and component structure.
- Use lucide icons for common controls when icons are needed.
- Do not add nested cards or decorative marketing layouts to the chat tool.
- Ensure labels and controls fit on mobile and desktop without overlap.
- For binary settings, use toggles/checkboxes. For option sets, use menus/segmented controls.

## Commands
- Install once: `cd frontend/web && npm install`
- Dev server: `cd frontend/web && npm run dev`
- Build/type check: `cd frontend/web && npm run build`
- Docker frontend: `docker compose up -d frontend-web`

## Docker Notes
- Compose bind-mounts the repo and runs Vite in dev mode for `frontend-web`.
- Source changes should hot reload, but browser hard refresh may be needed.
- If dependencies change, recreate `frontend-web` so `npm install` runs again:
  `docker compose up -d --force-recreate frontend-web`

## Testing And Verification
- There is no dedicated frontend test runner yet. Use `npm run build` as the minimum verification.
- After significant UI changes, open `http://localhost:3000` and verify the main chat workflow visually.
- For API shape changes, verify both TypeScript types and backend request models.
- For frontend feature or performance changes validated in Docker, inspect `docker compose logs --tail=200 frontend-web backend`.
- Include a short Docker log summary in the final response, or say explicitly if logs could not be checked.
