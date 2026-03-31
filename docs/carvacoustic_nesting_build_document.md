# CarvAcoustic irregular nesting engine build document

**V1 production plan, V2 optimization plan, and implementation handoff for Claude**

- **Prepared for:** Product and engineering implementation planning
- **Date:** March 30, 2026
- **Recommended path:** V1 uses a Python true-polygon geometry engine plus a contact-biased constructive search. V2 keeps the same geometry core and adds deeper local search, overlap minimization, and an optional compiled backend adapter.

> **Use of this document:** Part 1 explains the problem, the state of the field, the options that were weighed, and why the recommended architecture is the right first build. Part 2 is the V1 implementation brief Claude can act on after reviewing the current codebase. Part 3 is the V2 expansion plan that preserves the same core interfaces while adding higher-yield optimization.

## Executive summary

CarvAcoustic should build its nesting engine as a two-layer system: a geometry engine that owns true-polygon preprocessing, offsets, transform legality, collision checks, and exact validation; and a search engine that owns part ordering, candidate generation, scoring, and improvement passes.

For V1, the right build is a Python-first solver that nests inflated polygons using a flat-edge-aware contact / bottom-left-fill style constructive heuristic, several diversified part orders, and a small reinsert or swap improvement pass. This is the best tradeoff between utilization, runtime, robustness, implementation risk, and cloud cost.

For V2, the engine should keep the exact same geometry contracts and add deeper neighborhoods: ruin-and-recreate, cross-sheet moves, overlap-minimization style local search, and optionally a selective no-fit-polygon cache or a compiled backend adapter for premium Max Yield mode. The key principle is to deepen optimization without rewriting the geometry foundation.

> **Opinionated recommendation:** Do not start with a full NFP-first GA, simulated annealing solver, or MIP-heavy online optimizer. Build the geometry core once, make V1 fast and manufacturable, and only then add V2 optimization layers.

| Area | V1 | V2 |
| --- | --- | --- |
| Primary goal | Fast, exact, manufacturable online nesting | Higher utilization on harder jobs and premium modes |
| Main algorithm | Contact-biased constructive search with small repair | Local-search expansion on top of V1 core |
| Geometry model | Flattened true polygons with clearance inflation | Same as V1 |
| User modes | Fast / Balanced / Max Yield on same core budgets | Same modes, but Max Yield can route to deeper search |
| What is deferred | Full robust NFP engine, GA/SA-first search, MIP online path | Only add compiled backend if Max Yield economics justify it |

## Part 1. Background, options weighed, and state of the field

This section is for a human reader first. It explains what is being built in V1 and V2, why the recommendation is not a purely academic optimum, and what tradeoffs are being accepted deliberately.

The constraints that matter most for CarvAcoustic are not just packing density. The product needs true irregular nesting on rectangular sheet goods, optional grain lock, mirroring constraints, user-controlled discrete rotations, variable clearance, and manufacturable output, while still feeling interactive in a cost-sensitive cloud environment.

### 1.1 What problem is being solved

The core problem is irregular 2D nesting: place many non-rectangular parts onto one or more rectangular sheets so that parts do not overlap, stay within sheet boundaries, respect rotation / mirroring / grain constraints, and waste as little material as practical.

This is harder than rectangle packing because feasibility depends on the full polygon boundary, not a bounding box. It is made more complex by curved edges, small concavities, user-controlled clearance, and the fact that many different part orders and orientations can produce very different results.

For CarvAcoustic, there is also a useful domain pattern: many parts have one meaningful flat edge and the remainder is curved. That is not just a geometric detail. It is an exploitable search bias.

### 1.2 State of the field in plain English

Irregular nesting remains dominated by heuristics in practical settings. Exact or mixed-integer approaches are academically important, but even recent exact-model work still characterizes heuristics as the only practical general approach for many real irregular nesting instances.

The field has historically mixed two separate jobs into one codebase problem: geometry and optimization. Geometry means deciding whether a transformed part is feasible at a location. Optimization means choosing the order, orientation, and placement decisions that lead to a good overall layout. Newer work has made the case that these should be decoupled, and modern open-source systems such as jagua-rs and sparrow reinforce that split.

Constructive heuristics such as bottom-left-fill remain relevant because they are fast and reliable enough to produce feasible layouts quickly. Their weakness is order sensitivity and local minima. Local search and overlap-minimization methods can improve yield, but they add engineering complexity and computation cost.

