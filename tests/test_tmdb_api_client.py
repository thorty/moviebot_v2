import importlib
import json
import sys


def _load_tmdb_module(monkeypatch):
    monkeypatch.setenv("tmdb_bearer", "test-token")
    module_name = "backend.utils.tmdb.tmdb_api_client"
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


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

    monkeypatch.setattr(tmdb_api_client, "find_movie", lambda *args, **kwargs: movie)

    def _unexpected_provider_call(*args, **kwargs):
        raise AssertionError("Expected appended watch/providers payload to be used")

    monkeypatch.setattr(tmdb_api_client, "get_watch_providers", _unexpected_provider_call)

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

    monkeypatch.setattr(tmdb_api_client, "find_movie", lambda *args, **kwargs: movie)

    provider_calls = []

    def _provider_fallback(*args, **kwargs):
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

    monkeypatch.setattr(tmdb_api_client, "get_watch_providers", _provider_fallback)

    result = tmdb_api_client.create_movie_data("Fallback Movie")

    assert len(provider_calls) == 1
    assert result["flatproviders"] == ["Disney Plus"]
    assert result["rentproviders"] == []
    assert result["buyproviders"] == []