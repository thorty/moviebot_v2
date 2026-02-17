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


def test_chat_with_valid_token_and_extra_claims_returns_200(monkeypatch) -> None:
    secret = "local-test-secret"
    monkeypatch.setenv("SUPABASE_JWT_SECRET", secret)

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
