# BSW-R08 - Multi-orca instancing & scrub-synced timeline

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent e445b4de; written by the BSW sub-orchestrator.

## Summary

- **Today the twin mounts one orca:** `SalishScene.tsx` builds a single `OrcaRig` via `createOrcaController`, driven by the real SRKW driver with `track.sample(t)` each frame. There is **no multi-orca implementation** and **no `InstancedMesh`** anywhere under `web/`.
- **Depth pre-pass join is already correct for N opaque rigs:** `Water2Rig` calls `handle.renderDepthPrepass(gl, scene, camera)` once per frame. Any orca `SkinnedMesh` in the scene graph is drawn in that pass and the main opaque pass. **No third full-scene render** is required to add orcas.
- **Honest multi-orca pattern:** duplicate `OrcaController` instances with shared geometry + material + `WfxEnvHandle`, distinct `projectToScene` anchors, per-instance `track.sample(t)`. Acoustic BAM drives spawn count/type/labels; kinematic R04 drives motion clip windows, never hydrophone-invented trajectories.
- **LOD is per-orca and already implemented:** camera distance thresholds at **22 / 60 scene units** drop physics, mouth, gaze.
- **Scrub sync:** BSH `SpectroTimelineAuthority.currentTimeS` must replace SalishScene's wall-clock `elapsed`; BRE subscribes and passes `t` into each controller's `update(dt, t, cameraPos)`.
- **Perf:** incremental cost scales linearly with N. Single-orca CPU physics is <0.1 ms/frame (estimated); N=5 near-LOD adds ~35 draw calls and ~0.5-1.0 ms/frame GPU (estimated) on desktop, within 60 fps headroom.

## In-repo findings (cited)

### Orca mount (`SalishScene.tsx`)

```834:837:web/app/components/scene/SalishScene.tsx
// handed. Mounted AFTER Water2Rig so the orca is part of the opaque depth
// pre-pass the water already runs (no third full render). HONESTY: modeled
// animal, real SRKW DTAG telemetry; the humpback track is contrast-only and
// never drives this orca.
```

```884:924:web/app/components/scene/SalishScene.tsx
    createOrcaController({
      env, meshUrl: ORCA_MESH_URL, motionUrl: REAL_SRKW_MOTION_URL,
      worldUnitsPerMeter, depthScale: ORCA_DEPTH_SCALE, timeScale: 1,
    })
  useFrame((state, dt) => {
    const c = controllerRef.current; if (!c) return;
    if (startRef.current === null) startRef.current = state.clock.elapsedTime;
    const elapsed = ORCA_TRACK_START_S + (state.clock.elapsedTime - startRef.current);
    camera.getWorldPosition(camWorld);
    c.update(Math.min(dt, 1 / 30), elapsed, camWorld);
  });
```

Anchor/scale: `ORCA_ANCHOR = {lat: 48.57, lng: -123.02}`, `ORCA_BODY_SCALE = 0.5`. `worldUnitsPerMeter = fitRadius / geoRadiusMeters(TILESET_BOUNDS)`, fitRadius ~60 scene units. Shared WFX env via `makeRealWfxEnv`.

### Depth pre-pass (`depthWater.ts`)

```575:582:web/lib/scene/water2/depthWater.ts
    renderDepthPrepass(renderer, scene, camera) {
      const prevTarget = renderer.getRenderTarget();
      const wasVisible = mesh.visible;
      mesh.visible = false;
      renderer.setRenderTarget(depthTarget);
      renderer.render(scene, camera);
      renderer.setRenderTarget(prevTarget);
      mesh.visible = wasVisible;
    },
```

Baseline cost model (water sandbox): one opaque render = U; running twin ~2U (pre-pass + main), not a third pass per orca.

### Single-orca cost (`OrcaController.ts`)

```101:112:web/lib/scene/orca/OrcaController.ts
  const cost: OrcaCost = {
    triangles,
    bones: 4 + rig.bones.caudal.length + 2,
    drawCalls: 1 /*body*/ + 2 /*eyes*/ + 4 /*mouth parts*/,
    springsPerFrame: 2 + rig.bones.caudal.length,
    lod: "near",
  };
```

