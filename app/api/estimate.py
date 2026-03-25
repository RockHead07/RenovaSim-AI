# ---------------------------------------------------------------------------
# estimate.py
# API route — thin layer, no business logic.
# ---------------------------------------------------------------------------

from fastapi import APIRouter
from app.schemas.estimate_schema import EstimateRequest, EstimateResponse
from app.services.estimator import calculate_estimate

router = APIRouter()


@router.post(
    "/estimate",
    response_model=EstimateResponse,
    summary="Calculate renovation cost estimate",
    description=(
        "Submit a job type and area (m²) to receive a breakdown of "
        "material cost, labour cost, and total cost."
    ),
    tags=["Estimation"],
)
def estimate(request: EstimateRequest) -> EstimateResponse:
    return calculate_estimate(request)
