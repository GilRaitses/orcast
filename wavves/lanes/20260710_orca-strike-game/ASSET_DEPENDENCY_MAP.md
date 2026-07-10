# Orca Strike — asset and state dependency map

**Lane:** `wavves/lanes/20260710_orca-strike-game`  
**Authority:** Builder agents MUST read this before editing. No guessing paths.

## 1. Route shell (standalone game)

| Asset | Path | Role | State deps |
|-------|------|------|------------|
| Game page | `web/app/(game)/orca-strike/page.tsx` | Entry | — |
| Game layout | `web/app/(game)/orca-strike/layout.tsx` | Fullscreen, no site nav | — |
| Host | `web/app/(game)/orca-strike/OrcaStrikeHost.tsx` | Canvas mount, loading gate | tileset ready |
| Scene hub | `web/app/(game)/orca-strike/OrcaStrikeScene.tsx` | **Single integration file** | pilot FSM, match, scoring |
| Lobby UI | `web/app/(game)/orca-strike/lobby/` (new) | Orca pick, map spawn, room code | island defs |
| HUD | `web/app/(game)/orca-strike/hud/` (new) | Score, timer, breach meter | match state |
| Mobile overlay | `web/app/(game)/orca-strike/MobileControlsOverlay.tsx` | Touch breach/blowhole/sonar | control map |

**Migration note:** Move from `(sandbox)/orca-strike/` → `(game)/orca-strike/` in
STRIKE-W4. Until then, sandbox path remains live; game layout is net-new.

**Live sandbox paths (W1a verified):** `SeaSurface.tsx`, `SceneAtmosphere.tsx`,
`SonarContextMap.tsx`, `orcaStrikeTerrainStyle.ts`, `orcaStrikeInput.ts`
(superseded by W2 `controls.ts`), `MobileControlsOverlay.tsx` — all under
`web/app/(sandbox)/orca-strike/` today.

## 2. Control and pilot stack

| Asset | Path | Role | Locked? |
|-------|------|------|---------|
| HUNT input | `web/lib/scene/orcaPilot/input.ts` | WASD baseline | **LOCKED** |
| Strike controls | `web/lib/scene/orcaStrike/controls.ts` (new) | Q/E/A/D/S/W, Space/B/O → pilot | STRIKE |
| Strike input adapter | `web/lib/scene/orcaStrike/inputAdapter.ts` (new) | Maps to `OrcaPilotInput` | STRIKE |
| Dead reckoning | `web/lib/scene/orcaPilot/deadReckoning.ts` | depth, pitch, speed | editable |
| Chase camera | `web/lib/scene/orcaPilot/chaseCamera.ts` | follow + lag | editable |
| Pilot track | `web/lib/scene/orcaPilot/PilotTrack.ts` | DTAG clip driver | reuse |
| Mobile pilot | `web/lib/scene/orcaPilot/mobileInput.ts` | tilt (+ `isMobilePilot.ts`, `deviceTilt.ts`, `mergeInput.ts`) | extend |

### Control → pilot field mapping (locked)

```
Q     → dive intent (depth rate +)
E     → surface intent (depth rate −)
W     → forward thrust
S     → reverse thrust
A     → roll left (body roll DOF, not yaw)
D     → roll right
Space → breach charge (mash accumulator)
B     → blowhole charge (tap rate)
O     → hydrophone sonar emit
F     → radar ping (HUD context map fill)
1–9   → teleport to blip index
```

## 3. Articulation state machine (DTAG-derived rig)

| Asset | Path | Role |
|-------|------|------|
| Rig definition | `web/lib/scene/orca/rig/OrcaRig.ts` | bones: root, spine, head, jaw, caudal[5], pectoral |
| Biologging driver | `web/lib/scene/orca/motion/biologging.ts` | `driveOrca()` — yaw/pitch/roll/depth/fluke |
| Secondary dynamics | `web/lib/scene/orca/physics/secondaryDynamics.ts` | spine bank, caudal follow (OPHYS) |
| DTAG motion clip | `web/public/orca/motion/orca_srkw_oo14_driver.{json,bin}` | channel source |
| GLB mesh | `web/public/orca/orca.glb` | skinned mesh |
| Pilot FSM | `web/lib/scene/orcaStrike/pilotStateMachine.ts` (new) | mode → rig blend weights |

### Pilot modes → rig articulation (spec for W2)

