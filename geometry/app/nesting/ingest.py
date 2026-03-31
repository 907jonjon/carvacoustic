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
    """
    # Build part_id -> original index lookup
    id_to_index = {p["part_id"]: i for i, p in enumerate(parts)}

    # Group placements by sheet
    sheets_map: dict[int, list[PartPlacement]] = {}
    for pl in nest_result.placements:
        orig_idx = id_to_index.get(pl.part_id, 0)
        rotated = pl.transform.angle_deg in (90.0, 270.0)

        pp = PartPlacement(
            copy_index=0,
            x=pl.x,
            y=pl.y,
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
) -> LayoutResult:
    """
    End-to-end nesting: profiler output + config → LayoutResult.

    Falls back to FFD packer if the nesting engine fails for any reason.
    """
    try:
        from .solver.solve import solve_nest

        job = prepare_nest_job(parts, config, mode=mode)
        result = solve_nest(job, mode=mode)
        return nest_result_to_layout_result(result, parts, job)
    except Exception as exc:
        logger.warning("Nesting engine failed, falling back to FFD: %s", exc)
        return run_slat_layout(parts, config)
