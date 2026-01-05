import os
import dotenv
import time
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition, ToolNode
from backend.states import AgentState
from backend.prompts import get_interest_analyst_prompt, get_content_researcher_prompt
from langchain_openai import AzureChatOpenAI
from backend.tools import get_all_tools
from langchain_core.messages import SystemMessage, AIMessage

def get_retry_strategy(retry_count: int) -> dict:
    """
    Progressive broadening strategy for content search retries.
    Each retry uses wider search criteria to increase chances of finding content.
    
    Args:
        retry_count: Current retry attempt (0-based)
    
    Returns:
        dict: Strategy configuration for the current retry
    """
    strategies = {
        0: {
            "search_scope": "exact_match",
            "year_range": 3,
            "genres": "strict",
            "description": "Genaue Übereinstimmung mit Nutzeranfrage"
        },
        1: {
            "search_scope": "similar_themes",
            "year_range": 5,
            "genres": "flexible",
            "include_lesser_known": True,
            "description": "Ähnliche Themen und weniger bekannte Titel"
        },
        2: {
            "search_scope": "broad_category",
            "year_range": 10,
            "genres": "any",
            "include_lesser_known": True,
            "alternative_suggestions": True,
            "description": "Breite Kategorie mit alternativen Vorschlägen"
        }
    }
    
    return strategies.get(retry_count, strategies[2])

def result_validator(state: AgentState):
    """
    Rule-based validation of content search results.
    Determines whether to end successfully, retry with broader criteria, or provide fallback.
    
    Decision logic:
    - >= 1 title found: SUCCESS → END
    - < 1 title AND retry_count < 2: RETRY → content_researcher (Retry 1 oder 2)
    - < 1 title AND retry_count >= 2: FALLBACK → fallback_response (nach 3 Versuchen total)
    
    Retry count: 0 = erster Versuch, 1 = zweiter Versuch, 2 = dritter Versuch
    """
    retry_count = state.get("retry_count", 0)
    max_retries = 2  # 0, 1, 2 = 3 Versuche total
    found_titles_count = state.get("found_titles_count", 0)
    
    print(f"[VALIDATOR] Attempt {retry_count + 1}/3, Found titles: {found_titles_count}")
    
    # Success: Genug Titel gefunden (mind. 2 für robuste Empfehlung)
    if found_titles_count >= 2:
        print("[VALIDATOR] ✓ Success: Sufficient titles found")
        return {
            "validation_status": "success",
            "next_agent": "__END__"
        }
    
    # Max retries erreicht: Fallback (nach Versuch 3)
    if retry_count >= max_retries:
        print("[VALIDATOR] ⚠ Max attempts (3) reached, routing to fallback")
        return {
            "validation_status": "max_retries",
            "next_agent": "fallback_response"
        }
    
    # Retry mit neuer Strategie
    new_retry_count = retry_count + 1
    new_strategy = get_retry_strategy(new_retry_count)
    
    print(f"[VALIDATOR] ↻ Starting attempt {new_retry_count + 1}/3 - Strategy: {new_strategy['description']}")
    
    return {
        "validation_status": "retry",
        "next_agent": "content_researcher",
        "retry_count": new_retry_count,
        "retry_strategy": new_strategy
    }

def fallback_response(state: AgentState):
    """
    Generates a helpful fallback response when no suitable content was found
    after maximum retry attempts.
    """
    userstreamingproviders = state.get("userstreamingproviders", [])
    
    fallback_message = f"""Leider konnte ich auf deinen Streaming-Plattformen ({', '.join(userstreamingproviders)}) keine passenden Titel zu deiner Anfrage finden.

Das kann verschiedene Gründe haben:
- Die gesuchten Inhalte sind aktuell nicht auf diesen Plattformen verfügbar
- Die Titel sind möglicherweise regional eingeschränkt
- Sehr spezifische Anfragen haben manchmal eine begrenzte Auswahl

**Meine Vorschläge:**
1. Formuliere deine Anfrage etwas breiter (z.B. ähnliche Genres oder Themen)
2. Nenne mir konkrete Filme/Serien die dir gefallen haben - dann finde ich ähnliche Inhalte
3. Wenn du an anderen Plattformen interessiert bist, kann ich auch dort suchen

Was möchtest du tun?"""
    
    response_msg = AIMessage(content=fallback_message)
    
    return {
        "messages": [response_msg],
        "next_agent": "__END__"
    }

