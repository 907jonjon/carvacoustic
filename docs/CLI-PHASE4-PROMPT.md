# Claude CLI Prompt — Phase 4: Benchmarks + Hardening

**Copy-paste everything below the line into Claude Code CLI. Phases 1 and 2 must be complete and passing tests first.**

---

## Task

Add benchmarks, regression fixtures, result validation, and production hardening for CarvAcoustic's nesting engine. This is Phase 4 (final) of 3 implementation phases.

## Instructions

1. Verify Phases 1 and 2 are complete — run: `cd geometry && python -m pytest tests/test_nesting*.py -v`
   All tests must pass before proceeding.

2. Read these files first (in order):
   - `docs/carvacoustic_nesting_build_document.md` — sections 2.10–2.15 and 2.17
   - `docs/NESTING-PHASE4-BENCH.md` — the detailed implementation spec for this phase
   - `geometry/app/nesting/models.py` — NestJob, NestResult
   - `geometry/app/nesting/solver/solve.py` — solve_nest() entry point
   - `geometry/app/nesting/geometry/validate.py` — existing geometry validation

3. Create the package structure exactly as specified in NESTING-PHASE4-BENCH.md:
   ```
   geometry/app/nesting/
       bench/
           __init__.py
           datasets.py
           runner.py
           reports.py
       solver/
           validate_result.py   (may already exist from Phase 2 — extend it)
           result_schema.py     (may already exist from Phase 2 — extend it)
   geometry/tests/
       test_nesting_regression.py
       fixtures/
           nesting/
               simple_convex.json
               concave_slats.json
               grain_locked.json
               mirror_forbidden.json
               narrow_clearance.json
               high_vertex.json
               backing_with_slots.json
   ```

4. Implement every module according to the spec. Key requirements:
   - `solver/validate_result.py`: public `validate_nest(job, result) -> ValidationReport` — wraps geometry/validate.py, adds summary stats (total_parts_placed, sheets_used, avg_utilization, all_valid bool), returns structured ValidationReport dataclass
   - `solver/result_schema.py`: Pydantic models for JSON-serializable output — NestResultSchema, SheetSchema, PlacementSchema with `from_nest_result(job, result)` class method
   - `bench/datasets.py`: `load_internal_dataset(name) -> list[NestJob]` loads from fixtures/nesting/*.json, `generate_synthetic_dataset(n_parts, complexity) -> NestJob` creates random convex/concave polygons for stress testing
   - `bench/runner.py`: `BenchmarkResult` dataclass (job_name, mode, sheets_used, utilization, solve_time_ms, valid), `run_benchmark(jobs, modes) -> list[BenchmarkResult]`
   - `bench/reports.py`: `generate_report(results) -> str` markdown table, `compare_reports(baseline, current) -> str` shows regressions/improvements with delta columns

5. Create regression fixtures:
   - Each fixture is a JSON file with: `{"name": str, "parts": [{"part_id": str, "polygon_wkt": str, "part_type": str}], "config": {"sheet_width": float, "sheet_height": float, "clearance": float, "edge_margin": float, "rotation_mode": str, "preserve_grain": bool}}`
   - Generate 7 fixtures covering: simple convex slats, concave profiles, grain-locked rotation, mirror-forbidden, narrow clearance (0.5mm), high vertex count (500+ per part), backing boards with interior slots
   - Use real-ish polygon dimensions: slats ~40-200mm wide, 300-600mm tall, sheets 1220x2440mm

6. Write tests:
   - `test_nesting_regression.py`: loads each fixture, runs solve_nest() in balanced mode, asserts all parts placed + valid result + utilization > 0. Snapshot the sheet count — if a future change increases sheets for any fixture, the test fails (regression guard)
   - Add any additional hardening tests from the spec

7. Run a benchmark: add a `if __name__ == "__main__"` block to runner.py that loads all internal datasets, runs all three modes, and prints the report. Run it: `cd geometry && python -m geometry.app.nesting.bench.runner`

8. Run all tests: `cd geometry && python -m pytest tests/ -v`

9. Commit with message: `feat(nesting): add Phase 4 benchmarks, regression fixtures, and validation API`

## Acceptance Criteria
- All regression fixtures load and solve without errors
- `validate_nest()` correctly identifies valid and invalid results
- `result_schema.py` produces valid JSON from NestResult
- Benchmark runner completes for all modes and prints markdown report
- All existing tests still pass (no regressions)
- Regression test snapshots are committed (sheet counts per fixture per mode)
- Deliverables checklist from build document §2.17 is fully met
