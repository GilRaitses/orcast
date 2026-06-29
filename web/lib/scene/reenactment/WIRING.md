# BRE reenactment — wiring

Net-new, sandbox-only. Maps the BSH scrub playhead to scene time, spawns orcas
from the BAM acoustic classification, and drives each from the measured SRKW
DTAG telemetry. Mounted into SalishScene later by the integrator (gated).

## Files (BRE-owned, net-new / extended)

| File | Role |
|------|------|
| `web/lib/scene/reenactment/types.ts` | consumer contracts (acoustic record, clips, spawn record, timeline subset, `SpawnCountBasis`) |
| `web/lib/scene/reenactment/spawnFromClassification.ts` | classification -> multi-orca spawn record; honest count basis; per-instance ethogram clips; `presenceAtTime` |
| `web/lib/scene/reenactment/OrcaPool.ts` | spawn + drive N `OrcaController` instances (real SRKW driver); per-instance phase offset; `instanceLabels()` |
| `web/lib/scene/reenactment/TimelineDriver.ts` | follow the authority playhead; presence-gated visibility |
| `web/lib/scene/reenactment/povBinding.ts` | bind both camera POVs to BST's POV-selection object via the Camera Director |
| `web/lib/scene/reenactment/loaders.ts` | fetch the classification + clip manifest |
| `web/lib/scene/reenactment/index.ts` | barrel (re-exports the ethogram) |
| `web/lib/scene/orca/motion/clips/clipSampleTime.ts` | fold playhead into a clip window; optional per-instance `phaseOffsetS` |
| `web/lib/scene/orca/motion/clips/ethogram.ts` | behavior -> motion-clip ethogram from the manifest; per-instance clip assignment; disclosed modeled labels |
| `web/public/orca/motion/clips/manifest.json` | REAL behavior clips derived from the SRKW driver (web-served; fetched at `/orca/motion/clips/manifest.json`) |
| `web/app/(sandbox)/reenactment/` | net-new sandbox: multi-orca scrub/slow demo, both POVs, frame-time |

The clip manifest is produced offline by `modeling/acoustic/derive_srkw_clips.py`
from `web/public/orca/motion/orca_srkw_oo14_driver.bin` (measured kinematics). It
now carries 5 kinematic-matched classes (Traveling 8, Side_rolls 5,
Exploratory_dives 1, Surface_Active 7, Vertical_loop 9); Surface_Active and
Vertical_loop are emitted only when a real SRKW window passes their kinematic
guard, so a class is never a mislabeled fallback window.

## Multi-orca + ethogram (BRE-BUILD deepening)

- `buildSpawnRecord` spawns up to `nMax` (R08 cap 3). The COUNT is honest:
  `summary.spawnCount` capped at `nMax`, with `countBasis` mirroring BAM's
  `spawnCountBasis`. `demoCountOverride` is a SANDBOX-ONLY capability override,
  stamped `capability_demo` and labeled on-screen as NOT a model estimate.
- WHICH clip each orca plays is a KINEMATIC choice from `ethogram.assign(...)`
  (R04), disclosed as a modeled match, NEVER driven by the acoustic output.
  `distinct` policy rotates behaviors for breadth; `fixed`/`clipId` pins one.
- Each instance carries `behaviorLabel` (disclosed modeled string) and a small
  `phaseOffsetS` so orcas sharing a clip sample a DIFFERENT real moment of the
  driver (still measured telemetry, never synthesized).
- Camera POV reuses BST's `runStationPOV` through `bindReenactmentPov`; it only
  drives the Camera Director and never bypasses its surface/altitude clamps.

## Dependency gaps flagged (BRE consumes BAM/BSH/BST)

- **BAM (count):** the current `classification.json` is presence-only
  (`spawnCount: 1`, basis `presence_only`; `not_claimed` includes "whale count"
  and "single vs multiple callers"). So the HONEST spawn count is 0/1. The
  multi-orca CAPABILITY is built and proven, but it only spawns >1 under the
  labeled `capability_demo` override until BAM ships a count head with held-out
  eval. Do NOT spawn >1 from the real estimate.
