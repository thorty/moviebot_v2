import json
from typing import Any
from urllib import request

from backend.utils.setupenv import get_required_env_value, normalize_url_for_runtime


def get_or_create_active_conversation(user_id: str, access_token: str) -> dict[str, Any]:
    supabase_url = normalize_url_for_runtime(get_required_env_value("SUPABASE_URL"))
    supabase_anon_key = get_required_env_value("SUPABASE_ANON_KEY")

    rpc_url = f"{supabase_url.rstrip('/')}/rest/v1/rpc/get_or_create_active_conversation"
    payload = b"{}"
    req = request.Request(
        rpc_url,
        data=payload,
        method="POST",
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
        raise RuntimeError("Failed to get or create active conversation") from exc

    try:
        conversation = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid conversation payload from Supabase RPC") from exc

    if not isinstance(conversation, dict):
        raise RuntimeError("Unexpected Supabase RPC result format")

    conversation_id = conversation.get("id")
    conversation_user_id = conversation.get("user_id")
    conversation_status = conversation.get("status")

    if not conversation_id or not conversation_user_id:
        raise RuntimeError("Supabase RPC result missing conversation identity")

    if str(conversation_user_id) != str(user_id):
        raise RuntimeError("Conversation user mismatch")

    if conversation_status != "active":
        raise RuntimeError("Supabase RPC returned non-active conversation")

    return conversation
