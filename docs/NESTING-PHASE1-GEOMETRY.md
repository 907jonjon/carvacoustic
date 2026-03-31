# Nesting Engine — Phase 1: Geometry Foundation

**Goal:** Build the geometry subsystem that the nesting search engine will depend on. This goes into a new `geometry/app/nesting/` package alongside the existing `geometry/app/geometry/` directory.

**Context:** CarvAcoustic currently uses a simple FFD row-packing algorithm in `geometry/app/geometry/layout.py`. This phase builds the geometry foundation for a true irregular polygon nesting engine. Phase 2 (separate document) builds the search engine on top.

**Guiding document:** `docs/carvacoustic_nesting_build_document.md` — sections 2.1–2.8 and 2.16.

---

## Existing Code to Reuse (DO NOT duplicate)

### Slat polygon output (from `geometry/app/geometry/slat_profiler.py`)
Each part is a dict:
```python
{
    "part_id": "S001",          # str
    "part_type": "slat",        # "slat" | "backing"
    "polygon": Polygon,         # Shapely Polygon, ~200 vertices, Y-up coords
    "profile_heights": ndarray, # 1D Z heights (for rendering, not nesting)
    "slat_index": 0,            # int
    "bounding_box": (minx, miny, maxx, maxy),  # from polygon.bounds
    "area": float,              # polygon.area
    "tab_positions": [float],   # X-centres of mounting tabs
}
```
Backing board is the same shape but `part_type: "backing"` and has interior holes (slots).

### Config models (from `geometry/app/models.py`)
Key types to reference (do not recreate):
- `CanonicalConfig` — top-level config with `.fabrication.material`, `.fabrication.tool`, `.layout`, `.slats`, `.backing`
- `ConfigMaterial` — `sheet_width`, `sheet_height`, `thickness`, `grain_direction`
- `ConfigTool` — `clearance`, `border_gap`, `tool_diameter`
- `ConfigLayout` — `rotation_mode` (none|90_only|any), `preserve_grain`, `copies`
- `RotationMode` enum — `none`, `ninety_only`, `any`
- `GrainDirection` enum — `x`, `y`

### Current layout (from `geometry/app/geometry/layout.py`)
- `run_slat_layout(parts, config) -> LayoutResult` — current FFD packer
- `LayoutResult`, `SheetLayout`, `PartPlacement` dataclasses — keep these as the output contract
- The new nesting engine MUST return a `LayoutResult` so bundle.py and svg_export.py work unchanged

---

## Package Structure to Create

```
geometry/app/nesting/
    __init__.py
    models.py           # NestJob, PartSpec, TransformSpec, VariantGeom, SheetSpec, Placement, SheetState, SolutionState, NestResult
    ingest.py           # prepare_nest_job(): converts profiler output + config → NestJob
    geometry/
        __init__.py
        flatten.py      # Polygon simplification with chord tolerance
        normalize.py    # Winding, spike collapse, collinear merge
        offsets.py      # Clearance inflation model
        transforms.py   # TransformSpec enum, legal variant precomputation
        preferred_edges.py  # Flat-edge detection and scoring
        collision.py    # Prepared geometry + exact overlap checks
        spatial_hash.py # STRtree or grid-based broad-phase AABB pruning
        sheet.py        # SheetState: placed items, spatial index, exposed edges, usable bounds
        validate.py     # Post-solve exact validation
```

---

## Implementation Spec

### 1. `models.py` — Core Data Model

