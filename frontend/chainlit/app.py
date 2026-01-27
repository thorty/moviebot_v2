import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))


from langchain_core.messages import HumanMessage
from langchain_core.runnables.config import RunnableConfig
from langchain_openai import ChatOpenAI

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
import chainlit as cl
from dotenv import load_dotenv

from backend.graph import create_graph
from backend.utils.setupenv import enable_langsmith


load_dotenv()

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

app = create_chatbot()


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if (username, password) == ("admin", "admin"):
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None


@cl.on_chat_resume
async def on_chat_resume(thread):
    pass


@cl.on_message
async def main(message: cl.Message):
    # Show loading message
    loading_msg = cl.Message(content="🔍 Suche nach passenden Empfehlungen...")
    await loading_msg.send()

    config: RunnableConfig = {
        "configurable": {"thread_id": cl.context.session.thread_id}
    }
    
    # Input für den Graph vorbereiten
    graph_input = {
        "messages": [HumanMessage(content=message.content)],
        "userstreamingproviders": ["Disney Plus"]
    }
    
    # Use invoke() to wait for complete, filtered result
    # This ensures all State processing (add_message filtering) is applied
    result = await cl.make_async(app.invoke)(graph_input, config)
    
    # Remove loading message
    await loading_msg.remove()
    
    # Extract final messages from result (already filtered by add_message)
    final_messages = result.get("messages", [])
    
    # Get the last AI message(s) after state processing
    response_content = ""
    for msg in reversed(final_messages):
        if hasattr(msg, 'type') and msg.type == 'ai':
            if hasattr(msg, 'content') and msg.content:
                # Content is already filtered by add_message in State
                response_content = msg.content
                break
    
    # Send final response
    if response_content:
        answer = cl.Message(content=response_content)
        await answer.send()
    else:
        # Fallback if no AI message found
        answer = cl.Message(content="Entschuldigung, es gab ein Problem bei der Verarbeitung.")
        await answer.send()
    
if __name__ == "__main__":
    from chainlit.cli import run_chainlit
    run_chainlit(__file__)