# HCHK-W1a grounding findings

Lens: grounding. Reviewer: HCHK-W1a, read-only. Scope: verify every claim in
`HUNT-INT`'s plan and the `orcaPilot`/`boats`/`sonar` `WIRING.md` integration
steps against the ACTUAL exported symbols and types in the delivered code.
Flag wiring-doc code samples that would not compile against the real exports,
stale `repo_state_verified_against`, and cited paths that do not exist.

Method: read every delivered source file and its `WIRING.md`, read the one
edited pre-existing file (`OrcaController.ts`) plus its git diff, cross-checked
every exported symbol against the type it is claimed to satisfy, ran
`git rev-parse HEAD` and `npm run typecheck` for the two verifiable claims.

## Urgent active-regression check

None found. The single pre-existing-file edit is additive and backward
compatible (see PASS-2). No delivered code path mutates any existing route or
existing symbol behavior.

## Verdict for this lens

Effectively GO with one BLOCKING wiring-doc defect (G1) that will make a
literal `HUNT-INT` transcription fail `tsc`, and two low-severity doc
inaccuracies (G2, G3). None of the delivered library code is wrong. The
defects are all in `WIRING.md` prose / code comments, not in the compiled
exports.

---

## G1 (BLOCKING for a literal HUNT-INT transcription): sonar `WIRING.md` boat-mapping sample reads `boat.label`, which does not exist on the delivered `Boat` type

- Wiring doc: `web/lib/scene/sonar/WIRING.md:33-49`, the "On sonar ping" sample:
  ```ts
  boats: liveBoats.map((boat) => ({
    id: boat.id,
    label: boat.label,   // <-- boat.label
    x: boat.x,
    z: boat.z,
  })),
  ```
- Delivered type: `web/lib/scene/boats/BoatEntity.ts:3-15`. `Boat` has exactly
  `id, x, z, heading, state, sinkProgress, collisionRadius`. There is no
  `label` field.
- Consequence: if `liveBoats` is typed `Boat[]` (the only boat type this lane
  ships, exported from `web/lib/scene/boats/index.ts:1`), `boat.label` is a
  `tsc` error TS2339 "Property 'label' does not exist on type 'Boat'". The
  sonar `WIRING.md` integration sample therefore does NOT compile against the
  real `boats` export as written.
- Why it slipped through: `SonarSourceTarget.label` is optional
  (`web/lib/scene/sonar/radarTargets.ts:33-38`, `label?: string`), and the
  `sonar` module deliberately imports no boat code, so `radarTargets.ts`
  itself type-checks in isolation. The mismatch only appears at the
  integration seam the WIRING sample describes, which is exactly HUNT-INT's
  job and is not covered by either agent's isolated `typecheck`.
- Concrete fix for HUNT-INT (not prescribing a plan, just noting the seam):
  the integrator must synthesize a label, e.g. `label: boat.id`, since `Boat`
  carries no human label. Sonar rows fall back to `source.id` when `label` is
  omitted anyway (`radarTargets.ts:141`, `const label = source.label ?? source.id`),
  so dropping the `label` key entirely also compiles and is honest.

## G2 (low severity, doc inaccuracy): orcaPilot `WIRING.md` step 4 overstates what the `elapsed` argument drives

- Wiring doc: `web/lib/scene/orcaPilot/WIRING.md:82-86` states the `elapsed`
  argument passed to `controller.update()` is "still consumed for
  LOD/eye-gaze/mouth timing inside `OrcaController.update()`".
- Delivered code: `web/lib/scene/orca/OrcaController.ts:122-160`. Inside
  `update(dt, elapsed, cameraWorldPos)`, `elapsed` is used on exactly ONE line,
  `const pose = track.sample(elapsed * timeScale)` (line 123). LOD is derived
  from camera distance (lines 126-129), and mouth/eyes/physics timing all use
  `dt` (lines 144, 153, 156, 160), never `elapsed`.
