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
    "carpentry": {
        "ekonomi":  (50_000,   80_000),
        "standar":  (80_000,  150_000),
        "premium":  (150_000, 300_000),
    },
    "ceiling": {
        "ekonomi":  ( 50_000,   70_000),
        "standar":  (100_000,  150_000),
        "premium":  (150_000,  300_000),
    },
    "wall": {
        "ekonomi":  ( 65_000,   90_000),
        "standar":  ( 95_000,  140_000),
        "premium":  (140_000,  220_000),
    },
    "wall_tile": {
        "ekonomi":  (120_000,  165_000),
        "standar":  (165_000,  250_000),
        "premium":  (250_000,  450_000),
    },
    "window": {
        "ekonomi":  (200_000,  350_000),
        "standar":  (350_000,  550_000),
        "premium":  (550_000,  900_000),
    },
    "flooring_wood": {
        "ekonomi":  (100_000,  180_000),
        "standar":  (180_000,  320_000),
        "premium":  (320_000,  600_000),
    },
    "fence": {
        "ekonomi":  (300_000,  450_000),
        "standar":  (450_000,  650_000),
        "premium":  (650_000, 1_200_000),
    },
    "carport": {
        "ekonomi":  (250_000,  400_000),
        "standar":  (400_000,  650_000),
        "premium":  (650_000, 1_200_000),
    },
    "cabinet": {
        "ekonomi":  (350_000,  600_000),
        "standar":  (600_000, 1_000_000),
        "premium":  (1_000_000, 2_500_000),
    },
    "demolition": {
        "ekonomi":  ( 40_000,   70_000),
        "standar":  ( 70_000,  120_000),
        "premium":  (120_000,  200_000),
    },
    "insulation": {
        "ekonomi":  ( 60_000,  100_000),
        "standar":  (100_000,  160_000),
        "premium":  (160_000,  280_000),
    },
    "wallpaper": {
        "ekonomi":  ( 80_000,  130_000),
        "standar":  (130_000,  200_000),
        "premium":  (200_000,  400_000),
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
    "carpentry":      1.3,
    "ceiling":       1.1,
    "wall":          1.1,
    "wall_tile":     1.25,
    "window":        1.4,
    "flooring_wood": 1.2,
    "fence":         1.3,
    "carport":       1.4,
    "cabinet":       1.5,
    "demolition":    1.0,
    "insulation":    1.2,
    "wallpaper":     1.1,
}

