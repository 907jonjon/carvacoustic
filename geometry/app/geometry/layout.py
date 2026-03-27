"""
Layout / nesting engine — Milestone C.

Spec (02-geometry-spec.md §Layout / nesting):
    Phase 1 is usable layout, not optimal nesting.

    Use:
    1. Rectangular footprints
    2. Descending area sort
    3. First-fit decreasing placement
    4. Optional 90-degree rotation
    5. Spill to new sheet when needed

    Respect:
    - border gap
    - part clearance
    - grain lock if enabled

A "part" here is one copy of the full panel design (boundary bounding box).
The layout engine places `config.layout.copies` copies on physical material
sheets and returns per-sheet placement records so the export bundle can
generate one DXF/SVG per sheet with the correct translations applied.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import Polygon

from ..models import CanonicalConfig


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class PartPlacement:
    """One copy of the design placed on a sheet."""
    copy_index: int       # 0-based copy number
    x: float              # left edge origin on sheet (in design units)
    y: float              # bottom edge origin on sheet
    rotated_90: bool      # True → design rotated 90° CCW before placement


@dataclass
class SheetLayout:
    """One physical material sheet with zero or more placed parts."""
    sheet_index: int              # 1-based
    placements: list[PartPlacement] = field(default_factory=list)
    utilization: float = 0.0      # fraction of usable sheet area occupied


@dataclass
class LayoutResult:
    """Output of the layout engine."""
    sheets: list[SheetLayout]
    overflow: int = 0  # copies that could not be placed (should be 0 normally)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_layout(boundary_poly: Polygon, config: CanonicalConfig) -> LayoutResult:
    """
    Place config.layout.copies copies of the design on material sheets.

    Returns a LayoutResult with one SheetLayout per sheet required.
    """
    if not config.layout.enabled or config.layout.copies < 1:
        return LayoutResult(sheets=[])

    mat = config.fabrication.material
    tool = config.fabrication.tool
    layout_cfg = config.layout

    sheet_w = mat.sheet_width
    sheet_h = mat.sheet_height
    border = tool.border_gap
    clearance = tool.clearance

    # Usable area on each sheet (inset by border_gap on all sides)
    usable_w = sheet_w - 2.0 * border
    usable_h = sheet_h - 2.0 * border

    # Design bounding box
    minx, miny, maxx, maxy = boundary_poly.bounds
    design_w = maxx - minx
    design_h = maxy - miny

    copies = layout_cfg.copies
    preserve_grain = layout_cfg.preserve_grain
    rotation_mode = layout_cfg.rotation_mode.value  # "none" | "90_only" | "any"

    allow_rotate = rotation_mode != "none" and not preserve_grain

    # Actual design footprints — clearance is added to the cursor advance
    # inside try_place_on_sheet, not to the fit check size.
    normal_fw = design_w
    normal_fh = design_h
    rotated_fw = design_h
    rotated_fh = design_w

    # Sheet usable area
    usable_sheet_area = usable_w * usable_h

    sheets: list[SheetLayout] = []
    overflow = 0

    # Track placements per sheet using a simple row-packing cursor
    # We maintain for each sheet: list of rows, each row has (current_x, row_height, row_y)
    # New sheet state:
    sheet_rows: list[list[tuple[float, float, float]]] = []  # per sheet: list of (cur_x, row_h, row_y)

    def new_sheet() -> int:
        """Start a new sheet, return its 0-based index."""
        sheets.append(SheetLayout(sheet_index=len(sheets) + 1))
        sheet_rows.append([])  # no rows yet
        return len(sheets) - 1

    def try_place_on_sheet(
        si: int,
        fw: float,
        fh: float,
    ) -> tuple[float, float] | None:
        """
        Try to place a footprint (fw × fh) on sheet `si`.
        Returns (x, y) origin if successful, None if it doesn't fit.
        Uses row-based packing: left-to-right, bottom-to-top.
        """
        rows = sheet_rows[si]

        # Try adding to an existing row
        for i, (cur_x, row_h, row_y) in enumerate(rows):
            if fh <= row_h and cur_x + fw <= usable_w:
                # Fits in this row; advance cursor by part width + clearance gap
                x = border + cur_x
                y = border + row_y
                rows[i] = (cur_x + fw + clearance, row_h, row_y)
                return x, y

        # Try starting a new row
        if rows:
            next_row_y = sum(rh for _, rh, _ in rows)
        else:
            next_row_y = 0.0

        # Primary check: part fits within usable area with border on both sides.
        fits_strict = next_row_y + fh <= usable_h and fw <= usable_w

        # Lenient fallback for a fresh sheet: if the part physically fits on the
        # sheet (no border considered) and this is the only thing on the sheet,
        # place it at the border position and let validation warn about overflow.
        fits_lenient = (not rows
                        and next_row_y == 0.0
                        and fw <= sheet_w
                        and fh <= sheet_h)

        if fits_strict or fits_lenient:
            x = border
            y = border + next_row_y
            rows.append((fw + clearance, fh + clearance, next_row_y))
            return x, y

        return None

    # Place all copies using first-fit decreasing (all copies are identical here,
    # but we maintain the FFD structure for correctness with future mixed parts)
    placed_area = 0.0
    current_si = new_sheet()

    for copy_idx in range(copies):
        placed = False

        # Try normal orientation first, then rotated
        orientations: list[tuple[float, float, bool]] = [(normal_fw, normal_fh, False)]
        if allow_rotate:
            orientations.append((rotated_fw, rotated_fh, True))

        for fw, fh, rotated in orientations:
            # Try current sheet first, then all existing sheets, then open a new one
            sheet_candidates = list(range(len(sheets)))

            for si in sheet_candidates:
                result = try_place_on_sheet(si, fw, fh)
                if result is not None:
                    px, py = result
                    sheets[si].placements.append(
                        PartPlacement(
                            copy_index=copy_idx,
                            x=px,
                            y=py,
                            rotated_90=rotated,
                        )
                    )
                    placed_area += design_w * design_h
                    placed = True
                    break

            if placed:
                break

            if orientations.index((fw, fh, rotated)) == len(orientations) - 1:
                # Last orientation tried — open a new sheet and retry
                current_si = new_sheet()
                result = try_place_on_sheet(current_si, fw, fh)
                if result is not None:
                    px, py = result
                    sheets[current_si].placements.append(
                        PartPlacement(
                            copy_index=copy_idx,
                            x=px,
                            y=py,
                            rotated_90=rotated,
                        )
                    )
                    placed_area += design_w * design_h
                    placed = True

        if not placed:
            overflow += 1

    # Compute utilization per sheet
    single_design_area = design_w * design_h
    for sheet in sheets:
        n = len(sheet.placements)
        sheet.utilization = (
            min(n * single_design_area / usable_sheet_area, 1.0)
            if usable_sheet_area > 0
            else 0.0
        )

    return LayoutResult(sheets=sheets, overflow=overflow)
