from datetime import datetime, timezone
import logging
import os
import json
import time
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
from backend.persistence.watchlist_items import (
    delete_watchlist_item,
    list_watchlist_items,
    upsert_watchlist_item,
)
from backend.recommendations import (
    VALID_RECOMMENDATION_MEDIA_TYPES,
    extract_recommendations_from_reply,
    normalize_title_key,
)
from backend.utils.helper import choose_streaming_providers, split_streaming_and_mediatheken, verify_and_decode_supabase_jwt
from backend.utils.setupenv import load_environment


app = FastAPI(title="Moviebot API", version="0.1.0")
auth_scheme = HTTPBearer(auto_error=False)
graph_app: Any | None = None
logger = logging.getLogger(__name__)

DEFAULT_STREAMING_PROVIDERS = ["Netflix", "Disney Plus", "Amazon", "WOW", "Paramount Plus", "Apple TV", "Magenta TV"]
DEFAULT_PAYMENT_TYPES = ["free", "rent"]

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
    include_mediatheken: bool = False
    thread_id: str | None = None


class RecommendationCandidate(BaseModel):
    title: str
    media_type: str
    description: str
    cover_url: str | None = None
    rating: float | None = None
    rating_source: str | None = None
    streaming_providers: list[str]


class ChatResponse(BaseModel):
    status: str
    user_id: str
    conversation_id: str
    reply: str
    recommendations: list[RecommendationCandidate] = []


class NewChatResponse(BaseModel):
    status: str
    user_id: str
    conversation_id: str


class UserFilterPreferencesPayload(BaseModel):
    source: str
    providers: list[str]
    paymenttypes: list[str]
    include_mediatheken: bool = False


class UserFilterPreferencesResponse(BaseModel):
    status: str
    user_id: str
    source: str
    providers: list[str]
    paymenttypes: list[str]
    include_mediatheken: bool = False


class WatchlistItemPayload(BaseModel):
    title: str
    media_type: str
    description: str = ""
    cover_url: str | None = None
    rating: float | None = None
    rating_source: str | None = None
    streaming_providers: list[str] = []


class WatchlistItem(BaseModel):
    id: str
    user_id: str
    title: str
    media_type: str
    description: str
    cover_url: str | None = None
    rating: float | None = None
    rating_source: str | None = None
    streaming_providers: list[str]
    created_at: str | None = None
    updated_at: str | None = None


class WatchlistItemsResponse(BaseModel):
    status: str
    user_id: str
    items: list[WatchlistItem]


class WatchlistItemResponse(BaseModel):
    status: str
    user_id: str
    item: WatchlistItem


class WatchlistDeleteResponse(BaseModel):
    status: str
    user_id: str
    item_id: str


PROVIDER_QUOTA_ERROR_MESSAGE = (
    "Das KI-Modell-Limit ist gerade erreicht. Bitte warte kurz und versuche es dann erneut."
)
PROVIDER_TEMPORARY_ERROR_MESSAGE = (
    "sorry ich habe leider gerade technische Probleme, versuch es doch später nochmal"
)


class ChatInvocationResult(str):
    """String-compatible chat reply with structured recommendation metadata."""

    recommendations: list[dict[str, Any]]

    def __new__(cls, reply: str, recommendations: list[dict[str, Any]] | None = None):
        value = str.__new__(cls, reply)
        value.recommendations = recommendations or []
        return value


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


def is_provider_quota_error(exc: Exception) -> bool:
    error_text = f"{exc.__class__.__module__} {exc.__class__.__name__} {exc}"
    lowered = error_text.lower()
    return (
        ("429" in error_text or "ratelimiterror" in lowered or "rate limit" in lowered)
        and (
            "resource_exhausted" in lowered
            or "quota" in lowered
            or "rate-limit" in lowered
            or "rate limit" in lowered
            or "too many requests" in lowered
        )
    )


