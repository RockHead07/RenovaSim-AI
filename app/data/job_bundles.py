# ---------------------------------------------------------------------------
# job_bundles.py
# Room-based job bundles — a room renovation = multiple job types.
# Scope levels: light / medium / full
# ---------------------------------------------------------------------------

from typing import Literal

ScopeLevel = Literal["light", "medium", "full"]

JOB_BUNDLE: dict[str, dict[ScopeLevel, list[str]]] = {
    "bathroom": {
        "light":  ["plumbing"],
        "medium": ["plumbing", "ceramic"],
        "full":   ["plumbing", "ceramic", "electrical", "waterproofing"],
    },
    "kitchen": {
        "light":  ["ceramic"],
        "medium": ["ceramic", "plumbing"],
        "full":   ["ceramic", "plumbing", "electrical"],
    },
    "bedroom": {
        "light":  ["painting"],
        "medium": ["painting", "electrical"],
        "full":   ["painting", "electrical", "ceramic", "carpentry"],
    },
    "living_room": {
        "light":  ["painting"],
        "medium": ["painting", "ceramic"],
        "full":   ["painting", "ceramic", "electrical", "carpentry"],
    },
    "roof": {
        "light":  ["roofing"],
        "medium": ["roofing"],
        "full":   ["roofing", "painting"],
    },
}

# Keywords that map to room bundles
ROOM_KEYWORDS: dict[str, str] = {
    "kamar mandi":   "bathroom",
    "toilet":        "bathroom",
    "wc":            "bathroom",
    "dapur":         "kitchen",
    "kitchen":       "kitchen",
    "kamar tidur":   "bedroom",
    "kamar":         "bedroom",
    "bedroom":       "bedroom",
    "ruang tamu":    "living_room",
    "ruang keluarga":"living_room",
    "living room":   "living_room",
    "atap":          "roof",
    "genteng":       "roof",
}

# Scope hint keywords
SCOPE_KEYWORDS: dict[ScopeLevel, list[str]] = {
    "light":  ["cat ulang", "touch up", "ganti doang", "sedikit", "ringan", "minor"],
    "full":   ["renovasi total", "full renov", "dari nol", "semua", "total", "bongkar"],
}

# Scope multipliers
SCOPE_MULTIPLIER: dict[ScopeLevel, float] = {
    "light":  0.60,
    "medium": 1.00,
    "full":   1.30,
}


def get_jobs_for_bundle(room: str, scope: ScopeLevel) -> list[str]:
    """Return list of job types for a given room + scope."""
    bundle = JOB_BUNDLE.get(room)
    if not bundle:
        return []
    return bundle.get(scope, bundle["medium"])


def detect_room(description: str) -> str | None:
    """Detect room type from description text."""
    text = description.lower()
    for keyword, room in ROOM_KEYWORDS.items():
        if keyword in text:
            return room
    return None


def detect_scope(description: str) -> ScopeLevel:
    """Detect scope level from description text. Defaults to medium."""
    text = description.lower()
    for scope, keywords in SCOPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return scope
    return "medium"