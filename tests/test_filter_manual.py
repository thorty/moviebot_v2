"""
Manual test script for filter_streaming_providers tool
Run with: python test_filter_manual.py
"""

import sys
from pathlib import Path

# Add parent directory to path for backend module import
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.tools import filter_streaming_providers


def test_cyberpunk_anime_filter():
    """
    Test filter_streaming_providers with a large list of cyberpunk anime titles
    """
    titles = [
        'Akira', 'Paprika', 'Cowboy Bebop: The Movie', 'Appleseed', 'Metropolis', 
        'Memories', 'Cyber City Oedo 808', 'Wonderful Days (Sky Blue)', 
        'Ghost in the Shell 2: Innocence', 'The Animatrix', 'Redline', 
        'Psycho-Pass: The Movie', 'Expelled from Paradise', 'Blame!', 
        'Armitage III: Poly-Matrix', 'Armitage III: Dual-Matrix', 'Vexille', 
        'A Wind Named Amnesia', 'Battle Angel Alita', "Angel's Egg", 
        'Genocidal Organ', 'Harmony', 'Spriggan', 'Cyberpunk: Edgerunners', 
        'Neo Tokyo', 'Tekkonkinkreet', 'Patlabor: The Movie', 'Patlabor 2: The Movie', 
        'Ergo Proxy', 'Akudama Drive', 'Bubblegum Crisis', 'Time of Eve', 
        'Eve no Jikan', 'Ghost in the Shell 2.0', 'Pale Cocoon', 'Dead Leaves', 
        'Psycho Diver: Soul Siren', 'Cybernetics Guardian', 'Aachi and Ssipak', 
        'Red Ash: The Indelible Legend', 'Mardock Scramble', 'Gantz: O', 'Planzet', 
        'Origin: Spirits of the Past', '009 Re:Cyborg', 'Venus Wars', 
        'The Empire of Corpses', 'Short Peace', 'Eve no Jikan Gekijouban', 
        'Patema Inverted', "TRON"
    ]
    
    userstreamingproviders = ['Disney Plus', 'Amazon', 'Apple TV+']
    
    print("=" * 80)
    print("TESTING FILTER_STREAMING_PROVIDERS")
    print("=" * 80)
    print(f"\nTotal titles to check: {len(titles)}")
    print(f"Streaming providers: {', '.join(userstreamingproviders)}")
    print("\n" + "-" * 80 + "\n")
    
    # Call the tool
    result = filter_streaming_providers.invoke({
        'titleList': titles,
        'userstreamingproviders': userstreamingproviders
    })
    
    return result


def test_tron():
    """
    Test filter_streaming_providers with a large list of cyberpunk anime titles
    """
    titles = [
         "Tron", "Tron: Legacy", "Tron: Uprising"
    ]
    
    userstreamingproviders = ['Disney Plus', 'Amazon', 'Apple TV+']
    
    print("=" * 80)
    print("TESTING FILTER_STREAMING_PROVIDERS")
    print("=" * 80)
    print(f"\nTotal titles to check: {len(titles)}")
    print(f"Streaming providers: {', '.join(userstreamingproviders)}")
    print("\n" + "-" * 80 + "\n")
    
    # Call the tool
    result = filter_streaming_providers.invoke({
        'titleList': titles,
        'userstreamingproviders': userstreamingproviders
    })
    
    return result


def print_results(result):
    """
    Pretty print the results from filter_streaming_providers
    """
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"\nTotal titles checked: {result['total_checked']}")
    print(f"Available titles found: {result['found_count']}")
    print(f"Unavailable titles: {len(result['unavailable_titles'])}")
    
    if result['found_count'] > 0:
        print("\n" + "-" * 80)
        print("AVAILABLE TITLES:")
        print("-" * 80)
        
        for idx, title_info in enumerate(result['available_titles'], 1):
            print(f"\n{idx}. {title_info['title']} ({title_info.get('release_date', 'N/A')})")
            
            # Flatrate providers
            if title_info.get('flatproviders'):
                print(f"   🟢 Flatrate: {', '.join(title_info['flatproviders'])}")
            
            # Rent providers
            if title_info.get('rentproviders'):
                rent_providers = title_info['rentproviders'][:3]  # Show first 3
                print(f"   🟡 Leihen: {', '.join(rent_providers)}")
                if len(title_info['rentproviders']) > 3:
                    print(f"      ... und {len(title_info['rentproviders']) - 3} weitere")
            
            # Overview (first 100 chars)
            if title_info.get('overview'):
                overview = title_info['overview'][:100] + "..." if len(title_info['overview']) > 100 else title_info['overview']
                print(f"   📝 {overview}")
    
    if result['unavailable_titles']:
        print("\n" + "-" * 80)
        print(f"UNAVAILABLE TITLES ({len(result['unavailable_titles'])}):")
        print("-" * 80)
        unavailable_names = [t.get('title', 'Unknown') for t in result['unavailable_titles']]
        print(", ".join(unavailable_names[:10]))
        if len(unavailable_names) > 10:
            print(f"... und {len(unavailable_names) - 10} weitere")
    
    print("\n" + "=" * 80 + "\n")


def main():
    """
    Main function to run the test
    """
    try:
        # Run the test
        #result = test_cyberpunk_anime_filter()
        result = test_tron()
        
        # Print formatted results
        print_results(result)
        
        # Return result for further processing if needed
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = main()
    
    # Optional: Save results to file
    if result:
        import json
        with open('filter_results.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("✅ Results saved to filter_results.json")
