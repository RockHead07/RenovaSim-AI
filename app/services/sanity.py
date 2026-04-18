# ---------------------------------------------------------------------------
# sanity.py
# Layer 5: detect values that don't make sense before returning output.
# ---------------------------------------------------------------------------

import logging

logger = logging.getLogger(__name__)


def run_sanity_checks(
    total_min: float,
    total_max: float,
    area: float,
    user_budget: float | None = None,
) -> list[dict]:
    """Run all sanity checks and return list of warnings."""
    warnings = []

    # Underbudget
    if user_budget and total_min > user_budget * 1.2:
        warnings.append({
            "type": "underbudget",
            "severity": "critical",
            "message": (
                f"Budget Anda (Rp {int(user_budget):,}) kemungkinan tidak cukup "
                f"untuk scope ini. Estimasi minimal: Rp {int(total_min):,}."
            ),
        })

    # Overkill budget
    if user_budget and user_budget > total_max * 2:
        warnings.append({
            "type": "overkill_budget",
            "severity": "info",
            "message": (
                "Budget Anda jauh di atas estimasi normal. "
                "Pastikan scope pekerjaan sudah sesuai kebutuhan."
            ),
        })

    # Unusual area — too large
    if area > 500:
        warnings.append({
            "type": "unusual_area_large",
            "severity": "warning",
            "message": f"Luas {area}m² tergolong sangat besar — mohon konfirmasi.",
        })

    # Unusual area — too small
    if area < 2:
        warnings.append({
            "type": "unusual_area_small",
            "severity": "warning",
            "message": f"Luas {area}m² sangat kecil — mohon konfirmasi.",
        })

    return warnings