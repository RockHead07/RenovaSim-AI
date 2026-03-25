# RenovaSim AI — MVP Estimation API

A clean, modular FastAPI backend for calculating renovation cost estimates.

---

## Project Structure

```
renovasim-ai/
│
├── app/
│   ├── main.py               ← FastAPI app & router registration
│   │
│   ├── api/
│   │   └── estimate.py       ← POST /api/estimate route (thin, no logic)
│   │
│   ├── services/
│   │   └── estimator.py      ← Business logic: cost calculation
│   │
│   ├── data/
│   │   └── cost_data.py      ← Hardcoded unit cost table
│   │
│   ├── schemas/
│   │   └── estimate_schema.py ← Pydantic request / response models
│   │
│   └── models/
│       └── (reserved for future AI models)
│
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the server

```bash
uvicorn app.main:app --reload
```

### 3. Open interactive docs

```
http://127.0.0.1:8000/docs
```

---

## API Reference

### `POST /api/estimate`

Calculate the renovation cost for a given job type and area.

**Request body**

```json
{
  "job_type": "painting",
  "area": 50
}
```

| Field      | Type   | Constraint    | Description                               |
|------------|--------|---------------|-------------------------------------------|
| `job_type` | string | required      | `painting` / `ceramic` / `roof`           |
| `area`     | float  | > 0, required | Area in square metres                     |

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

---

## Supported Job Types & Unit Costs (per m²)

| Job Type  | Material (IDR) | Labor (IDR) |
|-----------|---------------|-------------|
| painting  | 25,000        | 15,000      |
| ceramic   | 120,000       | 80,000      |
| roof      | 150,000       | 100,000     |

---

## Design Principles

- **Routes are thin** — no business logic inside route handlers
- **Services hold logic** — `estimator.py` owns all calculations
- **Data is isolated** — `cost_data.py` can be swapped for a DB later
- **Schemas validate strictly** — Pydantic rejects invalid input early
- **Models folder is reserved** — ready for ML integration in future phases

---

## Extending Later

| What to add             | Where                              |
|-------------------------|------------------------------------|
| New job types           | `app/data/cost_data.py`            |
| Database persistence    | `app/data/` + new DB module        |
| ML price prediction     | `app/models/` + update `estimator` |
| Auth / API keys         | FastAPI middleware in `main.py`    |
| More endpoints          | New files in `app/api/`            |
