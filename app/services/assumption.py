# ---------------------------------------------------------------------------
# assumption.py
# Layer 3: fill missing fields with defaults, tag every assumption.
# Every assumption is active — drives confidence + clarification.
# ---------------------------------------------------------------------------

import logging
from app.services.parser import ParsedInput
from app.data.job_bundles import get_jobs_for_bundle, ScopeLevel

logger = logging.getLogger(__name__)

IMPACT_WEIGHT = {"high": 1.0, "medium": 0.6, "low": 0.3}

FIELD_WEIGHTS = {
    "area":     0.40,
    "job_type": 0.25,
    "location": 0.20,
    "quality":  0.15,
}

CRITICAL_FIELDS = ["area", "job_type"]

DEFAULT_QUALITY = "standar"
DEFAULT_LOCATION = "default"
DEFAULT_AREA_SMALL_ROOM = 9.0


class AssumptionField:
    def __init__(self, value, source, confidence, impact, reason, needs_clarification=False):
        self.value = value
        self.source = source          # confirmed | assumed | inferred
        self.confidence = confidence  # 0.0 – 1.0
        self.impact = impact          # high | medium | low
        self.reason = reason
        self.needs_clarification = needs_clarification

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "source": self.source,
            "confidence": self.confidence,
            "impact": self.impact,
            "reason": self.reason,
            "needs_clarification": self.needs_clarification,
            "editable": True,
        }


class AssumptionResult:
    def __init__(self):
        self.area: AssumptionField | None = None
        self.job_type: AssumptionField | None = None
        self.job_types: list[str] = []
        self.quality: AssumptionField | None = None
        self.location: AssumptionField | None = None
        self.scope: AssumptionField | None = None
        self.confidence_score: float = 0.0
        self.confidence_label: str = ""
        self.confidence_message: str = ""
        self.needs_clarification: list[str] = []


