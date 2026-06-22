
import logging
import os
import sys
import time
from typing import Any, Dict
from urllib.parse import urlparse
from langchain_core.tools import tool
from pydantic import BaseModel, Field, field_validator
# Tavily fallback, kept commented for easy future switching:
# from tavily import TavilyClient
# Optional page-content extraction fallback, kept commented:
# import requests
# from bs4 import BeautifulSoup
sys.path.append('./utils')  # Add the 'utils' directory to the Python path
from backend.utils.helper import (
    choose_streaming_providers,
    get_filtered_titles_tmdb,
    split_streaming_and_mediatheken,
)
from backend.utils.setupenv import get_required_env_value, load_environment

load_environment()
logger = logging.getLogger(__name__)

OPENAI_SEARCH_MODEL = os.getenv("OPENAI_MODEL_RESEARCH", "gpt-5.4")
OPENAI_WEB_SEARCH_CONTEXT = os.getenv("OPENAI_WEB_SEARCH_CONTEXT", "low")
SEARCH_SNIPPET_MAX_CHARS = 280
PUBLIC_MEDIATHEKEN_DOMAINS = {
    "ardmediathek.de": "ARD Mediathek",
    "ard.de": "ARD Mediathek",
    "daserste.de": "ARD Mediathek",
    "zdf.de": "ZDF Mediathek",
    "arte.tv": "Arte",
    "3sat.de": "3sat",
}
# Tavily fallback, kept commented for easy future switching:
# TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
# TAVILY_SNIPPET_MAX_CHARS = 280


class TitleInfo(BaseModel):
    title: str = Field(description="Movie or TV show title.")
    media_type: str = Field(default="", description="Either 'movie' or 'tv'.")


