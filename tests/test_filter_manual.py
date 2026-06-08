"""
Manual test script for filter_streaming_providers tool
Run with: python test_filter_manual.py
"""

import sys
from pathlib import Path

import pytest

# Add parent directory to path for backend module import
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.tools import filter_streaming_providers

pytest.skip("Manual TMDB smoke checks; run directly when needed.", allow_module_level=True)


def test_cyberpunk_anime_filter():
    """
    Test filter_streaming_providers with a large list of cyberpunk anime movies
    """
    titles = [
        {'title': 'Akira', 'media_type': 'movie'},
        {'title': 'Paprika', 'media_type': 'movie'},
        {'title': 'Cowboy Bebop: The Movie', 'media_type': 'movie'},
        {'title': 'Appleseed', 'media_type': 'movie'},
        {'title': 'Metropolis', 'media_type': 'movie'},
        {'title': 'Memories', 'media_type': 'movie'},
        {'title': 'Ghost in the Shell 2: Innocence', 'media_type': 'movie'},
        {'title': 'The Animatrix', 'media_type': 'movie'},
        {'title': 'Redline', 'media_type': 'movie'},
        {'title': 'Psycho-Pass: The Movie', 'media_type': 'movie'},
        {'title': 'Expelled from Paradise', 'media_type': 'movie'},
        {'title': 'Blame!', 'media_type': 'movie'},
        {'title': 'Vexille', 'media_type': 'movie'},
        {'title': 'Battle Angel Alita', 'media_type': 'movie'},
        {'title': 'Genocidal Organ', 'media_type': 'movie'},
        {'title': 'Harmony', 'media_type': 'movie'},
        {'title': 'Spriggan', 'media_type': 'movie'},
        {'title': 'Tekkonkinkreet', 'media_type': 'movie'},
        {'title': 'Patlabor: The Movie', 'media_type': 'movie'},
        {'title': 'Patlabor 2: The Movie', 'media_type': 'movie'},
        {'title': 'Gantz: O', 'media_type': 'movie'},
        {'title': 'Patema Inverted', 'media_type': 'movie'},
        {'title': 'TRON', 'media_type': 'movie'}
    ]
    
    userstreamingproviders = ['Disney Plus', 'Amazon', 'Apple TV+']
    paymenttypes = ['free', 'rent']
    
    print("=" * 80)
    print("TESTING FILTER_STREAMING_PROVIDERS - MOVIES")
    print("=" * 80)
    print(f"\nTotal titles to check: {len(titles)}")
    print(f"Streaming providers: {', '.join(userstreamingproviders)}")
    print(f"Payment types: {', '.join(paymenttypes)}")
    print("\n" + "-" * 80 + "\n")
    
    # Call the tool
    result = filter_streaming_providers.invoke({
        'titleList': titles,
        'userstreamingproviders': userstreamingproviders,
        'paymenttypes': paymenttypes
    })
    
    return result


def test_tron():
    """
    Test filter_streaming_providers with TRON franchise (mixed movies and TV series)
    """
    titles = [
        {'title': 'Tron', 'media_type': 'movie'},
        {'title': 'Tron: Legacy', 'media_type': 'movie'},
        {'title': 'Tron: Uprising', 'media_type': 'tv'}
    ]
    
    userstreamingproviders = ['Disney Plus', 'Amazon', 'Apple TV+']
    paymenttypes = ['free', 'rent']
    
    print("=" * 80)
    print("TESTING FILTER_STREAMING_PROVIDERS - MIXED (Movies + TV)")
    print("=" * 80)
    print(f"\nTotal titles to check: {len(titles)}")
    print(f"Streaming providers: {', '.join(userstreamingproviders)}")
    print(f"Payment types: {', '.join(paymenttypes)}")
    print("\n" + "-" * 80 + "\n")
    
    # Call the tool
    result = filter_streaming_providers.invoke({
        'titleList': titles,
        'userstreamingproviders': userstreamingproviders,
        'paymenttypes': paymenttypes
    })
    
    return result


