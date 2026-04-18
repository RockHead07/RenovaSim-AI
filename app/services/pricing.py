# ---------------------------------------------------------------------------
# pricing.py
# Layer 4: calculate cost range based on all multipliers.
# Always returns min/max range — never a single number.
# ---------------------------------------------------------------------------

import logging
from app.data.pricing_data import (
    BASE_RATE_RANGE,
    REGIONAL_MULTIPLIER,
    JOB_COMPLEXITY,
    WASTE_FACTOR,
    MINIMUM_PROJECT_COST,
)
from app.data.job_bundles import SCOPE_MULTIPLIER, ScopeLevel
from app.services.assumption import AssumptionResult

logger = logging.getLogger(__name__)


def get_size_factor(area: float) -> float:
    """Non-linear size adjustment — small jobs cost more per m²."""
    if area < 10:   return 1.30
    if area < 25:   return 1.10
    if area < 50:   return 1.00
    if area < 100:  return 0.92
    return 0.85


def calculate_job_cost(
    job_type: str,
    quality: str,
    area: float,
    location: str,
    scope: str = "medium",
) -> dict:
    """Calculate min/max cost for a single job type."""

    # Get base rate range
    job_rates = BASE_RATE_RANGE.get(job_type)
    if not job_rates:
        logger.warning(f"Unknown job type: {job_type}, using painting rates")
        job_rates = BASE_RATE_RANGE["painting"]

    quality_rates = job_rates.get(quality, job_rates["standar"])
    base_min, base_max = quality_rates

    # Multipliers
    regional  = REGIONAL_MULTIPLIER.get(location, REGIONAL_MULTIPLIER["default"])
    complexity = JOB_COMPLEXITY.get(job_type, 1.0)
    size      = get_size_factor(area)
    waste     = 1 + WASTE_FACTOR
    scope_mult = SCOPE_MULTIPLIER.get(scope, 1.0)

    # Calculate range
    min_cost = base_min * area * regional * complexity * size * waste * scope_mult
    max_cost = base_max * area * regional * complexity * size * waste * scope_mult

    # Apply minimum project cost
    min_cost = max(MINIMUM_PROJECT_COST, min_cost)
    max_cost = max(MINIMUM_PROJECT_COST, max_cost)

    explanation = [
        f"Harga dasar {job_type} ({quality}): Rp {int(base_min):,} – {int(base_max):,}/m²",
        f"Luas: {area}m²",
        f"Faktor lokasi ({location}): ×{regional}",
        f"Kompleksitas pekerjaan ({job_type}): ×{complexity}",
        f"Faktor ukuran: ×{size}",
        f"Waste factor: ×{waste}",
    ]
    if scope != "medium":
        explanation.append(f"Scope {scope}: ×{scope_mult}")

    return {
        "job_type": job_type,
        "area": area,
        "min": round(min_cost),
        "max": round(max_cost),
        "explanation": explanation,
    }


def calculate_total(assumptions: AssumptionResult) -> dict:
    """Calculate total cost range across all job types."""

    area     = assumptions.area.value
    quality  = assumptions.quality.value
    location = assumptions.location.value
    scope    = assumptions.scope.value if assumptions.scope else "medium"
    job_types = assumptions.job_types

    if not job_types:
        return {
            "breakdown": [],
            "total_min": 0,
            "total_max": 0,
            "display": "Tidak dapat dihitung — tipe pekerjaan tidak diketahui",
        }

    breakdown = []
    total_min = 0
    total_max = 0

    for job_type in job_types:
        job_cost = calculate_job_cost(job_type, quality, area, location, scope)
        breakdown.append(job_cost)
        total_min += job_cost["min"]
        total_max += job_cost["max"]

    # Widen range if confidence is low
    if assumptions.confidence_score < 0.50:
        total_min = round(total_min * 0.85)
        total_max = round(total_max * 1.20)

    # Round display based on confidence
    if assumptions.confidence_score > 0.70:
        # Round to nearest 100k
        display_min = round(total_min / 100_000) * 100_000
        display_max = round(total_max / 100_000) * 100_000
    else:
        # Round to nearest 500k
        display_min = round(total_min / 500_000) * 500_000
        display_max = round(total_max / 500_000) * 500_000

    def format_idr(amount: float) -> str:
        if amount >= 1_000_000:
            val = amount / 1_000_000
            return f"Rp {val:.1f} juta".replace(".0 ", " ")
        return f"Rp {int(amount):,}"

    display = f"{format_idr(display_min)} – {format_idr(display_max)}"

    logger.debug(f"Total range: {display}")

    return {
        "breakdown": breakdown,
        "total_min": total_min,
        "total_max": total_max,
        "display": display,
    }