# HUNT — movement-scale fork under the real bathymetry tileset

- **Date:** 2026-07-10
- **Lane:** wavves/lanes/20260709_orca-boat-hunt
- **Routed from:** wavves/lanes/20260709_orca-boat-hunt-check/findings/HCHK-verdict.md, Blocker 1 (adversarial check, `HCHK-adversarial.md` F1)
- **repo_state_verified_against:** cbe6483fb2157edcdca27e7b21dfffa7b961a7b5 (main, unchanged since HUNT/HCHK were chartered)
- **Question:** Under the real "full" bathymetry tileset that `HUNT-BATHY` GO'd, the fitted `worldUnitsPerMeter` is ~0.00216 scene units/metre. The pilot's dead-reckoning integrator (`deadReckoning.ts:157-161`) scales real swim speed (2.2-5.5 m/s) by this factor, giving ~0.005-0.012 scene units/second. Boats spawn 14-54 scene units out (`spawnBoats.ts:15-18`, sized for the flat-plane `wupm=1` convention `OrcaSandboxScene.tsx:124` uses). At that scale the nearest boat is ~20 minutes away at boost speed: acceptance criterion 4 (a boat sinks from ramming) is unreachable by swimming, and criterion 3 (visible movement) is technically true but imperceptible on screen. Which of the two legitimate product outcomes does `HUNT-INT` implement?
- **Options considered:**
  - A: Pass `worldUnitsPerMeter: 1` to the pilot regardless of the tileset's actual fitted scale, decoupling arcade movement speed from geographic scale entirely. The orca swims at a fun, fixed arcade pace over real-looking bathymetry, but is not moving at "real" metres/second relative to the terrain underneath it.
  - B: Scale boat spawn radii and collision radius down by the fitted `worldUnitsPerMeter`, keeping the pilot's real-metre speed meaningful relative to the real-scale terrain, but shrinking the whole reachable play area to a tiny patch of scene units.
- **Pick:** A (`arcade_fixed_scale`).
- **Rationale:** Operator call. Preserves the acceptance-critical gameplay loop (swim, see boats, ram, sink) at a speed a player can actually perceive and reach within a demo's attention span, which is the entire point of the hackathon build. The real bathymetry tileset still renders underneath (visual fidelity is unaffected by this pick — only the pilot's own X/Z integration speed changes), so the "swim over real-looking terrain" value proposition from `HUNT-bathy-fidelity.md` is preserved. Trades away literal metres/second realism, which nothing in the acceptance criteria or the pitch actually requires.
- **Implications for HUNT-INT:**
  - Whatever constructs the `PilotTrack`/dead-reckoning integrator for the `/orca-strike` route (or its Bash.tv-prompt equivalent) must pass a fixed `worldUnitsPerMeter: 1` constant, NOT the tileset's fitted scale value returned by `useTilesLayer`. This is a one-line call-site change at integration time, not a change to `deadReckoning.ts`'s own math (it already takes `worldUnitsPerMeter` as a parameter, per `deadReckoning.ts:157-161`).
  - `spawnBoats.ts`'s existing 14-54 scene-unit spawn radii (already tuned for `wupm=1`) remain correct as-is; no boat-spawn-radius change is needed under this pick.
  - This does NOT change how the bathymetry tileset itself is fitted/scaled for rendering (`useTilesLayer`'s own `worldUnitsPerMeter` output keeps driving the visual terrain fit); it only decouples the PILOT'S movement integrator from that value. Two different scale factors now coexist in the same scene (terrain-fit scale vs. pilot-movement scale) — `HUNT-INT` should name this explicitly in code (a comment at the pilot's construction call site) so a future maintainer doesn't "fix" it by unifying them.
  - Combined with `HUNT-bathy-fidelity.md`'s fixed 0-25m depth-clamp pick, the orca's depth behavior is already decoupled from strict real-world fidelity for this build; this decision extends the same "arcade over real-looking terrain" posture to horizontal movement, for consistency.

## Correction (2026-07-10, post-build, found by direct visual verification)

The Rationale line above states "visual fidelity is unaffected by this pick." That
was wrong. `HUNT-INT` initially mounted the tileset with Journey/Water/Salish's own
`fitScaleToWidth: SCENE_WIDTH` (120), which compresses the ~50km-diameter dataset
to ~0.00216 world units/metre. The orca mesh (~7-8m long, built at 1 unit = 1m to
match the pilot/boats/camera, per this decision) was never rescaled to match that
compression, so it rendered ~460x too large relative to the terrain: "the orca is
the size of some islands" (operator report, live build). The same effective
mismatch also made ordinary fluke/spine motion sweep through a disproportionate
share of the frame, presenting as "flailing."

Fix shipped directly (not re-litigated as a new fork, given hackathon timing):
`OrcaStrikeScene.tsx` now fits the tileset to its own real metric diameter
(`fitScaleToWidth: 2 * geoRadiusMeters(TILESET_BOUNDS)`, ~49,628 units) instead of
`SCENE_WIDTH`, which drives the terrain's own fit scale to ~1 unit/metre. That
makes it equal to `PILOT_WORLD_UNITS_PER_METER`, so the "two different scale
factors coexist" caveat above no longer applies: there is one scale, 1 world unit
= 1 metre, across terrain, pilot movement, boats, and camera. The Pick (A,
arcade_fixed_scale) is unchanged; only the terrain's own fit call is corrected so
the stated Rationale is actually true. Tradeoff made explicit: only a local patch
of the ~50km dataset is reachable in a play session (the rest renders at true
distance, mostly off-screen) — correct for a first-person swim, and a smaller
regression than the visual bug it replaces.
