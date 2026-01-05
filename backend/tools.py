
import sys, os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from langchain_core.tools import tool
import requests # Import the tool decorator again
sys.path.append('./utils')  # Add the 'utils' directory to the Python path
from backend.utils.helper import get_filtered_titles_tmdb  # Import the function to filter titles based on streaming providers
from langchain_community.utilities import GoogleSerperAPIWrapper


load_dotenv(dotenv_path=".env", override=True)

TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
SERPER_API_KEY = os.getenv('SERPER_API_KEY', '')

@tool
def filter_streaming_providers(titleList: list[str], userstreamingproviders: list[str]) -> dict:
    """Filters the streaming providers based on the user's preferences.
    Optimized to handle large lists (50-100+ titles) for better discovery.
    
    Args:
        titleList (list[str]): A list of titles to filter. Only titles, no additional info! 
                               Can handle 50-100+ titles for comprehensive search.
        userstreamingproviders (list[str]): A list of user's preferred streaming providers.
    
    Returns:
        dict: Structured results with available_titles, unavailable_titles, and count
    
    Example:
        Input: ['Ghost in the Shell', 'Akira', 'Blade Runner', ...] (60 titles)
        Output: {'available_titles': [...], 'found_count': 12, ...}
    """
    print(f"[TOOL] filter_streaming_providers called: {len(titleList)} titles, providers: {userstreamingproviders}")
    
    # Warnung wenn zu wenige Titel
    if len(titleList) < 30:
        print(f"[TOOL] ⚠️ WARNING: Only {len(titleList)} titles provided. Recommend 50-100+ for better discovery!")
    
    filtered_titles = get_filtered_titles_tmdb(titleList, userstreamingproviders)
    
    # Strukturiere die Ergebnisse für besseres Tracking
    available_titles = []
    unavailable_titles = []
    
    if filtered_titles:
        for title_info in filtered_titles:
            if isinstance(title_info, dict):
                # Prüfe ob Titel verfügbar ist (flatproviders oder rentproviders vorhanden)
                has_availability = False
                
                # Check flatproviders
                if 'flatproviders' in title_info and title_info['flatproviders']:
                    has_availability = True
                # Check rentproviders als Fallback
                elif 'rentproviders' in title_info and title_info['rentproviders']:
                    has_availability = True
                
                if has_availability:
                    available_titles.append(title_info)
                else:
                    unavailable_titles.append(title_info)
    
    result = {
        'available_titles': available_titles,
        'unavailable_titles': unavailable_titles,
        'total_checked': len(titleList),
        'found_count': len(available_titles),
        'raw_results': filtered_titles
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


def get_search_tools():
    return [internet_search_serper, process_content]   # Uncomment this and comment the line below to use Tavily instead of DuckDuckGo Search. 
    #return [internet_search_DDGO, process_content]  # Uncomment this and comment the line above to use DuckDuckGo Search instead of Tavily.
    
def get_streamingprovider_tools():
    return [filter_streaming_providers]  # This function returns a list of tools related to streaming providers.

def get_all_tools():
    """Returns all available tools."""
    return [internet_search_serper, process_content, filter_streaming_providers]  # Add more tools as needed.




