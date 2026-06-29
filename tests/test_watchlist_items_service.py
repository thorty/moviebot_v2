import json
from email.message import Message
from urllib.error import HTTPError

import pytest

from backend.persistence.watchlist_items import (
    delete_watchlist_item,
    list_watchlist_items,
    upsert_watchlist_item,
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


def test_list_watchlist_items_returns_user_rows(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    row = {
        "id": "item-1",
        "user_id": "user-1",
        "title": "Inception",
        "title_key": "inception",
        "media_type": "movie",
        "description": "Dream heist",
        "cover_url": "https://image.tmdb.org/t/p/w342/inception.jpg",
        "rating": 8.4,
        "rating_source": "TMDB",
        "streaming_providers": ["Netflix"],
    }

    monkeypatch.setattr("backend.persistence.watchlist_items.request.urlopen", lambda req, timeout: DummyResponse([row]))

    result = list_watchlist_items(user_id="user-1", access_token="jwt-token")

    assert result == [row]


def test_list_watchlist_items_rejects_user_mismatch(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    row = {"id": "item-1", "user_id": "other-user", "title": "Inception"}
    monkeypatch.setattr("backend.persistence.watchlist_items.request.urlopen", lambda req, timeout: DummyResponse([row]))

    with pytest.raises(RuntimeError, match="Watchlist user mismatch"):
        list_watchlist_items(user_id="user-1", access_token="jwt-token")


def test_upsert_watchlist_item_writes_snapshot_payload(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    captured_payload: dict = {}
    captured_url = ""

    def fake_urlopen(req, timeout):
        nonlocal captured_url
        captured_url = req.full_url
        captured_payload.update(json.loads(req.data.decode("utf-8")))
        return DummyResponse([
            {
                "id": "item-1",
                "user_id": "user-1",
                **captured_payload,
            }
        ])

    monkeypatch.setattr("backend.persistence.watchlist_items.request.urlopen", fake_urlopen)

    result = upsert_watchlist_item(
        user_id="user-1",
        access_token="jwt-token",
        title="Inception",
        title_key="inception",
        media_type="movie",
        description="Dream heist",
        cover_url="https://image.tmdb.org/t/p/w342/inception.jpg",
        rating=8.4,
        rating_source="TMDB",
        streaming_providers=["Netflix"],
    )

    assert "on_conflict=user_id%2Ctitle_key%2Cmedia_type" in captured_url
    assert captured_payload["title_key"] == "inception"
    assert captured_payload["cover_url"] == "https://image.tmdb.org/t/p/w342/inception.jpg"
    assert captured_payload["streaming_providers"] == ["Netflix"]
    assert result["user_id"] == "user-1"


def test_delete_watchlist_item_returns_deleted_row(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    row = {"id": "item-1", "user_id": "user-1", "title": "Inception"}
    monkeypatch.setattr("backend.persistence.watchlist_items.request.urlopen", lambda req, timeout: DummyResponse([row]))

    result = delete_watchlist_item(user_id="user-1", access_token="jwt-token", item_id="item-1")

    assert result == row


def test_delete_watchlist_item_returns_none_for_missing_row(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    monkeypatch.setattr("backend.persistence.watchlist_items.request.urlopen", lambda req, timeout: DummyResponse([]))

    result = delete_watchlist_item(user_id="user-1", access_token="jwt-token", item_id="missing")

    assert result is None


def test_delete_watchlist_item_handles_delete_error(monkeypatch) -> None:
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")

    def raise_http_error(req, timeout):
        raise HTTPError(url="http://localhost", code=500, msg="error", hdrs=Message(), fp=None)

    monkeypatch.setattr("backend.persistence.watchlist_items.request.urlopen", raise_http_error)

    with pytest.raises(RuntimeError, match="Failed to delete watchlist item"):
        delete_watchlist_item(user_id="user-1", access_token="jwt-token", item_id="item-1")
