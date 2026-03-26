# ---------------------------------------------------------------------------
# main.py
# Application entry point — initialise FastAPI, logging, DB, and routers.
# ---------------------------------------------------------------------------

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.api.estimate import router as estimate_router
from app.api.job_types import router as job_types_router
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
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "MVP estimation API for renovation costs.\n\n"
        "Calculates material cost, labour cost, and total cost "
        "based on job type and area (m²)."
    ),
    debug=settings.APP_DEBUG,
)

# ---------------------------------------------------------------------------
# Startup — create tables and seed default data
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    logger.info("Initialising database...")
    init_db()
    with Session(engine) as session:
        seed_job_types(session)
    logger.info("Database ready.")

# ---------------------------------------------------------------------------
# Custom 422 handler — clean, consistent validation error shape
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
app.include_router(estimate_router, prefix="/api")
app.include_router(job_types_router, prefix="/api")

logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started [{settings.APP_ENV}]")