# ---------------------------------------------------------------------------
# normalizer.py
# Layer 1: clean and normalize raw user input before parsing.
# ---------------------------------------------------------------------------

import re
import logging
from difflib import get_close_matches

logger = logging.getLogger(__name__)

# Known job types for fuzzy matching
KNOWN_JOB_TYPES = [
    "painting", "ceramic", "electrical", "plumbing", "roofing", "waterproofing"
]

# Common typo map for Indonesian context
TYPO_MAP: dict[str, str] = {
    "kermaik":    "ceramic",
    "kramik":     "ceramic",
    "keramik":    "ceramic",
    "cat":        "painting",
    "ngecat":     "painting",
    "catting":    "painting",
    "listrik":    "electrical",
    "listriik":   "electrical",
    "listirk":    "electrical",
    "elektrikal": "electrical",
    "pipa":       "plumbing",
    "sanitasi":   "plumbing",
    "atap":       "roofing",
    "genteng":    "roofing",
    "waterproof": "waterproofing",
    "anti bocor": "waterproofing",
}

# Quality keyword map
QUALITY_MAP: dict[str, str] = {
    "ekonomi":  "ekonomi",
    "murah":    "ekonomi",
    "biasa":    "ekonomi",
    "standar":  "standar",
    "standard": "standar",
    "normal":   "standar",
    "premium":  "premium",
    "bagus":    "premium",
    "mewah":    "premium",
    "mahal":    "premium",
    "impor":    "premium",
}


def normalize_area(text: str) -> float | None:
    """
    Extract and normalize area from text.
    Handles: 3x6, 3x6m, 3*6, 18m2, 18 m², sekitar 20, 15-20an
    """
    text = text.lower().strip()

    # Dimension format: 3x6, 3 x 6, 3*6, 3×6
    match = re.search(r'(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)', text)
    if match:
        area = float(match.group(1)) * float(match.group(2))
        logger.debug(f"Area from dimension: {match.group(0)} → {area}m²")
        return area

    # Range format: 15-20an, 15-20
    match = re.search(r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)', text)
    if match:
        area = (float(match.group(1)) + float(match.group(2))) / 2
        logger.debug(f"Area from range: {match.group(0)} → {area}m² (avg)")
        return area

    # Direct number with unit: 20m2, 20 m², 20 meter
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m²|m2|meter persegi|m\b)', text)
    if match:
        area = float(match.group(1))
        logger.debug(f"Area from unit: {match.group(0)} → {area}m²")
        return area

    # Vague qualifier: sekitar 20, kurang lebih 20, kira-kira 20
    match = re.search(
        r'(?:sekitar|kurang lebih|kira-kira|±|approximately)\s*(\d+(?:\.\d+)?)',
        text
    )
    if match:
        area = float(match.group(1))
        logger.debug(f"Area from vague: {match.group(0)} → {area}m²")
        return area

    # Plain number as fallback
    match = re.search(r'\b(\d+(?:\.\d+)?)\b', text)
    if match:
        area = float(match.group(1))
        logger.debug(f"Area from plain number: {area}m²")
        return area

    return None


def normalize_job_type(text: str) -> str | None:
    """Normalize job type — handles typos and Indonesian keywords."""
    text = text.lower().strip()

    # Direct match
    if text in KNOWN_JOB_TYPES:
        return text

    # Typo map
    if text in TYPO_MAP:
        return TYPO_MAP[text]

    # Partial match in typo map
    for keyword, job_type in TYPO_MAP.items():
        if keyword in text:
            return job_type

    # Fuzzy match as last resort
    matches = get_close_matches(text, KNOWN_JOB_TYPES, n=1, cutoff=0.7)
    if matches:
        logger.debug(f"Fuzzy matched '{text}' → '{matches[0]}'")
        return matches[0]

    return None


def normalize_quality(text: str) -> str | None:
    """Normalize material quality from text."""
    text = text.lower().strip()
    for keyword, quality in QUALITY_MAP.items():
        if keyword in text:
            return quality
    return None


def normalize_location(text: str) -> str:
    """Normalize city name to lowercase key."""
    return text.lower().strip().replace(" ", "_")


def normalize_size_description(text: str) -> tuple[float | None, float]:
    """
    Map vague size descriptions to approximate areas.
    Returns (area, confidence)
    """
    text = text.lower()
    SIZE_MAP = {
        ("sangat kecil", "mini", "mungil"):         (4.0,  0.25),
        ("kecil", "small", "sempit"):               (9.0,  0.30),
        ("sedang", "medium", "biasa", "standar"):   (16.0, 0.30),
        ("besar", "large", "luas"):                 (25.0, 0.25),
        ("sangat besar", "extra besar"):            (40.0, 0.20),
    }
    for keywords, (area, confidence) in SIZE_MAP.items():
        if any(kw in text for kw in keywords):
            return area, confidence
    return None, 0.0