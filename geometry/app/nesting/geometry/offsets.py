"""Clearance inflation model — inflate parts, contract sheets."""

from __future__ import annotations

from shapely.geometry import Polygon, box

from ..models import SheetSpec


def inflate_part(poly: Polygon, clearance: float) -> Polygon:
    """Inflate part by clearance/2. Uses Shapely buffer with round joins."""
    return poly.buffer(clearance / 2.0, quad_segs=16, join_style="round")


def contract_sheet(sheet: SheetSpec, clearance: float) -> Polygon:
    """
    Contract usable sheet by edge_margin + clearance/2.

    Returns a Polygon representing the usable placement area.
    Clearance model: inflate each part by clearance/2, contract sheet by
    edge_margin + clearance/2.  All feasibility checks then happen in one
    geometry space.
    """
    inset = sheet.edge_margin + clearance / 2.0
    return box(inset, inset, sheet.width - inset, sheet.height - inset)
