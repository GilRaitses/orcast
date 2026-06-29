# BRE reenactment — wiring

Net-new, sandbox-only. Maps the BSH scrub playhead to scene time, spawns orcas
from the BAM acoustic classification, and drives each from the measured SRKW
DTAG telemetry. Mounted into SalishScene later by the integrator (gated).

## Files (BRE-owned, net-new)

| File | Role |
|------|------|
| `web/lib/scene/reenactment/types.ts` | consumer contracts (acoustic record, clips, spawn record, timeline subset) |
| `web/lib/scene/reenactment/spawnFromClassification.ts` | classification -> spawn record; `presenceAtTime` |
| `web/lib/scene/reenactment/OrcaPool.ts` | spawn + drive N `OrcaController` instances (real SRKW driver) |
| `web/lib/scene/reenactment/TimelineDriver.ts` | follow the authority playhead; presence-gated visibility |
| `web/lib/scene/reenactment/loaders.ts` | fetch the classification + clip manifest |
| `web/lib/scene/reenactment/index.ts` | barrel |
| `web/lib/scene/orca/motion/clips/clipSampleTime.ts` | fold playhead into a clip window |
| `web/public/orca/motion/clips/manifest.json` | REAL behavior clips derived from the SRKW driver (web-served; fetched at `/orca/motion/clips/manifest.json`) |

The clip manifest is produced offline by `modeling/acoustic/derive_srkw_clips.py`
from `web/public/orca/motion/orca_srkw_oo14_driver.bin` (measured kinematics).

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
