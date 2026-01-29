import requests
import os
from dotenv import load_dotenv
from difflib import get_close_matches
import json

load_dotenv()
headers = {'accept': 'application/json', 'Authorization': os.environ['tmdb_bearer']}

# Test the exact curl from user
print("=" * 80)
print("Testing EXACT user query: 'Tron: Uprising' with de-DE")
print("=" * 80)
url = 'https://api.themoviedb.org/3/search/tv?query=Tron%3A%20Uprising%20&include_adult=false&language=de-DE'
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
    print("Testing closeMatches with 'TRON: Uprising':")
    names = [r.get('name', '') for r in data['results']]
    print(f"Names in results: {names}")
    matches = get_close_matches('TRON: Uprising', names, n=1, cutoff=0.4)
    print(f"Matches (cutoff=0.4): {matches}")
    
    # Test with original_name
    print("\nTesting with original_name:")
    original_names = [r.get('original_name', '') for r in data['results']]
    print(f"Original names in results: {original_names}")
    matches_orig = get_close_matches('TRON: Uprising', original_names, n=1, cutoff=0.4)
    print(f"Matches with original_name: {matches_orig}")
else:
    print("  No results found")
