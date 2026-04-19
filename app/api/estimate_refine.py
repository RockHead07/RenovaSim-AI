# ---------------------------------------------------------------------------
# estimate_refine.py
# PATCH /api/v2/estimate/refine — update assumptions without starting over.
# ---------------------------------------------------------------------------

import logging
from fastapi import APIRouter, HTTPException
from app.schemas.estimate_v2_schema import RefineRequest, RefineResponse
from app.services.refiner import refine_estimate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.patch(
    "/v2/estimate/refine",
    response_model=RefineResponse,
    summary="Refine a previous estimate with corrections",
    description=(
        "Submit corrections to a previous estimate. "
        "The system will update assumptions and recalculate without starting from scratch. "
        "Correctable fields: area, quality, location, scope, job_type, budget."
    ),
    tags=["Estimation v2"],
)
def refine(request: RefineRequest) -> RefineResponse:
    try:
        logger.info(f"Refine request — corrections: {list(request.corrections.keys())}")
        result = refine_estimate(
            previous_response=request.previous_result,
            corrections=request.corrections,
        )
        return RefineResponse(**result)
    except Exception as e:
        logger.error(f"Refine error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Refinement failed unexpectedly.")