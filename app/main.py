# ---------------------------------------------------------------------------
# main.py
# Application entry point — initialise FastAPI and register routers.
# ---------------------------------------------------------------------------

from fastapi import FastAPI
from app.api.estimate import router as estimate_router

app = FastAPI(
    title="RenovaSim AI",
    description=(
        "MVP estimation API for renovation costs.\n\n"
        "Calculates material cost, labour cost, and total cost "
        "based on job type and area (m²)."
    ),
    version="0.1.0",
    contact={
        "name": "RenovaSim AI",
    },
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(estimate_router, prefix="/api")
