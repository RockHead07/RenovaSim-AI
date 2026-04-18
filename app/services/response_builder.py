# ---------------------------------------------------------------------------
# response_builder.py
# Layer 6: assemble the final response in a human-readable format.
# ---------------------------------------------------------------------------

import logging
from app.services.assumption import AssumptionResult
from app.data.pricing_data import PRE_FRAMING

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "Estimasi ini berdasarkan harga pasar rata-rata. "
    "Harga aktual dapat berbeda tergantung kondisi lapangan, "
    "ketersediaan material, dan hasil negosiasi dengan kontraktor."
)

BEST_EFFORT_DISCLAIMER = (
    "Estimasi ini menggunakan banyak asumsi karena informasi yang diberikan terbatas. "
    "Hasilnya hanya sebagai gambaran kasar. "
    "Kami sangat menyarankan untuk melengkapi detail proyek."
)


def build_response(
    project_name: str,
    assumptions: AssumptionResult,
    pricing: dict,
    warnings: list[dict],
    conflicts: list[dict],
) -> dict:
    """Build the complete API response."""

    # Determine mode
    if not assumptions.job_types:
        mode = "incomplete"
    elif assumptions.confidence_score < 0.50:
        mode = "best_effort"
    else:
        mode = "standard"

    # Pre-framing — pick based on first job type
    first_job = assumptions.job_types[0] if assumptions.job_types else "default"
    pre_framing = PRE_FRAMING.get(first_job, PRE_FRAMING["default"])

    # Collect all assumptions as dicts
    assumption_list = []
    for field in ["area", "quality", "location", "scope"]:
        assumption = getattr(assumptions, field, None)
        if assumption and assumption.source != "confirmed":
            assumption_list.append({
                "field": field,
                **assumption.to_dict(),
            })

    # Collect all explanation lines
    explanation = []
    for job in pricing.get("breakdown", []):
        explanation.extend(job.get("explanation", []))

    # Clarification prompt if needed
    clarification_needed = None
    if assumptions.needs_clarification:
        field = assumptions.needs_clarification[0]
        clarification_messages = {
            "area":     "Berapa luas area yang akan direnovasi? (dalam m²)",
            "job_type": "Apa jenis pekerjaan utama yang dibutuhkan?",
            "quality":  "Material kualitas apa yang diinginkan? (Ekonomi / Standar / Premium)",
            "location": "Di kota mana proyek ini berada?",
        }
        clarification_needed = clarification_messages.get(field)

    response = {
        "project_name": project_name,
        "mode": mode,
        "confidence": {
            "score": assumptions.confidence_score,
            "label": assumptions.confidence_label,
            "message": assumptions.confidence_message,
        },
        "pre_framing": pre_framing,
        "total_range": {
            "min": pricing.get("total_min", 0),
            "max": pricing.get("total_max", 0),
            "display": pricing.get("display", "-"),
        },
        "breakdown": [
            {
                "job_type": job["job_type"],
                "area": job["area"],
                "min": job["min"],
                "max": job["max"],
            }
            for job in pricing.get("breakdown", [])
        ],
        "assumptions": assumption_list,
        "explanation": explanation,
        "warnings": warnings,
        "conflicts_resolved": conflicts,
        "clarification_needed": clarification_needed,
    "disclaimer": BEST_EFFORT_DISCLAIMER if mode == "best_effort" else DISCLAIMER,
    }

    logger.debug(f"Response built — mode={mode}, confidence={assumptions.confidence_score}")
    return response