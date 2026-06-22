import json
import importlib
import sys
import threading
from unittest.mock import Mock


class FakeAsyncClient:
    def __init__(self, responses):
        self._responses = iter(responses)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url):
        response = next(self._responses)
        if isinstance(response, Exception):
            raise response
        return response


def _load_tmdb_module(monkeypatch):
    monkeypatch.setenv("TMDB_BEARER", "test-token")
    module_name = "backend.utils.tmdb.tmdb_api_client"
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


def test_get_movie_form_search_prefers_tmdb_order_for_exact_original_title(monkeypatch):
    tmdb_api_client = _load_tmdb_module(monkeypatch)

    results = [
        {"id": 2756, "title": "Abyss - Abgrund des Todes", "original_title": "The Abyss"},
        {"id": 800753, "title": "The Abyss", "original_title": "The Abyss"},
    ]

    result = tmdb_api_client.get_movie_form_search(results, "The Abyss", "movie")

    assert result["id"] == 2756


def test_get_watch_provider_payload_from_appended_response(monkeypatch):
    tmdb_api_client = _load_tmdb_module(monkeypatch)

    payload = {
        "results": {
            "DE": {
                "flatrate": [{"provider_name": "Netflix"}],
            }
        }
    }

    result = tmdb_api_client.get_watch_provider_payload({"watch/providers": payload})

    assert json.loads(result) == payload


def test_create_movie_data_prefers_appended_watch_providers(monkeypatch):
    tmdb_api_client = _load_tmdb_module(monkeypatch)

    movie = {
        "id": 123,
        "title": "Test Movie",
        "watch/providers": {
            "results": {
                "DE": {
                    "flatrate": [{"provider_name": "Netflix"}],
                    "rent": [{"provider_name": "Apple TV"}],
                    "buy": [{"provider_name": "Amazon Video"}],
                }
            }
        },
        "genres": [{"name": "Sci-Fi"}],
        "production_countries": [{"name": "Germany"}],
        "overview": "Overview",
        "release_date": "2024-01-01",
        "runtime": 120,
        "vote_average": 8.5,
        "vote_count": 100,
    }

    async def _fake_find_movie_async(*args, **kwargs):
        return movie

    async def _unexpected_provider_call(*args, **kwargs):
        raise AssertionError("Expected appended watch/providers payload to be used")

    monkeypatch.setattr(tmdb_api_client, "_find_movie_async", _fake_find_movie_async)
    monkeypatch.setattr(tmdb_api_client, "_get_watch_providers_async", _unexpected_provider_call)

    result = tmdb_api_client.create_movie_data("Test Movie")

    assert result["title"] == "Test Movie"
    assert result["flatproviders"] == ["Netflix"]
    assert result["rentproviders"] == ["Apple TV"]
    assert result["buyproviders"] == ["Amazon Video"]
    assert result["genres"] == ["Sci-Fi"]
    assert result["production_countries"] == ["Germany"]


def test_create_movie_data_falls_back_to_provider_endpoint(monkeypatch):
    tmdb_api_client = _load_tmdb_module(monkeypatch)

    movie = {
        "id": 456,
        "title": "Fallback Movie",
        "genres": [],
        "production_countries": [],
        "overview": "Overview",
        "release_date": "2024-01-01",
    }

    async def _fake_find_movie_async(*args, **kwargs):
        return movie

    provider_calls = []

    async def _provider_fallback(*args, **kwargs):
        provider_calls.append((args, kwargs))
        return json.dumps(
            {
                "results": {
                    "DE": {
                        "flatrate": [{"provider_name": "Disney Plus"}],
                    }
                }
            }
        )

    monkeypatch.setattr(tmdb_api_client, "_find_movie_async", _fake_find_movie_async)
    monkeypatch.setattr(tmdb_api_client, "_get_watch_providers_async", _provider_fallback)

    result = tmdb_api_client.create_movie_data("Fallback Movie")

    assert len(provider_calls) == 1
    assert result["flatproviders"] == ["Disney Plus"]
    assert result["rentproviders"] == []
    assert result["buyproviders"] == []


def test_create_basic_movie_data_keeps_appended_recommendations(monkeypatch):
    tmdb_api_client = _load_tmdb_module(monkeypatch)

    movie = {
        "id": 789,
        "title": "Seed Movie",
        "watch/providers": {
            "results": {
                "DE": {
                    "flatrate": [{"provider_name": "Netflix"}],
                }
            }
        },
        "recommendations": {
            "results": [{"id": 99, "title": "Recommended Movie", "overview": "Rec", "release_date": "2025-01-01"}]
        },
        "overview": "Seed overview",
        "poster_path": "/seed-poster.jpg",
        "release_date": "2024-01-01",
        "vote_average": 7.8,
        "vote_count": 123,
    }

    async def _fake_find_movie_basic_async(*args, **kwargs):
        return movie

    async def _unexpected_provider_call(*args, **kwargs):
        raise AssertionError("Expected appended watch/providers payload to be used")

    monkeypatch.setattr(tmdb_api_client, "_find_movie_basic_async", _fake_find_movie_basic_async)
    monkeypatch.setattr(tmdb_api_client, "_get_watch_providers_async", _unexpected_provider_call)

    result = tmdb_api_client.create_basic_movie_data(
        "Seed Movie",
        append_responses=["watch/providers", "recommendations"],
    )

    assert result["title"] == "Seed Movie"
    assert result["flatproviders"] == ["Netflix"]
    assert result["poster_path"] == "/seed-poster.jpg"
    assert result["poster_url"] == "https://image.tmdb.org/t/p/w342/seed-poster.jpg"
    assert result["vote_average"] == 7.8
    assert result["vote_count"] == 123
    assert result["_recommendations_payload"] == movie["recommendations"]


