"""Unit-Tests für den Scope-Guard.

Diese Tests verwenden bewusst ein Dummy-Model (statt echtem LLM), um das Routing
deterministisch zu prüfen. Für produktnahe Validierung sollte zusätzlich ein
Integrationstest mit dem echten Modell laufen.
"""

from langchain_core.messages import AIMessage, HumanMessage

from backend.graph import create_scope_guard


class DummyResponse:
    def __init__(self, content: str):
        self.content = content


class DummyModel:
    def __init__(self, label: str = "in_scope"):
        self.label = label
        self.last_messages = None

    def invoke(self, messages):
        self.last_messages = messages
        return DummyResponse(self.label)


def test_scope_guard_uses_conversation_context_not_only_last_message() -> None:
    model = DummyModel(label="in_scope")
    guard = create_scope_guard(model)

    state = {
        "messages": [
            HumanMessage(content="Empfiehl mir einen guten Thriller auf Netflix"),
            AIMessage(content="Klar, hier sind ein paar Vorschläge."),
            HumanMessage(content="Und jetzt hilf mir kurz mit Python Debugging"),
        ]
    }

    result = guard(state)

    assert result["scope_status"] == "in_scope"
    assert result["next_agent"] == "interest_analyst"


def test_scope_guard_hard_out_of_scope_only_without_media_signals() -> None:
    model = DummyModel(label="in_scope")
    guard = create_scope_guard(model)

    state = {
        "messages": [
            HumanMessage(content="Hilf mir bei einem SQL Bug"),
            AIMessage(content="Kannst du den Fehler posten?"),
            HumanMessage(content="Es geht um Python und Excel"),
        ]
    }

    result = guard(state)

    assert result["scope_status"] == "out_of_scope"
    assert result["scope_reason"] == "keyword_out_of_scope"
    assert result["next_agent"] == "out_of_scope_response"


def test_scope_guard_passes_recent_conversation_to_llm_classifier() -> None:
    model = DummyModel(label="unclear")
    guard = create_scope_guard(model)

    state = {
        "messages": [
            HumanMessage(content="Hi"),
            AIMessage(content="Hallo!"),
            HumanMessage(content="Was meinst du zu sowas allgemein?"),
        ]
    }

    result = guard(state)

    assert result["scope_status"] == "unclear"
    assert model.last_messages is not None

    classifier_context = model.last_messages[1].content
    assert "User: Hi" in classifier_context
    assert "Assistant: Hallo!" in classifier_context
    assert "User: Was meinst du zu sowas allgemein?" in classifier_context
