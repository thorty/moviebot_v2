import os
import dotenv
import json
import re
from typing import Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition, ToolNode
from backend.states import AgentState
from backend.prompts import get_content_researcher_prompt_single_provider, get_interest_analyst_prompt, get_content_researcher_prompt, get_content_researcher_prompt_mediatheken, get_scope_guard_prompt
from langchain_openai import ChatOpenAI
from backend.tools import get_all_tools, get_tools_for_providers
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from backend.utils.tmdb.common import Provider, PaymentTypes
import logging

logging.basicConfig(level=logging.INFO)

def initialize_analyst_model():
    """
    Initialize model once.
    Called during graph creation to avoid repeated initialization.
    """
    model_name = "gemini-2.5-flash"
    analystmodel = ChatOpenAI(
        openai_api_key=os.getenv('TSYSTEMS_API_KEY'), 
        openai_api_base=os.getenv('TSYSTEMS_BASE_URL'),
        model=model_name,
        temperature=0.3,     
        max_completion_tokens=2048,          # Genug für Analyse + Folgefragen
        top_p=0.9,               # Fokus
        frequency_penalty=0.05,   # Wenig Wiederholungen
        streaming=False        
        )
    

    # Initialize our LLM
    #gpt4omini_model = ChatOpenAI(   
    #    api_key= os.getenv("OPENAI_API_KEY"),
    #    temperature=0.3,
    #    model="gpt-4o-mini"
        # todo maxtoken
    #)
    print(f"[MODEL_INIT] ✓ Model initialized: {model_name}")
    return analystmodel    

def initialize_research_model():
    """
    Initialize model once.
    Called during graph creation to avoid repeated initialization.
    """

    model_name = "claude-3-7-sonnet"
    research_model = ChatOpenAI(
       openai_api_key=os.getenv('TSYSTEMS_API_KEY'), 
       openai_api_base=os.getenv('TSYSTEMS_BASE_URL'),
       model=model_name,
       temperature=0.0,          # 0 für Claude: Deterministisch bei Tools (Docs empfehlen)[web:97][web:98]
       max_completion_tokens=10000,          # Hoch für Tavily-Results + Ranking-Logik
       top_p=0.95,               # Etwas flexibler für kreative Queries
       frequency_penalty=0.1,    # Vermeidet Loop-Wiederholungen
       streaming=False
   )
    
    # model_name = "gemini-2.5-pro"  # Oder "gemini-2.5-pro-exp" falls verfügbar
    # research_model = ChatOpenAI(
    #     openai_api_key=os.getenv('TSYSTEMS_API_KEY'), 
    #     openai_api_base=os.getenv('TSYSTEMS_BASE_URL'),
    #     model=model_name,
    #     temperature=0.1,              # Low: Präzise Tool-Queries (0.0–0.2 ideal)[web:105][web:149]
    #     max_completion_tokens=4096,   # Output-Limit (Gemini: bis 8k+)[web:144]
    #     top_p=0.95,                   # Nucleus-Sampling für Fokus (0.9–1.0)[web:146]
    #     #top_k=40,                     # Top-40 Tokens (reduziert Randomness)[web:144]
    #     frequency_penalty=0.1,        # Weniger Wiederholungen in Loops
    #     presence_penalty=0.0,         # Neutral für Research
    #     max_retries=2,                # Retry bei Fehlern
    #     streaming=False
    # )        
        
    

    # Initialize our LLM
    #gpt41_model = ChatOpenAI(   
    #    api_key= os.getenv("OPENAI_API_KEY"),
    #    temperature=0.3,
    #    model="gpt-4.1",
    #    max_tokens=10000
    
        # todo maxtoken
    #)
    print(f"[MODEL_INIT] ✓ Model initialized: {model_name}")
    return research_model    
    

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
        "user_id": state.get("user_id", ""),
        "conversation_id": state.get("conversation_id", ""),
        "userstreamingproviders": state.get("userstreamingproviders", []),
        "analystresult": state.get("analystresult", "")[:100] + "..." if state.get("analystresult", "") else "",
        "scope_status": state.get("scope_status", ""),
        "scope_reason": state.get("scope_reason", ""),
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


