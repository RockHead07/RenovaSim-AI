# ---------------------------------------------------------------------------
# cost_data.py
# Hardcoded unit cost table (per m²) for each supported job type.
# Replace this with a database lookup in a future iteration.
# ---------------------------------------------------------------------------

COST_TABLE: dict[str, dict[str, float]] = {
    "painting": {
        "material": 25_000,
        "labor":    15_000,
    },
    "ceramic": {
        "material": 120_000,
        "labor":     80_000,
    },
    "roof": {
        "material": 150_000,
        "labor":    100_000,
    },
}

# Convenience helper — useful for validation messages and docs
SUPPORTED_JOB_TYPES: list[str] = list(COST_TABLE.keys())
