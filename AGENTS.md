---
name: Moviebot Agent
description: Moviebot Fullstack: LangGraph/FastAPI Backend + React/Supabase Frontend
---

## Purpose
Moviebot is an LLM-based movie and TV recommendation assistant. The repo contains the active LangGraph/FastAPI backend, React/Supabase web frontend, legacy terminal frontend, local Supabase setup, migrations, and tests.

Use this file to avoid rediscovering core project decisions in every session. More specific instructions live in `backend/AGENTS.md` and `frontend/AGENTS.md`.

## Product Decisions
- MVP principle: keep features minimal and directly tied to the movie recommendation workflow.
- Auth: Supabase Auth with backend JWT verification per request.
- Conversations: exactly 1 active conversation per user.
- Logging/persistence: append-only user messages and assistant responses; do not overwrite history.
- Database: always use Supabase RLS for user-owned data.
- Availability: TMDB is the source for commercial streaming availability; public mediatheken availability is separate web evidence, not a TMDB provider.
- Mediatheken logic uses OR semantics with streaming availability. Do not implement hard AND matching unless explicitly requested.

## Architecture Map
- `main.py`: FastAPI entrypoint, request models, auth, chat API, preference API.
- `backend/graph.py`: LangGraph state machine and model initialization.
- `backend/tools.py`: LangChain tools for search, mediatheken search, and streaming provider filtering.
- `backend/prompts.py`: prompt templates and output instructions.
- `backend/utils/tmdb/`: TMDB provider and availability client.
- `backend/persistence/`: Supabase REST persistence services.
- `frontend/web/`: React/Vite/Supabase web app.
- `frontend/terminal/`: legacy/POC client.
- `supabase/migrations/`: SQL migrations run by the `supabase-migrations` service.

## Commands
- Backend local: `uvicorn main:app --reload`
- Frontend local: `cd frontend/web && npm run dev`
- Full stack: `docker compose up -d`
- Run backend tests: `uv run pytest -q`
- Run focused tests: `uv run pytest tests/test_tools.py tests/test_prompt_modes.py -q`
- Frontend build check: `cd frontend/web && npm run build`
- Run migrations in Docker: `docker compose run --rm supabase-migrations`

## Docker Notes
- Compose is development-style and bind-mounts `./:/workspace`.
- Backend container runs `uvicorn main:app` without `--reload`; restart `backend` after Python changes.
- Frontend container runs Vite dev server; browser hard refresh may be needed after UI changes.
- Backend dependencies in Docker are installed from `requirements-docker.txt`, not `uv.lock`.
- Migration changes require running `supabase-migrations`; PostgREST schema-cache issues can require `docker compose restart supabase-rest`.
- `docker compose down -v` deletes local Supabase data and users.

## Docker Log Review
- For every feature optimization, performance optimization, or Docker-validated bug fix, inspect Docker logs before finalizing.
- Minimum backend/API log check: `docker compose logs --tail=200 backend`
- For frontend-facing changes, also check: `docker compose logs --tail=200 frontend-web`
- For auth, persistence, migrations, or schema issues, also check: `docker compose logs --tail=200 supabase-rest supabase-auth supabase-db supabase-migrations`
- In the final response, mention whether logs were checked and summarize relevant errors or warnings.
- If Docker is not running or logs cannot be inspected, say that explicitly instead of implying runtime verification.

## Google/Gemini Notes
- The repo uses both `langchain-google-genai` for chat/tool-calling and `google-genai` directly for Google Search grounding.
- Be conservative with Gemini API-version changes. Prior attempts to force `v1` for LangChain chat/tool-calling caused 400 errors for `systemInstruction` and `tools` payload fields in Docker.
- If investigating 503s, first inspect actual package versions in both local and Docker environments before changing code:
  `docker compose exec backend python -c "import importlib.metadata as m; print(m.version('langchain-google-genai'), m.version('google-genai'))"`
- Treat 503 as transient service/capacity failure unless logs show deterministic 400 payload errors.

## Development Rules
- Prefer existing patterns over new abstractions.
- Keep API compatibility for existing frontend payloads unless the user explicitly approves a breaking change.
- Do not mix the `"Mediatheken"` sentinel into real streaming-provider lists; keep streaming providers and public mediatheken intent separate.
- Keep prompts and tool contracts synchronized. If tool return shape changes, update prompt instructions and tests together.
- For database changes, add a Supabase migration and update persistence tests.
- Do not edit `.env` secrets. Update `.env.example`, Docker, and docs when adding env variables.
- Before finishing implementation, run focused tests for touched areas and `uv run pytest -q` when backend behavior changes.
