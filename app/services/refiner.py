# ---------------------------------------------------------------------------
# refiner.py
# Logic for updating assumptions in-place based on user corrections.
# User corrects → system recalculates — no need to start from scratch.
# ---------------------------------------------------------------------------

import logging
from app.services.parser import parse_input
from app.services.assumption import build_assumptions
from app.services.pricing import calculate_total
from app.services.sanity import run_sanity_checks
from app.services.response_builder import build_response

logger = logging.getLogger(__name__)


def refine_estimate(
    previous_response: dict,
    corrections: dict,
) -> dict:
    """
    Apply user corrections to a previous estimate and recalculate.

    corrections can include:
    - area: float
    - quality: str
    - location: str
    - scope: str
    - job_type: str
    - budget: float
    """
    logger.info(f"Refining estimate with corrections: {list(corrections.keys())}")

    project_name = previous_response.get("project_name", "Proyek Renovasi")

    # Extract previous assumptions (assumed fields only)
    prev_assumptions = {
        item["field"]: item["value"]
        for item in previous_response.get("assumptions", [])
    }

    # Also extract confirmed values from top-level response
    # These are fields detected by LLM (not assumed), so NOT in assumptions array
    prev_confirmed = {}
    if previous_response.get("quality"):
        prev_confirmed["quality"] = previous_response["quality"]
    if previous_response.get("location") and previous_response["location"] != "default":
        prev_confirmed["location"] = previous_response["location"]
    if previous_response.get("breakdown"):
        first = previous_response["breakdown"][0]
        if first.get("area"):
            prev_confirmed["area"] = first["area"]

    # Merge priority: confirmed < assumed < corrections
    # corrections always win, then assumed, then confirmed
    merged = {**prev_confirmed, **prev_assumptions, **corrections}

    # Extract previous job types from breakdown
    breakdown = previous_response.get("breakdown", [])
    prev_job_types = [job["job_type"] for job in breakdown] if breakdown else []

    # Re-parse with corrected values
    parsed = parse_input(
        area=corrections.get("area") or merged.get("area"),
        job_type=corrections.get("job_type"),
        quality=corrections.get("quality") or merged.get("quality"),
        location=corrections.get("location") or merged.get("location"),
        scope=corrections.get("scope") or merged.get("scope"),
    )

    # Preserve ALL previous job types unless user explicitly corrects job_type.
    # This fixes multi-job context being lost after refinement.
    explicit_job_types = (
        prev_job_types
        if prev_job_types and not corrections.get("job_type")
        else None
    )

    # Build new assumptions, passing previous job types to preserve multi-job context
    assumptions = build_assumptions(
        parsed,
        location=corrections.get("location") or merged.get("location"),
        explicit_job_types=explicit_job_types,
    )

    # Recalculate
    pricing = calculate_total(assumptions)

    warnings = run_sanity_checks(
        total_min=pricing["total_min"],
        total_max=pricing["total_max"],
        area=assumptions.area.value,
        user_budget=corrections.get("budget"),
    )

    response = build_response(
        project_name=project_name,
        assumptions=assumptions,
        pricing=pricing,
        warnings=warnings,
        conflicts=parsed.conflicts,
    )

    # Add refinement note
    corrected_fields = list(corrections.keys())
    response["refinement_note"] = (
        f"Estimasi diperbarui berdasarkan koreksi: {', '.join(corrected_fields)}"
    )

    logger.info(
        f"Refined — confidence={assumptions.confidence_score}, "
        f"range={pricing['display']}"
    )

    return response