def _remove_prior_turn_tool_messages(messages: list[Any]) -> list[Any]:
    """
    Remove tool execution traces from earlier user turns to keep context compact.

    For turns before the latest human message, removes:
    - tool messages, and
    - assistant messages that contain tool_calls.

    Keeps messages from the current turn (after latest human), so ongoing
    tool loops still work.
    """
    if not messages:
        return messages

    latest_human_index = -1
    for idx, msg in enumerate(messages):
        if getattr(msg, "type", "") == "human":
            latest_human_index = idx

    pruned_messages: list[Any] = []
    for idx, msg in enumerate(messages):
        msg_type = getattr(msg, "type", "")
        is_prior_turn = idx <= latest_human_index
        has_tool_calls = bool(getattr(msg, "tool_calls", None))

        if is_prior_turn and msg_type == "tool":
            continue

        if is_prior_turn and msg_type == "ai" and has_tool_calls:
            continue

        pruned_messages.append(msg)

    return pruned_messages


def _extract_presented_titles_from_text(text: str) -> list[str]:
    """
    Extract recommendation titles from final assistant text.
    Expected primary format: 🎬 **Title (Year)**
    """
    if not text:
        return []

    titles: list[str] = []
    seen: set[str] = set()
    patterns = [
        r"🎬\s*\*\*([^*\n]+?)\s*\((?:19|20)\d{2}\)\*\*",
        r"🎬\s*\*\*([^*\n]+?)\*\*",
    ]

    for pattern in patterns:
        for match in re.findall(pattern, text):
            title = str(match).strip().strip("-• ")
            key = title.casefold()
            if not title or key in seen:
                continue
            seen.add(key)
            titles.append(title)

    return titles


def create_scope_guard(model):
    """Factory function for pre-routing in-scope / out-of-scope requests."""
    in_scope_pattern = re.compile(
        r"\b(film|filme|movie|movies|serie|serien|tv\s*show|show|stream|streaming|"
        r"netflix|disney\+?|prime|amazon\s*prime|apple\s*tv|wow|sky|ard|zdf|mediathek|"
        r"genre|thriller|komödie|drama|sci[-\s]?fi|doku|dokumentation|anime)\b",
        re.IGNORECASE,
    )

    media_context_pattern = re.compile(
        r"\b(film|filme|movie|movies|serie|serien|tv\s*show|show|doku|dokumentation|"
        r"stream|streaming|staffel|empfehl|vorschlag|anschauen|sehen)\b",
        re.IGNORECASE,
    )

    thematic_domain_pattern = re.compile(
        r"\b(finanz|börse|wirtschaft|geld|bank|medizin|arzt|klinik|krankenhaus|"
        r"anwalt|kanzlei|gericht|justiz|recht)\b",
        re.IGNORECASE,
    )

    strong_out_of_scope_pattern = re.compile(
        r"\b(code|python|javascript|bug|debug|sql|excel|rezept|kochen|wetter|mathe|"
        r"gleichung|algebra|integral|ableitung|hausaufgabe|lebenslauf|bewerbung|"
        r"übersetz|translate)\b",
        re.IGNORECASE,
    )

    def scope_guard(state: AgentState):
        recent_turns: list[str] = []
        latest_user_input = ""
        relevant_types = {"human", "ai"}
        max_turns = 8

        for msg in reversed(state.get("messages", [])):
            msg_type = getattr(msg, "type", "")
            if msg_type not in relevant_types:
                continue

            content = msg.content if hasattr(msg, "content") else ""
            text = content if isinstance(content, str) else str(content)
            normalized_text = text.strip()
            if not normalized_text:
                continue

            if not latest_user_input and msg_type == "human":
                latest_user_input = normalized_text

            speaker = "User" if msg_type == "human" else "Assistant"
            recent_turns.append(f"{speaker}: {normalized_text}")

            if len(recent_turns) >= max_turns:
                break

        recent_turns.reverse()
        conversation_context = "\n".join(recent_turns)

        if not conversation_context:
            return {
                "scope_status": "in_scope",
                "scope_reason": "no_user_message",
                "next_agent": "interest_analyst",
            }

        if not latest_user_input:
            latest_user_input = conversation_context

        has_in_scope = bool(in_scope_pattern.search(conversation_context))
        has_media_context = bool(media_context_pattern.search(conversation_context))
        has_thematic_domain = bool(thematic_domain_pattern.search(conversation_context))
        has_strong_out_of_scope = bool(strong_out_of_scope_pattern.search(conversation_context))

        # Allow topic-domain requests when they are clearly about media content
        # e.g. "Finanzdokus", "medizinische Dokus", "Anwaltsserien"
        if has_media_context and (has_in_scope or has_thematic_domain):
            return {
                "scope_status": "in_scope",
                "scope_reason": "media_context_with_thematic_domain",
                "next_agent": "interest_analyst",
            }

        if has_in_scope and not has_strong_out_of_scope:
            return {
                "scope_status": "in_scope",
                "scope_reason": "keyword_in_scope",
                "next_agent": "interest_analyst",
            }

        # Hard out-of-scope only when there are no media signals across the conversation
        if has_strong_out_of_scope and not has_in_scope and not has_media_context:
            return {
                "scope_status": "out_of_scope",
                "scope_reason": "keyword_out_of_scope",
                "next_agent": "out_of_scope_response",
            }

        sys_msg = SystemMessage(content=get_scope_guard_prompt())
        classifier_input = HumanMessage(content=conversation_context)
        response = model.invoke([sys_msg, classifier_input])
        label = (response.content if isinstance(response.content, str) else str(response.content)).strip().lower()

        if "out_of_scope" in label:
            return {
                "scope_status": "out_of_scope",
                "scope_reason": "llm_classifier",
                "next_agent": "out_of_scope_response",
            }

        if "unclear" in label:
            return {
                "scope_status": "unclear",
                "scope_reason": "llm_classifier",
                "messages": [AIMessage(content="Soll ich dir bei Film- oder Serienempfehlungen helfen? Wenn du mir sagst, worauf du Lust hast, suche ich dir was raus 🎥 🍿")],
                "next_agent": "__END__",
            }

        return {
            "scope_status": "in_scope",
            "scope_reason": "llm_classifier",
            "next_agent": "interest_analyst",
        }

    return scope_guard


