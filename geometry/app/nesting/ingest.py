"""
Bridge between slat_profiler output + CanonicalConfig and the nesting engine.

prepare_nest_job()  — converts profiler dicts + config into a NestJob
nest_result_to_layout_result() — converts NestResult back to LayoutResult
run_nesting() — end-to-end: profiler output → LayoutResult with FFD fallback
"""

from __future__ import annotations

import logging

from shapely.prepared import prep

from ..geometry.layout import LayoutResult, PartPlacement, SheetLayout, run_slat_layout
from ..models import CanonicalConfig
from .geometry.flatten import simplify_polygon
from .geometry.normalize import normalize_polygon
from .geometry.offsets import inflate_part
from .geometry.preferred_edges import detect_preferred_edges
from .geometry.transforms import apply_transform, enumerate_transforms
from .models import NestJob, NestResult, PartSpec, SheetSpec, TransformSpec, VariantGeom

logger = logging.getLogger(__name__)


def prepare_nest_job(
    parts: list[dict],
    config: CanonicalConfig,
    mode: str = "balanced",
    seed: int | None = None,
) -> NestJob:
    """
    Convert slat_profiler output + CanonicalConfig into a NestJob.

    Each part dict is expected to have at minimum:
        part_id, part_type, polygon, bounding_box, area
    """
    mat = config.fabrication.material
    tool = config.fabrication.tool

    sheet = SheetSpec(
        width=mat.sheet_width,
        height=mat.sheet_height,
        edge_margin=tool.border_gap,
        grain_axis=mat.grain_direction.value if mat.grain_direction else None,
    )

    clearance = tool.clearance
    grain_dir = sheet.grain_axis

    part_specs: list[PartSpec] = []

    for part_dict in parts:
        poly = part_dict["polygon"]
        part_id = part_dict["part_id"]

        # Simplify and normalize
        simplified = simplify_polygon(poly, tool.tool_diameter)
        normalized = normalize_polygon(simplified)

        # Centre polygon at origin for transform/offset operations
        cx, cy = normalized.centroid.x, normalized.centroid.y
        from shapely import affinity
        centred = affinity.translate(normalized, xoff=-cx, yoff=-cy)

        # Enumerate legal transforms
        allow_mirror = part_dict.get("allow_mirror", False)
        legal_transforms = enumerate_transforms(
            config.layout, grain_dir, allow_mirror=allow_mirror
        )

        # Build variants
        variants: list[VariantGeom] = []
        for t in legal_transforms:
            transformed = apply_transform(centred, t)
            inflated = inflate_part(transformed, clearance)
            prepared = prep(inflated)
            edges = detect_preferred_edges(transformed)

            variants.append(
                VariantGeom(
                    transform=t,
                    polygon=transformed,
                    inflated=inflated,
                    prepared_inflated=prepared,
                    aabb=inflated.bounds,
                    preferred_edges=edges,
                    area=transformed.area,
                )
            )

        part_specs.append(
            PartSpec(
                part_id=part_id,
                quantity=1,
                variants=variants,
                original_polygon=poly,
                grain_locked=config.layout.preserve_grain,
                allow_mirror=allow_mirror,
            )
        )

    return NestJob(
        sheets=sheet,
        parts=part_specs,
        clearance=clearance,
        mode=mode,
        seed=seed,
    )


