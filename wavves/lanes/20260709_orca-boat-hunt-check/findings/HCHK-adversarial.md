# HCHK-W1d — adversarial findings

Lens: adversarial. Hunt for failure modes and happy-path-only assumptions in
the delivered `orcaPilot`/`boats`/`sonar` code and in the `HUNT-INT` plan it
feeds. Read-only. Every finding cites an exact file and line/symbol.

## Active-regression check (per dispatch escalation clause)

No active regression on already-working code. Every HUNT deliverable is a new
file except the single additive, backward-compatible edit to
`web/lib/scene/orca/OrcaController.ts` (verified by `git diff`, lines 39-43 add
an optional `track?` field, lines 74-77 branch on it with
`opts.track ? Promise.resolve(opts.track) : loadBiologging(motionUrl)`). Every
existing caller omits `track` and is unaffected, so `/workbench` and the `orca`
sandbox cannot regress from this edit. The findings below are about whether
`HUNT-INT` and `HUNT-ACCEPT` will actually *work* and pass their own acceptance
criteria, not about breaking existing routes.

Severity legend used below: BLOCKER (an acceptance criterion cannot be met as
built), MAJOR (likely to fail or badly degrade in a real session), MINOR
(edge-case robustness / contract ambiguity).

---

## F1 (BLOCKER, and the sharpest finding) — the real-tileset "happy path" makes the swim-to-ram mechanic effectively unreachable; the documented flat-plane "fallback" is the only playable movement scale, and nothing locks which scale `HUNT-INT` uses

This is the answer to the dispatch's bathymetry question, and it is worse than
"does the tileset mount."

The pilot converts real swim speed to scene units by multiplying by
`worldUnitsPerMeter`:

```157:161:web/lib/scene/orcaPilot/deadReckoning.ts
    const speedWorldPerSec = speedMps * wupm;
    const fx = Math.cos(heading);
    const fz = -Math.sin(heading);
    controllerRoot.position.x += fx * speedWorldPerSec * dt;
    controllerRoot.position.z += fz * speedWorldPerSec * dt;
```

Under the locked real "full" tileset path, `worldUnitsPerMeter` is derived in
`onFit` as `sphere.radius / geoRadiusMeters(TILESET_BOUNDS)`, which HUNT-BATHY
itself computes as **≈ 0.00216 scene units per metre**
(`wavves/lanes/20260709_orca-boat-hunt/findings/HUNT-BATHY.md:192`). So cruise
(2.2 m/s, `deadReckoning.ts:22`) is ≈ 0.0047 scene units/s and boost (5.5 m/s,
`deadReckoning.ts:25`) is ≈ 0.0119 scene units/s.

But boats are spawned in *scene units*, sized to the 120-unit frame, not to the
orca's real-metre speed:

```15:18:web/lib/scene/boats/spawnBoats.ts
export const DEFAULT_BOAT_COUNT = 8;
export const DEFAULT_MIN_RADIUS = 14;
export const DEFAULT_MAX_RADIUS = 54;
export const DEFAULT_BOAT_COLLISION_RADIUS = 2.2;
```

The nearest boat is ≥ 14 scene units from the spawn origin. At boost speed under
the real-tileset scale that is 14 / 0.0119 ≈ **1180 seconds (~20 minutes) of
holding Shift to reach the closest boat**, and the collision radius is 2.2 units
(≈ 1000 m of real-scale travel). The `boats/` module and the `orcaPilot/`
module were built disjointly and never reconciled on scale: boat distances
assume the flat-plane convention (`worldUnitsPerMeter: 1`, as
`OrcaSandboxScene.tsx:124` uses and as `deadReckoning.ts:122` defaults to),
where cruise is 2.2 units/s and the nearest boat is ~6 s away.

