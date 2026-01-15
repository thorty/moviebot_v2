import os
import dotenv
import time
import json
from typing import Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition, ToolNode
from backend.states import AgentState
from backend.prompts import get_content_researcher_prompt_single_provider, get_interest_analyst_prompt, get_content_researcher_prompt
from langchain_openai import AzureChatOpenAI
from backend.tools import get_all_tools
from langchain_core.messages import SystemMessage, AIMessage

def log_state(node_name: str, state: dict, position: str = "ENTRY"):
    """
    Logs state information before/after node execution.
    
    Args:
        node_name: Name of the node
        state: Current agent state
        position: "ENTRY" or "EXIT"
    """
    print(f"\n{'='*80}")
    print(f"[{position}] {node_name.upper()}")
    print(f"{'='*80}")
    
    # Log relevant state fields (excluding messages for brevity)
    found_titles = state.get("found_titles", [])
    state_summary = {
        "userstreamingproviders": state.get("userstreamingproviders", []),
        "analystresult": state.get("analystresult", "")[:100] + "..." if state.get("analystresult", "") else "",
        "next_agent": state.get("next_agent", ""),
        "control_signal": state.get("control_signal", ""),
        "found_titles_count": len(found_titles),
        "validation_status": state.get("validation_status", ""),
        "found_titles": found_titles,
        "last_filter_results": {
            "found_count": state.get("last_filter_results", {}).get("found_count", 0)
        } if state.get("last_filter_results") else {},
        "messages_count": len(state.get("messages", []))
    }
    
    print(json.dumps(state_summary, indent=2, ensure_ascii=False))
    print(f"{'='*80}\n")

def result_validator(state: AgentState):
    """
    Validates content search results.
    Checks if content_researcher found results or sent #NO_RESULTS# signal.
    
    Decision logic:
    - Content found: SUCCESS → END
    - #NO_RESULTS# signal: FALLBACK → fallback_response
    """
    log_state("result_validator", dict(state), "ENTRY")
    
    found_titles = state.get("found_titles", [])
    found_titles_count = len(found_titles)
    
    # Check control_signal (internal state, not in messages)
    control_signal = state.get("control_signal", "")
    no_results_signal = control_signal == "no_results"
    
    print(f"[VALIDATOR] Found titles: {found_titles_count}, No-results signal: {no_results_signal}")
    
    # LLM signaled no results after 3 attempts
    if no_results_signal:
        print("[VALIDATOR] ⚠ LLM sent #NO_RESULTS# signal, routing to fallback")
        result = {
            "validation_status": "max_retries",
            "next_agent": "fallback_response"
        }
        log_state("result_validator", {**state, **result}, "EXIT")
        return result
    
    # Success: Found titles
    if found_titles_count >= 1:
        print("[VALIDATOR] ✓ Success: Titles found")
        result = {
            "validation_status": "success",
            "next_agent": "__END__"
        }
        log_state("result_validator", {**state, **result}, "EXIT")
        return result
    
    # Should not happen, but fallback just in case
    print("[VALIDATOR] ⚠ Unexpected state: No titles and no signal, routing to END")
    result = {
        "validation_status": "success",
        "next_agent": "__END__"
    }
    log_state("result_validator", {**state, **result}, "EXIT")
    return result

def fallback_response(state: AgentState):
    """
    Generates a helpful fallback response when no suitable content was found
    after maximum retry attempts.
    """
    log_state("fallback_response", dict(state), "ENTRY")
    
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
    
    result = {
        "messages": [response_msg],
        "next_agent": "__END__"
    }
    
    log_state("fallback_response", {**state, **result}, "EXIT")
    return result