| Mode | Enter | Rig behavior | DTAG channels emphasized |
|------|-------|--------------|--------------------------|
| `idle` | no thrust 2s | neutral hover, slow caudal | depth hold |
| `swim` | W/S thrust | full `driveOrca` + secondaryDynamics | pitch, yaw, fluke |
| `dive` | Q held | nose-down pitch cap, pectoral tuck | pitch, depth |
| `surface` | E held | nose-up, blowhole prep blend | pitch, depth |
| `roll_left` | A held | roll DOF ±90° cap, reduced forward | roll |
| `roll_right` | D held | same | roll |
| `boost` | W double-tap (optional W3) | fluke amp, speed cap | fluke, pitch |
| `breach_charge` | Space mash | spine arch, fluke load | pitch, fluke (anticipation) |
| `breach_air` | velocity > surface + charge | full extension, trick slots | roll, pitch (air) |
| `breach_land` | water re-entry | splash VFX trigger, replay buffer | pitch damp |
| `blowhole_charge` | B mash rate | head vent angle, jaw closed | head pitch |
| `blowhole_squirt` | charge threshold | particle arc, audio puff | head |

**Integration rule:** `OrcaStrikeScene` calls
`pilotStateMachine.tick(dt, controls, pilotState)` then
`driveOrca(rig, blendedMotion)` — never call `driveOrca` without FSM output in
STRIKE builds.

## 4. Materials, shaders, environment

| Asset | Path | Role | State deps |
|-------|------|------|------------|
| Orca material | `web/lib/scene/orca/materials/orcaMaterial.ts` | PBR skin, B&W readable | underwater fog |
| WFX env | `web/lib/scene/orca/materials/wfxEnv.ts` | metric absorption (`makeSandboxWfxEnv` via `orca/index.ts`) | depth |
| Sea surface | `web/app/(game)/orca-strike/SeaSurface.tsx` | transparent water plane | camera above/below |
| Atmosphere | `web/app/(game)/orca-strike/SceneAtmosphere.tsx` | sky/fog, land vs sea | y=0 horizon |
| Terrain style | `web/app/(game)/orca-strike/orcaStrikeTerrainStyle.ts` | green land, teal seabed | tileset y |
| Tileset | `https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json` | bathymetry + islands | `TILESET_METRIC_DIAMETER_UNITS` |
| Metric fit | `OrcaStrikeScene.tsx` constant | worldUnitsPerMeter = 1 (HUNT lock) | — |

## 5. Camera choreography

| Asset | Path | Mode | Trigger |
|-------|------|------|---------|
| Chase cam | `web/lib/scene/orcaPilot/chaseCamera.ts` | default follow | swim/dive/roll |
| Breach cam | `web/lib/scene/orcaStrike/cameras/breachCamera.ts` (new) | low angle, widen FOV | `breach_air` |
| Replay cam | `web/lib/scene/orcaStrike/cameras/replayCamera.ts` (new) | orbit slow-mo | post-landing 3s |
| Director (forbidden) | `web/lib/scene/camera/director.ts` | workbench only | **do not import** |

Replay buffer: ring buffer of `{t, position, rotation, mode}` 5s @ 30Hz in
`web/lib/scene/orcaStrike/replayBuffer.ts` (new).

## 6. Sonar and hydrophone audio

| Asset | Path | Role | Key |
|-------|------|------|-----|
| Radar targets | `web/lib/scene/sonar/radarTargets.ts` | blip list | F ping |
| Sonar ping | `web/lib/scene/sonar/ping.ts` | context map fill | F |
| Floo teleport | `web/lib/scene/sonar/teleport.ts` | instant move to blip | 1–9 |
| Context map HUD | `web/app/(game)/orca-strike/SonarContextMap.tsx` | 2D minimap | blips |
| Hydro slice audio | `web/public/hydrophone/slice/orcasound_lab_20210825_srkw.m4a` | **O key sample** | **gitignored** (`slice/.gitignore`); fetch via `slice/PROVENANCE.md` / `modeling/acoustic/fetch_orcasound_clip.py` |
| Classifications | `web/public/hydrophone/slice/classification.json` | pick clip offset by label | O sonar |
| Hydro station rig | `web/lib/scene/hydrophone/` | reference only | do not mount in game |
| Strike sonar | `web/lib/scene/orcaStrike/hydrophoneSonar.ts` (new) | play annotation slice + visual pulse | O |

**O key behavior (locked):** On press, play a short classified call from
`classification.json` (default: `SRKW` contact class), emit expanding sonar
ring in world space, add discovery points if new blip revealed.

## 7. Boats, kayaks, scoring

