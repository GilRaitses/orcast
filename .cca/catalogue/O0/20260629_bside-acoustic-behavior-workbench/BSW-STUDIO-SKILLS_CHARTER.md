# BSW-STUDIO-SKILLS charter (annotation UI + tagtools pipeline studio + managed HUD skills)

- Lane code: **BSS** (under family BSW)
- Owner: O0 dispatches; a background sub-orchestrator runs the gated build waves.
- Type: research-first (grounded by BSW-RESEARCH R04/R10/R11/R12/R13); build/integrate/accept gated.
- `repo_state_verified_against`: origin/main `240570e961913fb610c2765a4ef77cace3f216f1`.
- Charter method: `~/.cursor/skills/waveset-orchestration/SKILL.md`. Umbrella: `PROGRAM.md`.

## Intent (operator)
An annotation UI: start from the analysis .h5, mine the schema for the MLops, a managed agent skill
catalog that can block / camera-test / screen-test and capture orca behaviors in the 3D models from
classified DTAG examples. An annotation framework that includes the poster-folder visualization
methods as managed skills for invoking HUDs, and tagtools UIs in a reusable processing-pipeline
studio the orchestrated console can invoke.

## Grounding (verified seams)
- Real analysis h5:
  `/Users/gilraitses/whale-behavior-analysis/Visualization_Poster_Appendix/data/dive_analysis.h5`
  (99,925 @ 5 Hz). Schema: `dive_analysis_schema_flat.json` (121 datasets),
  `DATA_BINDING_MANIFEST.md`. REAL derived products: 128 dives + descent/bottom/ascent phases, 51
  manual annotations (`log_mn09_203a.csv`), 9-class taxonomy (`behavior_mapping.json`), tagtools
  stroke/glide + ODBA/VDBA/jerk, validation behavior masks. **No automated classifier shipped.**
- Poster viz (candidate managed HUD skills),
  `/Users/gilraitses/whale-behavior-analysis/Visualization_Poster_Appendix/scripts/`: R+ggplot2
  composite dashboard / dive overview / per-dive frames / energetics scatter (static PNG) + one
  interactive Plotly 3D dive lattice (`06_hierarchical_visualization.R` -> HTML). tagtools outputs
  are consumed from h5; tagtools/animaltags is NOT directly invoked in that repo.
- Managed skills = backend Central Casting: `docs/devpost/casting/SKILL_CATALOG.md`,
  `src/aws_backend/casting/skills.py` + `skills_manifest.json`,
  `docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md`. Tiers T0-T3; T0/T1 public.
- Console invocation: `web/app/components/AdaptiveExplore.tsx` (plan->narrate) ->
  `web/app/components/ActiveSurfaceHost.tsx` renders allowlisted `ui_intent.panels`;
  `web/lib/uiIntent.ts` types. Demo director process to reuse:
  `.cca/catalogue/O0/20260628_demo-production/` (blk/cam/scr stages).

## Locked decisions (do NOT reopen)
- **Start from the real h5 schema.** The annotation UI + pipeline are grounded in the actual
  datasets/paths (R04 maps schema -> ethogram -> behavior->motion clips for BRE). No invented schema.
- **Reuse existing visualization methods.** The poster R/ggplot2/Plotly methods are registered as
  managed HUD skills; R10 decides per-viz whether to server-render PNG (call the R script) or port
  to JS (the interactive 3D lattice). Do not reimplement what already produces correct figures.
- **tagtools pipeline studio is real + reusable.** Expose the tagtools/animaltags stages
  (calibration, orientation, stroke/glide, ODBA, dive detection - R11) as console-invokable steps;
  the studio is the reusable processing surface, not a one-off.
- **Managed skill catalog extends Central Casting,** with tiering/honesty preserved (public T0/T1).
  The block/camera/screen-test + behavior-capture automation reuses the demo-production director
  process; it captures REAL classified behaviors pulled from real DTAG examples - no scripted fakes.
- **Annotations are first-class + attributable.** Community/expert annotations carry provenance;
  privacy preserved; license-clear. New annotations persist via the existing API contract.
- **Net-new + gated:** `tsc`/lint clean, no `next dev/build` in parallel waves, commit is an
  operator gate; heavy artifacts to the box.

## Wave structure
- **BSS-BUILD** (gated, net-new): `web/app/(workbench)/` (annotation UI for audio + kinematics),
  `infra/tagtools/` (pipeline studio steps + skill descriptors), `src/aws_backend/casting/`
  additions (register poster viz + pipeline as managed skills), + the behavior-capture automation
  layered on the demo-production director. Sandbox-verified.
- **BSS-INTEGRATE** (gated, single editor): wire the studio + skills into the console
  (`AdaptiveExplore`/`ActiveSurfaceHost`/`uiIntent`); serialize vs LGC/CVP.
- **BSS-ACCEPT** (gated): Read-examined - the console invokes a poster-viz HUD skill and a tagtools
  pipeline step; an annotation round-trips; a behavior-capture run pulls a real DTAG example into a
  3D capture.

## Acceptance criteria (hard, checkable)
- The console can invoke at least one poster-viz HUD skill and one tagtools pipeline step.
- The annotation UI reads the real h5-derived data and round-trips a new annotation with provenance.
- A managed behavior-capture run captures a real classified behavior from a real DTAG example.

## Escalation
Answers to O0. R-vs-JS viz port decision, new dependency (R runtime / tagtools), Central Casting
tier/honesty questions, privacy/license, convergence collisions, or any gated step: pause to O0.

## Return contract
Net-new file list + WIRING; the registered skill descriptors; the schema->ethogram map handed to
BRE; GPU-host / capture evidence; open questions for O0.