Triangles ~3.1k (Trouvaille mesh); bones 11; draw calls 7 (near/mid); CPU physics <0.1 ms/frame (OPHYS-R). LOD gates: dist>60 -> far (skip physics, hide mouth, disable gaze); dist>22 -> mid. Motion: `track.sample(elapsed*timeScale)` -> `driveOrca` (driver `simulated:false`, 7 ch, 8187.4 s, 5 Hz).

### Multi-orca sandbox + instancing
`web/app/(sandbox)/orca/OrcaSandboxScene.tsx` proves single-orca controller + scrub via `?t=`; does not spawn multiple. Grep finds **zero `InstancedMesh`** under `web/`. Charter pattern: duplicate `OrcaRig` mounts with distinct anchors.

## Multi-orca instancing approach (geometry/material sharing, LOD, depth pre-pass join)

**Why not `InstancedMesh`:** `OrcaRig` is GPU-skinned with an 11-bone skeleton + per-frame bone matrix updates; `InstancedMesh` doesn't skin per instance with independent bone poses. Use N separate `SkinnedMesh` rigs sharing heavy assets.

| Asset | Share strategy |
|-------|----------------|
| Base geometry | Load once via `loadOrcaMesh`; `geometry.clone()` per rig for unique skin attributes |
| Textures / PBR maps | Single `sourceMaterial.map/normalMap` references |
| Body material | One `MeshPhysicalMaterial` or shared uniforms; `setEnv` on all when env updates |
| WFX env | One `makeRealWfxEnv` per scene |
| Motion | Each instance: own `BiologgingTrack` (same SRKW URL or clip window via R04 offset) |
| Eyes/mouth | Per instance (6 extra draw calls per near orca) |

```typescript
// web/lib/scene/reenactment/OrcaPool.ts (proposed)
const shared = await loadOrcaMesh(ORCA_MESH_URL);
const sharedMat = makeOrcaMaterial({ map: shared.sourceMaterial.map, normalMap: shared.sourceMaterial.normalMap, env });
function spawnOrca(anchor, motionUrl, clip?) {
  const rig = buildOrcaRig(shared.geometry.clone(), sharedMat.material, DEFAULT_LIMITS);
  return { root: rig.root, update, track, cost, dispose };
}
```

**Depth pre-pass join (no third render):** orcas added to same `scene`, opaque (`SkinnedMesh` default), `visible=true` during `renderDepthPrepass`. Each adds draw cost to both pre-pass RT and main framebuffer, not another full-scene pass. Mount order preserved: IntentDirectorRig -> RealismRig -> Water2Rig -> OrcaRig(s) -> scenic/bathy -> tiles.

**LOD per instance:** reuse `OrcaController.update` distance test unchanged (near <=22 full; mid 22-60 physics+mouth no gaze; far >60 body skinning only ~3 draws).

**Spacing:** `instances[i].root.position.set(ax + i*8*worldUnitsPerMeter, SEA_LEVEL_Y, az)` (~8 m separation, estimated readable spacing).

## Spawn-from-classification record contract (proposed data shape)