def out_of_scope_response(state: AgentState):
    """Friendly response for requests outside movie/series recommendation scope."""
    response_msg = AIMessage(
        content=(
            "Da bin ich leider raus 😅 – aber bei Filmen und Serien kenn ich mich richtig gut aus!"
            "Sag mir einfach, worauf du Lust hast und ich finde was Passendes. 🎥 🍿"
        )
    )
    return {
        "messages": [response_msg],
        "next_agent": "__END__",
    }

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
    last_filter_results = state.get("last_filter_results", {})
    last_filter_found_count = 0
    if isinstance(last_filter_results, dict):
        last_filter_found_count = int(last_filter_results.get("found_count", 0) or 0)
    effective_found_count = max(found_titles_count, last_filter_found_count)
    
    # Check control_signal (internal state, not in messages)
    control_signal = state.get("control_signal", "")
    no_results_signal = control_signal == "no_results"
    
    print(
        f"[VALIDATOR] Found titles(blacklist): {found_titles_count}, "
        f"last_filter_found_count: {last_filter_found_count}, "
        f"effective_found_count: {effective_found_count}, "
        f"No-results signal: {no_results_signal}"
    )
    
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
    if effective_found_count >= 1:
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
    
    fallback_message = """
    Aktuell habe ich auf deinen gewählten Plattformen nichts wirklich Passendes gefunden.

    Lass uns mit einer leicht angepassten Suche direkt weitermachen:
    • Weitere Plattformen auswählen
    • Anfrage breiter formulieren (Genre, Stimmung oder Zeitraum)
    • 1–2 Referenztitel nennen, die dir gefallen

    Schreib kurz, welche Richtung du willst, dann starte ich die nächste Suche.
    """
    
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
    content_str = content if isinstance(content, str) else str(content)
    content_lower = content_str.lower()
    
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
        (content_str.count('\n-') > 2 or content_str.count('\n•') > 2 or content_str.count('\n1.') > 0)
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
        
        original_messages = state.get("messages", [])
        llm_messages = _remove_prior_turn_tool_messages(original_messages)
        removed_count = len(original_messages) - len(llm_messages)
        if removed_count > 0:
            print(
                f"[CONTEXT_PRUNE][interest_analyst] total_messages={len(original_messages)} "
                f"after_prune={len(llm_messages)} removed={removed_count}"
            )
        response = model.invoke([sys_msg] + llm_messages)
        original_content = response.content if isinstance(response.content, str) else str(response.content)
        response_text = original_content.lower()
        normalized_response = original_content.strip()
        has_finished_tag = "#finished#" in response_text
        ends_with_question_mark = normalized_response.endswith("?")
        is_finished = has_finished_tag or (bool(normalized_response) and not ends_with_question_mark)

        finish_reason = "question_pending"
        if has_finished_tag:
            finish_reason = "finished_tag"
        elif bool(normalized_response) and not ends_with_question_mark:
            finish_reason = "no_trailing_question_mark"

        print(
            f"[INTEREST_ANALYST] finish_check: "
            f"has_finished_tag={has_finished_tag}, "
            f"ends_with_question_mark={ends_with_question_mark}, "
            f"is_finished={is_finished}, "
            f"reason={finish_reason}"
        )
        
        if is_finished:
            # Interest Analyst ist bereit - remove #FINISHED# from content before sending
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
        
        #if is_first_call:
            #log_state("content_researcher", dict(state), "ENTRY")
           
        default_streamingproviders = [provider.value for provider in Provider]
        userstreamingproviders = state.get("userstreamingproviders", default_streamingproviders)
        paymenttypes = state.get("paymenttypes", [payment.value for payment in PaymentTypes])
        analystresult = state.get("analystresult", "The best actual movies and tv-shows that match the user interest")
        found_titles = state.get("found_titles", [])
        last_filter_results = state.get("last_filter_results", {})
        last_filter_found_count = 0
        if isinstance(last_filter_results, dict):
            last_filter_found_count = int(last_filter_results.get("found_count", 0) or 0)

        force_finalize = last_filter_found_count >= 2

        tools = get_tools_for_providers(userstreamingproviders)
        model_with_searchtools = model.bind_tools(tools)
        
        print(f"[CONTENT_RESEARCHER] Using providers from state: {userstreamingproviders}")
        
        # Build system prompt
        base_prompt = get_content_researcher_prompt(userstreamingproviders, analystresult,paymenttypes)
        if len(userstreamingproviders) == 1:
            base_prompt = get_content_researcher_prompt_single_provider(userstreamingproviders[0], analystresult,paymenttypes)
        # Check for Mediatheken (case-insensitive)
        if any(p.lower() == "mediatheken" for p in userstreamingproviders):
            paymenttypes = ["free"]  # Override payment types for mediatheken to simplify prompt
            base_prompt = get_content_researcher_prompt_mediatheken(userstreamingproviders, analystresult,paymenttypes)
            print(f"[CONTENT_RESEARCHER] 📺 Using Mediatheken-specific prompt (ARD/ZDF only, no TMDB)")
        # Add blacklist to prevent duplicates
        if found_titles:
            blacklist_note = f"""
        
        **WICHTIG - Blacklist (bereits genutzte Titel):**
        Diese Titel wurden bereits verwendet und dürfen NICHT nochmal vorgeschlagen werden:
        {', '.join(found_titles)}
        
        Suche nach NEUEN, ANDEREN Titeln die noch nicht genannt wurden!
        """
            base_prompt += blacklist_note

        if force_finalize:
            finalize_note = f"""

        **EARLY STOP ACTIVATED - FINALIZE NOW**
        - The latest `filter_streaming_providers` result already found {last_filter_found_count} suitable title(s).
        - You MUST finalize now using only the titles from the latest filter results.
        - Do NOT call any search or filter tool again.
        - If 4 or more suitable titles exist, output the best 4.
        - If only 2-3 suitable titles exist, output exactly those 2-3.
        - Do not continue searching just to find more titles.
            """
            base_prompt += finalize_note
        
        sys_msg = SystemMessage(content=base_prompt)
        original_messages = state.get("messages", [])
        llm_messages = _remove_prior_turn_tool_messages(original_messages)
        removed_count = len(original_messages) - len(llm_messages)
        if removed_count > 0:
            print(
                f"[CONTEXT_PRUNE][content_researcher] total_messages={len(original_messages)} "
                f"after_prune={len(llm_messages)} removed={removed_count}"
            )
        if force_finalize:
            print(f"[CONTENT_RESEARCHER] Early stop active with {last_filter_found_count} filtered title(s); finalizing without more tool calls")

        # Keep using the tool-bound model even during forced finalization.
        # Anthropic-compatible backends reject histories containing tool messages
        # when the request omits the tools parameter entirely.
        response = model_with_searchtools.invoke([sys_msg] + llm_messages)
        
        # ALWAYS add response to messages first (for tools_condition to work)
        result: dict[str, Any] = {
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
                print(f"[CONTENT_RESEARCHER] Empty response without tool calls, retrying once with recovery instruction")
                recovery_msg = HumanMessage(
                    content=(
                        "Your previous response was empty. You must respond now. "
                        "If enough candidates already exist, finalize immediately. "
                        "Otherwise call the next required tool. "
                        "Only return #NO_RESULTS# if you truly cannot continue after the allowed attempts."
                    )
                )
                response = model_with_searchtools.invoke([sys_msg] + llm_messages + [recovery_msg])
                result["messages"] = [response]

                if not response.content or response.content == "null":
                    has_retry_tool_calls = bool(getattr(response, 'tool_calls', None))
                    if has_retry_tool_calls:
                        print(f"[CONTENT_RESEARCHER] ✓ Recovery retry produced tool calls")
                    else:
                        print(f"[CONTENT_RESEARCHER] Recovery retry still empty and without tool calls, signaling no_results")
                        result["control_signal"] = "no_results"
                        return result
        
        # Check for #NO_RESULTS# signal
        if hasattr(response, 'content') and isinstance(response.content, str):
            if "#NO_RESULTS#" in response.content or "#no_results#" in response.content.lower():
                print("[CONTENT_RESEARCHER] LLM sent #NO_RESULTS# signal after 3 attempts")
                result["control_signal"] = "no_results"
                return result

        # Track only final presented titles (not raw tool candidates) for blacklist usage.
        # This runs when the assistant returns normal text output.
        has_tool_calls = bool(getattr(response, "tool_calls", None))
        if not has_tool_calls and hasattr(response, "content") and isinstance(response.content, str):
            presented_titles = _extract_presented_titles_from_text(response.content)
            if presented_titles:
                existing_found = state.get("found_titles", [])
                existing_keys = {str(title).casefold() for title in existing_found}
                merged_titles = existing_found.copy()
                for title in presented_titles:
                    key = title.casefold()
                    if key not in existing_keys:
                        merged_titles.append(title)
                        existing_keys.add(key)
                result["found_titles"] = merged_titles
                print(f"[CONTENT_RESEARCHER] Added presented titles to blacklist: {', '.join(presented_titles)}")
        
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
                        print(f"[TOOL_NODE] Tracked filter results: {found_count} titles found")
                        print("[TOOL_NODE] Blacklist unchanged (only final presented titles are blacklisted)")
                        
                        # Update result with filter stats only.
                        # Do NOT write available tool candidates into found_titles here,
                        # otherwise they get blacklisted before being presented.
                        result.update({
                            "last_filter_results": filter_results
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
    model_analyst = initialize_analyst_model()
    model_researcher = initialize_research_model()
    
    workflow = StateGraph(AgentState)

    # Create nodes with model closure (no re-initialization)
    workflow.add_node("scope_guard", create_scope_guard(model_analyst))
    workflow.add_node("out_of_scope_response", out_of_scope_response)
    workflow.add_node("interest_analyst", create_interest_analyst(model_analyst))
    workflow.add_node("analyst_output_validator", analyst_output_validator)
    workflow.add_node("content_researcher", create_content_researcher(model_researcher))
    workflow.add_node("tools", tool_node_with_state_tracking)
    workflow.add_node("result_validator", result_validator)
    workflow.add_node("fallback_response", fallback_response)
    
    # Entry Point definieren
    workflow.set_entry_point("scope_guard")

    # Scope Guard → Interest Analyst oder Out-of-scope response oder END (unclear)
    workflow.add_conditional_edges(
        "scope_guard",
        lambda state: state.get("next_agent", "interest_analyst"),
        {
            "interest_analyst": "interest_analyst",
            "out_of_scope_response": "out_of_scope_response",
            "__END__": END,
        }
    )

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

    # Out-of-scope response → END
    workflow.add_edge("out_of_scope_response", END)

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


