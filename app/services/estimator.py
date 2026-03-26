# ---------------------------------------------------------------------------
# estimator.py
# Pure business logic — reads prices from DB instead of hardcoded dict.
# ---------------------------------------------------------------------------

import logging
from sqlmodel import Session
from app.services.job_type_service import get_job_type_by_name
from app.schemas.estimate_schema import EstimateRequest, EstimateResponse

logger = logging.getLogger(__name__)


def calculate_estimate(request: EstimateRequest, session: Session) -> EstimateResponse:
    """
    Calculate material cost, labour cost, and total cost for a renovation job.

    Formula
    -------
    material_cost = area × unit_material_price
    labor_cost    = area × unit_labor_price
    total_cost    = material_cost + labor_cost
    """
    logger.debug(f"Calculating estimate for job_type={request.job_type}, area={request.area}")

    job_type = get_job_type_by_name(request.job_type, session)
    if not job_type:
        raise ValueError(
            f"'{request.job_type}' is not a supported job type."
        )

    material_cost = request.area * job_type.material_price
    labor_cost    = request.area * job_type.labor_price
    total_cost    = material_cost + labor_cost

    logger.debug(f"Costs — material={material_cost}, labor={labor_cost}, total={total_cost}")

    return EstimateResponse(
        job_type=request.job_type,
        area=request.area,
        material_cost=material_cost,
        labor_cost=labor_cost,
        total_cost=total_cost,
    )