No-fit polygons remain a powerful geometry primitive, but building a fully robust NFP-heavy solver for arbitrary non-convex polygons with multiple discrete transforms and curve-derived geometry is a project of its own. It is often more valuable to use NFP selectively than to make it the entire architecture.

In other words: the right first build for a production SaaS is not the most theoretically ambitious solver. It is the solver that gives fast exact layouts, scales reasonably in the cloud, fails predictably, and creates a clean path to deeper search later.

### 1.3 What V1 and V2 actually are

| Version | Human description | Why it exists |
| --- | --- | --- |
| V1 | A production-feasible Python nesting engine that produces exact, manufacturable layouts quickly using true polygon geometry and a contact-biased constructive search. | Gets a solid online nesting experience into the product without overbuilding the optimizer. |
| V2 | A higher-effort optimization layer that keeps the same data model and geometry contracts, but applies deeper improvement passes and harder neighborhoods to raise material utilization. | Improves yield on difficult jobs and makes Max Yield mode meaningfully better without destabilizing the product. |

V1 is not a prototype. It is the first production engine. It must be exact, deterministic when seeded, manufacturable, and support Fast / Balanced / Max Yield modes on the same core.

V2 is not a rewrite. It is an optimization expansion. The geometry engine, transform model, validation contract, and result schema should stay stable.

### 1.4 Options that were weighed

The following families were considered against five criteria: solution quality, speed, implementation complexity, production robustness, and cloud compute cost.

| Family | Strengths | Weaknesses | Decision |
| --- | --- | --- | --- |
| Contact / BLF constructive heuristics | Fast, understandable, low cloud cost, easy to budget, good first feasible layouts | Order-sensitive, can leave yield on the table | Use as the V1 core |
| Guided local search / overlap minimization | Usually stronger yield on hard instances, good V2 path | More engineering, harder scoring / neighborhood design, more runtime | Use in V2 after V1 geometry is stable |
| NFP-first architecture | Powerful geometry primitive, can speed repeated pair reasoning | Robust general implementation is expensive, especially with non-convex + transformed + curve-derived parts | Use selectively later, not as the V1 architecture |
| Genetic algorithms | Can explore many orderings and orientations | Noisy, parameter-sensitive, expensive online, hard to make feel responsive | Do not use as the first production solver |
| Simulated annealing | Can escape local minima and compact tough layouts | Tuning-heavy and usually slower than needed for interactive SaaS | Research tool, not the first product path |
| Raster / occupancy / semi-discrete methods | Cheap overlap approximations and fast accelerators | Approximation error if used as source of truth | Possible accelerator later, but keep exact polygon validation |
| LP / MIP hybrids | Elegant formulations, useful for small exact subproblems | Not a practical online general solution for complex irregular jobs | Do not put on the online critical path |

### 1.5 Why the recommended architecture wins for this product

- It matches the economics of a web product. A constructive solver with exact geometry can give sub-second or low-single-digit-second results on many jobs without turning every request into a heavy search run.
- It matches the manufacturing risk profile. Exact polygon validation, clearance inflation, and explicit transform legality are more important than chasing an incremental few percent of utilization with a brittle search stack.
- It exploits the product’s shape distribution. A preferred-flat-edge bias is a good domain heuristic here because many parts expose one long nearly straight segment that often wants to sit against a sheet boundary or another flat edge.
- It preserves future optionality. By separating geometry from search, V2 can deepen search or swap geometry / collision internals without breaking API contracts or rewriting result validation.

### 1.6 Why the geometry/search split should be explicit

The geometry engine should answer the question: 'Is this transformed part feasible here, and if not, why not?' It owns curve flattening, validity repair, offsets, transform enumeration, broad-phase pruning, exact narrow-phase checks, and final validation.

The search engine should answer the question: 'Which legal placement should I try next to get a good overall nest?' It owns part ordering, variant prioritization, candidate generation, scoring, diversified restarts, and improvement passes.

This split is the right system boundary for maintainability. It makes unit tests cleaner, benchmarking clearer, and later replacement with a compiled engine realistic.

> **Design rule:** Never let search logic quietly redefine geometry legality. Geometry produces the legal candidate set and exact validator. Search may rank or prune legal candidates, but it should not invent alternate geometry semantics.

### 1.7 Why the flat-edge bias is worth building

