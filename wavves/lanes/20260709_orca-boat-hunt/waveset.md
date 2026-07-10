# HUNT waveset: orca-boat-hunt

Lane code: HUNT
Owner: O0 (operator-facing thread, this session)
Type: execution (net-new game feature on a real codebase)
repo_state_verified_against: cbe6483fb2157edcdca27e7b21dfffa7b961a7b5 (main, before this lane)

Working-tree note: at charter time the repo has a large set of pre-existing
uncommitted changes from unrelated concurrent work (demo-production recut,
whitepaper edits, `WorkbenchScene.tsx`, `stationCamera.ts`, `doubleDiffusion.ts`,
`web/.env.example`, etc, per `git status`). HUNT must not touch, depend on, or
commit any of those paths. HUNT's own file set is disjoint from all of them.

## Intent

Operator's framing, verbatim: "a way to swim around the bathymetry map as an
orca and sink boats." Clarified in-thread: build it for real in this orcast
repo (reusing the existing orca/bathymetry/camera stack), simple arcade
boat-sinking as the baseline mechanic, plus a sonar radar that shows boat
locations and a Floo-network-style instant teleport to a pinged target. This
charter is also asked to produce a portable build-prompt deliverable for the
Bash Hackathon platform (Bash.tv, July 10), with agent-model recommendations
written for credit discipline, and to preflight/dispatch the actual build so
waves execute and land a working feature, not just a spec.

## Grounding

Real files read and cited (all verified to exist at the hash above):

- `web/lib/scene/orca/OrcaController.ts` - assembles mesh + rig + material +
  eyes + mouth + biologging-driven motion + bounded secondary physics into one
  `update(dt, elapsed, cameraWorldPos)` call. `createOrcaController(opts)`
  hardcodes `loadBiologging(motionUrl)`, an async `fetch` of a JSON manifest +
  sibling `.bin` track. There is no way to hand it a live, non-file pose
  source without a signature change.
- `web/lib/scene/orca/motion/biologging.ts` - `BiologgingTrack.sample(t)`
  returns `{yaw,pitch,roll,depthM,flukePhase,flukeAmp}`; `driveOrca(rig, pose,
  worldUnitsPerMeter)` calls `rig.setOrientation` + `rig.setDepthPose` +
  `rig.setFluke`. **It never sets rig.root position X/Z.** Horizontal
  position is not owned by the orca stack at all today.
- `web/lib/scene/orca/rig/OrcaRig.ts` - `OrcaRig` exposes `setOrientation`,
  `setDepthPose` (Y only, `-depthM * worldUnitsPerMeter`), `setFluke`,
  `setJaw`, `setHeadOffset`, `setPectoral`, `setSecondaryFlex`,
  `setCaudalFollow`. No `setPosition`/XZ mover exists.
- `web/app/(sandbox)/orca/OrcaSandboxScene.tsx` + `page.tsx` - the closest
  existing template: Canvas + `createOrcaController` + an orbiting chase
  camera that tracks `c.root.getWorldPosition`. No bathymetry tiles here, flat
  water plane only, biologging playback, not player input.
- `web/lib/scene/camera/director.ts` + `types.ts` - cinematic eased
  `flyTo`/`descendTo`/`followPath`/`orbit` driven by lat/lng via
  `projectToScene`/`unprojectFromScene`. Built for scripted camera beats, not
  a per-frame player chase cam; reusable for the Floo teleport's short
  fly-in/settle beat and for `getSurfaceY`/no-dunk-clamp conventions, not for
  the moment-to-moment gameplay camera.
- `web/lib/geo/gazetteer.ts` - ~40 curated real Salish Sea places
  (`GAZETTEER: Place[]`), each with `{id, name, lat, lng, bounds, kind}`.
  Exactly the shape needed for Floo-teleport destinations and offline, no
  network required (`resolvePlace` is synchronous).
- `web/lib/journey/controller.ts` - shows the `flyTo`/`descendTo`/
  `followPath`/`orbit` beat-composition pattern and altitude-band constants;
  a reference for the teleport beat, not reused directly.
