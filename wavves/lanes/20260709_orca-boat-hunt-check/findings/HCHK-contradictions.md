# HCHK-W1b — contradictions

Reviewer lens: internal conflicts between the three HUNT-W2 module contracts,
the two locked decision records, and the HUNT lane's original `waveset.md`
locked decisions. Read-only. No code was edited. `git diff` was run only to
read the `OrcaController.ts` change.

repo_state_verified_against: cbe6483fb2157edcdca27e7b21dfffa7b961a7b5 (confirmed
via `git rev-parse HEAD`, matches both wavesets' recorded hash; nothing has
landed since).

## Active-regression check (read first)

No HUNT file wires anything into a route yet (`web/app/(sandbox)/orca-strike/`
does not exist, confirmed by the orchestrator summary line 103 and the gate).
Every conflict below is therefore LATENT: it becomes a real bug only when
HUNT-INT wires the modules together. Nothing in the delivered library code is
actively breaking an existing working route. The one existing-file edit
(`OrcaController.ts`, additive optional `track?` param) is backward compatible
and does not conflict with any current caller. So there is no urgent active
regression to escalate; the findings are for HUNT-INT to resolve before wiring.

---

## Finding 1 (BLOCKING) — pilot and teleport both write `controller.root.position.x/z` every frame during the 420 ms beat, with no defined order; the orchestrator's "not a competing per-frame writer" claim is inaccurate

This is the exact frame-for-frame collision the lens asks about, and the answer
is: the two modules DO collide, on the same two fields, on the same frames.

- `orcaPilot`'s integrator writes position RELATIVELY every frame:
  `web/lib/scene/orcaPilot/deadReckoning.ts:160-161`
  (`controllerRoot.position.x += fx * speedWorldPerSec * dt;` and `.z += ...`).
  Its WIRING prescribes calling `pilot.update(input, dt, controller.root)`
  once per frame, before `controller.update()`
  (`web/lib/scene/orcaPilot/WIRING.md:68-91`). Nothing in that WIRING mentions
  a teleport, and nothing tells the integrator to skip `pilot.update()` while a
  teleport is active.

- `sonar`'s teleport WIRING writes position ABSOLUTELY every frame while the
  beat is active: `web/lib/scene/sonar/WIRING.md:58-68`
  (`controller.root.position.x = xz.x; controller.root.position.z = xz.z;`
  inside `if (teleportBeat.isActive()) { ... }`).

- The beat is not a single-frame event. `createTeleportBeat` runs for
  `DEFAULT_TELEPORT_BEAT_DURATION_MS = 420` ms
  (`web/lib/scene/sonar/teleport.ts:1`, `:34-56`), i.e. roughly 25 frames at
  60 fps, and `currentXZ()` returns the SAME fixed target for the whole beat
  (`web/lib/scene/sonar/teleport.ts:63-65`, and `WIRING.md:94`
  "Teleport position snaps immediately"). So for ~25 consecutive frames BOTH
  writers fire on `controller.root.position.x/z`.

Because one writer uses `+=` and the other uses `=`, the per-frame result
depends entirely on call order, which neither WIRING doc pins down:

- pilot-then-teleport: pilot's swim increment is silently discarded each frame
  (position ends at the fixed target). Benign visually, but the pilot's
  displacement is thrown away for the beat's duration.
- teleport-then-pilot: teleport sets the target, then pilot adds
  `speed*dt` back on top, so the rendered position drifts off the flash target
  by up to `BOOST_SPEED_MPS * wupm * dt` each frame
  (`deadReckoning.ts:25`, `:157-161`), and the final resting position after the
  beat retains that last nudge.

