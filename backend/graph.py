import os
from xml.parsers.expat import model
import dotenv
import time
import json
import re
from typing import Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition, ToolNode
from backend.states import AgentState
from backend.prompts import get_content_researcher_prompt_single_provider, get_interest_analyst_prompt, get_content_researcher_prompt
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from backend.tools import get_all_tools
from langchain_core.messages import SystemMessage, AIMessage    
from openai import AzureOpenAI  
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from backend.utils.tmdb.common import Provider, PaymentTypes
import logging

logging.basicConfig(level=logging.INFO)

def initialize_gpt4omini_model():
    """
    Initialize Azure OpenAI model once.
    Called during graph creation to avoid repeated initialization.
    """

    # Initialize our LLM
    gpt4omini_model = ChatOpenAI(   
        api_key= os.getenv("OPENAI_API_KEY"),
        temperature=0.3,
        model="gpt-4o-mini"
        # todo maxtoken
    )
    print(f"[MODEL_INIT] ✓ Model initialized: gpt4o-mini")
    return gpt4omini_model    

def initialize_gpt41_model():
    """
    Initialize Azure OpenAI model once.
    Called during graph creation to avoid repeated initialization.
    """

    # Initialize our LLM
    gpt41_model = ChatOpenAI(   
        api_key= os.getenv("OPENAI_API_KEY"),
        temperature=0.3,
        model="gpt-4.1"
        # todo maxtoken
    )
    print(f"[MODEL_INIT] ✓ Model initialized: gpt-4.1")
    return gpt41_model    
    

def initialize_azmodel():
    """
    Initialize Azure OpenAI model once.
    Called during graph creation to avoid repeated initialization.
    """

    # Initialize our LLM
    #model = AzureChatOpenAI(   
    #    api_key= os.getenv("AZURE_API_KEY"),
    #    api_version="2025-01-01-preview",
    #    temperature=0.3,
    #    model="GPT4-UK",        
    #    azure_endpoint=os.getenv("AZURE_API_BASE")        
    #)
    
    
    endpoint = os.getenv("AZURE_ENDPOINT_URL", "https://gpt4-se-dev.openai.azure.com/")
    model_name = os.getenv("AZURE_DEPLOYMENT_NAME", "GPT-4o")
    api_version = os.getenv("AZURE_API_VERSION", "2025-01-01-preview")

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(), 
        "https://cognitiveservices.azure.com/.default"
    )

    az_model = AzureChatOpenAI(
        model=model_name,
        api_version=api_version,
        azure_endpoint=endpoint,
        temperature=0.3,
        azure_ad_token_provider=token_provider
    )
    
    print(f"[MODEL_INIT] ✓ Model initialized: {model_name}")
    return az_model


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
    #log_state("result_validator", dict(state), "ENTRY")
    
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
        #log_state("result_validator", {**state, **result}, "EXIT")
        return result
    
    # Success: Found titles
    if found_titles_count >= 1:
        print("[VALIDATOR] ✓ Success: Titles found")
        result = {
            "validation_status": "success",
            "next_agent": "__END__"
        }
        ##log_state("result_validator", {**state, **result}, "EXIT")
        return result
    
    # Should not happen, but fallback just in case
    print("[VALIDATOR] ⚠ Unexpected state: No titles and no signal, routing to END")
    result = {
        "validation_status": "success",
        "next_agent": "__END__"
    }
    #log_state("result_validator", {**state, **result}, "EXIT")
    return result

def fallback_response(state: AgentState):
    """
    Generates a helpful fallback response when no suitable content was found
    after maximum retry attempts.
    """
    #log_state("fallback_response", dict(state), "ENTRY")
    
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
    
    #log_state("fallback_response", {**state, **result}, "EXIT")
    return result

