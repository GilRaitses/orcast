# HCHK verdict: REVISE

Reconciled by O0 from all four Wave 1 findings files (grounding,
contradictions, completeness, adversarial), each read in full, not summary
only. repo_state_verified_against: `cbe6483fb2157edcdca27e7b21dfffa7b961a7b5`
(re-confirmed via `git rev-parse HEAD`, unchanged since HUNT and HCHK were
chartered). No code was edited by any HCHK reviewer or by this reconciliation
except the one documentation correction in Blocker 3 below.

**No active regression.** All four lenses independently confirm: nothing in
the HUNT tree wires into a route yet, `/orca-strike` does not exist, and the
one existing-file edit (`OrcaController.ts`) is additive and backward
compatible. Every finding below is about whether `HUNT-INT`/`HUNT-ACCEPT` can
actually succeed as currently planned, not about breaking something that
works today.

## Verdict: REVISE (not BLOCK, not GO)

The architecture is sound (disjoint modules, the one additive edit is exactly
as scoped, `npm run typecheck` passes, all conventions are internally
consistent per two independent lenses). Nothing here indicates the plan's
phase boundaries or architecture are wrong. But one genuine, unlocked product
fork and one mis-cited decision record must be resolved before `HUNT-INT` is
chartered, and several build-scope gaps must be named in `HUNT-INT`'s own
charter rather than assumed away.

## Blocker 1 — unlocked movement-scale fork (route to `/mod-decide`, do not silently pick)

**Finding:** `HCHK-adversarial.md` F1. Under the real "full" bathymetry
tileset that `HUNT-BATHY` GO'd, the fitted `worldUnitsPerMeter` is
`~0.00216` scene units/metre. The pilot's dead-reckoning integrator
(`deadReckoning.ts:157-161`) scales real swim speed (2.2-5.5 m/s) by this
factor, giving ~0.005-0.012 scene units/second. Boats spawn 14-54 scene
units out (`spawnBoats.ts:15-18`, sized for the flat-plane `wupm=1`
convention `OrcaSandboxScene.tsx:124` uses). At that scale the nearest boat
is ~20 minutes away at boost speed. Acceptance criterion 4 (a boat sinks from
ramming) is unreachable by swimming under the real-tileset scale; criterion
3 (visible movement) is technically true but imperceptible on screen.

**Why this is a fork, not a bug fix:** there are two materially different,
both-legitimate product outcomes, and picking one changes what the demo
looks like:
- (a) Pass `worldUnitsPerMeter: 1` to the pilot regardless of the tileset
  fit, decoupling arcade movement speed from geographic scale (the orca
  swims at a fun, fixed arcade pace over real-looking bathymetry, but is not
  moving at "real" metres/second relative to the terrain).
- (b) Scale boat spawn radii and collision radius down by the fitted
  `worldUnitsPerMeter`, keeping the pilot's real-metre speed meaningful
  relative to the real-scale terrain, but shrinking the whole play area to a
  tiny patch of scene units.

This is exactly the kind of call `/mod-decide` exists for. It is not
resolved by either locked decision this lane already made
(`HUNT-bathy-fidelity` addresses the DEPTH-CLAMP probe, a different axis, per
Blocker 3 below; `HUNT-orbit-coexistence` is unrelated). **Recommend running
`/mod-decide` for this one fork before `/charter`-ing `HUNT-INT`.**

## Blocker 2 — pilot/teleport per-frame write collision (name as a required `HUNT-INT` implementation constraint, not a fork)

**Finding:** `HCHK-contradictions.md` Finding 1 and `HCHK-adversarial.md` F5,
independently, same root cause. `pilot.update()` writes
`controller.root.position.x/z` RELATIVELY every frame
(`deadReckoning.ts:160-161`, `+=`). The sonar teleport beat writes the SAME
two fields ABSOLUTELY every frame for its full ~25-frame (420 ms) duration
while active (`sonar/WIRING.md:58-68`, `teleport.ts:1,34-65`, `=`). Neither
`WIRING.md` pins the combined order. This directly contradicts
`HUNT-ORCHESTRATOR-SUMMARY.md:66-72`'s claim that the teleport is "not a
competing per-frame writer": for the beat's duration, it is, on the same two
fields.

Unlike Blocker 1, there is only one correct outcome here (an "instant"
teleport must not visibly creep or rotate), not a legitimate product choice
between two designs. This is a naming/ordering gap, not an open fork:
**`HUNT-INT` must order the teleport write strictly after `pilot.update()`
each frame, and should suppress the pilot's own XZ integration (or zero its
computed delta) while `teleportBeat.isActive()`**, per both lenses'
recommendation. This requirement should be written directly into
`HUNT-INT`'s own charter as a named constraint, not re-litigated via
`/mod-decide`.