| Asset | Path | Role |
|-------|------|------|
| Boat spawn | `web/lib/scene/boats/spawnBoats.ts` + `spawnKayaks.ts` | toy boats + kayaks |
| Collision | `web/lib/scene/boats/collision.ts` | ram detect (boats only; kayaks separate hitboxes in W3) |
| Sink | `web/lib/scene/boats/sinkAnimation.ts` | `advanceSink`, `sinkTransform` |
| Boat marker | `web/lib/scene/boats/BoatMarker.tsx` | hull ~2.8×0.95 m, deck ~1.18 m |
| Kayak marker | `web/lib/scene/boats/KayakMarker.tsx` | capsule ~1.5 m, r=0.22 m |
| Kayak entity | `web/lib/scene/boats/KayakEntity.ts` | no `collisionRadius` (scoring hitboxes in W3) |
| Scoring | `web/lib/scene/orcaStrike/scoring.ts` (new) | point table |
| Match | `web/lib/scene/orcaStrike/match.ts` (new) | timer, win/lose |

### Score table (locked defaults)

| Event | Points | Notes |
|-------|--------|-------|
| Breach over kayak | 500 | aerial overlap AABB |
| Blowhole hit kayak | 300 | squirt cone overlap |
| Ram sink boat | 200 | HUNT carry-over |
| Land on boat deck | **round win** | team +1000 |
| O sonar new blip | 50 | once per blip |
| Trick in air (per slot) | 100–400 | mash combo |

## 8. Breach and blowhole VFX (new)

| Asset | Path | Trigger |
|-------|------|---------|
| Breach particles | `web/lib/scene/orcaStrike/vfx/breachSplash.ts` | water exit/entry |
| Blowhole spray | `web/lib/scene/orcaStrike/vfx/blowholeSpray.ts` | squirt |
| Trick indicators | `web/app/(game)/orca-strike/hud/TrickCombo.tsx` | air mash |

## 9. Island maps and spawn picker

| Asset | Path | Role |
|-------|------|------|
| Island defs | `web/lib/scene/orcaStrike/islands/definitions.ts` (new) | named sub-regions of tileset bounds |
| Island maps | `web/lib/scene/orcaStrike/islands/maps.ts` (new) | context-map crop per island |
| Spawn picker | `web/app/(game)/orca-strike/lobby/SpawnPicker.tsx` (new) | click map → lat/lon → world xyz |

**Preflight islands (locked v1 set):**

1. `san-juan-core` — default HUNT spawn region  
2. `haro-strait` — west channel  
3. `puget-approach` — east extent  

Each def: `{ id, label, bounds: [west,south,east,north], defaultDepthM, thumb }`.

## 10. Multiplayer (STRIKE-W5 only)

| Asset | Path | Role |
|-------|------|------|
| Room protocol | `web/lib/scene/orcaStrike/net/protocol.ts` (new) | room code, join, state sync |
| Room client | `web/lib/scene/orcaStrike/net/client.ts` (new) | WebSocket |
| Remote orcas | `web/lib/scene/orcaStrike/net/RemoteOrca.tsx` (new) | interpolated ghosts |

Do not start W5 until `findings/STRIKE-W1e-multiplayer.md` has O0 approval.

## Deploy and verify

| Item | Value |
|------|-------|
| Primary ship target | **Bash.tv** (standalone game build) |
| Dev mirror (optional) | EC2 `i-04a649f91274e9fce`, port 3010, `orca-strike.aimez.ai` |
| Visual verify | breach replay, spawn picker, score HUD screenshots |

## 12. HUNT locks still in force

- `worldUnitsPerMeter: 1` — `HUNT-movement-scale.md`
- No OrbitControls — `HUNT-orbit-coexistence.md`
- Fixed 0–25 m depth band — `HUNT-bathy-fidelity.md`
- `orcaPilot/input.ts` untouched — remap in `orcaStrike/` only

## 13. File ownership matrix (builder agents)

| Agent domain | May create/edit | Must not edit |
|--------------|-----------------|---------------|
| Controls/FSM | `orcaStrike/controls*`, `pilotStateMachine.ts` | `orcaPilot/input.ts` |
| Scene INT | `OrcaStrikeScene.tsx` only | SalishScene, workbench |
| Articulation | `orcaStrike/pilotStateMachine.ts`, tune `deadReckoning.ts` | `OrcaRig.ts` bone list |
| Audio sonar | `hydrophoneSonar.ts` | hydrophone station scene |
| UI/lobby | `(game)/orca-strike/lobby/**`, `hud/**` | root `layout.tsx` nav |
| Net | `orcaStrike/net/**` | — (W5 gated) |
