# BSW dispatch handoff — hydration packet

Read in this order (files, not the transcript). All paths are repo-relative to `/Users/gilraitses/orcast`.

## 1. Method / canon (how O0 + dispatch works)
- `~/.cursor/skills/waveset-orchestration/SKILL.md` — the three roles (O0 / dispatched orchestrator /
  parallel subagents), dispatch mechanics, the escalation catch, file-ownership discipline.
- `~/.cursor/skills/orchestrator-rotation/SKILL.md` — why this handoff exists (read only if re-rotating).

## 2. This campaign — authority + plan
- `.cca/catalogue/O0/20260629_bsw-dispatch-handoff/HANDOFF_CHARTER.md` — THIS rotation's charter (§B locked, §E dispatch table, §F gate authority, §H ack).
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/PROGRAM.md` — BSW umbrella authority + locked decisions.
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/SIGN_OFF.md` — owner ratification (NC authorized; honest acoustic scope).
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/dispatch/SEQUENCING.md` — dependency DAG + the single-editor convergence queues.

## 3. The six lane packets (each = the dispatch prompt + the roster)
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/dispatch/SLICE-INTEGRATE/{ORCHESTRATOR_DISPATCH_PROMPT.md,wave_shape.yml}`
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/dispatch/BST/{ORCHESTRATOR_DISPATCH_PROMPT.md,wave_shape.yml}`
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/dispatch/BAM/{ORCHESTRATOR_DISPATCH_PROMPT.md,wave_shape.yml}`
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/dispatch/BSH/{ORCHESTRATOR_DISPATCH_PROMPT.md,wave_shape.yml}`
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/dispatch/BRE/{ORCHESTRATOR_DISPATCH_PROMPT.md,wave_shape.yml}`
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/dispatch/BSS/{ORCHESTRATOR_DISPATCH_PROMPT.md,wave_shape.yml}`

## 4. Per-lane charters (intent / grounding / acceptance)
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/BSW-STATION_CHARTER.md` (BST)
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/BSW-ACOUSTIC-ML_CHARTER.md` (BAM)
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/BSW-SPECTRO-HUD_CHARTER.md` (BSH)
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/BSW-REENACTMENT_CHARTER.md` (BRE)
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/BSW-STUDIO-SKILLS_CHARTER.md` (BSS)

## 5. Evidence the slice is real (what breadth extends)
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/research/SYNTHESIS_bside.md` — ranked build plan + the slice spec.
- `infra/acoustic/eval_report.json` + `infra/acoustic/PROVENANCE.md` — the slice's real BAM model + its confounds + the `to_strengthen` follow-on BAM breadth runs.
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/gate_screenshots/` + `demo/` — the accepted slice frames + B-side beats.

## 6. Code seams (the slice modules + convergence files)
- Slice route: `web/app/workbench/{page,WorkbenchHost,WorkbenchScene}.tsx`.
- Lane modules: `web/lib/scene/hydrophone/`, `web/lib/scene/hud/spectro/`, `web/lib/scene/ocean/`, `web/lib/scene/reenactment/`, `web/lib/scene/orca/motion/clips/` (+ each `WIRING.md`); `modeling/acoustic/`, `infra/acoustic/`.
- Convergence (single-editor only): `web/app/components/scene/SalishScene.tsx`, `web/app/globals.css`, `web/app/components/AdaptiveExplore.tsx`, `web/app/components/ActiveSurfaceHost.tsx`, `web/lib/uiIntent.ts`.
- Public artifacts: `web/public/hydrophone/slice/classification.json`, `web/public/orca/motion/clips/manifest.json`.

## 7. Real external data (not in checkout)
- DTAG/h5: `/Users/gilraitses/whale-behavior-analysis/dive_analysis_schema_flat.json`, `behavior_mapping.json`, `Visualization_Poster_Appendix/{data/dive_analysis.h5,scripts/}`.
- Orcasound audio: `s3://audio-orcasound-net/rpi_orcasound_lab/...` (public, `--no-sign-request`); catalog `src/integrations/live_orcasound_feeds.json`.

## 8. Verification + registry
- GPU host: `infra/render_host/render.sh` + `RUNBOOK.md` (aimez-gpu-capture Tesla T4).
- Registry: `docs/devpost/waves.registry.yaml` (BSW entries carry `dispatch:` pointers).

## Repo / environment
- Repo `/Users/gilraitses/orcast`, branch `main`, last commit `1b9772e`, pushed to `origin/main`.
- Web app under `web/` (Next.js, three/react-three-fiber). Validate with `cd web && npx tsc --noEmit`.
