# ---------------------------------------------------------------------------
# health.py
# GET /health — system health check endpoint.
# Used by Docker, monitoring tools, and deployment pipelines.
# ---------------------------------------------------------------------------

import logging
import httpx
from fastapi import APIRouter
from sqlmodel import Session, text
from app.config import settings
from app.db.session import engine

logger = logging.getLogger(__name__)
router = APIRouter(tags=["System"])


def _check_database() -> str:
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        return "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return "error"


def _check_ollama() -> str:
    try:
        with httpx.Client(timeout=3.0) as client:
            response = client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                return "ok"
        return "error"
    except Exception:
        return "unavailable"


@router.get(
    "/health",
    summary="System health check",
    description="Returns the health status of the API, database, and Ollama.",
)
def health_check() -> dict:
    db_status = _check_database()
    ollama_status = _check_ollama()

    overall = "ok" if db_status == "ok" else "degraded"

    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "services": {
            "database": db_status,
            "ollama": ollama_status,
        },
    }