class FilterStreamingProvidersArgs(BaseModel):
    titleList: list[TitleInfo] = Field(
        description="Candidate titles to check for streaming availability."
    )
    userstreamingproviders: list[str] = Field(
        description="The user's preferred streaming providers."
    )
    paymenttypes: list[str] = Field(
        description="The user's preferred payment types, such as free or rent."
    )

    @field_validator("titleList", mode="before")
    @classmethod
    def normalize_title_list(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value
        return [
            {"title": item, "media_type": ""}
            if isinstance(item, str)
            else item
            for item in value
        ]


def _build_title_key(title_info: Any) -> tuple[str, str]:
    """Create a stable deduplication key from title entries."""
    if isinstance(title_info, dict):
        raw_title = title_info.get("title", "")
        raw_media_type = title_info.get("media_type", "")
    else:
        raw_title = title_info
        raw_media_type = ""

    title = str(raw_title).strip().casefold()
    media_type = str(raw_media_type).strip().casefold()
    return (title, media_type)


def _is_mediatheken_mode(userstreamingproviders: list[str]) -> bool:
    streaming_providers, include_mediatheken = split_streaming_and_mediatheken(userstreamingproviders)
    return include_mediatheken and not streaming_providers


def _truncate_text(value: Any, max_chars: int) -> str:
    text = str(value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def _get_public_mediatheken_service(url: str) -> str:
    host = urlparse(str(url or "")).netloc.lower()
    if host.startswith("www."):
        host = host[4:]

    for domain, service in PUBLIC_MEDIATHEKEN_DOMAINS.items():
        if host == domain or host.endswith(f".{domain}"):
            return service

    return ""


def _enrich_public_mediatheken_source(source: dict[str, str]) -> dict[str, str | bool]:
    url = str(source.get("url", "") or "").strip()
    service = _get_public_mediatheken_service(url)

    return {
        **source,
        "service": service,
        "deeplink_url": url if service else "",
        "is_official_mediathek_source": bool(service),
    }


# Tavily fallback, kept commented for easy future switching:
# def _compact_tavily_response(response: Dict[str, Any]) -> Dict[str, Any]:
#     compact_results = []
#
#     for item in response.get("results", []) or []:
#         compact_results.append(
#             {
#                 "title": item.get("title", ""),
#                 "url": item.get("url", ""),
#                 "content": _truncate_text(item.get("content", ""), TAVILY_SNIPPET_MAX_CHARS),
#                 "score": item.get("score"),
#             }
#         )
#
#     return {
#         "query": response.get("query"),
#         "follow_up_questions": response.get("follow_up_questions"),
#         "answer": response.get("answer"),
#         "results": compact_results,
#         "response_time": response.get("response_time"),
#         "request_id": response.get("request_id"),
#     }


def _response_to_plain_data(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if isinstance(response, dict):
        return response
    return {}


def _extract_openai_web_sources(response: Any) -> list[dict[str, str]]:
    """Extract a Tavily-like compact source list from OpenAI Responses output."""
    sources: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    def add_source(raw_source: dict[str, Any]) -> None:
        url = str(raw_source.get("url") or raw_source.get("uri") or "").strip()
        if not url or url in seen_urls:
            return

        seen_urls.add(url)
        sources.append(
            {
                "title": str(raw_source.get("title") or raw_source.get("text") or ""),
                "url": url,
                "content": str(
                    raw_source.get("content")
                    or raw_source.get("snippet")
                    or raw_source.get("description")
                    or ""
                ),
            }
        )

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if value.get("url") or value.get("uri"):
                add_source(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(_response_to_plain_data(response))

    return sources


def _run_openai_web_search(query: str) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "OpenAI dependencies are missing. Install openai."
        ) from exc

    query_text = str(query or "")
    start_time = time.perf_counter()
    logger.info(
        "[LLM_WEB_SEARCH_START] model=%s context=%s query_chars=%s",
        OPENAI_SEARCH_MODEL,
        OPENAI_WEB_SEARCH_CONTEXT,
        len(query_text),
    )

    try:
        client = OpenAI(api_key=get_required_env_value("OPENAI_API_KEY"))
        response = client.responses.create(
            model=OPENAI_SEARCH_MODEL,
            tools=[
                {
                    "type": "web_search",
                    "search_context_size": OPENAI_WEB_SEARCH_CONTEXT,
                }
            ],
            input=query,
            temperature=0.2,
            include=["web_search_call.results"],
        )
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.exception(
            "[LLM_WEB_SEARCH_ERROR] model=%s duration_ms=%.1f error_type=%s",
            OPENAI_SEARCH_MODEL,
            duration_ms,
            exc.__class__.__name__,
        )
        raise

    duration_ms = (time.perf_counter() - start_time) * 1000
    answer = getattr(response, "output_text", "") or ""
    source_count = len(_extract_openai_web_sources(response))
    logger.info(
        "[LLM_WEB_SEARCH_END] model=%s duration_ms=%.1f answer_chars=%s sources=%s",
        OPENAI_SEARCH_MODEL,
        duration_ms,
        len(answer),
        source_count,
    )
    return response

@tool(args_schema=FilterStreamingProvidersArgs)
def filter_streaming_providers(titleList: list[TitleInfo], userstreamingproviders: list[str], paymenttypes: list[str]) -> dict:
    """Filters the streaming providers based on the user's preferences.
    Optimized to handle large lists (50-100+ titles) for better discovery.
    
    Args:
        titleList (list): A list of title objects with 'title' and 'media_type' keys.
                         Format: [
                             {"title": "Breaking Bad", "media_type": "tv"},
                             {"title": "Inception", "media_type": "movie"}
                         ]
                         media_type must be either "movie" or "tv"
                         Can handle 50-100+ titles for comprehensive search.
        userstreamingproviders (list[str]): A list of user's preferred streaming providers.
        paymenttypes (list[str]): A list of user's preferred payment types (free, rent).
    
    Returns:
        dict: Structured results with available_titles, unavailable_titles, and count
    
    Example:
        Input: [
            {"title": "Breaking Bad", "media_type": "tv"},
            {"title": "Akira", "media_type": "movie"}
        ]
        Output: {'available_titles': [...], 'found_count': 2, ...}
    """
    
    original_userstreamingproviders = list(userstreamingproviders)

    # Deduplicate incoming titles before TMDB calls to avoid redundant lookups/results
    seen_input_keys = set()
    unique_title_list = []
    normalized_title_list = [
        title_info.model_dump() if isinstance(title_info, TitleInfo) else title_info
        for title_info in titleList
    ]

    for title_info in normalized_title_list:
        key = _build_title_key(title_info)
        if not key[0]:
            continue
        if key in seen_input_keys:
            continue
        seen_input_keys.add(key)
        unique_title_list.append(title_info)

    removed_input_duplicates = len(normalized_title_list) - len(unique_title_list)
    if removed_input_duplicates > 0:
        print(f"[TOOL] Removed {removed_input_duplicates} duplicate title(s) from input")

    print(f"[TOOL] Choosing streaming providers based on payment types: {paymenttypes}")
    # choose streeming providers based on properties
    userstreamingproviders = choose_streaming_providers(original_userstreamingproviders, paymenttypes)
    print(f"[TOOL] filter_streaming_providers called: {len(normalized_title_list)} titles, providers: {userstreamingproviders}")
    
    # Warnung wenn zu wenige Titel
    if len(unique_title_list) < 30:
        print(f"[TOOL] ⚠️ WARNING: Only {len(unique_title_list)} titles provided. Recommend 50-100+ for better discovery!")
    
    filtered_titles = get_filtered_titles_tmdb(unique_title_list, userstreamingproviders)

    # Deduplicate TMDB results as a second safety net
    deduplicated_filtered_titles = []
    seen_result_keys = set()
    if filtered_titles:
        for title_info in filtered_titles:
            key = _build_title_key(title_info)
            if not key[0]:
                continue
            if key in seen_result_keys:
                continue
            seen_result_keys.add(key)
            deduplicated_filtered_titles.append(title_info)

    removed_result_duplicates = (len(filtered_titles) if filtered_titles else 0) - len(deduplicated_filtered_titles)
    if removed_result_duplicates > 0:
        print(f"[TOOL] Removed {removed_result_duplicates} duplicate title(s) from TMDB results")
    
    # Strukturiere die Ergebnisse für besseres Tracking
    available_titles = []
    unavailable_titles = []
    
    if deduplicated_filtered_titles:
        for title_info in deduplicated_filtered_titles:
            if isinstance(title_info, dict):
                # Prüfe ob Titel verfügbar ist (flatproviders oder rentproviders vorhanden)
                has_availability = False                
                # Check flatproviders
                if 'flatproviders' in title_info and title_info['flatproviders']:
                    has_availability = True
                # Check rentproviders als Fallback
                elif 'rentproviders' in title_info and title_info['rentproviders'] and 'rent' in paymenttypes:
                    has_availability = True
                
                if has_availability:
                    available_titles.append(title_info)
                else:
                    unavailable_titles.append(title_info)
    
    result = {
        'available_titles': available_titles,
        'unavailable_titles': unavailable_titles,
        'total_checked': len(unique_title_list),
        'duplicates_removed_input': removed_input_duplicates,
        'duplicates_removed_results': removed_result_duplicates,
        'found_count': len(available_titles)
    }
    
    print(f"[TOOL] Results: {len(available_titles)} available, {len(unavailable_titles)} unavailable")
    
    return result

# Optional page-content extraction tool.
# Use this if the search tool returns URLs that the model should fetch and parse itself.
# @tool("process_content", return_direct=False)
# def process_content(url: str) -> str:
#     """Processes content from a webpage."""
#
#     response = requests.get(url)
#     soup = BeautifulSoup(response.content, 'html.parser')
#     return soup.get_text()

@tool("internet_search_web", return_direct=False)
def internet_search_web(query: str) -> Dict[str, Any]:
    """Searches the internet using OpenAI Responses web_search.
    
    Args:
        query (str): The search query.
    
    Returns:
        A compact answer and source list to be processed further by the LLM.
    """

    try:
        response = _run_openai_web_search(query)
    except Exception as exc:
        error_message = str(exc)
        print(f"[TOOL] Web search failed: {error_message}")
        return {
            "query": query,
            "answer": "",
            "results": [],
            "error": "web_search_unavailable",
            "error_message": _truncate_text(error_message, 500),
        }

    answer = getattr(response, "output_text", "") or ""
    return {
        "query": query,
        "answer": _truncate_text(answer, 1200),
        "results": [
            {
                **source,
                "content": _truncate_text(source.get("content", ""), SEARCH_SNIPPET_MAX_CHARS),
            }
            for source in _extract_openai_web_sources(response)
        ],
    }


@tool("search_public_mediatheken", return_direct=False)
def search_public_mediatheken(query: str) -> Dict[str, Any]:
    """Searches public German media libraries such as ARD, ZDF, Arte, and 3sat."""

    original_query = str(query or "").strip()
    mediatheken_query = (
        f"{original_query} ARD Mediathek ZDF Mediathek Arte 3sat verfügbar kostenlos "
        "öffentlich-rechtlich"
    ).strip()

    try:
        response = _run_openai_web_search(mediatheken_query)
    except Exception as exc:
        error_message = str(exc)
        print(f"[TOOL] Public mediatheken search failed: {error_message}")
        return {
            "query": original_query,
            "search_query": mediatheken_query,
            "answer": "",
            "results": [],
            "official_results": [],
            "found_count": 0,
            "error": "web_search_unavailable",
            "error_message": _truncate_text(error_message, 500),
        }

    sources = [
        _enrich_public_mediatheken_source(
            {
                **source,
                "content": _truncate_text(source.get("content", ""), SEARCH_SNIPPET_MAX_CHARS),
            }
        )
        for source in _extract_openai_web_sources(response)
    ]
    official_sources = [source for source in sources if source.get("is_official_mediathek_source")]
    answer = getattr(response, "output_text", "") or ""
    return {
        "query": original_query,
        "search_query": mediatheken_query,
        "answer": _truncate_text(answer, 1200),
        "results": sources,
        "official_results": official_sources,
        "found_count": len(official_sources) if official_sources else (1 if answer else 0),
    }


# Tavily fallback, kept commented for easy future switching:
# @tool("internet_search_tavily", return_direct=False)
# def internet_search_tavily(query: str) -> Dict[str, Any]:
#     """Searches the internet using Tavily API.
#
#     Args:
#         query (str): The search query.
#
#     Returns:
#         The search results from Tavily API to be processed further by the LLM.
#     """
#
#     client = TavilyClient(api_key=TAVILY_API_KEY)
#     response = client.search(
#         query=query,
#         search_depth="advanced",
#         country="germany",
#     )
#     return _compact_tavily_response(response)
#
#
# Legacy search-tool group helper.
# Use this if the graph is split again into search-only and streaming-provider tool groups.
# def get_search_tools():
#     return [internet_search_web]
#     # With optional page-content extraction:
#     # return [internet_search_web, process_content]
#     # Tavily fallback:
#     # return [internet_search_tavily]
#     # Tavily with optional page-content extraction:
#     # return [internet_search_tavily, process_content]


# Legacy streaming-provider-tool group helper.
# Use this if the graph is split again into search-only and streaming-provider tool groups.
# def get_streamingprovider_tools():
#     return [filter_streaming_providers]


def get_tools_for_providers(userstreamingproviders: list[str]):
    """Return only the tools relevant for the current provider selection."""
    streaming_providers, include_mediatheken = split_streaming_and_mediatheken(userstreamingproviders)
    return get_tools_for_availability(streaming_providers, include_mediatheken)


def get_tools_for_availability(userstreamingproviders: list[str], include_mediatheken: bool):
    """Return tools for streaming-only, mediathek-only, or combined availability search."""
    streaming_providers, legacy_include_mediatheken = split_streaming_and_mediatheken(userstreamingproviders)
    should_include_mediatheken = include_mediatheken or legacy_include_mediatheken

    if should_include_mediatheken and not streaming_providers:
        return [search_public_mediatheken]
        # Tavily fallback:
        # return [internet_search_tavily]

    if should_include_mediatheken:
        return [internet_search_web, filter_streaming_providers, search_public_mediatheken]

    return [internet_search_web, filter_streaming_providers]

def get_all_tools():
    """Returns all available tools."""
    return [internet_search_web, filter_streaming_providers, search_public_mediatheken]
    # Tavily fallback:
    # return [internet_search_tavily, filter_streaming_providers]