def analyst_output_validator(state: AgentState):
    """
    Validates that interest_analyst followed the rules and didn't recommend movies directly.
    If rules were broken, overrides behavior and forces routing to content_researcher.
    """
    #log_state("analyst_output_validator", dict(state), "ENTRY")
    
    # Get last message from analyst
    if not state.get("messages"):
        result = {"next_agent": state.get("next_agent", "__END__")}
        #log_state("analyst_output_validator", {**state, **result}, "EXIT")
        return result
    
    last_message = state["messages"][-1]
    content = last_message.content if hasattr(last_message, 'content') else str(last_message)
    content_lower = content.lower()
    
    # Define forbidden patterns that indicate direct movie recommendations
    forbidden_patterns = [
        r'🟢|🟡|🔴',  # Streaming symbols
        r'verfügbar auf',  # Availability phrases
        r'streamen auf',
        r'anschauen auf',
        r'flatrate|leihen|kaufen',  # Streaming terms
        r'\(\d{4}\)',  # Year numbers like (2020)
        r'netflix|disney|amazon prime|wow',  # Platform names in recommendations
    ]
    
    # Check for forbidden patterns
    rule_violation = any(re.search(pattern, content_lower) for pattern in forbidden_patterns)
    
    # Additional check: Does content look like a movie list?
    # (Multiple bullet points or numbered items without #FINISHED#)
    looks_like_movie_list = (
        (content.count('\n-') > 2 or content.count('\n•') > 2 or content.count('\n1.') > 0)
        and '#finished#' not in content_lower
    )
    
    if rule_violation or looks_like_movie_list:
        # VIOLATION DETECTED - Override behavior
        print("[VALIDATOR] ⚠️  Analyst broke rules - direct movie recommendations detected!")
        print(f"[VALIDATOR] Rule violation: {rule_violation}, Looks like list: {looks_like_movie_list}")
        
        # Extract the latest user input from conversation history
        latest_user_input = ""
        for msg in reversed(state.get("messages", [])):
            if hasattr(msg, 'type') and msg.type == 'human':
                latest_user_input = msg.content
                break
        
        # Get previous analyst result (search query) if it exists
        previous_query = state.get("analystresult", "")
        
        # Combine previous query with new user input for context-aware search
        if previous_query and latest_user_input:
            # User has refined their request - combine both
            combined_query = f"{previous_query}. Zusätzliche Anforderung: {latest_user_input}"
            print(f"[VALIDATOR] Combining previous query with new input")
        elif previous_query:
            # No new input, use previous query
            combined_query = previous_query
            print(f"[VALIDATOR] Using previous query")
        elif latest_user_input:
            # No previous query, use user input as base
            combined_query = f"Suche basierend auf Nutzeranfrage: {latest_user_input}"
            print(f"[VALIDATOR] Creating query from user input")
        else:
            # Fallback if nothing is available
            combined_query = "Allgemeine Film- und Seriensuche"
            print(f"[VALIDATOR] Using generic fallback query")
        
        result = {
            "messages": [AIMessage(content="Ich starte die Suche für dich...")],
            "next_agent": "content_researcher",
            "analystresult": combined_query,
            "validation_status": "override"  # Mark that we overrode
        }
        
        #log_state("analyst_output_validator", {**state, **result}, "EXIT")
        return result
    
    # No violation - pass through normally
    print("[VALIDATOR] ✓ Analyst output looks valid")
    result = {"next_agent": state.get("next_agent", "__END__")}
    
    #log_state("analyst_output_validator", {**state, **result}, "EXIT")
    return result

def create_interest_analyst(model):
    """Factory function to create interest_analyst node with model closure."""
    def interest_analyst(state: AgentState):
        #log_state("interest_analyst", dict(state), "ENTRY")
        
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
            #log_state("interest_analyst", {**state, **result}, "EXIT")
            return result
        else:
            # Interest Analyst hat eine Frage - wird normal angezeigt
            result = {
                "messages": [response],  # Normale Anzeige
                "analystresult": response_text, 
                "next_agent": "__END__"
            }
            #log_state("interest_analyst", {**state, **result}, "EXIT")
            return result
    
    return interest_analyst
    

