# Claude CLI Prompt — Phase 1: Nesting Geometry Foundation

**Copy-paste everything below the line into Claude Code CLI.**

---

## Task

Build the geometry foundation for CarvAcoustic's nesting engine. This is Phase 1 of 3. Read the full spec before writing any code.

## Instructions

1. Read these files first (in order):
   - `docs/carvacoustic_nesting_build_document.md` — the master build document, sections 2.1–2.8 and 2.16
   - `docs/NESTING-PHASE1-GEOMETRY.md` — the detailed implementation spec for this phase
   - `geometry/app/models.py` — existing config models you must reference (DO NOT recreate)
   - `geometry/app/geometry/layout.py` — existing FFD packer and LayoutResult/SheetLayout/PartPlacement dataclasses you must be compatible with
   - `geometry/app/geometry/slat_profiler.py` — the slat polygon output format your ingest.py must accept

2. Create the package structure exactly as specified in NESTING-PHASE1-GEOMETRY.md:
   ```
   geometry/app/nesting/
       __init__.py
       models.py
       ingest.py
       geometry/
           __init__.py
           flatten.py
           normalize.py
           offsets.py
           transforms.py
           preferred_edges.py
           collision.py
           spatial_hash.py
           sheet.py
           validate.py
   ```

3. Implement every module according to the spec. Key requirements:
   - `models.py`: NestJob, PartSpec, TransformSpec, VariantGeom, SheetSpec, Placement, SheetState, SolutionState, NestResult — use dataclasses, not Pydantic
   - `ingest.py`: `prepare_nest_job(parts, config) -> NestJob` converts slat_profiler output + CanonicalConfig into a NestJob. Also `nest_result_to_layout_result(job, result) -> LayoutResult` bridge function
   - `geometry/offsets.py`: inflate parts by `clearance/2`, contract sheets by `edge_margin + clearance/2` using Shapely buffer()
   - `geometry/transforms.py`: generate placement variants (original, rotated 90°, mirrored) filtered by rotation_mode + preserve_grain config
   - `geometry/preferred_edges.py`: detect flat edges on parts for contact-biased placement
   - `geometry/collision.py`: Shapely STRtree-based collision checking
   - `geometry/spatial_hash.py`: grid-based spatial index for fast candidate filtering
   - `geometry/sheet.py`: SheetState manager — tracks placed parts, available space, occupied area
   - `geometry/validate.py`: post-placement validation (no overlaps, within sheet bounds, clearance respected)

4. Write tests in `geometry/tests/test_nesting_geometry.py` covering the 16 test cases listed in the spec document.

5. Run all tests and make sure they pass: `cd geometry && python -m pytest tests/test_nesting_geometry.py -v`

6. Do NOT modify any existing files outside the new `nesting/` package. The bridge function in ingest.py is the only integration point — do not wire it into pipeline.py yet.

7. Commit with message: `feat(nesting): add Phase 1 geometry foundation for nesting engine`

## Acceptance Criteria
- All 16 test cases pass
- `prepare_nest_job()` accepts real slat_profiler output format
- `nest_result_to_layout_result()` returns a valid LayoutResult compatible with bundle.py
- No modifications to existing files
- All Shapely operations use Y-up coordinate system consistently
