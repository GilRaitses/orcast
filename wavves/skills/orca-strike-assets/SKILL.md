---
name: orca-strike-assets
description: Quick-reference asset and state dependency map for Orca Strike (STRIKE lane). Use when you need exact file paths for rig, hydrophone, materials, cameras, boats, or island defs without searching the repo.
---

# Orca Strike Asset Map (quick reference)

Full authority: `wavves/lanes/20260710_orca-strike-game/ASSET_DEPENDENCY_MAP.md`

## Route shell

| What | Path |
|------|------|
| Game page | `web/app/(game)/orca-strike/page.tsx` |
| Standalone layout | `web/app/(game)/orca-strike/layout.tsx` |
| Scene hub | `web/app/(game)/orca-strike/OrcaStrikeScene.tsx` |
| Legacy sandbox | `web/app/(sandbox)/orca-strike/` (migrate in W4) |

## Controls (STRIKE-owned)

| What | Path |
|------|------|
| Control map | `web/lib/scene/orcaStrike/controls.ts` |
| HUNT adapter | `web/lib/scene/orcaStrike/inputAdapter.ts` |
| HUNT input (LOCKED) | `web/lib/scene/orcaPilot/input.ts` |
| Dead reckoning | `web/lib/scene/orcaPilot/deadReckoning.ts` |

## Rig + articulation

| What | Path |
|------|------|
| Bones API | `web/lib/scene/orca/rig/OrcaRig.ts` |
| driveOrca | `web/lib/scene/orca/motion/biologging.ts` |
| Secondary dynamics | `web/lib/scene/orca/physics/secondaryDynamics.ts` |
| Pilot FSM | `web/lib/scene/orcaStrike/pilotStateMachine.ts` |
| GLB | `web/public/orca/orca.glb` |
| DTAG clip | `web/public/orca/motion/orca_srkw_oo14_driver.{json,bin}` |

## Environment

| What | Path |
|------|------|
| Orca material | `web/lib/scene/orca/materials/orcaMaterial.ts` |
| WFX env | `web/lib/scene/orca/materials/wfxEnv.ts` |
| Sea surface | `.../orca-strike/SeaSurface.tsx` |
| Atmosphere | `.../orca-strike/SceneAtmosphere.tsx` |
| Terrain style | `.../orca-strike/orcaStrikeTerrainStyle.ts` |
| Tileset URL | `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json` |

## Camera

| What | Path |
|------|------|
| Chase (default) | `web/lib/scene/orcaPilot/chaseCamera.ts` |
| Breach | `web/lib/scene/orcaStrike/cameras/breachCamera.ts` |
| Replay | `web/lib/scene/orcaStrike/cameras/replayCamera.ts` |
| Forbidden | `web/lib/scene/camera/director.ts` |

## Sonar + hydrophone

| What | Path |
|------|------|
| Radar (F) | `web/lib/scene/sonar/ping.ts` |
| Teleport (1–9) | `web/lib/scene/sonar/teleport.ts` |
| Context map HUD | `.../orca-strike/SonarContextMap.tsx` |
| O-key sonar | `web/lib/scene/orcaStrike/hydrophoneSonar.ts` |
| Audio slice | `web/public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a` (gitignored; PROVENANCE fetch) |
| Classifications | `web/public/hydrophone/slice/classification.json` |

## Boats + scoring

| What | Path |
|------|------|
| Spawn/collision/sink | `web/lib/scene/boats/` |
| Scoring | `web/lib/scene/orcaStrike/scoring.ts` |
| Match timer | `web/lib/scene/orcaStrike/match.ts` |

## Islands + lobby

| What | Path |
|------|------|
| Island defs | `web/lib/scene/orcaStrike/islands/definitions.ts` |
| Map crops | `web/lib/scene/orcaStrike/islands/maps.ts` |
| Spawn picker | `web/app/(game)/orca-strike/lobby/SpawnPicker.tsx` |

## VFX + replay

| What | Path |
|------|------|
| Breach splash | `web/lib/scene/orcaStrike/vfx/breachSplash.ts` |
| Blowhole spray | `web/lib/scene/orcaStrike/vfx/blowholeSpray.ts` |
| Replay buffer | `web/lib/scene/orcaStrike/replayBuffer.ts` |

## Multiplayer (W5 only)

| What | Path |
|------|------|
| Protocol | `web/lib/scene/orcaStrike/net/protocol.ts` |
| Client | `web/lib/scene/orcaStrike/net/client.ts` |
| Remote orca | `web/lib/scene/orcaStrike/net/RemoteOrca.tsx` |

## State dependency chain

```
controls.ts → inputAdapter → deadReckoning → pilotStateMachine
  → driveOrca(rig) + secondaryDynamics
  → chaseCamera | breachCamera | replayCamera
  → scoring.ts ← collision/breach/blowhole hitboxes
  → match.ts (timer, win)
```

## Deploy

- URL: `https://orca-strike.aimez.ai/orca-strike`
- EC2: `i-04a649f91274e9fce`, port `3010`
