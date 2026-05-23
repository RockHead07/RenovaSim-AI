# RenovaSim AI — System Specification
> Version: 0.1.0 (MVP)  
> Status: Active Development  
> Last Updated: 2026-05-23  
> This is the single source of truth for the RenovaSim AI system.  
> README and AI_CONTEXT are derived from this document.

---

## 1. Product Definition

**RenovaSim AI** is a location-aware, AI-assisted renovation cost estimation platform (RAB generator) for the Indonesian market.

It is a **decision-support SaaS tool** — not a marketplace, not a contractor platform.

### Core Value Proposition
> Help homeowners and property owners get a credible, explainable renovation cost estimate before talking to a contractor.

### What it is NOT
- Not a fixed price guarantee
- Not a contractor booking platform
- Not a material procurement tool
- Not a design simulation tool (yet)

---

## 2. User Flow (Source of Truth)

```
Step 1 — Project Name
         User gives the project a name for tracking
         e.g., "Renovasi Rumah Pak Budi"

Step 2 — Location
         User selects city/kabupaten
         Purpose: determines local labor rates (upah tukang)

Step 3 — Renovation Type
         User selects primary job type
         e.g., Listrik, Keramik, Cat, Atap, Plumbing

Step 4 — Material Quality
         User selects: Ekonomi / Standar / Premium
         Purpose: price multiplier for materials

         ↓

AI Estimation Page
         - Summary bar (nama, lokasi, tipe, kualitas)
         - MANDATORY scope clarifier:
           "Renovasi ini lebih ke: Ringan / Sedang / Total?"
         - Input: Luas Area (m² or sqft)
         - Input: Deskripsi bebas (free text, optional but encouraged)
         - Button: "Generate Estimasi"

         ↓

Result Page
         - Pre-framing statement (expectation management)
         - Cost range (NOT single number)
         - Breakdown: material + labor per job
         - Assumptions shown (all of them, editable)
         - Confidence score (human-readable, not raw number)
         - Warnings (budget mismatch, unusual values)
         - Explanation trail ("angka ini dari mana?")
```

---

## 3. Estimation Engine (Source of Truth)

### 3.1 Pricing Formula

```
final_cost = base_rate[job_type][quality]
           × regional_multiplier[city]
           × job_complexity_multiplier[job_type]
           × size_factor(area)
           × (1 + waste_factor)

total = max(minimum_project_cost, final_cost)
```

### 3.2 Base Rate (Range, NOT single number)

```python
BASE_RATE_RANGE = {
    "painting": {
        "ekonomi":  (35_000,  55_000),   # IDR per m²
        "standar":  (55_000,  80_000),
        "premium":  (80_000, 120_000),
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
}
```

> ⚠️ These are market estimates, not validated field data.  
> Must be updated with real data as soon as available.

### 3.3 Regional Multiplier

```python
REGIONAL_MULTIPLIER = {
    "jakarta":    1.30,
    "surabaya":   1.15,
    "bandung":    1.10,
    "semarang":   1.05,
    "jogja":      0.90,
    "medan":      0.95,
    "makassar":   0.92,
    "papua":      1.40,
    "default":    1.00,   # baseline nasional
}
```

> Source: Market estimation (not SNI validated).  
> Framing: "baseline nasional + adjustment" — NOT "accurate per city".

### 3.4 Job Complexity Multiplier

```python
JOB_COMPLEXITY = {
    "painting":   1.0,
    "ceramic":    1.2,
    "plumbing":   1.3,
    "electrical": 1.4,
    "roofing":    1.5,
}
```

### 3.5 Size Factor (non-linear pricing)

```python
def get_size_factor(area: float) -> float:
    if area < 10:   return 1.30   # small job overhead
    if area < 25:   return 1.10
    if area < 50:   return 1.00   # baseline
    if area < 100:  return 0.92
    return 0.85                   # economies of scale
```

### 3.6 Waste Factor & Minimum Cost

```python
WASTE_FACTOR = 0.05          # 5% added to all estimates
MINIMUM_PROJECT_COST = 500_000   # IDR — no job below this
```

### 3.7 Job Bundles (room = multiple jobs)

```python
JOB_BUNDLE = {
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
        "full":   ["painting", "electrical", "ceramic"],
    },
}
```

---

## 4. Assumption Engine (Source of Truth)

Every unknown field must be:
1. Assigned a default value
2. Tagged with source, confidence, impact, and needs_clarification
3. Shown to the user
4. Replaceable by user input

### 4.1 Assumption Structure

```python
{
    "area": {
        "value": 9,
        "source": "assumed",          # "confirmed" | "assumed" | "inferred"
        "confidence": 0.30,
        "impact": "high",             # "high" | "medium" | "low"
        "reason": "user said 'kecil'",
        "needs_clarification": True
    }
}
```

