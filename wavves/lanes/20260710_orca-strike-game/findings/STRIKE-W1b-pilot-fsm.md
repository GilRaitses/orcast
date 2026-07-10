# STRIKE-W1b — pilot mode state machine

**Lane:** `wavves/lanes/20260710_orca-strike-game`  
**Inputs:** `decisions/STRIKE-controls.md`, HUNT `deadReckoning.ts`, sandbox `OrcaStrikeScene.tsx`  
**Deliverable owner:** W3a `pilotStateMachine.ts`

## Purpose

Replace HUNT's implicit single-mode swim with an explicit `PilotMode` graph that
feeds `OrcaPilotInput` adaptation, depth integration overrides, and rig blend
weights before `driveOrca()` runs inside `OrcaController.update()`.

## Mode set (locked)

```typescript
export type PilotMode =
  | 'idle'
  | 'swim'
  | 'dive'
  | 'surface'
  | 'roll_left'
  | 'roll_right'
  | 'boost'
  | 'breach_charge'
  | 'breach_air'
  | 'breach_land'
  | 'blowhole_charge'
  | 'blowhole_squirt';
```

## State variables (FSM internal)

| Variable | Type | Role |
|----------|------|------|
| `mode` | `PilotMode` | Current mode |
| `modeTimeS` | number | Time since last transition |
| `idleTimerS` | number | Thrust-off accumulator for idle entry |
| `breachCharge` | 0..1 | Space mash accumulator |
| `blowholeCharge` | 0..1 | B tap-rate accumulator |
| `airTimeS` | number | Time since surface exit (breach_air) |
| `trickSlots` | bitmask | Air trick flags (W1d) |
| `lastWDownS` | number | Double-tap boost detection |
| `depthRateMps` | number | Q/E commanded depth rate (overrides pitch dive) |
| `bodyRollTargetRad` | number | A/D roll target, ±π/2 cap |
| `prevDepthM` | number | For breach velocity detection |

## Input contract (`StrikeControls`)

Produced by `orcaStrike/controls.ts`, consumed by FSM (not raw keyboard):

| Field | Source key | Semantics |
|-------|------------|-----------|
| `forward` | W | Forward thrust |
| `reverse` | S | Reverse thrust (not dive) |
| `dive` | Q held | Depth rate + |
| `surface` | E held | Depth rate − |
| `rollLeft` | A held | Body roll left |
| `rollRight` | D held | Body roll right |
| `breachMash` | Space edge/hold | Increment breach charge |
| `blowholeTap` | B edge | Increment blowhole charge |
| `sonarEmit` | O edge | Hydrophone sonar (scene side effect) |
| `radarPing` | F edge | HUNT radar (scene) |
| `yawDelta`, `pitchDelta` | mouse / tilt | Look (swim modes only) |
| `boost` | Shift OR W double-tap | Speed cap boost |

## Transition table

Priority column: lower number wins when multiple guards fire same frame.

