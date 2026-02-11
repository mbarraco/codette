from fastapi import FastAPI

from app.api.routes.submission import router as submission_router
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title="Codette API", version="0.1.0")
app.include_router(submission_router, prefix="/submissions", tags=["submissions"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