### 4.2 Impact Levels

| Field | Impact | Rationale |
|---|---|---|
| `area` | high | Linear effect on all costs |
| `job_type` | high | Determines entire formula |
| `location` | medium | ±30% effect |
| `quality` | medium | ±50% effect on materials |
| `scope` | medium | Determines job bundle |
| `description` | low | Context only |

### 4.3 Clarification Priority

```python
# Only ask top 1-2 fields, sorted by: impact × uncertainty
clarification_priority = impact_weight × (1 - confidence)

# Max 3 clarification attempts, then exit to best_effort mode
```

### 4.4 Hard Cap Rule

```python
# Critical fields not confirmed = confidence capped at 50%
CRITICAL_FIELDS = ["area", "job_type"]

if any field in CRITICAL_FIELDS is not confirmed:
    confidence = min(confidence, 0.50)
```

---

## 5. Confidence System (Source of Truth)

### 5.1 Calculation

```python
FIELD_WEIGHTS = {
    "area":     0.40,
    "job_type": 0.25,
    "location": 0.20,
    "quality":  0.15,
}

confidence = sum(weight for confirmed fields)
# Apply hard cap if critical fields unconfirmed
```

### 5.2 Human-readable Labels

| Score | Label | Output language |
|---|---|---|
| > 0.75 | Tinggi | "Estimasi cukup akurat" |
| 0.50–0.75 | Sedang | "Estimasi perlu beberapa asumsi" |
| < 0.50 | Rendah | "Estimasi kasar, banyak asumsi" |

### 5.3 Range Widening by Confidence

```python
if confidence < 0.50:
    min_cost *= 0.85
    max_cost *= 1.20
```

### 5.4 Output Rounding by Confidence

```python
if confidence > 0.70:
    # round to nearest 100k
    "Rp 8,3 – 11,7 juta"
else:
    # round to nearest 500k or 1M
    "Rp 8 – 12 juta"
```

---

## 6. Input Processing Pipeline (Source of Truth)

```
[ Raw User Input ]
        ↓
[ 1. Input Normalization ]
   - "3x6m" → 18
   - "sekitar 20" → 20
   - "15-20an" → 17.5
   - typo correction (fuzzy match)
        ↓
[ 2. Conflict Resolution ]
   - explicit value overrides assumption
   - log and show conflict to user
        ↓
[ 3. Pre-parser (regex + keyword) ]
   - extract: area, job_type, location, quality
   - detect: multi-job, room bundles, scope hints
        ↓
[ 4. Assumption Engine ]
   - fill missing fields with defaults
   - tag source, confidence, impact
        ↓
[ 5. LLM Layer (Ollama llama3.2) ]  ← Phase 3, not yet built
   - clarify ambiguous intent
   - normalize messy phrasing
   - extract structured data
   - NEVER guess — detect missing → trigger clarification
        ↓
[ 6. Validation Layer ]
   - parse LLM JSON output
   - retry up to 2x on failure
   - fallback to rule-based if LLM fails
        ↓
[ 7. Pricing Engine ]
   - apply all multipliers
   - calculate min/max range
   - apply minimum cost
        ↓
[ 8. Sanity Check ]
   - underbudget warning
   - overkill budget warning
   - unusual area warning
        ↓
[ 9. Response Builder ]
   - pre-framing statement
   - range output (rounded by confidence)
   - breakdown per job
   - assumptions (shown + editable)
   - confidence label
   - explanation trail
   - warnings
```

---

## 7. Output Structure (Source of Truth)

### 7.1 API Response Shape

```json
{
  "project_name": "Renovasi Rumah Pak Budi",
  "mode": "standard",
  "confidence": {
    "score": 0.72,
    "label": "Sedang",
    "message": "Estimasi perlu beberapa asumsi"
  },
  "pre_framing": "Banyak yang mengira renovasi kamar mandi hanya 3–5 juta. Berdasarkan harga material & tukang saat ini...",
  "total_range": {
    "min": 8000000,
    "max": 12000000,
    "display": "Rp 8 – 12 juta"
  },
  "breakdown": [
    {
      "job_type": "ceramic",
      "area": 9,
      "min": 5000000,
      "max": 7500000
    },
    {
      "job_type": "plumbing",
      "area": 9,
      "min": 3000000,
      "max": 4500000
    }
  ],
  "assumptions": [
    {
      "field": "area",
      "value": 9,
      "source": "assumed",
      "reason": "User menyebut 'kecil'",
      "impact": "high",
      "editable": true
    }
  ],
  "explanation": [
    "Luas: 9m² (diasumsikan dari 'kecil')",
    "Harga dasar keramik standar: Rp 120–180rb/m²",
    "Faktor lokasi Jakarta: ×1.3",
    "Waste factor: 5%"
  ],
  "warnings": [
    {
      "type": "low_confidence_area",
      "severity": "warning",
      "message": "Luas belum dikonfirmasi — estimasi bisa berubah signifikan"
    }
  ],
  "disclaimer": "Estimasi ini berdasarkan harga pasar rata-rata. Harga aktual dapat berbeda tergantung kondisi lapangan dan negosiasi dengan kontraktor."
}
```

