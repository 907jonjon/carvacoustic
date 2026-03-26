# CarvAcoustic — Report 2
## Technical Build Specification for Phase 1
### Decorative-first, acoustic-ready architecture reservations

## 0. How to use this spec

This spec is normative.

Interpret labels as:
- MUST = required in phase 1
- SHOULD = recommended default
- RESERVED = create room for later, do not implement now
- OUT OF SCOPE = do not build in phase 1

## 1. Canonical decisions

```yaml
product:
  canonical_name: CarvAcoustic
  domain: carvacoustic.com
  phase_1_focus:
    - decorative_wall_art
    - decorative_cabinet_front_panels
    - decorative_architectural_face_panels
  downstream_cam: vectric
  build_priority:
    - geometry_generation
    - manufacturability_validation
    - export_quality
    - project_persistence
    - workflow_usability
  explicit_non_goals_phase_1:
    - full_cam_replacement
    - gcode_generation
    - acoustic_generation_logic
    - cloud_suspension_generation
    - manufacturing_operations
    - packaging_shipping_logic
    - marketing_automation
```

## 2. Phase 1 technical scope

### MUST implement
```yaml
phase_1_must_build:
  app_shell:
    - auth
    - dashboard
    - project_list
    - create_project_flow
    - edit_project_flow
  design_modes:
    - wall_art
    - cabinet_front_panel
    - architectural_face_panel
  boundary_inputs:
    - rectangle
    - rounded_rectangle
    - imported_svg_boundary
  pattern_families:
    - wave_field
    - contour_bands
    - slat_rib
  processing:
    - geometry_generation
    - validation
    - sheet_layout
    - export_bundle
  persistence:
    - save_project
    - project_versions
    - presets
  exports:
    - dxf
    - svg
    - pdf_reference
    - json_manifest
```

### RESERVED for later
```yaml
reserved_later:
  decorative_phase_2:
    - slotted_relief_wall_art
    - richer_pattern_families
    - better_layout_optimization
  acoustic_future:
    - acoustic_wall_modes
    - acoustic_cloud_modes
    - room_intake_forms
    - vendor_intake
    - measurement_uploads
    - suspension_points
    - acoustic_specific_validators
```

### OUT OF SCOPE
```yaml
phase_1_out_of_scope:
  - acoustic_calculations
  - acoustic_performance_claims
  - cloud_suspension_geometry
  - automatic_toolpath_assignment
  - post_processor_output
  - machine_specific_gcode
  - quoting_checkout_fulfillment
```

## 3. System architecture

```yaml
architecture:
  frontend:
    framework: nextjs_app_router
    runtime: vercel
    language: typescript
  backend_bff:
    location: nextjs_route_handlers
    responsibilities:
      - auth_session_check
      - project_crud
      - config_validation
      - geometry_service_proxy
      - export_bundle_orchestration
  data_platform:
    provider: supabase
    services:
      - postgres
      - auth
      - storage
  geometry_service:
    language: python
    framework: fastapi
    libs:
      - shapely
      - ezdxf
    responsibilities:
      - generate_geometry
      - validate_geometry
      - layout_parts
      - prepare_export_data
  downstream:
    vectric_manual_handoff: true
```

### Runtime responsibilities
- Browser: UI, forms, SVG preview, draft state, export/download UI
- Next.js Route Handlers: auth, CRUD, schema enforcement, geometry service calls, export orchestration
- Geometry service: canonical geometry generation, validation, layout, DXF/SVG/PDF-ready data
- Supabase: auth, relational data, storage, row ownership
- Future Windows tool: reserved only

### Job model
- MUST use synchronous generation for phase 1
- RESERVED async jobs only if real latency demands it

## 4. Recommended technology choices

```yaml
tech_choices:
  web:
    - nextjs_app_router
    - typescript
    - tailwindcss
    - react_hook_form
    - zod
    - zustand
  data:
    - supabase_auth
    - supabase_postgres
    - supabase_storage
  geometry:
    - python
    - fastapi
    - shapely
    - ezdxf
  rendering:
    - native_svg
  packaging:
    - zip_bundle_generation
```

## 5. Repository structure

```text
carvacoustic/
  apps/
    web/
      app/
        (marketing)/
        app/
        api/
      components/
      features/
      lib/
      styles/
    geometry-service/
      app/
      domain/
      generators/
      validators/
      layout/
      exporters/
      tests/
  packages/
    schemas/
    shared-types/
    ui/
    config/
    docs-contracts/
  docs/
    00-governing/
    01-product/
    02-architecture/
    03-geometry/
    04-validation/
    05-export/
    06-prompts/
    07-qa/
```

Rules:
- MUST keep web and geometry separated
- MUST keep shared schemas/types in their own package
- SHOULD keep docs in-repo and versioned

## 6. Domain model