```python
from dataclasses import dataclass, field
from shapely.geometry import Polygon
from shapely.prepared import PreparedGeometry

@dataclass
class SheetSpec:
    width: float
    height: float
    edge_margin: float      # from config.fabrication.tool.border_gap
    grain_axis: str | None  # "x" | "y" | None

@dataclass
class TransformSpec:
    angle_deg: float        # 0, 90, 180, 270
    mirrored: bool          # True = flipped along Y axis

@dataclass
class VariantGeom:
    transform: TransformSpec
    polygon: Polygon            # exact transformed polygon
    inflated: Polygon           # polygon.buffer(clearance / 2)
    prepared_inflated: PreparedGeometry  # for fast intersection tests
    aabb: tuple[float, float, float, float]  # inflated.bounds
    preferred_edges: list[dict]  # from preferred_edges.py
    area: float

@dataclass
class PartSpec:
    part_id: str
    quantity: int               # usually 1 for slats
    variants: list[VariantGeom] # one per legal transform
    original_polygon: Polygon   # unsimplified, for export
    grain_locked: bool
    allow_mirror: bool

@dataclass
class Placement:
    part_id: str
    sheet_index: int
    transform: TransformSpec
    x: float                    # translation X
    y: float                    # translation Y
    anchor_tag: str             # "boundary", "flat-edge-contact", "generic-contact", "reinsert"
    score: float

@dataclass
class SheetState:
    index: int
    spec: SheetSpec
    placements: list[Placement] = field(default_factory=list)
    placed_inflated: list[Polygon] = field(default_factory=list)  # for collision checks
    # spatial index rebuilt after each placement
    used_area: float = 0.0
    usable_bounds: Polygon | None = None  # contracted sheet polygon

@dataclass
class NestJob:
    sheets: SheetSpec           # all sheets are identical for now
    parts: list[PartSpec]
    clearance: float
    mode: str                   # "fast" | "balanced" | "max_yield"
    seed: int | None = None

@dataclass
class NestResult:
    placements: list[Placement]
    sheets_used: int
    utilization: float          # average across sheets
    unplaced: list[str]         # part_ids that couldn't be placed
    warnings: list[str]
    elapsed_ms: float
```

### 2. `ingest.py` — Bridge from Profiler Output to NestJob

```python
def prepare_nest_job(
    parts: list[dict],          # from slat_profiler
    config: CanonicalConfig,
    mode: str = "balanced",
    seed: int | None = None,
) -> NestJob:
```

This function:
1. Creates a `SheetSpec` from `config.fabrication.material` and `config.fabrication.tool`
2. For each part dict, creates a `PartSpec`:
   - Simplifies polygon using `flatten.simplify_polygon(poly, config.fabrication.tool.tool_diameter)`
   - Normalizes winding via `normalize.normalize_polygon()`
   - Enumerates legal transforms via `transforms.enumerate_transforms(config.layout)`
   - For each transform, precomputes `VariantGeom` via `offsets.inflate()` and `preferred_edges.detect()`
3. Returns a `NestJob`

### 3. `geometry/flatten.py` — Polygon Simplification

```python
def simplify_polygon(poly: Polygon, tool_diameter: float) -> Polygon:
    """
    Simplify polygon to reduce vertex count for nesting.
    Uses Shapely's topology-preserving simplify with tolerance = tool_diameter / 4.
    Keeps the original polygon for export; nests on the simplified version.
    """
```