# Pre-framing messages per job type
PRE_FRAMING: dict[str, str] = {
    "painting":      "Banyak yang mengira biaya cat hanya untuk catnya saja. Estimasi ini sudah mencakup plamir, cat dasar, dan upah tukang.",
    "ceramic":       "Pemasangan keramik mencakup material, perekat, nat, dan upah tukang. Harga bisa bervariasi tergantung ukuran dan motif keramik.",
    "electrical":    "Instalasi listrik memerlukan keahlian khusus. Estimasi ini mencakup kabel, komponen, dan upah teknisi listrik.",
    "plumbing":      "Pekerjaan plumbing mencakup pipa, fitting, dan upah tukang. Kondisi instalasi lama bisa mempengaruhi biaya aktual.",
    "roofing":       "Pekerjaan atap sangat dipengaruhi kondisi lapangan. Estimasi ini sebagai gambaran awal sebelum survei langsung.",
    "waterproofing": "Waterproofing yang baik mencegah kebocoran jangka panjang. Biaya tergantung kondisi permukaan dan produk yang digunakan.",
    "carpentry":     "Pekerjaan pertukangan mencakup material kayu/UPVC, aksesoris, dan upah tukang. Harga bervariasi tergantung jenis dan kualitas material pintu/jendela.",
    "ceiling":       "Biaya plafon mencakup rangka hollow galvanis, papan gypsum/GRC, dan upah tukang. Drop ceiling atau desain bertingkat menambah biaya.",
    "wall":          "Plester dan acian dinding mencakup material semen, pasir, dan upah tukang. Dinding lama yang tidak rata membutuhkan biaya tambahan.",
    "wall_tile":     "Keramik dinding lebih rumit dari lantai karena butuh perekat khusus dan presisi tinggi. Harga bervariasi tergantung ukuran dan motif.",
    "window":        "Biaya jendela mencakup kusen aluminium/UPVC, kaca, dan upah pasang. Jendela dengan kaca tempered atau double glass lebih mahal.",
    "flooring_wood": "Lantai vinyl dan parket mencakup material dan upah pasang. Vinyl lebih ekonomis, parket solid lebih premium dan tahan lama.",
    "fence":         "Biaya pagar mencakup material (bata/besi/hollow) dan upah tukang. Pagar dengan desain khusus atau finishing cat menambah biaya.",
    "carport":       "Biaya kanopi mencakup rangka baja ringan/hollow, atap polycarbonate/spandek, dan upah pasang. Luas area = panjang \u00d7 lebar kanopi.",
    "cabinet":       "Lemari built-in dan wardrobe dihitung per m\u00b2 area dinding yang tertutup. Material HPL lebih ekonomis, solid wood lebih premium.",
    "demolition":    "Biaya bongkaran mencakup upah tukang dan pembuangan material. Dinding struktural lebih mahal dibongkar dari dinding partisi.",
    "insulation":    "Insulasi atap dan dinding mengurangi panas dan kebisingan. Glasswool/rockwool standar, foam polyurethane premium.",
    "wallpaper":     "Biaya wallpaper mencakup material dan upah pasang. Dinding harus rata sebelum pasang. Wallpaper impor dan motif khusus lebih mahal.",
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
    "complexity_carpentry":  "Pekerjaan pertukangan (pintu/jendela) butuh keahlian khusus dan material berkualitas",
    "complexity_ceiling":      "Plafon membutuhkan ketelitian dan rangka yang presisi \u2014 biaya di atas pengecatan biasa",
    "complexity_wall":         "Plester dan acian butuh keahlian agar dinding rata sempurna \u2014 biaya standar finishing",
    "complexity_wall_tile":    "Keramik dinding butuh presisi dan perekat khusus \u2014 lebih mahal dari keramik lantai",
    "complexity_window":       "Pemasangan jendela butuh keahlian kusen dan kaca \u2014 biaya di atas pertukangan standar",
    "complexity_flooring_wood":"Lantai vinyl/parket butuh alas rata sempurna \u2014 biaya di atas keramik standar",
    "complexity_fence":        "Pagar tembok butuh pondasi dan plester finishing \u2014 pekerjaan sipil berbiaya menengah",
    "complexity_carport":      "Kanopi butuh struktur baja dan waterproofing \u2014 pekerjaan menengah ke atas",
    "complexity_cabinet":      "Lemari built-in butuh ketelitian tinggi \u2014 pekerjaan interior berbiaya tinggi",
    "complexity_demolition":   "Bongkaran adalah pekerjaan dasar \u2014 biaya tenaga relatif rendah",
    "complexity_insulation":   "Insulasi butuh material khusus dan pemasangan rapi \u2014 biaya menengah",
    "complexity_wallpaper":    "Pasang wallpaper butuh dinding rata dan ketelitian \u2014 biaya menengah",

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
        "carpentry":     "Berdasarkan detail yang Anda berikan, berikut estimasi biaya pekerjaan pertukangan:",
        "ceiling":       "Berdasarkan detail yang Anda berikan, berikut estimasi biaya pekerjaan plafon:",
        "wall":          "Berdasarkan detail yang Anda berikan, berikut estimasi biaya plester dan acian:",
        "wall_tile":     "Berdasarkan detail yang Anda berikan, berikut estimasi biaya keramik dinding:",
        "window":        "Berdasarkan detail yang Anda berikan, berikut estimasi biaya pemasangan jendela:",
        "flooring_wood": "Berdasarkan detail yang Anda berikan, berikut estimasi biaya lantai vinyl/parket:",
        "fence":         "Berdasarkan detail yang Anda berikan, berikut estimasi biaya pembangunan pagar:",
        "carport":       "Berdasarkan detail yang Anda berikan, berikut estimasi biaya kanopi/carport:",
        "cabinet":       "Berdasarkan detail yang Anda berikan, berikut estimasi biaya lemari/wardrobe:",
        "demolition":    "Berdasarkan detail yang Anda berikan, berikut estimasi biaya bongkaran:",
        "insulation":    "Berdasarkan detail yang Anda berikan, berikut estimasi biaya insulasi:",
        "wallpaper":     "Berdasarkan detail yang Anda berikan, berikut estimasi biaya pemasangan wallpaper:",
        "default":       "Berdasarkan detail yang Anda berikan, berikut estimasi biaya renovasi:",
    },
    "medium": {
        "painting":      "Banyak yang mengira biaya cat hanya untuk catnya saja. Estimasi ini sudah mencakup plamir, cat dasar, dan upah tukang.",
        "ceramic":       "Pemasangan keramik mencakup material, perekat, nat, dan upah tukang. Harga bisa bervariasi tergantung ukuran dan motif.",
        "electrical":    "Instalasi listrik memerlukan keahlian khusus. Estimasi ini mencakup kabel, komponen, dan upah teknisi.",
        "plumbing":      "Pekerjaan plumbing mencakup pipa, fitting, dan upah tukang. Kondisi instalasi lama bisa mempengaruhi biaya.",
        "roofing":       "Pekerjaan atap sangat dipengaruhi kondisi lapangan. Estimasi ini sebagai gambaran awal sebelum survei.",
        "waterproofing": "Waterproofing yang baik mencegah kebocoran jangka panjang. Biaya tergantung kondisi permukaan.",
        "carpentry":     "Pekerjaan pertukangan mencakup material pintu/jendela, aksesoris, dan upah tukang. Harga sangat bergantung pada jenis material yang dipilih.",
        "ceiling":       "Biaya plafon mencakup rangka dan papan gypsum. Drop ceiling atau desain khusus dapat menambah biaya signifikan.",
        "wall":          "Plester dan acian butuh waktu cukup lama. Kualitas akhir sangat tergantung keahlian tukang yang dipilih.",
        "wall_tile":     "Keramik dinding lebih menantang dari lantai. Pastikan pilih tukang yang berpengalaman untuk hasil nat yang rapi.",
        "window":        "Biaya jendela sangat bervariasi tergantung material kusen dan jenis kaca yang dipilih.",
        "flooring_wood": "Vinyl dan parket membutuhkan alas yang benar-benar rata. Persiapan permukaan sering menjadi biaya tersembunyi.",
        "fence":         "Biaya pagar sangat dipengaruhi desain dan material. Pagar tembok lebih mahal tapi lebih tahan lama dari pagar besi.",
        "carport":       "Biaya kanopi tergantung material atap. Polycarbonate lebih murah, atap spandek atau genteng metal lebih premium.",
        "cabinet":       "Lemari built-in sangat bervariasi tergantung material finishing. HPL paling umum, solid wood untuk premium.",
        "demolition":    "Biaya bongkaran tergantung jenis dinding. Dinding bata lebih mahal dibongkar dari dinding partisi gypsum.",
        "insulation":    "Insulasi atap sangat direkomendasikan di iklim tropis. Investasi awal terbayar dari tagihan listrik yang lebih rendah.",
        "wallpaper":     "Kondisi dinding sangat menentukan hasil wallpaper. Dinding tidak rata perlu perbaikan dulu sebelum pasang.",
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