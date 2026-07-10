# STRIKE-W1d — breach, blowhole, scoring, replay spec

**Lane:** `wavves/lanes/20260710_orca-strike-game`  
**Locked defaults:** `ASSET_DEPENDENCY_MAP.md` §7, `decisions/STRIKE-controls.md`

## Match timer flow

```
lobby (orca pick + island spawn)
  → countdown 3s
  → round_active (default 180s)
  → round_end (timer zero OR deck landing win)
  → results overlay 8s
  → lobby rematch or solo restart
```

State machine in `match.ts`:

| Phase | Duration | Notes |
|-------|----------|-------|
| `lobby` | ∞ | Spawn picker, optional room code (W5) |
| `countdown` | 3s | Controls disabled |
| `active` | 180s default | Scoring enabled |
| `replay` | 3s | Optional; runs after breach_land if charge was high |
| `ended` | 8s | Show score breakdown |

Timer HUD: MM:SS, turns red under 30s.

## Score table (locked)

| Event ID | Points | Condition | Once per |
|----------|--------|-----------|----------|
| `breach_over_kayak` | **500** | Orca AABB overlaps kayak AABB while `mode === breach_air` | kayak per round |
| `blowhole_hit_kayak` | **300** | Squirt cone overlaps kayak within 0.45s of squirt start | kayak per round |
| `ram_sink_boat` | **200** | `checkRamCollisions` hit on floating boat (HUNT) | boat |
| `land_on_deck` | **round win** + team +1000 | Orca centroid over boat deck AABB, `depthM <= 0.3`, downward vel | round |
| `sonar_new_blip` | **50** | O-key reveals blip ID not in `discoveredBlips` set | blip per round |
| `trick_t1` / `t2` | **100** each | Barrel roll slot in air | air phase |
| `trick_t3` | **150** | Tail whip mash combo | air phase |
| `trick_t4` | **200** | Sky hook W hold | air phase |

Combo multiplier (optional W3 polish): second trick in same air phase ×1.25,
third ×1.5 (cap 400 per trick before multiplier).

## Breach mash mechanics

### Charge accumulation (`breach_charge` mode)

| Parameter | Value |
|-----------|-------|
| Mash source | Space keydown edges (desktop); rapid tap zone (mobile) |
| Charge per mash | +0.12 |
| Decay rate | −0.08 /s when not mashing |
| Min launch charge | 0.35 |
| Max charge | 1.0 |
| Depth gate | `depthM >= 0.5` to enter charge |
| Speed gate at surface | upward `d(depthM)/dt < −2 m/s` OR vertical world velocity > 2 m/s |

### Launch impulse

On `breach_air` entry:

- Vertical velocity: `vy = 4.5 + charge × 3.5` m/s (world +Y)
- Forward carry: 80% current horizontal speed
- Partial charge consume: `breachCharge *= 0.3`

### Air phase

- Duration: until `depthM <= 0.05` (re-entry)
- Gravity: −9.8 m/s² on world Y (arcade, not full ballistic sim)
- Trick slots: see W1c; scored on first valid input per slot per air phase
- Horizontal control: 40% swim authority (W/A/S/D damped)

### Kayak overlap (breach_over_kayak)

Orca hitbox during `breach_air`:

- AABB centered at orca world position
- Half-extents: **4.0 m (X) × 1.2 m (Y) × 2.0 m (Z)** in world units (= metres)

Kayak hitbox (derived from `KayakMarker.tsx` capsule 1.5 m + padding):

- Half-extents: **1.0 m × 0.6 m × 0.5 m**
- Center: kayak `(x, 0.25, z)`

Overlap test: AABB intersection in XZ plus Y band. Score once per kayak ID per round.

## Blowhole squirt

### Charge (`blowhole_charge`)

| Parameter | Value |
|-----------|-------|
| Tap source | B keydown |
| Charge per tap | +0.22 |
| Decay | −0.15 /s |
| Fire threshold | 1.0 |
| Surface gate | `depthM <= 1.0` |

### Squirt cone (`blowhole_squirt`, 0.45s)

- Origin: orca rostrum + head offset (~1.5 m forward, 1.8 m above root at surface)
- Axis: rostrum forward +30° pitch up
- Half-angle: **18°**
- Range: **12 m**
- Test: kayak centroid within cone OR within 0.8 m of axis segment

Particle arc: `blowholeSpray.ts` stub in W2c.

Audio: short puff (synthetic until hydrophone map extended).

