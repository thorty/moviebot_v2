from datetime import datetime, timezone
import os
import json
from typing import Any

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from backend.persistence.conversations import get_or_create_active_conversation, start_new_active_conversation
from backend.persistence.message_logs import append_message_log
from backend.persistence.user_filter_preferences import (
    get_user_filter_preferences,
    upsert_user_filter_preferences,
)
from backend.utils.helper import choose_streaming_providers, verify_and_decode_supabase_jwt
from backend.utils.setupenv import load_environment


app = FastAPI(title="Moviebot API", version="0.1.0")
auth_scheme = HTTPBearer(auto_error=False)
graph_app: Any | None = None

default_frontend_origin = os.getenv("FRONTEND_WEB_URL", "http://localhost:3000").rstrip("/")
allowed_origins = [
    default_frontend_origin,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",  # Frontend dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(allowed_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    userstreamingproviders: list[str] = ["Disney Plus"]
    paymenttypes: list[str] = ["flatrate", "rent"]
    thread_id: str | None = None


class NewChatResponse(BaseModel):
    status: str
    user_id: str
    conversation_id: str


class UserFilterPreferencesPayload(BaseModel):
    source: str
    providers: list[str]
    paymenttypes: list[str]


class UserFilterPreferencesResponse(BaseModel):
    status: str
    user_id: str
    source: str
    providers: list[str]
    paymenttypes: list[str]


@app.on_event("startup")
def startup_load_environment() -> None:
    load_environment()


def require_user_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    if credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme",
        )

    token = credentials.credentials
    try:
        claims = verify_and_decode_supabase_jwt(token)
        claims["_access_token"] = token
        return claims
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired token",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


def get_graph_app() -> Any:
    global graph_app
    if graph_app is None:
        from backend.graph import create_graph

        graph_app = create_graph()
    return graph_app


def reset_graph_thread_state(thread_id: str) -> None:
    global graph_app
    if graph_app is None:
        return

    checkpointer = getattr(graph_app, "checkpointer", None)
    if checkpointer is None:
        return

    delete_thread = getattr(checkpointer, "delete_thread", None)
    if delete_thread is None:
        return

    try:
        delete_thread(thread_id)
    except Exception:
        # Best effort reset: do not fail user flow if checkpoint cleanup fails.
        pass


def stringify_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
                elif item:
                    parts.append(json.dumps(item, ensure_ascii=False))
            elif item is not None:
                parts.append(str(item))
        return "\n".join(part.strip() for part in parts if part and part.strip())

    if isinstance(content, dict):
        text = content.get("text")
        if isinstance(text, str):
            return text
        return json.dumps(content, ensure_ascii=False)

    if content is None:
        return ""

    return str(content)


def invoke_user_chat(user_id: str, conversation_id: str, payload: ChatRequest) -> str:
    app_graph = get_graph_app()

    normalized_paymenttypes = [payment.strip().lower() for payment in payload.paymenttypes if payment and payment.strip()]
    normalized_paymenttypes = ["free" if payment == "flatrate" else payment for payment in normalized_paymenttypes]
    normalized_paymenttypes = list(dict.fromkeys(normalized_paymenttypes))
    if not normalized_paymenttypes:
        normalized_paymenttypes = ["free", "rent"]

    normalized_user_providers = [provider.strip() for provider in payload.userstreamingproviders if provider and provider.strip()]
    effective_providers = choose_streaming_providers(normalized_user_providers, normalized_paymenttypes)
    if not effective_providers:
        effective_providers = normalized_user_providers

    graph_input = {
        "messages": [HumanMessage(content=payload.message)],
        "user_id": user_id,
        "conversation_id": conversation_id,
        "userstreamingproviders": effective_providers,
        "paymenttypes": normalized_paymenttypes,
    }
    config = {
        "configurable": {"thread_id": payload.thread_id or f"conversation:{conversation_id}"},
        "recursion_limit": 50,
    }

    result = app_graph.invoke(graph_input, config)
    final_messages = result.get("messages", [])
    for msg in reversed(final_messages):
        if hasattr(msg, "type") and msg.type == "ai" and getattr(msg, "content", ""):
            return stringify_message_content(msg.content)
    return ""


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "moviebot-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _normalize_filter_payload(payload: UserFilterPreferencesPayload) -> tuple[str, list[str], list[str]]:
    source = payload.source.strip().lower()
    if source not in {"streaming", "mediathek"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid filter source",
        )

    providers = [provider.strip() for provider in payload.providers if provider and provider.strip()]
    paymenttypes = [payment.strip().lower() for payment in payload.paymenttypes if payment and payment.strip()]

    if source == "mediathek":
        return source, ["Mediatheken"], ["free"]

    if not providers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one provider is required for streaming source",
        )

    normalized_paymenttypes: list[str] = []
    for payment in paymenttypes:
        if payment in {"free", "flatrate"}:
            normalized_paymenttypes.append("free")
        elif payment == "rent":
            normalized_paymenttypes.append("rent")

    normalized_paymenttypes = list(dict.fromkeys(normalized_paymenttypes))
    if not normalized_paymenttypes:
        normalized_paymenttypes = ["free", "rent"]

    return source, providers, normalized_paymenttypes