### 7.2 Modes

| Mode | Trigger | Behavior |
|---|---|---|
| `standard` | confidence ≥ 0.5 | Normal output |
| `best_effort` | confidence < 0.5 OR 3 failed clarifications | Wide range, heavy disclaimer |
| `incomplete` | critical fields missing | Ask clarification before output |

---

## 8. Tech Stack (Source of Truth)

| Layer | Technology | Notes |
|---|---|---|
| Backend | Python 3.13 + FastAPI | Structured, modular |
| Database | SQLite → PostgreSQL | MVP → Production |
| ORM | SQLModel | SQLAlchemy + Pydantic combined |
| AI Layer | Ollama + llama3.2 | Active |
| Auth/Security | middleware/auth + slowapi | Active |
| Frontend | Laravel Blade + Tailwind CSS | Converted from Lovable prototype |
| Config | pydantic-settings + .env | Per-environment |
| Testing | pytest + httpx | In-memory SQLite for tests |
| Deployment | Docker + docker-compose | Phase 4 complete |

---

## 9. Build Phases (Source of Truth)

### ✅ Phase 1 — Code Quality
- Virtual env, .env, config.py, logging, .gitignore

### ✅ Phase 2 — Tests & Error Handling
- pytest, httpx, custom 422 handler, consistent error shape

### ✅ Phase 3 — Real Database
- SQLite, SQLModel, job_types table, CRUD endpoints, seeder

### ✅ Phase 4 — Docker & Deployment
- Dockerfile, docker-compose, lifespan pattern, .env.production

### ✅ Phase 5 — Estimation Engine (NO AI YET)
- Input normalization
- Pre-parser (regex + keyword)
- Job bundles + scope detection
- Pricing engine (range, multipliers, size factor)
- Assumption engine
- Sanity check layer
- Response builder

### ✅ Phase 6 — Trust Layer
- Confidence system
- Range rounding by confidence
- Pre-framing statements
- Explanation trail
- Editable assumptions (UI)

### ✅ Phase 7 — AI Layer (Ollama)
- LLM integration for messy input
- Validation + retry logic
- Clarification loop
- Fallback to rule-based

### ✅ Phase 8 — Production Hardening
- PostgreSQL migration
- Authentication (JWT)
- CORS configuration
- Real market data validation

---

## 10. Critical Design Decisions (Source of Truth)

| Decision | Rationale |
|---|---|
| Range output, not single number | Honesty > false precision |
| Rule-based BEFORE LLM | Stability > intelligence |
| Assumption engine is active, not passive | User must be able to correct assumptions |
| Confidence has hard cap on critical fields | Prevents misleading high confidence |
| Regional multiplier, not per-city rate | We don't have validated city data yet |
| base_rate is a range, not a single number | We don't have validated field data yet |
| Multi-job via bundles | Real renovations involve multiple trades |
| Scope clarifier is mandatory | Prevents scope mismatch = #1 trust killer |
| Pre-framing before numbers | Expectation management > explanation |
| AI is Phase 7, not Phase 1 | Accuracy before intelligence |

---

## 11. Known Limitations (Source of Truth)

- Base rates are market estimates, not field-validated
- Regional multipliers are approximations
- No real user data yet — synthetic logic only
- No feedback loop from contractors
- Frontend not yet connected to this backend

---

## 12. What "Done" Looks Like for MVP

A contractor looks at the output and says:

> *"Angkanya masuk akal, dan aku ngerti dari mana asumsinya."*

Not:

> *"Wah canggih banget AI-nya."*

Trust > Intelligence. Always.

---

## 13. Available Endpoints

### Estimation
- `POST /api/estimate` (v1 basic)
- `POST /api/estimate/v2` (v2 full RAB)
- `POST /api/estimate/v2/refine` (Refine estimate)
- `POST /api/estimate/v2/ai` (AI estimate)

### System
- `GET /api/health`

### Job Types
- `GET /api/job-types`
- `POST /api/job-types`
- `PUT /api/job-types/{name}`
- `DELETE /api/job-types/{name}`
