
import os
import sys
from typing import Any, Dict
from langchain_core.tools import tool
from pydantic import BaseModel, Field, field_validator
# Tavily fallback, kept commented for easy future switching:
# from tavily import TavilyClient
# Optional page-content extraction fallback, kept commented:
# import requests
# from bs4 import BeautifulSoup
sys.path.append('./utils')  # Add the 'utils' directory to the Python path
from backend.utils.helper import choose_streaming_providers, get_filtered_titles_tmdb  # Import the function to filter titles based on streaming providers
from backend.utils.setupenv import get_required_env_value, load_environment

load_environment()

GOOGLE_SEARCH_MODEL = os.getenv("GOOGLE_SEARCH_MODEL", os.getenv("GOOGLE_MODEL_RESEARCHER", "gemini-2.5-flash"))
SEARCH_SNIPPET_MAX_CHARS = 280
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
    return any(str(provider).strip().casefold() == "mediatheken" for provider in userstreamingproviders)


def _truncate_text(value: Any, max_chars: int) -> str:
    text = str(value or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


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


def _extract_google_grounding_sources(response: Any) -> list[dict[str, str]]:
    """Extract a Tavily-like compact source list from Gemini grounding metadata."""
    sources: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        grounding_metadata = getattr(candidate, "grounding_metadata", None)
        grounding_chunks = getattr(grounding_metadata, "grounding_chunks", None) or []
        for chunk in grounding_chunks:
            web_chunk = getattr(chunk, "web", None)
            if web_chunk is None:
                continue

            url = str(getattr(web_chunk, "uri", "") or "").strip()
            if not url or url in seen_urls:
                continue

            seen_urls.add(url)
            sources.append(
                {
                    "title": str(getattr(web_chunk, "title", "") or ""),
                    "url": url,
                    "content": "",
                }
            )

    return sources


def _run_google_grounded_search(query: str) -> Any:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise RuntimeError(
            "Google Gemini dependencies are missing. Install google-genai and langchain-google-genai."
        ) from exc

    client = genai.Client(api_key=get_required_env_value("GOOGLE_API_KEY"))
    return client.models.generate_content(
        model=GOOGLE_SEARCH_MODEL,
        contents=query,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.2,
        ),
    )

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

@tool("internet_search_google", return_direct=False)
def internet_search_google(query: str) -> Dict[str, Any]:
    """Searches the internet using Gemini Grounding with Google Search.
    
    Args:
        query (str): The search query.
    
    Returns:
        A compact answer and source list to be processed further by the LLM.
    """

    response = _run_google_grounded_search(query)

    answer = getattr(response, "text", "") or ""
    return {
        "query": query,
        "answer": _truncate_text(answer, 1200),
        "results": [
            {
                **source,
                "content": _truncate_text(source.get("content", ""), SEARCH_SNIPPET_MAX_CHARS),
            }
            for source in _extract_google_grounding_sources(response)
        ],
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
#     return [internet_search_google]
#     # With optional page-content extraction:
#     # return [internet_search_google, process_content]
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
    if _is_mediatheken_mode(userstreamingproviders):
        return [internet_search_google]
        # Tavily fallback:
        # return [internet_search_tavily]
    return get_all_tools()

def get_all_tools():
    """Returns all available tools."""
    return [internet_search_google, filter_streaming_providers]
    # Tavily fallback:
    # return [internet_search_tavily, filter_streaming_providers]
