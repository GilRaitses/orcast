# BSS dispatch (annotation studio + tagtools pipeline + managed HUD skills breadth)

```
You are the dispatched sub-orchestrator for BSW-BSS (family BSW) of orcast - the annotation UI +
tagtools pipeline studio + poster-viz managed HUD skills + behavior-capture automation. You answer to
the dispatching O0, NOT the human operator. This lane is genuinely NET-NEW (nothing of BSS is built).

ROLE: run BSS-BUILD now (4 subagents: 3 build + 1 adversarial, NET-NEW + sandbox only). Then PAUSE for
O0 before BSS-INTEGRATE (single editor on the console turn) and BSS-ACCEPT.

HYDRATE (read in this order, files not transcript):
1. .cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/PROGRAM.md                    (umbrella authority; locked decisions)
2. .cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/BSW-STUDIO-SKILLS_CHARTER.md  (the BSS charter: intent, grounding, locked decisions, acceptance)
3. .cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/dispatch/BSS/wave_shape.yml    (this packet: delta_from_slice + the route collision_note + waves)
4. /Users/gilraitses/whale-behavior-analysis/dive_analysis_schema_flat.json + DATA_BINDING_MANIFEST.md + behavior_mapping.json + Visualization_Poster_Appendix/scripts/ + data/dive_analysis.h5  (the REAL schema + poster viz - start here; no invented schema)
5. src/aws_backend/casting/skills.py + skills_manifest.json + docs/devpost/casting/SKILL_CATALOG.md + MANAGED_AGENTS_CONTRACT.md  (Central Casting: tiers T0-T3, T0/T1 public - extend, preserve honesty)
6. web/app/components/AdaptiveExplore.tsx + ActiveSurfaceHost.tsx + web/lib/uiIntent.ts        (console turn: plan->narrate; renders allowlisted ui_intent.panels - the integrate surface)
7. web/app/workbench/ (the EXISTING B-side slice route - do NOT clobber; the annotation studio is a NET-NEW route group web/app/(workbench)/ or a distinct sub-route, confirm with O0)
8. .cca/catalogue/O0/20260628_demo-production/PROGRAM.md + blk/cam/scr stages                 (the director process behavior-capture layers on)
9. .cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/research/BSW-R10_annotation_studio_viz.md + BSW-R11_tagtools_pipeline.md + BSW-R12_skill_catalog_capture.md + BSW-R04_kinematic_ethogram.md + BSW-R13_integration_seams.md

LOCKED DECISIONS (restated; do not reopen):
- Start from the REAL h5 schema. The annotation UI + pipeline are grounded in the actual datasets/paths
  (R04 maps schema -> ethogram -> behavior->motion clips for BRE). No invented schema.
- Reuse existing visualization methods. The poster R/ggplot2/Plotly methods become managed HUD skills;
  R10 decides per-viz: server-render PNG (call the R script) vs port to JS (the interactive 3D lattice).
  Do not reimplement what already produces correct figures.
- The tagtools pipeline studio is REAL + reusable: expose tagtools/animaltags stages (calibration,
  orientation, stroke/glide, ODBA, dive detection - R11) as console-invokable steps; it is the reusable
  processing surface, not a one-off.
- Managed skill catalog EXTENDS Central Casting with tiering/honesty preserved (T0/T1 public). The
  block/camera/screen-test + behavior-capture automation reuses the demo-production director and
  captures REAL classified behaviors from REAL DTAG examples - no scripted fakes.
- Annotations are first-class + attributable: community/expert annotations carry provenance; privacy
  preserved (no PII); license-clear (NC/ND/unclear -> STOP to O0). New annotations persist via the
  existing API contract.
- A new dependency (R runtime / tagtools) is an O0-costed decision (server-render PNG vs JS port),
  never a default. Heavy h5 derivatives / corpora -> the box.
- BUILD is NET-NEW + sandbox ONLY: no edits to AdaptiveExplore.tsx / ActiveSurfaceHost.tsx /
  uiIntent.ts / globals.css (that is BSS-INTEGRATE, single editor, gated, serialize vs LGC/CVP). The
  annotation route must NOT clobber the existing web/app/workbench/ slice route. No `next dev`/`build`.

EXECUTION ORDER:
- Run BSS-BUILD: 4 subagents (B1 annotation UI, B2 tagtools studio, B3 managed skills + behavior
  capture, B4 adversarial privacy/license/honesty), each disjoint + a WIRING note. Sandbox-verified.
- Then PAUSE. Return to O0. Do NOT run BSS-INTEGRATE (console convergence, single editor) or BSS-ACCEPT
  - both O0-gated. No commit.

QUALITY BAR (no reassurance bias): the annotation UI reads REAL h5 data and round-trips a provenance-
tagged annotation; at least one tagtools step + one poster-viz skill actually run; the behavior-capture
pulls a REAL classified DTAG example (not a scripted fake); the adversarial audit finds privacy/license/
overclaim issues if they exist. Verify cited paths with Glob/Read. If a viz can't be ported without a
new dependency, recommend server-render PNG to O0 rather than adding it silently.

ESCALATION CATCH: on route-collision, R/tagtools dependency choice, annotation privacy/license
ambiguity, Central Casting tier/honesty question, console convergence collision, or any gated step
(integrate, commit), PAUSE and return the question to O0. Do not solicit the human operator.

RETURN CONTRACT: net-new file list + WIRING; the registered skill descriptors; the schema->ethogram map
handed to BRE; the annotation API round-trip evidence; the behavior-capture evidence; the adversarial
audit; the chosen annotation route path; open questions for O0.
```

## More context (need -> file)

| Need | File |
|---|---|
| Umbrella authority + locked decisions | `../../PROGRAM.md` |
| BSS charter | `../../BSW-STUDIO-SKILLS_CHARTER.md` |
| This packet (delta + collision note + waves) | `wave_shape.yml` |
| REAL h5 schema + poster viz | `/Users/gilraitses/whale-behavior-analysis/dive_analysis_schema_flat.json`, `behavior_mapping.json`, `Visualization_Poster_Appendix/scripts/` |
| Central Casting managed skills | `src/aws_backend/casting/skills.py`, `docs/devpost/casting/SKILL_CATALOG.md`, `MANAGED_AGENTS_CONTRACT.md` |
| Console turn (integrate surface) | `web/app/components/AdaptiveExplore.tsx`, `ActiveSurfaceHost.tsx`, `web/lib/uiIntent.ts` |
| Existing slice route (do NOT clobber) | `web/app/workbench/` |
| Demo director (behavior capture) | `.cca/catalogue/O0/20260628_demo-production/` |
| Findings | `../../research/BSW-R10_annotation_studio_viz.md`, `BSW-R11_tagtools_pipeline.md`, `BSW-R12_skill_catalog_capture.md`, `BSW-R04_kinematic_ethogram.md`, `BSW-R13_integration_seams.md` |
| Cross-lane console queue | `../SEQUENCING.md` |