def interest_analyst(state: AgentState):
        
    # Initialize our LLM
    model = AzureChatOpenAI(   
        api_key= os.getenv("AZURE_API_KEY"),
        api_version="2025-01-01-preview",
        temperature=0.3,
        model="GPT4-UK",        
        azure_endpoint=os.getenv("AZURE_API_BASE")
        
    )
  
    sys_msg = SystemMessage(content=get_interest_analyst_prompt())
    
    response = model.invoke([sys_msg] + state["messages"])          
    response_text = response.content.lower() if isinstance(response.content, str) else str(response.content).lower()
    is_finished = "#finished#" in response_text
    
    if is_finished:
        # Interest Analyst ist bereit - deine add_message Funktion filtert automatisch!
        original_content = response.content if isinstance(response.content, str) else str(response.content)
        cleaned_response_text = original_content.replace("#FINISHED#", "").replace("#finished#", "").strip()
        
        # WICHTIG: Reset retry state bei neuem Search-Zyklus
        return {
            "messages": [response],  # add_message Funktion filtert das #FINISHED# automatisch heraus!
            "next_agent": "content_researcher", 
            "analystresult": cleaned_response_text.lower(),
            "retry_count": 0,  # Reset für neuen Search
            "found_titles_count": 0,  # Reset
            "validation_status": "pending",  # Reset
            "last_filter_results": {}  # Reset
        }
    else:
        # Interest Analyst hat eine Frage - wird normal angezeigt
        return {
            "messages": [response],  # Normale Anzeige
            "analystresult": response_text, 
            "next_agent": "__END__"
        }
    

def content_researcher(state: AgentState):

    
    # Initialize our LLM
    model = AzureChatOpenAI(   
        api_key= os.getenv("AZURE_API_KEY"),
        api_version="2025-01-01-preview",
        temperature=0.3,
        model="GPT4-UK",        
        azure_endpoint=os.getenv("AZURE_API_BASE")
        
    )
    tools = get_all_tools()
    model_with_searchtools = model.bind_tools(tools)    

    default_streamingproviders = ["Netflix", "Disney Plus", "Amazon Prime", "Hulu", "HBO Max", "Apple TV+", "MagentaTV", "Joyn", "Sky Ticket"]
    userstreamingproviders = state.get("userstreamingproviders", default_streamingproviders)
    analystresult = state.get("analystresult", "The best actual movies and tv-shows that match the user interest")
    retry_count = state.get("retry_count", 0)
    retry_strategy = state.get("retry_strategy", get_retry_strategy(0))
    recommended_titles = state.get("recommended_titles", [])
    
    # Erweitere System Prompt mit Retry-Strategie
    base_prompt = get_content_researcher_prompt(userstreamingproviders, analystresult)
    
    # Füge Info über bereits empfohlene Titel hinzu
    if recommended_titles:
        duplicate_prevention = f"""
        
        **WICHTIG - Duplikat-Vermeidung:**
        Die folgenden Titel wurden bereits empfohlen und dürfen NICHT nochmal vorgeschlagen werden:
        {', '.join(recommended_titles)}
        
        Suche nach NEUEN, ANDEREN Titeln die noch nicht genannt wurden!
        """
        base_prompt += duplicate_prevention
    
    if retry_count > 0:
        strategy_hint = f"""
        
        **WICHTIG - Retry-Strategie (Versuch {retry_count + 1}/4):**
        - Such-Scope: {retry_strategy.get('search_scope', 'normal')}
        - Jahr-Range: letzte {retry_strategy.get('year_range', 3)} Jahre
        - Genre-Flexibilität: {retry_strategy.get('genres', 'strict')}
        - Strategie: {retry_strategy.get('description', 'Standard-Suche')}
        
        Passe deine Suchanfragen entsprechend an, um mehr Ergebnisse zu finden!
        """
        base_prompt += strategy_hint
    
    sys_msg = SystemMessage(content=base_prompt)
    response = model_with_searchtools.invoke([sys_msg] + state["messages"])
    
    # Extrahiere found_titles_count aus Tool-Calls wenn vorhanden
    found_count = 0
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            if tool_call.get('name') == 'filter_streaming_providers':
                # Dieser Wert wird später vom ToolNode aktualisiert
                print("[CONTENT_RESEARCHER] filter_streaming_providers wird aufgerufen")
    
    # Falls bereits Filter-Ergebnisse im State vorhanden
    if state.get("last_filter_results"):
        found_count = state["last_filter_results"].get("found_count", 0)
    
    return {
        "messages": [response],
        "found_titles_count": found_count
    }