def is_provider_temporary_error(exc: Exception) -> bool:
    error_text = f"{exc.__class__.__module__} {exc.__class__.__name__} {exc}"
    lowered = error_text.lower()
    temporary_signals = (
        "500",
        "502",
        "503",
        "504",
        "apitimeouterror",
        "apiconnectionerror",
        "internalservererror",
        "service unavailable",
        "timeout",
        "timed out",
        "deadline_exceeded",
        "connection error",
    )
    provider_signals = (
        "openai",
        "langchain_openai",
        "llm",
        "model",
        "responses",
    )

    return any(signal in lowered for signal in temporary_signals) and any(
        signal in lowered for signal in provider_signals
    )


def invoke_user_chat(user_id: str, conversation_id: str, payload: ChatRequest) -> str:
    app_graph = get_graph_app()
    start_time = time.perf_counter()

    normalized_paymenttypes = [payment.strip().lower() for payment in payload.paymenttypes if payment and payment.strip()]
    normalized_paymenttypes = ["free" if payment == "flatrate" else payment for payment in normalized_paymenttypes]
    normalized_paymenttypes = list(dict.fromkeys(normalized_paymenttypes))
    if not normalized_paymenttypes:
        normalized_paymenttypes = ["free", "rent"]

    normalized_user_providers = [provider.strip() for provider in payload.userstreamingproviders if provider and provider.strip()]
    streaming_provider_candidates, legacy_include_mediatheken = split_streaming_and_mediatheken(normalized_user_providers)
    include_mediatheken = bool(payload.include_mediatheken) or legacy_include_mediatheken
    effective_providers = choose_streaming_providers(streaming_provider_candidates, normalized_paymenttypes)
    if not effective_providers:
        effective_providers = streaming_provider_candidates
    if include_mediatheken and not effective_providers:
        normalized_paymenttypes = ["free"]

    graph_input = {
        "messages": [HumanMessage(content=payload.message)],
        "user_id": user_id,
        "conversation_id": conversation_id,
        "userstreamingproviders": effective_providers,
        "paymenttypes": normalized_paymenttypes,
        "include_mediatheken": include_mediatheken,
    }
    config = {
        "configurable": {"thread_id": payload.thread_id or f"conversation:{conversation_id}"},
        "recursion_limit": 50,
    }

    logger.info(
        "[CHAT_GRAPH_START] user_id=%s conversation_id=%s message_chars=%s providers=%s paymenttypes=%s include_mediatheken=%s thread_id=%s",
        user_id,
        conversation_id,
        len(payload.message or ""),
        effective_providers,
        normalized_paymenttypes,
        include_mediatheken,
        config["configurable"]["thread_id"],
    )

    try:
        result = app_graph.invoke(graph_input, config)
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        if is_provider_temporary_error(exc):
            logger.warning(
                "[CHAT_GRAPH_TEMPORARY_PROVIDER_ERROR] user_id=%s conversation_id=%s duration_ms=%.1f error_type=%s",
                user_id,
                conversation_id,
                duration_ms,
                exc.__class__.__name__,
            )
            return ChatInvocationResult(PROVIDER_TEMPORARY_ERROR_MESSAGE, [])

        logger.exception(
            "[CHAT_GRAPH_ERROR] user_id=%s conversation_id=%s duration_ms=%.1f error_type=%s",
            user_id,
            conversation_id,
            duration_ms,
            exc.__class__.__name__,
        )
        raise

    final_messages = result.get("messages", [])
    reply = ""
    for msg in reversed(final_messages):
        if hasattr(msg, "type") and msg.type == "ai" and getattr(msg, "content", ""):
            reply = stringify_message_content(msg.content)
            break

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "[CHAT_GRAPH_END] user_id=%s conversation_id=%s duration_ms=%.1f final_messages=%s reply_chars=%s",
        user_id,
        conversation_id,
        duration_ms,
        len(final_messages),
        len(reply),
    )

    recommendations = extract_recommendations_from_reply(
        reply,
        filter_results=result.get("last_filter_results", {}),
        mediatheken_results=result.get("last_mediatheken_results", {}),
    )

    return ChatInvocationResult(reply, recommendations)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "moviebot-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _normalize_filter_payload(payload: UserFilterPreferencesPayload) -> tuple[str, list[str], list[str], bool]:
    source = payload.source.strip().lower()
    if source not in {"streaming", "mediathek"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid filter source",
        )

    raw_providers = [provider.strip() for provider in payload.providers if provider and provider.strip()]
    providers, legacy_include_mediatheken = split_streaming_and_mediatheken(raw_providers)
    include_mediatheken = bool(payload.include_mediatheken) or legacy_include_mediatheken or source == "mediathek"
    paymenttypes = [payment.strip().lower() for payment in payload.paymenttypes if payment and payment.strip()]

    if source == "mediathek":
        return source, [], ["free"], True

    if not providers and not include_mediatheken:
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
        normalized_paymenttypes = ["free"] if include_mediatheken and not providers else ["free", "rent"]

    return source, providers, normalized_paymenttypes, include_mediatheken


