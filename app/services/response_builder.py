# ---------------------------------------------------------------------------
# response_builder.py
# Layer 6: assemble the final response in a human-readable format.
# ---------------------------------------------------------------------------

import logging
from app.services.assumption import AssumptionResult
from app.data.pricing_data import (
    PRE_FRAMING,
    get_contextual_preframing,
    get_human_explanation,
)

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

    # Pre-framing — contextual based on confidence + job type
    first_job = assumptions.job_types[0] if assumptions.job_types else "default"
    pre_framing = get_contextual_preframing(
        assumptions.confidence_label, first_job
    ) or PRE_FRAMING.get(first_job, PRE_FRAMING["default"])

    # Collect all assumptions as dicts
    assumption_list = []
    for field in ["area", "quality", "location", "scope"]:
        assumption = getattr(assumptions, field, None)
        if assumption and assumption.source != "confirmed":
            assumption_list.append({
                "field": field,
                **assumption.to_dict(),
            })

    # Human-readable explanation
    explanation = []
    location = assumptions.location.value if assumptions.location else "default"
    quality = assumptions.quality.value if assumptions.quality else "standar"
    location_display = assumptions.location.value if assumptions.location else None
    if location_display == "default":
        location_display = None
    area = assumptions.area.value if assumptions.area else 0

    regional_exp = get_human_explanation(f"regional_{location}") or get_human_explanation("regional_default")
    if regional_exp:
        explanation.append(regional_exp)

    quality_exp = get_human_explanation(f"quality_{quality}")
    if quality_exp:
        explanation.append(quality_exp)

    for job in pricing.get("breakdown", []):
        complexity_exp = get_human_explanation(f"complexity_{job['job_type']}")
        if complexity_exp:
            explanation.append(complexity_exp)

    if area < 10:
        size_exp = get_human_explanation("size_small")
        if size_exp:
            explanation.append(size_exp)
    elif area > 50:
        size_exp = get_human_explanation("size_large")
        if size_exp:
            explanation.append(size_exp)

    waste_exp = get_human_explanation("waste_factor")
    if waste_exp:
        explanation.append(waste_exp)

    if assumptions.scope and assumptions.scope.value != "medium":
        scope_exp = get_human_explanation(f"scope_{assumptions.scope.value}")
        if scope_exp:
            explanation.append(scope_exp)

    explanation = [e for e in explanation if e]

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

    if not assumptions.job_types and clarification_needed is None:
        clarification_needed = "Apa jenis pekerjaan yang ingin direnovasi? (cat, keramik, listrik, dll)"        

    response = {
        "project_name": project_name,
        "mode": mode,
        "confidence": {
            "score": assumptions.confidence_score,
            "label": assumptions.confidence_label,
            "message": assumptions.confidence_message,
        },
        "pre_framing": pre_framing,
        "quality":  quality if assumptions.quality and assumptions.quality.source == "confirmed" else None,
        "location": location_display,
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

