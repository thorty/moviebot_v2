import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))


from langchain_core.messages import HumanMessage, AIMessageChunk
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
    answer = cl.Message(content="")
    await answer.send()

    config: RunnableConfig = {
        "configurable": {"thread_id": cl.context.session.thread_id}
    }
    
    # Input für den Graph vorbereiten
    graph_input = {
        "messages": [HumanMessage(content=message.content)],
        #"userstreamingproviders": ["Netflix", "Disney Plus", "Amazon Prime", "Hulu", "HBO Max", "Apple TV+", "MagentaTV", "Joyn", "Sky Ticket"]
        "userstreamingproviders": ["Disney Plus", "Amazon Prime", "Apple TV+"]
    }
            

    for msg, _ in app.stream(                
        graph_input, 
        config,
        stream_mode="messages",
    ):
        if isinstance(msg, AIMessageChunk):
            answer.content += msg.content  # type: ignore
            await answer.update()