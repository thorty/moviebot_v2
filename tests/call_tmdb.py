import requests
import os, sys
from pathlib import Path
from difflib import get_close_matches
import json

# Add parent directory to path for backend module import
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.setupenv import get_required_env_value, load_environment
from backend.utils.helper import get_streaming_providers_tmdb




def find_movie(title: str):
    """Test TMDB TV search with the given title."""
    # Test the exact curl from user
    print("=" * 80)
    print(f"Testing user query: '{title}' with de-DE")
    print("=" * 80)
    url = f'https://api.themoviedb.org/3/search/tv?query={requests.utils.quote(title)}&include_adult=false&language=de-DE'
    response = requests.get(url, headers=headers)
    data = response.json()

    print(f"\nTotal results: {data.get('total_results', 0)}")
    if data.get('results'):
        print("\nAll results:")
        for idx, r in enumerate(data['results'], 1):
            print(f"\n{idx}. ID: {r.get('id')}")
            print(f"   name: {r.get('name')}")
            print(f"   original_name: {r.get('original_name')}")
            print(f"   first_air_date: {r.get('first_air_date')}")
        
        # Test closeMatches with name field
        print("\n" + "-" * 80)
        print(f"Testing closeMatches with '{title}':")
        names = [r.get('name', '') for r in data['results']]
        print(f"Names in results: {names}")
        matches = get_close_matches(title, names, n=1, cutoff=0.4)
        print(f"Matches (cutoff=0.4): {matches}")
        
        # Test with original_name
        print("\nTesting with original_name:")
        original_names = [r.get('original_name', '') for r in data['results']]
        print(f"Original names in results: {original_names}")
        matches_orig = get_close_matches(title, original_names, n=1, cutoff=0.4)
        print(f"Matches with original_name: {matches_orig}")
    else:
        print("  No results found")



if __name__ == '__main__':
    load_environment()
    headers = {'accept': 'application/json', 'Authorization': get_required_env_value('TMDB_BEARER')}    
    
    #main('TRON: Uprising')
    get_streaming_providers_tmdb(['The Abyss'])
