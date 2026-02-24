from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage
from langgraph.managed.is_last_step import RemainingSteps

def add_message(existing_messages: list, new_messages: list) -> list:
    """
    Custom message handler with filtering for control signals.
    Completely removes messages containing #FINISHED# or #NO_RESULTS# to prevent
    them from appearing in the frontend.
    """
    result_messages = existing_messages.copy()
    
    for msg in new_messages:
        # Filter control signals: skip messages with #FINISHED# or #NO_RESULTS#
        if hasattr(msg, 'content') and isinstance(msg.content, str):
            content_lower = msg.content.lower()
            if "#finished#" in content_lower or "#no_results#" in content_lower:
                # Skip this message completely - don't add to result
                print(f"[STATE] Filtered control message: {msg.content[:50]}...")
                continue
        
        # Add normal messages
        result_messages.append(msg)
    
    return result_messages

class AgentState(TypedDict):
    # Authenticated user id from JWT (sub claim)
    user_id: str
    # Active conversation id for the current user
    conversation_id: str
    # User's streaming providers
    userstreamingproviders: list[str]
    # User's payment types (e.g., free, rent)
    paymenttypes: list[str]
    # Messages for conversation history
    messages: Annotated[list[AnyMessage], add_message]
    # The result from the interest analyst (search query summary)
    analystresult: str
    # Flag to indicate which agent to route to next
    next_agent: str
    
    # Internal control signals (not visible in messages)
    control_signal: str  # "" | "no_results" - for inter-node communication
    
    # Validation and results tracking
    last_filter_results: dict  # Results from filter_streaming_providers tool
    validation_status: str  # "success" | "max_retries" | "pending"
    found_titles: list[str]  # Blacklist: Only titles already presented to the user (prevents duplicate recommendations)

    # Scope guard routing (movie/series domain check)
    scope_status: str  # "in_scope" | "out_of_scope" | "unclear"
    scope_reason: str
    
    # remaining_steps: Used by LangGraph to track the number of allowed steps 
    # to prevent infinite loops in cyclic graphs.
    remaining_steps: RemainingSteps