def test_get_recro_movies_prefers_appended_recommendations(monkeypatch):
    tmdb_api_client = _load_tmdb_module(monkeypatch)

    appended_recommendations = {
        "results": [{"id": 99, "title": "Recommended Movie", "overview": "Rec", "release_date": "2025-01-01"}]
    }
    movies = [{"id": 1, "_recommendations_payload": appended_recommendations}]

    async def _unexpected_find_similar(*args, **kwargs):
        raise AssertionError("Expected appended recommendations payload to be used")

    async def _fake_parse_movies_from_search(results, media_type="movie", client=None):
        return [{"title": results["results"][0]["title"], "media_type": media_type}]

    monkeypatch.setattr(tmdb_api_client, "_find_smilar_movies_async", _unexpected_find_similar)
    monkeypatch.setattr(tmdb_api_client, "_parse_movies_from_search_async", _fake_parse_movies_from_search)

    result = tmdb_api_client.get_recro_movies(movies, "movie")

    assert result == [{"title": "Recommended Movie", "media_type": "movie"}]


def test_get_movies_for_providers_preserves_input_order(monkeypatch):
    tmdb_api_client = _load_tmdb_module(monkeypatch)

    async def _resolve_title(title, media_type="movie", append_responses=None, client=None):
        if title == "Skip Me":
            return None
        return {
            "title": title,
            "flatproviders": [],
            "rentproviders": [],
            "overview": f"Overview {title}",
            "release_date": "2024-01-01",
            "id": len(title),
            "media_type": media_type,
        }

    monkeypatch.setattr(tmdb_api_client, "_get_basic_data_from_tmdb_for_title_async", _resolve_title)

    result = tmdb_api_client.get_movies_for_providers(["First", "Skip Me", "Second"], [])

    assert [item["title"] for item in result] == ["First", "Second"]


def test_get_movies_with_recro_appends_only_seed_title(monkeypatch):
    tmdb_api_client = _load_tmdb_module(monkeypatch)

    calls = []
    lock = threading.Lock()

    async def _resolve_title(title, media_type="movie", append_responses=None, client=None):
        with lock:
            calls.append((title, tuple(append_responses) if append_responses else None))
        return {
            "title": title,
            "flatproviders": ["Netflix"],
            "rentproviders": [],
            "overview": f"Overview {title}",
            "release_date": "2024-01-01",
            "id": len(title),
            "media_type": media_type,
            "_recommendations_payload": {"results": []},
        }

    async def _fake_get_recro_movies(movies, media_type="movie", client=None):
        return []

    monkeypatch.setattr(tmdb_api_client, "_get_basic_data_from_tmdb_for_title_async", _resolve_title)
    monkeypatch.setattr(tmdb_api_client, "_get_recro_movies_async", _fake_get_recro_movies)

    result = tmdb_api_client.get_movies_with_recro(["Seed", "Other"], ["Netflix"])

    assert "Title: Seed" in result
    assert "Title: Other" in result
    assert sorted(calls) == [
        ("Other", None),
        ("Seed", ("watch/providers", "recommendations")),
    ]


def test_tmdb_get_retries_on_429_with_retry_after(monkeypatch):
    tmdb_api_client = _load_tmdb_module(monkeypatch)

    sleep_calls = []
    client = FakeAsyncClient(
        [
            Mock(status_code=429, text="{}", headers={"Retry-After": "0.25"}),
            Mock(status_code=200, text='{"ok": true}', headers={}),
        ]
    )

    async def _fake_sleep(delay):
        sleep_calls.append(delay)

    monkeypatch.setattr(tmdb_api_client.asyncio, "sleep", _fake_sleep)

    response = tmdb_api_client._run_async(tmdb_api_client._tmdb_get_async("https://example.test/tmdb", client))

    assert response.status_code == 200
    assert sleep_calls == [0.25]


def test_get_watch_providers_returns_empty_payload_after_exhausted_retries(monkeypatch):
    tmdb_api_client = _load_tmdb_module(monkeypatch)

    sleep_calls = []
    client = FakeAsyncClient([
        Mock(status_code=429, text="{}", headers={}),
        Mock(status_code=429, text="{}", headers={}),
        Mock(status_code=429, text="{}", headers={}),
        Mock(status_code=429, text="{}", headers={}),
    ])

    async def _fake_sleep(delay):
        sleep_calls.append(delay)

    monkeypatch.setattr(tmdb_api_client.asyncio, "sleep", _fake_sleep)
    monkeypatch.setattr(tmdb_api_client, "_make_async_client", lambda: client)

    payload = tmdb_api_client.get_watch_providers(1)

    assert json.loads(payload) == {"results": {}}
    assert len(sleep_calls) == tmdb_api_client.TMDB_MAX_RETRIES