- **BSH (clock):** the structural `ReenactmentTimeline` is a subset of BSH's
  `SpectroTimelineAuthority`; the sandbox runs a `SandboxClock` implementing that
  contract, and `/slice` already exercises the real BSH WebAudio engine. No gap
  for the contract; the real-engine multi-orca path lands at integrate.
- **BST (POV):** the POV-selection object (`runStationPOV`) has landed in
  `web/lib/scene/hydrophone`; `povBinding.ts` consumes it directly. No gap.

## R08 shared-asset optimization (deferred, ORCA-coordinated)

`OrcaPool` uses `createOrcaController` per instance (the tested path). Sharing one
`loadOrcaMesh` + `makeOrcaMaterial` + `BiologgingTrack` across rigs needs
`createOrcaController` to accept preloaded assets, which lives in the ORCA-owned
stack and is a serialized, O0-coordinated change. Deferred to BRE-INTEGRATE; for
nMax=3 the only saving is one-time spawn load + memory (per-frame cost is N rig
skinning passes either way).

## Cross-lane contracts consumed

- **Timeline (BSH):** BRE follows a `ReenactmentTimeline` (a structural subset of
  BSH's `SpectroTimelineAuthority`: `durationS`, `currentTimeS`, `playbackRate`,
  `playing`, `subscribe`). Because it is structural, BRE compiles independently
  of BSH's concrete impl; pass BSH's authority straight in. `currentTimeS` is
  ALREADY advanced at `playbackRate`, so BRE does not rescale time (slow-mo and
  scrub are handled entirely by the authority).
- **Classification (BAM):** `/hydrophone/slice/classification.json`
  (`bsw-acoustic-classification/v1`). `summary.spawnCount` (presence-only: 0/1,
  capped at `nMax`) sets how many orcas spawn; `windows[]` gives presence +
  confidence per time so visibility + HUD label track the playhead.

## Drive loop (sandbox / integrator)

```ts
const classification = await loadClassification();
const manifest = await loadClipManifest();
const record = buildSpawnRecord(classification, manifest, {
  anchor: { lat: 48.5583362, lng: -123.1735774 }, clipId: "Traveling", nMax: 3,
});
const pool = createOrcaPool({ env, bounds, sceneDepth, worldUnitsPerMeter, depthScale });
await pool.setSpawn(record);
scene.add(pool.group);
const driver = createTimelineDriver(spectroAuthority, pool, classification, { presenceGated: true });
// in useFrame:
driver.update(dt, cameraWorldPos);   // reads authority.currentTimeS, drives pool
// HUD: driver.getState().hudLabel  -> "estimated: SRKW call present (confidence 74%)"
```

## Honesty (locked)

- Motion is measured SRKW DTAG telemetry only; `OrcaPool` always loads
  `REAL_SRKW_MOTION_URL`. No fabricated trajectory, no `orca_dev_track`, no
  humpback bin as a driver.
- Acoustic presence picks WHETHER/HOW MANY orcas spawn + the HUD label. It never
  touches depth/pitch/roll/yaw/fluke or clip selection.
- Behavior clip = a window into the real driver; the behavior NAME is a modeled
  kinematic match to the humpback ethogram (R04), disclosed as such.
- Mandatory on-screen label: "Kinematics are representative SRKW DTAG motion,
  not the recorded animal." (carried in the clip manifest + spawn record).
- Cross-sensor: hydrophone audio and the oo14 DTAG deployment are different
  animals; the scrub sync is illustrative (`crossSensor: "illustrative"`).

## Perf

N `OrcaController` instances join the existing opaque depth pre-pass (no third
full render). LOD per instance (near/mid/far) is inherited from
`OrcaController`. Demo `spawnCount` is presence-only (1), so cost is the
single-orca baseline; `nMax` caps multi-spawn at 3 (R08 laptop budget).