| From | Event / guard | To | Priority | Actions on entry |
|------|---------------|-----|----------|------------------|
| `*` | `depthM <= 0.05` AND `mode === breach_air` | `breach_land` | 1 | Start splash VFX, push replay snapshot, start 3s replay cam |
| `*` | `depthM <= 0.05` AND vertical vel > 2 m/s AND `breachCharge >= 0.35` | `breach_air` | 2 | Zero charge partial, apply launch impulse, widen FOV |
| `breach_land` | `modeTimeS >= 0.6` | `swim` or `idle` | 3 | Restore chase cam |
| `blowhole_squirt` | `modeTimeS >= 0.45` | `swim` or `idle` | 3 | — |
| `*` | `blowholeTap` AND `blowholeCharge >= 1` | `blowhole_squirt` | 4 | Fire cone VFX, score test, reset charge |
| `*` | `breachMash` AND `depthM < 3` AND `mode ∉ {breach_air, breach_land}` | `breach_charge` | 5 | — |
| `breach_charge` | launch guard (above) | `breach_air` | 2 | — |
| `breach_charge` | `!breachMash` AND `breachCharge < 0.1` for 0.4s | `swim` | 6 | Decay charge |
| `*` | `rollLeft` XOR `rollRight` AND `mode ∉ {breach_air, breach_land, blowhole_*}` | `roll_left` / `roll_right` | 7 | Zero yaw assist in adapter |
| `roll_*` | `!rollLeft && !rollRight` | `swim` or `idle` | 8 | — |
| `*` | `dive` AND not in breach/blowhole | `dive` | 9 | `depthRateMps = +2.5` |
| `*` | `surface` AND not in breach/blowhole | `surface` | 9 | `depthRateMps = -2.5` |
| `dive`/`surface` | key released | `swim` or `idle` | 10 | `depthRateMps = 0` |
| `*` | `forward \|\| reverse` AND not in special modes | `swim` | 11 | Reset idle timer |
| `*` | `boost` AND `forward` | `boost` | 12 | Fluke amp cap 1.0 |
| `boost` | `!boost` OR `!forward` | `swim` | 13 | — |
| `swim`/`idle`/… | no thrust 2s continuous | `idle` | 14 | Reduce fluke amp target 0.15 |
| `idle` | any thrust or Q/E/A/D | `swim`/`dive`/… | 15 | — |

Modes not listed as "from" remain in mode until a higher-priority row fires.

## Entry / exit conditions (detail)

### idle
- **Enter:** no forward/reverse/dive/surface/roll for `idleTimerS >= 2`
- **Exit:** any movement input
- **Motion:** speed decays via dead reckoning; depth holds; fluke amp → 0.15

### swim
- **Enter:** default locomotion; W/S thrust
- **Exit:** dive, surface, roll, boost, breach_charge, blowhole_charge
- **Motion:** full dead reckoning with mouse yaw; S is reverse (not pitch dive)

### dive / surface
- **Enter:** Q or E held
- **Exit:** key release
- **Motion:** `depthM` integrates at ±2.5 m/s independent of pitch; pitch capped nose-down/up ±25° cosmetic

### roll_left / roll_right
- **Enter:** A or D held (mutually exclusive; last pressed wins tie)
- **Exit:** key release
- **Motion:** forward speed ×0.6; **no yaw assist** from A/D (`left`/`right` forced false in adapter); `bodyRollTargetRad` slews ±90°

### boost
- **Enter:** Shift+W OR W double-tap within 0.28s
- **Exit:** boost key up or W released
- **Motion:** `BOOST_SPEED_MPS` (5.5) from deadReckoning

### breach_charge
- **Enter:** Space mash while submerged (`depthM >= 0.5`)
- **Exit:** launch OR charge decay
- **Motion:** forward speed ×0.3; pitch arch +15°; fluke amp loads to min(charge, 0.8)

### breach_air
- **Enter:** upward velocity > 2 m/s at surface with charge ≥ 0.35
- **Exit:** re-entry (`depthM <= 0.05`)
- **Motion:** ballistic arc (gravity −9.8 m/s² on vertical world Y); roll/pitch free for tricks; no player depth control

### breach_land
- **Enter:** water re-entry from `breach_air`
- **Exit:** 0.6s timer
- **Motion:** pitch damp; replay buffer playback trigger

### blowhole_charge / blowhole_squirt
- **Enter charge:** B taps increase charge at 0.22 per tap, decay 0.15/s
- **Enter squirt:** charge ≥ 1 at surface (`depthM <= 1`)
- **Exit squirt:** 0.45s timer
- **Motion:** head vent pitch; jaw closed; forward speed 0

## Input conflict priority (same frame)

When multiple inputs are active, apply in this order:

1. **Phase locks:** `breach_air`, `breach_land`, `blowhole_squirt` ignore locomotion except tricks/mash
2. **Blowhole squirt** beats breach charge if charge threshold met at surface
3. **Breach launch** beats roll/dive/surface if surface velocity guard passes
4. **Roll (A/D)** beats mouse yaw assist; adapter zeros `left`/`right` for deadReckoning turn assist
5. **Q/E depth** beats mouse pitch for depth integration (pitch becomes cosmetic only)
6. **S** is reverse thrust only (STRIKE lock); never dive
7. **W** forward beats idle timer reset
8. **Mouse/tilt** yaw always applies except during roll modes (roll drives body roll instead)

