import os
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"

REQUIRED_ENV_GROUPS: dict[str, list[str]] = {
    "core": ["OPENAI_API_KEY", "TMDB_BEARER"],
    "search": ["TAVILY_API_KEY"],
    "supabase": ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_JWT_SECRET"],
    "app": ["BACKEND_API_URL", "FRONTEND_WEB_URL"],
}


def load_environment(env_file: str | Path = DEFAULT_ENV_PATH, override: bool = False) -> bool:
    """Load environment variables from a single, centralized env path."""
    env_path = Path(env_file)
    if not env_path.is_absolute():
        env_path = PROJECT_ROOT / env_path

    loaded = dotenv.load_dotenv(dotenv_path=env_path, override=override)
    normalize_legacy_env_keys()
    return loaded


def normalize_legacy_env_keys() -> None:
    """Keep old keys compatible while using uppercase canonical names."""
    if os.getenv("tmdb_bearer") and not os.getenv("TMDB_BEARER"):
        os.environ["TMDB_BEARER"] = os.environ["tmdb_bearer"]
    if os.getenv("TMDB_BEARER") and not os.getenv("tmdb_bearer"):
        os.environ["tmdb_bearer"] = os.environ["TMDB_BEARER"]


def get_missing_required_env(groups: list[str]) -> list[str]:
    """Return required env vars that are missing for the selected groups."""
    required_vars: list[str] = []
    for group in groups:
        required_vars.extend(REQUIRED_ENV_GROUPS.get(group, []))

    unique_required = sorted(set(required_vars))
    return [var for var in unique_required if not os.getenv(var)]


def validate_required_env(groups: list[str]) -> tuple[bool, list[str]]:
    """Validate required env vars for chosen groups and return (ok, missing)."""
    missing = get_missing_required_env(groups)
    return len(missing) == 0, missing


def get_required_env_value(name: str) -> str:
    """Return an env value or raise a clear error when missing."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip().strip('"').strip("'")


def normalize_url_for_runtime(url: str) -> str:
    """Rewrite loopback hosts for container runtime access when needed."""
    parsed = urlparse(url)
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        return url

    is_docker_runtime = os.path.exists("/.dockerenv")
    if not is_docker_runtime:
        return url

    host = "host.docker.internal"
    port_part = f":{parsed.port}" if parsed.port else ""
    netloc = f"{host}{port_part}"
    return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))


def enable_langsmith() -> None:
    """Enable LangSmith tracing only when API key is configured."""
    load_environment()
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    if not langsmith_key:
        return

    os.environ["LANGSMITH_TRACING"] = os.getenv("LANGSMITH_TRACING", "true")
    os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "moviebot")

