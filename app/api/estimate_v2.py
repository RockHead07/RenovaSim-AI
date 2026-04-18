# ---------------------------------------------------------------------------
# estimate_v2.py
# POST /api/v2/estimate — full RAB estimation with assumptions & confidence.
# Thin route — all logic in services.
# ---------------------------------------------------------------------------

import logging
from fastapi import APIRouter, HTTPException
from app.schemas.estimate_v2_schema import EstimateV2Request, EstimateV2Response
from app.services.parser import parse_input
from app.services.assumption import build_assumptions
from app.services.pricing import calculate_total
from app.services.sanity import run_sanity_checks
from app.services.response_builder import build_response

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/v2/estimate",
    response_model=EstimateV2Response,
    summary="Generate full RAB estimation",
    description=(
        "Submit project details to receive a full renovation cost estimate (RAB) "
        "with range output, assumptions, confidence score, and explanation trail."
    ),
    tags=["Estimation v2"],
)
def estimate_v2(request: EstimateV2Request) -> EstimateV2Response:
    try:
        logger.info(
            f"v2 Estimate — project='{request.project_name}', "
            f"job={request.job_type}, area={request.area}, location={request.location}"
        )

        # Layer 1+2: Parse input
        parsed = parse_input(
            description=request.description or "",
            area=request.area,
            job_type=request.job_type,
            quality=request.quality,
            location=request.location,
            scope=request.scope,
        )

        # Layer 3: Build assumptions
        assumptions = build_assumptions(parsed, location=request.location)

        # Layer 4: Calculate pricing
        pricing = calculate_total(assumptions)

        # Layer 5: Sanity checks
        warnings = run_sanity_checks(
            total_min=pricing["total_min"],
            total_max=pricing["total_max"],
            area=assumptions.area.value,
            user_budget=request.budget,
        )

        # Layer 6: Build response
        response = build_response(
            project_name=request.project_name,
            assumptions=assumptions,
            pricing=pricing,
            warnings=warnings,
            conflicts=parsed.conflicts,
        )

        logger.info(
            f"v2 Estimate done — mode={response['mode']}, "
            f"confidence={response['confidence']['score']}, "
            f"range={response['total_range']['display']}"
        )

        return EstimateV2Response(**response)

    except Exception as e:
        logger.error(f"v2 Estimation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Estimation failed unexpectedly.")