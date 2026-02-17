from datetime import datetime, timezone

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.utils.helper import verify_and_decode_supabase_jwt
from backend.utils.setupenv import load_environment


app = FastAPI(title="Moviebot API", version="0.1.0")
auth_scheme = HTTPBearer(auto_error=False)


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


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "moviebot-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/v1/chat")
def chat(user_claims: dict = Depends(require_user_context)) -> dict[str, str]:
    return {
        "status": "accepted",
        "user_id": str(user_claims.get("sub", "")),
    }
