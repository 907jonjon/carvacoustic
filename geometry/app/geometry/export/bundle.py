"""
Export bundle assembly.

Milestone B bundle contents:
  manifest.json        — metadata and file inventory
  project-config.json  — the canonical config that produced this bundle
  sheet-01.dxf         — DXF with all spec layers
  sheet-01.svg         — standalone SVG (file variant)
  README.txt           — human-readable handoff notes for Vectric

Milestone C will add:
  reference.pdf        — reference sheet with part labels
"""

from __future__ import annotations

import json
import zipfile
import io
from datetime import datetime, timezone

from shapely.geometry import Polygon

from ...models import CanonicalConfig, ExportManifest
from .dxf_export import create_dxf
from .svg_export import generate_file_svg

_README_TEMPLATE = """\
CarvAcoustic Export Bundle
==========================
Project : {project_name}
Mode    : {mode}
Units   : {units}
Generated: {generated_at}

Files
-----
  manifest.json        Bundle metadata
  project-config.json  Source config (schema v{schema_version})
  sheet-01.dxf         Cut geometry — import into Vectric
  sheet-01.svg         SVG reference geometry

DXF Layers
----------
  CUT_OUTER           Outer panel boundary cut
  CUT_INNER           Pattern cut paths
  ENGRAVE_LABEL       Part labels (engrave only)
  REFERENCE_BOUNDARY  Reference outline (do not cut)
  SAFE_MARGIN_GUIDE   Safe margin guide (do not cut)

Vectric Handoff
---------------
1. Import sheet-01.dxf into Vectric Aspire / VCarve Pro.
2. Confirm job size and material settings.
3. Assign toolpaths to CUT_OUTER and CUT_INNER layers.
4. Do NOT assign toolpaths to REFERENCE_BOUNDARY or SAFE_MARGIN_GUIDE.
5. Run simulation before cutting.

CarvAcoustic does NOT generate G-code. All toolpath setup is done in Vectric.
"""


def build_export_bundle(
    config: CanonicalConfig,
    boundary_poly: Polygon,
    safe_poly: Polygon,
    bands: list[Polygon],
    labels: list[dict],
) -> tuple[bytes, str]:
    """
    Assemble the export ZIP bundle.

    Returns (zip_bytes, filename).
    """
    units = config.project.units.value
    generated_at = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_name = _safe_filename(config.project.name)
    zip_filename = f"carvacoustic-{safe_name}-{generated_at}.zip"

    # Build artifacts
    dxf_bytes = create_dxf(boundary_poly, safe_poly, bands, labels, units)
    svg_string = generate_file_svg(boundary_poly, safe_poly, bands, labels, units)

    manifest = ExportManifest(
        schema_version="1.0.0",
        project_name=config.project.name,
        mode=config.project.mode,
        units=config.project.units,
        generated_at=generated_at,
        files=[
            "manifest.json",
            "project-config.json",
            "sheet-01.dxf",
            "sheet-01.svg",
            "README.txt",
        ],
    )

    readme = _README_TEMPLATE.format(
        project_name=config.project.name,
        mode=config.project.mode.value,
        units=units,
        generated_at=generated_at,
        schema_version=config.schema_version,
    )

    # Assemble ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", manifest.model_dump_json(indent=2))
        zf.writestr(
            "project-config.json",
            config.model_dump_json(indent=2),
        )
        zf.writestr("sheet-01.dxf", dxf_bytes)
        zf.writestr("sheet-01.svg", svg_string.encode("utf-8"))
        zf.writestr("README.txt", readme.encode("utf-8"))

    return buf.getvalue(), zip_filename


def _safe_filename(name: str) -> str:
    """Sanitise project name for use in a filename."""
    import re
    sanitised = re.sub(r"[^a-zA-Z0-9_-]", "-", name)
    sanitised = re.sub(r"-{2,}", "-", sanitised).strip("-")
    return sanitised[:48] or "project"