def _normalize_watchlist_payload(
    payload: WatchlistItemPayload,
) -> tuple[str, str, str, str, str | None, float | None, str | None, list[str]]:
    title = payload.title.strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Watchlist title is required",
        )

    media_type = payload.media_type.strip().lower()
    if media_type not in VALID_RECOMMENDATION_MEDIA_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Invalid watchlist media type",
        )

    rating = payload.rating
    if rating is not None and (rating < 0 or rating > 10):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Watchlist rating must be between 0 and 10",
        )

    streaming_providers = []
    seen_providers: set[str] = set()
    for provider in payload.streaming_providers:
        provider_name = provider.strip()
        provider_key = provider_name.casefold()
        if not provider_name or provider_key in {"mediathek", "mediatheken"} or provider_key in seen_providers:
            continue
        streaming_providers.append(provider_name)
        seen_providers.add(provider_key)

    if not streaming_providers:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="At least one watchlist provider is required",
        )

    description = payload.description.strip()
    cover_url = payload.cover_url.strip() if payload.cover_url else None
    rating_source = payload.rating_source.strip() if payload.rating_source else None
    if rating is None:
        rating_source = None

    return (
        title,
        normalize_title_key(title),
        media_type,
        description,
        cover_url,
        rating,
        rating_source,
        streaming_providers,
    )


def _watchlist_item_from_row(row: dict[str, Any]) -> WatchlistItem:
    return WatchlistItem(
        id=str(row.get("id", "")),
        user_id=str(row.get("user_id", "")),
        title=str(row.get("title", "")),
        media_type=str(row.get("media_type", "")),
        description=str(row.get("description", "") or ""),
        cover_url=row.get("cover_url"),
        rating=row.get("rating"),
        rating_source=row.get("rating_source"),
        streaming_providers=list(row.get("streaming_providers", []) or []),
        created_at=row.get("created_at"),
        updated_at=row.get("updated_at"),
    )


@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, user_claims: dict = Depends(require_user_context)) -> ChatResponse:
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

    try:
        reply_result = invoke_user_chat(user_id=user_id, conversation_id=conversation_id, payload=payload)
    except Exception as exc:
        if is_provider_quota_error(exc):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=PROVIDER_QUOTA_ERROR_MESSAGE,
            ) from exc
        raise

    reply = str(reply_result)
    recommendations = getattr(reply_result, "recommendations", []) or []

    append_message_log(
        conversation_id=conversation_id,
        user_id=user_id,
        access_token=access_token,
        role="assistant",
        content=reply or "(empty)",
        metadata={"source": "api"},
    )

    return ChatResponse(
        status="accepted",
        user_id=user_id,
        conversation_id=conversation_id,
        reply=reply,
        recommendations=[RecommendationCandidate(**recommendation) for recommendation in recommendations],
    )


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
            providers=DEFAULT_STREAMING_PROVIDERS,
            paymenttypes=DEFAULT_PAYMENT_TYPES,
            include_mediatheken=False,
        )

    source = str(preferences.get("source", "streaming"))
    providers = list(preferences.get("providers", []) or [])
    paymenttypes = list(preferences.get("payment_types", []) or [])
    include_mediatheken = bool(preferences.get("include_mediatheken", source == "mediathek"))

    if source == "streaming" and not providers and not include_mediatheken:
        providers = DEFAULT_STREAMING_PROVIDERS

    return UserFilterPreferencesResponse(
        status="ok",
        user_id=user_id,
        source=source,
        providers=providers,
        paymenttypes=paymenttypes or DEFAULT_PAYMENT_TYPES,
        include_mediatheken=include_mediatheken,
    )