```yaml
domain_entities:
  project:
    purpose: top_level_container
  project_version:
    purpose: immutable_snapshot_of_config_and_results
  boundary:
    purpose: outer_shape_definition
  pattern:
    purpose: decorative_generator_definition
  material_preset:
    purpose: fabrication_defaults
  tool_preset:
    purpose: cutter_defaults
  validation_report:
    purpose: errors_warnings_info
  part:
    purpose: generated_cuttable_unit
  sheet_layout:
    purpose: positioned_parts_per_sheet
  export_bundle:
    purpose: downloadable_output_package
  asset:
    purpose: imported_svg_or_future_upload
  reserved_acoustic_intake:
    purpose: future_room_site_data_placeholder
```

## 7. Data model and persistence

### SQL-style schema summary
Tables:
- profiles
- projects
- project_versions
- material_presets
- tool_presets
- assets
- export_bundles

Storage buckets:
- boundary-assets
- export-bundles
- reserved-future-intake

Versioning rules:
- MUST keep editable draft separate from immutable versions
- MUST create new version on explicit save checkpoint or export
- SHOULD NOT overwrite prior exported versions

## 8. Configuration schema

### Canonical config object
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
    "asset_id": "uuid-or-null",
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
    "intake_id": null
  }
}
```

Schema rules:
- MUST version the config schema
- MUST keep one canonical config object per version
- MUST keep reserved_acoustic present but inert
- SHOULD validate with Zod on web side and Pydantic on geometry side
- SHOULD NOT store derived geometry inside editable config

## 9. Geometry engine specification

### Core rule
Pure transformation:
`config -> normalized_boundary -> generated_pattern -> validated_parts -> layout -> export_artifacts`

### Supported phase-1 modes
```yaml
phase_1_modes:
  wall_art:
    construction: surface_panel_only
  cabinet_front_panel:
    construction: surface_panel_only
  architectural_face_panel:
    construction: surface_panel_only
reserved_decorative_phase_2:
  wall_art_slotted_relief:
    construction: backer_plus_slots_plus_profiles
```

### Supported pattern families
- wave_field
- contour_bands
- slat_rib

### Geometry pipeline
1. normalize boundary
2. apply safe margin
3. generate raw pattern guides
4. clip guides to boundary
5. convert guides to cut geometry
6. merge/clean geometry
7. place labels
8. generate parts list
9. validate
10. layout to sheets
11. assemble export-ready entities

### Boundary normalization
Must:
- ensure closed shape
- remove duplicate points
- simplify micro-segments below threshold
- normalize orientation
- compute inner safe boundary

Invalid:
- self-intersection
- disconnected outer loops
- zero area

### Pseudocode
```python
def generate_project(config):
    boundary = normalize_boundary(config.boundary)
    inner_boundary = apply_safe_margin(boundary, config.boundary.safe_margin)

    pattern = build_pattern(
        family=config.pattern.family,
        boundary=inner_boundary,
        pattern_cfg=config.pattern
    )

    cut_geometry = convert_pattern_to_parts(
        family=config.pattern.family,
        pattern=pattern,
        fabrication=config.fabrication
    )

    labels = place_labels(cut_geometry.parts, config.labeling)

    validation = run_validation(
        boundary=inner_boundary,
        parts=cut_geometry.parts,
        fabrication=config.fabrication,
        labels=labels
    )

    layout = None
    if config.layout.enabled and not validation.has_blocking_errors:
        layout = layout_parts(
            parts=cut_geometry.parts,
            layout_cfg=config.layout,
            fabrication=config.fabrication
        )

    return {
        "boundary": boundary,
        "parts": cut_geometry.parts,
        "labels": labels,
        "validation": validation,
        "layout": layout
    }
```

## 10. Validation engine specification

### Severity levels
```yaml
severity:
  error: export_blocked
  warning: export_allowed_but_risky
  info: advisory_only
```

### Required validation rules
```yaml
errors:
  - boundary_invalid
  - feature_below_minimum
  - inside_radius_impossible
  - self_intersection_detected
  - open_cut_geometry
  - sheet_overflow
  - duplicate_part_id
  - imported_svg_parse_failure

warnings:
  - bridge_thin
  - label_close_to_cut_edge
  - high_part_count
  - grain_conflict
  - low_material_utilization
  - very_small_part

info:
  - export_uses_default_preset
  - layout_spans_multiple_sheets
  - dogbones_not_applied
```

### Validation contract
```json
{
  "has_blocking_errors": true,
  "items": [
    {
      "code": "feature_below_minimum",
      "severity": "error",
      "message": "Feature width 0.18 is below minimum bridge 0.30",
      "target": "part:P12",
      "suggestion": "Increase spacing or line width"
    }
  ]
}
```

### Future acoustic validator reservations
```yaml
reserved_acoustic_validators:
  - missing_room_dimensions
  - missing_surface_data
  - missing_installation_constraints
  - missing_suspension_data
  - low_confidence_measurement_data
