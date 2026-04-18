# ---------------------------------------------------------------------------
# pricing_data.py
# Range-based pricing data — replaces single-number cost_data.py for v2.
# Source: market estimates (NOT field-validated).
# ---------------------------------------------------------------------------

# Base rate ranges per job_type per quality (IDR per m²)
BASE_RATE_RANGE: dict[str, dict[str, tuple[float, float]]] = {
    "painting": {
        "ekonomi":  (35_000,   55_000),
        "standar":  (55_000,   80_000),
        "premium":  (80_000,  120_000),
    },
    "ceramic": {
        "ekonomi":  (80_000,  120_000),
        "standar":  (120_000, 180_000),
        "premium":  (180_000, 280_000),
    },
    "electrical": {
        "ekonomi":  (90_000,  130_000),
        "standar":  (130_000, 200_000),
        "premium":  (200_000, 350_000),
    },
    "plumbing": {
        "ekonomi":  (80_000,  120_000),
        "standar":  (120_000, 180_000),
        "premium":  (180_000, 280_000),
    },
    "roofing": {
        "ekonomi":  (100_000, 150_000),
        "standar":  (150_000, 220_000),
        "premium":  (220_000, 380_000),
    },
    "waterproofing": {
        "ekonomi":  (60_000,   90_000),
        "standar":  (90_000,  140_000),
        "premium":  (140_000, 220_000),
    },
}

# Regional multipliers — baseline nasional + adjustment
REGIONAL_MULTIPLIER: dict[str, float] = {
    "jakarta":   1.30,
    "surabaya":  1.15,
    "bandung":   1.10,
    "semarang":  1.05,
    "jogja":     0.90,
    "yogyakarta":0.90,
    "medan":     0.95,
    "makassar":  0.92,
    "palembang": 0.90,
    "pekanbaru": 0.92,
    "balikpapan":1.10,
    "manado":    0.95,
    "papua":     1.40,
    "default":   1.00,
}

# Job complexity multipliers
JOB_COMPLEXITY: dict[str, float] = {
    "painting":       1.0,
    "ceramic":        1.2,
    "plumbing":       1.3,
    "electrical":     1.4,
    "roofing":        1.5,
    "waterproofing":  1.2,
}

# Pre-framing messages per job type
PRE_FRAMING: dict[str, str] = {
    "painting":      "Banyak yang mengira biaya cat hanya untuk catnya saja. Estimasi ini sudah mencakup plamir, cat dasar, dan upah tukang.",
    "ceramic":       "Pemasangan keramik mencakup material, perekat, nat, dan upah tukang. Harga bisa bervariasi tergantung ukuran dan motif keramik.",
    "electrical":    "Instalasi listrik memerlukan keahlian khusus. Estimasi ini mencakup kabel, komponen, dan upah teknisi listrik.",
    "plumbing":      "Pekerjaan plumbing mencakup pipa, fitting, dan upah tukang. Kondisi instalasi lama bisa mempengaruhi biaya aktual.",
    "roofing":       "Pekerjaan atap sangat dipengaruhi kondisi lapangan. Estimasi ini sebagai gambaran awal sebelum survei langsung.",
    "waterproofing": "Waterproofing yang baik mencegah kebocoran jangka panjang. Biaya tergantung kondisi permukaan dan produk yang digunakan.",
    "default":       "Estimasi ini berdasarkan harga pasar rata-rata. Harga aktual dapat berbeda tergantung kondisi lapangan.",
}

WASTE_FACTOR: float = 0.05
MINIMUM_PROJECT_COST: float = 500_000