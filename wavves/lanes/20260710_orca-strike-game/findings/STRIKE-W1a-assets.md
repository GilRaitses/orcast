# STRIKE-W1a — asset map verification

**Lane:** `wavves/lanes/20260710_orca-strike-game`  
**Verified:** 2026-07-10 (live repo walk, not charter hash alone)  
**Authority:** `ASSET_DEPENDENCY_MAP.md`

## Summary

The asset map is structurally correct. All `(new)` STRIKE paths are absent as
expected. HUNT baseline files exist at the documented sandbox paths. Five path
corrections and one filename correction are required in the map before W2 agents
treat it as canonical.

## 1. Route shell

| Map path | Status | Actual path / note |
|----------|--------|-------------------|
| `(game)/orca-strike/page.tsx` | **MISSING (new)** | Not created. Live route is `web/app/(sandbox)/orca-strike/page.tsx` |
| `(game)/orca-strike/layout.tsx` | **MISSING (new)** | W4 deliverable |
| `(game)/orca-strike/OrcaStrikeHost.tsx` | **MISSING (new)** | Live: `web/app/(sandbox)/orca-strike/OrcaStrikeHost.tsx` |
| `(game)/orca-strike/OrcaStrikeScene.tsx` | **MISSING (new)** | Live hub: `web/app/(sandbox)/orca-strike/OrcaStrikeScene.tsx` (49628-byte integration file) |
| `(game)/orca-strike/lobby/**` | **MISSING (new)** | W3f |
| `(game)/orca-strike/hud/**` | **MISSING (new)** | W3/W4 |
| `(game)/orca-strike/MobileControlsOverlay.tsx` | **CONFIRMED (sandbox)** | `web/app/(sandbox)/orca-strike/MobileControlsOverlay.tsx` |
| `(game)/orca-strike/SeaSurface.tsx` | **CONFIRMED (sandbox)** | `web/app/(sandbox)/orca-strike/SeaSurface.tsx` |
| `(game)/orca-strike/SceneAtmosphere.tsx` | **CONFIRMED (sandbox)** | `web/app/(sandbox)/orca-strike/SceneAtmosphere.tsx` |
| `(game)/orca-strike/SonarContextMap.tsx` | **CONFIRMED (sandbox)** | `web/app/(sandbox)/orca-strike/SonarContextMap.tsx` |
| `(game)/orca-strike/orcaStrikeTerrainStyle.ts` | **CONFIRMED (sandbox)** | Present |
| `(game)/orca-strike/orcaStrikeInput.ts` | **CONFIRMED (sandbox, supersede)** | HUNT depth remap; STRIKE-W2 replaces with `orcaStrike/controls.ts` |

Migration note in map is accurate: sandbox remains live until W4.

## 2. Control and pilot stack

| Map path | Status | Note |
|----------|--------|------|
| `web/lib/scene/orcaPilot/input.ts` | **CONFIRMED, LOCKED** | WASD + Shift boost + mouse look only |
| `web/lib/scene/orcaStrike/controls.ts` | **MISSING (new)** | W2e |
| `web/lib/scene/orcaStrike/inputAdapter.ts` | **MISSING (new)** | W2e |
| `web/lib/scene/orcaPilot/deadReckoning.ts` | **CONFIRMED** | Editable; depth via pitch today |
| `web/lib/scene/orcaPilot/chaseCamera.ts` | **CONFIRMED** | Sole camera writer (HUNT lock) |
| `web/lib/scene/orcaPilot/PilotTrack.ts` | **CONFIRMED** | Live pose source for `createOrcaController` |
| `web/lib/scene/orcaPilot/mobile.ts` | **CORRECTION** | File is `web/lib/scene/orcaPilot/mobileInput.ts` (+ `isMobilePilot.ts`, `deviceTilt.ts`, `mergeInput.ts`) |

Supporting orcaPilot files not in map but present: `index.ts`, `WIRING.md`.

## 3. Articulation / rig

| Map path | Status | Note |
|----------|--------|------|
| `web/lib/scene/orca/rig/OrcaRig.ts` | **CONFIRMED** | DOF API: `setOrientation`, `setDepthPose`, `setFluke`, `setJaw`, `setHeadOffset`, `setPectoral`, `setSecondaryFlex`, `setCaudalFollow` |
| `web/lib/scene/orca/motion/biologging.ts` | **CONFIRMED** | `driveOrca()`, 7-channel layout documented in header |
| `web/lib/scene/orca/motion/secondaryDynamics.ts` | **CORRECTION** | Actual path: `web/lib/scene/orca/physics/secondaryDynamics.ts` |
| `web/public/orca/motion/orca_srkw_oo14_driver.{json,bin}` | **CONFIRMED** | bin 1,146,236 bytes; json 40937 samples @ 5 Hz |
| `web/public/orca/orca.glb` | **CONFIRMED** | 486,752 bytes |
| `web/lib/scene/orcaStrike/pilotStateMachine.ts` | **MISSING (new)** | W3a |

## 4. Materials, shaders, environment