Related, lower-severity items from the same lenses, also to fold into
`HUNT-INT`'s charter as named constraints rather than re-decided:
- Collision reads of orca X/Z must happen after BOTH writers in the same
  frame (`HCHK-adversarial.md` F6; `HCHK-completeness.md` Finding 6).
- Sunk boats should be filtered out of the sonar target list so they are not
  teleport-selectable after sinking (`HCHK-adversarial.md` F4.2).
- Boat state should not be driven through per-frame React `setState` inside
  the frame loop; prefer a mutable ref or throttled sync
  (`HCHK-adversarial.md` F6.2), an r3f perf smell, not a correctness bug.

## Blocker 3 — `HUNT-bathy-fidelity.md` mis-cites locked decision 8 (fixed directly, no re-decision needed)

**Finding:** `HCHK-contradictions.md` Finding 2. The decision record justified
skipping the real seabed probe by citing "locked decision 8's flat-plane
fallback language," but decision 8's fallback is conditioned on the tileset
FAILING to mount, a different axis from the depth-clamp probe choice. Since
`HUNT-BATHY` GO'd the real tileset, the actual planned state is: real
bathymetry renders AND a flat 0-25m depth clamp ignores it, so the orca can
visibly clip through or hover above rendered seabed wherever the real floor
isn't near 25m deep. This does not change the PICK (the fixed band still
ships now, per the original rationale: time budget before the event), but
the decision record's justification was wrong and hid a real, if currently
low-magnitude, cosmetic risk. I have corrected the decision record below
rather than reopening the pick, consistent with the check lane's rule that
reviewers may flag a new risk a lock introduces without proposing to reverse
it.

## Non-blocking scope gaps for `HUNT-INT`'s own charter (not forks, not re-decisions; name and own them there)

From `HCHK-completeness.md`, all confirmed by cross-reading the actual code:

1. No position/heading getter or `window.__*` debug hook exists anywhere in
   the HUNT tree (Finding 1), so acceptance criterion 3 has nothing for a CDP
   read to verify. `HUNT-INT` must add one (matching the repo's own
   convention, e.g. `hud/spectro/WIRING.md:197`'s `window.__SPECTRO_PERF`).
2. The sonar HUD element and target-selection interaction are pure data today
   (`sonar/` has zero `.tsx` files); the on-screen radar and its
   click-to-teleport handler are entirely `HUNT-INT`'s to build (Finding 2).
3. No input triggers a sonar ping; `HUNT-INT` must add a key binding and wire
   it to `buildRadarTargets`/`sonarPing.ping()` (Finding 3).
4. The required disclaimer line ("arcade prototype, not navigational or
   scientific data", locked decision 9) is not rendered anywhere yet
   (Finding 4).
5. Boat HUD labels have no source field on `Boat` (Finding 7 /
   `HCHK-grounding.md` G1); `HUNT-INT` should use `boat.id` or drop the
   `label` key when mapping into `sonar`'s `SonarSourceTarget`, since
   `radarTargets.ts:141` already falls back to `source.id`.
6. `sonarPing.ping([])` reads as an active-but-empty ping, not "no ping"
   (`HCHK-adversarial.md` F3); worth a HUD-contract note, not a blocker given
   the default range filter makes the empty case unreachable in practice.

## Minor documentation nits (no action required before `HUNT-INT`, listed for completeness)

- `orcaPilot/WIRING.md:82-86` overstates what `elapsed` drives inside
  `OrcaController.update()` (`HCHK-grounding.md` G2).
- `deadReckoning.ts:73-74` cites the wrong file for `CameraDirectorHandle`
  (`camera/director.ts` instead of `camera/types.ts`); `HCHK-grounding.md`
  G3.

## Recommended next step

1. Run `/mod-decide` for Blocker 1 (movement-scale fork) — the only genuine
   open product call this check surfaced.
2. Once locked, `/charter` `HUNT-INT` with: the movement-scale lock, Blocker
   2's frame-order constraints written in as named requirements (not forks),
   Blocker 3's corrected decision record, and the six non-blocking scope
   gaps listed as `HUNT-INT`'s own acceptance-relevant build items.
3. Do not run `HUNT-ACCEPT` until `HUNT-INT` demonstrates the frame-order fix
   and the movement-scale fix concretely (not just typecheck-clean).