```typescript
/** BAM inference output for one scrubbed audio slice (read-only to BRE). */
export interface AcousticClassificationRecord {
  schema: "bsw-acoustic-classification/v1";
  clipId: string; stationId: string;
  windowStartS: number; windowEndS: number;
  presence: boolean;
  presenceConfidence: number;        // 0..1, real softmax/sigmoid
  callTypes?: Array<{ label: string; confidence: number }>;  // only if multi-class head trained
  vocalizingCount?: number;          // R03: generally NOT evaluable; omit unless eval supports
  vocalizingCountConfidence?: number;
  spawnCount: number;                // 0 if !presence; else min(cap, supportedCount)
  spawnCountBasis: "presence_only" | "count_head" | "capped_fallback";
  honesty: {
    inference: "measured_model_output";
    spawn: "modeled_3d_placement";
    motion: "measured_srkw_dtag";    // always, even when behavior label modeled
    crossSensor: "illustrative";     // hydrophone audio != oo14 tag deployment (R05)
  };
}

/** Per-orca scene instance (BRE owns). */
export interface OrcaSpawnInstance {
  instanceId: string;
  anchor: { lat: number; lng: number };
  sceneOffsetM?: { x: number; z: number };
  motion: {
    driverUrl: "/orca/motion/orca_srkw_oo14_driver.json";  // ALWAYS real SRKW
    clip?: { t0_s: number; t1_s: number; behaviorClass?: 1|2|3|4|5|6|7|8|9;
             selection: "srkw_native_segment"|"srkw_kinematic_match"|"continuous_fallback";
             honesty: "measured"|"modeled" };
    timeScale: number;               // follows BSH playbackRate
  };
  acousticLabel?: { callType?: string; confidence?: number };  // HUD only; MUST NOT affect kinematics
  bodyScale?: number;
}

export interface ReenactmentSpawnRecord {
  classification: AcousticClassificationRecord;
  instances: OrcaSpawnInstance[];    // length MUST === classification.spawnCount
  timelineDurationS: number;
}
```

**Spawn count rules (standin-free):** presence only (v1) -> `presence?1:0`; presence + unresolved multi-call -> 1 + HUD "multiple callers detected (unresolved)"; count head with held-out eval (future) -> `min(N_max, modelCount)` + confidence band; no model -> 0 or 1 continuous SRKW + "behavior: unclassified". **Never** spawn N from invented counts; never load humpback or `orca_dev_track`; never map call type -> depth/fluke/clip without R04 kinematic match.

## Scrub-synced timeline integration (consume BSH playhead)

BRE wiring replaces SalishScene wall clock: `authority.subscribe(({currentTimeS, playbackRate}) => { const t = currentTimeS*playbackRate; for (const orca of pool) orca.controller.update(dtCap, orca.clip ? clipSampleTime(t, clip.t0_s, clip.t1_s, clip.loop) : t, cameraWorldPos); })`. Per-orca pose remains `track.sample(t)` (`biologging.ts:83-98`). Clip sampling: `pose = track.sample(((t - t0) % (t1 - t0)) + t0)` - still real SRKW samples.

Rules: BRE must not run its own clock during scrub; `dt` capped `Math.min(dt, 1/30)`; scrub-while-paused still updates pose from `currentTimeS`; slow-mo lowers `playbackRate`. **Open discrepancy (R04 Q7):** manifest `sample_rate_hz: 5` vs `driver_stats.out_rate_hz: 25` - O0 must pick canonical rate. Module placement: `web/lib/scene/reenactment/` + `web/lib/scene/orca/motion/clips/`.

## Perf budget (estimated ms/frame, draw calls, tris, N=1..5; desktop/laptop)

Budgets: 60 fps desktop 16.7 ms; 30 fps laptop 33.3 ms. Baseline twin: opaque render U; pre-pass + main ~2U; tiles+water dominate U; orca incremental.

Per-orca (near LOD, estimated unless noted): body ~3,100 tris; accessories ~1,500 tris; total ~4,600; draw calls 7 (near) / ~3 (far); CPU OPHYS <0.1 ms; CPU `track.sample` <0.01 ms; GPU skinning+draw ~0.10-0.20 ms (1080p). Depth pre-pass multiplier: each near orca ~7 draws x 2 passes ~14 submissions.

| N | Extra draw calls (near, both passes) | Extra tris (near) | CPU increment (est) | GPU increment (est) |
|---|--------------------------------------|-------------------|---------------------|---------------------|
| 1 | 0 (already mounted) | 0 | 0 | 0 |
| 2 | +14 | +~4,600 | +<0.1 ms | +~0.10-0.20 ms |
| 3 | +28 | +~9,200 | +<0.2 ms | +~0.20-0.40 ms |
| 4 | +42 | +~13,800 | +<0.3 ms | +~0.30-0.60 ms |
| 5 | +56 | +~18,400 | +<0.4 ms | +~0.40-0.80 ms |

BSH HUD add (R06, est): +0.3-1.5 ms/frame desktop, budget separately.