| Map path | Status | Note |
|----------|--------|------|
| `web/lib/scene/orca/orcaMaterial.ts` | **CORRECTION** | Actual: `web/lib/scene/orca/materials/orcaMaterial.ts` |
| `web/lib/scene/orca/wfxEnv.ts` | **CORRECTION** | Actual: `web/lib/scene/orca/materials/wfxEnv.ts`; export `makeSandboxWfxEnv` from `web/lib/scene/orca/index.ts` |
| Tileset URL | **CONFIRMED** | `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json` used in `OrcaStrikeScene.tsx:82` |
| `TILESET_METRIC_DIAMETER_UNITS` | **CONFIRMED** | `OrcaStrikeScene.tsx:115`, `PILOT_WORLD_UNITS_PER_METER = 1` at line 123 |

## 5. Camera / replay

| Map path | Status |
|----------|--------|
| `orcaStrike/cameras/breachCamera.ts` | **MISSING (new)** W2/W3 |
| `orcaStrike/cameras/replayCamera.ts` | **MISSING (new)** W2/W3 |
| `orcaStrike/replayBuffer.ts` | **MISSING (new)** W2d |
| `web/lib/scene/camera/director.ts` | **CONFIRMED present, forbidden import** |

## 6. Sonar and hydrophone audio

| Map path | Status | Note |
|----------|--------|------|
| `web/lib/scene/sonar/radarTargets.ts` | **CONFIRMED** | |
| `web/lib/scene/sonar/ping.ts` | **CONFIRMED** | F-key radar fill |
| `web/lib/scene/sonar/teleport.ts` | **CONFIRMED** | Not named in map; used by scene |
| `web/public/hydrophone/slice/classification.json` | **CONFIRMED** | 17,321 bytes; SRKW windows with `tStartS`/`tEndS` |
| `web/public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a` | **GITIGNORED, ON DISK** | 2,204,788 bytes present locally; excluded by `web/public/hydrophone/slice/.gitignore` (`*.m4a`) |
| `web/public/hydrophone/slice/PROVENANCE.md` | **CONFIRMED** | Re-fetch via `modeling/acoustic/fetch_orcasound_clip.py` |
| `web/lib/scene/hydrophone/` | **CONFIRMED (reference only)** | 12 files; station rig, not for game mount |
| `web/lib/scene/orcaStrike/hydrophoneSonar.ts` | **MISSING (new)** | W2b |

**O-key audio blocker status:** Not a W1 hard blocker on this machine (file
present). CI/clean clone must run provenance fetch before STRIKE-ACCEPT O-sonar
check.

## 7. Boats, kayaks, scoring

| Map path | Status | Note |
|----------|--------|------|
| `web/lib/scene/boats/spawn.ts` | **CORRECTION** | Actual: `spawnBoats.ts` + `spawnKayaks.ts` |
| `web/lib/scene/boats/collision.ts` | **CONFIRMED** | Circle test; boats only, not kayaks |
| `web/lib/scene/boats/sink.ts` | **CORRECTION** | Actual: `sinkAnimation.ts`; export `advanceSink`, `sinkTransform` |
| `web/lib/scene/boats/BoatMarker.tsx` | **CONFIRMED** | Hull ~2.8 x 0.95 m, deck top ~1.18 m |
| `web/lib/scene/boats/KayakMarker.tsx` | **CONFIRMED** | Capsule hull ~1.5 m long, radius 0.22 m |
| `web/lib/scene/boats/KayakEntity.ts` | **CONFIRMED** | Explicitly no `collisionRadius` |
| `web/lib/scene/orcaStrike/scoring.ts` | **MISSING (new)** | W3b |
| `web/lib/scene/orcaStrike/match.ts` | **MISSING (new)** | W3b |

## 8–10. VFX, islands, net

All `(new)` paths absent as expected:

- `orcaStrike/vfx/breachSplash.ts`, `blowholeSpray.ts`
- `orcaStrike/islands/definitions.ts`, `maps.ts`
- `orcaStrike/net/protocol.ts`, `client.ts`, `RemoteOrca.tsx`

## 11. Deploy

| Item | Verified |
|------|----------|
| EC2 `i-04a649f91274e9fce` | Documented in waveset; not live-probed in W1 |
| Port 3010 | Documented |
| URL `https://orca-strike.aimez.ai/orca-strike` | Documented target |

## Corrections required in ASSET_DEPENDENCY_MAP.md

Apply before W2 agents treat the map as path authority:

1. `orcaMaterial.ts` → `materials/orcaMaterial.ts`
2. `wfxEnv.ts` → `materials/wfxEnv.ts`
3. `motion/secondaryDynamics.ts` → `physics/secondaryDynamics.ts`
4. `boats/spawn.ts` → `boats/spawnBoats.ts` + `spawnKayaks.ts`
5. `boats/sink.ts` → `boats/sinkAnimation.ts` (`advanceSink`)
6. `orcaPilot/mobile.ts` → `orcaPilot/mobileInput.ts`
7. Add `sonar/teleport.ts` under section 6 (HUNT carry-over)
8. Note hydrophone m4a is gitignored but required at runtime; cite `PROVENANCE.md`

## Net-new inventory (expected absent)

Zero files under `web/lib/scene/orcaStrike/` (Glob empty). Zero files under
`web/app/(game)/`. This matches charter placeholders.
