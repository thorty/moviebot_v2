import json
from typing import Any
from urllib import parse, request
from urllib.error import HTTPError

from backend.utils.setupenv import get_required_env_value, normalize_url_for_runtime


WATCHLIST_SELECT_FIELDS = (
    "id,user_id,title,title_key,media_type,description,cover_url,rating,rating_source,"
    "streaming_providers,created_at,updated_at"
)


def _supabase_rest_base() -> tuple[str, str]:
    supabase_url = normalize_url_for_runtime(get_required_env_value("SUPABASE_URL"))
    supabase_anon_key = get_required_env_value("SUPABASE_ANON_KEY")
    return supabase_url.rstrip("/"), supabase_anon_key


def _request_headers(access_token: str, prefer: str | None = None) -> dict[str, str]:
    _supabase_url, supabase_anon_key = _supabase_rest_base()
    headers = {
        "Content-Type": "application/json",
        "apikey": supabase_anon_key,
        "Authorization": f"Bearer {access_token}",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def _parse_rows(body: str, context: str) -> list[dict[str, Any]]:
    try:
        rows = json.loads(body or "[]")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid {context} payload from Supabase") from exc

    if not isinstance(rows, list):
        raise RuntimeError(f"Unexpected {context} result format")

    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError(f"Invalid {context} row format")

    return rows


def _ensure_user_rows(rows: list[dict[str, Any]], user_id: str, context: str) -> None:
    for row in rows:
        if str(row.get("user_id", "")) != str(user_id):
            raise RuntimeError(f"{context} user mismatch")


def list_watchlist_items(*, user_id: str, access_token: str) -> list[dict[str, Any]]:
    supabase_url, _supabase_anon_key = _supabase_rest_base()

    query = parse.urlencode(
        {
            "select": WATCHLIST_SELECT_FIELDS,
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc",
        }
    )
    endpoint = f"{supabase_url}/rest/v1/watchlist_items?{query}"
    req = request.Request(
        endpoint,
        method="GET",
        headers=_request_headers(access_token),
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
    except Exception as exc:
        raise RuntimeError("Failed to fetch watchlist items") from exc

    rows = _parse_rows(body, "watchlist select")
    _ensure_user_rows(rows, user_id, "Watchlist")
    return rows


def upsert_watchlist_item(
    *,
    user_id: str,
    access_token: str,
    title: str,
    title_key: str,
    media_type: str,
    description: str,
    cover_url: str | None,
    rating: float | None,
    rating_source: str | None,
    streaming_providers: list[str],
) -> dict[str, Any]:
    supabase_url, _supabase_anon_key = _supabase_rest_base()

    query = parse.urlencode({"on_conflict": "user_id,title_key,media_type"})
    endpoint = f"{supabase_url}/rest/v1/watchlist_items?{query}"
    payload_obj = {
        "user_id": user_id,
        "title": title,
        "title_key": title_key,
        "media_type": media_type,
        "description": description,
        "cover_url": cover_url,
        "rating": rating,
        "rating_source": rating_source,
        "streaming_providers": streaming_providers,
    }
    payload = json.dumps(payload_obj).encode("utf-8")
    req = request.Request(
        endpoint,
        data=payload,
        method="POST",
        headers=_request_headers(access_token, "resolution=merge-duplicates,return=representation"),
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
    except Exception as exc:
        raise RuntimeError("Failed to upsert watchlist item") from exc

    rows = _parse_rows(body, "watchlist upsert")
    if not rows:
        raise RuntimeError("Unexpected watchlist upsert result format")
    _ensure_user_rows(rows, user_id, "Watchlist")
    return rows[0]


def delete_watchlist_item(*, user_id: str, access_token: str, item_id: str) -> dict[str, Any] | None:
    supabase_url, _supabase_anon_key = _supabase_rest_base()

    query = parse.urlencode(
        {
            "id": f"eq.{item_id}",
            "user_id": f"eq.{user_id}",
        }
    )
    endpoint = f"{supabase_url}/rest/v1/watchlist_items?{query}"
    req = request.Request(
        endpoint,
        method="DELETE",
        headers=_request_headers(access_token, "return=representation"),
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise RuntimeError("Failed to delete watchlist item") from exc
    except Exception as exc:
        raise RuntimeError("Failed to delete watchlist item") from exc

    rows = _parse_rows(body, "watchlist delete")
    if not rows:
        return None
    _ensure_user_rows(rows, user_id, "Watchlist")
    return rows[0]
