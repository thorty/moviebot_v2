#what it is

beim MVP gefixte bugs für langgraph:

# kompletter context in scope-guard:
```python
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
```

##  tokenlimit 
for gpt 4.1

## change intrest_analyst prompt 
    short and clear