- `web/lib/scene/markers/buoyMarker.tsx` - pure r3f marker component pattern
  (no scene/camera reference, caller owns placement): the template for a new
  `BoatMarker`.
- `web/lib/scene/picking/worldPointToLatLng.ts` - inverts a raycast hit back
  to lat/lng via the same `unprojectFromScene`/`SCENE_WIDTH` frame the rest of
  the scene uses. Reusable for converting boat/orca world positions to
  lat/lng for the sonar radar and for teleport math.
- `web/lib/scene/tiles/useTilesLayer.ts` - the bathymetry/terrain tiles hook:
  `TilesRenderer` lifecycle, `fitScaleToWidth` to scale a real-metres tileset
  into the synthetic `SCENE_WIDTH=120` frame, `onFit(sphere)` callback for
  camera framing, `groupRotationX` for z-up -> y-up.
- `web/lib/sceneIntent.ts` - `SCENE_WIDTH=120`, `sceneDepth(bounds)`,
  `projectToScene`/`unprojectFromScene`, `HeightmapBounds`. The one frame
  every geo<->world mapping in the scene goes through.
- `web/app/workbench/WorkbenchScene.tsx` - the fullest existing integration
  example (Canvas + camera director handle + ocean layer + orca pool + sun/sky
  + honesty legend). Confirms the Canvas/tone-mapping/env conventions to copy,
  and confirms this repo is otherwise honesty-gated for scientific claims
  (measured vs modeled labeling, `ocean/interpretiveOceanLayer.ts`'s
  `FORBIDDEN_OCEAN_CLAIMS` guard). HUNT is an arcade feature and makes no
  scientific claims, but must not present fictional boats as real
  vessel-traffic data (no AIS/vessel data exists anywhere in this repo,
  verified by grep).
- `web/package.json` - Next.js 14 App Router, `@react-three/fiber` 8.18,
  `@react-three/drei` 9.122, `three` 0.169, `3d-tiles-renderer` 0.4.28.
  `npm run typecheck` (`tsc --noEmit`) and `npm run lint` (`next lint`) are the
  local validation commands, run from `web/`.
- Verified absent by search: no `AIS`/vessel/ferry/shipping-lane data source,
  no boat/vessel asset, no keyboard/pointer-lock input controller anywhere in
  `web/`. All of it is net-new.

Root constraint this charter is actually solving: the orca stack has a rich,
locked-composition-order rig and a real biologging-driven demo, but zero
horizontal-position ownership and zero live/input pose source, so "swim
around" cannot be built by wiring existing pieces alone. It needs exactly one
small additive seam in `OrcaController.ts` plus a new input-driven pose
source and a new dead-reckoning position integrator.

## Locked decisions (do NOT reopen)

1. **Boat-sinking mechanic is the simple arcade version** (operator-selected):
   spawn floating boat props on the water surface, orca rams/collides with a
   boat, it plays a sink animation with a small splash/particle burst. No AIS
   or real vessel-traffic data exists in this repo and none is fetched; boats
   are explicitly stylized arcade props, never presented as real vessel data.
2. **Add sonar + Floo teleport on top of the baseline** (operator addendum):
   a sonar-ping action reveals a radar-style readout of nearby targets
   (boats, plus a handful of curated `gazetteer.ts` places) with bearing and
   range from the orca; selecting a pinged target instantly teleports
   (snaps position, plays a short warp/flash beat) the orca there. This is
   the ONLY fast-travel mechanic; there is no continuous "swim to" auto-pilot
   requirement.
3. **The orca visual/rig stack is reused, not rebuilt.** `loadOrcaMesh`,
   `buildOrcaRig`, `makeOrcaMaterial`, `makeOrcaEyes`, `makeOrcaMouth`,
   `makeSecondaryDynamics`, and `OrcaController`'s per-frame composition order
   (OG -> OPHYS -> OMOU -> OEYE) are never modified in their internals.
4. **The one permitted existing-file edit**: add an optional `track?:
   BiologgingTrack`-shaped param to `OrcaControllerOptions` in
   `OrcaController.ts`. When present, `createOrcaController` skips
   `loadBiologging(motionUrl)` and uses the supplied track directly. This is
   additive and backward compatible (every existing caller omits it and is
   unaffected). This is the ONLY change to a pre-existing file the build wave
   may make. Every other deliverable is new files.
