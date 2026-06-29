# BSW-STATION charter (hydrophone equipment model + station player + camera POV)

- Lane code: **BST** (under family BSW)
- Owner: O0 dispatches; a background sub-orchestrator runs the gated build waves.
- Type: research-first (grounded by BSW-RESEARCH R01/R06/R07/R13); build/integrate/accept gated.
- `repo_state_verified_against`: origin/main `240570e961913fb610c2765a4ef77cace3f216f1`.
- Charter method: `~/.cursor/skills/waveset-orchestration/SKILL.md`. Umbrella: `PROGRAM.md`.

## Intent (operator)
A 3D model that represents close enough what the hydrophone equipment looks like, shown under the
water when a station is chosen; a station player that lets you select things and see it from the POV
of the hydrophone or top-down via an interactive camera-selection object that extends from the LGC.

## Grounding (verified seams)
- Station catalog is REAL and already served: `GET /api/live-hydrophones`
  (`src/aws_backend/routers/read.py` -> `src/aws_backend/sources/orcasound.py`); per-station
  `id/name/lat/lng/status/streamUrl/source/imageUrl`. Catalogs:
  `src/integrations/orcasound_hydrophones_for_orcast.json`, `live_orcasound_feeds.json`
  (slug/bucket/node_name/GeoJSON coords).
- Scene click already emits a hydrophone `SceneIntent` `{id,name,lat,lng,streamUrl}`
  (`web/app/components/scene/SalishScene.tsx`); `AdaptiveExplore.tsx` slots a `hydrophone_signal`
  panel but **drops `streamUrl`**. Marker geometry: `web/lib/scene/markers/buoyMarker.tsx`;
  placement via `projectToScene` + downward raycast (`SurfaceBeacons`/`HydrophoneBeacon`).
- Camera director already exists: `web/lib/scene/camera/director.ts`
  (moveTo/descendTo/followPath/orbit), wired by `IntentDirectorRig` + `OrbitControls`; resting orbit
  + `runPlaceJourney` (`web/lib/journey/controller.ts`). No camera-SELECTION UI exists.
- LGC tokens are unbuilt (`LIQUID_GLASS_CONSOLE_MANIFEST.md`, `20260628_liquid-glass-console/`).

## Locked decisions (do NOT reopen)
- The hydrophone equipment model is **modeled** (a representative cabled-hydrophone / node-on-mooring
  rig), placed at the real station lat/lng on the seabed via `projectToScene` + the raycast depth.
  Label it modeled; it represents, it is not a scanned asset of a specific node unless one is
  license-clear.
- Mesh license first (CC0/CC-BY/permissive), recorded with attribution; else build a simple
  parametric `three` model in-repo (hydrophone element + housing + cable/mooring + surface buoy).
- Bind the already-present `streamUrl` and real Orcasound archived audio (per BSW-R01); do not
  invent a stream. Audio handling is the player's; classification is BAM's; spectrogram is BSH's.
- Camera POV-selection object extends LGC tokens via a **minimal local glass surface** (LGC is
  unbuilt); coordinate token names with O0. Two named POVs minimum: **hydrophone POV** (camera at
  the node looking up/around) and **top-down**; both drive `director.ts`, never bypass it.
- Compute-neutral: the equipment model is low-poly + instanced; POV transitions reuse the director.

## Wave structure
- **BST-BUILD** (gated, net-new): `web/lib/scene/hydrophone/` (model + placement + player binding),
  `web/public/hydrophone/` (mesh/license if external), `web/app/(sandbox)/station/` sandbox; camera
  POV-selection object + LGC-aligned glass control. `tsc`/lint clean; verified on the GPU render host.
- **BST-INTEGRATE** (gated, single editor): land station-select -> underwater model + POV object into
  `SalishScene.tsx`/`AdaptiveExplore.tsx`; serialize vs LGC/CVP/WFX/ORCA/3D-TWIN.
- **BST-ACCEPT** (gated): Read-examined frames - station chosen shows the equipment model underwater
  at the right place/depth; hydrophone-POV and top-down both reachable; glass control legible.

## Acceptance criteria (hard, checkable)
- Selecting a real station places the equipment model at that station's lat/lng on the seabed.
- The camera POV-selection object switches between hydrophone POV and top-down via the director.
- `streamUrl`/archived audio is bound (playable), labeled modeled-vs-measured; frame budget held.

## Escalation
Answers to O0, not the operator. License ambiguity, dependency choice, LGC-token questions,
convergence-file collisions, regressions, or any gated step: pause and return to O0.

## Return contract
Net-new file list + WIRING docs; GPU-host gate frames (Read-examined); the POV/director wiring note;
any open questions (token names, mesh license) for O0.
