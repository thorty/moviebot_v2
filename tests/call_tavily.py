"""
Test script für Tavily API - Mediathek Search
"""
import os
from tavily import TavilyClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_basic_search():
    """Einfache Tavily Suche."""
    print("="*80)
    print("TEST 1: Basic Tavily Search")
    print("="*80)
    
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    query = "Klimawandel Dokumentation"
    
    print(f"\nQuery: {query}")
    print("\nSearching...")
    
    response = client.search(
        query=query,
        search_depth="basic",
        max_results=5
    )
    
    print(f"\nResults found: {len(response.get('results', []))}")
    print("\n" + "-"*80)
    
    for i, result in enumerate(response.get('results', []), 1):
        print(f"\n{i}. {result.get('title', 'N/A')}")
        print(f"   URL: {result.get('url', 'N/A')}")
        print(f"   Score: {result.get('score', 'N/A')}")
        print(f"   Content: {result.get('content', 'N/A')[:200]}...")
    
    print("\n" + "="*80)


def test_mediathek_search_with_include_domains():
    """Tavily Suche nur in Mediatheken (include_domains)."""
    print("\n\n")
    print("="*80)
    print("TEST 2: Mediathek Search with include_domains")
    print("="*80)
    
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    query = "Finde Fantasy Filme oder Serien die aktuell in den mediatheken verfügbar sind: ard und zdf"
    mediathek_domains = [
        "ardmediathek.de",
        "zdf.de",
    ]
    
    print(f"\nQuery: {query}")
    print(f"Include domains: {mediathek_domains}")
    print("\nSearching...")
    
    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=10,
        include_domains=mediathek_domains
    )
    
    results = response.get('results', [])
    print(f"\nResults found: {len(results)}")
    print("\n" + "-"*80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('title', 'N/A')}")
        print(f"   URL: {result.get('url', 'N/A')}")
        print(f"   Score: {result.get('score', 'N/A')}")
        print(f"   Content: {result.get('content', 'N/A')[:300]}...")
    
    if not results:
        print("\n⚠️  Keine Ergebnisse gefunden!")
        print("   Mögliche Gründe:")
        print("   - Tavily hat diese Domains noch nicht gecrawlt")
        print("   - Query zu spezifisch")
        print("   - Versuche allgemeinere Suche")
    
    print("\n" + "="*80)


def test_mediathek_search_with_context():
    """Tavily Suche mit Mediathek-Context in der Query."""
    print("\n\n")
    print("="*80)
    print("TEST 3: Mediathek Search with Context in Query")
    print("="*80)
    
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    base_query = "Klimawandel Dokumentation"
    enhanced_query = f"{base_query} ARD ZDF Arte Mediathek"
    
    print(f"\nOriginal Query: {base_query}")
    print(f"Enhanced Query: {enhanced_query}")
    print("\nSearching...")
    
    response = client.search(
        query=enhanced_query,
        search_depth="advanced",
        max_results=10
    )
    
    results = response.get('results', [])
    print(f"\nResults found: {len(results)}")
    print("\n" + "-"*80)
    
    # Filtere Mediathek-Ergebnisse
    mediathek_keywords = ['ard', 'zdf', 'arte', '3sat', 'phoenix', 'mediathek']
    mediathek_results = []
    other_results = []
    
    for result in results:
        url_lower = result.get('url', '').lower()
        title_lower = result.get('title', '').lower()
        
        if any(keyword in url_lower or keyword in title_lower for keyword in mediathek_keywords):
            mediathek_results.append(result)
        else:
            other_results.append(result)
    
    print(f"\n📺 Mediathek Results: {len(mediathek_results)}")
    for i, result in enumerate(mediathek_results, 1):
        print(f"\n{i}. {result.get('title', 'N/A')}")
        print(f"   URL: {result.get('url', 'N/A')}")
        print(f"   Score: {result.get('score', 'N/A')}")
        print(f"   Content: {result.get('content', 'N/A')[:200]}...")
    
    print(f"\n\n🌐 Other Results: {len(other_results)}")
    for i, result in enumerate(other_results[:3], 1):
        print(f"\n{i}. {result.get('title', 'N/A')}")
        print(f"   URL: {result.get('url', 'N/A')}")
    
    print("\n" + "="*80)


def test_answer_mode():
    """Tavily Answer Mode - direktes LLM-generiertes Answer."""
    print("\n\n")
    print("="*80)
    print("TEST 4: Tavily Answer Mode")
    print("="*80)
    
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    query = "Welche Dokumentationen über Klimawandel gibt es in deutschen Mediatheken?"
    
    print(f"\nQuery: {query}")
    print("\nSearching...")
    
    response = client.search(
        query=query,
        search_depth="advanced",
        include_answer=True,
        max_results=5
    )
    
    print("\n" + "-"*80)
    print("ANSWER:")
    print("-"*80)
    print(response.get('answer', 'No answer generated'))
    
    print("\n" + "-"*80)
    print("SOURCES:")
    print("-"*80)
    for i, result in enumerate(response.get('results', []), 1):
        print(f"{i}. {result.get('title', 'N/A')}")
        print(f"   {result.get('url', 'N/A')}\n")
    
    print("="*80)


if __name__ == "__main__":
    # Prüfe ob API Key vorhanden
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ ERROR: TAVILY_API_KEY nicht gefunden!")
        print("   Setze den API Key in .env Datei:")
        print("   TAVILY_API_KEY=your_key_here")
        exit(1)
    
    print("\n🔍 Tavily API Test Suite")
    print("Testing verschiedene Ansätze für Mediathek-Suche\n")
    
    # Führe alle Tests aus
    try:
        #test_basic_search()
        test_mediathek_search_with_include_domains()
        #test_mediathek_search_with_context()
        #test_answer_mode()
        
        print("\n\n✅ Alle Tests abgeschlossen!")
        
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