5. **Horizontal position is owned by the new pilot module, not the rig.**
   Player input drives a small dead-reckoning integrator (heading + speed ->
   dx/dz per frame) that writes `controller.root.position.x/z` directly each
   frame, alongside a `PilotTrack` (same shape as `BiologgingTrack`) whose
   `sample()` returns the live computed pose (yaw = heading, pitch/roll = a
   small bounded dive/bank feel, depthM = a separate depth accumulator
   clamped to a safe band above the seabed, flukePhase incrementing with
   speed, flukeAmp from throttle). `driveOrca` itself is never modified.
6. **New route, disjoint from every existing route.** A new sandbox page at
   `web/app/(sandbox)/orca-strike/page.tsx` (+ `OrcaStrikeScene.tsx` +
   `OrcaStrikeHost.tsx`, mirroring the `orca/` and `journey/` sandbox
   pairs). `/workbench` and every other existing route are never touched.
7. **New library code lives under three disjoint new directories**:
   `web/lib/scene/orcaPilot/` (input + pose integrator + chase camera),
   `web/lib/scene/boats/` (boat entity, spawn, collision, sink FX,
   `BoatMarker.tsx`), `web/lib/scene/sonar/` (radar target list, ping/HUD,
   teleport beat). No file in these directories is shared with any other
   in-flight work.
