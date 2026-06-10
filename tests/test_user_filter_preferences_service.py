import json

from backend.persistence.user_filter_preferences import (
    get_user_filter_preferences,
    upsert_user_filter_preferences,
)


class DummyResponse:
    def __init__(self, payload: list[dict]):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_get_user_filter_preferences_reads_include_mediatheken(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    row = {
        "user_id": "user-1",
        "source": "streaming",
        "providers": ["Netflix"],
        "payment_types": ["free"],
        "include_mediatheken": True,
        "updated_at": "2026-06-10T12:00:00Z",
    }
    monkeypatch.setattr("backend.persistence.user_filter_preferences.request.urlopen", lambda req, timeout: DummyResponse([row]))

    result = get_user_filter_preferences(user_id="user-1", access_token="jwt-token")

    assert result is not None
    assert result["include_mediatheken"] is True


def test_upsert_user_filter_preferences_writes_include_mediatheken(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    captured_payload: dict = {}

    def fake_urlopen(req, timeout):
        captured_payload.update(json.loads(req.data.decode("utf-8")))
        return DummyResponse([
            {
                "user_id": "user-1",
                "source": "streaming",
                "providers": ["Netflix"],
                "payment_types": ["free"],
                "include_mediatheken": True,
            }
        ])

    monkeypatch.setattr("backend.persistence.user_filter_preferences.request.urlopen", fake_urlopen)

    result = upsert_user_filter_preferences(
        user_id="user-1",
        access_token="jwt-token",
        source="streaming",
        providers=["Netflix"],
        payment_types=["free"],
        include_mediatheken=True,
    )

    assert captured_payload["include_mediatheken"] is True
    assert result["include_mediatheken"] is True
