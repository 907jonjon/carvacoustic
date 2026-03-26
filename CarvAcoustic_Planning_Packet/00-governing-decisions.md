# 00 — Governing Decisions

## Canonical name
- Product: CarvAcoustic
- Domain: carvacoustic.com

## Phase 1 scope
Build only:
- decorative wall art
- decorative cabinet/front panels
- decorative architectural face panels

Keep Vectric downstream for:
- toolpaths
- machine setup
- simulation
- post-processing

## Phase 1 deliverables
- web app shell
- auth + dashboard
- project create/edit/save/load
- decorative geometry generation
- manufacturability validation
- sheet layout
- export package
- Vectric-friendly DXF/SVG/PDF/JSON output

## Phase 1 non-goals
Do not build:
- direct G-code
- full CAM replacement
- acoustic generation logic
- acoustic intake UI
- cloud suspension generation
- manufacturing operations
- packaging / shipping logic
- marketing flows

## Approved phase order
1. Product definition and setup
2. Decorative workflow proof
3. Decorative hardening
4. Acoustic intake/schema prep
5. Acoustic implementation later

## Gate 1 proof criteria
A pass requires:
- one valid wall-art project
- one valid cabinet/front-panel project
- clean Vectric import
- useful nested output
- save/load/versioning works
- core validation catches common failures

## Coding rules
1. Build only approved phase-1 scope.
2. Keep web app and geometry service separate.
3. Use config schema as source of truth.
4. Keep geometry deterministic.
5. Do not add extra pattern families without approval.
6. Do not blur decorative and acoustic modes.
7. Do not replace Vectric in phase 1.
8. Every feature must map to a named use case and phase.
