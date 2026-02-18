import json
from typing import Any
from urllib import request
from urllib.error import HTTPError

from backend.utils.setupenv import get_required_env_value, normalize_url_for_runtime


def _call_conversation_rpc(rpc_name: str, access_token: str) -> dict[str, Any]:
    supabase_url = normalize_url_for_runtime(get_required_env_value("SUPABASE_URL"))
    supabase_anon_key = get_required_env_value("SUPABASE_ANON_KEY")

    rpc_url = f"{supabase_url.rstrip('/')}/rest/v1/rpc/{rpc_name}"
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
    except HTTPError as exc:
        error_body = ""
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:
            pass
        detail = f"status={exc.code}"
        if error_body:
            detail = f"{detail}, body={error_body}"
        raise RuntimeError(f"Failed to call conversations RPC: {rpc_name} ({detail})") from exc
    except Exception as exc:
        raise RuntimeError(f"Failed to call conversations RPC: {rpc_name}") from exc

    try:
        conversation = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Invalid conversation payload from Supabase RPC") from exc

    if not isinstance(conversation, dict):
        raise RuntimeError("Unexpected Supabase RPC result format")

    return conversation


def get_or_create_active_conversation(user_id: str, access_token: str) -> dict[str, Any]:
    conversation = _call_conversation_rpc(
        rpc_name="get_or_create_active_conversation",
        access_token=access_token,
    )

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


def start_new_active_conversation(user_id: str, access_token: str) -> dict[str, Any]:
    conversation = _call_conversation_rpc(
        rpc_name="start_new_active_conversation",
        access_token=access_token,
    )

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
