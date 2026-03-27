# CarvAcoustic — Geometry Service

Stateless FastAPI service that receives canonical config objects and returns geometry artifacts.

- No G-code output
- No acoustic calculations
- Deterministic: same config → same output

## Milestone status

| Milestone | Status | Description |
|-----------|--------|-------------|
| A | Done | Scaffolding — stubs only |
| B | Pending | `generate` + `validate` |
| C | Pending | `layout` + `export` |

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
cd geometry
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8001
```

API docs: http://localhost:8001/docs

## Endpoints

| Method | Path | Milestone | Description |
|--------|------|-----------|-------------|
| GET | /health | A | Health check |
| POST | /generate | B | Run geometry pipeline |
| POST | /validate | B | Validate config |
| POST | /layout | C | Layout to sheets |
| POST | /export | C | Assemble export bundle |

## Authentication

All endpoints require `X-API-Key` header matching `API_KEY` in `.env`.
The web app sends this key from `GEOMETRY_SERVICE_API_KEY` (server-side only).

## Architecture

```
app/
├── main.py         # FastAPI app + CORS
├── models.py       # Pydantic models (mirrors shared/config-schema.json)
├── config.py       # Settings from .env
├── auth.py         # API key dependency
└── routers/
    ├── generate.py # POST /generate — geometry pipeline
    ├── validate.py # POST /validate — validation engine
    ├── layout.py   # POST /layout  — sheet nesting
    └── export.py   # POST /export  — bundle assembly
```
