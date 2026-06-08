#tmdb api
# moviedb tool singe title search
import asyncio
from difflib import get_close_matches
import json
import os
import threading

import dotenv
import httpx

dotenv.load_dotenv()

headers = {
    "accept": "application/json",
    "Authorization": os.environ["tmdb_bearer"],
}

TMDB_MAX_CONCURRENCY = max(
    1,
    int(os.getenv("TMDB_MAX_CONCURRENCY", os.getenv("TMDB_MAX_WORKERS", "6"))),
)
TMDB_MAX_RETRIES = max(0, int(os.getenv("TMDB_MAX_RETRIES", "3")))
TMDB_RETRY_BACKOFF_SECONDS = max(0.0, float(os.getenv("TMDB_RETRY_BACKOFF_SECONDS", "1.0")))
TMDB_REQUEST_TIMEOUT_SECONDS = max(1.0, float(os.getenv("TMDB_REQUEST_TIMEOUT_SECONDS", "10.0")))
TMDB_RETRY_STATUS_CODES = {429, 500, 502, 503, 504}
TMDB_IMAGE_BASE_URL = os.getenv("TMDB_IMAGE_BASE_URL", "https://image.tmdb.org/t/p")
TMDB_POSTER_SIZE = os.getenv("TMDB_POSTER_SIZE", "w342")


def normalize_media_item(item, media_type="movie"):
    """Normalize TV show and movie data to consistent format"""
    if not item:
        return None

    if "name" in item and "title" not in item:
        item["title"] = item["name"]

    if "first_air_date" in item and "release_date" not in item:
        item["release_date"] = item["first_air_date"]

    return item


def build_tmdb_poster_url(poster_path: str | None) -> str:
    path = str(poster_path or "").strip()
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{TMDB_IMAGE_BASE_URL}/{TMDB_POSTER_SIZE}{path}"


def _extract_title_input(item):
    if isinstance(item, dict):
        return item.get("title"), item.get("media_type", "movie")

    return item, "movie"


def _get_concurrency_limit(task_count: int) -> int:
    return max(1, min(task_count, TMDB_MAX_CONCURRENCY))


def _make_async_client() -> httpx.AsyncClient:
    limits = httpx.Limits(
        max_connections=TMDB_MAX_CONCURRENCY,
        max_keepalive_connections=TMDB_MAX_CONCURRENCY,
    )
    timeout = httpx.Timeout(TMDB_REQUEST_TIMEOUT_SECONDS)
    return httpx.AsyncClient(headers=headers, limits=limits, timeout=timeout)


