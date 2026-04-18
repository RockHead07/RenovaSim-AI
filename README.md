# RenovaSim AI — Backend API

> Location-aware, AI-assisted renovation cost estimation platform (RAB generator) for the Indonesian market.  
> Read `SYSTEM_SPEC.md` for full architecture decisions.  
> Read `AI_CONTEXT.md` to onboard any AI assistant to this project.

---

## What This Is

A FastAPI backend that powers renovation cost estimation (RAB) based on:
- Job type (painting, ceramic, electrical, etc.)
- Location (city-based labor rate adjustment)
- Material quality (Ekonomi / Standar / Premium)
- Area (m²)
- Free-text description (AI-processed in Phase 7)

---

## Project Structure

```
renovasim-ai/
│
├── app/
│   ├── main.py                    ← FastAPI app, lifespan, error handlers
│   ├── config.py                  ← Settings via pydantic-settings + .env
│   │
│   ├── api/
│   │   ├── estimate.py            ← POST /api/estimate
│   │   └── job_types.py           ← CRUD /api/job-types
│   │
│   ├── services/
│   │   ├── estimator.py           ← Estimation logic (reads from DB)
│   │   └── job_type_service.py    ← Job type CRUD logic
│   │
│   ├── schemas/
│   │   ├── estimate_schema.py     ← Request/response models for estimation
│   │   └── job_type_schema.py     ← Request/response models for job types
│   │
│   ├── models/
│   │   └── job_type.py            ← SQLModel DB table definition
│   │
│   ├── db/
│   │   ├── session.py             ← DB engine, get_session dependency
│   │   └── seeder.py              ← Seeds default job types on startup
│   │
│   └── data/
│       └── cost_data.py           ← Default cost table (used by seeder)
│
├── tests/
│   ├── conftest.py                ← Shared test client + in-memory DB
│   └── test_estimate.py           ← 13 tests (happy + sad path)
│
├── SYSTEM_SPEC.md                 ← Source of truth for architecture
├── AI_CONTEXT.md                  ← Paste this to onboard any AI assistant
├── Dockerfile
├── docker-compose.yml
├── .env                           ← Local config (never commit)
├── .env.example                   ← Template for new devs
├── .env.production                ← Production config
├── .gitignore
└── requirements.txt
```

---

## Quick Start

### Option A — Local (Python)

**Prerequisites:** Python 3.13

```bash
# 1. Install dependencies
py -3.13 -m pip install -r requirements.txt

# 2. Run the server
py -3.13 -m uvicorn app.main:app --reload

# 3. Open docs
http://127.0.0.1:8000/docs
```

### Option B — Docker

**Prerequisites:** Docker Desktop running

```bash
# Build and run
docker compose up --build

# Run in background
docker compose up --build -d

# Stop
docker compose down
```

### Run Tests

```bash
py -3.13 -m pytest tests/ -v
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
APP_NAME="RenovaSim AI"
APP_VERSION="0.1.0"
APP_DEBUG=True
APP_ENV="development"
DATABASE_URL="sqlite:///./renovasim.db"
```

---

## API Reference

### Estimation

#### `POST /api/estimate`
Calculate renovation cost for a given job type and area.

**Request**
```json
{
  "job_type": "painting",
  "area": 50
}
```

**Response**
```json
{
  "job_type": "painting",
  "area": 50,
  "material_cost": 1250000,
  "labor_cost": 750000,
  "total_cost": 2000000
}
```

> ⚠️ This endpoint is Phase 3 (basic). Phase 5 will replace it with full RAB output including range, assumptions, confidence, and breakdown.

---

### Job Types (CRUD)

#### `GET /api/job-types`
List all supported job types and their unit prices.

#### `POST /api/job-types`
Add a new job type.
```json
{
  "name": "plumbing",
  "material_price": 90000,
  "labor_price": 60000
}
```

#### `PUT /api/job-types/{name}`
Update prices for an existing job type.
```json
{
  "material_price": 100000,
  "labor_price": 70000
}
```

#### `DELETE /api/job-types/{name}`
Remove a job type. Returns `204 No Content`.

---

## Default Job Types (seeded on startup)

| Job Type | Material (IDR/m²) | Labor (IDR/m²) |
|---|---|---|
| painting | 25,000 | 15,000 |
| ceramic | 120,000 | 80,000 |
| roof | 150,000 | 100,000 |

> These will be replaced by range-based pricing in Phase 5. See `SYSTEM_SPEC.md` section 3.2.

---

## Build Progress

| Phase | Description | Status |
|---|---|---|
| 1 | Code quality — .env, config, logging | ✅ Done |
| 2 | Tests & error handling | ✅ Done |
| 3 | SQLite database + CRUD endpoints | ✅ Done |
| 4 | Docker & deployment | ✅ Done |
| 5 | Full estimation engine (no AI) | 🔲 Next |
| 6 | Trust layer — confidence, framing, assumptions | 🔲 Upcoming |
| 7 | AI layer — Ollama + llama3.2 | 🔲 Upcoming |
| 8 | Production hardening — PostgreSQL, auth | 🔲 Upcoming |

---

## Design Principles

- **Routes are thin** — no logic inside route handlers
- **Services hold logic** — all business rules live in `services/`
- **One source of truth** — `SYSTEM_SPEC.md` governs all decisions
- **Rule-based before AI** — system works without LLM first
- **Range over single number** — honesty over false precision
- **Trust over intelligence** — explainability is the product

---

## For New Team Members

1. Read `SYSTEM_SPEC.md` — understand the architecture before touching code
2. Read `AI_CONTEXT.md` — paste this when using AI assistants
3. Run the project locally (Option A above)
4. Run tests — all 13 should pass
5. Check `/docs` — understand existing endpoints
6. Start on Phase 5 — see `SYSTEM_SPEC.md` section 9

---

## Contributing

- Follow the folder structure — do not put logic in routes
- Add tests for every new endpoint
- Update `SYSTEM_SPEC.md` if you make architecture decisions
- Use CSS variable classes in Blade/Tailwind — never hardcode hex values
