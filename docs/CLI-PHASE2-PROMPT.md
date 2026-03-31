# Claude CLI Prompt — Phase 2: Search Engine + Constructive Solver

**Copy-paste everything below the line into Claude Code CLI. Phase 1 must be complete and passing tests first.**

---

## Task

Build the search engine and constructive solver for CarvAcoustic's nesting engine. This is Phase 2 of 3 and depends on the Phase 1 geometry foundation.

## Instructions

1. Verify Phase 1 is complete — run: `cd geometry && python -m pytest tests/test_nesting_geometry.py -v`
   If any tests fail, fix them before proceeding.

2. Read these files first (in order):
   - `docs/carvacoustic_nesting_build_document.md` — sections 2.6–2.13 and 2.16
   - `docs/NESTING-PHASE2-SEARCH.md` — the detailed implementation spec for this phase
   - `geometry/app/nesting/models.py` — NestJob, PartSpec, SheetState, Placement, NestResult (from Phase 1)
   - `geometry/app/nesting/geometry/collision.py` — collision checking API
   - `geometry/app/nesting/geometry/preferred_edges.py` — flat edge detection API
   - `geometry/app/nesting/geometry/sheet.py` — SheetState manager API
   - `geometry/app/nesting/geometry/transforms.py` — variant generation API
   - `geometry/app/geometry/layout.py` — existing FFD packer (becomes fallback)

3. Create the package structure exactly as specified in NESTING-PHASE2-SEARCH.md:
   ```
   geometry/app/nesting/
       search/
           __init__.py
           ordering.py
           candidates.py
           scoring.py
           constructive.py
           improve.py
           modes.py
       solver/
           __init__.py
           solve.py
           validate_result.py
           result_schema.py
   ```

4. Implement every module according to the spec. Key requirements:
   - `ordering.py`: generate N seeded part orderings (area-descending base, then shuffled variants with fixed random seeds for reproducibility)
   - `candidates.py`: three anchor strategies — boundary scan (sheet edges), flat-edge contact (align flat edges of new part against placed parts), generic contact (slide along placed part boundaries). Each returns candidate (x, y, variant_index) tuples
   - `scoring.py`: weighted scorer with ScoringWeights dataclass — contact_length (0.4), compactness (0.3), utilization (0.2), preferred_edge_bonus (0.1). Modes adjust these weights
   - `constructive.py`: main loop — for each part in order, generate candidates across all strategies, score each, pick best feasible placement (collision-free via Phase 1 geometry). If no placement fits current sheet, open new sheet
   - `improve.py`: post-construction improvement — compact (slide parts toward origin), reinsert_worst (remove lowest-scored N parts and re-place), small_swap (try swapping adjacent pairs)
   - `modes.py`: three presets over one shared solver — FAST (20 max candidates, 1 ordering, no improvement), BALANCED (60 candidates, 3 orderings, compact only), MAX_YIELD (100 candidates, 5 orderings, full improvement)
   - `solve.py`: top-level `solve_nest(job: NestJob) -> NestResult` that runs the mode specified in job config, picks best solution across orderings by total sheets then utilization

5. Wire into the pipeline with FFD fallback:
   - Modify `geometry/app/nesting/ingest.py` to add a `run_nesting(parts, config) -> LayoutResult` function that:
     1. Calls `prepare_nest_job(parts, config)`
     2. Calls `solve_nest(job)`
     3. Converts via `nest_result_to_layout_result(job, result)`
     4. On any exception, logs warning and falls back to `run_slat_layout(parts, config)` from the existing layout.py
   - Modify `geometry/app/geometry/pipeline.py` to import and call `run_nesting()` instead of `run_slat_layout()` directly. The fallback is inside run_nesting, so pipeline.py just swaps the call.

6. Write tests:
   - `geometry/tests/test_nesting_search.py` — unit tests for ordering, candidates, scoring (12 cases from spec)
   - `geometry/tests/test_nesting_solver.py` — integration tests for constructive loop and solve_nest (6 cases from spec)
   - `geometry/tests/test_nesting_integration.py` — end-to-end: slat_profiler output → run_nesting() → valid LayoutResult (4 cases from spec)

7. Run all nesting tests: `cd geometry && python -m pytest tests/test_nesting*.py -v`

8. Commit with message: `feat(nesting): add Phase 2 search engine and constructive solver`

## Acceptance Criteria
- All 22 test cases pass
- `solve_nest()` produces valid NestResult for all three modes (fast/balanced/max_yield)
- `run_nesting()` returns LayoutResult compatible with bundle.py and svg_export.py
- FFD fallback works when nesting engine throws
- pipeline.py calls run_nesting() instead of run_slat_layout()
- Deterministic results for same seed (reproducibility)
- Only these existing files are modified: `geometry/app/nesting/ingest.py`, `geometry/app/geometry/pipeline.py`
