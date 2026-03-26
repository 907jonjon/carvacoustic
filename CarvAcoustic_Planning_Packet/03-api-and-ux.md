# 03 — API and UX

## Product surfaces

### Public
- `/` landing page
- `/docs` help and usage notes

### Authenticated app
- `/login`
- `/app`
- `/app/projects/new`
- `/app/projects/[id]`
- `/app/projects/[id]/edit`
- `/app/projects/[id]/exports`

## Workspace layout

### Left panel
- mode
- dimensions
- boundary
- pattern
- fabrication
- layout
- export settings

### Center panel
- SVG preview
- sheet preview toggle

### Right panel
- validation list
- save actions
- generate actions
- export actions

## Required editor sections
- setup
- pattern
- fabrication
- validation
- layout
- export

## UX rules
- Keep preview visible while editing.
- Separate config editing from validation output.
- Show last generated timestamp/version.
- Require explicit Generate / Validate / Export actions.
- Do not hide fabrication settings too deeply in phase 1.

## API endpoints

### Project CRUD
- `POST /api/projects`
- `GET /api/projects/:id`
- `PATCH /api/projects/:id`
- `POST /api/projects/:id/versions`

### Processing
- `POST /api/generate`
- `POST /api/validate`
- `POST /api/layout`
- `POST /api/export`

### Presets
- `GET /api/presets/materials`
- `POST /api/presets/materials`
- `GET /api/presets/tools`
- `POST /api/presets/tools`

## API contracts

### Create project
```json
{
  "name": "Lobby Wave Panel",
  "mode": "wall_art",
  "units": "in"
}
```

### Generate
```json
{
  "config": { "...": "canonical config object" }
}
```

### Standard error shape
```json
{
  "error": {
    "code": "boundary_invalid",
    "message": "Imported SVG contains self-intersecting outer loop"
  }
}
```

## Sync vs async
Phase 1:
- generate = sync
- validate = sync
- layout = sync
- export = sync if fast enough

Reserve async jobs later only if measured latency requires it.

## Vectric handoff contract
CarvAcoustic produces:
- clean vectors
- sheet files
- labels
- reference PDF
- manifest

Founder still does in Vectric:
- import
- job/material confirmation
- toolpath setup
- tabs/holds
- simulation
- post-processing