Because many CarvAcoustic parts have one meaningful flat edge, the solver can do better than a shape-agnostic candidate generator. After flattening and simplification, it should detect the strongest nearly straight edge chain or edge pair on each part and attach a score to it.

That feature should not become a hard rule. Instead it should bias candidate generation and scoring toward three behaviors: placing the edge flush to a sheet boundary, pairing it against an exposed flat edge on a placed part, and aligning it with grain when the job allows.

This is exactly the kind of domain-specific heuristic that tends to improve runtime-to-quality in production: it reduces the number of candidates that need exact checking while steering the search toward layouts a human operator would often prefer anyway.

### 1.8 Fast / Balanced / Max Yield is the right user-facing mode design

The product should expose one solver family with different effort budgets, not three unrelated algorithms. That keeps results consistent, simplifies maintenance, and makes debugging easier.

In V1, all three modes should share the same geometry engine, transform model, candidate generator, and exact validator. The difference should be how many seeds, variants, anchors, and repair passes the search is allowed to try. In V2, Max Yield can deepen further and optionally run on a background worker.

| Mode | Use case | Search behavior | Execution path |
| --- | --- | --- | --- |
| Fast | Interactive preview | Very small candidate set, 2–3 seeded orders, minimal repair | Online request path |
| Balanced | Default production mode | Broader anchors, more seeds, reinsert / swap pass | Online request path |
| Max Yield | Premium or deliberate deeper solve | More seeds, larger candidate budgets, deeper repair; V2 adds local search and cross-sheet moves | Prefer worker path once V2 exists |

### 1.9 What is explicitly deferred

- Continuous free-angle rotation as a general production feature.
- Hole / part-in-part nesting as a default capability.
- Defect-aware boards or arbitrary irregular containers.
- A fully robust general no-fit-polygon engine in Python.
- GA-first or SA-first optimization.
- Exact MIP optimization on the online request path.
- Toolpath optimization; nesting output should feed it, not replace it.

## Part 2. V1 build plan and Claude implementation brief

V1 is the first production engine, not a throwaway prototype. It should give CarvAcoustic a reliable irregular nesting pipeline that uses true polygon geometry, obeys transform constraints exactly, and feels responsive in normal product use.

The brief below is written so Claude can first review the existing codebase, identify what can be reused, and then implement the missing pieces without changing the core product semantics.

### 2.1 V1 definition of done

- Given a job with rectangular sheets and irregular parts, the engine returns a feasible placement or an explicit failure report.
- All returned placements are exactly validated against contracted sheet boundaries and inflated inter-part clearance geometry.
- Allowed rotations, mirroring rules, handedness constraints, and grain lock are enforced by a single transform legality layer.
- The solver supports Fast, Balanced, and Max Yield modes using one shared core solver with different effort budgets.
- A benchmark harness exists with public and internal datasets, deterministic seeding, runtime metrics, and feasibility checks.
- A product-facing result schema exists for placements, material utilization, warnings, timings, and validation metadata.

### 2.2 V1 scope and non-goals

| Category | Contents |
| --- | --- |
| In scope | Flatten curves to polylines; repair invalid geometry; offset / inflate parts; explicit transform enumeration; flat-edge detection; constructive placement; broad-phase + exact collision checks; small repair pass; deterministic seeding; benchmark harness; product-facing result object. |
| Out of scope | Full NFP engine; part-in-part; free-angle rotation; defect-aware stock; compiled backend; optimizer-specific persistent caches; toolpath generation. |

### 2.3 Architecture to implement

The V1 engine should be implemented as a package with two top-level subsystems: `geometry` and `search`. A thin `solver` layer should orchestrate preprocessing, search execution, validation, and result assembly.

The geometry subsystem should be entirely reusable by V2. The search subsystem should be replaceable in parts without changing geometry contracts.

```
carvacoustic_nesting/
    ingest/
        flatten.py
        normalize.py
        units.py
    geometry/
        validate.py
        offsets.py
        transforms.py
        preferred_edges.py
        collision.py
        spatial_hash.py
        sheet.py
    search/
        ordering.py
        candidates.py
        scoring.py
        constructive.py
        improve.py
        modes.py
    solver/
        solve.py
        validate_result.py
        result_schema.py
    bench/
        datasets.py
        runner.py
        reports.py
    tests/
```

### 2.4 Core data model

