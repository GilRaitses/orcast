# HUNT-W2 Agent A - orcaPilot (input / dead-reckoning / chase camera)

Scope: `web/lib/scene/orcaPilot/` (new directory, new files only) plus the one
permitted additive edit to `web/lib/scene/orca/OrcaController.ts`. No git
commands run (read-only `git diff` used once, for self-verification only).

---

## Progress log

1. Read grounding files first: `OrcaController.ts`, `biologging.ts`,
   `rig/OrcaRig.ts`, `camera/director.ts`, `camera/types.ts`,
   `OrcaSandboxScene.tsx`, `HUNT-INPUT.md`, `HUNT-ADVERSARIAL.md`,
   `waveset.md`, `WIRING-tiles-layer.md` (WIRING.md style reference),
   `web/tsconfig.json`, `web/package.json`. Confirmed no eslint config file
   exists anywhere under `web/` (relevant for the validation step below).
2. Wrote `web/lib/scene/orcaPilot/input.ts` - `createOrcaPilotInputSampler`.
3. Wrote `web/lib/scene/orcaPilot/PilotTrack.ts` - `createPilotTrack`, the
   generic `BiologgingTrack`-shaped stub wrapper around a live pose getter.
4. Wrote `web/lib/scene/orcaPilot/deadReckoning.ts` - `createOrcaPilot`, the
   stateful dead-reckoning integrator (heading/speed/pitch/roll/depth/fluke).
5. Wrote `web/lib/scene/orcaPilot/chaseCamera.ts` - `createChaseCamera`.
6. Applied the one permitted edit to `OrcaController.ts` (diff pasted below).
7. Wrote `web/lib/scene/orcaPilot/index.ts` barrel and this WIRING/findings
   note plus `web/lib/scene/orcaPilot/WIRING.md`.
8. Ran `npm run typecheck` and `npm run lint` from `web/`. Results below.

---

## Files created

- `web/lib/scene/orcaPilot/input.ts`
- `web/lib/scene/orcaPilot/PilotTrack.ts`
- `web/lib/scene/orcaPilot/deadReckoning.ts`
- `web/lib/scene/orcaPilot/chaseCamera.ts`
- `web/lib/scene/orcaPilot/index.ts`
- `web/lib/scene/orcaPilot/WIRING.md`
- `wavves/lanes/20260709_orca-boat-hunt/findings/HUNT-W2-AGENT-A.md` (this file)

No file was created under `web/lib/scene/boats/`, `web/lib/scene/sonar/`, or
`web/app/(sandbox)/orca-strike/`, and no other existing file besides
`OrcaController.ts` was touched.

---

## OrcaController.ts edit (exact diff)

```diff
--- a/web/lib/scene/orca/OrcaController.ts
+++ b/web/lib/scene/orca/OrcaController.ts
@@ -36,6 +36,10 @@ export interface OrcaControllerOptions {
   worldUnitsPerMeter?: number;
   /** Extra multiplier on the depth descent for a watchable sandbox dive. */
   depthScale?: number;
+  /** Live pose source (e.g. a player-piloted PilotTrack). When present, skips
+   * loadBiologging(motionUrl) and drives from this track directly. Backward
+   * compatible: omit this to keep the existing biologging-driven behavior. */
+  track?: BiologgingTrack;
 }
 
 export interface OrcaCost {
@@ -69,7 +73,7 @@ export async function createOrcaController(opts: OrcaControllerOptions): Promise
 
   const [{ geometry, sourceMaterial }, track] = await Promise.all([
     loadOrcaMesh(meshUrl),
-    loadBiologging(motionUrl),
+    opts.track ? Promise.resolve(opts.track) : loadBiologging(motionUrl),
   ]);
 
   const matHandle: OrcaMaterialHandle = makeOrcaMaterial({
```

Nothing else in the file was touched (verified with `git diff -- web/lib/scene/orca/OrcaController.ts`, shown in full above - only these two hunks).

---

## Chosen numeric constants (also restated in WIRING.md)

| Constant | Value | Meaning |
|---|---|---|
| `CRUISE_SPEED_MPS` | 2.2 m/s | sustained forward speed |
| `BOOST_SPEED_MPS` | 5.5 m/s | Shift-held top speed |
| `REVERSE_SPEED_MPS` | 1.2 m/s | max backward speed |
| `ACCEL_MPS2` | 3.0 m/s^2 | acceleration toward desired speed |
| `DAMPING_MPS2` | 4.5 m/s^2 | braking/coast deceleration |
| `EXTRA_TURN_RATE_RADPS` | 1.4 rad/s | additive turn-rate assist from A/D (not a strafe) |
| `MAX_PITCH_RAD` | 20 deg | bounded cosmetic dive/climb pitch |
| `MAX_ROLL_RAD` | 15 deg | bounded cosmetic bank roll |
| `PITCH_RETURN_RATE` | 2.5 /s | pitch spring-back-to-level decay constant |
| `BANK_GAIN` | 0.35 | roll radians per (rad/s) of total turn rate |
| `DIVE_CLIMB_RATE_MPS` | 1.5 m/s | depth change rate at max pitch angle |
| `DEFAULT_MIN_DEPTH_M` / `DEFAULT_MAX_DEPTH_M` | 0 / 25 m | fallback safe depth band with no seabed probe |
| `FLUKE_HZ_AT_IDLE` / `FLUKE_HZ_AT_BOOST` | 0.15 / 0.6 Hz | fluke beat rate range, matched in order of magnitude to the real SRKW driver's corrected ~0.2-0.35 Hz band |
| chase camera `distance` / `height` / `smoothing` | 8 / 3 / 8 (defaults) | third-person follow standoff and exponential-smoothing rate |

