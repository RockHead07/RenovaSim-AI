# ---------------------------------------------------------------------------
# middleware/auth.py
# API key authentication dependency.
# Enabled only when API_KEY_ENABLED=True in .env
# ---------------------------------------------------------------------------

import logging
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.config import settings

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> None:
    """
    FastAPI dependency — validates X-API-Key header.
    Skipped entirely if API_KEY_ENABLED=False.
    """
    if not settings.API_KEY_ENABLED:
        return  # Auth disabled — allow all requests

    if not api_key:
        logger.warning("Request missing X-API-Key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header.",
        )

    if api_key != settings.API_KEY:
        logger.warning("Request with invalid API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )