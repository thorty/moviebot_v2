import json
from email.message import Message
from urllib.error import HTTPError

import pytest

from backend.persistence.message_logs import append_message_log


class DummyResponse:
    def __init__(self, payload: list[dict]):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_append_message_log_inserts_user_message(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    row = {
        "id": 11,
        "conversation_id": "conv-1",
        "user_id": "user-1",
        "role": "user",
        "content": "hello",
        "metadata": {},
    }
    monkeypatch.setattr("backend.persistence.message_logs.request.urlopen", lambda req, timeout: DummyResponse([row]))

    result = append_message_log(
        conversation_id="conv-1",
        user_id="user-1",
        access_token="jwt-token",
        role="user",
        content="hello",
    )

    assert result["id"] == 11
    assert result["role"] == "user"


def test_append_message_log_rejects_invalid_role(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    with pytest.raises(RuntimeError, match="Invalid message role"):
        append_message_log(
            conversation_id="conv-1",
            user_id="user-1",
            access_token="jwt-token",
            role="invalid",
            content="hello",
        )


def test_append_message_log_handles_insert_error(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    def raise_http_error(req, timeout):
        raise HTTPError(url="http://localhost", code=500, msg="error", hdrs=Message(), fp=None)

    monkeypatch.setattr("backend.persistence.message_logs.request.urlopen", raise_http_error)

    with pytest.raises(RuntimeError, match="Failed to append message log"):
        append_message_log(
            conversation_id="conv-1",
            user_id="user-1",
            access_token="jwt-token",
            role="assistant",
            content="hello",
        )
