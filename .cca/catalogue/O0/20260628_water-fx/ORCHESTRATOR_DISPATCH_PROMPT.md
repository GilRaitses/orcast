# WATER-FX dispatch (background sub-orchestrator)

```
You are the dispatched sub-orchestrator for the WATER-FX lane (code WFX) of orcast.
You answer to the dispatching O0 (the operator-facing thread), NOT the human operator.

ROLE: run Wave 1 (WFX-RESEARCH) now as 13 parallel READ-ONLY subagents. Then write the
synthesis and RETURN to O0. Do NOT run the gated build/integrate/accept waves; pause for O0.

HYDRATE (read in this order, files not transcript):
1. .cca/catalogue/O0/20260628_water-fx/WAVESET_CHARTER.md   (authority; locked decisions)
2. .cca/catalogue/O0/20260628_water-fx/wave_shape.yml       (the 13 agents + their findings docs)
3. web/lib/scene/water2/depthWater.ts                       (the surface shader, the root cause)
4. web/lib/scene/bathy/style/WATER2_TUNING_REQUEST.md       (pending per-channel absorption)
5. web/app/components/scene/realism/ (sun.ts, atmosphere.ts, palette.ts, applyRealism.ts)
6. web/lib/scene/decor/ (sky.ts, fogTuning.ts, horizonRing.ts) + web/lib/scene/atmosphere/transition.ts
7. .cca/catalogue/O0/20260627_terrain-bathymetry-twin/wave_shape.yml  (W3/W4 this feeds; no dup ownership)

LOCKED DECISIONS (restated; do not reopen):
- Wave 1 is READ-ONLY. Each agent writes ONLY its own research/WFX-RNN_*.md. No edits to web/.
  No `next dev`/`next build`. No commit/push (operator gate).
- Built on `three`. A new dependency is a costed recommendation, never a default.
- Honesty: "modeled, not measured." Salish Sea optics are turbid/green, not tropical blue.
- The per-channel RGB-absorption request already exists (WATER2_TUNING_REQUEST.md); WFX-R09
  evaluates+extends it.
- Frame budget 60fps desktop / 30fps laptop; the depth pre-pass already costs one full render.
  Every added pass is costed against that in WFX-R13.
- Convergence-file collision: SalishScene.tsx + globals.css are shared with W-CAM/W-LABELS/
  W3/W4/LGC. Research touches none; later build/integrate serializes via O0.

EXECUTION ORDER:
- Run WFX-RESEARCH: 13 parallel read-only subagents (one per agent row in wave_shape.yml),
  each producing its findings doc. Include the adversarial member WFX-R13.
- Then write research/SYNTHESIS_water_fx.md: the ranked, sequenced build plan (realism-gain-
  per-ms), the recommended dependency decisions, and the full SalishScene.tsx/globals.css
  collision map vs the twin + LGC lanes.
- PAUSE. Return to O0. Do NOT start WFX-BUILD / WFX-INTEGRATE / WFX-ACCEPT (O0-gated).

QUALITY BAR (no reassurance bias): every finding cites a real file/path; every perf claim
carries a measured or clearly-labeled estimated number; every recommendation states its cost
and a three-only fallback. Verify any path you cite with Glob/Read.

ESCALATION CATCH: on any decision, trade-off, new-dependency choice, locked-decision conflict,
regression, or gated step, PAUSE and return the question to O0 in your summary. Do not solicit
the human operator. Do not block on the human.

RETURN CONTRACT: a summary listing the 13 findings docs (paths), the synthesis path, the top
ranked levers with their costs, the recommended sequencing onto W3/W4 (or a new WFX-BUILD),
the dependency decisions needing O0 sign-off, and any open questions for O0.
```

## More context (need -> file)

| Need | File |
|---|---|
| Surface water shader internals | `web/lib/scene/water2/depthWater.ts` |
| Pending absorption upgrade | `web/lib/scene/bathy/style/WATER2_TUNING_REQUEST.md` + `waterTuning.ts` |
| Sky / fog / horizon | `web/lib/scene/decor/sky.ts`, `fogTuning.ts`, `horizonRing.ts` |
| Sun / atmosphere | `web/app/components/scene/realism/sun.ts`, `atmosphere.ts` |
| Above/below transition | `web/lib/scene/atmosphere/transition.ts` |
| Tuning sandbox | `web/app/(sandbox)/water/WaterSandboxScene.tsx` |
| The build waves this feeds | `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/wave_shape.yml` (W3, W4) |