def nest_result_to_layout_result(
    nest_result: NestResult,
    parts: list[dict],
    job: NestJob,
) -> LayoutResult:
    """
    Convert NestResult to the LayoutResult format expected by bundle.py.

    Maps each Placement to a PartPlacement with x, y, rotated_90, and part_index.

    COORDINATE MAPPING:
    The nesting engine works with centred polygons (centroid at origin) and stores
    (x, y) as translation offsets from origin.  But svg_export.py expects (x, y) to
    be the sheet position of the part's original bounding-box min corner:

        dx = pl.x - bbox[0]   (where bbox = original polygon bounds)
        dy = pl.y - bbox[1]

    So we convert:  sheet_x = nesting_x + centroid_x - bbox_minx + bbox_minx
    i.e. the placed position of the original polygon's min corner on the sheet is
    nesting_x + centroid_x (since centring shifted by -centroid, placement shifts back).
    But svg_export subtracts bbox[0] again, so we need to provide:
        pl.x = nesting_x + centroid_x
    which gives dx = nesting_x + centroid_x - bbox[0] = nesting_x - (-centroid_x + bbox[0])
    Hmm, let's be explicit: after nesting, the part's min corner on the sheet is at:
        sheet_minx = nesting_x + (centred_polygon.bounds[0])
    And svg_export does:
        dx = pl.x - original_bbox[0]
        moved = translate(original_poly, dx, dy)
    So the moved polygon's min-x = original_bbox[0] + dx = pl.x.
    Therefore pl.x should equal the desired sheet_minx = nesting_x + centred_bounds[0].
    But wait — centred_bounds[0] = original_bbox[0] - centroid_x. So:
        pl.x = nesting_x + original_bbox[0] - centroid_x
    And svg_export gives:
        dx = (nesting_x + bbox[0] - cx) - bbox[0] = nesting_x - cx
        moved_minx = bbox[0] + nesting_x - cx
    We actually want the polygon placed so that the CENTRED polygon translated by
    nesting_x lands correctly. The centred polygon's min-x is bbox[0]-cx.
    After translate by nesting_x: min-x = bbox[0] - cx + nesting_x. ✓

    Simpler approach: just translate the original polygon by the nesting offset,
    then read off where its bounding box landed on the sheet.
    """
    from shapely import affinity as _aff

    # Build part_id -> original index lookup
    id_to_index = {p["part_id"]: i for i, p in enumerate(parts)}

    # Build part_id -> PartSpec lookup for centroid info
    spec_map = {ps.part_id: ps for ps in job.parts}

    # Group placements by sheet
    sheets_map: dict[int, list[PartPlacement]] = {}
    for pl in nest_result.placements:
        orig_idx = id_to_index.get(pl.part_id, 0)
        rotated = pl.transform.angle_deg in (90.0, 270.0)

        # Convert nesting coordinates to svg_export coordinates.
        # The nesting engine centred the polygon at origin before placing.
        # svg_export expects pl.x/pl.y to be the sheet position of the
        # original polygon's bounding-box min corner.
        orig_poly = parts[orig_idx]["polygon"]
        orig_bbox = orig_poly.bounds  # (minx, miny, maxx, maxy)
        cx, cy = orig_poly.centroid.x, orig_poly.centroid.y

        # The nesting engine centred the poly by translating (-cx, -cy),
        # then optionally rotated it, then placed it at (pl.x, pl.y).
        # To find where the original poly's bbox min ends up on the sheet:
        #
        # For the unrotated case (angle=0):
        #   placed poly = translate(translate(orig, -cx, -cy), pl.x, pl.y)
        #               = translate(orig, pl.x - cx, pl.y - cy)
        #   placed bbox min = (orig_minx + pl.x - cx, orig_miny + pl.y - cy)
        #
        # svg_export does: dx = target_x - orig_minx, so:
        #   target_x = orig_minx + pl.x - cx → target_x = pl.x + orig_minx - cx
        #
        # For rotated case, we need to actually simulate the transform to find
        # where the bounding box ends up.

        spec = spec_map.get(pl.part_id)
        if spec and spec.variants:
            # Find the variant that matches this placement's transform
            matching = [v for v in spec.variants if v.transform == pl.transform]
            if matching:
                variant = matching[0]
                # The variant.polygon is the centred + transformed polygon.
                # Translate it to the placed position.
                placed = _aff.translate(variant.polygon, xoff=pl.x, yoff=pl.y)
                placed_bbox = placed.bounds
                # svg_export wants target_x such that:
                #   translate(orig_poly, target_x - orig_bbox[0], target_y - orig_bbox[1])
                # lands the poly at the right spot.
                # For rotated parts, svg_export also applies rotation after translation,
                # so we just need the bounding box origin.
                target_x = placed_bbox[0]
                target_y = placed_bbox[1]
            else:
                # Fallback: use simple offset
                target_x = pl.x + orig_bbox[0] - cx
                target_y = pl.y + orig_bbox[1] - cy
        else:
            target_x = pl.x + orig_bbox[0] - cx
            target_y = pl.y + orig_bbox[1] - cy

        pp = PartPlacement(
            copy_index=0,
            x=target_x,
            y=target_y,
            rotated_90=rotated,
            part_index=orig_idx,
        )
        sheets_map.setdefault(pl.sheet_index, []).append(pp)

    # Build SheetLayout list
    sheet_layouts: list[SheetLayout] = []
    usable_w = job.sheets.width - 2.0 * job.sheets.edge_margin
    usable_h = job.sheets.height - 2.0 * job.sheets.edge_margin
    usable_area = usable_w * usable_h

    for si in sorted(sheets_map.keys()):
        placements = sheets_map[si]
        # Compute utilization
        total_area = sum(
            parts[p.part_index]["area"] for p in placements
        )
        util = min(total_area / usable_area, 1.0) if usable_area > 0 else 0.0

        sheet_layouts.append(
            SheetLayout(
                sheet_index=si + 1,  # 1-based
                placements=placements,
                utilization=util,
            )
        )

    return LayoutResult(
        sheets=sheet_layouts,
        overflow=len(nest_result.unplaced),
    )


def run_nesting(
    parts: list[dict],
    config: CanonicalConfig,
    mode: str = "balanced",
    on_progress: "Callable[[int, int], None] | None" = None,
) -> LayoutResult:
    """
    End-to-end nesting: profiler output + config → LayoutResult.

    Falls back to FFD packer if the nesting engine fails for any reason.
    The returned LayoutResult has an `engine` attribute indicating which
    engine produced the result ("nesting" or "ffd").
    """
    try:
        from .solver.solve import solve_nest

        logger.info("Nesting engine starting: %d parts, mode=%s", len(parts), mode)
        job = prepare_nest_job(parts, config, mode=mode)
        logger.info(
            "NestJob ready: %d part specs, %d variants on first part",
            len(job.parts),
            len(job.parts[0].variants) if job.parts else 0,
        )
        result = solve_nest(job, mode=mode, on_progress=on_progress)
        logger.info(
            "Nesting complete: %d sheets, %.1f%% util, %d placed, %d unplaced, %.0fms",
            result.sheets_used,
            result.utilization * 100,
            len(result.placements),
            len(result.unplaced),
            result.elapsed_ms,
        )
        layout = nest_result_to_layout_result(result, parts, job)
        layout.engine = "nesting"  # type: ignore[attr-defined]
        return layout
    except Exception as exc:
        import traceback
        tb = traceback.format_exc()
        logger.error(
            "Nesting engine FAILED — falling back to FFD.\n"
            "Exception: %s: %s\n"
            "Traceback:\n%s",
            type(exc).__name__, exc, tb,
        )
        layout = run_slat_layout(parts, config)
        layout.engine = "ffd"  # type: ignore[attr-defined]
        return layout