- Consequence: harmless in practice (passing a real per-frame clock is fine),
  but the stated rationale is wrong. When a `PilotTrack` is supplied,
  `sample()` ignores its argument (`web/lib/scene/orcaPilot/PilotTrack.ts:37`),
  so `elapsed` is effectively unused in the piloted route, not "consumed for
  LOD/eye-gaze/mouth timing." A HUNT-INT reader trusting this note might
  wrongly believe `elapsed` accuracy affects animation timing.

## G3 (low severity, path citation): `deadReckoning.ts` comment cites the wrong file for the `getSurfaceY` probe shape

- Code comment: `web/lib/scene/orcaPilot/deadReckoning.ts:73-74` cites
  "`web/lib/scene/camera/director.ts`'s `CameraDirectorHandle.getSurfaceY`"
  for the seabed probe shape.
- Actual definition: `CameraDirectorHandle` and its `getSurfaceY` member are
  defined in `web/lib/scene/camera/types.ts:113,136`
  (`getSurfaceY?: ((x: number, z: number) => number | null) | null`).
  `director.ts` only consumes it (`web/lib/scene/camera/director.ts:124,150-151`).
- Note: the `orcaPilot/WIRING.md:104-111` version of the same reference cites
  `web/lib/scene/camera/types.ts` correctly, so the two internal docs
  disagree. The WIRING doc is right; the inline comment is off by one file.
  Also note the real probe returns a scene-Y value or `null`, not metres, so
  the integrator-side "convert probed elevation to metres" step the WIRING
  calls out (`WIRING.md:106-117`) is genuinely required, not optional.

---

## Claims verified as GROUNDED (no defect)

### PASS-1: `repo_state_verified_against` is current, NOT stale
- `git rev-parse HEAD` returns `cbe6483fb2157edcdca27e7b21dfffa7b961a7b5`.
- Matches HCHK `waveset.md:24` and HUNT `waveset.md:6`. No commit has landed
  since charter. The delivered code is uncommitted working-tree state exactly
  as both wavesets state.

### PASS-2: the one permitted `OrcaController.ts` edit matches locked decision 4 exactly
- HUNT `waveset.md:118-124` (locked decision 4) permits ONLY an additive
  optional `track?: BiologgingTrack` param that skips `loadBiologging`.
- `git diff web/lib/scene/orca/OrcaController.ts`: two hunks only. Adds
  `track?: BiologgingTrack` to `OrcaControllerOptions`
  (`OrcaController.ts:39-42`) and changes the load line to
  `opts.track ? Promise.resolve(opts.track) : loadBiologging(motionUrl)`
  (`OrcaController.ts:76`). No other file line changed. Backward compatible:
  every existing caller omits `track` and hits the original path.

### PASS-3: orcaPilot exports match `WIRING.md`; `PilotTrack` structurally satisfies `BiologgingTrack`
- `WIRING.md:16-30` export list matches `web/lib/scene/orcaPilot/index.ts:5-11`
  symbol-for-symbol (`createOrcaPilotInputSampler`, `createOrcaPilot`,
  `createPilotTrack`, `createChaseCamera`, and the seven exported types).
- `createPilotTrack` (`PilotTrack.ts:29-41`) returns an object with
  `manifest, data, nSamples, nChannels, sampleRate, duration, sample`, which
  are exactly the seven required members of `BiologgingTrack`
  (`web/lib/scene/orca/motion/biologging.ts:49-58`). `PILOT_MANIFEST`
  (`PilotTrack.ts:13-21`) provides all required `BiologgingManifest` fields
  (`biologging.ts:21-38`: `simulated, bin_file, sample_rate_hz, n_samples,
  n_channels, duration_s`). So `pilot.track` is assignable to
  `OrcaControllerOptions.track` and to `createOrcaController`'s
  `track.sample(...)` call site. Confirmed by PASS-6.

### PASS-4: orcaPilot `WIRING.md` step 3 and step 4 samples compile against real exports
- Step 3 (`WIRING.md:60-66`): `createOrcaController({ env, worldUnitsPerMeter:
  wupm, track: pilot.track })`. `OrcaControllerOptions`
  (`OrcaController.ts:28-43`) requires `env: WfxEnvHandle` and accepts optional
  `worldUnitsPerMeter` and `track`. Valid.
