# CarvAcoustic Nesting Engine

True irregular polygon nesting for CarvAcoustic slat panels, replacing the FFD row-packing algorithm.

## Solver Flow

```
slat_profiler output + CanonicalConfig
        │
        ▼
   ingest.py: prepare_nest_job()
        │
        ▼
   geometry pipeline:
     flatten → normalize → offsets → transforms → preferred_edges
        │
        ▼
   search pipeline:
     ordering → candidates → scoring → constructive → improve
        │
        ▼
   solver/solve.py: solve_nest()
        │
        ▼
   geometry/validate.py: validate_solution()
        │
        ▼
   ingest.py: nest_result_to_layout_result() → LayoutResult
```

## Entry Points

- **`run_nesting(parts, config)`** — end-to-end, returns `LayoutResult`, falls back to FFD on failure
- **`solve_nest(job, mode, seed)`** — lower-level, returns `NestResult`
- **`validate_nest(job, result)`** — independent validation, returns `ValidationReport`

## Modes

All three modes use the same solver with different effort budgets:

| Mode | Seeds | Max Candidates | Improvement | Use Case |
|------|-------|---------------|-------------|----------|
| fast | 3 | 20 | compact only | Interactive preview |
| balanced | 8 | 60 | compact + reinsert + swap | Default production |
| max_yield | 16 | 100 | deep reinsert + swap | Premium / deliberate |

## Scoring Weights

Edit `search/scoring.py :: ScoringWeights` to tune placement quality:

- `envelope_growth` (1.0) — penalty for expanding used area
- `max_x_growth` (0.5) — penalty for rightward expansion
- `max_y_growth` (0.5) — penalty for upward expansion
- `contact_length` (-0.8) — bonus for flush contact
- `preferred_edge` (-0.6) — bonus for flat-edge alignment

Lower total score = better placement.

## Running Benchmarks

```bash
cd geometry
python3 -m app.nesting.bench.runner
```

This loads all fixture datasets plus synthetic ones, runs all three modes, and prints a markdown report.

## Adding a Benchmark Dataset

1. Create a JSON file in `tests/fixtures/nesting/`:
   ```json
   {
     "sheet": {"width": 96, "height": 48, "edge_margin": 0.75, "grain_axis": "x"},
     "clearance": 0.125,
     "parts": [
       {"part_id": "S001", "polygon_wkt": "POLYGON ((...))","quantity": 1,
        "grain_locked": false, "allow_mirror": false, "allowed_angles": [0, 90]}
     ],
     "expected": {"max_sheets": 1, "min_utilization": 0.01}
   }
   ```
2. Add the fixture name to `FIXTURES` and `SHEET_SNAPSHOTS` in `test_nesting_regression.py`

## Package Structure

```
nesting/
  models.py         — NestJob, PartSpec, Placement, NestResult, SolutionState
  ingest.py         — prepare_nest_job(), nest_result_to_layout_result(), run_nesting()
  geometry/         — Phase 1: polygon preprocessing, collision, validation
    flatten.py, normalize.py, offsets.py, transforms.py,
    preferred_edges.py, collision.py, spatial_hash.py, sheet.py, validate.py
  search/           — Phase 2: constructive solver
    ordering.py, candidates.py, scoring.py, constructive.py, improve.py, modes.py
  solver/           — Phase 2+4: top-level entry points
    solve.py, validate_result.py, result_schema.py
  bench/            — Phase 4: benchmarks
    datasets.py, runner.py, reports.py
```
