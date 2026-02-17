from datetime import datetime, timezone
from typing import Any

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from backend.utils.helper import verify_and_decode_supabase_jwt
from backend.utils.setupenv import load_environment


app = FastAPI(title="Moviebot API", version="0.1.0")
auth_scheme = HTTPBearer(auto_error=False)
graph_app: Any | None = None


class ChatRequest(BaseModel):
    message: str
    userstreamingproviders: list[str] = ["Disney Plus"]
    paymenttypes: list[str] = ["free", "flatrate", "rent", "buy"]
    thread_id: str | None = None


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
        return verify_and_decode_supabase_jwt(token)
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


def invoke_user_chat(user_id: str, payload: ChatRequest) -> str:
    app_graph = get_graph_app()
    graph_input = {
        "messages": [HumanMessage(content=payload.message)],
        "user_id": user_id,
        "userstreamingproviders": payload.userstreamingproviders,
        "paymenttypes": payload.paymenttypes,
        "found_titles": [],
        "analystresult": "",
    }
    config = {
        "configurable": {"thread_id": payload.thread_id or f"user:{user_id}"},
        "recursion_limit": 50,
    }

    result = app_graph.invoke(graph_input, config)
    final_messages = result.get("messages", [])
    for msg in reversed(final_messages):
        if hasattr(msg, "type") and msg.type == "ai" and getattr(msg, "content", ""):
            return msg.content
    return ""


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "moviebot-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/v1/chat")
def chat(payload: ChatRequest, user_claims: dict = Depends(require_user_context)) -> dict[str, str]:
    user_id = str(user_claims.get("sub", ""))
    reply = invoke_user_chat(user_id=user_id, payload=payload)
    return {
        "status": "accepted",
        "user_id": user_id,
        "reply": reply,
    }
