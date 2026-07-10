# HCHK — orca-boat-hunt-check

## Intent

Adversarial sanity-check of the `HUNT` lane's plan and delivered code before
`HUNT-INT` (the gated single-editor integration wave) is chartered/run. No
build. No implementation plan. This lane only produces findings and a
verdict.

## Artifact

- path: `wavves/lanes/20260709_orca-boat-hunt/waveset.md` (the plan, in
  particular the `HUNT-INT`/`HUNT-ACCEPT` sections, acceptance criteria, and
  the escalation catch), read together with:
  - `wavves/lanes/20260709_orca-boat-hunt/decisions/HUNT-bathy-fidelity.md`
  - `wavves/lanes/20260709_orca-boat-hunt/decisions/HUNT-orbit-coexistence.md`
  - `wavves/lanes/20260709_orca-boat-hunt/findings/HUNT-ORCHESTRATOR-SUMMARY.md`
  - the delivered code: `web/lib/scene/orcaPilot/*`, `web/lib/scene/boats/*`,
    `web/lib/scene/sonar/*`, and the diff on
    `web/lib/scene/orca/OrcaController.ts`
- landing_commit_hash: n/a (nothing in this repo has been committed; the
  delivered code is uncommitted working-tree state)
- branch: main
- repo_state_verified_against: cbe6483fb2157edcdca27e7b21dfffa7b961a7b5
  (verified via `git rev-parse HEAD` at HCHK charter time, matches the HUNT
  lane's own `repo_state_verified_against`; no commit has landed since)

## Locked

- Read-only reviewers. No file in `web/` or `wavves/lanes/20260709_orca-boat-hunt/`
  (the HUNT lane, as opposed to this HCHK lane) is edited by any HCHK member.
- High-reasoning model tier for every wave member (spec/code-integration
  review is judgment work, per the skill's own non-negotiable).
- Verdict must be `GO` | `REVISE` | `BLOCK` with named gaps, each citing an
  exact file and line/section, never a bare assertion.
- This check does not re-litigate the two decisions already locked in
  `decisions/HUNT-bathy-fidelity.md` and `HUNT-orbit-coexistence.md` (ship
  with the fixed 0-25m depth band; no `OrbitControls` in the new route).
  Reviewers may flag a NEW risk those locks introduce, but may not propose
  reopening the picks themselves.

## Waves

### Wave 1 — adversarial check (parallel, high-reasoning, NOT gated)

- `HCHK-W1a` grounding -> `findings/HCHK-grounding.md`: verify every claim in
  `HUNT-INT`'s plan and the `orcaPilot`/`boats`/`sonar` `WIRING.md` integration
  steps against the ACTUAL exported symbols and types in the delivered code
  (not just the WIRING prose). Flag any wiring-doc code sample that would not
  actually compile against the real exports, any stale `repo_state_verified_against`,
  and any cited path that does not exist.
- `HCHK-W1b` contradictions -> `findings/HCHK-contradictions.md`: hunt for
  internal conflicts between the three W2 modules' stated contracts (for
  example: does `orcaPilot`'s depth/position ownership genuinely never
  collide with `sonar/teleport.ts`'s planned `controller.root.position`
  write, frame-for-frame, once both are active in the same route? Does the
  now-locked "no OrbitControls" decision conflict with anything any WIRING.md
  assumed about camera setup?). Also check the two fresh decision records
  against `waveset.md`'s original locked decisions for any contradiction.
- `HCHK-W1c` completeness -> `findings/HCHK-completeness.md`: what does
  `HUNT-INT` need to do that is NOT covered by any existing WIRING.md or
  locked decision (silent assumptions, unowned edges)? In particular: exact
  disclaimer placement, exact boat-to-orca collision loop ownership (route
  state vs a new hook), how `sonarPing`'s visible-target list becomes an
  actual on-screen HUD element, and whether `HUNT-ACCEPT`'s acceptance
  criteria (in the HUNT `waveset.md`) are actually verifiable given what was
  built (e.g. is there a debug readout or `window` hook for a CDP position
  read, per acceptance criterion 3?).
- `HCHK-W1d` adversarial -> `findings/HCHK-adversarial.md`: hunt for failure
  modes and happy-path-only assumptions. In particular: what happens if the
  real "full" bathymetry tileset fails to load or fit in the browser during
  `HUNT-ACCEPT` (given the just-locked decision to skip the seabed probe, is
  there still a hard requirement that the tileset itself mounts, or does the
  flat-plane fallback cover this too)? What happens if `sonarPing.ping()` is
  called with zero targets in range? What happens to `boats/` state if the
  orca is teleported directly on top of a boat by the sonar teleport (does
  the ram-collision check still fire correctly, or does it get skipped
  because the position jumped rather than moved continuously)? Is there a
  frame-order hazard between `pilot.update()` (writes position), the boat
  collision check (reads position), and the teleport beat (also writes
  position) if `HUNT-INT` gets the per-frame call order wrong?

### Gate

- `HCHK-VERDICT`: O0 reconciles the four findings into
  `findings/HCHK-verdict.md`. Pass metric: every blocking gap is named with
  cited evidence (exact file/section), or the verdict is `GO` with zero
  blockers.

## Out of scope

- Writing `HUNT-INT`'s implementation plan.
- Any code change anywhere in `web/`.
- Reopening `HUNT-bathy-fidelity` or `HUNT-orbit-coexistence`.
- Commits, push, deploy.