| Type | Purpose |
| --- | --- |
| SheetSpec | Sheet width / height, edge margin, material metadata, grain axis. |
| PartSpec | Canonical part geometry, quantity, allowed angles, mirror rule, grain rule, metadata. |
| TransformSpec | Discrete `(angle_deg, mirrored)` pair. This is the only legal transform representation. |
| VariantGeom | Precomputed transformed exact polygon, inflated polygon, AABB, preferred-edge descriptors, prepared geometry handle. |
| Placement | Part id, sheet index, transform, translation, anchor kind, score breakdown. |
| SheetState | Placed items, spatial hash, used envelope, exposed edges, cached sheet metrics. |
| SolutionState | All sheets, objective metrics, unplaced parts, seed, timings, warnings. |
| NestJob | Top-level solve request with sheets, parts, clearance, mode, and quality settings. |
| NestResult | Placements plus utilization, validation report, leftover metrics, debug stats. |

Instruction for Claude: if the current codebase already has equivalent models, adapt them rather than duplicating them. The target is one coherent domain model, not parallel types.

### 2.5 Geometry pipeline specification

1. Ingest all input geometry in one canonical unit system. Normalize units at the boundary of the solver.
2. Flatten curves and arcs to polylines using a chord tolerance tied to manufacturing tolerance. Keep the original curves for rendering/export, but nest on polygonal approximations.
3. Repair invalid geometries and reject or sanitize degenerate outputs. Invalid input is expected in production.
4. Normalize winding, remove repeated points, collapse tiny spikes, and merge nearly collinear edge runs.
5. Detect one or two preferred flat-edge chains per part after simplification. Store chain length, angle, and confidence score.
6. Enumerate all legal discrete transforms for each part up front. Legal transforms are the intersection of user settings and part-specific rules.
7. For each transform, precompute both the exact polygon and an inflated nesting polygon using half the inter-part clearance.
8. Contract the usable sheet by edge margin plus half the inter-part clearance so the hot loop only reasons about one clearance model.

> **Clearance model:** Use the clean production model: inflate each part by `clearance / 2`, and contract the usable sheet by `edge_margin + clearance / 2`. Then all feasibility checks happen in one geometry space.

### 2.6 Search pipeline specification

1. Build several seeded part orders, at minimum: area descending, largest extent descending, awkwardness descending, and a few randomized perturbations.
2. For each unplaced part, prioritize its legal variants according to mode rules and grain / mirroring constraints.
3. Generate a small candidate set from three anchor families: sheet-boundary anchors, preferred-flat-edge contact anchors, and generic contact anchors.
4. Use a dynamic spatial hash on AABBs for broad-phase pruning. Only send nearby candidates to exact geometry checks.
5. Use prepared inflated polygons and exact predicates for narrow-phase overlap testing.
6. Score feasible candidates using compactness, contact length, preferred-flat-edge bonuses, and fragmentation penalties.
7. Place the best candidate, update sheet state, and continue until all parts are placed or a new sheet must be opened.
8. After constructive placement, run a cheap repair pass: compact, remove the most damaging parts, and reinsert them; optionally try a small swap neighborhood.
9. Run exact validation on the final result and emit warnings or structured failure reasons.

### 2.7 Candidate generator requirements

The candidate generator is the heart of V1 performance. It must be biased, not exhaustive. The goal is to produce the small set of placements a skilled human would probably try first.

Every candidate should carry an anchor tag so the result can be debugged and the search can be profiled. Example tags: `left-boundary`, `bottom-boundary`, `flat-edge-contact`, `generic-contact`, `reinsert`.

| Anchor family | How it is generated | Why it matters |
| --- | --- | --- |
| Boundary anchor | Slide preferred edge or bounding edge against a sheet boundary at promising y/x values | Very cheap and often strong for one-flat-edge parts |
| Flat-edge contact | Align the part’s preferred edge against exposed near-straight edges of already placed parts | Encodes the product-specific geometric bias |
| Generic contact | Touch candidate against nearby obstacles using contact points / endpoints when no strong flat match exists | Prevents the bias from missing curved-shape opportunities |

### 2.8 Scoring function requirements

Claude should implement a normalized weighted scorer, not hard-code an opaque pile of constants. Put weights in config so they can be tuned without code edits.

The score should reward compact used area and good contacts, while penalizing slivers and tiny trapped cavities.