| Config | N | Orca increment | Fits budget? |
|--------|---|----------------|--------------|
| Desktop 60 fps | <=5 near | ~0.5-1.0 ms GPU + <0.5 ms CPU | Yes (estimated) |
| Laptop 30 fps | <=3 near | ~0.3-0.6 ms GPU | Yes (estimated) |
| Laptop 30 fps | 5 near all visible | ~0.8 ms GPU + HUD | Marginal - rely on far LOD + cap N_max=3 |

**No third full render:** confirmed.

## Recommendations with cost + standin-free fallback

1. Ship N `OrcaController` instances, not `InstancedMesh` (low refactor + shared geometry cache).
2. Cap `N_max = 3` for laptop/demo until count head is eval-validated. Fallback: `spawnCount = presence?1:0`.
3. Shared `loadOrcaMesh` + one `makeOrcaMaterial` per scene (est. -50-100 ms load per extra orca).
4. Wire BSH authority before multi-orca - scrub sync is correctness-critical (~100 LOC `reenactment/TimelineDriver.ts`).
5. Per-instance R04 clip optional - continuous SRKW driver at scrub `t` when no kinematic match.
6. Keep acoustic labels HUD-only (badges/colors from `callTypes[]`; motion unchanged).
7. Far-LOD enhancement (optional): hide eye meshes at far to drop 2 draws/instance.
8. **Standin-free fallback ladder:** no BAM -> 1 orca continuous SRKW, no spawn record; presence only -> 0/1 orca at station; multi-call unresolved -> 1 + caveat; no R04 clip -> full driver; never `orca_dev_track` or humpback bin in demo.

## Open questions for O0

1. `N_max` for demo: 3 vs 5 given laptop budget + unresolved count head?
2. Spawn count policy: presence-only 0/1 until count eval exists, or "multiple callers (unresolved)" with spawnCount=1?
3. Anchor layout: single station lat/lng + metre offsets vs distinct projected lat/lng per instance?
4. Canonical driver sample rate: reconcile `sample_rate_hz: 5` vs `driver_stats.out_rate_hz: 25` (R04 Q7).
5. Clip API: single active clip vs playlist keyed to BSH segment boundaries?
6. Cross-sensor honesty string for hydrophone audio + oo14 DTAG motion (R05 Q1)?
7. Shared material vs per-orca material; one env update path on `scene.environment` change?
8. Far LOD: hide eyes at far (visual acceptance needed)?
9. Geometry cache ownership: extend `loadOrcaMesh` vs new `OrcaAssetPool`?
10. Classification record persistence: store BAM output JSON alongside clip in box vs ephemeral per session?

## Sources

**Orca runtime:** `web/lib/scene/orca/{OrcaController.ts,rig/OrcaRig.ts,motion/biologging.ts,loadOrcaMesh.ts,materials/orcaMaterial.ts,physics/secondaryDynamics.ts,eyes/orcaEyes.ts,mouth/orcaMouth.ts,physics/OPHYS-R_dynamics.md,materials/OMAT-R_shading.md}`, `web/public/orca/motion/{orca_srkw_oo14_driver.json,orca_dev_track.json}`
**Scene integration:** `web/app/components/scene/SalishScene.tsx`, `web/app/(sandbox)/orca/OrcaSandboxScene.tsx`, `web/lib/sceneIntent.ts`, `web/lib/scene/water2/depthWater.ts`, `web/lib/scene/wfx/realWfxEnv.ts`, `web/lib/scene/tiles/{useTilesLayer.ts,WIRING-tiles-layer.md}`, `web/app/(sandbox)/water/WaterSandboxScene.tsx`
**BSW program/research:** `BSW-REENACTMENT_CHARTER.md`, `BSW-ACOUSTIC-ML_CHARTER.md`, `research/BSW-R0{3,4,5,6}_*.md`
**Mesh/perf:** `.cca/catalogue/O0/20260628_orca-biologging-twin/findings/SYNTHESIS_orca.md`, `infra/orca/mesh/OM-R_candidates.md`, `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/research/RP1_load_perf.md`, `.cca/catalogue/O0/20260628_water-fx/research/WFX-R08_underwater_volumetrics.md`