```

## 11. Layout / nesting system specification

### Phase-1 rule
Implement usable sheet layout, not optimal polygon nesting.

Use:
- deterministic placement
- predictable spill to new sheets
- rotation limited to 0/90 in v1 by default
- border gap and clearance
- grain lock when enabled

### Suggested algorithm
1. compute rectangular footprint for each part
2. sort by descending footprint area
3. place by first-fit decreasing
4. allow 90-degree rotation if permitted
5. spill to new sheet when no fit remains

## 12. Export system specification

### Required bundle
```yaml
export_bundle:
  root:
    - manifest.json
    - project-config.json
    - README.txt
  sheets:
    - sheet-01.dxf
    - sheet-01.svg
    - sheet-02.dxf
    - sheet-02.svg
  reference:
    - reference-pack.pdf
```

### Mandatory formats
- DXF = primary fabrication export
- SVG = secondary fabrication / preview export
- PDF = human-readable reference
- JSON manifest = machine-readable package index

### Layer names
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

## 13. Vectric handoff conventions

CarvAcoustic delivers:
- clean vectors
- sheet files
- part IDs
- reference PDF
- manifest

Founder still does in Vectric:
- import files
- confirm job size/material
- assign toolpaths
- set tabs/holds if needed
- run machine simulation
- post-process machine output

Reserved future companion scope:
- import export bundle
- create jobs/sheets
- map layers to toolpath templates
- batch recalculate
- post-process named outputs

## 14. Website/app UX implementation specification

### Route map
```text
/
  landing page
/login
  auth
/app
  dashboard
/app/projects/new
  create project
/app/projects/[id]
  project summary
/app/projects/[id]/edit
  design workspace
/app/projects/[id]/exports
  export history
/docs
  help and usage notes
```

### Design workspace layout
```yaml
workspace_layout:
  left_panel:
    - mode
    - dimensions
    - boundary
    - pattern
    - fabrication
    - layout
    - export settings
  center_panel:
    - svg_preview
    - sheet_preview_toggle
  right_panel:
    - validation_list
    - save_actions
    - generate_actions
    - export_actions
```

### Required editor sections
- setup
- pattern
- fabrication
- validation
- layout
- export

## 15. API contract specification

Required endpoints:
- POST /api/projects
- GET /api/projects/:id
- PATCH /api/projects/:id
- POST /api/projects/:id/versions
- POST /api/generate
- POST /api/validate
- POST /api/layout
- POST /api/export
- GET /api/presets/materials
- GET /api/presets/tools
- POST /api/presets/materials
- POST /api/presets/tools

Error contract:
```json
{
  "error": {
    "code": "boundary_invalid",
    "message": "Imported SVG contains self-intersecting outer loop"
  }
}
```

## 16. Acoustic-ready architecture reservations

Reserve:
- separate acoustic mode family
- future intake schema placeholders
- future validator categories
- future export metadata
- future website intake paths
- future measurement uploads
- future cloud-suspension support

Do not implement acoustic logic in phase 1.

## 17. AI coding-agent build rules

1. Build only phase-1 decorative scope.
2. Do not implement acoustic generation, intake UI, or calculations.
3. Keep geometry deterministic and stateless.
4. Treat config schema as source of truth.
5. Keep web app and geometry service separate.
6. Do not replace Vectric.
7. Do not generate G-code.
8. Write tests for every geometry family.
9. Use feature flags or reserved enums for future modes.
10. Document assumptions.
11. Never add a new pattern family without a founder-approved use case.
12. Prefer explicit contracts over clever abstractions.

## 18. Test and QA specification

### Unit tests
Web:
- schema parsing
- API request validation
- preset CRUD
- project version creation

Geometry:
- boundary normalization
- clipping behavior
- line/band generation
- label placement
- validation rules
- layout placement
- DXF/SVG/manifest assembly

### Golden sample tests
- wall_art_wave_panel
- cabinet_front_contour_panel

For each:
- generate preview
- validate
- layout
- export
- import into Vectric manually
- confirm scale/layers/closure

### Regression tests
- same config returns same part count
- same config returns same sheet count
- same config returns same part IDs
- invalid SVG stays invalid
- warnings do not silently disappear

## 19. Implementation sequence

```yaml
build_order:
  1:
    - create_repo
    - establish_docs
    - define_shared_schemas
  2:
    - scaffold_nextjs_app
    - connect_supabase_auth
    - implement_projects_crud
  3:
    - scaffold_geometry_service
    - implement_boundary_normalization
  4:
    - implement_wave_field
    - implement_contour_bands
    - implement_slat_rib
  5:
    - implement_validation_engine
  6:
    - implement_layout_engine
  7:
    - implement_export_bundle
  8:
    - wire_preview_and_editor_ui
  9:
    - run_golden_sample_tests
  10:
    - refine_errors_and_docs
```

## 20. Compact prompt pack for the coding agent

### Master build prompt
Build CarvAcoustic phase 1 exactly to the governing spec.

Scope:
- web-first app on Next.js + Supabase
- separate Python FastAPI geometry service
- decorative wall art, cabinet front panel, architectural face panel modes
- pattern families: wave_field, contour_bands, slat_rib
- boundary inputs: rectangle, rounded rectangle, imported SVG
- generate, validate, layout, export
- export DXF, SVG, PDF reference, JSON manifest
- keep Vectric downstream
- no G-code
- no acoustic implementation
