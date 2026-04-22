# ---------------------------------------------------------------------------
# main.py
# Application entry point — FastAPI, logging, CORS, rate limiting, routers.
# ---------------------------------------------------------------------------

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import settings
from app.api.estimate import router as estimate_router
from app.api.job_types import router as job_types_router
from app.api.estimate_v2 import router as estimate_v2_router
from app.api.estimate_refine import router as estimate_refine_router
from app.api.estimate_ai import router as estimate_ai_router
from app.api.health import router as health_router
from app.middleware.auth import verify_api_key
from app.db.session import init_db, engine
from app.db.seeder import seed_job_types
from sqlmodel import Session

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.APP_DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialising database...")
    init_db()
    with Session(engine) as session:
        seed_job_types(session)
    logger.info("Database ready.")
    yield
    logger.info("Shutting down...")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered renovation cost estimation API (RAB generator) "
        "for the Indonesian market."
    ),
    debug=settings.APP_DEBUG,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# Custom 422 handler
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    details = []
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
        details.append({
            "field": field or "unknown",
            "message": error["msg"],
        })
    logger.warning(f"Validation error on {request.url.path}: {details}")
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Validation failed",
            "details": details,
        },
    )

# ---------------------------------------------------------------------------
# Global 500 handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An unexpected error occurred. Please try again later.",
        },
    )

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
auth = Depends(verify_api_key)

app.include_router(health_router)                                          # no auth
app.include_router(estimate_router,        prefix="/api", dependencies=[auth])
app.include_router(job_types_router,       prefix="/api", dependencies=[auth])
app.include_router(estimate_v2_router,     prefix="/api", dependencies=[auth])
app.include_router(estimate_refine_router, prefix="/api", dependencies=[auth])
app.include_router(estimate_ai_router,     prefix="/api", dependencies=[auth])

logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started [{settings.APP_ENV}]")