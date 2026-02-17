from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

import jwt

from main import app


client = TestClient(app)


def test_chat_without_token_returns_401() -> None:
    response = client.post("/api/v1/chat", json={"message": "Hi"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"


def test_chat_with_invalid_token_returns_403(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_JWT_SECRET", "local-test-secret")

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
        json={"message": "Hi"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid or expired token"


def test_chat_with_valid_token_returns_200(monkeypatch) -> None:
    secret = "local-test-secret"
    monkeypatch.setenv("SUPABASE_JWT_SECRET", secret)
    monkeypatch.setattr(
        "main.get_or_create_active_conversation",
        lambda user_id, access_token: {"id": "conv-123", "user_id": user_id, "status": "active"},
    )
    monkeypatch.setattr("main.invoke_user_chat", lambda user_id, conversation_id, payload: "stubbed reply")

    payload = {
        "sub": "user-123",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "role": "authenticated",
    }
    token = jwt.encode(payload, secret, algorithm="HS256")

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Hi"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["user_id"] == "user-123"
    assert body["conversation_id"] == "conv-123"
    assert body["reply"] == "stubbed reply"


def test_chat_with_valid_token_and_extra_claims_returns_200(monkeypatch) -> None:
    secret = "local-test-secret"
    monkeypatch.setenv("SUPABASE_JWT_SECRET", secret)
    monkeypatch.setattr(
        "main.get_or_create_active_conversation",
        lambda user_id, access_token: {"id": "conv-456", "user_id": user_id, "status": "active"},
    )
    monkeypatch.setattr("main.invoke_user_chat", lambda user_id, conversation_id, payload: "stubbed reply")

    payload = {
        "sub": "user-456",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "role": "authenticated",
        "email": "user456@example.com",
        "app_metadata": {"provider": "email"},
    }
    token = jwt.encode(payload, secret, algorithm="HS256")

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Hi"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "accepted"
    assert body["user_id"] == "user-456"
    assert body["conversation_id"] == "conv-456"
    assert body["reply"] == "stubbed reply"


def test_chat_forwards_jwt_sub_into_backend_flow(monkeypatch) -> None:
    secret = "local-test-secret"
    monkeypatch.setenv("SUPABASE_JWT_SECRET", secret)

    forwarded: dict[str, str] = {}

    monkeypatch.setattr(
        "main.get_or_create_active_conversation",
        lambda user_id, access_token: {"id": "conv-flow", "user_id": user_id, "status": "active"},
    )

    def fake_invoke_user_chat(user_id, conversation_id, payload):
        forwarded["user_id"] = user_id
        forwarded["conversation_id"] = conversation_id
        return "ok"

    monkeypatch.setattr("main.invoke_user_chat", fake_invoke_user_chat)

    payload = {
        "sub": "flow-user-999",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "role": "authenticated",
    }
    token = jwt.encode(payload, secret, algorithm="HS256")

    response = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Hi"},
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == "flow-user-999"
    assert response.json()["conversation_id"] == "conv-flow"
    assert forwarded["user_id"] == "flow-user-999"
    assert forwarded["conversation_id"] == "conv-flow"


def test_chat_same_user_reuses_single_active_conversation(monkeypatch) -> None:
    secret = "local-test-secret"
    monkeypatch.setenv("SUPABASE_JWT_SECRET", secret)

    calls: list[str] = []
    active_conversations: dict[str, str] = {}

    def fake_get_or_create_active_conversation(user_id, access_token):
        calls.append(user_id)
        conversation_id = active_conversations.setdefault(user_id, "conv-single")
        return {"id": conversation_id, "user_id": user_id, "status": "active"}

    monkeypatch.setattr("main.get_or_create_active_conversation", fake_get_or_create_active_conversation)
    monkeypatch.setattr("main.invoke_user_chat", lambda user_id, conversation_id, payload: "ok")

    payload = {
        "sub": "same-user-1",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "role": "authenticated",
    }
    token = jwt.encode(payload, secret, algorithm="HS256")

    response_1 = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Hi"},
    )
    response_2 = client.post(
        "/api/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "Noch mal"},
    )

    assert response_1.status_code == 200
    assert response_2.status_code == 200
    assert response_1.json()["conversation_id"] == "conv-single"
    assert response_2.json()["conversation_id"] == "conv-single"
    assert calls == ["same-user-1", "same-user-1"]
