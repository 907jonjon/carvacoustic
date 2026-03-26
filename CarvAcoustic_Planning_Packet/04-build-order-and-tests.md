# 04 — Build Order and Tests

## Build order
1. Create repo and docs folders
2. Define shared schemas
3. Scaffold Next.js app shell
4. Connect Supabase auth and project CRUD
5. Scaffold geometry service
6. Implement boundary normalization
7. Implement `wave_field`
8. Implement `contour_bands`
9. Implement `slat_rib`
10. Implement validation engine
11. Implement layout engine
12. Implement export bundle
13. Wire preview and editor UI
14. Run golden-sample tests
15. Refine errors, docs, and acceptance checks

## Milestones

### Milestone A
- app shell works
- auth works
- project CRUD works

### Milestone B
- first pattern family works end to end
- preview + validation + export works

### Milestone C
- all three pattern families implemented
- layout works
- Vectric import confirmed

### Milestone D
- persistence and versioning stable
- docs and acceptance tests complete

## Golden samples
- `wall_art_wave_panel`
- `cabinet_front_contour_panel`

For each sample:
1. generate preview
2. validate
3. layout
4. export
5. import into Vectric
6. confirm scale
7. confirm layers
8. confirm closed geometry

## Regression tests
- same config => same part count
- same config => same sheet count
- same config => same part IDs
- invalid SVG remains invalid
- warnings do not silently disappear between versions

## Founder acceptance checks
- can create project from blank
- can save and reload
- can edit and re-export
- can open DXF in Vectric without repair work
- can identify parts from labels/reference sheet

## Coding-agent rules
1. Stay inside phase-1 decorative scope.
2. Do not implement acoustic generation, intake UI, or calculations.
3. Keep geometry deterministic and stateless.
4. Keep web app and geometry service separate.
5. Do not generate G-code.
6. Do not add new pattern families without approval.
7. Prefer explicit contracts over clever abstractions.
8. Write tests before claiming milestone completion.

## Compact prompt pack

### Master prompt
Build CarvAcoustic phase 1 exactly to the governing spec.

Scope:
- web-first app on Next.js + Supabase
- separate Python FastAPI geometry service
- decorative wall art, cabinet front panel, architectural face panel modes
- pattern families: wave_field, contour_bands, slat_rib
- boundary inputs: rectangle, rounded rectangle, imported SVG
- generate, validate, layout, export
- export DXF, SVG, PDF reference, JSON manifest
- keep Vectric downstream
- no G-code
- no acoustic implementation

### Milestone prompt A
Implement repository scaffolding, shared schemas, Next.js app shell, Supabase auth, and project CRUD. Do not build geometry yet.

### Milestone prompt B
Implement geometry service boundary normalization and the first pattern family end to end, including preview, validation, and DXF/SVG export.

### Milestone prompt C
Implement the remaining pattern families, layout engine, reference PDF, JSON manifest, and project versioning. Validate against golden samples.

### Milestone prompt D
Harden UX, validation messages, docs, and founder acceptance tests. Do not expand scope.