## Boat hitbox rules

### Ram sink (existing HUNT)

From `collision.ts` + `spawnBoats.ts`:

- Circle test XZ: radius **2.2 m** (`DEFAULT_BOAT_COLLISION_RADIUS`)
- Orca test point: `(orcaX, orcaZ)` — consider adding orca radius **2.0 m** in W3 for fairness

### Deck landing (round win)

Boat deck AABB from `BoatMarker.tsx` (cab box ~0.9×0.62 m on hull 2.8 m):

- Deck footprint in XZ: centered on boat, half-extents **1.4 m × 0.5 m**
- Vertical: orca root Y between **0.2 m and 1.4 m** above sea level (`SEA_LEVEL_Y = 0`)
- Heading tolerance: ±60° from boat heading (optional polish)
- Velocity: downward `vy < −0.5 m/s` or just entered from `breach_land`

Landing triggers `match.endRound('deck_win')` immediately.

## Slow-mo replay buffer

File: `web/lib/scene/orcaStrike/replayBuffer.ts` (W2d)

### Recording

| Parameter | Value |
|-----------|-------|
| Duration | **5.0 s** ring buffer |
| Sample rate | **30 Hz** |
| Sample struct | `{ t, position: Vector3, rotation: Euler, mode: PilotMode, charge: number }` |
| Memory | 150 samples × ~48 bytes ≈ 7 KB |

Record every frame in `OrcaStrikeScene` after pose finalize:

```typescript
replayBuffer.push(elapsed, root.position, root.rotation, fsm.mode, fsm.breachCharge);
```

### Playback trigger

- On `breach_land` entry when `breachChargeAtLaunch >= 0.5` OR any trick scored
- Playback duration: **3.0 s** real time
- Time scale: **0.35×** (slow-mo)
- Camera: `replayCamera.ts` orbits 120° around splash point, radius 14 m, height 3 m
- During replay: player input disabled; physics paused

### Fallback

If buffer empty (first 5s of round), skip replay, normal chase cam.

## O-key hydrophone sonar (scoring tie-in)

On O press (`hydrophoneSonar.ts`):

1. Pick highest-confidence SRKW window from `classification.json` (`presence: true`, max `presenceConfidence`) not played recently
2. Play 3s slice from `orcasound_lab_20210825_srkw.m4a` at `tStartS`
3. Emit expanding ring mesh at orca position (world space)
4. If ring reveals new sonar blip ID → `sonar_new_blip` +50

Distinct from F-key radar (HUNT UI fill). Both may coexist.

## Mobile gesture equivalents

| Desktop | Mobile | Implementation |
|---------|--------|----------------|
| W/S | auto-forward / brake hold | Existing `MobileControlsOverlay` boost/back |
| Q/E dive/surface | tilt pitch beyond 18° threshold | Extend tilt mapping in `controls.ts` |
| A/D roll | two-finger twist OR on-screen roll buttons | New overlay buttons L/R roll |
| Space breach mash | large "BREACH" tap zone; each tap = mash | `PointerEvent` counter, haptic optional |
| B blowhole | "SPOUT" tap button | Edge counter |
| O sonar | "CALL" button (distinct from F sonar) | New button; plays audio |
| F radar | existing Sonar button | Unchanged |
| 1-9 warp | tap blip list | Unchanged |
| Shift boost | existing Boost hold | Unchanged |
| Mouse look | tilt steer | Unchanged |

Mobile overlay additions in W3f: breach zone (bottom-right), blowhole (top-right),
O-call (near sonar).

## scoring.ts event API (sketch)

```typescript
type ScoreEvent =
  | { type: 'breach_over_kayak'; kayakId: string }
  | { type: 'blowhole_hit_kayak'; kayakId: string }
  | { type: 'ram_sink'; boatId: string }
  | { type: 'deck_win'; boatId: string }
  | { type: 'sonar_blip'; targetId: string }
  | { type: 'trick'; slot: 't1'|'t2'|'t3'|'t4' };

function applyScore(state: MatchState, event: ScoreEvent): MatchState;
```

Idempotency via `scoredKeys: Set<string>` per round.

## Dependencies

- W2d: `replayBuffer.ts` stub with push/getWindow
- W2c: VFX stubs for breach splash and blowhole spray
- W3b: `scoring.ts`, `match.ts`
- W3c/d: collision hooks in scene useFrame after pose update
- W2b: hydrophone audio load path for O-key