| Component | Intent | Suggested starting direction |
| --- | --- | --- |
| Used-envelope growth | Keep the active nest compact | Positive penalty |
| Max-X / Max-Y growth | Bias strip-like compaction or balanced fill | Positive penalty |
| Contact length | Reward flush contacts with sheet or parts | Negative bonus |
| Preferred-edge alignment | Reward part-specific flat-edge use | Negative bonus |
| Sliver creation | Avoid unusable narrow leftovers | Positive penalty |
| Tiny cavity creation | Avoid little trapped pockets | Positive penalty |

Implementation note: normalize geometric measures by sheet dimensions or part size so weights remain stable across different board sizes.

### 2.9 User mode configuration for V1

| Mode | Seeds | Anchors / variant | Repair | Target behavior |
| --- | --- | --- | --- | --- |
| Fast | 2–3 | 8–20 | Compact only | Near-instant preview |
| Balanced | 6–12 | 20–60 | Compact + reinsert + small swap | Default production mode |
| Max Yield | 12–20 | 40–100 | Deeper reinsert / swap within V1 limits | Better yield, still same solver family |

Claude should implement these as config presets over the same solver components, not as separate code paths.

### 2.10 Public interfaces Claude should preserve or create

```
def solve_nest(job: NestJob, mode: SolveMode, seed: int | None = None) -> NestResult:
    ...

def validate_nest(job: NestJob, result: NestResult) -> ValidationReport:
    ...

def benchmark_case(case: BenchmarkCase, mode: SolveMode, seed: int | None = None) -> BenchmarkResult:
    ...
```

The concrete names may differ if the codebase already exposes nesting services, but the product needs clean equivalents to these three entry points: solve, validate, and benchmark.

Validation must be callable independently from solve so that imported or edited placements can be checked later without rerunning the optimizer.

### 2.11 Example configuration schema

```
{
  "sheet": {
    "width_mm": 2440.0,
    "height_mm": 1220.0,
    "edge_margin_mm": 6.0,
    "grain_axis": "x"
  },
  "clearance_mm": 3.0,
  "mode": "balanced",
  "parts": [
    {
      "id": "panel_a",
      "quantity": 2,
      "allow_mirror": false,
      "allowed_angles_deg": [0, 180],
      "grain_locked": true,
      "geometry": "..."
    }
  ]
}
```

### 2.12 Claude implementation sequence

| Phase | What Claude should do |
| --- | --- |
| Phase 0. Codebase review | Inventory existing geometry types, importers, sheet models, worker / API entry points, current tests, and any nesting or packing logic already present. Produce a short delta plan before changing behavior. |
| Phase 1. Geometry foundation | Implement or normalize curve flattening, geometry repair, transform enumeration, offsets, contracted sheet logic, and exact validation. |
| Phase 2. Candidate generation + constructive search | Add preferred-edge detection, anchor generation, broad-phase pruning, exact feasibility checks, scoring, and placement loop. |
| Phase 3. Improvement pass + modes | Add compaction, reinsert / swap neighborhoods, config-driven mode presets, deterministic seeding, and debug metrics. |
| Phase 4. Bench + integration | Add benchmark runner, public interfaces, API integration, result schema, and regression tests. |

Important instruction: Claude should prefer extending existing modules and tests instead of dropping in a parallel `v1` implementation unless the current code is structurally unusable.

### 2.13 Pseudocode Claude can implement from

```
preprocess all parts
for each part:
    flatten curves
    repair / normalize polygon
    detect preferred flat edges
    enumerate legal transforms
    build exact polygon + inflated polygon for each transform

build seeded part orders

best_solution = None
for seed_order in seed_orders:
    state = empty_solution()

    for next_part in seed_order:
        candidate_list = []

        for sheet in candidate_sheets(state):
            for variant in legal_variants(next_part):
                anchors = (
                    boundary_anchors(variant, sheet, state) +
                    flat_edge_contact_anchors(variant, sheet, state) +
                    generic_contact_anchors(variant, sheet, state)
                )

                for pose in shortlist(anchors, mode_limits):
                    if not inside_contracted_sheet(variant, pose, sheet):
                        continue
                    nearby = spatial_hash_query(state, variant, pose)
                    if broadphase_reject(variant, pose, nearby):
                        continue
                    if exact_overlap(variant, pose, nearby):
                        continue
                    score = score_candidate(variant, pose, state)
                    candidate_list.append((score, sheet, variant, pose))

        if candidate_list:
            place(best(candidate_list), state)
        elif can_open_new_sheet(state):
            open_new_sheet(state)
            retry same part
        else:
            record_unplaced_part(state, next_part)

    compact(state)
    reinsert_worst_parts(state)
    small_swap_pass(state)
    exact_validate(state)

    if better_than_best(state, best_solution):
        best_solution = state

return best_solution
```