All are documented inline as comments in `deadReckoning.ts` and `chaseCamera.ts`.

---

## Design choices made where the prompt left a "your call"

- **Left/right semantics**: implemented as an additive yaw-rate turn ASSIST
  on top of mouse yaw (`EXTRA_TURN_RATE_RADPS`), not a strafe. The orca always
  moves along its own heading; there is no lateral slide. Documented in
  `deadReckoning.ts` and WIRING.md.
- **Chase camera look-at**: looks at a point raised `height * 0.35` above the
  target's root position (roughly body-level) rather than the bare root
  origin, so the framing does not point down at the ground under the orca.
  Documented in `chaseCamera.ts`.
- **`getSeabedClearanceM` contract**: defined as "maximum safe `depthM` at
  this world XZ", i.e. the seabed floor minus a safety margin, already
  expressed in metres-below-surface so `deadReckoning.ts` can clamp `depthM`
  to it directly with zero bathymetry-specific math in `orcaPilot/`. A future
  integrator is responsible for deriving this from the tiles probe's
  `getSurfaceY` plus `worldUnitsPerMeter`. Documented as a contract, not
  implemented here (keeps `orcaPilot/` disjoint from `web/lib/scene/tiles/`
  per the lane charter).
- **File split**: `PilotTrack.ts` holds the small generic
  `BiologgingTrack`-shaped wrapper (`createPilotTrack`); `deadReckoning.ts`
  holds all the stateful integration logic and constants and calls
  `createPilotTrack` internally. Kept as two files instead of one for
  reusability/readability, per "your choice how to split, but keep it
  organized" in the prompt.

---

## Validation

Both commands run from `/Users/gilraitses/orcast/web`, after all files above
were created and the `OrcaController.ts` edit applied.

### `npm run typecheck` (`tsc --noEmit`)

PASS, exit code 0, against the whole `web/` project.

```
$ npm run typecheck

> orcast-web@0.1.0 typecheck
> tsc --noEmit

(no output; exit 0)
```

### `npm run lint` (`next lint`)

BLOCKED, not a failure caused by these changes. Actual output:

```
$ npm run lint < /dev/null

> orcast-web@0.1.0 lint
> next lint

? How would you like to configure ESLint? https://nextjs.org/docs/basic-features/eslint
❯  Strict (recommended)
   Base
   Cancel ⚠ If you set up ESLint yourself, we recommend adding the Next.js ESLint plugin. See https://nextjs.org/docs/basic-features/eslint#migrating-existing-config
```

Root cause verified before writing this off as unrelated:

- No ESLint config file exists anywhere: `web/.eslintrc*`, `web/eslint.config.*`
  both glob to zero files, and `web/package.json` has no `eslintConfig` key.
- `web/node_modules` has no `eslint` package or `.bin/eslint` installed at all
  (checked directly), so `next lint` cannot even fall back to a bare default,
  it needs one of its interactive setup choices answered first, which writes
  a new top-level config file as a side effect of answering.
- This is a repo-wide, pre-existing condition unrelated to `orcaPilot/` or the
  `OrcaController.ts` edit; it would block `next lint` identically on a clean
  checkout with zero changes.

I did not answer the prompt (which would create a new `.eslintrc.json` at
`web/` root, a file outside my permitted scope of `web/lib/scene/orcaPilot/`
plus the one line-level `OrcaController.ts` edit) and did not install the
`eslint` package (a new dependency, also outside scope). As a substitute
sanity check within scope, Cursor's own linter (`ReadLints`) was run against
every file this task touched or created and reports **zero errors**:
`input.ts`, `PilotTrack.ts`, `deadReckoning.ts`, `chaseCamera.ts`, `index.ts`,
and `OrcaController.ts`.

---

## Gaps / escalations

1. **`npm run lint` cannot run to completion in this workspace** because the
   repo has no ESLint configuration anywhere and no `eslint` package
   installed (see above). This is pre-existing and reproducible with zero
   changes applied; I did not attempt to fix it since doing so requires
   either a new top-level config file or a new dependency, both outside this
   task's permitted file scope. `tsc --noEmit` passes cleanly and Cursor's
   linter reports zero errors on every file I touched, so I did not revert
   anything on account of this. **Escalating to O0**: someone with
   permission to add a repo-root-level ESLint config (or install `eslint`)
   should do so once, after which `npm run lint` should work for every HUNT
   agent, not just this one.
2. No other gaps. Every deliverable in the task list was completed:
   `input.ts`, `PilotTrack.ts` + `deadReckoning.ts` (dead-reckoning integrator
   + `PilotTrack`), `chaseCamera.ts`, the one-line-plus-one-field
   `OrcaController.ts` edit, the `index.ts` barrel, and `WIRING.md`.
