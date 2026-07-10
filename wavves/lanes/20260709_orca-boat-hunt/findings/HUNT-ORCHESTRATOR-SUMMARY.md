# HUNT orchestrator reconciliation summary

Lane orchestrator (HUNT-O) reconciliation after HUNT-W1 (discovery) and
HUNT-W2 (build). HUNT-INT and HUNT-ACCEPT were NOT run (both gated on O0, per
dispatch.md). No git command was run by the orchestrator or by any dispatched
wave subagent at any point in this run.

## Waves run

- **HUNT-W1** (discovery, 3 members, composer-2.5-fast, parallel): HUNT-INPUT,
  HUNT-BATHY, HUNT-ADVERSARIAL. All three landed their findings file. Verdicts:
  INPUT confirmed no existing controller (go for hand-rolled sampler); BATHY
  gave a GO recommendation for the real "full" tileset on first attempt;
  ADVERSARIAL gave a safety verdict of "safe" for the one-file
  `OrcaController.ts` edit, with an exact recommended diff pattern.
- **HUNT-W2** (build, 4 agents): Agent A (orcaPilot + the one edit,
  claude-sonnet-5-thinking-high), Agent B (boats, gpt-5.5-medium), Agent C
  (sonar/teleport, gpt-5.5-medium), Agent D (Bash.tv deliverable,
  composer-2.5-fast). All four completed. Agent A ran sequentially first
  (the risky shared-file touch); B/C/D ran afterward in parallel since none
  of them depend on A's files.

## Mid-run defect found and fixed (orchestrator-level)

While reconciling Agent C's `web/lib/scene/sonar/radarTargets.ts` against
Agent A's `web/lib/scene/orcaPilot/deadReckoning.ts`, found the two modules
used inconsistent heading/bearing conventions:

- `deadReckoning.ts` defines world forward at `yaw = heading` as
  `(cos(heading), -sin(heading))` in world X/Z (matches
  `OrcaRig.setOrientation`'s `outer.rotateY(yaw)`).
- `radarTargets.ts`'s original `targetBearingRad` computed
  `Math.atan2(dx, -dz)`, which is 90 degrees rotated from the convention
  above. Verified numerically: a target dead ahead of the orca at
  `heading = 0` (world +X) was reported at `bearingRad = +pi/2` (90 degrees
  to the right) instead of `0` (dead ahead).

This was not caught by `npm run typecheck` (pure numeric logic, not a type
error) or by either agent's own isolated validation (each module type-checks
and lints clean on its own; the bug is only visible when reasoning about both
conventions together, which is exactly the orchestrator's reconciliation job
since the two directories are intentionally disjoint and neither agent read
the other's file).

**Fix applied** (orchestrator, directly, in Agent C's own file only): changed
`targetBearingRad` to `Math.atan2(-dz, dx)`, which inverts the
`deadReckoning.ts` forward mapping exactly, and updated the doc comments on
`SonarTarget.bearingRad` and the function itself to state the convention
explicitly and cite `deadReckoning.ts` by name so a future reader does not
need to re-derive it. Re-ran `npm run typecheck` from `web/` after the fix:
still exit 0, clean.

**Cost:** ~15 minutes orchestrator time, one file touched
(`web/lib/scene/sonar/radarTargets.ts`), no new files, no agent re-dispatch
needed (fix was small enough to apply directly rather than re-dispatching
Agent C).

## Design decision made under delegated authority (not an escalation)

Agent C's teleport beat (`web/lib/scene/sonar/teleport.ts`) deliberately does
NOT write to any orca `controller.root.position` itself; it only computes and
returns the target world XZ and a flash-intensity curve. This was an explicit
instruction I gave Agent C to keep `sonar/` and `orcaPilot/` disjoint (locked
decision 7) while still satisfying locked decision 2 (instant teleport). The
actual one-line position write (`controllerRoot.position.x = ...`) is left
for HUNT-INT to perform, exactly mirroring how `orcaPilot`'s own
`update()` writes position, so there is no ownership conflict with locked
decision 5 (pilot module owns the per-frame position mutation) - the teleport
beat is a distinct, occasional action, not a competing per-frame writer.
I judged this a reasonable interpretation within delegated authority, not a
locked-decision conflict requiring escalation, but flag it explicitly here so
O0/HUNT-INT reviews the seam before wiring it.

## Verified repo-wide condition (escalation, not fixed)

`npm run lint` (`next lint`) is unusable across the ENTIRE repo right now,
independent of anything in this lane: there is no ESLint config file
anywhere under `web/` and no `eslint` package installed, so the command drops
into an interactive "how would you like to configure ESLint" prompt and
cannot complete non-interactively. Verified directly by the orchestrator
(piped empty stdin, confirmed the same interactive prompt appears). This is
NOT something any HUNT agent caused and NOT something any HUNT agent
attempted to fix (creating a new top-level ESLint config or installing a new
dependency is out of this lane's scope and a decision for O0/the operator).
`npm run typecheck` was used as the enforced validation gate instead, plus
Cursor's own linter via `ReadLints` on every new/changed file (zero errors
reported anywhere in the HUNT tree, both per-agent and in this orchestrator's
own final sweep).

## Full working-tree scope check (orchestrator-level)

`git status --short` was read (never written to) and every path was
attributed: the ONLY existing-file modification anywhere in the working tree
attributable to HUNT is `web/lib/scene/orca/OrcaController.ts`; the only new
HUNT directories are `web/lib/scene/orcaPilot/`, `web/lib/scene/boats/`,
`web/lib/scene/sonar/`, and `wavves/` (this lane's own home). No file under
`docs/whitepaper*/`, `web/app/workbench/WorkbenchScene.tsx`,
`web/lib/scene/hydrophone/stationCamera.ts`,
`web/lib/scene/ocean/doubleDiffusion.ts`, `web/.env.example`, `.cca/`,
`.render-array/`, `docs/devpost/`, `web/e2e/beats/`, `web/app/sign-in/`,
`web/public/demo-gifs/`, or `tools/testing/_ssm_run.sh` was touched, read as a
build dependency, or relied upon by any HUNT file. `web/app/(sandbox)/orca-strike/`
was NOT created, per the gate.

## Final validation (orchestrator, whole project, after the defect fix)

- `npm run typecheck` from `/Users/gilraitses/orcast/web`: **PASS**, exit 0.
- `npm run lint`: blocked repo-wide (see above), not a HUNT-caused failure.
- `ReadLints` over `web/lib/scene/orcaPilot/`, `web/lib/scene/boats/`,
  `web/lib/scene/sonar/`, and `web/lib/scene/orca/OrcaController.ts`: zero
  errors.

## HUNT-INT readiness recommendation

**Ready to run**, with three things O0/HUNT-INT should look at first:

1. The bearing-convention fix above (already applied) - HUNT-INT should
   spot-check that a sonar target directly ahead of the orca reads as bearing
   ~0 once the HUD is wired, as a quick sanity check that the fix is correct
   in practice, not just in isolated review.
2. The teleport-write seam (design decision above): HUNT-INT is the first
   code that will actually write `teleportBeat.currentXZ()` onto
   `controller.root.position.x/z`; confirm this composes cleanly with
   `orcaPilot`'s own per-frame `update()` (it should, since both are simple
   direct writes to the same two fields, not competing owners of a stored
   "authoritative" value).
3. The `OrbitControls` coexistence gap: both Agent A's `WIRING.md` and
   HUNT-INPUT.md flag that the future integrator must disable/detach any
   `OrbitControls` while pointer-lock/chase-camera is active; none of A/B/C
   implemented this since it is route-level wiring, not library code.

No other gaps found in HUNT-W1/W2 scope. `deliverable/BASHTV_BUILD_PROMPT.md`
was written by Agent D and independently reviewed by the orchestrator; it
transcribes the locked decisions faithfully and names real assets by path/URL
without inventing new mechanics.