### 2.14 Test plan and acceptance criteria for V1

| Category | Acceptance criterion |
| --- | --- |
| Feasibility | No overlaps on inflated geometry; no part outside contracted sheet; exact validator agrees with solver result. |
| Transform legality | Every returned placement uses a transform from the explicit allowed transform set. |
| Determinism | Same job + same seed + same mode returns the same layout and score. |
| Robust import handling | Dirty or invalid input geometry is either repaired successfully or rejected with a clear reason. |
| Mode behavior | Fast, Balanced, and Max Yield all produce feasible layouts while showing predictable effort / quality differences. |
| Benchmarking | Benchmark harness records runtime, utilization, sheet count, warnings, and failure reasons. |
| Regression safety | Add snapshot-style fixtures for representative jobs: simple convex, concave, grain-locked, mirror-forbidden, narrow-clearance, and high-vertex jobs. |

### 2.15 Benchmark plan for V1

Use a mix of public irregular nesting datasets and an internal CarvAcoustic corpus. Public datasets prove general correctness and allow comparison against the literature. Internal datasets prove product relevance.

Track at minimum: sheet count, utilization, runtime to first feasible result, runtime to best result, invalid-result rate, geometry repair failure rate, and leftover quality metrics such as sliver count.

| Dataset source | Purpose |
| --- | --- |
| ESICUP public datasets | General irregular nesting regression and comparability |
| Internal anonymized jobs | Real product difficulty: curved parts, one-flat-edge shapes, grain lock, mirror rules, and realistic clearances |
| Synthetic edge-case fixtures | Narrow channels, near tangencies, invalid polygons, high-vertex shapes, repeated parts |

### 2.16 Guardrails: what Claude should not do in V1

- Do not switch V1 to a GA-first or SA-first optimizer.
- Do not introduce continuous free-angle rotation.
- Do not add hole nesting, part-in-part, or defect-aware stock in the same implementation pass.
- Do not let search logic bypass exact validation or transform legality checks.
- Do not create duplicate domain models if equivalent models already exist in the codebase.
- Do not silently approximate away clearances; exact inflated-geometry checks remain the source of truth.

### 2.17 Deliverables Claude should leave behind for V1

- A short code review memo describing what was reused, what was added, and what was intentionally deferred.
- Production code for preprocessing, transforms, candidate generation, search, validation, and mode configs.
- Tests covering geometry repair, transform legality, feasibility, and deterministic behavior.
- A benchmark runner and at least one benchmark report artifact.
- A concise developer README describing the solver flow and tuning knobs.

## Part 3. V2 build plan and higher-yield optimization brief

V2 should deepen optimization, not replace the system. The key requirement is to preserve the V1 geometry contracts, result schema, and validation semantics while making harder jobs use less material more consistently.

The safest V2 plan is staged. First add deeper local neighborhoods on top of V1. Then add optional selective geometry accelerators. Only after that decide whether Max Yield economics justify a compiled backend.

### 3.1 V2 definition of done

- V2 reuses the V1 geometry pipeline and exact validator without semantic drift.
- Balanced and especially Max Yield show measurable utilization gains on the internal benchmark set compared with V1 at higher effort budgets.
- The search layer supports deeper neighborhoods: ruin-and-recreate, cross-sheet reinsertions, and stronger compaction.
- The system can route deeper solves to a worker path without changing the job or result contract.
- Optional selective NFP or compiled-backend hooks exist behind clear interfaces, not fused into product logic.

### 3.2 What changes from V1

| Area | V2 treatment |
| --- | --- |
| Stays the same | Geometry import, flattening, repair, offsets, transform legality, exact validation, result schema, benchmark harness. |
| Gets deeper | Neighborhood search, sheet-elimination moves, reinsert logic, candidate budgets, mode routing. |
| May become optional | Selective NFP cache, compiled geometry/search adapter, worker-only deep solve execution. |

### 3.3 Recommended V2 search additions

