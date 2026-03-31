# Nesting Engine — Code Review Memo

## What was reused from the existing codebase

- **`CanonicalConfig`** and all its sub-models (`ConfigMaterial`, `ConfigTool`, `ConfigLayout`, `RotationMode`, `GrainDirection`) — referenced directly, not duplicated
- **`LayoutResult`, `SheetLayout`, `PartPlacement`** from `geometry/app/geometry/layout.py` — the nesting engine converts its output to these types via `nest_result_to_layout_result()` so the export pipeline (bundle.py, svg_export.py, dxf_export.py) works unchanged
- **`run_slat_layout()`** — kept intact as the FFD fallback inside `run_nesting()`
- **Slat profiler output format** — `ingest.py` accepts the exact dict format from `slat_profiler.py`
- **Shapely** — all geometry operations use Shapely 2.x (STRtree, prepared geometry, buffer, affinity transforms)

## What was added

### Phase 1: Geometry Foundation (`nesting/geometry/`)
- Polygon simplification, normalization, clearance inflation model
- Discrete transform enumeration respecting rotation_mode + grain lock + mirror constraints
- Preferred flat-edge detection for contact-biased placement
- STRtree-based spatial index for broad-phase collision pruning
- Exact overlap testing with Shapely prepared geometry
- Sheet state manager tracking placed parts and spatial index
- Independent post-solve validator (overlaps, bounds, transforms, part accounting)

### Phase 2: Search Engine (`nesting/search/` + `nesting/solver/`)
- Multiple seeded part orderings (area, extent, awkwardness, randomized)
- Three anchor-based candidate generators: boundary, flat-edge contact, generic contact
- Weighted placement scorer with configurable weights
- Constructive placement loop with sheet spill
- Improvement passes: compact, reinsert worst, small swap
- Mode presets: Fast (3 seeds, 20 candidates), Balanced (8/60), Max Yield (16/100)
- `solve_nest()` top-level entry that picks best solution across all orderings

### Phase 4: Benchmarks + Hardening (`nesting/bench/`)
- 7 regression fixtures covering convex, concave, grain-locked, mirror-forbidden, narrow clearance, high vertex, and backing board with slots
- Fixture loader and synthetic dataset generator
- Benchmark runner with metrics collection (sheets, utilization, runtime, validation)
- Markdown report generator with baseline comparison
- Public `validate_nest()` API returning structured ValidationReport
- Pydantic `NestResultOut` schema for JSON-serializable API output
- Sheet count snapshot regression guards

## What was intentionally deferred

- **V2 optimization layers** — ruin-and-recreate, cross-sheet moves, overlap-minimization (per build document §3.x)
- **No-fit polygon engine** — using direct Shapely intersection instead
- **Compiled backend** — pure Python only
- **Continuous free-angle rotation** — discrete angles only (0, 90, 180, 270)
- **Part-in-part / hole nesting** — not in V1 scope
- **Defect-aware stock** — all sheets assumed uniform
- **ESICUP public dataset integration** — synthetic + internal fixtures only for now
- **Worker-path execution** — all modes run inline

## Pipeline integration

`pipeline.py` now calls `run_nesting()` instead of `run_slat_layout()`. If the nesting engine fails for any reason, it automatically falls back to the FFD packer with a logged warning. No other existing files were modified.