## Adapter mapping to `OrcaPilotInput`

`inputAdapter.ts` converts FSM output + raw sampler into the locked HUNT struct:

```typescript
// Pseudocode — do not edit input.ts
function toOrcaPilotInput(raw: OrcaPilotInput, ctrl: StrikeControls, fsm: PilotFsmOutput): OrcaPilotInput {
  return {
    forward: ctrl.forward && fsm.mode !== 'blowhole_squirt',
    back: ctrl.reverse && !fsm.inBreachPhase,
    left: false,   // STRIKE: A is roll, not turn assist
    right: false,  // STRIKE: D is roll, not turn assist
    boost: ctrl.boost || fsm.mode === 'boost',
    yawDelta: fsm.mode.startsWith('roll_') ? 0 : raw.yawDelta,
    pitchDelta: fsm.usePitchForDepth ? raw.pitchDelta : 0,
    pointerLocked: raw.pointerLocked,
  };
}
```

Depth from Q/E is applied **after** `pilot.update()` by writing into `pose.depthM`
on the pilot track OR by a small `applyDepthRate(fsm.depthRateMps, dt)` hook in
`OrcaStrikeScene` before `controller.update()`. Do not change `input.ts`.

Roll from A/D merges into `pose.roll` after dead reckoning, replacing the bank
from turn rate when `mode.startsWith('roll_')`.

## Integration point in OrcaStrikeScene

Current frame order (`OrcaStrikeScene.tsx` useFrame ~349–474):

```
1. sampler.getInput() + merge mobile
2. applyOrcaStrikeDepthInput()  ← REMOVE at W4; replaced by controls+adapter
3. teleport beat / pilot.update(input)  ← pilot XZ integration
4. controller.update() → driveOrca + secondaryDynamics
5. boats collision, sonar, chaseCam
```

STRIKE frame order (W3/W4 convergence):

```
1. rawInput = merge(desktop, mobile)
2. strikeControls = controls.tick(rawInput, keyboardEdges)
3. fsmOut = pilotStateMachine.tick(dt, strikeControls, pilot.track.sample(0))
4. adapted = inputAdapter.toOrcaPilotInput(rawInput, strikeControls, fsmOut)
5. if (!teleportBeat.isActive()) pilot.update(adapted, dt, root)
6. applyFsmMotionOverrides(pilot.pose, fsmOut)  // depth rate, roll, breach arc
7. controller.update(dt, elapsed, camera)       // driveOrca uses overridden pose
8. applyFsmRigLayers(controller.rig, fsmOut)    // head/pectoral/blowhole overlays
9. scoring.match.tick(...); replayBuffer.record(...)
10. camera = selectCamera(fsmOut.mode)           // chase | breach | replay
11. boats/kayaks collision + sonar (unchanged order)
```

Single integration hub rule preserved: only `OrcaStrikeScene.tsx` wires FSM,
scoring, cameras, and HUNT modules.

## HUNT compatibility notes

| HUNT behavior | STRIKE change |
|---------------|---------------|
| A/D turn assist (`deadReckoning.ts:147-149`) | Disabled via adapter (`left`/`right` false) |
| S reverse | Preserved (STRIKE lock) |
| Space climb (`orcaStrikeInput.ts`) | Removed; Space → breach mash |
| Shift boost | Preserved; optional W double-tap adds `boost` mode |
| Pitch-driven depth | Replaced by Q/E in dive/surface modes |
| Mouse yaw | Preserved in swim/dive/surface/boost |

## W2/W3 dependencies

- W2e: `controls.ts` edge detection for Space/B/O/Q/E
- W3a: `pilotStateMachine.ts` pure module
- W3c/d: breach/blowhole guards and charge vars
- W2d: replay buffer snapshot on `breach_land` entry
