# RenovaSim AI — Context for AI Assistants

> Paste this entire file at the start of any AI conversation about RenovaSim.
> This is a wrapper around SYSTEM_SPEC.md — do not duplicate decisions here.
> If something conflicts with SYSTEM_SPEC.md, SYSTEM_SPEC.md wins.

---

## Who you are talking to

You are helping **RockHead07**, an independent developer building RenovaSim AI.

He works across:
- Backend: Python + FastAPI (primary active work)
- Frontend: Laravel Blade + Tailwind CSS (converted from Lovable prototype)
- DevOps: Docker

He prefers:
- Concise, direct responses
- No over-explanation unless asked
- Code first, explanation after
- Don't ask unnecessary clarifying questions — make a reasonable assumption and state it

---

## What RenovaSim AI is

A **location-aware, AI-assisted renovation cost estimation platform (RAB generator)** for the Indonesian market.

Target users: Indonesian homeowners who want a credible cost estimate before talking to a contractor.

It is a **decision-support SaaS tool** — not a marketplace, not a booking platform.

Core promise to user:
> "Here is a credible, explainable renovation cost estimate — and here is exactly how we calculated it."

---

## Current state of the project

### ✅ Already built (do not re-suggest these)
- FastAPI backend, modular structure (api/, services/, schemas/, models/, db/)
- SQLite database with SQLModel ORM
- Job types CRUD (GET, POST, PUT, DELETE /api/job-types)
- Basic estimate endpoint (POST /api/estimate) — currently rule-based, hardcoded math
- Config via pydantic-settings + .env
- Structured logging
- Custom 422 + 500 error handlers
- pytest test suite (13 tests, all passing)
- Docker + docker-compose deployment
- Lifespan pattern (not deprecated on_event)
- DB seeder for default job types
- Normalizer, parser, assumption engine, pricing engine, sanity check, response builder
- Refiner and LLM extractor (Ollama + llama3.2)
- Security: CORS, auth, rate limiting
- Health check endpoint
- All v2 endpoints (v2/estimate, v2/estimate/refine, v2/estimate/ai)

### 🔲 Not yet built (active development area)
- Frontend connection to this backend

---

## Architecture principles (never violate these)

1. **Rule-based BEFORE LLM** — the system must work without AI first
2. **Range output, not single number** — honesty over false precision
3. **Assumption engine is active** — every assumption is shown, tagged, and editable by user
4. **Confidence has hard cap** — if area or job_type unconfirmed, max confidence = 50%
5. **Scope clarifier is mandatory** — never skip it, it prevents #1 trust killer
6. **Pre-framing before numbers** — manage expectation before showing cost
7. **AI is Phase 7** — do not suggest AI shortcuts before the engine is solid
8. **One source of truth** — SYSTEM_SPEC.md is the law, not this file

---

## Estimation formula (simplified)

```python
final_cost = base_rate[job_type][quality]   # range, not single number
           × regional_multiplier[city]
           × job_complexity_multiplier[job_type]
           × size_factor(area)              # non-linear
           × (1 + waste_factor)             # 5%

total = max(minimum_project_cost, final_cost)  # IDR 500,000 minimum
```

Output is always a **range** (min–max), never a single number.

---

## Input processing pipeline (9 layers)

```
Raw Input
  → Normalization (3x6m → 18, typo correction)
  → Conflict resolution (explicit overrides assumption)
  → Pre-parser (regex + keyword)
  → Assumption engine (fill + tag missing fields)
  → LLM layer (Phase 7 — not yet)
  → Validation layer
  → Pricing engine
  → Sanity check
  → Response builder
```

---

## Key data structures

### Assumption field
```python
{
    "field_name": {
        "value": any,
        "source": "confirmed" | "assumed" | "inferred",
        "confidence": float,          # 0.0 – 1.0
        "impact": "high" | "medium" | "low",
        "reason": str,
        "needs_clarification": bool
    }
}
```

### API response shape
```json
{
  "mode": "standard | best_effort | incomplete",
  "confidence": { "score": 0.72, "label": "Sedang", "message": "..." },
  "pre_framing": "...",
  "total_range": { "min": 8000000, "max": 12000000, "display": "Rp 8 – 12 juta" },
  "breakdown": [...],
  "assumptions": [...],
  "explanation": [...],
  "warnings": [...],
  "disclaimer": "..."
}
```

---

## Tech stack (quick reference)

| Layer | Tech |
|---|---|
| Language | Python 3.13 |
| Framework | FastAPI 0.115.6 |
| ORM | SQLModel 0.0.22 |
| DB (MVP) | SQLite |
| DB (prod) | PostgreSQL (not yet) |
| AI | Ollama + llama3.2 (Phase 7) |
| Config | pydantic-settings |
| Testing | pytest + httpx |
| Container | Docker + docker-compose |
| Frontend | Laravel Blade + Tailwind |

---

## Design system (frontend reference)

```
Font body/UI:    PP Neue Montreal (weights: 100/400/500/700)
Font headings:   PP Editorial New (weights: 100/400/700)

CSS Variables:
  bg-background:   #2C2C2B
  text-foreground: #F5F5F5
  card:            #333331
  primary/olive:   #3B411E
  accent green:    #8BA023
  text-paragraph:  #838383
  border-border:   rgba(245,245,245,0.1)
```

> Always use CSS variable classes in Blade/Tailwind — never hardcode hex values.

---

## Folder structure (current)

```
renovasim-ai/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── estimate.py
│   │   ├── estimate_v2.py
│   │   ├── estimate_refine.py
│   │   ├── estimate_ai.py
│   │   ├── health.py
│   │   └── job_types.py
│   ├── middleware/
│   │   └── auth.py
│   ├── services/
│   │   ├── estimator.py
│   │   ├── job_type_service.py
│   │   ├── normalizer.py
│   │   ├── parser.py
│   │   ├── pricing.py
│   │   ├── assumption.py
│   │   ├── sanity.py
│   │   ├── response_builder.py
│   │   ├── refiner.py
│   │   └── llm_extractor.py
│   ├── schemas/
│   │   ├── estimate_schema.py
│   │   └── job_type_schema.py
│   ├── models/
│   │   └── job_type.py
│   ├── db/
│   │   ├── session.py
│   │   └── seeder.py
│   └── data/
│       ├── cost_data.py
│       ├── pricing_data.py
│       └── job_bundles.py
├── tests/
│   ├── conftest.py
│   └── test_estimate.py
├── SYSTEM_SPEC.md    ← source of truth
├── AI_CONTEXT.md     ← this file
├── README.md         ← how to run
├── Dockerfile
├── docker-compose.yml
├── .env
├── .env.production
└── requirements.txt
```

---

## What to help with next (current priority)

The backend is complete — next priority is connecting the Laravel frontend to this API.

---

## How to run the project

```bash
# Without Docker
py -3.13 -m uvicorn app.main:app --reload

# With Docker
docker compose up --build

# Run tests
py -3.13 -m pytest tests/ -v

# API docs
http://127.0.0.1:8000/docs
```

---

## Critical reminder for AI assistants

> The goal of RenovaSim is not to look smart.
> The goal is to be **trusted**.
>
> A contractor looking at the output should say:
> *"Angkanya masuk akal, dan aku ngerti dari mana asumsinya."*
>
> Not: *"Wah canggih banget AI-nya."*
>
> **Trust > Intelligence. Always.**
