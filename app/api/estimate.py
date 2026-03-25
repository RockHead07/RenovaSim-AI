# ---------------------------------------------------------------------------
# estimate.py
# API route — thin layer, no business logic.
# ---------------------------------------------------------------------------

import logging
from fastapi import APIRouter, HTTPException
from app.schemas.estimate_schema import EstimateRequest, EstimateResponse
from app.services.estimator import calculate_estimate

logger = logging.getLogger(__name__)
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
    try:
        logger.info(f"Estimate request — job_type={request.job_type}, area={request.area}")
        result = calculate_estimate(request)
        logger.info(f"Estimate result — total_cost={result.total_cost}")
        return result
    except ValueError as e:
        logger.warning(f"Invalid estimate request: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during estimation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Estimation failed unexpectedly.")