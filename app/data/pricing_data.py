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

# ---------------------------------------------------------------------------
# Human-readable explanation templates
# ---------------------------------------------------------------------------

HUMAN_EXPLANATIONS: dict[str, str] = {
    "regional_jakarta":    "Upah tukang di Jakarta ~30% lebih tinggi dari rata-rata nasional",
    "regional_surabaya":   "Upah tukang di Surabaya ~15% lebih tinggi dari rata-rata nasional",
    "regional_bandung":    "Upah tukang di Bandung ~10% lebih tinggi dari rata-rata nasional",
    "regional_jogja":      "Upah tukang di Jogja ~10% lebih rendah dari rata-rata nasional",
    "regional_papua":      "Upah tukang di Papua ~40% lebih tinggi karena faktor logistik",
    "regional_default":    "Menggunakan harga rata-rata nasional sebagai acuan",

    "complexity_painting":       "Pengecatan adalah pekerjaan dasar — biaya tukang relatif standar",
    "complexity_ceramic":        "Pemasangan keramik butuh ketelitian lebih — biaya tukang lebih tinggi dari cat",
    "complexity_plumbing":       "Pekerjaan plumbing butuh keahlian khusus — biaya tukang di atas rata-rata",
    "complexity_electrical":     "Instalasi listrik butuh teknisi bersertifikat — biaya tertinggi di antara pekerjaan umum",
    "complexity_roofing":        "Pekerjaan atap berisiko tinggi dan butuh alat khusus — biaya paling tinggi",
    "complexity_waterproofing":  "Waterproofing butuh material dan teknik khusus — biaya di atas standar",

    "size_small":    "Proyek kecil (<10m²) memiliki biaya per m² lebih tinggi karena overhead tetap tukang",
    "size_medium":   "Ukuran standar — tidak ada penyesuaian biaya per m²",
    "size_large":    "Proyek besar (>50m²) mendapat efisiensi biaya — harga per m² lebih rendah",

    "waste_factor":  "Ditambahkan 5% untuk material cadangan dan waste selama pengerjaan",
    "minimum_cost":  "Biaya minimum proyek diterapkan — tidak ada pekerjaan di bawah Rp 500.000",

    "quality_ekonomi":  "Material ekonomi: produk lokal standar, tahan pakai untuk kebutuhan dasar",
    "quality_standar":  "Material standar: keseimbangan kualitas dan harga, pilihan umum",
    "quality_premium":  "Material premium: produk impor atau merek ternama, kualitas dan estetika terbaik",

    "scope_light":   "Scope ringan: hanya pekerjaan utama, tanpa bongkar atau finishing tambahan",
    "scope_medium":  "Scope sedang: pekerjaan standar termasuk persiapan dan finishing dasar",
    "scope_full":    "Scope total: renovasi menyeluruh termasuk bongkar, pengerjaan, dan finishing lengkap",
}


def get_human_explanation(key: str) -> str | None:
    return HUMAN_EXPLANATIONS.get(key)


# Contextual pre-framing based on confidence + job type
CONTEXTUAL_PREFRAMING: dict[str, dict[str, str]] = {
    "high": {
        "painting":      "Berdasarkan detail yang Anda berikan, berikut estimasi biaya pengecatan:",
        "ceramic":       "Berdasarkan detail yang Anda berikan, berikut estimasi biaya pemasangan keramik:",
        "electrical":    "Berdasarkan detail yang Anda berikan, berikut estimasi biaya instalasi listrik:",
        "plumbing":      "Berdasarkan detail yang Anda berikan, berikut estimasi biaya pekerjaan plumbing:",
        "roofing":       "Berdasarkan detail yang Anda berikan, berikut estimasi biaya pekerjaan atap:",
        "waterproofing": "Berdasarkan detail yang Anda berikan, berikut estimasi biaya waterproofing:",
        "default":       "Berdasarkan detail yang Anda berikan, berikut estimasi biaya renovasi:",
    },
    "medium": {
        "painting":      "Banyak yang mengira biaya cat hanya untuk catnya saja. Estimasi ini sudah mencakup plamir, cat dasar, dan upah tukang.",
        "ceramic":       "Pemasangan keramik mencakup material, perekat, nat, dan upah tukang. Harga bisa bervariasi tergantung ukuran dan motif.",
        "electrical":    "Instalasi listrik memerlukan keahlian khusus. Estimasi ini mencakup kabel, komponen, dan upah teknisi.",
        "plumbing":      "Pekerjaan plumbing mencakup pipa, fitting, dan upah tukang. Kondisi instalasi lama bisa mempengaruhi biaya.",
        "roofing":       "Pekerjaan atap sangat dipengaruhi kondisi lapangan. Estimasi ini sebagai gambaran awal sebelum survei.",
        "waterproofing": "Waterproofing yang baik mencegah kebocoran jangka panjang. Biaya tergantung kondisi permukaan.",
        "default":       "Estimasi ini berdasarkan harga pasar rata-rata dengan beberapa asumsi yang bisa Anda koreksi.",
    },
    "low": {
        "default": (
            "Dengan informasi yang masih terbatas, ini adalah perkiraan kasar. "
            "Lengkapi detail proyek untuk estimasi yang lebih akurat."
        ),
    },
}


def get_contextual_preframing(confidence_label: str, job_type: str) -> str:
    """Get pre-framing message based on confidence level and job type."""
    level_map = {"Tinggi": "high", "Sedang": "medium", "Rendah": "low"}
    level = level_map.get(confidence_label, "medium")

    level_frames = CONTEXTUAL_PREFRAMING.get(level, CONTEXTUAL_PREFRAMING["medium"])
    return level_frames.get(job_type, level_frames.get("default", ""))