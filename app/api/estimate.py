import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session
from app.schemas.estimate_schema import EstimateRequest, EstimateResponse
from app.services.estimator import calculate_estimate
from app.db.session import get_session

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/estimate",
    response_model=EstimateResponse,
    summary="Calculate renovation cost estimate",
    tags=["Estimation"],
)
def estimate(
    request: EstimateRequest,
    session: Session = Depends(get_session),
) -> EstimateResponse:
    try:
        logger.info(f"Estimate request — job_type={request.job_type}, area={request.area}")
        result = calculate_estimate(request, session)
        logger.info(f"Estimate result — total_cost={result.total_cost}")
        return result
    except ValueError as e:
        logger.warning(f"Invalid estimate request: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during estimation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Estimation failed unexpectedly.")