import json
from typing import Any
from urllib import request

from backend.utils.setupenv import get_required_env_value, normalize_url_for_runtime

VALID_ROLES = {"user", "assistant", "system", "tool"}


def append_message_log(
    *,
    conversation_id: str,
    user_id: str,
    access_token: str,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if role not in VALID_ROLES:
        raise RuntimeError(f"Invalid message role: {role}")

    normalized_content = content.strip()
    if not normalized_content:
        raise RuntimeError("Message content must not be empty")

    supabase_url = normalize_url_for_runtime(get_required_env_value("SUPABASE_URL"))
    supabase_anon_key = get_required_env_value("SUPABASE_ANON_KEY")

    insert_url = f"{supabase_url.rstrip('/')}/rest/v1/message_logs"
    payload_obj = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "role": role,
        "content": normalized_content,
        "metadata": metadata or {},
    }
    payload = json.dumps(payload_obj).encode("utf-8")

    req = request.Request(
        insert_url,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Prefer": "return=representation",
            "apikey": supabase_anon_key,
            "Authorization": f"Bearer {access_token}",
        },
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            body = response.read().decode("utf-8")
    except Exception as exc:
        raise RuntimeError("Failed to append message log") from exc

    try:
        rows = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid message_logs payload from Supabase") from exc

    if not isinstance(rows, list) or not rows:
        raise RuntimeError("Unexpected message_logs insert result format")

    row = rows[0]
    if not isinstance(row, dict):
        raise RuntimeError("Invalid message_logs row format")

    if str(row.get("conversation_id", "")) != str(conversation_id):
        raise RuntimeError("Message log conversation mismatch")
    if str(row.get("user_id", "")) != str(user_id):
        raise RuntimeError("Message log user mismatch")
    if row.get("role") != role:
        raise RuntimeError("Message log role mismatch")

    return row