def interest_analyst(state: AgentState):
    log_state("interest_analyst", dict(state), "ENTRY")
    
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
        # Interest Analyst ist bereit - remove #FINISHED# from content before sending
        original_content = response.content if isinstance(response.content, str) else str(response.content)
        cleaned_response_text = original_content.replace("#FINISHED#", "").replace("#finished#", "").strip()
        
        # Create clean message without #FINISHED# tag
        clean_response = AIMessage(content=cleaned_response_text)
        
        # Reset state for new search cycle
        result = {
            "messages": [clean_response],  # Send cleaned message to user
            "next_agent": "content_researcher", 
            "analystresult": cleaned_response_text.lower(),
            "control_signal": "",  # Reset
            "validation_status": "pending",  # Reset
            "last_filter_results": {}  # Reset
        }
        log_state("interest_analyst", {**state, **result}, "EXIT")
        return result
    else:
        # Interest Analyst hat eine Frage - wird normal angezeigt
        result = {
            "messages": [response],  # Normale Anzeige
            "analystresult": response_text, 
            "next_agent": "__END__"
        }
        log_state("interest_analyst", {**state, **result}, "EXIT")
        return result
    

def content_researcher(state: AgentState):
    """
    Content researcher with LLM-managed internal retry logic.
    LLM will make up to 3 attempts internally and send #NO_RESULTS# if unsuccessful.
    """
    # Only log on first entry (when no found_titles exist yet)
    found_titles = state.get("found_titles", [])
    is_first_call = len(found_titles) == 0
    
    if is_first_call:
        log_state("content_researcher", dict(state), "ENTRY")
    
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
    found_titles = state.get("found_titles", [])
    
    print(f"[CONTENT_RESEARCHER] Using providers from state: {userstreamingproviders}")
    
    # Build system prompt
    base_prompt = get_content_researcher_prompt(userstreamingproviders, analystresult)
    if len(userstreamingproviders) == 1:
        base_prompt = get_content_researcher_prompt_single_provider(userstreamingproviders, analystresult)
    
    # Add blacklist to prevent duplicates
    if found_titles:
        blacklist_note = f"""
        
        **WICHTIG - Blacklist (bereits genutzte Titel):**
        Diese Titel wurden bereits verwendet und dürfen NICHT nochmal vorgeschlagen werden:
        {', '.join(found_titles)}
        
        Suche nach NEUEN, ANDEREN Titeln die noch nicht genannt wurden!
        """
        base_prompt += blacklist_note
    
    sys_msg = SystemMessage(content=base_prompt)
    response = model_with_searchtools.invoke([sys_msg] + state["messages"])
    
    # Check for #NO_RESULTS# signal
    if hasattr(response, 'content') and isinstance(response.content, str):
        if "#NO_RESULTS#" in response.content or "#no_results#" in response.content.lower():
            print("[CONTENT_RESEARCHER] LLM sent #NO_RESULTS# signal after 3 attempts")
            # Set control signal in state (not in messages)
            result = {
                "control_signal": "no_results"  # Internal signal for validator
            }
            log_state("content_researcher", {**state, **result}, "EXIT")
            return result
    
    # Normal flow - keep existing found_titles_count from tool_node
    # Only return messages, other state values are preserved by LangGraph
    result = {
        "messages": [response]
    }
    
    log_state("content_researcher", {**state, **result}, "EXIT")
    return result

def tool_node_with_state_tracking(state: AgentState):
    """
    Custom tool node that tracks filter_streaming_providers results in state.
    """
    log_state("tool_node", dict(state), "ENTRY")
    
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
                        
                        # Extrahiere Titelnamen für Blacklist
                        new_found = []
                        for title_info in available_titles:
                            if isinstance(title_info, dict) and 'title' in title_info:
                                new_found.append(title_info['title'])
                        
                        # Merge mit bereits gefundenen Titeln (keine Duplikate)
                        existing_found = state.get('found_titles', [])
                        updated_found = list(set(existing_found + new_found))
                        
                        print(f"[TOOL_NODE] Tracked filter results: {found_count} titles found")
                        if new_found:
                            print(f"[TOOL_NODE] New titles added to blacklist: {', '.join(new_found)}")
                        
                        # Update result mit tracking info
                        result.update({
                            "last_filter_results": filter_results,
                            "found_titles": updated_found
                        })
                        break
                except Exception as e:
                    print(f"[TOOL_NODE] Error parsing filter results: {e}")
                    import traceback
                    traceback.print_exc()
    
    log_state("tool_node", {**state, **result}, "EXIT")
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