- Step 4 (`WIRING.md:70-75`): `controller.root` is `THREE.Group`
  (`OrcaController.ts:54`), which matches `pilot.update(input, dt,
  controllerRoot: THREE.Group)` (`deadReckoning.ts:103`).
  `controller.update(dt, elapsed, camera.position)` matches
  `OrcaController.ts:58`. `pilot.track.sample(0).yaw` returns a number from
  `OrcaPose` (`biologging.ts:40-47`). All valid.

### PASS-5: boats exports and render sample match; sonar exports match
- boats `WIRING.md:10-18` import list (`BoatMarker, advanceSink,
  checkRamCollisions, spawnBoats, type Boat`) all exist in
  `web/lib/scene/boats/index.ts:1-21`. Render sample `WIRING.md:75-81` uses
  `boat.heading`/`boat.sinkProgress`, both present on `Boat`
  (`BoatEntity.ts:8,11`), and `BoatMarkerProps` requires exactly those two
  (`BoatMarker.tsx:6-11`). `spawnBoats({ seed })`, `checkRamCollisions(...)`,
  `advanceSink(boat, dt)` all match their signatures
  (`spawnBoats.ts:38`, `collision.ts:3-8`, `sinkAnimation.ts:18-22`).
- sonar `WIRING.md:9-12` "Public Surface" names `getCuratedPlaceTargets`,
  `buildRadarTargets`, `createSonarPing`, `createTeleportBeat`, all exported
  from `web/lib/scene/sonar/index.ts:1-19`.

### PASS-6: sonar curated place IDs all exist in the gazetteer and fall in the documented bounds
- `CURATED_PLACE_IDS` (`radarTargets.ts:47-56`) lists eight slugs. Every one
  exists in `web/lib/geo/gazetteer.ts` (verified: `east-sound:76`,
  `friday-harbor:86`, `orcas-village:106`, `roche-harbor:146`,
  `deer-harbor:156`, `san-juan-island:186`, `lime-kiln:296`,
  `jones-island:356`).
- All eight lat/lng fall inside the sonar `WIRING.md:19-24` `TILESET_BOUNDS`
  (`48.4..48.7` lat, `-123.25..-122.75` lng), so `getCuratedPlaceTargets`
  (`radarTargets.ts:84-97`) returns a non-empty place set rather than silently
  dropping every place. `HeightmapBounds` field shape used by the bounds
  literal matches `web/lib/sceneIntent.ts:16-21`, and `projectToScene`
  (`sceneIntent.ts:67-76`) returns the `[x, z]` tuple `radarTargets.ts:94`
  destructures.

### PASS-7: the orchestrator-summary bearing fix is present as reported
- HUNT-ORCHESTRATOR-SUMMARY.md:45-50 claims `targetBearingRad` was changed to
  `Math.atan2(-dz, dx)`. Confirmed at `radarTargets.ts:69-73`
  (`return Math.atan2(-dz, dx)`), and the accompanying convention doc comment
  is present at `radarTargets.ts:13-31,64-68`, citing `deadReckoning.ts` by
  name as claimed.

### PASS-8: `npm run typecheck` passes, as self-reported
- Ran `npm run typecheck` (`tsc --noEmit`) from `web/`: exit 0, no output.
  This grounds the identical claim in all three `WIRING.md` validation
  sections and in the orchestrator summary. Note this does not catch G1,
  because the failing code (`boat.label`) does not exist in the tree yet; it
  is only introduced when HUNT-INT transcribes the sonar WIRING sample.

### PASS-9: cited support paths exist
- orcaPilot `WIRING.md:10` cites
  `wavves/lanes/20260709_orca-boat-hunt/findings/HUNT-W2-AGENT-A.md`, which
  exists. `sonar/WIRING.md` and `boats/WIRING.md` cite only in-directory
  symbols and the two `sceneIntent`/`gazetteer` modules, all confirmed present.