def test_tv_series():
    """
    Test filter_streaming_providers with popular TV series
    """
    titles = [
        {'title': 'Breaking Bad', 'media_type': 'tv'},
        {'title': 'Game of Thrones', 'media_type': 'tv'},
        {'title': 'Stranger Things', 'media_type': 'tv'},
        {'title': 'The Mandalorian', 'media_type': 'tv'},
        {'title': 'The Crown', 'media_type': 'tv'},
        {'title': 'The Witcher', 'media_type': 'tv'},
        {'title': 'House of the Dragon', 'media_type': 'tv'},
        {'title': 'The Last of Us', 'media_type': 'tv'},
        {'title': 'Wednesday', 'media_type': 'tv'},
        {'title': 'Better Call Saul', 'media_type': 'tv'},
        {'title': 'The Boys', 'media_type': 'tv'},
        {'title': 'Arcane', 'media_type': 'tv'},
        {'title': 'The Handmaid\'s Tale', 'media_type': 'tv'},
        {'title': 'Westworld', 'media_type': 'tv'},
        {'title': 'Dark', 'media_type': 'tv'},
        {'title': 'Ozark', 'media_type': 'tv'},
        {'title': 'Succession', 'media_type': 'tv'},
        {'title': 'Severance', 'media_type': 'tv'},
        {'title': 'The Office', 'media_type': 'tv'},
        {'title': 'Friends', 'media_type': 'tv'}
    ]
    
    userstreamingproviders = ['Netflix', 'Disney Plus', 'Amazon', 'Apple TV+', 'Sky']
    paymenttypes = ['free']
    
    print("=" * 80)
    print("TESTING FILTER_STREAMING_PROVIDERS - TV SERIES")
    print("=" * 80)
    print(f"\nTotal titles to check: {len(titles)}")
    print(f"Streaming providers: {', '.join(userstreamingproviders)}")
    print(f"Payment types: {', '.join(paymenttypes)}")
    print("\n" + "-" * 80 + "\n")
    
    # Call the tool
    result = filter_streaming_providers.invoke({
        'titleList': titles,
        'userstreamingproviders': userstreamingproviders,
        'paymenttypes': paymenttypes
    })
    
    return result


def test_sci_fi_mixed():
    """
    Test filter_streaming_providers with sci-fi movies and series mixed
    """
    titles = [
        # Movies
        {'title': 'Inception', 'media_type': 'movie'},
        {'title': 'Interstellar', 'media_type': 'movie'},
        {'title': 'The Matrix', 'media_type': 'movie'},
        {'title': 'Blade Runner 2049', 'media_type': 'movie'},
        {'title': 'Arrival', 'media_type': 'movie'},
        {'title': 'Ex Machina', 'media_type': 'movie'},
        {'title': 'Dune', 'media_type': 'movie'},
        {'title': 'The Martian', 'media_type': 'movie'},
        # TV Series
        {'title': 'Black Mirror', 'media_type': 'tv'},
        {'title': 'Foundation', 'media_type': 'tv'},
        {'title': 'For All Mankind', 'media_type': 'tv'},
        {'title': 'Raised by Wolves', 'media_type': 'tv'},
        {'title': 'Altered Carbon', 'media_type': 'tv'},
        {'title': 'The Expanse', 'media_type': 'tv'},
        {'title': 'Battlestar Galactica', 'media_type': 'tv'},
        {'title': 'Silo', 'media_type': 'tv'}
    ]
    
    userstreamingproviders = ['Netflix', 'Amazon', 'Apple TV+']
    paymenttypes = ['free', 'rent']
    
    print("=" * 80)
    print("TESTING FILTER_STREAMING_PROVIDERS - SCI-FI MIXED")
    print("=" * 80)
    print(f"\nTotal titles to check: {len(titles)}")
    print(f"Movies: {len([t for t in titles if t['media_type'] == 'movie'])}")
    print(f"TV Series: {len([t for t in titles if t['media_type'] == 'tv'])}")
    print(f"Streaming providers: {', '.join(userstreamingproviders)}")
    print(f"Payment types: {', '.join(paymenttypes)}")
    print("\n" + "-" * 80 + "\n")
    
    # Call the tool
    result = filter_streaming_providers.invoke({
        'titleList': titles,
        'userstreamingproviders': userstreamingproviders,
        'paymenttypes': paymenttypes
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
            media_type = title_info.get('media_type', 'unknown')
            media_icon = '🎬' if media_type == 'movie' else '📺' if media_type == 'tv' else '❓'
            media_label = 'Film' if media_type == 'movie' else 'Serie' if media_type == 'tv' else 'Unknown'
            print(f"\n{idx}. {media_icon} {title_info['title']} ({title_info.get('release_date', 'N/A')}) [{media_label}]")
            
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
    import sys
    
    # Choose which test to run
    print("\nAvailable Tests:")
    print("1. Cyberpunk Anime Movies")
    print("2. TRON Franchise (Mixed)")
    print("3. TV Series")
    print("4. Sci-Fi Mixed")
    
    # If argument provided, use it; otherwise default to test 3
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nEnter test number (1-4, default=3): ").strip() or "3"
    
    test_map = {
        "1": test_cyberpunk_anime_filter,
        "2": test_tron,
        "3": test_tv_series,
        "4": test_sci_fi_mixed
    }
    
    test_func = test_map.get(choice)
    if not test_func:
        print(f"Invalid choice: {choice}. Using default (TV Series)")
        test_func = test_tv_series
    
    try:
        # Run the selected test
        result = test_func()
        
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
