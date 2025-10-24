
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
    
    Args:
        titleList (list[str]): A list of titles to filter.
        userstreamingproviders (list[str]): A list of user's preferred streaming providers.    
    """
    print(f"tmdb filter calles: titles: {titleList}, streamingproviders: {userstreamingproviders}")
    filtered_titles = get_filtered_titles_tmdb(titleList, userstreamingproviders)
    return filtered_titles

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




