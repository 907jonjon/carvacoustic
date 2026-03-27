# CarvAcoustic

Web-first decorative panel design tool. Generates Vectric-ready DXF/SVG/PDF output for wall art, cabinet front panels, and architectural face panels.

## Repository layout

```
carvacoustic/
├── web/                  # Next.js 14 front-end + API routes
├── geometry/             # Python FastAPI geometry service
├── supabase/             # Database migrations and seed data
├── shared/               # Canonical config schema and TypeScript types
└── CarvAcoustic_Planning_Packet/   # Governing spec and planning docs
```

## Phase 1 scope

- Decorative wall art
- Decorative cabinet/front panels
- Decorative architectural face panels

Pattern families: `wave_field`, `contour_bands`, `slat_rib`

Exports: DXF, SVG, PDF reference, JSON manifest

Vectric handles all toolpaths, simulation, and post-processing downstream.

## Non-goals (phase 1)

- No G-code generation
- No acoustic calculations
- No acoustic intake UI
- No full CAM replacement

## Milestones

| Milestone | Status | Description |
|-----------|--------|-------------|
| A | In progress | Repo scaffold, auth, project CRUD |
| B | Pending | First pattern family end to end |
| C | Pending | All pattern families, layout, export |
| D | Pending | Hardening, docs, acceptance tests |

## Setup

See `web/README.md` and `geometry/README.md` for service-specific setup instructions.

### Quick start

```bash
# Web app
cd web
cp .env.local.example .env.local
# Fill in NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY
npm install
npm run dev

# Geometry service
cd geometry
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8001
```

## Spec

See `CarvAcoustic_Planning_Packet/` for governing decisions, schema contracts, geometry spec, API/UX spec, and build order.