| Addition | Description | Priority |
| --- | --- | --- |
| Ruin-and-recreate | Remove a subset of difficult or disruptive placements, then reinsert them with larger candidate budgets. | Best first V2 upgrade: high impact, moderate complexity. |
| Cross-sheet moves | Attempt to move parts between sheets to collapse one sheet entirely or reduce waste concentration. | Important when sheet count matters more than local compactness. |
| Overlap-minimization local search | Allow temporary overlaps in a controlled neighborhood and iteratively repair them toward feasibility. | Higher yield on hard cases, but more engineering risk; build after ruin-and-recreate. |
| Selective NFP cache | Cache pairwise geometry information only for repeated or hard part-pair / transform combinations. | Useful accelerator, not the primary architecture. |
| Compiled backend adapter | Add an interface boundary so Max Yield can later use a Rust engine without changing product contracts. | Optional economics play, not mandatory for V2 launch. |

### 3.4 Staged V2 implementation order

| Stage | What to build |
| --- | --- |
| Stage A | Implement deeper neighborhoods in pure Python: ruin-and-recreate, larger reinsertion neighborhoods, and cross-sheet compaction. |
| Stage B | Add overlap-minimization style repair for Max Yield mode, reusing V1 exact geometry checks as the oracle of feasibility. |
| Stage C | Add selective NFP caching only where repeated hard geometry pairs justify it. |
| Stage D | If Max Yield mode needs more performance per dollar, add a compiled backend adapter behind the geometry/search interface. |

This order is important. Stage A yields a meaningful V2 without forcing an early backend rewrite.

### 3.5 V2 architecture additions Claude should implement

- Add a neighborhood-search module that operates on a complete feasible solution and can remove, reinsert, swap, or migrate parts between sheets.
- Add a `sheet_elimination` objective helper that tries to free the worst-utilized sheet or the last-opened sheet by migrating its parts elsewhere.
- Add a `deep_mode` execution policy so Max Yield can run with larger budgets or on a worker path without changing the solver contract.
- Add optional caching boundaries for expensive repeated geometry relations. Keep the cache behind interfaces so it can be disabled.

### 3.6 Interface boundary for optional compiled backend

```
class GeometryOracle(Protocol):
    def inside_sheet(self, variant_id: str, pose: Pose, sheet_id: str) -> bool: ...
    def colliders(self, variant_id: str, pose: Pose, sheet_state: SheetState) -> list[str]: ...
    def place(self, variant_id: str, pose: Pose, sheet_state: SheetState) -> None: ...
    def validate(self, solution: SolutionState) -> ValidationReport: ...

class SearchEngine(Protocol):
    def solve(self, job: NestJob, oracle: GeometryOracle, mode: SolveMode, seed: int | None) -> NestResult: ...
```

This interface boundary lets CarvAcoustic keep Python orchestration while swapping the geometry oracle or deeper search engine later if Max Yield needs it.

### 3.7 Worker-path recommendation for V2

Once V2 exists, Fast and most Balanced solves should remain on the direct request path. Max Yield should be allowed to run on a deeper budget, which makes a queued worker path appropriate for larger jobs or premium workflows.

The important product rule is that the job schema and result schema remain identical whether the solve happens inline or on a worker. Execution policy must not leak into product semantics.

| Path | Best use |
| --- | --- |
| Inline solve | Fast preview, most Balanced jobs, small / medium part counts |
| Worker solve | Large jobs, Max Yield, deep V2 neighborhoods, future compiled backend runs |

### 3.8 Claude implementation sequence for V2

| Phase | What Claude should do |
| --- | --- |
| Phase 0. Review V1 behavior | Measure where V1 loses utilization: order sensitivity, sheet fragmentation, or inability to escape early bad contacts. |
| Phase 1. Deeper neighborhoods | Implement ruin-and-recreate, cross-sheet migration, and stronger reinsertion on the existing feasible layout representation. |
| Phase 2. Max Yield execution policy | Add deep-budget configs and optional worker execution without changing API contracts. |
| Phase 3. Overlap-minimization search | Implement controlled temporary-overlap local search for Max Yield, using V1 geometry checks to re-establish exact feasibility. |
| Phase 4. Optional accelerators | Add selective NFP cache or compiled adapter only if benchmark evidence shows enough ROI. |

### 3.9 V2 benchmark and acceptance criteria

| Category | Acceptance criterion |
| --- | --- |
| Quality delta | Balanced and Max Yield should beat V1 on a meaningful share of internal hard jobs, especially on sheet count or utilization. |
| Semantic stability | V2 results still pass the exact V1 validator with no special cases. |
| Execution routing | Same job and result schema work for inline and worker execution. |
| Fallback safety | If deep search fails, times out, or is disabled, the system can still return a V1-feasible result. |
| Observability | Benchmark reports attribute gains to neighborhood types, time budgets, and candidate counts. |

