import re
from typing import Any


PUBLIC_MEDIATHEK_SERVICES = ("ARD Mediathek", "ZDF Mediathek", "Arte", "3sat")
VALID_RECOMMENDATION_MEDIA_TYPES = {"movie", "documentary", "series"}
SENTINEL_PROVIDER_NAMES = {"mediathek", "mediatheken"}

TITLE_LINE_RE = re.compile(
    r"(?m)(?:^\s*!\[[^\]]*\]\((?P<poster_url>[^)]+)\)\s*\n)?"
    r"^\s*🎬\s*\*\*(?P<title>[^*\n]+?)\*\*\s*(?:\[(?P<label>[^\]]+)\])?",
)
YEAR_SUFFIX_RE = re.compile(r"\s*\((?:19|20)\d{2}(?:\s*[-–]\s*(?:19|20)\d{2})?\)\s*$")
RATING_RE = re.compile(r"TMDB-Bewertung:\*\*\s*(?P<rating>\d+(?:[,.]\d+)?)\s*/\s*10", re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def normalize_title_key(title: str) -> str:
    """Normalize a display title for user-scoped watchlist de-duplication."""
    text = str(title or "").casefold()
    text = re.sub(r"[^\w\s]+", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def normalize_recommendation_media_type(value: str, fallback: str = "movie") -> str:
    normalized = str(value or "").strip().casefold()
    fallback = fallback if fallback in VALID_RECOMMENDATION_MEDIA_TYPES else "movie"

    exact_labels = {
        "film": "movie",
        "movie": "movie",
        "serie": "series",
        "series": "series",
        "tv": "series",
        "tv show": "series",
        "doku": "documentary",
        "dokumentation": "documentary",
        "documentary": "documentary",
    }
    if normalized in exact_labels:
        return exact_labels[normalized]

    matches: list[str] = []
    if "doku" in normalized or "documentary" in normalized:
        matches.append("documentary")
    if "serie" in normalized or "series" in normalized or "tv" in normalized:
        matches.append("series")
    if "film" in normalized or "movie" in normalized:
        matches.append("movie")

    unique_matches = list(dict.fromkeys(matches))
    if len(unique_matches) == 1:
        return unique_matches[0]
    if fallback in unique_matches or not unique_matches:
        return fallback
    return unique_matches[0]


def map_tool_media_type(value: Any) -> str:
    normalized = str(value or "").strip().casefold()
    if normalized == "tv":
        return "series"
    if normalized in VALID_RECOMMENDATION_MEDIA_TYPES:
        return normalized
    return "movie"


def _clean_title(raw_title: str) -> str:
    title = str(raw_title or "").strip()
    title = YEAR_SUFFIX_RE.sub("", title).strip()
    return title.strip("[] ")


def _plain_markdown_text(line: str) -> str:
    text = MARKDOWN_LINK_RE.sub(r"\1", str(line or ""))
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = text.strip().strip("*_").strip()
    return text


def _extract_description(block: str) -> str:
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lowered = line.casefold()
        if (
            "🎬" in line
            or line.startswith("![")
            or line.startswith("**TMDB-Bewertung")
            or line.startswith("**Verfügbar")
            or line.startswith("•")
            or line.startswith("-")
            or set(line) <= {"-"}
            or "tmdb-bewertung" in lowered
            or "verfügbar" in lowered
        ):
            continue

        description = _plain_markdown_text(line)
        if description:
            return description

    return ""


def _extract_rating(block: str) -> float | None:
    match = RATING_RE.search(block)
    if not match:
        return None

    try:
        rating = float(match.group("rating").replace(",", "."))
    except ValueError:
        return None

    if rating < 0 or rating > 10:
        return None
    return rating


def _dedupe_providers(providers: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for provider in providers:
        name = str(provider or "").strip()
        key = name.casefold()
        if not name or key in seen or key in SENTINEL_PROVIDER_NAMES:
            continue
        seen.add(key)
        result.append(name)
    return result


def _extract_tool_providers(row: dict[str, Any] | None) -> list[str]:
    if not row:
        return []
    providers = []
    providers.extend(row.get("flatproviders") or [])
    providers.extend(row.get("rentproviders") or [])
    providers.extend(row.get("buyproviders") or [])
    return _dedupe_providers(providers)


def _extract_providers_from_block(block: str) -> list[str]:
    providers: list[str] = []

    for service in PUBLIC_MEDIATHEK_SERVICES:
        if service.casefold() in block.casefold():
            providers.append(service)

    for raw_line in block.splitlines():
        if "🎬" in raw_line or raw_line.strip().startswith("!["):
            continue
        line = _plain_markdown_text(raw_line).strip(" •-")
        if not line or not any(symbol in line for symbol in (":", "🟢", "🟡", "🔴")):
            continue

        provider = re.split(r":|🟢|🟡|🔴", line, maxsplit=1)[0].strip()
        if provider and provider.casefold() not in {"verfügbar auf", "verfügbar in"}:
            providers.append(provider)

    return _dedupe_providers(providers)


def _build_tool_title_map(filter_results: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(filter_results, dict):
        return {}

    title_map: dict[str, dict[str, Any]] = {}
    for row in filter_results.get("available_titles") or []:
        if not isinstance(row, dict):
            continue
        title_key = normalize_title_key(str(row.get("title", "")))
        if title_key and title_key not in title_map:
            title_map[title_key] = row
    return title_map


def extract_recommendations_from_reply(
    reply: str,
    *,
    filter_results: dict[str, Any] | None = None,
    mediatheken_results: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Extract watchlist candidates that were actually presented in the final reply."""
    text = str(reply or "")
    if not text:
        return []

    tool_title_map = _build_tool_title_map(filter_results)
    matches = list(TITLE_LINE_RE.finditer(text))
    recommendations: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for index, match in enumerate(matches):
        title = _clean_title(match.group("title"))
        title_key = normalize_title_key(title)
        if not title_key:
            continue

        block_start = match.start()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[block_start:block_end]

        tool_row = tool_title_map.get(title_key)
        fallback_media_type = map_tool_media_type(tool_row.get("media_type") if tool_row else "")
        media_type = normalize_recommendation_media_type(match.group("label") or "", fallback_media_type)

        description = _extract_description(block)
        if not description and tool_row:
            description = str(tool_row.get("overview") or "").strip()

        rating = _extract_rating(block)
        if rating is None and tool_row:
            raw_rating = tool_row.get("vote_average")
            if isinstance(raw_rating, (int, float)) and raw_rating > 0:
                rating = float(raw_rating)

        providers = _extract_tool_providers(tool_row) or _extract_providers_from_block(block)
        if not providers or not description:
            continue

        cover_url = str(match.group("poster_url") or "").strip()
        if not cover_url and tool_row:
            cover_url = str(tool_row.get("poster_url") or "").strip()

        unique_key = (title_key, media_type)
        if unique_key in seen:
            continue
        seen.add(unique_key)

        recommendations.append(
            {
                "title": title,
                "media_type": media_type,
                "description": description,
                "cover_url": cover_url or None,
                "rating": rating,
                "rating_source": "TMDB" if rating is not None else None,
                "streaming_providers": providers,
            }
        )

    return recommendations
