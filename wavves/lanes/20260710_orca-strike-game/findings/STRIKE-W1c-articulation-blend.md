# STRIKE-W1c — articulation blend map (PilotMode → OrcaRig DOF)

**Lane:** `wavves/lanes/20260710_orca-strike-game`  
**Sources:** `OrcaRig.ts`, `biologging.ts`, `orca_srkw_oo14_driver.json`, `secondaryDynamics.ts`, `OrcaController.ts`

## DTAG channel reference (locked)

From `biologging.ts` header and `orca_srkw_oo14_driver.json` `channels[]`:

| Index | Name | Unit | Rig DOF | `driveOrca` mapping |
|-------|------|------|---------|---------------------|
| 0 | `t_s` | s | — | sample time |
| 1 | `body_yaw_rad` | rad | heading | `setOrientation(pitch, roll, **yaw**)` |
| 2 | `body_pitch_rad` | rad | nose up + | `setOrientation(**pitch**, roll, yaw)` |
| 3 | `body_roll_rad` | rad | port bank + | `setOrientation(pitch, **roll**, yaw)` |
| 4 | `depth_m` | m +down | world Y | `setDepthPose(**depthM**, wupm)` |
| 5 | `fluke_phase_rad` | rad | caudal beat | `setFluke(**phase**, amp)` |
| 6 | `fluke_amplitude` | 0..1 | stroke power | `setFluke(phase, **amp**)` |

Driver stats (oo14): pitch p95 61.6°, roll p95 133.25°, fluke median 0.183 Hz.
Arcade modes clamp to rig limits (`DEFAULT_LIMITS` in `OrcaRig.ts`).

## Composition order (do not reorder)

Per `OrcaController.update()` and OPHYS-R:

1. **OG** — `driveOrca(rig, blendedPose, wupm)` from FSM output pose
2. **OPHYS** — `setSecondaryFlex`, `setCaudalFollow` from yaw rate + fluke (swim modes)
3. **OMOU** — `setJaw` (foraging proxy; suppressed in blowhole)
4. **OEYE** — gaze (unchanged)
5. **STRIKE overlays** — `setHeadOffset`, `setPectoral` from FSM `rigBlend`

FSM never calls bone methods directly. Scene or a `applyStrikeRigLayers(rig, fsmOut, sec)` helper runs after `controller.update()` step 2.

## RigBlend schema

```typescript
interface RigBlendWeights {
  swim: number;      // 1 = full driveOrca pose + secondaryDynamics
  roll: number;      // 1 = A/D body roll dominates setOrientation roll
  breach: number;    // 1 = arch/extension pose overlay
  blowhole: number;  // 1 = head vent + jaw clamp
}
interface MotionOverrides extends Partial<OrcaPose> {
  headOffsetYaw?: number;
  headOffsetPitch?: number;
  pectoralL?: number;
  pectoralR?: number;
  jawOpen?: number;
}
```

## Per-mode blend table

Weights are 0..1. Pose overrides additive unless noted.

| Mode | swim | roll | breach | blowhole | Primary channels | DOF calls |
|------|------|------|--------|----------|------------------|-----------|
| `idle` | 0.35 | 0 | 0 | 0 | depth, fluke amp | `driveOrca` low amp; OPHYS damped |
| `swim` | **1.0** | 0 | 0 | 0 | yaw, pitch, depth, fluke | full `driveOrca` + OPHYS |
| `dive` | 0.85 | 0 | 0 | 0 | pitch ↓, depth, fluke | pitch cap −25°; pectoral tuck |
| `surface` | 0.85 | 0 | 0 | 0.15 | pitch ↑, depth | pitch cap +20°; blowhole prep on head |
| `roll_left` | 0.55 | **0.9** | 0 | 0 | roll − | roll target −70°; pitch damp 0.5× |
| `roll_right` | 0.55 | **0.9** | 0 | 0 | roll + | roll target +70° |
| `boost` | **1.0** | 0 | 0 | 0 | fluke amp, pitch | fluke amp min 0.85; OPHYS bank ×1.2 |
| `breach_charge` | 0.4 | 0 | **0.7** | 0 | pitch, fluke | pitch +15° arch; fluke amp → charge |
| `breach_air` | 0.2 | 0.5 | **1.0** | 0 | roll, pitch | roll free ±120°; pitch ±45°; fluke amp 0.3 |
| `breach_land` | 0.5 | 0 | 0.6 | 0 | pitch damp | pitch snap toward 0; fluke splash amp 0.6 |
| `blowhole_charge` | 0.3 | 0 | 0 | **0.8** | head pitch | headOffsetPitch +charge×12° |
| `blowhole_squirt` | 0.2 | 0 | 0 | **1.0** | head | headOffsetPitch +18°; jaw 0 |

## DOF detail by mode

### setOrientation(pitch, roll, yaw)

