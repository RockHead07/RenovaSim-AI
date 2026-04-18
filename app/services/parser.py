# ---------------------------------------------------------------------------
# parser.py
# Layer 2: extract structured fields from normalized input.
# ---------------------------------------------------------------------------

import logging
from app.services.normalizer import (
    normalize_area,
    normalize_job_type,
    normalize_quality,
    normalize_size_description,
)
from app.data.job_bundles import detect_room, detect_scope

logger = logging.getLogger(__name__)


class ParsedInput:
    """Result of parsing raw user input."""

    def __init__(self):
        self.area: float | None = None
        self.area_confidence: float = 0.0
        self.area_source: str = "missing"

        self.job_type: str | None = None
        self.room: str | None = None

        self.quality: str | None = None
        self.scope: str = "medium"

        self.conflicts: list[dict] = []


def parse_input(
    description: str = "",
    area: float | None = None,
    job_type: str | None = None,
    quality: str | None = None,
    location: str | None = None,
    scope: str | None = None,
) -> ParsedInput:
    """
    Parse and extract structured fields from user input.
    Explicit fields (from wizard) take priority over description parsing.
    """
    result = ParsedInput()

    # --- Area ---
    if area is not None and area > 0:
        result.area = area
        result.area_confidence = 1.0
        result.area_source = "confirmed"
    elif description:
        # Try explicit dimension/number from description
        extracted_area = normalize_area(description)
        if extracted_area:
            result.area = extracted_area
            result.area_confidence = 0.75
            result.area_source = "inferred"
        else:
            # Try vague size description
            vague_area, vague_conf = normalize_size_description(description)
            if vague_area:
                result.area = vague_area
                result.area_confidence = vague_conf
                result.area_source = "assumed"

    # --- Job type ---
    if job_type:
        result.job_type = job_type.lower().strip()
    elif description:
        # Try room bundle detection first
        room = detect_room(description)
        if room:
            result.room = room
        else:
            # Try direct job type extraction
            extracted_job = normalize_job_type(description)
            if extracted_job:
                result.job_type = extracted_job

    # --- Quality ---
    if quality:
        result.quality = quality.lower().strip()
    elif description:
        extracted_quality = normalize_quality(description)
        if extracted_quality:
            result.quality = extracted_quality

    # --- Scope ---
    if scope:
        result.scope = scope.lower().strip()
    elif description:
        result.scope = detect_scope(description)

    # --- Conflict detection ---
    # Example: user said "kecil" but also provided explicit 3x6
    if area and description:
        vague_area, _ = normalize_size_description(description)
        if vague_area and abs(vague_area - area) > 5:
            result.conflicts.append({
                "field": "area",
                "ignored": f"~{vague_area}m² (dari deskripsi)",
                "used": f"{area}m² (dari input eksplisit)",
                "reason": "Ukuran eksplisit lebih diprioritaskan dari deskripsi umum",
            })

    logger.debug(f"Parsed: area={result.area} ({result.area_source}), "
                 f"job={result.job_type}, room={result.room}, "
                 f"quality={result.quality}, scope={result.scope}")

    return result