### 3.10 Guardrails: what Claude should not do in V2

- Do not rewrite the geometry model unless the validator proves it is impossible to extend safely.
- Do not fuse optional NFP or compiled-backend code directly into product-specific logic.
- Do not let Max Yield become a separate incompatible solver with different semantics for transforms or clearance.
- Do not enable deep worker routing without preserving deterministic seeds and structured metrics.

### 3.11 Deliverables Claude should leave behind for V2

- An updated delta memo explaining where V2 improves over V1 and where it intentionally stops.
- Neighborhood-search code with tests and benchmark evidence.
- Execution-policy support for deeper solves and worker routing.
- A benchmark report comparing V1 and V2 across representative internal jobs.
- Clear interface boundaries around any optional cache or compiled backend adapter.

## Appendix A. Prompt-ready instructions for Claude

```
Review the current CarvAcoustic codebase before implementing anything. Identify existing geometry models, importers, nesting logic, worker / API boundaries, and test coverage. Then implement the target architecture in-place where possible rather than creating duplicate parallel models.

For V1, build a Python irregular nesting engine with:
- true polygon preprocessing
- explicit transform legality
- clearance inflation and contracted sheet logic
- preferred-flat-edge detection
- contact-biased constructive search
- mode presets for Fast / Balanced / Max Yield
- exact post-solve validation
- deterministic benchmark support

For V2, keep the same geometry contracts and add:
- ruin-and-recreate
- cross-sheet moves
- stronger reinsertion / compaction
- optional overlap-minimization local search
- optional interface boundaries for selective NFP caching or a compiled backend

Do not add continuous free-angle rotation, part-in-part, a full NFP-first engine, GA-first search, or an online MIP path in the same implementation stream.
```

## Appendix B. Source list worth keeping near the implementation

| Reference | Why it matters |
| --- | --- |
| [R1] Burke et al. (2006), A New Bottom-Left-Fill Heuristic Algorithm for the Two-Dimensional Irregular Packing Problem. | Classic constructive reference and still useful for placement thinking. |
| [R2] Guo et al. (2022), Two-dimensional irregular packing problems: A review. | Good field overview and family classification. |
| [R3] Gardeyn et al. (2025), Decoupling Geometry from Optimization in 2D Irregular Cutting and Packing Problems. | Best modern argument for the geometry/search split. |
| [R4] sparrow paper and repository. | Best current open reference for deeper search and realistic benchmark thinking. |
| [R5] Zhang et al. (2022), iteratively doubling local search for irregular bin packing with limited rotations. | Strong limited-rotation local-search reference that maps well to transform-constrained manufacturing jobs. |
| [R6] Lastra-Díaz and Ortuño (2024), mixed-integer programming models for irregular strip packing. | Useful for understanding why exact models remain relevant academically but not ideal as the online product path. |
| [R7] Shapely 2.1 docs: make_valid, prepare, STRtree, buffer, release notes. | Directly relevant to the Python geometry stack. |
| [R8] pyclipper / pyclipr docs. | Directly relevant to robust polygon offsetting decisions. |
| [R9] SVGnest. | Useful practical reference for user-facing knobs such as spacing, curve tolerance, rotations, and optional part-in-part. |
| [R10] libnest2d README. | Useful architecture reference and also a reminder that concavities and holes remain painful in generic NFP-based systems. |
| [R11] ESICUP datasets. | Public benchmark source. |

## Appendix C. Reference links

[R1] https://pubsonline.informs.org/doi/10.1287/opre.1060.0293

[R2] https://www.frontiersin.org/journals/mechanical-engineering/articles/10.3389/fmech.2022.966691/full

[R3] https://pubsonline.informs.org/doi/10.1287/ijoc.2024.1025

[R4] https://github.com/JeroenGar/sparrow

[R5] https://www.sciencedirect.com/science/article/abs/pii/S0305054821002847

[R6] https://www.sciencedirect.com/science/article/pii/S0377221723006148

[R7] https://shapely.readthedocs.io/

[R8] https://pypi.org/project/pyclipper/  and  https://github.com/drlukeparry/pyclipr

[R9] https://github.com/Jack000/SVGnest

[R10] https://github.com/tamasmeszaros/libnest2d

[R11] https://github.com/ESICUP/datasets