def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result = {}
    error = {}

    def runner():
        try:
            result["value"] = asyncio.run(coro)
        except Exception as exc:  # pragma: no cover
            error["value"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()

    if "value" in error:
        raise error["value"]

    return result.get("value")


async def _collect_parallel_results_async(items, worker):
    if not items:
        return []

    if len(items) == 1:
        result = await worker(items[0])
        return [result] if result else []

    semaphore = asyncio.Semaphore(_get_concurrency_limit(len(items)))

    async def guarded_worker(item):
        async with semaphore:
            return await worker(item)

    results = await asyncio.gather(*(guarded_worker(item) for item in items))
    return [result for result in results if result]


def _get_retry_delay(response, attempt: int) -> float:
    retry_after = None
    if response is not None:
        retry_after = response.headers.get("Retry-After")

    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            pass

    return TMDB_RETRY_BACKOFF_SECONDS * (2 ** attempt)


async def _tmdb_get_async(url: str, client: httpx.AsyncClient):
    last_response = None
    last_error = None

    for attempt in range(TMDB_MAX_RETRIES + 1):
        try:
            response = await client.get(url)
            last_response = response
        except httpx.HTTPError as error:
            last_error = error
            if attempt >= TMDB_MAX_RETRIES:
                print(f"[TMDB] Request failed after retries for {url}: {error}")
                return None

            await asyncio.sleep(_get_retry_delay(None, attempt))
            continue

        if response.status_code not in TMDB_RETRY_STATUS_CODES or attempt >= TMDB_MAX_RETRIES:
            return response

        delay = _get_retry_delay(response, attempt)
        print(f"[TMDB] Retryable status {response.status_code} for {url}; retrying in {delay:.2f}s")
        await asyncio.sleep(delay)

    if last_response is not None:
        return last_response

    if last_error is not None:
        print(f"[TMDB] Request failed for {url}: {last_error}")

    return None


async def _find_smilar_movies_async(movie_id, media_type="movie", client=None):
    if client is None:
        async with _make_async_client() as managed_client:
            return await _find_smilar_movies_async(movie_id, media_type, managed_client)

    endpoint = "movie" if media_type == "movie" else "tv"
    url = f"https://api.themoviedb.org/3/{endpoint}/{movie_id}/recommendations?language=en-US&page=1"
    response = await _tmdb_get_async(url, client)
    if response and response.status_code == 200:
        return json.loads(response.text)
    return None


async def _get_watch_providers_async(movie_id, media_type="movie", client=None):
    if client is None:
        async with _make_async_client() as managed_client:
            return await _get_watch_providers_async(movie_id, media_type, managed_client)

    endpoint = "movie" if media_type == "movie" else "tv"
    url = f"https://api.themoviedb.org/3/{endpoint}/{movie_id}/watch/providers"
    response = await _tmdb_get_async(url, client)
    if not response or response.status_code != 200:
        return json.dumps({"results": {}})
    return response.text


async def _get_detail_moviedata_async(movie_id, media_type="movie", append_responses=None, client=None):
    if client is None:
        async with _make_async_client() as managed_client:
            return await _get_detail_moviedata_async(movie_id, media_type, append_responses, managed_client)

    endpoint = "movie" if media_type == "movie" else "tv"
    url = f"https://api.themoviedb.org/3/{endpoint}/{movie_id}?language=en-US"
    if append_responses:
        append_value = ",".join(append_responses)
        url += f"&append_to_response={append_value}"

    response = await _tmdb_get_async(url, client)
    if not response or response.status_code != 200:
        return json.dumps({})
    return response.text


async def _find_movie_basic_async(title, lang, media_type="movie", append_responses=None, client=None):
    if client is None:
        async with _make_async_client() as managed_client:
            return await _find_movie_basic_async(title, lang, media_type, append_responses, managed_client)

    original_title = title
    title_encoded = title.replace(" ", "+")
    endpoint = "movie" if media_type == "movie" else "tv"
    url = f"https://api.themoviedb.org/3/search/{endpoint}?include_adult=false&language={lang}&page=1&query={title_encoded}"

    response = await _tmdb_get_async(url, client)
    if not response or response.status_code != 200:
        return None

    data = json.loads(response.text)
    if "results" in str(data) and len(data["results"]) > 0:
        movie = get_movie_form_search(data["results"], original_title, media_type)
        if movie:
            if append_responses:
                movie = await _get_detail_moviedata_async(get_movie_id(movie), media_type, append_responses, client)
                movie = json.loads(movie)
            movie = normalize_media_item(movie, media_type)
        return movie

    return None


async def _find_movie_async(title, lang, media_type="movie", client=None):
    if client is None:
        async with _make_async_client() as managed_client:
            return await _find_movie_async(title, lang, media_type, managed_client)

    original_title = title
    title_encoded = title.replace(" ", "+")
    endpoint = "movie" if media_type == "movie" else "tv"
    url = f"https://api.themoviedb.org/3/search/{endpoint}?include_adult=false&language={lang}&page=1&query={title_encoded}"

    response = await _tmdb_get_async(url, client)
    if not response or response.status_code != 200:
        return None

    data = json.loads(response.text)
    print("find_movie for", title, "response: ", data)

    if "results" in str(data) and len(data["results"]) > 0:
        print("movie found!")
        movie = get_movie_form_search(data["results"], original_title, media_type)
        if movie:
            movie = await _get_detail_moviedata_async(get_movie_id(movie), media_type, ["watch/providers"], client)
            movie = json.loads(movie)
            movie = normalize_media_item(movie, media_type)
        return movie

    return None


async def _create_movie_data_async(title, media_type="movie", client=None):
    if client is None:
        async with _make_async_client() as managed_client:
            return await _create_movie_data_async(title, media_type, managed_client)

    movie = await _find_movie_async(title, "de-DE", media_type, client)
    if movie and "id" in movie:
        movie_id = get_movie_id(movie)
        providers = get_watch_provider_payload(movie)
        if not providers:
            providers = await _get_watch_providers_async(movie_id, media_type, client)
        flatproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"), "flatrate")
        rentproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"), "rent")
        buyproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"), "buy")
        genres = [x["name"] for x in movie.get("genres", [])]
        prodcountries = [x["name"] for x in movie.get("production_countries", [])]

        return {
            "title": movie["title"],
            "flatproviders": flatproviders,
            "rentproviders": rentproviders,
            "buyproviders": buyproviders,
            "adult": movie.get("adult", False),
            "genres": genres,
            "budget": movie.get("budget", 0),
            "overview": movie.get("overview", ""),
            "popularity": movie.get("popularity", 0),
            "poster_path": movie.get("poster_path", ""),
            "poster_url": build_tmdb_poster_url(movie.get("poster_path", "")),
            "release_date": movie.get("release_date", ""),
            "runtime": movie.get("runtime", 0),
            "revenue": movie.get("revenue", 0),
            "vote_average": movie.get("vote_average", 0),
            "vote_count": movie.get("vote_count", 0),
            "production_countries": prodcountries,
            "media_type": media_type,
        }

    return None


async def _create_basic_movie_data_async(title, media_type="movie", append_responses=None, client=None):
    if client is None:
        async with _make_async_client() as managed_client:
            return await _create_basic_movie_data_async(title, media_type, append_responses, managed_client)

    movie = await _find_movie_basic_async(title, "de-DE", media_type, append_responses, client)
    if movie and "id" in movie:
        movie_id = get_movie_id(movie)
        providers = get_watch_provider_payload(movie)
        if not providers:
            providers = await _get_watch_providers_async(movie_id, media_type, client)
        flatproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"), "flatrate")
        rentproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"), "rent")

        return {
            "title": movie["title"],
            "flatproviders": flatproviders,
            "rentproviders": rentproviders,
            "overview": movie.get("overview", ""),
            "poster_path": movie.get("poster_path", ""),
            "poster_url": build_tmdb_poster_url(movie.get("poster_path", "")),
            "release_date": movie.get("release_date", ""),
            "vote_average": movie.get("vote_average", 0),
            "vote_count": movie.get("vote_count", 0),
            "id": movie_id,
            "media_type": media_type,
            "_recommendations_payload": get_recommendation_payload(movie),
        }

    return None


async def _get_basic_data_from_tmdb_for_title_async(title: str, media_type: str = "movie", append_responses=None, client=None):
    if client is None:
        async with _make_async_client() as managed_client:
            return await _get_basic_data_from_tmdb_for_title_async(title, media_type, append_responses, managed_client)

    try:
        print("get_movie_data_from_tmdb", "title=", title, "media_type=", media_type)
        fulldata = await _create_basic_movie_data_async(title, media_type, append_responses, client)

        if not fulldata:
            fallback_type = "tv" if media_type == "movie" else "movie"
            print(f"[FALLBACK] Title '{title}' not found as {media_type}, trying {fallback_type}")
            fulldata = await _create_basic_movie_data_async(title, fallback_type, append_responses, client)

        return fulldata
    except Exception as e:
        print(f"[ERROR] get_basic_data_from_tmdb_for_title: {e}")
        return None


async def _get_detail_data_from_tmdb_for_title_async(title: str, media_type: str = "movie", client=None):
    if client is None:
        async with _make_async_client() as managed_client:
            return await _get_detail_data_from_tmdb_for_title_async(title, media_type, managed_client)

    try:
        print("get_movie_data_from_tmdb", "title=", title, "media_type=", media_type)
        fulldata = await _create_movie_data_async(title, media_type, client)

        if not fulldata:
            fallback_type = "tv" if media_type == "movie" else "movie"
            print(f"[FALLBACK] Title '{title}' not found as {media_type}, trying {fallback_type}")
            fulldata = await _create_movie_data_async(title, fallback_type, client)

        return fulldata
    except Exception as e:
        print(f"[ERROR] get_detail_data_from_tmdb_for_title: {e}")
        return None


async def _parse_movies_from_search_async(results, media_type="movie", client=None):
    if client is None:
        async with _make_async_client() as managed_client:
            return await _parse_movies_from_search_async(results, media_type, managed_client)

    async def build_movie(movie):
        if not movie or "id" not in movie:
            return None

        movie = normalize_media_item(movie, media_type)
        if not movie:
            return None

        movie_id = get_movie_id(movie)
        providers = await _get_watch_providers_async(movie_id, media_type, client)
        flatproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"), "flatrate")
        rentproviders = get_watch_providers_via_subtype(filter_watch_providers(providers, "DE"), "rent")

        return {
            "title": movie["title"],
            "flatproviders": flatproviders,
            "rentproviders": rentproviders,
            "overview": movie.get("overview", ""),
            "poster_path": movie.get("poster_path", ""),
            "poster_url": build_tmdb_poster_url(movie.get("poster_path", "")),
            "release_date": movie.get("release_date", ""),
            "vote_average": movie.get("vote_average", 0),
            "vote_count": movie.get("vote_count", 0),
            "id": movie_id,
            "media_type": media_type,
        }

    return await _collect_parallel_results_async(results.get("results", []), build_movie)


async def _get_recro_movies_async(movies, media_type="movie", client=None):
    if client is None:
        async with _make_async_client() as managed_client:
            return await _get_recro_movies_async(movies, media_type, managed_client)

    if len(movies) > 0:
        results = get_recommendation_payload(movies[0])
        if not results:
            search_id = movies[0]["id"]
            results = await _find_smilar_movies_async(search_id, media_type, client)
        if results:
            return await _parse_movies_from_search_async(results, media_type, client)
    return None


async def _get_movies_with_recro_async(titles: list, providers: list[str]):
    print("get_movies_with_recro", titles)
    async with _make_async_client() as client:
        async def resolve_title(indexed_item):
            index, item = indexed_item
            title, media_type = _extract_title_input(item)
            if not title:
                return None

            append_responses = ["watch/providers", "recommendations"] if index == 0 else None
            return await _get_basic_data_from_tmdb_for_title_async(title, media_type, append_responses, client)

        movies = await _collect_parallel_results_async(list(enumerate(titles)), resolve_title)

        if movies:
            first_media_type = movies[0].get("media_type", "movie")
            similar_movies = await _get_recro_movies_async(movies, first_media_type, client)
            if similar_movies:
                movies = movies + similar_movies

    result_movies = filter_movies(movies, providers)
    if result_movies and len(result_movies) > 5:
        result_movies = result_movies[:4]
    return create_data_list(result_movies)


async def _get_movies_for_providers_async(titles: list, providers: list[str]):
    print("get_basic_data_from_tmdb_for_titles", titles)
    async with _make_async_client() as client:
        async def resolve_title(item):
            title, media_type = _extract_title_input(item)
            if not title:
                return None
            return await _get_basic_data_from_tmdb_for_title_async(title, media_type, None, client)

        movies = await _collect_parallel_results_async(titles, resolve_title)

    return filter_movies(movies, providers)


async def _get_basic_data_from_tmdb_for_titles_async(titles: list):
    print("get_basic_data_from_tmdb_for_titles", titles)
    async with _make_async_client() as client:
        async def resolve_title(item):
            title, media_type = _extract_title_input(item)
            if not title:
                return None
            return await _get_basic_data_from_tmdb_for_title_async(title, media_type, None, client)

        movies = await _collect_parallel_results_async(titles, resolve_title)

    return create_data_list(movies)


async def _get_detail_data_from_tmdb_for_titles_async(titles: list):
    print("get_detail_data_from_tmdb_for_titles", titles)
    async with _make_async_client() as client:
        async def resolve_title(item):
            title, media_type = _extract_title_input(item)
            if not title:
                return None
            return await _get_detail_data_from_tmdb_for_title_async(title, media_type, client)

        return await _collect_parallel_results_async(titles, resolve_title)


def get_movies_with_recro(titles: list, providers: list[str]):
    """Get movies/TV shows with recommendations. Accepts list of strings or list of dicts with media_type."""
    return _run_async(_get_movies_with_recro_async(titles, providers))


def get_movies_for_providers(titles: list, providers: list[str]):
    """Get movies/TV shows for providers. Accepts list of strings or list of dicts with media_type."""
    return _run_async(_get_movies_for_providers_async(titles, providers))


def get_basic_data_from_tmdb_for_titles(titles: list):
    """Get basic data for titles. Accepts list of strings or list of dicts with media_type."""
    return _run_async(_get_basic_data_from_tmdb_for_titles_async(titles))


def get_detail_data_from_tmdb_for_titles(titles: list):
    """Get detailed data for titles. Accepts list of strings or list of dicts with media_type."""
    return _run_async(_get_detail_data_from_tmdb_for_titles_async(titles))


def get_basic_data_from_tmdb_for_title(title: str, media_type: str = "movie", append_responses=None):
    """Get basic data for a title. Falls back to other media_type if not found."""
    return _run_async(_get_basic_data_from_tmdb_for_title_async(title, media_type, append_responses))


def get_detail_data_from_tmdb_for_title(title: str, media_type: str = "movie"):
    """Get detailed data for a title. Falls back to other media_type if not found."""
    return _run_async(_get_detail_data_from_tmdb_for_title_async(title, media_type))


def get_recro_movies(movies, media_type="movie"):
    return _run_async(_get_recro_movies_async(movies, media_type))


def find_smilar_movies(movie_id, media_type="movie"):
    return _run_async(_find_smilar_movies_async(movie_id, media_type))


def parse_movies_from_search(results, media_type="movie"):
    return _run_async(_parse_movies_from_search_async(results, media_type))


def find_movie_basic(title, lang, media_type="movie", append_responses=None):
    return _run_async(_find_movie_basic_async(title, lang, media_type, append_responses))


def find_movie(title, lang, media_type="movie"):
    return _run_async(_find_movie_async(title, lang, media_type))


def get_movie_id(movie):
    if movie:
        return movie["id"]


def get_watch_providers(movie_id, media_type="movie"):
    return _run_async(_get_watch_providers_async(movie_id, media_type))


def get_detail_moviedata(movie_id, media_type="movie", append_responses=None):
    return _run_async(_get_detail_moviedata_async(movie_id, media_type, append_responses))


def get_watch_provider_payload(movie):
    if not movie:
        return None

    appended_providers = movie.get("watch/providers")
    if appended_providers:
        return json.dumps(appended_providers)

    return None


def get_recommendation_payload(movie):
    if not movie:
        return None

    appended_recommendations = movie.get("_recommendations_payload")
    if appended_recommendations:
        return appended_recommendations

    recommendations = movie.get("recommendations")
    if recommendations:
        return recommendations

    return None


def filter_watch_providers(data, lang):
    data = json.loads(data)
    if lang in data["results"]:
        return data["results"][lang]


def get_watch_providers_via_subtype(data, subtype):
    provider_names = []
    if subtype in str(data):
        filtered_data = data[subtype]
        if len(filtered_data) > 0:
            provider_names = [item["provider_name"] for item in filtered_data]

    return provider_names


def create_movie_data(title, media_type="movie"):
    return _run_async(_create_movie_data_async(title, media_type))


def create_basic_movie_data(title, media_type="movie", append_responses=None):
    return _run_async(_create_basic_movie_data_async(title, media_type, append_responses))


def create_recommendation_data(item):
    filtered_data = {
        "title": item["title"],
        "flatproviders": item["flatproviders"],
        "rentproviders": item["rentproviders"],
        "buyproviders": item["buyproviders"],
    }
    item = filtered_data

    if "flatproviders" in item and len(item["flatproviders"]) > 0:
        if "rentproviders" in item and len(item["rentproviders"]) > 0:
            return {"title": item["title"], "flatproviders": item["flatproviders"], "rentproviders": item["rentproviders"]}
        return {"title": item["title"], "flatproviders": item["flatproviders"]}
    if "rentproviders" in item and len(item["rentproviders"]) > 0:
        return {"title": item["title"], "rentproviders": item["rentproviders"]}


def get_movie_form_search(data: dict, search: str, media_type="movie"):
    try:
        if media_type == "tv":
            titles = [x.get("name", x.get("title", "")) for x in data]
            original_titles = [x.get("original_name", x.get("original_title", "")) for x in data]
        else:
            titles = [x.get("title", x.get("name", "")) for x in data]
            original_titles = [x.get("original_title", x.get("original_name", "")) for x in data]

        title_match = closeMatches(titles, search)
        if title_match:
            title = title_match[0]
            if media_type == "tv":
                movie = [x for x in data if x.get("name", x.get("title", "")) == title]
            else:
                movie = [x for x in data if x.get("title", x.get("name", "")) == title]
            return movie[0] if movie else None

        original_match = closeMatches(original_titles, search)
        if original_match:
            original_title = original_match[0]
            if media_type == "tv":
                movie = [x for x in data if x.get("original_name", x.get("original_title", "")) == original_title]
            else:
                movie = [x for x in data if x.get("original_title", x.get("original_name", "")) == original_title]
            return movie[0] if movie else None

        return None
    except Exception as e:
        print(f"[ERROR] get_movie_form_search: {e}")
        return None


def closeMatches(patterns, word):
    return get_close_matches(word, patterns)


def create_data_list(fulldata):
    movieinfoasstring = ""
    for movie_info in fulldata:
        formatted_info = f"Title: {movie_info['title']}, "
        formatted_info += f"Overview: {movie_info['overview']}, "
        formatted_info += f"flatproviders: {', '.join(movie_info['flatproviders'])}, "
        formatted_info += f"rentproviders: {', '.join(movie_info['rentproviders'])}\n"
        movieinfoasstring += formatted_info
    return movieinfoasstring


def filter_movies(movies: list, providers: list[str]):
    filtered_list = movies
    if providers and len(providers) > 0:
        filtered_list = filterforproviders(movies, providers)
    return filtered_list


def filterforproviders(movies, providers):
    filtered_list = [
        d for d in movies
        if (
            "flatproviders" in d and any(
                any(provider.lower() in fp.lower() for fp in d["flatproviders"])
                for provider in providers
            )
        ) or (
            "rentproviders" in d and any(
                any(provider.lower() in rp.lower() for rp in d["rentproviders"])
                for provider in providers
            )
        )
    ]
    return filtered_list
