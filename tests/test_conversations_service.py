import json
from urllib.error import HTTPError
from email.message import Message

import pytest

from backend.persistence.conversations import get_or_create_active_conversation, start_new_active_conversation


class DummyResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_get_or_create_active_conversation_returns_active_record(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    payload = {"id": "conv-1", "user_id": "user-1", "status": "active"}
    monkeypatch.setattr("backend.persistence.conversations.request.urlopen", lambda req, timeout: DummyResponse(payload))

    result = get_or_create_active_conversation(user_id="user-1", access_token="jwt-token")

    assert result["id"] == "conv-1"
    assert result["user_id"] == "user-1"
    assert result["status"] == "active"


def test_get_or_create_active_conversation_rejects_user_mismatch(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    payload = {"id": "conv-1", "user_id": "other-user", "status": "active"}
    monkeypatch.setattr("backend.persistence.conversations.request.urlopen", lambda req, timeout: DummyResponse(payload))

    with pytest.raises(RuntimeError, match="Conversation user mismatch"):
        get_or_create_active_conversation(user_id="user-1", access_token="jwt-token")


def test_get_or_create_active_conversation_handles_rpc_error(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    def raise_http_error(req, timeout):
        raise HTTPError(url="http://localhost", code=500, msg="error", hdrs=Message(), fp=None)

    monkeypatch.setattr("backend.persistence.conversations.request.urlopen", raise_http_error)

    with pytest.raises(RuntimeError, match="Failed to call conversations RPC: get_or_create_active_conversation"):
        get_or_create_active_conversation(user_id="user-1", access_token="jwt-token")


def test_start_new_active_conversation_returns_active_record(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    payload = {"id": "conv-new-1", "user_id": "user-1", "status": "active"}
    monkeypatch.setattr("backend.persistence.conversations.request.urlopen", lambda req, timeout: DummyResponse(payload))

    result = start_new_active_conversation(user_id="user-1", access_token="jwt-token")

    assert result["id"] == "conv-new-1"
    assert result["user_id"] == "user-1"
    assert result["status"] == "active"


def test_start_new_active_conversation_rejects_user_mismatch(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    payload = {"id": "conv-new-1", "user_id": "other-user", "status": "active"}
    monkeypatch.setattr("backend.persistence.conversations.request.urlopen", lambda req, timeout: DummyResponse(payload))

    with pytest.raises(RuntimeError, match="Conversation user mismatch"):
        start_new_active_conversation(user_id="user-1", access_token="jwt-token")
