# 01 — Schema Contracts

## Core entities
- project
- project_version
- boundary
- pattern
- material_preset
- tool_preset
- validation_report
- part
- sheet_layout
- export_bundle
- asset
- reserved_acoustic_intake

## Project modes
```yaml
modes:
  - wall_art
  - cabinet_front_panel
  - architectural_face_panel
reserved_future_modes:
  - acoustic_wall_absorber
  - acoustic_cloud
  - acoustic_resonant_panel
```

## Canonical config schema
```json
{
  "schema_version": "1.0.0",
  "project": {
    "name": "Lobby Wave Panel",
    "mode": "wall_art",
    "units": "in"
  },
  "boundary": {
    "type": "svg_import",
    "width": 60,
    "height": 48,
    "corner_radius": 0,
    "asset_id": null,
    "safe_margin": 1.0
  },
  "pattern": {
    "family": "wave_field",
    "density": 0.65,
    "spacing": 1.2,
    "line_width": 0.4,
    "amplitude": 0.8,
    "seed": 42,
    "symmetry": "none"
  },
  "fabrication": {
    "material": {
      "thickness": 0.75,
      "sheet_width": 96,
      "sheet_height": 48,
      "min_bridge": 0.3,
      "grain_direction": "x"
    },
    "tool": {
      "tool_diameter": 0.25,
      "kerf_allowance": 0.0,
      "min_inside_radius": 0.125,
      "dogbone_style": "classic",
      "clearance": 0.125,
      "border_gap": 0.75
    }
  },
  "layout": {
    "enabled": true,
    "copies": 1,
    "rotation_mode": "90_only",
    "preserve_grain": false
  },
  "labeling": {
    "enabled": true,
    "prefix": "P",
    "position": "footer"
  },
  "export": {
    "formats": ["dxf", "svg", "pdf", "json"],
    "units": "in"
  },
  "reserved_acoustic": {
    "enabled": false,
    "room_use": null,
    "target_issue": null,
    "room_dimensions": null,
    "surface_summary": null,
    "installation_constraints": null,
    "attachments": []
  }
}
```

## Schema rules
- Keep one canonical config object per version.
- Keep editable draft separate from immutable versions.
- Derived geometry must not live inside editable config.
- `reserved_acoustic` must exist but remain inert in phase 1.
- Validate config on web side and geometry side.

## Suggested SQL tables
- profiles
- projects
- project_versions
- material_presets
- tool_presets
- assets
- export_bundles

## Minimal table intent
- `projects`: top-level mutable records
- `project_versions`: immutable snapshots for save checkpoints and exports
- `material_presets` / `tool_presets`: reusable fabrication defaults
- `assets`: imported SVG boundaries, future uploads
- `export_bundles`: stored export packages and manifests

## Storage buckets
- `boundary-assets`
- `export-bundles`
- `reserved-future-intake`

## Versioning rules
- Create a new immutable version on explicit save checkpoint or export.
- Never overwrite a previously exported version.
- Allow a current draft to differ from latest immutable version.