- Use `poly.simplify(tolerance, preserve_topology=True)`
- Tolerance = `tool_diameter / 4` (half the kerf — features smaller than this can't be cut anyway)
- Validate result is still valid; fall back to original if not
- Log vertex count reduction for debugging

### 4. `geometry/normalize.py` — Polygon Normalization

```python
def normalize_polygon(poly: Polygon) -> Polygon:
    """
    Normalize winding (CCW exterior, CW holes), remove duplicate points,
    collapse tiny spikes, and merge nearly collinear edges.
    """
```

- Ensure CCW exterior winding via `shapely.geometry.polygon.orient(poly, sign=1.0)`
- Remove consecutive duplicate points (within 1e-10 tolerance)
- Collapse spikes shorter than `min_edge_length` (0.01 in design units)
- Use `poly.simplify(1e-6, preserve_topology=True)` as a final cleanup

### 5. `geometry/offsets.py` — Clearance Inflation

```python
def inflate_part(poly: Polygon, clearance: float) -> Polygon:
    """Inflate part by clearance/2. Uses Shapely buffer with round joins."""
    return poly.buffer(clearance / 2.0, resolution=16, join_style="round")

def contract_sheet(sheet: SheetSpec, clearance: float) -> Polygon:
    """
    Contract usable sheet by edge_margin + clearance/2.
    Returns a Polygon representing the usable placement area.
    """
    inset = sheet.edge_margin + clearance / 2.0
    from shapely.geometry import box
    return box(inset, inset, sheet.width - inset, sheet.height - inset)
```

**Clearance model:** inflate each part by `clearance / 2`, contract sheet by `edge_margin + clearance / 2`. All feasibility checks then happen in one geometry space.

### 6. `geometry/transforms.py` — Transform Enumeration

```python
def enumerate_transforms(
    layout_config,          # ConfigLayout
    grain_direction: str,   # "x" | "y"
) -> list[TransformSpec]:
    """
    Return all legal discrete transforms based on rotation_mode,
    preserve_grain, and grain_direction.
    """
```

Logic:
- `rotation_mode == "none"` → `[TransformSpec(0, False)]`
- `rotation_mode == "90_only"` → `[TransformSpec(0, False), TransformSpec(90, False)]`
- `rotation_mode == "any"` → `[TransformSpec(0, False), TransformSpec(90, False), TransformSpec(180, False), TransformSpec(270, False)]`
- If `preserve_grain` is True, filter out any transform where `angle_deg % 180 != 0` (only 0° and 180° preserve grain for grain_direction "x")
- Mirroring: disabled by default in V1. Add `TransformSpec(angle, True)` variants only if `allow_mirror` is True on the part.

```python
def apply_transform(poly: Polygon, t: TransformSpec) -> Polygon:
    """Apply a TransformSpec to a polygon centred at origin."""
    from shapely import affinity
    result = poly
    if t.mirrored:
        result = affinity.scale(result, xfact=-1, yfact=1, origin=(0, 0))
    if t.angle_deg != 0:
        result = affinity.rotate(result, t.angle_deg, origin=(0, 0))
    return result
```

### 7. `geometry/preferred_edges.py` — Flat Edge Detection

```python
def detect_preferred_edges(poly: Polygon, min_length_ratio: float = 0.3) -> list[dict]:
    """
    Detect nearly-straight edge chains on a polygon.

    Returns list of:
        {
            "start_idx": int,
            "end_idx": int,
            "length": float,
            "angle": float,         # angle in degrees
            "confidence": float,    # 0-1, higher = straighter
            "midpoint": (float, float),
        }

    A "preferred edge" is a chain of consecutive edges where the total
    angular deviation is < 5° and the chain length is > min_length_ratio
    of the polygon's longest dimension.
    """
```

Key insight from the build document: CarvAcoustic slats have one meaningful flat edge (the base). Detecting this edge and using it as a placement bias is a major performance win.

### 8. `geometry/collision.py` — Exact Overlap Testing

```python
from shapely.prepared import prep

def check_collision(
    variant_inflated: PreparedGeometry,
    pose_x: float,
    pose_y: float,
    placed_inflated: list[Polygon],
) -> bool:
    """
    Return True if the variant at (pose_x, pose_y) overlaps any placed part.
    Uses prepared geometry for speed.
    """
    from shapely import affinity
    translated = affinity.translate(variant_inflated.context, xoff=pose_x, yoff=pose_y)
    for placed in placed_inflated:
        if translated.intersects(placed):
            return True
    return False

def check_inside_sheet(
    variant_inflated: Polygon,
    pose_x: float,
    pose_y: float,
    usable_bounds: Polygon,
) -> bool:
    """Return True if the variant at (pose_x, pose_y) fits inside the usable sheet."""
    from shapely import affinity
    translated = affinity.translate(variant_inflated, xoff=pose_x, yoff=pose_y)
    return usable_bounds.contains(translated)
```

### 9. `geometry/spatial_hash.py` — Broad-Phase Pruning

```python
from shapely import STRtree

class SpatialIndex:
    """Wrapper around Shapely STRtree for fast AABB-based broad-phase checks."""

    def __init__(self):
        self._polys: list[Polygon] = []
        self._tree: STRtree | None = None

    def add(self, inflated_poly: Polygon) -> None:
        self._polys.append(inflated_poly)
        self._tree = None  # invalidate

    def query_nearby(self, candidate_inflated: Polygon) -> list[Polygon]:
        """Return placed polygons whose AABBs overlap the candidate's AABB."""
        if not self._polys:
            return []
        if self._tree is None:
            self._tree = STRtree(self._polys)
        indices = self._tree.query(candidate_inflated)
        return [self._polys[i] for i in indices]
```

### 10. `geometry/sheet.py` — Sheet State

```python
@dataclass
class SheetState:
    """Mutable state for one material sheet during nesting."""
    index: int
    usable_bounds: Polygon      # contracted sheet polygon
    spatial_index: SpatialIndex
    placements: list[Placement] = field(default_factory=list)
    placed_inflated: list[Polygon] = field(default_factory=list)
    used_area: float = 0.0

    def place(self, variant: VariantGeom, x: float, y: float,
              part_id: str, transform: TransformSpec, anchor_tag: str, score: float):
        """Record a placement and update spatial index."""
        from shapely import affinity
        translated = affinity.translate(variant.inflated, xoff=x, yoff=y)
        self.placed_inflated.append(translated)
        self.spatial_index.add(translated)
        self.used_area += variant.area
        self.placements.append(Placement(
            part_id=part_id, sheet_index=self.index,
            transform=transform, x=x, y=y,
            anchor_tag=anchor_tag, score=score,
        ))
```

### 11. `geometry/validate.py` — Post-Solve Validation

```python
def validate_solution(job: NestJob, result: NestResult, parts: list[PartSpec]) -> list[str]:
    """
    Independently validate a nesting result. Returns list of error strings.
    Empty list = valid.

    Checks:
    1. No overlaps between any pair of placed inflated polygons
    2. All placed parts inside contracted sheet bounds
    3. All transforms are from the part's legal transform set
    4. All parts accounted for (placed + unplaced = total)
    """
```

---

## Bridge Function: NestResult → LayoutResult

The existing export pipeline expects `LayoutResult` from `geometry/app/geometry/layout.py`. Add this to `ingest.py`:

```python
def nest_result_to_layout_result(
    nest_result: NestResult,
    parts: list[dict],          # original profiler output
    job: NestJob,
) -> LayoutResult:
    """Convert NestResult to the LayoutResult format expected by bundle.py."""
```

This maps each `Placement` to a `PartPlacement` with `x`, `y`, `rotated_90`, and `part_index`.

---

## Integration Point

In `geometry/app/geometry/pipeline.py`, the call to `run_slat_layout()` should be replaced with:
```python
try:
    from ..nesting.ingest import prepare_nest_job, nest_result_to_layout_result
    from ..nesting.solver.solve import solve_nest
    job = prepare_nest_job(all_parts, config)
    nest_result = solve_nest(job, mode="balanced")
    layout_result = nest_result_to_layout_result(nest_result, all_parts, job)
except Exception:
    # Fallback to FFD if nesting engine fails
    layout_result = run_slat_layout(all_parts, config)
```

The same pattern applies in `bundle.py::build_export_bundle()`.

---

## Tests to Write

File: `geometry/tests/test_nesting_geometry.py`

1. **test_simplify_preserves_validity** — simplified polygon is valid and area delta < 5%
2. **test_normalize_ccw_winding** — exterior is CCW after normalization
3. **test_inflate_clearance** — inflated polygon is larger by expected amount
4. **test_contract_sheet** — contracted sheet dimensions match expectation
5. **test_enumerate_transforms_none** — returns only identity
6. **test_enumerate_transforms_90** — returns 0° and 90°
7. **test_enumerate_transforms_grain_locked** — only 0° and 180°
8. **test_apply_transform_rotate** — polygon rotated correctly
9. **test_collision_overlapping** — detects overlap
10. **test_collision_non_overlapping** — no false positive
11. **test_inside_sheet_yes** — part fits
12. **test_inside_sheet_no** — part outside bounds detected
13. **test_spatial_index_query** — returns correct nearby polygons
14. **test_preferred_edge_detection** — finds the flat base edge on a slat polygon
15. **test_validate_solution_clean** — valid solution passes
16. **test_validate_solution_overlap** — overlap detected

---

## What NOT to Do

- Do not modify `slat_profiler.py`, `height_field.py`, `boundary.py`, or `pipeline.py` (except the integration point above)
- Do not create a full NFP engine
- Do not add continuous free-angle rotation
- Do not duplicate `CanonicalConfig` or `LayoutResult` models
- Do not change the export pipeline (bundle.py, dxf_export.py, svg_export.py)