def build_assumptions(
    parsed: ParsedInput,
    location: str | None = None,
    explicit_job_types: list[str] | None = None,
) -> AssumptionResult:
    result = AssumptionResult()

    # --- Area ---
    if parsed.area and parsed.area_source == "confirmed":
        result.area = AssumptionField(
            value=parsed.area,
            source="confirmed",
            confidence=1.0,
            impact="high",
            reason="Luas diberikan langsung oleh user",
        )
    elif parsed.area and parsed.area_source == "inferred":
        result.area = AssumptionField(
            value=parsed.area,
            source="inferred",
            confidence=parsed.area_confidence,
            impact="high",
            reason="Luas diambil dari deskripsi teks",
            needs_clarification=True,
        )
    elif parsed.area and parsed.area_source == "assumed":
        result.area = AssumptionField(
            value=parsed.area,
            source="assumed",
            confidence=parsed.area_confidence,
            impact="high",
            reason=f"Luas diasumsikan dari deskripsi ukuran (~{parsed.area}m²)",
            needs_clarification=True,
        )
    else:
        # No area at all — use default, flag as critical
        result.area = AssumptionField(
            value=DEFAULT_AREA_SMALL_ROOM,
            source="assumed",
            confidence=0.20,
            impact="high",
            reason="Luas tidak disebutkan — diasumsikan 9m² (ruangan kecil)",
            needs_clarification=True,
        )

    # --- Job types (from bundle or direct) ---
    if explicit_job_types:
        # LLM extracted multiple job types explicitly — use them directly
        result.job_types = explicit_job_types
        result.job_type = AssumptionField(
            value=explicit_job_types[0] if explicit_job_types else None,
            source="confirmed",
            confidence=1.0,
            impact="high",
            reason="Pekerjaan diekstrak secara eksplisit",
        )
        logger.debug(f"Using explicit job_types from LLM: {explicit_job_types}")
    elif parsed.job_type:
        result.job_types = [parsed.job_type]
        result.job_type = AssumptionField(
            value=parsed.job_type,
            source="confirmed",
            confidence=1.0,
            impact="high",
            reason="Pekerjaan dipilih secara eksplisit",
        )
    elif parsed.room:
        scope = parsed.scope or "medium"
        jobs = get_jobs_for_bundle(parsed.room, scope)
        result.job_types = jobs
        result.job_type = AssumptionField(
            value=jobs[0] if jobs else None,
            source="inferred",
            confidence=0.80,
            impact="high",
            reason=f"Pekerjaan dideteksi dari ruangan '{parsed.room}'",
        )
        result.scope = AssumptionField(
            value=scope,
            source="inferred" if parsed.scope != "medium" else "assumed",
            confidence=0.70 if parsed.scope != "medium" else 0.50,
            impact="medium",
            reason=f"Ruangan '{parsed.room}' dengan scope '{scope}'",
        )
    else:
        # No job type detected — cannot proceed without clarification
        result.job_types = []
        result.job_type = AssumptionField(
            value=None,
            source="assumed",
            confidence=0.0,
            impact="high",
            reason="Pekerjaan tidak ditentukan",
            needs_clarification=True,
        )

    # --- Quality ---
    if parsed.quality:
        result.quality = AssumptionField(
            value=parsed.quality,
            source="confirmed",
            confidence=1.0,
            impact="medium",
            reason="Kualitas dipilih oleh user",
        )
    else:
        result.quality = AssumptionField(
            value=DEFAULT_QUALITY,
            source="assumed",
            confidence=0.60,
            impact="medium",
            reason=f"Kualitas tidak disebutkan — diasumsikan '{DEFAULT_QUALITY}'",
        )

    # --- Location ---
    if location:
        result.location = AssumptionField(
            value=location.lower().strip(),
            source="confirmed",
            confidence=1.0,
            impact="medium",
            reason="Lokasi dipilih oleh user",
        )
    else:
        result.location = AssumptionField(
            value=DEFAULT_LOCATION,
            source="assumed",
            confidence=0.50,
            impact="medium",
            reason="Lokasi tidak disebutkan — menggunakan harga rata-rata nasional",
        )

    # --- Confidence calculation ---
    score = 0.0
    for field, weight in FIELD_WEIGHTS.items():
        assumption = getattr(result, field, None)
        if assumption and assumption.source == "confirmed":
            score += weight
        elif assumption and assumption.source == "inferred":
            score += weight * assumption.confidence

    # Hard cap: only if critical fields are fully assumed (not inferred from text)
    for field in CRITICAL_FIELDS:
        assumption = getattr(result, field, None)
        if assumption and assumption.source == "assumed":
            score = min(score, 0.60)  # softer cap for assumed
            break
        elif assumption and assumption.source == "missing":
            score = min(score, 0.40)  # hard cap only if missing
            break

    # Bonus: LLM confirmed multiple job types explicitly
    if len(result.job_types) >= 3 and not result.scope:
        score = min(score + 0.10, 1.0)  # bonus for rich input

    result.confidence_score = round(score, 2)

    # Human-readable confidence
    if result.confidence_score >= 0.75:
        result.confidence_label = "Tinggi"
        result.confidence_message = "Estimasi cukup akurat"
    elif result.confidence_score >= 0.55:
        result.confidence_label = "Sedang"
        result.confidence_message = "Estimasi perlu beberapa asumsi"
    else:
        result.confidence_label = "Rendah"
        result.confidence_message = "Estimasi kasar, banyak asumsi"

    # Clarification priority: top 2 fields with highest impact × uncertainty
    clarification_candidates = []
    for field in ["area", "job_type", "quality", "location"]:
        assumption = getattr(result, field, None)
        if assumption and assumption.needs_clarification:
            priority = IMPACT_WEIGHT[assumption.impact] * (1 - assumption.confidence)
            clarification_candidates.append((field, priority))

    clarification_candidates.sort(key=lambda x: x[1], reverse=True)
    result.needs_clarification = [f for f, _ in clarification_candidates[:2]]

    logger.debug(f"Confidence: {result.confidence_score} ({result.confidence_label})")
    return result