Consequences for acceptance:
- Acceptance criterion 4 ("at least one boat, when the orca is driven within its
  collision radius, sinks", HUNT `waveset.md:232-233`) is **only reachable by
  swimming in the flat-plane/`wupm=1` configuration**, or by teleporting onto a
  boat (F4). By swimming under the real tileset it is not reachable in a demo.
- Acceptance criterion 3 ("pressing movement keys *visibly* changes the orca's
  world position over multiple frames", `waveset.md:229-231`) is technically
  true (position changes by a nonzero epsilon) but a CDP `Runtime.evaluate`
  read would pass while the on-screen orca looks frozen, because the chase
  camera sits only 8 units back (`chaseCamera.ts:42`) and the per-frame delta is
  ~1e-4 units.

The `HUNT-bathy-fidelity` lock (skip the seabed probe, use the fixed 0-25 m
band) does **not** cover this: it addresses the *depth clamp* input, not the
*horizontal movement scale*. `worldUnitsPerMeter` is a separate dependency that
HUNT-BATHY tells the integrator to derive from `onFit` and to gate movement on
(`HUNT-BATHY.md:202` "Gate on `worldUnitsPerMeter != null` before
integrating"). Which `worldUnitsPerMeter` HUNT-INT actually passes to
`createOrcaPilot` is not fixed by any locked decision or WIRING doc, yet it is
the single value that decides whether the game is playable. This is an unowned,
outcome-determining edge.

Recommendation for O0 (not an implementation plan, just the named gap):
HUNT-INT must consciously choose either (a) pass `worldUnitsPerMeter: 1` to the
pilot regardless of the tileset fit, decoupling arcade movement speed from the
geographic scale, or (b) scale boat spawn radii and collision radius down by the
fitted `worldUnitsPerMeter`. Shipping the "proven path" wupm from `onFit`
straight into `createOrcaPilot` without rescaling boats fails AC3/AC4 in
practice.

## F2 (BLOCKER) — if the tileset never fits, an `onFit`-gated integrator freezes the orca entirely; the flat-plane fallback covers *rendering* but not *movement*

Direct answer to "is there still a hard requirement the tileset mounts, or does
the flat-plane fallback cover this too."

There is no hard requirement the tileset renders. Locked decision 8
(`waveset.md:143-149`) and AC3 (`waveset.md:229-231`, "or the documented
flat-plane fallback") both explicitly allow the flat plane, and
`OrcaSandboxScene.tsx:206-218` is the cited fallback. So the *seabed/render*
side is covered.

The failure mode the fallback does NOT automatically cover is movement scale
sourcing. `useTilesLayer` only invokes `onFit` after the root bounding sphere
is available:

```183:187:web/lib/scene/tiles/useTilesLayer.ts
    if (fittedRef.current) return;

    const sphere = new THREE.Sphere();
    if (!tiles.getBoundingSphere(sphere)) return; // root not loaded yet
```

If the CloudFront tileset `load-error`s, times out, or never streams the root
(HUNT-BATHY.md:221 flags exactly this and notes Salish wires a `load-error`
fallback), `onFit` never fires. An integrator that follows HUNT-BATHY's
recommendation to gate dead-reckoning on `worldUnitsPerMeter != null`
(`HUNT-BATHY.md:202`) will then integrate with a null/undefined scale forever,
so the orca never moves and AC3 fails, even though the flat plane is happily
rendering. The fallback path must therefore *also* set an explicit
`worldUnitsPerMeter` (the `wupm=1` sandbox value) when it trips, not only swap
the geometry. No WIRING doc or decision states this coupling; it is a silent
assumption that "fallback == render a plane." Flagging as a named gap.

## F3 (MINOR) — `sonarPing.ping([])` with zero targets is a live, non-crashing but ambiguous state: an empty array reads as an *active* ping, not as *no* ping

Direct answer to "what happens if `ping()` is called with zero targets in
range." No crash, no throw. But the empty array is truthy, so the ping module
treats "pinged, found nothing" identically to "pinged, found something" and
distinctly from "never pinged":

```36:46:web/lib/scene/sonar/ping.ts
    getVisibleTargets() {
      if (!targets || remainingSeconds <= 0) return null;
      return targets;
    },
    clear() {
      targets = null;
      remainingSeconds = 0;
    },
    timeRemaining() {
      return targets ? remainingSeconds : 0;
    },
```

With `targets = []`, `getVisibleTargets()` returns `[]` (not `null`) for the
full `visibleSeconds` window (default 7 s, `ping.ts:3`), and `timeRemaining()`
returns a nonzero countdown. So a HUD that decides "radar open?" via
`getVisibleTargets() !== null` will open an empty radar panel for 7 s; a HUD
that maps `getVisibleTargets()?.map(...)` renders an empty list. Neither
crashes, but AC5 ("a non-empty target list with bearing/range for at least one
boat", `waveset.md:236-237`) then fails and the HUD gives the player no signal
distinguishing "out of range" from "sonar broken." This is a HUD-contract
ambiguity HUNT-INT owns.

Reachability of the empty state: `buildRadarTargets` defaults
`maxRangeWorldUnits = Infinity` (`radarTargets.ts:125`) and only drops a target
when `rangeWorldUnits > maxRangeWorldUnits` (`radarTargets.ts:137`), so with the
default filter every boat is always in range and the empty state cannot occur.
It only occurs if HUNT-INT (a) sets a finite `maxRangeWorldUnits` and everything
is beyond it, or (b) passes an empty `boats` array with no in-bounds `places`.
Bounded, hence MINOR, but the "empty means active ping" behavior is worth
pinning before the HUD is written.

## F4 (MAJOR, with a good-news half) — teleporting directly onto a boat DOES sink it (the ram check is stateless, not swept), but teleport + the skipped seabed probe can leave the orca's depth stale, and sunk boats remain teleport-selectable

Direct answer to "does the ram check still fire if position jumps rather than
moves continuously." Yes, it fires. `checkRamCollisions` is a pure per-frame
overlap test with no dependence on previous position or continuity:

```11:23:web/lib/scene/boats/collision.ts
  for (const boat of boats) {
    if (boat.state !== "floating") {
      continue;
    }

    const radius = boat.collisionRadius + extraRadius;
    const dx = boat.x - orcaX;
    const dz = boat.z - orcaZ;

    if (dx * dx + dz * dz <= radius * radius) {
      hits.push(boat.id);
    }
  }
```

Because the teleport target for a boat is exactly that boat's stored `x`/`z`
(radar targets copy `source.x`/`source.z`, `radarTargets.ts:147-148`; the beat
returns that XZ verbatim, `teleport.ts:63-65`), a teleport lands at distance 0,
which is inside the 2.2-unit radius, so the boat sinks on the first frame
`checkRamCollisions` runs after the write. It is NOT skipped by the jump.
(Only one sink: once `state !== "floating"` the boat is excluded, `collision.ts:12`,
so the 420 ms beat spent sitting on it does not re-fire.) This is arguably the
*only* reliable way to sink a boat given F1.

Two adversarial residues remain:
1. Teleport writes only X/Z (`teleport.ts:63-65`, sonar `WIRING.md:60-68`);
   depth (`pose.depthM` -> root Y via `driveOrca`) is owned entirely by the
   pilot's internal depth accumulator (`deadReckoning.ts:129,176-182`) and is
   never re-clamped on teleport. Because the real seabed probe is skipped
   (`HUNT-bathy-fidelity` lock; `getSeabedClearanceM` omitted, so `maxDepthM`
   stays the fixed 25 m band, `deadReckoning.ts:177-182`), teleporting from deep
   water into a shallow bay leaves the orca at its old `depthM` with no
   correction against the new location's floor. Under the real-tileset scale the
   magnitude is tiny (25 m ≈ 0.05 scene units), so it is cosmetic today, but it
   is a happy-path assumption that "teleport = XZ only" is complete; it is only
   complete because the depth clamp was deferred.
2. The sonar->boat mapping example passes boats with no state filter
   (`sonar/WIRING.md:37-43` maps `id/label/x/z` for every live boat), and
   nothing in `radarTargets.ts` filters on boat state. So already-sunk boats
   stay on the radar and remain teleport-selectable. Teleporting to a sunk boat
   lands the orca on a `state !== "floating"` prop that will not re-sink
   (correct) but also gives a dead target on the HUD. HUNT-INT should filter
   sunk boats out of the radar source list.

## F5 (MAJOR) — real frame-order hazard: `pilot.update()` and the teleport write are BOTH per-frame writers of `controller.root.position.x/z`, and no doc pins their combined order; the orchestrator's "composes cleanly" claim only holds if teleport runs last

Direct answer to the frame-order question. The three modules' WIRING docs each
specify an *internal* order but never a *combined* one, and HUNT-INT is the
first code to run all three in one `useFrame`.

- `orcaPilot/WIRING.md:68-86` requires `pilot.update(input, dt, controller.root)`
  (which does `position.x += ...`, `deadReckoning.ts:160-161`) to run BEFORE
  `controller.update()`.
- `sonar/WIRING.md:58-68` says every frame, if the beat is active, write
  `controller.root.position.x = xz.x; ...z = xz.z`.
- `boats/WIRING.md:45-49` reads `orcaX, orcaZ` for `checkRamCollisions`.

During an active teleport beat (default 420 ms ≈ 25 frames at 60 fps,
`teleport.ts:1,35`), `currentXZ()` returns the constant target every frame
(`teleport.ts:63-65`) while `pilot.update()` also keeps adding its own
`fx*speed*dt` increment to `controller.root.position` every frame
(`deadReckoning.ts:160-161`), because the pilot has no notion that a teleport is
in progress. The outcome depends entirely on ordering within the frame:
- teleport write AFTER `pilot.update()`  -> teleport wins, position pinned to
  target, clean snap. (This is the order the orchestrator assumed.)
- teleport write BEFORE `pilot.update()` -> the pilot's increment is applied on
  top of the target every frame, so the orca creeps off the target by up to
  `boost*wupm*dt` per frame for the whole beat, and `heading` keeps integrating
  from held keys, so the "instant teleport" visibly drifts and can rotate.

The orchestrator explicitly flagged this seam as unresolved and asserted it
"should" compose cleanly "since both are simple direct writes to the same two
fields, not competing owners of a stored authoritative value"
(`HUNT-ORCHESTRATOR-SUMMARY.md:64-72` and `:124-126`). That assertion is only
correct under one of the two orderings. It is a real ordering constraint, not a
non-issue, and it is currently written down as an assumption rather than a
locked frame sequence. HUNT-INT must (a) order the teleport write strictly after
`pilot.update()`, and ideally (b) suppress or zero the pilot's own XZ
integration while `teleportBeat.isActive()` so the two writers cannot fight.

Good-news half worth recording so O0 does not over-correct: position
*continuity* across a teleport is actually safe, because the pilot stores no
separate authoritative XZ. It reads and mutates `controller.root.position`
in place (`deadReckoning.ts:160-161`), so once the teleport moves that vector,
the pilot's next `+=` builds on the teleported value. The hazard is only the
per-frame contention *during* the beat, not desync after it.

## F6 (MINOR) — collision reads a position that must be sampled AFTER both writers, and boat state lives in per-frame React `setState`, a known r3f anti-pattern

Two smaller frame-order/perf hazards HUNT-INT inherits with no doc coverage:

1. `checkRamCollisions(orcaX, orcaZ, ...)` needs `orcaX/orcaZ` read from
   `controller.root.position` AFTER both `pilot.update()` and the teleport write
   in the same frame, or a teleport-onto-boat sinks one frame late (harmless) or
   a stale/mirrored position source misses the overlap entirely (a real miss).
   `boats/WIRING.md:45-49` only says "read the orca world X/Z from the future
   controller owner" and does not pin the read point in the frame. Unowned edge.
2. `boats/WIRING.md:56-70` mutates boat state through React `useState` +
   `setBoats(...)` **inside `useFrame`, every frame** (one `setBoats` for the
   collision flip, another for `advanceSink`, each producing new object
   references via the `{ ...boat }` spreads in `sinkAnimation.ts:35`). Calling
   `setState` 60x/s and re-reconciling 8 `BoatMarker` components each frame is
   the classic r3f "don't setState in the loop" anti-pattern and fights the
   invalidate/demand frameloop `useTilesLayer` relies on
   (`useTilesLayer.ts:109,177-181`). Recommend HUNT-INT hold boats in a mutable
   ref and drive `BoatMarker` transforms imperatively (or via a throttled state
   sync), not per-frame `setState`. MINOR because it is a perf/architecture
   smell rather than a correctness break, but on a hackathon demo machine it can
   cause visible jank.

## F7 (MINOR) — `getInput()` is single-consumer by construction; a second caller in the same frame silently steals the look deltas

`getInput()` returns the accumulated yaw/pitch then immediately zeroes them:

```119:133:web/lib/scene/orcaPilot/input.ts
    getInput(): OrcaPilotInput {
      const input: OrcaPilotInput = {
        forward,
        back,
        left,
        right,
        boost,
        yawDelta: accumYaw,
        pitchDelta: accumPitch,
        pointerLocked,
      };
      accumYaw = 0;
      accumPitch = 0;
      return input;
    },
```

If HUNT-INT calls `getInput()` more than once per frame (e.g. once to drive the
pilot and once to feed a HUD or a "press E to ping" reader), every call after
the first sees `yawDelta = pitchDelta = 0`, so mouse-look turning degrades or
dies depending on call order. The single-consumer-per-frame contract is real
but implicit; it is not stated in `orcaPilot/WIRING.md`. Flag so the integrator
reads input exactly once per frame and shares the snapshot.

---

## Notes on scope

- I did not reopen `HUNT-bathy-fidelity` or `HUNT-orbit-coexistence`. F1/F2/F4
  flag NEW risks the bathy lock introduces (movement scale and stale depth), as
  the check lane permits (`waveset.md:36-40`), without proposing to reverse the
  pick.
- No file was edited except this findings file. No git-mutating command was run
  (`git diff web/lib/scene/orca/OrcaController.ts` was used read-only to verify
  the one permitted edit).
