# CarvAcoustic

Web-first decorative panel design tool. Generates Vectric-ready DXF/SVG/PDF output
for wall art, cabinet front panels, and architectural face panels.

## Phase 1 scope

- Decorative wall art, cabinet front panels, architectural face panels
- Pattern families: `wave_field`, `contour_bands`, `slat_rib`
- Sheet layout with optional 90° rotation and multi-sheet spill
- Export bundle: DXF (5 layers), SVG, reference PDF, JSON manifest

**Non-goals (phase 1):** no G-code, no acoustic calculations, no acoustic intake UI.
Vectric handles all toolpaths, simulation, and post-processing downstream.

## Repository layout

```
carvacoustic/
├── web/                  # Next.js 14 front-end + API proxy routes
├── geometry/             # Python FastAPI geometry service
├── supabase/             # Database migrations + seed data
├── shared/               # Canonical config schema (JSON Schema v7) + TypeScript types
└── CarvAcoustic_Planning_Packet/   # Governing spec and planning docs
```

## Quick start

### Prerequisites

- Node.js 18+
- Python 3.11+
- A Supabase project (free tier is fine)

### 1 — Clone and configure

```bash
git clone <repo>
cd carvacoustic
```

Create `web/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
GEOMETRY_SERVICE_URL=http://localhost:8001
GEOMETRY_SERVICE_API_KEY=dev-secret
```

Create `geometry/.env` (optional — defaults work for local dev):

```env
API_KEY=dev-secret
```

### 2 — Run the Supabase migration

In your Supabase dashboard → SQL editor, run:

```sql
-- paste contents of supabase/migrations/001_initial.sql
-- then paste contents of supabase/seed.sql
```

Or with the Supabase CLI:

```bash
supabase db push
```

### 3 — Start the geometry service

```bash
cd geometry
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8001
```

Verify: `http://localhost:8001/health` → `{"status":"ok"}`

### 4 — Start the web app

```bash
cd web
npm install
npm run dev
```

Open `http://localhost:3000`.

## Billing (future launch)

Stripe-based Pro plan billing is planned but not yet wired. The `.env.example`
includes placeholder keys (`STRIPE_SECRET_KEY`, `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`,
`STRIPE_WEBHOOK_SECRET`, `STRIPE_PRO_PRICE_ID_MONTHLY`, `STRIPE_PRO_PRICE_ID_YEARLY`).
These are not required for local development or the current free-preview launch.

## Running tests

```bash
cd geometry
source .venv/bin/activate
pytest tests/ -v
```

51 tests covering regression, golden samples, validation rules, and API endpoints.

## Milestones

| Milestone | Status | Description |
|-----------|--------|-------------|
| A | ✅ Done | Repo scaffold, auth, project CRUD |
| B | ✅ Done | wave_field pattern, boundary normalization, preview, DXF/SVG export |
| C | ✅ Done | contour_bands, slat_rib, layout engine, reference PDF |
| D | ✅ Done | Tests, UX hardening, docs, founder acceptance checks |

## Founder acceptance checks

- [x] Create project from blank
- [x] Save and reload
- [x] Edit and re-export (immutable version checkpoints)
- [x] Open DXF in Vectric — all 5 spec layers present, $INSUNITS set, closed geometry
- [x] Identify parts from labels / reference PDF

## Spec

See `CarvAcoustic_Planning_Packet/` for governing decisions, schema contracts,
geometry spec, API/UX spec, and build order.
