# ---------------------------------------------------------------------------
# estimate_ai.py
# POST /api/v2/estimate/ai — free-text estimation powered by Ollama.
# Thin route — all logic in services.
# ---------------------------------------------------------------------------

import logging
from fastapi import APIRouter, HTTPException
from app.schemas.estimate_v2_schema import EstimateAIRequest, EstimateAIResponse
from app.services.llm_extractor import extract_from_text, merge_llm_with_parsed
from app.services.parser import parse_input
from app.services.assumption import build_assumptions
from app.services.pricing import calculate_total
from app.services.sanity import run_sanity_checks
from app.services.response_builder import build_response

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/v2/estimate/ai",
    response_model=EstimateAIResponse,
    summary="AI-powered free-text renovation estimation",
    description=(
        "Submit a free-text description of your renovation project in Indonesian. "
        "The AI will extract job type, area, quality, and location automatically, "
        "then return a full RAB estimation. Falls back to rule-based if AI is unavailable."
    ),
    tags=["Estimation v2"],
)
def estimate_ai(request: EstimateAIRequest) -> EstimateAIResponse:
    try:
        logger.info(f"AI estimate — project='{request.project_name}', text='{request.text[:60]}...'")

        # Step 1: Rule-based pre-parser (fast, stable)
        parsed = parse_input(description=request.text)

        # Step 2: LLM extraction (fills what rule-based missed)
        llm_result = extract_from_text(request.text)
        llm_used = llm_result is not None

        # Step 3: Merge — explicit parsed fields win over LLM
        parsed_fields = {
            "area":     parsed.area,
            "job_type": parsed.job_type,
            "quality":  parsed.quality,
            "scope":    parsed.scope if parsed.scope != "medium" else None,
            "room":     parsed.room,
        }
        merged = merge_llm_with_parsed(llm_result, parsed_fields)

        # Step 4: Re-parse with merged data
        final_parsed = parse_input(
            description=request.text,
            area=merged.get("area_m2") or merged.get("area") or request.area_hint,
            job_type=merged.get("job_type"),
            quality=merged.get("quality"),
            location=merged.get("location"),
            scope=merged.get("scope"),
        )

        # If room detected by LLM but not rule-based, set it
        if not final_parsed.room and merged.get("room"):
            final_parsed.room = merged.get("room")

        # Step 5: Extract multi-job types from LLM result
        explicit_job_types = merged.get("job_types", [])
        if not explicit_job_types:
            single = merged.get("job_type")
            explicit_job_types = [single] if single else []
        # Deduplicate
        explicit_job_types = list(dict.fromkeys(jt for jt in explicit_job_types if jt))

        # Step 6: Build assumptions
        assumptions = build_assumptions(
            final_parsed,
            location=merged.get("location"),
            explicit_job_types=explicit_job_types if explicit_job_types else None,
        )

        # Step 7: Calculate pricing
        pricing = calculate_total(assumptions)

        # Step 8: Sanity checks
        warnings = run_sanity_checks(
            total_min=pricing["total_min"],
            total_max=pricing["total_max"],
            area=assumptions.area.value,
            user_budget=request.budget,
        )

        # Step 9: Build response
        response = build_response(
            project_name=request.project_name,
            assumptions=assumptions,
            pricing=pricing,
            warnings=warnings,
            conflicts=final_parsed.conflicts,
        )

        # Add AI metadata
        response["llm_used"] = llm_used
        response["llm_extracted"] = llm_result

        logger.info(
            f"AI estimate done — llm_used={llm_used}, "
            f"mode={response['mode']}, "
            f"confidence={response['confidence']['score']}, "
            f"range={response['total_range']['display']}"
        )

        return EstimateAIResponse(**response)

    except Exception as e:
        logger.error(f"AI estimation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="AI estimation failed unexpectedly.")