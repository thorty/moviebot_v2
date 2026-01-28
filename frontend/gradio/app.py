import os
import sys
import uuid
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

import gradio as gr
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

from backend.graph import create_graph
from backend.utils.setupenv import enable_langsmith
from backend.utils.tmdb.common import Provider


load_dotenv()

# Initialize backend
enable_langsmith()
graph = create_graph()

# Available streaming providers
AVAILABLE_PROVIDERS = [provider.value for provider in Provider]

# Global state to store last result for state persistence
last_result_store = {}


def clear_thread_state(thread_id):
    """Clear stored state for a thread when chat is reset."""
    if thread_id in last_result_store:
        del last_result_store[thread_id]
    return None


def chat_with_bot(message, history, selected_providers, thread_id):
    """
    Handle chat interaction with the MovieBot.
    
    Args:
        message: User's input message
        history: Chat history in Gradio format [(user_msg, bot_msg), ...]
        selected_providers: List of selected streaming providers
        thread_id: Unique session ID
    
    Returns:
        Updated history with new bot response
    """
    if not message or not message.strip():
        return history
    
    # Use selected providers or default to Disney Plus
    providers = selected_providers if selected_providers else AVAILABLE_PROVIDERS
    
    # Retrieve previous state for persistence
    previous_result = last_result_store.get(thread_id, {})
    
    # Prepare input for LangGraph with state persistence
    graph_input = {
        "messages": [HumanMessage(content=message)],
        "userstreamingproviders": providers,
        # Persist important state fields between requests
        "found_titles": previous_result.get("found_titles", []),
        "analystresult": previous_result.get("analystresult", "")
    }
    
    # Configure with thread_id for session persistence
    config = {
        "configurable": {"thread_id": thread_id}
    }
    
    print(f"[DEBUG] Using thread_id: {thread_id}")
    print(f"[DEBUG] Selected providers: {providers}")
    print(f"[DEBUG] Persisted found_titles (blacklist): {len(graph_input['found_titles'])} titles")
    
    try:
        # Invoke the graph
        result = graph.invoke(graph_input, config)
        
        # Store result for next request (state persistence)
        last_result_store[thread_id] = result
        
        # Extract AI response from result
        final_messages = result.get("messages", [])
        response_content = ""
        
        for msg in reversed(final_messages):
            if hasattr(msg, 'type') and msg.type == 'ai':
                if hasattr(msg, 'content') and msg.content:
                    response_content = msg.content
                    break
        
        if not response_content:
            response_content = "Entschuldigung, es gab ein Problem bei der Verarbeitung."
        
    except Exception as e:
        response_content = f"Fehler: {str(e)}"
    
    return response_content


def create_ui():
    """Create and configure the Gradio interface."""
    
    with gr.Blocks(
        title="MovieBot - Film & Serien Empfehlungen"
    ) as demo:
        # Store thread_id in session state
        thread_id_state = gr.State(value=lambda: str(uuid.uuid4()))
        
        gr.Markdown(
            """
            # 🎬 MovieBot - Dein Film & Serien Assistent
            Frage mich nach Empfehlungen für Filme und Serien!
            """
        )
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ Einstellungen")
                
                provider_selector = gr.CheckboxGroup(
                    choices=AVAILABLE_PROVIDERS,
                    value=["Disney Plus"],
                    label="Streaming-Anbieter",
                    info="Wähle deine verfügbaren Streaming-Dienste"
                )
                
                gr.Markdown(
                    """
                    ### 💡 Beispiel-Anfragen:
                    - "Ich suche spannende Thriller"
                    - "ich will gerne spnnende fantasy abenteuer sehen für erwachsene. aber keinen der klassiker wie harry potter oder herr der ringe. eher geheimtips. gerne mit humor"
                    - "Welche Science-Fiction Filme gibt es?"
                    """
                )
            
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Chat",
                    height=500
                )
                
                msg = gr.Textbox(
                    label="Deine Nachricht",
                    placeholder="Schreib deine Frage hier...",
                    lines=2
                )
                
                with gr.Row():
                    submit_btn = gr.Button("Senden", variant="primary")
                    clear_btn = gr.Button("Chat löschen")
        
        # Event handlers
        def respond(message, history, providers, thread_id):
            bot_response = chat_with_bot(message, history, providers, thread_id)
            # Gradio expects messages in dict format with 'role' and 'content'
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": bot_response})
            return "", history
        
        submit_btn.click(
            respond,
            inputs=[msg, chatbot, provider_selector, thread_id_state],
            outputs=[msg, chatbot]
        )
        
        msg.submit(
            respond,
            inputs=[msg, chatbot, provider_selector, thread_id_state],
            outputs=[msg, chatbot]
        )
        
        clear_btn.click(
            lambda thread_id: (None, str(uuid.uuid4()), clear_thread_state(thread_id)),
            inputs=[thread_id_state],
            outputs=[chatbot, thread_id_state]
        )
        
        gr.Markdown(
            """
            ---
            **Hinweis:** Der Bot nutzt KI, um personalisierte Empfehlungen zu finden. 
            Die Verfügbarkeit der Inhalte wird in Echtzeit geprüft.
            """
        )
    
    return demo


if __name__ == "__main__":
    print("🤖 MovieBot wird gestartet...")
    print("✅ Backend erfolgreich initialisiert!")
    print("💡 Öffne die App in deinem Browser")
    print("🔚 Zum Beenden: Strg+C\n")
    
    demo = create_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        auth=("admin", "admin")  # Optional: Basic Auth entfernen wenn nicht benötigt
    )
