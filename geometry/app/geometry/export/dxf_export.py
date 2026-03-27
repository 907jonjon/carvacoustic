"""
DXF export using ezdxf.

Spec layers (02-geometry-spec.md):
  CUT_OUTER           — outer boundary cut path
  CUT_INNER           — pattern cut paths (wave bands)
  ENGRAVE_LABEL       — text labels
  REFERENCE_BOUNDARY  — reference outline (no cut)
  SAFE_MARGIN_GUIDE   — inner safe-margin guide (no cut)

Reserved future layers (not created here):
  HANGING_HARDWARE / SUSPENSION_POINTS / ACOUSTIC_REFERENCE
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

import ezdxf
from shapely.geometry import MultiPolygon, Polygon

if TYPE_CHECKING:
    from ezdxf.layouts.layouts import Modelspace

# ── Layer definitions ─────────────────────────────────────────────────────────
# DXF colour index: 1=red 2=yellow 3=green 5=blue 7=white/black 8=grey
_LAYERS: dict[str, dict] = {
    "CUT_OUTER":          {"color": 1, "linetype": "CONTINUOUS"},  # red
    "CUT_INNER":          {"color": 5, "linetype": "CONTINUOUS"},  # blue
    "ENGRAVE_LABEL":      {"color": 3, "linetype": "CONTINUOUS"},  # green
    "REFERENCE_BOUNDARY": {"color": 7, "linetype": "CONTINUOUS"},  # white/black
    "SAFE_MARGIN_GUIDE":  {"color": 8, "linetype": "DASHED"},      # grey
}

# Supabase INSUNITS: 1=inches, 4=mm
_INSUNITS = {"in": 1, "mm": 4}


def create_dxf(
    boundary_poly: Polygon,
    safe_poly: Polygon,
    bands: list[Polygon],
    labels: list[dict],
    units: str,
) -> bytes:
    """
    Build a DXF R2010 document and return it as UTF-8 bytes.

    Args:
        boundary_poly: outer panel boundary
        safe_poly:     inner safe-margin boundary
        bands:         list of cut-band Polygons (CUT_INNER layer)
        labels:        list of {"text": str, "x": float, "y": float, "height": float}
        units:         "in" or "mm"
    """
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = _INSUNITS.get(units, 1)

    # Ensure DASHED linetype exists
    if "DASHED" not in doc.linetypes:
        doc.linetypes.new("DASHED", dxfattribs={"description": "Dashed"})

    msp: Modelspace = doc.modelspace()

    # Create spec layers
    for name, attrs in _LAYERS.items():
        doc.layers.new(name=name, dxfattribs=attrs)

    # ── REFERENCE_BOUNDARY ──────────────────────────────────────────────────
    _add_geometry(msp, boundary_poly, "REFERENCE_BOUNDARY")

    # ── SAFE_MARGIN_GUIDE ───────────────────────────────────────────────────
    _add_geometry(msp, safe_poly, "SAFE_MARGIN_GUIDE")

    # ── CUT_OUTER ───────────────────────────────────────────────────────────
    _add_geometry(msp, boundary_poly, "CUT_OUTER")

    # ── CUT_INNER ───────────────────────────────────────────────────────────
    for band in bands:
        _add_geometry(msp, band, "CUT_INNER")

    # ── ENGRAVE_LABEL ───────────────────────────────────────────────────────
    for lbl in labels:
        height = lbl.get("height", _default_label_height(boundary_poly))
        text = msp.add_text(
            lbl["text"],
            dxfattribs={
                "layer": "ENGRAVE_LABEL",
                "height": height,
                "halign": 1,  # centre
            },
        )
        text.dxf.insert = (lbl["x"], lbl["y"])
        text.dxf.align_point = (lbl["x"], lbl["y"])

    # Serialise to bytes
    buf = io.StringIO()
    doc.write(buf)
    return buf.getvalue().encode("utf-8")


def _add_geometry(msp: "Modelspace", geom: object, layer: str) -> None:
    """Add a Shapely Polygon or MultiPolygon as closed LWPOLYLINE(s)."""
    if isinstance(geom, MultiPolygon):
        for g in geom.geoms:
            _add_geometry(msp, g, layer)
        return

    if not isinstance(geom, Polygon) or geom.is_empty:
        return

    # Exterior ring
    _add_ring(msp, list(geom.exterior.coords), layer)

    # Interior rings (holes)
    for interior in geom.interiors:
        _add_ring(msp, list(interior.coords), layer)


def _add_ring(msp: "Modelspace", coords: list[tuple], layer: str) -> None:
    pts = coords[:-1] if coords and coords[0] == coords[-1] else coords
    if len(pts) < 2:
        return
    msp.add_lwpolyline(
        [(x, y) for x, y in pts],
        dxfattribs={"layer": layer, "closed": True},
    )


def _default_label_height(boundary_poly: Polygon) -> float:
    """Reasonable label text height: 2% of the shorter boundary dimension."""
    minx, miny, maxx, maxy = boundary_poly.bounds
    return min(maxx - minx, maxy - miny) * 0.02
