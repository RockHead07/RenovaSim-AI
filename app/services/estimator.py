# ---------------------------------------------------------------------------
# estimator.py
# Pure business logic — no FastAPI / HTTP concerns here.
# ---------------------------------------------------------------------------

import logging
from app.data.cost_data import COST_TABLE
from app.schemas.estimate_schema import EstimateRequest, EstimateResponse

logger = logging.getLogger(__name__)


def calculate_estimate(request: EstimateRequest) -> EstimateResponse:
    """
    Calculate material cost, labour cost, and total cost for a renovation job.

    Formula
    -------
    material_cost = area × unit_material_price
    labor_cost    = area × unit_labor_price
    total_cost    = material_cost + labor_cost
    """
    logger.debug(f"Calculating estimate for job_type={request.job_type}, area={request.area}")

    unit_costs = COST_TABLE[request.job_type]  # key already validated in schema

    material_cost = request.area * unit_costs["material"]
    labor_cost    = request.area * unit_costs["labor"]
    total_cost    = material_cost + labor_cost

    logger.debug(
        f"Costs — material={material_cost}, labor={labor_cost}, total={total_cost}"
    )

    return EstimateResponse(
        job_type=request.job_type,
        area=request.area,
        material_cost=material_cost,
        labor_cost=labor_cost,
        total_cost=total_cost,
    )