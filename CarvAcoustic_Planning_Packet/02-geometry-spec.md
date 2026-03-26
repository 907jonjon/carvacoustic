# 02 — Geometry Spec

## Approved phase-1 modes
```yaml
phase_1_modes:
  wall_art:
    construction: surface_panel_only
  cabinet_front_panel:
    construction: surface_panel_only
  architectural_face_panel:
    construction: surface_panel_only
```

## Reserved decorative phase-2 mode
```yaml
reserved_decorative_phase_2:
  wall_art_slotted_relief:
    construction: backer_plus_slots_plus_profiles
```

## Approved phase-1 pattern families
- `wave_field`
- `contour_bands`
- `slat_rib`

Do not add more in phase 1.

## Geometry pipeline
1. Normalize boundary
2. Apply safe margin
3. Generate raw pattern guides
4. Clip guides to boundary
5. Convert guides to cut geometry
6. Merge and clean geometry
7. Place labels
8. Generate parts list
9. Run validation
10. Layout to sheets
11. Assemble export-ready artifacts

## Boundary normalization
Must:
- ensure closed outer shape
- remove duplicate points
- simplify micro-segments below threshold
- normalize winding/orientation
- compute inner safe boundary

Reject if:
- self-intersection
- multiple disconnected outer loops
- zero-area shape

## Pattern-family intent

### wave_field
- Build repeated guide lines across the usable boundary.
- Displace guides by a smooth wave function.
- Clip to boundary.
- Convert to line/band geometry based on fabrication settings.

### contour_bands
- Generate inward offset bands from boundary or center guide.
- Enforce spacing threshold.
- Clip and clean each band.

### slat_rib
- Generate repeated linear members.
- Allow straight or lightly curved guide path.
- Clip to boundary.
- Preserve edge-safe margin.

## Determinism rule
The same canonical config must produce the same:
- part count
- part IDs
- sheet count
- export file names

## Label placement
- Labels must be separate from cut geometry.
- Labels should land in low-risk areas.
- Validation should warn if a label is too close to a cut edge.

## Dogbones
- Dogbones are optional in phase 1.
- Only apply where inside corners cannot be cleared by the selected tool radius.
- Default should be off for purely decorative surface panels unless required.

## Layout / nesting
Phase 1 is usable layout, not optimal nesting.

Use:
1. rectangular footprints
2. descending area sort
3. first-fit decreasing placement
4. optional 90-degree rotation
5. spill to new sheet when needed

Respect:
- border gap
- part clearance
- grain lock if enabled

## Validation rules

### Errors
- invalid boundary
- feature below minimum
- impossible inside radius
- self-intersection
- open cut geometry
- sheet overflow
- duplicate part ID
- imported SVG parse failure

### Warnings
- thin bridge
- label too close to cut edge
- high part count
- grain conflict
- very small part
- low material utilization

### Info
- default preset in use
- layout spans multiple sheets
- dogbones not applied

## Export layers
```yaml
dxf_layers:
  - CUT_OUTER
  - CUT_INNER
  - ENGRAVE_LABEL
  - REFERENCE_BOUNDARY
  - SAFE_MARGIN_GUIDE
reserved_future_layers:
  - HANGING_HARDWARE
  - SUSPENSION_POINTS
  - ACOUSTIC_REFERENCE
```

## Export bundle
Must include:
- `manifest.json`
- `project-config.json`
- per-sheet DXF
- per-sheet SVG
- reference PDF
- package README

## Reserved future acoustic validators
- missing_room_dimensions
- missing_surface_data
- missing_installation_constraints
- missing_suspension_data
- low_confidence_measurement_data
