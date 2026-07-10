# HCHK-W1c — completeness

Lens: completeness. What does `HUNT-INT` need to do that is NOT covered by any
existing `WIRING.md` or locked decision (silent assumptions, unowned edges)?

Read-only review. No file was edited except this one. Verified against working
tree at `git rev-parse HEAD` = `cbe6483fb2157edcdca27e7b21dfffa7b961a7b5`
(matches the HCHK and HUNT wavesets' `repo_state_verified_against`); the
`OrcaController.ts` edit and the three new library directories are uncommitted
working-tree state.

## Urgent / active-regression flags

None. Nothing found here would make `HUNT-INT` break an already-working route.
Every item below is a missing piece that `HUNT-INT` must supply, not a
regression in delivered code. The delivered code type-checks and the three
modules are internally clean; the gaps are unowned integration edges that no
`WIRING.md` or locked decision assigns to anyone.

## Summary verdict for this lens

`HUNT-INT` cannot reach the HUNT `waveset.md` acceptance criteria by
"wiring existing pieces" alone. Four acceptance-relevant surfaces are net-new
and unowned: the sonar HUD element and its target-selection interaction, the
ping trigger input, the required disclaimer line, and a position-read hook for
acceptance criterion 3. Two of these (the HUD/selection and the criterion-3
hook) block specific numbered acceptance criteria, not just polish.

---

## Finding 1 (BLOCKING for acceptance criterion 3): no position-read hook or debug readout exists anywhere in the HUNT tree

HUNT `waveset.md:228-230` (acceptance criterion 3) requires movement to be
"verified via a CDP `Runtime.evaluate` position read or an on-screen debug
readout, not eyeballed alone."

- The pilot writes position at
  `web/lib/scene/orcaPilot/deadReckoning.ts:160-161`
  (`controllerRoot.position.x += ...`, `.z += ...`), but nothing exposes that
  value. `createOrcaPilot` (`deadReckoning.ts:121-200`) returns only
  `{ track, update }` (`deadReckoning.ts:92-104`, `199`); it exposes no getter
  for heading, position, speed, or depth.
- No `window.__*` hook is published anywhere under `web/lib/scene/orcaPilot/`,
  `web/lib/scene/boats/`, or `web/lib/scene/sonar/` (grep for `window.__`
  across `web/lib/scene` returns matches only in other lanes, e.g.
  `web/lib/scene/hud/spectro/WIRING.md:197` `window.__SPECTRO_PERF` and
  `web/lib/scene/hydrophone/WIRING.md:144` `window.__STATION_PLAYER`).
- No debug-readout component exists in any HUNT directory (the only HUD/readout
  components in `web/lib/scene` are the unrelated `PerfHud`
  (`web/lib/scene/picking/PerfHud.tsx`) and `SpectroHud`
  (`web/lib/scene/hud/spectro/SpectroHud.ts`), neither in HUNT scope).

Neither `orcaPilot/WIRING.md`, `boats/WIRING.md`, `sonar/WIRING.md`, nor any
locked decision assigns a debug readout or a `window` position hook to anyone.
This is an established repo convention for CDP-verifiable acceptance
(`hud/spectro/WIRING.md:197`, `hydrophone/WIRING.md:144` both do it), so its
absence in the HUNT tree is a silent gap: `HUNT-INT` must add the hook (a
`window.__ORCA_STRIKE` position publisher or an on-screen readout) or
acceptance criterion 3 has nothing to read. `HUNT-ORCHESTRATOR-SUMMARY.md`
does not mention this gap in its "HUNT-INT readiness" section
(`HUNT-ORCHESTRATOR-SUMMARY.md:113-135`).

## Finding 2 (BLOCKING for acceptance criteria 5-6): the sonar HUD element and its target-selection interaction are entirely unbuilt and unowned

`sonar/WIRING.md:51` states "Show `sonarPing.getVisibleTargets()` in the HUD.
On target selection, close the ping if desired and start the teleport." That is
the only mention of the HUD, and it is a directive to a future integrator, not
a delivered component.

- `createSonarPing().getVisibleTargets()` returns `SonarTarget[] | null` data
  only (`web/lib/scene/sonar/ping.ts:11`, `36-39`). Nothing renders it.
- The whole `web/lib/scene/sonar/` module is "pure TypeScript ... does not
  import ... React, or three.js" (`sonar/WIRING.md:3`), so it contains no HUD
  component and no click/tap target-selection handler. There is no `.tsx` file
  in `web/lib/scene/sonar/` (only `index.ts`, `radarTargets.ts`, `ping.ts`,
  `teleport.ts`).
- `SonarTarget` carries `bearingRad` and `rangeWorldUnits`/`rangeMeters`
  (`web/lib/scene/sonar/radarTargets.ts:6-31`), so acceptance criterion 5
  ("non-empty target list with bearing/range", `waveset.md:236-237`) is
  satisfiable at the data level. But acceptance criterion 6
  ("selecting a sonar target", `waveset.md:238-240`) requires a selection UI
  that does not exist, and the selection-to-`teleportBeat.start(x, z)` wiring
  (`sonar/WIRING.md:53-56`, `teleport.ts:45-48`) is unbuilt.

`HUNT-INT` must build a net-new React/DOM HUD that renders the target rows,
draws bearing/range, and calls `teleportBeat.start()` on click. No `WIRING.md`
sizes this, and no locked decision assigns its ownership (locked decision 7,
`waveset.md:137-142`, lists `sonar/` as "radar target list, ping/HUD, teleport
beat", but the delivered `sonar/` module produced only the target-list and beat
math, deferring the actual "HUD" rendering to the route without saying so
explicitly in a decision record).

## Finding 3 (BLOCKING for acceptance criteria 5-6): no input binding triggers a sonar ping

The input sampler captures only WASD/arrows, Shift boost, and mouse-look
(`web/lib/scene/orcaPilot/input.ts:49-53`, `74-88`, `94-100`). There is no key
mapped to fire a ping, and `OrcaPilotInput` (`input.ts:19-36`) has no ping
field.

`sonarPing.ping(targets)` (`ping.ts:7`, `24-27`) and `buildRadarTargets(...)`
(`radarTargets.ts:99-161`) must be invoked by something, but nothing in
`orcaPilot/`, `boats/`, or `sonar/` invokes them, and no `WIRING.md` names the
trigger (`sonar/WIRING.md:30-49` shows the call site but presupposes an
already-decided "on sonar ping" event). `HUNT-INT` must add the ping trigger
(a key binding in the route, or an extension to the sampler) and decide whether
it lives in `OrcaPilotInput` or in route-level state. This is an unowned edge
between the `orcaPilot` input module and the `sonar` module.

## Finding 4: the required disclaimer line is unplaced and unowned

Locked decision 9 (`waveset.md:150-154`) requires "a single small in-scene
disclaimer line ('arcade prototype, not navigational or scientific data')".
The only reference in delivered code is `boats/WIRING.md:83-84`: "The eventual
route should include the required in-scene disclaimer text, `arcade prototype,
not navigational or scientific data`."

- No component in any HUNT directory renders this string (grep for
  "arcade prototype" / "navigational or scientific" across `web/lib/scene`
  returns only `boats/WIRING.md:84`).
- Neither the placement (DOM overlay vs in-scene `<Html>` vs a fixed caption
  row like `SpectroHud`'s provenance caption at `hud/spectro/SpectroHud.ts:22`)
  nor the owning module is specified. `orcaPilot/WIRING.md` and
  `sonar/WIRING.md` do not mention the disclaimer at all.

This is not acceptance-blocking (no numbered criterion tests for it), but it is
a hard locked-decision requirement (`waveset.md:150-154`) with no owner, so it
is a silent assumption that `HUNT-INT` will remember to add it. `HUNT-INT`
should place it as a plain DOM caption on the new route.

## Finding 5: boat-to-orca collision loop ownership is delegated to "the route", with an unowned per-frame state-management choice

`checkRamCollisions` is a stateless pure helper
(`web/lib/scene/boats/collision.ts:3-26`). `boats/WIRING.md:52-53` explicitly
pushes state ownership to the caller: "Keep this transition in the route or
controller owner so the pure helper stays stateless." The suggested pattern is
React `useState` + a per-frame `setBoats(...)` inside the frame loop
(`boats/WIRING.md:41-42`, `54-71`).

Unowned edges here that no decision resolves:

1. The `boats/WIRING.md` pattern calls `setBoats(...)` twice per frame
   (`boats/WIRING.md:56-63` for the floating->sinking flip, and
   `boats/WIRING.md:67-71` for `advanceSink` on every non-floating boat). A
   per-frame React `setState` inside a `useFrame`/RAF loop forces a re-render
   each frame; whether the route should instead hold boats in a mutable ref and
   mutate in place is left undecided. No locked decision covers this, and it is
   the kind of choice that determines whether the boat layer re-renders 60x/s.
2. Who calls `checkRamCollisions` each frame, and with which orca position
   (the pilot's `controller.root.position` after `pilot.update()`, or a stale
   pre-update value), is stated only as prose in `boats/WIRING.md:45-49`
   ("read the orca world X/Z position from the future controller owner"),
   not owned by any module. This interacts with Finding 6.

Ownership is nominally answered ("the route owns it") but the concrete
mechanism (state vs ref) and the frame-order contract are silent assumptions.

## Finding 6: the per-frame call order across pilot / collision / teleport is only partially specified, and the collision read point is unowned

Two writers touch `controller.root.position` and one reader depends on it:

- `pilot.update()` writes `.x/.z` every frame
  (`deadReckoning.ts:160-161`); `orcaPilot/WIRING.md:68-76` fixes the order
  `pilot.update()` -> `controller.update()` -> `chaseCam.update()`.
- The teleport beat writes `.x/.z` directly, but only from the integrator
  (`sonar/WIRING.md:58-69`, `teleport.ts:63-65`); this write is explicitly
  left to `HUNT-INT` (`HUNT-ORCHESTRATOR-SUMMARY.md:58-72`).
- `checkRamCollisions` reads the orca X/Z (`collision.ts:17-20`).

No `WIRING.md` states a single unified per-frame order covering all three
(pilot write, teleport write, collision read). `orcaPilot/WIRING.md:68-76`
covers pilot+controller+camera but not boats or teleport. `boats/WIRING.md`
and `sonar/WIRING.md` each specify their own step in isolation. So the
question "does the ram check run before or after the teleport write on a
teleport frame" is unspecified. This is closely related to
`HCHK-W1d`'s adversarial frame-order concern; for the completeness lens the
gap is that no artifact defines the combined order, so `HUNT-INT` must author
it from scratch.

## Finding 7 (minor): boat display labels for the HUD are unowned

`buildRadarTargets` maps a boat's optional `label` and falls back to its `id`
(`radarTargets.ts:33-38`, `141` `const label = source.label ?? source.id`).
But the delivered `Boat` type has no `label` field
(`web/lib/scene/boats/BoatEntity.ts:3-15`), while `sonar/WIRING.md:37-43` shows
mapping `label: boat.label`. So the sonar HUD would display boat rows as
`boat-1`, `boat-2` (from `spawnBoats`' `id` at
`web/lib/scene/boats/spawnBoats.ts:64`) unless `HUNT-INT` invents a display
label. Not acceptance-blocking (criterion 5 only needs bearing/range), but the
HUD's human-readable boat labels are an unowned edge, and the
`sonar/WIRING.md:37-43` sample references a `boat.label` field that does not
exist on the delivered `Boat`.

---

## What is adequately covered (not a gap)

- The one permitted `OrcaController.ts` edit is present and matches locked
  decision 4 exactly (`git diff web/lib/scene/orca/OrcaController.ts`: additive
  optional `track?: BiologgingTrack` on `OrcaControllerOptions` plus the
  `opts.track ? Promise.resolve(opts.track) : loadBiologging(motionUrl)`
  branch). No completeness gap there.
- The flat-plane / fixed-depth fallback is fully owned and non-silent
  (`deadReckoning.ts:53-58`, `177-182`; `HUNT-bathy-fidelity.md` pick A), so
  the seabed-probe deferral is a documented decision, not a silent assumption.
- The teleport snap satisfies criterion 6's "within one frame" wording:
  `currentXZ()` returns the target immediately on the first active frame
  (`teleport.ts:63-65`), so the position write is single-frame, not eased.