def tool_node_with_state_tracking(state: AgentState):
    """
    Custom tool node that tracks filter_streaming_providers results in state.
    """
    tools = get_all_tools()
    tool_node = ToolNode(tools)
    
    # Führe Tools aus
    result = tool_node.invoke(state)
    
    # Extrahiere Filter-Ergebnisse aus der letzten Tool-Nachricht
    if "messages" in result:
        for msg in reversed(result["messages"]):
            if hasattr(msg, 'name') and msg.name == 'filter_streaming_providers':
                try:
                    # Parse Tool-Result
                    if hasattr(msg, 'content'):
                        content = msg.content
                        
                        # Content kann schon ein dict sein oder ein JSON-String
                        if isinstance(content, dict):
                            filter_results = content
                        elif isinstance(content, str):
                            import json
                            filter_results = json.loads(content)
                        else:
                            print(f"[TOOL_NODE] Unknown content type: {type(content)}")
                            continue
                        
                        found_count = filter_results.get('found_count', 0)
                        available_titles = filter_results.get('available_titles', [])
                        
                        # Extrahiere Titelnamen für Duplikat-Tracking
                        new_recommended = []
                        for title_info in available_titles:
                            if isinstance(title_info, dict) and 'title' in title_info:
                                new_recommended.append(title_info['title'])
                        
                        # Merge mit bereits empfohlenen Titeln (keine Duplikate)
                        existing_recommended = state.get('recommended_titles', [])
                        updated_recommended = list(set(existing_recommended + new_recommended))
                        
                        print(f"[TOOL_NODE] Tracked filter results: {found_count} titles found")
                        if new_recommended:
                            print(f"[TOOL_NODE] New recommendations: {', '.join(new_recommended)}")
                        
                        # Update result mit tracking info
                        result.update({
                            "last_filter_results": filter_results,
                            "found_titles_count": found_count,
                            "recommended_titles": updated_recommended
                        })
                        break
                except Exception as e:
                    print(f"[TOOL_NODE] Error parsing filter results: {e}")
                    import traceback
                    traceback.print_exc()
    
    return result
    
    return result

def create_graph():
    
    dotenv.load_dotenv(dotenv_path=".env", override=True)
    
    workflow = StateGraph(AgentState)

    # Nodes hinzufügen
    workflow.add_node("interest_analyst", interest_analyst)
    workflow.add_node("content_researcher", content_researcher)
    workflow.add_node("tools", tool_node_with_state_tracking)
    workflow.add_node("result_validator", result_validator)
    workflow.add_node("fallback_response", fallback_response)
    
    # Entry Point definieren
    workflow.set_entry_point("interest_analyst")

    # Interest Analyst → Content Researcher oder END
    workflow.add_conditional_edges(
        "interest_analyst",
        lambda state: state.get("next_agent", "__END__"),
        {
            "content_researcher": "content_researcher",
            "__END__": END
        }
    )

    # Content Researcher → Tools (immer, da er Tools nutzen muss)
    workflow.add_conditional_edges(
        "content_researcher",
        # If the latest message (result) from assistant is a tool call → tools
        # If the latest message (result) from assistant is not a tool call → validator
        tools_condition,
        {
            "tools": "tools",
            END: "result_validator"  # Wenn keine tool_calls mehr: zur Validierung
        }
    )
    
    # Tools → Content Researcher (zurück für finale Antwort)
    workflow.add_edge("tools", "content_researcher")

    # Result Validator → Content Researcher (retry) oder END oder Fallback
    workflow.add_conditional_edges(
        "result_validator",
        lambda state: state.get("next_agent", "__END__"),
        {
            "content_researcher": "content_researcher",
            "fallback_response": "fallback_response",
            "__END__": END
        }
    )
    
    # Fallback Response → END
    workflow.add_edge("fallback_response", END)

    # Graph mit dem in-memory Checkpoint kompilieren
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    draw_graph(app)
    return app

def draw_graph(graph) -> None:
    """Draws the graph using Mermaid syntax."""
    try:
        with open("graph.png", "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
    except Exception:
        # This requires some extra dependencies and is optional
        pass


