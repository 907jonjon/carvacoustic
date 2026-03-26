# CarvAcoustic — Report 1
## Software Product Execution, Staging, and Workflow Proof Plan

## 1. Executive summary

CarvAcoustic should start as a **web-first software tool plus authenticated app shell** that generates decorative panel geometry, validates manufacturability, nests parts, and exports Vectric-ready files for downstream toolpath creation.

Phase 1 should prove:
- decorative wall art workflows
- decorative cabinet/front-panel workflows
- geometry generation
- validation
- export quality
- project persistence
- website/app coherence

Acoustic features should be staged later because they add:
- different user inputs
- room/site data requirements
- separate validation logic
- different installation constraints
- future customer/vendor intake flows

The website should be treated as part of the product from day one:
- landing surface
- authenticated app shell
- dashboard
- docs/help surface
- export/download surface

## 2. Product intent statement

### What the software solves
CarvAcoustic reduces the repetitive work involved in turning decorative panel ideas into fabrication-ready vector packages.

### What phase 1 is
A design-to-export system for:
- decorative wall art
- decorative cabinet/front panels
- decorative architectural face panels

### What phase 1 is not
- not a full CAD system
- not a full CAM system
- not a G-code generator
- not an acoustic-engineering product
- not a manufacturing/pack/ship system
- not a marketing platform

### What later phases can become
- acoustic wall-treatment modes
- acoustic ceiling cloud modes
- room/site intake workflows
- vendor-assisted intake
- future Windows-side Vectric companion

## 3. Scope boundaries for this report

### Included
- software product planning
- app + website planning
- phased workflow planning
- stage gates
- founder proof criteria
- AI coding-agent guidance
- acoustic roadmap framing
- acoustic intake planning at a high level

### Excluded
- detailed manufacturing operations
- packaging engineering
- shipping execution
- pricing/business model
- full go-to-market planning
- acoustic implementation details
- direct CAM replacement

## 4. Product phases and stage gates

### Phase 0 — Product definition and setup
Goals:
- freeze phase-1 scope
- define core modes
- define success criteria
- define repo and documentation structure
- define acceptance tests before coding

Gate 0 requires:
- approved product scope
- approved phase ordering
- explicit deferred list
- approved golden sample projects
- coding-agent guardrails

### Phase 1 — Decorative workflow proof
Goals:
- prove wall-art workflow
- prove cabinet/front-panel workflow
- prove app shell
- prove clean export + Vectric handoff
- prove save/load/versioning basics

Gate 1 requires:
- founder completes one valid wall-art project
- founder completes one valid cabinet/front project
- exports open cleanly in Vectric
- common geometry problems are caught before export
- nested layouts are usable
- projects can be reopened and re-exported

### Phase 2 — Decorative hardening and usability
Goals:
- improve reliability and speed
- improve onboarding
- improve presets
- harden validation/export behavior
- improve project organization and docs

Gate 2 requires:
- repeated founder test projects succeed
- export cleanup in Vectric is minimal and predictable
- decorative workflow is stable enough to expand

### Phase 3 — Acoustic intake and schema preparation
Goals:
- define acoustic mode families
- define future room/site intake requirements
- define future role changes
- reserve schema and UX space
- avoid major rework

Gate 3 requires:
- acoustic modes are separate product modes
- intake requirements are documented
- future schema fields are reserved
- website intake flow is planned
- no unsafe performance claims are implied

### Phase 4 — Acoustic feature implementation
Goals:
- implement acoustic wall-treatment modes
- implement acoustic cloud modes
- add measurement-driven configuration
- add suspension-point logic later
- generate conservative, non-certifying guidance

Gate 4 requires:
- one wall-treatment flow works end to end
- one cloud-treatment flow works end to end
- intake questions are understandable
- required measurements are realistically collectible
- outputs are actionable for founder/vendor review

## 5. Software workflow definition

### Phase-1 workflow
1. Create project
2. Choose mode
3. Set units and dimensions
4. Define boundary
5. Choose pattern family
6. Tune parameters
7. Generate preview
8. Run validation
9. Review warnings/errors
10. Generate or refine nesting
11. Export package
12. Save project/version
13. Open exports in Vectric
14. Create toolpaths and machine output in Vectric

### What stays manual in phase 1
- final toolpath strategy
- feeds/speeds
- hold-down strategy
- tabs where needed
- machine post-processor selection
- final simulation and machining

### What gets automated first
- boundary handling
- pattern generation
- manufacturability validation
- part labeling
- nesting prep
- export packaging
- project persistence

### Later acoustic workflow, high level
1. Create acoustic project
2. Choose acoustic mode
3. Enter room/site/use-case information
4. Complete self-service or vendor-assisted intake
5. Upload photos/sketches/measurement files
6. Generate treatment options
7. Validate installation constraints
8. Produce treatment package and review notes

## 6. Website scope and role

### Phase 1 website/app role
The website should serve as:
- landing surface
- authenticated app shell
- project dashboard
- help/docs surface
- export/download surface

