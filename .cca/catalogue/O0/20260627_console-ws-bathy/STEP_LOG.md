# WS-BATHY step log

Home: `.cca/catalogue/O0/20260627_console-ws-bathy/`
Suborchestrator task scope, run the Research wave then the Discovery wave only, read-only on code, Markdown docs only, end with a proposed implementation dispatch. No commit, no deploy, no dev server, no subagents.

## S01, 2026-06-27, intake

Read `PROGRAM_WAVESETS_CHARTER.md` and `VISUAL_DEFICIENCY_REGISTER.md`. Confirmed WS-BATHY scope, the four special teams, the locked constraints B.1, B.6, B.8, B.10, and the convergence calendar order INTENT then SCENIC then BATHY on `SalishScene.tsx`.

## S02, 2026-06-27, live underwater stack read

Read `web/lib/scene/water2/index.ts` and `depthWater.ts`, `web/lib/scene/substrate/` (`types.ts`, `loadSubstrate.ts`, `sampleSubstrate.ts`, `buildSubstrateOverlay.ts`, `index.ts`, `WIRING-substrate.md`), and `web/app/components/scene/SalishScene.tsx`. Confirmed the depth pre-pass, the Beer-Lambert column-to-alpha-and-color map, the `uDebug` thickness instrument, the substrate public surface, and that the pick `depth_m` is modeled CUDEM via `sampleSubstrate`. Confirmed `buildSubstrateOverlay` is built but not mounted.

## S03, 2026-06-27, provenance ground truth

Read `infra/3dtwin/host/WIRING-host.md`, `infra/3dtwin/science/SCIENCE-SPIKE.md`, `infra/3dtwin/science/WIRING-science.md`, `src/aws_backend/sources/bathymetry.py`, and the substrate JSON header. Resolved the key fact, the served tileset is CUDEM topobathy, elevation range -376.431 to +733.885 m NAVD88, the seafloor is baked into the render geometry. The substrate field and the render tiles share one CUDEM geometry and the NAVD88 datum.

## S04, 2026-06-27, research wave, web search

Searched and cited NOAA NCEI CUDEM 1/9 arc-second topobathy (public domain, only 1/9 integrates bathy and topo, built from measured sources), NOAA BlueTopo (per-pixel `bathy_coverage` measured flag, NAVD88, public domain), CHS NONNA-10 and NONNA-100 (measured, Open Government Licence Canada, chart datum), GEBCO_2024 (15 arc-second, context only), and depth-rendering technique sources (Beer-Lambert depth-driven water, cmocean perceptually uniform `deep` ramp, Patterson seafloor relief, the foam `dh` shoreline term).

## S05, 2026-06-27, RESEARCH_SYNTHESIS.md written

Wrote the synthesis. Research gate PASSED, concrete cited techniques and sources, key fact resolved.

## S06, 2026-06-27, DISCOVERY_MAP.md written

Mapped the reusable public surfaces, the new `web/lib/scene/bathy/` module family slots, the phase-B scene-mount seam, the one-file-one-owner table, and the honesty ledger. Discovery gate PASSED, the only convergence-file edit is `SalishScene.tsx` in phase B serialized after SCENIC, water2 and substrate internals are request-only.

## S07, 2026-06-27, IMPLEMENTATION_DISPATCH.md written, PROPOSED

Wrote the four phase-A producer prompts plus the phase-B mount step, each with task, deliverables, validation including the real depth-read visual check, and collision avoidance. Marked PROPOSED, held for the program orchestrator gate. Listed the open operator decisions.

## S08, 2026-06-27, task close

Created the waveset home with README, RESEARCH_SYNTHESIS, DISCOVERY_MAP, IMPLEMENTATION_DISPATCH, and this STEP_LOG. Returned the summary to the program orchestrator. No code, config, commit, deploy, dev server, or subagent. Implementation held for the gate.
