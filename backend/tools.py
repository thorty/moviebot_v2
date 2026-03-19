
import os
import sys
from typing import Any, Dict
from bs4 import BeautifulSoup
from tavily import TavilyClient
from duckduckgo_search import DDGS
from langchain_core.tools import tool
import requests # Import the tool decorator again
sys.path.append('./utils')  # Add the 'utils' directory to the Python path
from backend.utils.helper import choose_streaming_providers, get_filtered_titles_tmdb  # Import the function to filter titles based on streaming providers
from langchain_community.utilities import GoogleSerperAPIWrapper
from backend.utils.setupenv import load_environment

load_environment(override=True)

TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
SERPER_API_KEY = os.getenv('SERPER_API_KEY', '')
TAVILY_SNIPPET_MAX_CHARS = 280


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


def _compact_tavily_response(response: Dict[str, Any]) -> Dict[str, Any]:
    compact_results = []

    for item in response.get("results", []) or []:
        compact_results.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": _truncate_text(item.get("content", ""), TAVILY_SNIPPET_MAX_CHARS),
                "score": item.get("score"),
            }
        )

    return {
        "query": response.get("query"),
        "follow_up_questions": response.get("follow_up_questions"),
        "answer": response.get("answer"),
        "results": compact_results,
        "response_time": response.get("response_time"),
        "request_id": response.get("request_id"),
    }

@tool
def filter_streaming_providers(titleList: list, userstreamingproviders: list[str], paymenttypes: list[str]) -> dict:
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
    for title_info in titleList:
        key = _build_title_key(title_info)
        if not key[0]:
            continue
        if key in seen_input_keys:
            continue
        seen_input_keys.add(key)
        unique_title_list.append(title_info)

    removed_input_duplicates = len(titleList) - len(unique_title_list)
    if removed_input_duplicates > 0:
        print(f"[TOOL] Removed {removed_input_duplicates} duplicate title(s) from input")

    print(f"[TOOL] Choosing streaming providers based on payment types: {paymenttypes}")
    # choose streeming providers based on properties
    userstreamingproviders = choose_streaming_providers(original_userstreamingproviders, paymenttypes)
    print(f"[TOOL] filter_streaming_providers called: {len(titleList)} titles, providers: {userstreamingproviders}")
    
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

@tool
def internet_search_serper(query: str) -> str:
    """Searches the internet.
    
    Args: 
        query (str): Mandatory search query you want to use to search the internet"
    """    
    search_tool = GoogleSerperAPIWrapper(api_key=SERPER_API_KEY, max_results=5)  # Use Serper API for search
    results = search_tool.run(query)    
    
    # Log the raw results for debugging purposes
    print("Raw results:", results)
    return results

@tool("process_content", return_direct=False)
def process_content(url: str) -> str:

    """Processes content from a webpage."""

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.get_text()

@tool("internet_search_DDGO", return_direct=False)
def internet_search_DDGO(query: str) -> str:

  """Searches the internet using DuckDuckGo."""

  with DDGS() as ddgs:
    results = [r for r in ddgs.text(query, max_results=5)]
    return results if results else "No results found."

@tool("internet_search_tavily", return_direct=False)
def internet_search_tavily(query: str) -> Dict[str, Any]:
    """Searches the internet using Tavily API.
    
    Args:
        query (str): The search query.
    
    Returns:
        The search results from Tavily API to be processed further by llm model
    """
    
    client = TavilyClient(api_key=TAVILY_API_KEY)
    response = client.search(
        query=query,
        search_depth="advanced",
        country="germany"
    )
    return _compact_tavily_response(response)


def get_search_tools():
    return [internet_search_serper, process_content]   # Uncomment this and comment the line below to use Tavily instead of DuckDuckGo Search. 
    #return [internet_search_DDGO, process_content]  # Uncomment this and comment the line above to use DuckDuckGo Search instead of Tavily.
    
def get_streamingprovider_tools():
    return [filter_streaming_providers]  # This function returns a list of tools related to streaming providers.


def get_tools_for_providers(userstreamingproviders: list[str]):
    """Return only the tools relevant for the current provider selection."""
    if _is_mediatheken_mode(userstreamingproviders):
        return [internet_search_tavily]
    return get_all_tools()

def get_all_tools():
    """Returns all available tools."""
    #return [internet_search_serper, process_content, filter_streaming_providers]  # Add more tools as needed.
    return [internet_search_tavily, filter_streaming_providers]  # Add more tools as needed.




