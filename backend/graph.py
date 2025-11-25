import os
import dotenv
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition, ToolNode
from backend.states import AgentState
from backend.prompts import get_interest_analyst_prompt, get_content_researcher_prompt
from langchain_openai import AzureChatOpenAI
from backend.tools import get_all_tools
from langchain_core.messages import HumanMessage, SystemMessage, AnyMessage

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
        
        return {
            "messages": [response],  # add_message Funktion filtert das #FINISHED# automatisch heraus!
            "next_agent": "content_researcher", 
            "analystresult": cleaned_response_text.lower()
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

    default_streamingproviders = ["Netflix", "Disney Plus", "Amazon Prime", "Hulu", "HBO Max", "Apple TV+", "MagentaTV", "Joyn", "Sky Ticket"] #todo define
    userstreamingproviders = state.get("userstreamingproviders", default_streamingproviders)
    analystresult = state.get("analystresult", "The best actual movies and tv-shows that match the user interest") 
    sys_msg = SystemMessage(content=get_content_researcher_prompt(userstreamingproviders, analystresult))
    response = model_with_searchtools.invoke([sys_msg] + state["messages"])          
    return {"messages": [response] }

def create_graph():
    
    dotenv.load_dotenv(dotenv_path=".env", override=True)
    
    workflow = StateGraph(AgentState)

    tools = get_all_tools()

    # Nodes hinzufügen
    workflow.add_node("interest_analyst", interest_analyst)
    workflow.add_node("content_researcher", content_researcher)
    workflow.add_node("tools", ToolNode(tools))
    
    # Entry Point definieren
    workflow.set_entry_point("interest_analyst")

    workflow.add_conditional_edges(
        "content_researcher",
        # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
        # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
        tools_condition,
    )    
    workflow.add_edge("tools", "content_researcher") #back to assistant node    

    # Kanten für die bedingte Weiterleitung vom Interest Analyst
    workflow.add_conditional_edges(
        "interest_analyst",
        lambda state: state.get("next_agent", "__END__"),
        {
            "content_researcher": "content_researcher",
            "__END__": END
        }
    )

    # Content Researcher beendet den Graph
    workflow.add_edge("content_researcher", END)

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