| Mode | pitch | roll | yaw |
|------|-------|------|-----|
| swim | DTAG + mouse | OPHYS bank from yaw rate | pilot heading |
| dive | lerp(DTAG, −25°, 0.7) | DTAG ×0.3 | pilot heading |
| surface | lerp(DTAG, +15°, 0.6) | DTAG ×0.3 | pilot heading |
| roll_left | DTAG ×0.4 | lerp(DTAG, −70°, rollW) | pilot heading |
| roll_right | DTAG ×0.4 | lerp(DTAG, +70°, rollW) | pilot heading |
| breach_charge | DTAG + 15° arch | DTAG | pilot heading |
| breach_air | trick offset + DTAG×0.2 | trick roll + DTAG×0.2 | pilot heading |
| blowhole_* | DTAG ×0.2 | 0 | pilot heading |

`rollW` = rigBlend.roll (0.9 in roll modes).

### setDepthPose(depthM, wupm)

All modes: FSM-integrated `depthM` from pilot pose. Breach air uses world Y
ballistic override on `controller.root.position.y` while `depthM` derived from
`-y/wupm` for splash detection.

### setFluke(phase, amplitude)

| Mode | phase | amplitude |
|------|-------|-----------|
| idle | integrate 0.15 Hz | 0.15 |
| swim/boost | pilot integrator | speed fraction (boost min 0.85) |
| dive/surface | pilot | ×0.75 |
| roll_* | pilot | ×0.5 |
| breach_charge | pilot + π offset | charge value |
| breach_air | hold launch phase | 0.25–0.35 |
| breach_land | rapid decay | 0.6 → 0.2 over 0.4s |

### setHeadOffset(yaw, pitch)

| Mode | yaw | pitch |
|------|-----|-------|
| default | 0 | 0 |
| surface | 0 | +3° prep |
| blowhole_charge | 0 | +(charge × 12°) capped at `headOffsetMax` (5°) — use 80% of max |
| blowhole_squirt | 0 | +5° (max) |

Note: blowhole vent may require raising `headOffsetMax` in STRIKE-only overlay
clamp to 20° via `Math.min(computed, limits.headOffsetMax * 4)` in strike layer
without editing `OrcaRig.ts` bone limits. W3d should tune visually.

### setPectoral(left, right)

| Mode | left | right |
|------|------|-------|
| dive | +15° tuck | +15° tuck |
| surface | −8° | −8° |
| roll_left | +20° | −10° |
| roll_right | −10° | +20° |
| breach_air | trick-dependent | trick-dependent |
| others | 0 | 0 |

Angles clamped to `limits.pectoralMax` (35°).

### setSecondaryFlex(spineYaw, bankRoll)

Run only when `rigBlend.swim >= 0.5` and mode ∉ `{breach_air, blowhole_squirt}`.

Source: `makeSecondaryDynamics().step(yawRate, flukePhase, flukeAmp, dt)` as today.

| Mode | spine scale | bank scale |
|------|-------------|------------|
| swim | 1.0 | 1.0 |
| boost | 1.1 | 1.2 |
| dive/surface | 0.6 | 0.4 |
| roll_* | 0.2 | 0 (roll replaces bank) |
| idle | 0.3 | 0.3 |

### setCaudalFollow(offsets)

Unchanged from OPHYS output in swim/boost/dive/surface. Zeroed in roll, blowhole,
breach_charge (follow would fight arch pose).

## Trick slots (breach_air, ties to W1d)

Trick input adds to roll/pitch offsets before `setOrientation`:

| Slot | Input | roll Δ | pitch Δ | Points |
|------|-------|--------|---------|--------|
| T1 barrel | mash + A | −45° | 0 | 100 |
| T2 barrel | mash + D | +45° | 0 | 100 |
| T3 tail whip | mash alone | 0 | −30° | 150 |
| T4 sky hook | W hold in air | 0 | +35° | 200 |

Each slot scores once per air phase.

## Sample implementation hook

```typescript
export function applyStrikeRigLayers(
  rig: OrcaRig,
  fsm: PilotFsmOutput,
  sec: SecondaryOutput | null,
): void {
  const { rigBlend, motionOverrides } = fsm;
  if (motionOverrides.headOffsetPitch != null || motionOverrides.headOffsetYaw != null) {
    rig.setHeadOffset(
      motionOverrides.headOffsetYaw ?? 0,
      motionOverrides.headOffsetPitch ?? 0,
    );
  }
  if (motionOverrides.pectoralL != null || motionOverrides.pectoralR != null) {
    rig.setPectoral(motionOverrides.pectoralL ?? 0, motionOverrides.pectoralR ?? 0);
  }
  if (fsm.mode.startsWith('blowhole')) {
    rig.setJaw(0);
  }
  if (sec && rigBlend.swim >= 0.5) {
    rig.setSecondaryFlex(
      sec.spineYaw * rigBlend.swim,
      sec.bankRoll * rigBlend.swim,
    );
    rig.setCaudalFollow(sec.caudalFollow);
  }
}
```

Called from `OrcaStrikeScene` after `controller.update()` when STRIKE FSM is active.

## Visual verify checklist (STRIKE-ACCEPT)

Screenshot pairs: idle vs roll vs breach_charge vs blowhole_squirt. Confirm
pectoral tuck visible in dive, head vent in blowhole, fluke load in breach_charge.
