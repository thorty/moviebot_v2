---
name: Moviebot Backend Agent
description: Backend-specific guidance for FastAPI, LangGraph, Supabase persistence, tools, prompts, and tests
---

## Backend Scope
This directory owns LangGraph behavior, LLM/tool orchestration, TMDB filtering, public mediatheken search, prompt templates, shared state, and Supabase persistence helpers. `main.py` at the repo root is also backend code.

## Core Files
- `../main.py`: FastAPI request/response models, auth dependencies, chat invocation, filter preference endpoints.
- `graph.py`: graph construction, node functions, prompt-mode selection, model setup.
- `tools.py`: LangChain tools and tool-selection helpers.
- `prompts.py`: prompt text for analyst, researcher, mediatheken, combined availability, scope guard.
- `states.py`: LangGraph state contract.
- `utils/helper.py`: provider normalization and request helper logic.
- `utils/tmdb/tmdb_api_client.py`: TMDB availability lookups, retries, provider filtering.
- `persistence/`: Supabase REST services for conversations, messages, and user preferences.

## Backend Principles
- Keep graph state explicit. Add state fields only when they are needed across nodes or tests.
- Preserve legacy payload compatibility where practical, especially chat/filter payloads used by the frontend.
- Tool selection must be deterministic and tested. Mediathek-only, streaming-only, and combined availability should route to distinct tool sets.
- TMDB checks commercial streaming providers only. Public mediatheken are web-evidence based and must not be treated as TMDB providers.
- Do not invent mediatheken deep links. Only surface official URLs returned by grounded search evidence.
- If prompt behavior changes, update tests for prompt mode or tool-selection behavior in the same change.

## LLM And Tools
- Chat models are initialized in `graph.py`; search grounding is called directly in `tools.py`.
- OpenAI is the active LLM/search provider. Keep `LLM_PROVIDER`, `OPENAI_MODEL_FAST`, `OPENAI_MODEL_RESEARCH`, and `OPENAI_WEB_SEARCH_CONTEXT` synchronized across code, Docker, docs, and tests.
- `filter_streaming_providers` expects candidate titles and real streaming providers.
- `search_public_mediatheken` should restrict evidence to public broadcaster domains such as ARD, ZDF, Arte, and 3sat.
- Existing structured error returns for web search should prevent chat crashes. Preserve this behavior.

## Persistence And Migrations
- Supabase persistence uses REST helpers in `persistence/`; use service role only on the backend.
- Add SQL migrations under `../supabase/migrations/` for DB schema changes.
- Include tests for select/upsert payload changes, especially user filter preferences.
- Remember to run `docker compose run --rm supabase-migrations` for local Docker schema changes.

## Testing
- Common focused backend tests:
  - `uv run pytest tests/test_tools.py -q`
  - `uv run pytest tests/test_tool_selection.py tests/test_prompt_modes.py -q`
  - `uv run pytest tests/test_user_filter_preferences_service.py -q`
  - `uv run pytest tests/test_auth_guard.py -q`
- Run `uv run pytest -q` for graph/tool/persistence changes before final response.
- Tests should mock external APIs. Do not depend on live OpenAI, TMDB, or Supabase network calls in unit tests.
- For backend feature or performance changes validated in Docker, inspect `docker compose logs --tail=200 backend`.
- For persistence, auth, migration, or schema changes, also inspect `docker compose logs --tail=200 supabase-rest supabase-auth supabase-db supabase-migrations`.
- Include a short Docker log summary in the final response, or say explicitly if logs could not be checked.