@app.post("/api/v1/chat")
def chat(payload: ChatRequest, user_claims: dict = Depends(require_user_context)) -> dict[str, str]:
    user_id = str(user_claims.get("sub", ""))
    access_token = str(user_claims.get("_access_token", ""))
    conversation = get_or_create_active_conversation(user_id=user_id, access_token=access_token)
    conversation_id = str(conversation["id"])

    append_message_log(
        conversation_id=conversation_id,
        user_id=user_id,
        access_token=access_token,
        role="user",
        content=payload.message,
        metadata={"source": "api"},
    )

    reply = invoke_user_chat(user_id=user_id, conversation_id=conversation_id, payload=payload)

    append_message_log(
        conversation_id=conversation_id,
        user_id=user_id,
        access_token=access_token,
        role="assistant",
        content=reply or "(empty)",
        metadata={"source": "api"},
    )

    return {
        "status": "accepted",
        "user_id": user_id,
        "conversation_id": conversation_id,
        "reply": reply,
    }


@app.get("/api/v1/user/filters", response_model=UserFilterPreferencesResponse)
def get_user_filters(user_claims: dict = Depends(require_user_context)) -> UserFilterPreferencesResponse:
    user_id = str(user_claims.get("sub", ""))
    access_token = str(user_claims.get("_access_token", ""))

    preferences = get_user_filter_preferences(user_id=user_id, access_token=access_token)
    if preferences is None:
        return UserFilterPreferencesResponse(
            status="ok",
            user_id=user_id,
            source="streaming",
            providers=["Netflix", "Disney Plus", "Amazon", "WOW", "Paramount Plus", "Apple TV", "Magenta TV"],
            paymenttypes=["free", "rent"],
        )

    return UserFilterPreferencesResponse(
        status="ok",
        user_id=user_id,
        source=str(preferences.get("source", "streaming")),
        providers=list(preferences.get("providers", []) or []),
        paymenttypes=list(preferences.get("payment_types", []) or []),
    )


@app.put("/api/v1/user/filters", response_model=UserFilterPreferencesResponse)
def save_user_filters(
    payload: UserFilterPreferencesPayload,
    user_claims: dict = Depends(require_user_context),
) -> UserFilterPreferencesResponse:
    user_id = str(user_claims.get("sub", ""))
    access_token = str(user_claims.get("_access_token", ""))

    source, providers, paymenttypes = _normalize_filter_payload(payload)
    row = upsert_user_filter_preferences(
        user_id=user_id,
        access_token=access_token,
        source=source,
        providers=providers,
        payment_types=paymenttypes,
    )

    return UserFilterPreferencesResponse(
        status="ok",
        user_id=user_id,
        source=str(row.get("source", source)),
        providers=list(row.get("providers", providers) or providers),
        paymenttypes=list(row.get("payment_types", paymenttypes) or paymenttypes),
    )


@app.post("/api/v1/chat/new", response_model=NewChatResponse)
def start_new_chat(user_claims: dict = Depends(require_user_context)) -> NewChatResponse:
    user_id = str(user_claims.get("sub", ""))
    access_token = str(user_claims.get("_access_token", ""))
    previous_conversation = get_or_create_active_conversation(user_id=user_id, access_token=access_token)
    previous_conversation_id = str(previous_conversation["id"])

    conversation = start_new_active_conversation(user_id=user_id, access_token=access_token)
    conversation_id = str(conversation["id"])

    reset_graph_thread_state(f"conversation:{previous_conversation_id}")
    reset_graph_thread_state(f"conversation:{conversation_id}")

    return NewChatResponse(
        status="accepted",
        user_id=user_id,
        conversation_id=conversation_id,
    )