This directly contradicts the reconciliation claim in
`wavves/lanes/20260709_orca-boat-hunt/findings/HUNT-ORCHESTRATOR-SUMMARY.md:66-69`
that the teleport is "a distinct, occasional action, not a competing per-frame
writer" and that there is therefore "no ownership conflict with locked decision
5." For the 420 ms of the beat it IS a competing per-frame writer of the same
two fields, and locked decision 5
(`wavves/lanes/20260709_orca-boat-hunt/waveset.md:125-132`, "Horizontal
position is owned by the new pilot module") names exactly one owner. The
summary's follow-up caveat (points 2 in `HUNT-ORCHESTRATOR-SUMMARY.md:122-126`)
asserts it "should compose cleanly ... since both are simple direct writes to
the same two fields," but that is the assertion, not a proof; "both write the
same two fields every frame" is the collision, not the reason it is safe.

There is also a completion off-by-one worth flagging against acceptance
criterion 6 (`waveset.md:236-238`): `update(dt)` sets `target = null` the frame
`elapsedMs >= durationMs` (`teleport.ts:52-55`), and `currentXZ()` is called
AFTER `update()` in the WIRING (`sonar/WIRING.md:62-64`), so the completing
frame writes nothing. The orca lands at the target only because the PREVIOUS
frame wrote it; if `pilot.update()` runs after that last teleport write, the
handoff frame carries the pilot's nudge.

Unowned edge: the per-frame ordering of `pilot.update()` versus the teleport
position write, and whether the pilot is suppressed during the beat, is
specified in NEITHER `orcaPilot/WIRING.md` nor `sonar/WIRING.md`. HUNT-INT must
lock this order (recommend: pilot first, teleport last, or gate `pilot.update`'s
position write while `teleportBeat.isActive()`), or the "no collision" claim is
unbacked.

---

## Finding 2 (BLOCKING) — `HUNT-bathy-fidelity` justifies the fixed depth band by citing decision 8's fallback, but decision 8's fallback is conditioned on the tileset FAILING; the two are different axes

`decisions/HUNT-bathy-fidelity.md` picks "ship the fixed 0-25 m band now, defer
the real `getSurfaceY` seabed probe," and justifies it (line 12) as "documented
in `orcaPilot/WIRING.md` already as a supported, non-silent fallback (locked
decision 8's flat-plane fallback language)."

That conflates two independent axes:

- Decision 8 (`waveset.md:143-149`) is about whether the real bathymetry
  TILESET mounts (the seabed the orca swims over). Its fallback is explicitly
  conditional: "If the real tileset URL or a fit issue blocks this within the
  time budget, a flat water-plane fallback ... is an acceptable documented
  fallback." The fallback is licensed only when the tileset FAILS.
- `HUNT-bathy-fidelity` is about the pilot's DEPTH-CLAMP source (fixed 0-25 m
  band vs the real `getSurfaceY` probe), which is a separate concern from
  whether the tileset renders.

These are not the same decision. Per the orchestrator summary
(`HUNT-ORCHESTRATOR-SUMMARY.md:12-13`), HUNT-BATHY gave a GO for the real "full"
tileset on the first attempt, so the planned state is: real tileset mounts
(decision 8 SATISFIED, not fallen back) AND fixed 0-25 m depth band applied
UNCONDITIONALLY (`deadReckoning.ts:53-58`, `:177-182` — the band is used
whenever `getSeabedClearanceM` is omitted, regardless of whether the tileset
loaded). `HUNT-bathy-fidelity` invokes decision 8's tileset-failure fallback
authority for a case decision 8 never covered (tileset succeeds, depth probe
deliberately not wired). `orcaPilot/WIRING.md:104-117` carries the same
conflation ("falls back to a fixed [0, 25] m depth band, which is ALSO the
correct behavior for the documented flat-plane fallback").

NEW risk this lock introduces (flagging, not reopening the pick): under the
flat-plane fallback the 0-25 m band is invisible because there is no rendered
seabed to clip through. Under the real "full" tileset that HUNT-BATHY GO'd, the
orca visually swims over real 3D bathymetry but its dive is clamped to a flat
0-25 m band that ignores it, so in any spot where the real seabed is shallower
than 25 m (or deeper, leaving the orca hovering) the orca will visibly clip
through or float above rendered seabed geometry. The fallback's own safety
argument ("no seabed to hit") does not transfer to the tileset-present case the
plan actually targets.

---

## Finding 3 (risk introduced by the locks) — deferring the real seabed probe hides a teleport-vs-pilot depth-ordering bug that resurfaces the moment the deferred probe is wired

`deadReckoning.ts:178-182` clamps `depthM` using
`getSeabedClearanceM(controllerRoot.position.x, controllerRoot.position.z)` —
it reads the CURRENT root XZ. Combined with Finding 1's unspecified frame order:

- If a teleport writes the new XZ before `pilot.update()` runs that frame, the
  depth clamp uses the NEW location's seabed.
- If `pilot.update()` runs first, the clamp uses the OLD location's seabed,
  then the teleport moves the orca to a different XZ whose seabed was never
  consulted that frame.

Right now this is masked purely because `HUNT-bathy-fidelity` (option A) omits
the probe, so `getSeabedClearanceM` is undefined and the clamp is a
location-independent constant (`deadReckoning.ts:177-182`). The decision itself
calls real-probe wiring "a candidate follow-up"
(`HUNT-bathy-fidelity.md:12`). If that follow-up is ever taken WITHOUT also
fixing Finding 1's frame order, teleporting into a shallow area can leave the
orca clamped to the departure location's (deeper) seabed for one or more frames,
i.e. briefly inside terrain. The frame-order fix (Finding 1) and the deferred
probe are coupled; that coupling is documented nowhere.

---

## Finding 4 (checked, NO contradiction) — the "no OrbitControls" lock is consistent with every WIRING.md camera assumption

I checked whether the `HUNT-orbit-coexistence` lock (option A, no
`OrbitControls` in the route) conflicts with anything any WIRING assumed about
camera setup. It does not:

- `orcaPilot/chaseCamera.ts:10-13` assumes the host "must disable/detach any
  `OrbitControls` ... so the two do not fight." No-orbit is the strongest form
  of that; consistent.
- `orcaPilot/WIRING.md:93-98` (step 5) leaves the choice open ("while
  `input.pointerLocked` is true, or for the whole pilot session, integrator's
  choice"). The lock resolves that open choice; it does not contradict it.
- `HUNT-INPUT.md:200-202` says a pilot scene "must disable or detach orbit
  controls while pointer-lock is active." Satisfied by removing orbit entirely.
- No original `waveset.md` locked decision requires `OrbitControls`; the
  grounding notes (`waveset.md:46-48`, `:52-54`) only describe the existing
  sandboxes' orbit cam as NOT the gameplay camera. So the lock also does not
  contradict any original locked decision.

The decision's supporting claim is accurate against the code: it states
`input.pointerLocked` "remains meaningful only for the pilot's own mouse-look
... which the sampler already zeroes while unlocked"
(`HUNT-orbit-coexistence.md:12`), and `input.ts:95` early-returns from
`onMouseMove` when unlocked, while `input.ts:102-109` zeroes the accumulated
deltas on lock loss. Consistent.

Minor NEW consequence (not a contradiction, the decision accepts it at line 12):
with orbit removed AND mouse-look gated behind `pointerLocked`
(`input.ts:70,95`, lock requires a click at `input.ts:90-92`), the player has
zero camera-rotation control before clicking to lock. `chaseCamera.update()`
runs unconditionally and frames the orca, so the view is not black, but it
cannot be rotated pre-lock. This is a UX consequence of the lock, explicitly
anticipated by the decision, not a contract conflict.

---

## Checked, consistent — heading / bearing / forward-vector conventions agree across all three modules

Not a contradiction, recorded so the verdict can rely on it. After the
orchestrator's bearing fix, the forward-vector convention
`(cos(heading), -sin(heading))` is identical in:

- `web/lib/scene/orcaPilot/deadReckoning.ts:154-161` (position integration)
- `web/lib/scene/orcaPilot/chaseCamera.ts:60-61` (behind-target eye placement)
- `web/lib/scene/sonar/radarTargets.ts:64-72` (`atan2(-dz, dx)` inverts it) with
  its documented convention at `radarTargets.ts:13-31` and `sonar/WIRING.md:73-75`

For a target on the orca's forward ray, `atan2(-dz, dx)` recovers `heading`
exactly, so `bearingRad` normalizes to 0 dead ahead. The three modules are
self-consistent by construction. The only wiring caveat (a completeness item,
not a contradiction) is that `buildRadarTargets`'s `orcaHeadingRad`
(`radarTargets.ts:99-102`) must be fed the pilot's live `pose.yaw`; the sonar
WIRING example (`sonar/WIRING.md:32-49`) passes `orcaHeadingRad` but does not
name its source.

## `controller.root` shape assumption is consistent

Both WIRING docs assume `controller.root` is a `THREE.Group` with `.position`.
Confirmed: `OrcaController.root: THREE.Group`
(`web/lib/scene/orca/OrcaController.ts:53-54`). `orcaPilot` takes
`controllerRoot: THREE.Group` (`deadReckoning.ts:103`) and `sonar/WIRING.md`
writes `controller.root.position.x/z`. No type conflict.