def create_content_researcher(model):
    """Factory function to create content_researcher node with model closure."""
    def content_researcher(state: AgentState):
        """
        Content researcher with LLM-managed internal retry logic.
        LLM will make up to 3 attempts internally and send #NO_RESULTS# if unsuccessful.
        """
        # Only log on first entry (when no found_titles exist yet)
        found_titles = state.get("found_titles", [])
        is_first_call = len(found_titles) == 0
        
        #if is_first_call:
            #log_state("content_researcher", dict(state), "ENTRY")
           
        tools = get_all_tools()
        model_with_searchtools = model.bind_tools(tools)    

        default_streamingproviders = [provider.value for provider in Provider]
        userstreamingproviders = state.get("userstreamingproviders", default_streamingproviders)
        paymenttypes = state.get("paymenttypes", [payment.value for payment in PaymentTypes])
        analystresult = state.get("analystresult", "The best actual movies and tv-shows that match the user interest")
        found_titles = state.get("found_titles", [])
        
        print(f"[CONTENT_RESEARCHER] Using providers from state: {userstreamingproviders}")
        
        # Build system prompt
        base_prompt = get_content_researcher_prompt(userstreamingproviders, analystresult,paymenttypes)
        if len(userstreamingproviders) == 1:
            base_prompt = get_content_researcher_prompt_single_provider(userstreamingproviders, analystresult,paymenttypes)
        
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
        
        # ALWAYS add response to messages first (for tools_condition to work)
        result = {
            "messages": [response]
        }
        
        # THEN check for problems and add signals if needed
        # Check for AI Refusal (GPT-4o safety filter)
        if hasattr(response, 'response_metadata'):
            refusal = response.response_metadata.get('refusal')
            if refusal:
                print(f"[CONTENT_RESEARCHER] ⚠️  AI REFUSAL detected: {refusal}")
                print(f"[CONTENT_RESEARCHER] Response added to messages, tools_condition will handle routing")
                # Don't return early - let tools_condition handle the response
        
        # Check for empty/null content (but response might still have tool_calls)
        if not response.content or response.content == "null":
            print(f"[CONTENT_RESEARCHER] ⚠️  Empty response content")
            print(f"[CONTENT_RESEARCHER] Checking if tool_calls present...")
            if hasattr(response, 'tool_calls') and response.tool_calls:
                print(f"[CONTENT_RESEARCHER] ✓ Tool calls present, will execute tools")
            else:
                print(f"[CONTENT_RESEARCHER] No tool calls, signaling no_results")
                result["control_signal"] = "no_results"
                return result
        
        # Check for #NO_RESULTS# signal
        if hasattr(response, 'content') and isinstance(response.content, str):
            if "#NO_RESULTS#" in response.content or "#no_results#" in response.content.lower():
                print("[CONTENT_RESEARCHER] LLM sent #NO_RESULTS# signal after 3 attempts")
                result["control_signal"] = "no_results"
                return result
        
        # Normal flow - response already added to messages above
        return result
    
    return content_researcher

def tool_node_with_state_tracking(state: AgentState):
    """
    Custom tool node that tracks filter_streaming_providers results in state.
    """
    #log_state("tool_node", dict(state), "ENTRY")
    
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
    
    #log_state("tool_node", {**state, **result}, "EXIT")
    return result

def create_graph():
    
    dotenv.load_dotenv(dotenv_path=".env", override=True)
    
    # Initialize model ONCE for the entire graph
    model_gpt41 = initialize_gpt41_model()
    model_gpt4omini = initialize_gpt4omini_model()
    
    workflow = StateGraph(AgentState)

    # Create nodes with model closure (no re-initialization)
    workflow.add_node("interest_analyst", create_interest_analyst(model_gpt4omini))
    workflow.add_node("analyst_output_validator", analyst_output_validator)
    workflow.add_node("content_researcher", create_content_researcher(model_gpt41))
    workflow.add_node("tools", tool_node_with_state_tracking)
    workflow.add_node("result_validator", result_validator)
    workflow.add_node("fallback_response", fallback_response)
    
    # Entry Point definieren
    workflow.set_entry_point("interest_analyst")

    # Interest Analyst → Validator (IMMER zur Validierung)
    workflow.add_edge("interest_analyst", "analyst_output_validator")
    
    # Validator → Content Researcher oder END
    workflow.add_conditional_edges(
        "analyst_output_validator",
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