### Phase 1 minimum scope
- home page
- sign-in/auth
- project list/dashboard
- create project flow
- design workspace
- validation/export screen
- docs/help section
- founder/admin preset settings

### Later expansion scope
Reserved for later:
- customer intake surface
- vendor/installer portal
- acoustic measurement guidance center
- uploads for room sketches and measurement files
- role-specific dashboards

## 7. User roles and workflow participants

### Founder / internal operator
Needs:
- speed
- repeatability
- useful exports
- strong control over dimensions and fabrication constraints

### Designer / fabricator
Needs:
- clean decorative outputs
- understandable presets
- predictable exports

### Future customer
Appears later.
Needs:
- guided intake
- preview/proposal visibility
- simple measurement guidance

### Future vendor / installer
Appears later.
Needs:
- validated site data
- install constraints
- room measurements
- later suspension/installation notes

## 8. Feature planning by phase

### Required now
- decorative wall art generation
- cabinet/front-panel generation
- architectural face-panel generation
- custom boundaries
- presets
- validation
- nesting
- export package
- project persistence
- authenticated dashboard
- basic docs/help

### Deferred to phase 2
- richer preset libraries
- improved onboarding
- better versioning UX
- stronger docs
- stronger export polish

### Reserved for future architecture
- acoustic intake
- acoustic guidance surfaces
- cloud suspension logic
- vendor-assisted intake
- customer self-service intake
- measurement uploads
- Windows-side Vectric companion

### Not needed now
- direct G-code generation
- full CAM replacement
- e-commerce checkout
- packaging/shipping operations
- marketing automation
- certified acoustic modeling

## 9. Project management and execution plan

### Workstreams
1. Product definition
2. App/platform
3. Geometry
4. Validation + export
5. Founder QA

### Milestone order
1. Planning docs approved
2. Schemas frozen
3. App shell working
4. Save/load working
5. Decorative generation working
6. Validation working
7. Nesting/export working
8. Founder sample tests
9. Decorative hardening
10. Acoustic prep only after Gate 2

### Founder review rhythm
- weekly review of working increments
- mandatory gate reviews
- explicit approved / revise / defer decision each review

## 10. Required documentation package for the AI coding agent

Required docs:
- master product brief
- PRD
- technical architecture spec
- geometry engine spec
- frontend UX spec
- data/schema spec
- API contract spec
- validation spec
- export/layer convention spec
- implementation roadmap
- coding-agent prompt pack
- founder acceptance checklist

## 11. Decorative workflow proof criteria

Gate 1 passes only if:
- founder can create a valid wall-art project
- founder can create a valid cabinet/front-panel project
- software catches common fabrication issues
- exports open cleanly in Vectric
- nested layouts are usable
- save/load works
- website/app flow is coherent

## 12. Acoustic expansion framing

Acoustic work should remain in separate later modes because it adds:
- room/site input requirements
- different validation logic
- installation constraints
- customer/vendor role changes
- greater risk of overclaiming performance

Likely later acoustic families:
- acoustic wall absorber
- acoustic ceiling cloud
- resonant / slotted / perforated panel
- diffuser mode only after the others are stable

## 13. Acoustic measurement and intake planning framework

### Simple self-service intake
Future customers may provide:
- room dimensions
- room use case
- basic surface materials
- treatment goals
- photos
- rough sketch
- optional simple sound-level or clap-test notes

### Advanced vendor-assisted intake
Future vendor/installer may provide:
- scaled room plan
- verified dimensions
- ceiling/plenum conditions
- MEP conflicts
- mounting constraints
- RT60 and other measurement data
- annotated install notes

### Future software intake requirements
Future forms should request:
- room use
- room dimensions
- finishes/materials
- target outcome
- uploads
- installation restrictions
- simple and advanced measurement sections
- confidence/assumption flags

## 14. AI coding-agent operating rules

1. Do not overbuild phase 1.
2. Do not mix acoustic logic into decorative v1.
3. Preserve modularity.
4. Document assumptions.
5. Respect stage gates.
6. Treat Vectric as downstream in phase 1.
7. Build save/load and export early enough to test real workflow.
8. Do not create direct G-code features in phase 1.
9. Use feature flags or reserved schemas for future acoustic work.
10. Write tests before calling a milestone complete.

## 15. Risks and mitigations

Major risks:
- scope drift
- architecture drift
- geometry complexity
- website bloat
- export incompatibility
- AI-agent overbuilding
- premature acoustic complexity
- unclear success gates

Mitigation pattern:
- phase labels on every feature
- explicit deferred lists
- gate reviews against real sample projects
- Vectric import checks before declaring success
- no acoustic implementation before Gate 2

## 16. Recommended implementation sequence

1. Approve Report 1
2. Approve Report 2
3. Freeze two golden sample projects
4. Freeze phase-1 feature list
5. Build schemas and app shell
6. Build boundary + pattern generation
7. Build validation
8. Build nesting
9. Build export package
10. Run founder Gate 1 tests in Vectric
11. Harden decorative workflow
12. Prepare later acoustic intake only after Gate 2
