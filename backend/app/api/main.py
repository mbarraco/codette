from fastapi import FastAPI

from app.core.logging import setup_logging

setup_logging()

app = FastAPI(title="Codette API", version="0.1.0")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
