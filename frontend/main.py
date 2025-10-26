import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.graph import create_graph
from backend.utils.setupenv import enable_langsmith
from langchain_core.messages import HumanMessage


def create_chatbot():
    
    #init langsmith
    enable_langsmith()
    
    
    """Erstellt und konfiguriert den LangGraph Chatbot"""
    print("🤖 Chatbot wird initialisiert...")
    
    
    # Graph erstellen
    graph = create_graph()
    
    print("✅ Chatbot erfolgreich initialisiert!")
    print("💡 Tipp: Du kannst nach Film- und Serienempfehlungen fragen!")
    print("🔚 Zum Beenden gib 'quit', 'exit' oder 'q' ein.\n")
    
    return graph

def stream_graph_updates(graph, user_input: str):
    """Streamt die Updates vom Graph und zeigt sie in der Konsole an"""
    try:
        # Konfiguration für den Graph-Stream mit Thread-ID für Speicher
        config = {"configurable": {"thread_id": "main_conversation"}}
        
        # Input für den Graph vorbereiten
        graph_input = {
            "messages": [HumanMessage(content=user_input)],
            #"userstreamingproviders": ["Netflix", "Disney Plus", "Amazon Prime", "Hulu", "HBO Max", "Apple TV+", "MagentaTV", "Joyn", "Sky Ticket"]
            "userstreamingproviders": ["Disney Plus", "Amazon Prime", "Apple TV+"]
        }
        
        print("\n🤔 Analysiere deine Anfrage...")
        
        # Graph streamen und Antworten anzeigen
        for event in graph.stream(graph_input, config=config):
            for node_name, value in event.items():
                if "messages" in value and value["messages"]:
                    latest_message = value["messages"][-1]
                    if hasattr(latest_message, 'content') and latest_message.content:
                        # Bereinige die Ausgabe von internen Markern
                        content = latest_message.content.replace("#FINISHED#", "").strip()
                        if content:
                            print(f"\n🤖 {node_name}: {content}")
                            
    except Exception as e:
        print(f"❌ Fehler beim Verarbeiten der Anfrage: {str(e)}")
        print("🔄 Bitte versuche es erneut oder formuliere deine Anfrage anders.")

def main():
    """Hauptfunktion für den Chatbot"""
    print("=" * 60)
    print("🎬 FILM & SERIEN EMPFEHLUNGS-CHATBOT 🎬")
    print("=" * 60)
    
    # Graph erstellen
    try:
        graph = create_chatbot()
    except Exception as e:
        print(f"❌ Fehler beim Initialisieren des Chatbots: {str(e)}")
        print("🔧 Bitte überprüfe deine Umgebungsvariablen (.env Datei)")
        return
    
    # Chat-Loop
    while True:
        try:
            user_input = input("\n👤 Du: ").strip()
            
            if not user_input:
                print("⚠️  Bitte gib eine Nachricht ein.")
                continue
                
            if user_input.lower() in ["quit", "exit", "q", "bye", "tschüss"]:
                print("\n👋 Auf Wiedersehen! Viel Spaß beim Schauen! 🎬")
                break
                
            stream_graph_updates(graph, user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 Chat beendet. Bis bald!")
            break
        except EOFError:
            # Fallback wenn input() nicht verfügbar ist (z.B. in manchen IDEs)
            print("⚠️  Input nicht verfügbar. Teste mit Beispiel-Anfrage...")
            user_input = "Ich suche nach einem lustigen Film für heute Abend"
            print(f"👤 Du: {user_input}")
            stream_graph_updates(graph, user_input)
            break
        except Exception as e:
            print(f"❌ Unerwarteter Fehler: {str(e)}")
            print("🔄 Der Chat läuft weiter...")

if __name__ == "__main__":
    main()