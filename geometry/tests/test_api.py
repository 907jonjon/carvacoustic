"""
FastAPI endpoint integration tests.

Uses httpx AsyncClient with the app in test mode (no real Supabase).
The X-API-Key header is set to the dev default "dev-secret".
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app

API_KEY = "dev-secret"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def wave_cfg_dict():
    return {
        "schema_version": "1.0.0",
        "project": {"name": "Test Panel", "mode": "wall_art", "units": "in"},
        "boundary": {
            "type": "rectangle",
            "width": 24,
            "height": 20,
            "corner_radius": 0,
            "asset_id": None,
            "safe_margin": 0.5,
        },
        "pattern": {
            "family": "wave_field",
            "density": 0.5,
            "spacing": 1.5,
            "line_width": 0.4,
            "amplitude": 0.5,
            "seed": 1,
            "symmetry": "none",
        },
        "fabrication": {
            "material": {
                "thickness": 0.75,
                "sheet_width": 48,
                "sheet_height": 24,
                "min_bridge": 0.3,
                "grain_direction": "x",
            },
            "tool": {
                "tool_diameter": 0.25,
                "kerf_allowance": 0.0,
                "min_inside_radius": 0.125,
                "dogbone_style": "classic",
                "clearance": 0.125,
                "border_gap": 0.5,
            },
        },
        "layout": {"enabled": True, "copies": 1, "rotation_mode": "90_only", "preserve_grain": False},
        "labeling": {"enabled": True, "prefix": "T", "position": "footer"},
        "export": {"formats": ["dxf", "svg", "pdf", "json"], "units": "in"},
        "reserved_acoustic": {
            "enabled": False,
            "room_use": None,
            "target_issue": None,
            "room_dimensions": None,
            "surface_summary": None,
            "installation_constraints": None,
            "attachments": [],
        },
    }


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_generate_returns_ok(wave_cfg_dict):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.post(
            "/generate", headers=HEADERS, json={"config": wave_cfg_dict}
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "ok"
    assert data["part_count"] > 0
    assert data["svg_preview"].startswith("<svg")
    assert data["validation"]["valid"] is True


@pytest.mark.asyncio
async def test_generate_wrong_api_key(wave_cfg_dict):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.post(
            "/generate",
            headers={"X-API-Key": "wrong", "Content-Type": "application/json"},
            json={"config": wave_cfg_dict},
        )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_generate_missing_config():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.post(
            "/generate", headers=HEADERS, json={"wrong_key": {}}
        )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_validate_returns_valid(wave_cfg_dict):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.post(
            "/validate", headers=HEADERS, json={"config": wave_cfg_dict}
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["valid"] is True
    errors = [i for i in data["issues"] if i["level"] == "error"]
    assert not errors


@pytest.mark.asyncio
async def test_validate_detects_feature_below_minimum(wave_cfg_dict):
    """v2: tab_width smaller than tool_diameter triggers feature_below_minimum."""
    import copy
    cfg = copy.deepcopy(wave_cfg_dict)
    # Force to v2 with a tab_width smaller than the tool diameter
    cfg["schema_version"] = "2.0.0"
    cfg["surface"] = {
        "type": "wave", "max_depth": 3.0, "min_depth": 0.0,
        "amplitude": 0.7, "frequency": 3.0, "phase": 0.0,
        "flow_direction": "x", "symmetry": "none", "smoothness": 0.5,
        "seed": 42, "noise_amount": 0.2,
    }
    cfg["slats"] = {
        "count": 10, "spacing": 0.75, "thickness": 0.75,
        "base_height": 1.5,
        "tab_width": 0.1,  # < tool_diameter=0.25 → feature_below_minimum
        "tab_depth": 0.75, "tab_count": 3, "tab_clearance": 0.01,
    }
    cfg["backing"] = {
        "enabled": True, "width": 24.0, "height": 3.0,
        "slot_width": 0.76, "slot_depth": 0.75, "mounting_holes": True,
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.post(
            "/validate", headers=HEADERS, json={"config": cfg}
        )
    assert r.status_code == 200
    data = r.json()
    assert data["valid"] is False
    codes = [i["code"] for i in data["issues"]]
    assert "feature_below_minimum" in codes


@pytest.mark.asyncio
async def test_export_returns_zip(wave_cfg_dict):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.post(
            "/export", headers=HEADERS, json={"config": wave_cfg_dict}
        )
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/zip"
    assert "attachment" in r.headers["content-disposition"]
    assert len(r.content) > 1000


@pytest.mark.asyncio
async def test_layout_returns_sheet_info(wave_cfg_dict):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.post(
            "/layout", headers=HEADERS, json={"config": wave_cfg_dict}
        )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "ok"
    assert data["sheet_count"] >= 1
    assert len(data["placements"]) == wave_cfg_dict["layout"]["copies"]


@pytest.mark.asyncio
async def test_generate_contour_bands(wave_cfg_dict):
    import copy
    cfg = copy.deepcopy(wave_cfg_dict)
    cfg["pattern"]["family"] = "contour_bands"
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.post(
            "/generate", headers=HEADERS, json={"config": cfg}
        )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"
    assert r.json()["part_count"] > 0


@pytest.mark.asyncio
async def test_generate_slat_rib(wave_cfg_dict):
    import copy
    cfg = copy.deepcopy(wave_cfg_dict)
    cfg["pattern"]["family"] = "slat_rib"
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r = await client.post(
            "/generate", headers=HEADERS, json={"config": cfg}
        )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "ok"
    assert r.json()["part_count"] > 0


@pytest.mark.asyncio
async def test_generate_determinism(wave_cfg_dict):
    """Two identical requests must return identical results."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        r1 = await client.post("/generate", headers=HEADERS, json={"config": wave_cfg_dict})
        r2 = await client.post("/generate", headers=HEADERS, json={"config": wave_cfg_dict})
    assert r1.json()["part_count"] == r2.json()["part_count"]
    assert r1.json()["svg_preview"] == r2.json()["svg_preview"]
