import json
from typing import Any
from urllib import parse, request

from backend.utils.setupenv import get_required_env_value, normalize_url_for_runtime


def get_user_filter_preferences(*, user_id: str, access_token: str) -> dict[str, Any] | None:
    supabase_url = normalize_url_for_runtime(get_required_env_value("SUPABASE_URL"))
    supabase_anon_key = get_required_env_value("SUPABASE_ANON_KEY")

    query = parse.urlencode(
        {
            "select": "user_id,source,providers,payment_types,updated_at",
            "user_id": f"eq.{user_id}",
            "limit": "1",
        }
    )
    endpoint = f"{supabase_url.rstrip('/')}/rest/v1/user_filter_preferences?{query}"

    req = request.Request(
        endpoint,
        method="GET",
        headers={
            "Content-Type": "application/json",
            "apikey": supabase_anon_key,
            "Authorization": f"Bearer {access_token}",
        },
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
    except Exception as exc:
        raise RuntimeError("Failed to fetch user filter preferences") from exc

    try:
        rows = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid filter preferences payload from Supabase") from exc

    if not isinstance(rows, list):
        raise RuntimeError("Unexpected filter preferences select result format")

    if not rows:
        return None

    row = rows[0]
    if not isinstance(row, dict):
        raise RuntimeError("Invalid filter preferences row format")

    if str(row.get("user_id", "")) != str(user_id):
        raise RuntimeError("Filter preferences user mismatch")

    return row


def upsert_user_filter_preferences(
    *,
    user_id: str,
    access_token: str,
    source: str,
    providers: list[str],
    payment_types: list[str],
) -> dict[str, Any]:
    supabase_url = normalize_url_for_runtime(get_required_env_value("SUPABASE_URL"))
    supabase_anon_key = get_required_env_value("SUPABASE_ANON_KEY")

    endpoint = f"{supabase_url.rstrip('/')}/rest/v1/user_filter_preferences"
    payload_obj = {
        "user_id": user_id,
        "source": source,
        "providers": providers,
        "payment_types": payment_types,
    }
    payload = json.dumps(payload_obj).encode("utf-8")

    req = request.Request(
        endpoint,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation",
            "apikey": supabase_anon_key,
            "Authorization": f"Bearer {access_token}",
        },
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
    except Exception as exc:
        raise RuntimeError("Failed to upsert user filter preferences") from exc

    try:
        rows = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid filter preferences upsert payload from Supabase") from exc

    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Unexpected filter preferences upsert result format")

    row = rows[0]
    if not isinstance(row, dict):
        raise RuntimeError("Invalid filter preferences row format")

    if str(row.get("user_id", "")) != str(user_id):
        raise RuntimeError("Filter preferences user mismatch")

    return row