@app.put("/api/v1/user/filters", response_model=UserFilterPreferencesResponse)
def save_user_filters(
    payload: UserFilterPreferencesPayload,
    user_claims: dict = Depends(require_user_context),
) -> UserFilterPreferencesResponse:
    user_id = str(user_claims.get("sub", ""))
    access_token = str(user_claims.get("_access_token", ""))

    source, providers, paymenttypes, include_mediatheken = _normalize_filter_payload(payload)
    row = upsert_user_filter_preferences(
        user_id=user_id,
        access_token=access_token,
        source=source,
        providers=providers,
        payment_types=paymenttypes,
        include_mediatheken=include_mediatheken,
    )

    return UserFilterPreferencesResponse(
        status="ok",
        user_id=user_id,
        source=str(row.get("source", source)),
        providers=list(row.get("providers", providers) or providers),
        paymenttypes=list(row.get("payment_types", paymenttypes) or paymenttypes),
        include_mediatheken=bool(row.get("include_mediatheken", include_mediatheken)),
    )


@app.get("/api/v1/user/watchlist", response_model=WatchlistItemsResponse)
def get_user_watchlist(user_claims: dict = Depends(require_user_context)) -> WatchlistItemsResponse:
    user_id = str(user_claims.get("sub", ""))
    access_token = str(user_claims.get("_access_token", ""))

    rows = list_watchlist_items(user_id=user_id, access_token=access_token)
    return WatchlistItemsResponse(
        status="ok",
        user_id=user_id,
        items=[_watchlist_item_from_row(row) for row in rows],
    )


@app.post("/api/v1/user/watchlist", response_model=WatchlistItemResponse)
def save_user_watchlist_item(
    payload: WatchlistItemPayload,
    user_claims: dict = Depends(require_user_context),
) -> WatchlistItemResponse:
    user_id = str(user_claims.get("sub", ""))
    access_token = str(user_claims.get("_access_token", ""))

    title, title_key, media_type, description, cover_url, rating, rating_source, streaming_providers = _normalize_watchlist_payload(payload)
    row = upsert_watchlist_item(
        user_id=user_id,
        access_token=access_token,
        title=title,
        title_key=title_key,
        media_type=media_type,
        description=description,
        cover_url=cover_url,
        rating=rating,
        rating_source=rating_source,
        streaming_providers=streaming_providers,
    )

    return WatchlistItemResponse(
        status="ok",
        user_id=user_id,
        item=_watchlist_item_from_row(row),
    )


@app.delete("/api/v1/user/watchlist/{item_id}", response_model=WatchlistDeleteResponse)
def remove_user_watchlist_item(
    item_id: str,
    user_claims: dict = Depends(require_user_context),
) -> WatchlistDeleteResponse:
    user_id = str(user_claims.get("sub", ""))
    access_token = str(user_claims.get("_access_token", ""))

    deleted_row = delete_watchlist_item(user_id=user_id, access_token=access_token, item_id=item_id)
    if deleted_row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist item not found",
        )

    return WatchlistDeleteResponse(
        status="deleted",
        user_id=user_id,
        item_id=item_id,
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