8. **Bathymetry reuse**: the new route mounts the real tileset via
   `useTilesLayer` exactly as the `tiles3d`/`orca` sandboxes do (same
   `fitScaleToWidth`/`SCENE_WIDTH` frame), so the orca swims over the real
   bathymetry, not a flat plane. If the real tileset URL or a fit issue blocks
   this within the time budget, a flat water-plane fallback (matching
   `OrcaSandboxScene`'s plane) is an acceptable documented fallback, never a
   silent one.
9. **No acoustic/scientific claims.** HUNT never touches the workbench's
   measured/modeled honesty machinery and adds no acoustic estimate, no AIS
   claim, and no navigational claim. A single small in-scene disclaimer line
   ("arcade prototype, not navigational or scientific data") is the only
   honesty-adjacent UI text required.
10. **Bash.tv deliverable is a paste-ready prompt package, not a promise of a
    second build.** Wave 2 produces `deliverable/BASHTV_BUILD_PROMPT.md`
    describing the game, the reusable real assets (orca mesh URL, bathymetry
    tileset conventions, gazetteer place list), and a suggested build
    sequence sized for Bash.tv's single-agent-in-a-VM model with its own
    credit cost in mind (fewer, larger prompts over many small back-and-forth
    turns). It is written once the in-repo prototype's real decisions are
    locked, so it is not speculative.
11. **Git**: O0 (this session) is the sole git actor. No dispatched agent runs
    a git command. Nothing is committed without an explicit operator request
    in this session; O0 returns a commit plan on reconciliation instead.

## Wave structure

- **HUNT-W1 (discovery, parallel, read-only, NOT gated).** Members write
  disjoint findings files under `findings/`:
  - `findings/HUNT-INPUT.md`: confirm there is truly no existing keyboard/
    pointer-lock controller to reuse (already grep-verified absent by O0;
    this member re-verifies and checks `package.json`/`node_modules` for any
    unused-but-installed input helper) and proposes the minimal input-state
    shape (keys held, mouse delta, a throttle/boost key).
  - `findings/HUNT-BATHY.md`: confirm the exact tileset URL and fit options
    the `orca`/`tiles3d` sandboxes use (or would use) so HUNT-W2 mounts the
    real bathymetry correctly on the first attempt, and confirms
    `getSurfaceY` availability for a seabed collision floor.
  - `findings/HUNT-ADVERSARIAL.md` (adversarial member): hunt for anything
    that would make the additive `OrcaController` edit unsafe (other callers
    of `createOrcaController`, any test coverage on it, whether `timeScale`/
    `elapsed` semantics matter for a live pose source), and flag any hidden
    perf budget (frame-time budgets exist in `web/lib/scene/ocean/perf.ts` -
    check whether they apply here).
- **HUNT-W2 (build, parallel, NEW files preferred, NOT gated).** Disjoint
  owners, each ending with a short WIRING note in its own directory:
  - Agent A - `web/lib/scene/orcaPilot/`: input capture, dead-reckoning
    integrator, `PilotTrack`, third-person chase camera, and the ONE
    permitted edit to `OrcaController.ts` (locked decision 4).
  - Agent B - `web/lib/scene/boats/`: `BoatEntity`, `spawnBoats`, ram/
    collision test, sink animation, `BoatMarker.tsx` (r3f, modeled on
    `buoyMarker.tsx`).
  - Agent C - `web/lib/scene/sonar/`: radar target list (boats + a handful of
    curated `gazetteer.ts` places), ping/HUD overlay, Floo teleport beat.
  - Agent D - `deliverable/BASHTV_BUILD_PROMPT.md`: the Bash.tv build-prompt
    package (locked decision 10). Depends only on the locked decisions in
    this file, not on A/B/C's code, so it can run in parallel.
  Each of A/B/C runs `npm run typecheck` and `npm run lint` in `web/` against
  its own new files before reporting done; code that cannot be made to pass
  is reverted from the working tree with the revert stated in its findings,
  never left broken.
- **HUNT-INT (integration, single serialized editor, GATED on O0).** Wires
  A+B+C into `web/app/(sandbox)/orca-strike/` (locked decision 6), runs
  `npm run typecheck` + `npm run lint` over the whole `web/` tree, confirms
  `/workbench` and other existing routes are untouched (`git status` scoped
  diff). Runs no git commands (O0 syncs/freezes/commits around this wave).
- **HUNT-ACCEPT (acceptance, GATED on O0).** Starts the Next dev server,
  loads `/orca-strike` in a real browser (Cursor's browser MCP tools),
  verifies: orca responds to input and moves over the bathymetry (or the
  documented flat-plane fallback), at least one boat can be rammed and sinks,
  the sonar ping shows targets, teleporting to a pinged target snaps the orca
  there, and `/workbench` still loads unchanged. Captures screenshots to
  `gate-captures/`. Honest verdict with named failures if any step does not
  work within the time budget; a partial pass (e.g. sonar works, teleport
  does not) is reported as such, never rounded up.

Remediation-loop cap: 2 repeats per gate (HUNT-INT, HUNT-ACCEPT). On a second
failure the runner stops and escalates to O0 with the named failures rather
than attempting a third pass.

## Acceptance criteria (hard, checkable)

1. `npm run typecheck` and `npm run lint` pass in `web/` with HUNT's changes
   included.
2. `/orca-strike` loads in a browser without a console error that blocks
   render.
3. Pressing movement keys visibly changes the orca's world position over
   multiple frames (verified via a CDP `Runtime.evaluate` position read or an
   on-screen debug readout, not eyeballed alone).
4. At least one spawned boat, when the orca's world position is driven within
   its collision radius, transitions to a sunk state (visually distinct:
   rotated/lowered/particle burst) and this is captured in a screenshot.
5. The sonar action produces a non-empty target list with bearing/range for
   at least one boat.
6. Selecting a sonar target moves the orca's world position to within a
   small tolerance of that target's projected world position within one
   frame of the teleport beat completing.
7. `/workbench` (and any other pre-existing route touched by nothing in this
   lane) still renders with no new console errors, confirming no regression.
8. `deliverable/BASHTV_BUILD_PROMPT.md` exists, names the real reusable
   assets by path/URL, and states a build sequence sized to minimize Bash.tv
   agent turns (credit discipline), not just a feature list.

Any criterion not met is reported as a named gap in the return, never
silently dropped.

## Gated waves and operator involvement

- HUNT-W1 and HUNT-W2: **not gated**, run immediately on dispatch.
- HUNT-INT: **GATED**. Requires O0 review of the build-wave findings and an
  explicit go-ahead before the single integration editor touches the new
  route.
- HUNT-ACCEPT: **GATED**. Requires O0 approval to run the dev server and
  drive a real browser session.
- No step in this lane pushes to a remote, opens a PR, or deploys anywhere.
  Those would be a further, separate operator gate not chartered here.

## Model routing and token discipline

| role | model tier | recommended slug | reason | expected context | expected file reads | cost caveat |
|---|---|---|---|---|---|---|
| lane orchestrator (HUNT-O) | high-reasoning | claude-sonnet-5-thinking-high | owns the one shared-file edit (locked decision 4), reconciles A/B/C, runs the gated waves; needs cross-file judgment without opus-tier cost | this waveset.md + dispatch.md + the ~12 grounded files above | ~15-20 files | highest-cost role in this lane; keep it out of per-boat/per-marker mechanical edits, delegate those to build agents |
| HUNT-W1 discovery (all 3) | fast | composer-2.5-fast | pure inventory/search/confirmation, no architectural judgment | this waveset.md + a narrow grep/read set per topic | 3-8 files each | cap each member to its one findings file; no exploratory wandering |
| HUNT-W2 Agent A (orcaPilot + the OrcaController edit) | high-reasoning | claude-sonnet-5-thinking-high | the one risky shared-file touch; must not break the locked composition order | OrcaController.ts, OrcaRig.ts, biologging.ts, this waveset.md | 5-8 files | the only build agent that needs high-reasoning; A/B/C otherwise cost the same tier |
| HUNT-W2 Agent B (boats) | balanced | gpt-5.5-medium | bounded new-file mechanic with local typecheck validation, no shared-file risk | buoyMarker.tsx, worldPointToLatLng.ts, this waveset.md | 3-5 files | validate locally before returning |
| HUNT-W2 Agent C (sonar/teleport) | balanced | gpt-5.5-medium | bounded new-file mechanic, reuses gazetteer + picking conventions | gazetteer.ts, worldPointToLatLng.ts, director.ts, this waveset.md | 4-6 files | validate locally before returning |
| HUNT-W2 Agent D (Bash.tv deliverable) | fast | composer-2.5-fast | synthesis of already-locked decisions into a prompt document, no new judgment | this waveset.md only | 1 file | do not re-derive decisions, transcribe them |
| HUNT-INT | high-reasoning | claude-sonnet-5-thinking-high | cross-file wiring risk, must not regress /workbench or other routes | A/B/C outputs + WorkbenchScene.tsx (read-only reference) | 10-15 files | single serialized editor, run after A/B/C land |
| HUNT-ACCEPT | high-reasoning | claude-sonnet-5-thinking-high | judgment on partial-pass honesty, browser verification | gate-captures/, the new route only | 5-8 files | cite captures, do not re-read the whole chat |

Model enforcement note: when dispatched through a tool that exposes a `model`
argument, set it to the slug above. When it does not, this table stays the
instruction and the runner reports `model_enforcement: not_available`.

Savings claim: none asserted. This table makes model selection auditable
before execution and reserves the high-reasoning tier for the one genuinely
risky shared-file touch and the two judgment-heavy gates; a later accounting
pass would be needed to claim actual token/cost savings.

## Escalation (operator-protection catch)

The dispatched HUNT lane orchestrator answers to O0 (this session), never to
the human operator directly. If it hits a decision, trade-off, or
locked-decision conflict (for example: the real tileset URL does not fit in
time and it wants to fall back to the flat-plane, or the additive
`OrcaController` edit turns out to require touching more than the one
optional param), it pauses and returns the question to O0 in its summary
rather than soliciting the operator. HUNT-INT and HUNT-ACCEPT are GATED and
require O0's explicit go-ahead, which is only valid when O0 holds the
operator's approval for it (already given in this session for the charter and
build; HUNT-INT/HUNT-ACCEPT approval is requested fresh at reconciliation
time since they are gated). An urgent finding (for example a regression on
`/workbench`) interrupts and is returned immediately rather than held to the
end of a wave. Dispatch depth is bounded to 1: the lane orchestrator may
dispatch HUNT-W1/W2 wave subagents; those wave subagents never dispatch
further background orchestrators.
