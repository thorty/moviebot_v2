from datetime import datetime, timezone

from fastapi import FastAPI


app = FastAPI(title="Moviebot API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "moviebot-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
