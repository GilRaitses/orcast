# HUNT-ADVERSARIAL: OrcaController optional `track` param safety review

Adversarial review of the locked one-file edit: add optional `track?: BiologgingTrack` to `OrcaControllerOptions` so `createOrcaController` skips `loadBiologging(motionUrl)` when `track` is present. Scope: `web/` only. No git commands run.

---

## Callers of createOrcaController

Grep for `createOrcaController(` under `web/` finds **four** matches: three call sites plus the definition.

| Caller | File:line | Options passed | Interaction with track-skip |
|--------|-----------|----------------|------------------------------|
| SalishScene orca mount | `web/app/components/scene/SalishScene.tsx:955` | `env`, `meshUrl: ORCA_MESH_URL`, `motionUrl: REAL_SRKW_MOTION_URL`, `worldUnitsPerMeter`, `depthScale: ORCA_DEPTH_SCALE` (1 at `SalishScene.tsx:206`), `timeScale: 1` | Does **not** pass `track`. Will continue to hit `loadBiologging(motionUrl)` on the default branch. No `motionUrl`-only side-effect consumption after build; only `c.root` / `c.update` used (`SalishScene.tsx:970-994`). |
| Orca sandbox | `web/app/(sandbox)/orca/OrcaSandboxScene.tsx:120` | `env`, `meshUrl` (param-driven), `motionUrl` (sim vs real at `OrcaSandboxScene.tsx:118`), `worldUnitsPerMeter: 1`, `depthScale` (view-dependent at `OrcaSandboxScene.tsx:113`), `timeScale: 1` | Does **not** pass `track`. Post-build reads `c.track.manifest`, `c.track.duration`, `c.track.sampleRate` for `__ORCA_DEBUG` (`OrcaSandboxScene.tsx:135-148`). Those fields come from `loadBiologging`, unchanged when `track` is omitted. |
| Reenactment pool | `web/lib/scene/reenactment/OrcaPool.ts:82` | `env`, `motionUrl: REAL_SRKW_MOTION_URL`, `worldUnitsPerMeter: wupm`, `depthScale`, `timeScale: 1` | Does **not** pass `track`. Spawns one controller per instance via `Promise.all` over instances (`OrcaPool.ts:80-88`). Per-frame `elapsed` comes from `clipSampleTime(currentTimeS, ...)` (`OrcaPool.ts:111-112`), not from controller internals. |
| Definition | `web/lib/scene/orca/OrcaController.ts:63` | N/A | Current unconditional `Promise.all([loadOrcaMesh, loadBiologging])` at `OrcaController.ts:70-73`. |

### Promise.all ordering / side effects (callers without `track`)

Current init at `OrcaController.ts:70-73`:

```ts
const [{ geometry, sourceMaterial }, track] = await Promise.all([
  loadOrcaMesh(meshUrl),
  loadBiologging(motionUrl),
]);
```

- `loadBiologging` (`biologging.ts:63-101`) performs two `fetch` calls (JSON + bin) and returns a closure; it has **no module-level side effects** beyond those network loads.
- `loadOrcaMesh` is independent. No caller reads partial controller state while `createOrcaController` is in flight; all three await the returned promise before use.
- **No caller relies on mesh vs biologging completion order.** Controllers are only attached after the full promise resolves (`SalishScene.tsx:963-971`, `OrcaSandboxScene.tsx:128-134`, `OrcaPool.ts:82-98`).
- `motionUrl` is resolved at `OrcaController.ts:65` (`opts.motionUrl ?? REAL_SRKW_MOTION_URL`) and passed only to `loadBiologging`. When a future caller supplies `track`, an unread `motionUrl` local is harmless; no caller today depends on `motionUrl` being fetched when unused.

**Conclusion for existing callers:** Conditional skip is safe. Omitting `track` preserves identical fetch behavior and timing semantics from the caller's perspective.

---

## Test coverage

### Unit tests (`npm run test:unit`)

`web/package.json:12` runs `node --test "lib/**/*.test.mts"`.

Under `web/lib/scene/orca/`, the only matching file is:

- `web/lib/scene/orca/physics/secondaryDynamics.test.mts` — imports `makeSecondaryDynamics` from `./secondaryDynamics.ts` (`secondaryDynamics.test.mts:19`). Loads motion `.bin` files directly from disk (`secondaryDynamics.test.mts:34-50`). Does **not** import `OrcaController.ts`, `biologging.ts`, or `rig/OrcaRig.ts`.

### Other test patterns in `web/`

Glob for `*.test.ts`, `*.test.mts`, `*.spec.ts` under `web/` (26 files). Grep for `OrcaController`, `biologging`, `OrcaRig` in those files:

- **No** `*.test.ts` / `*.spec.ts` file references these modules.
- E2e specs mention "orca" only in unrelated copy (e.g. `beat-05-ask.spec.ts:19` natural-language question) or repo branding (`demo-no-cred-walkthrough.spec.ts`). None exercise `createOrcaController` or the orca rig stack.

**Conclusion:** There is **zero automated test coverage** on `OrcaController.ts`, `biologging.ts`, or `OrcaRig.ts`. The optional-param change will not break an existing unit test; regression detection is manual / sandbox-only.

---

## elapsed/timeScale hazard analysis

### How `elapsed` and `timeScale` are used in `update()`

Definition: `web/lib/scene/orca/OrcaController.ts:118-157`.

| Symbol | Set in `createOrcaController` | Used in `update()` |
|--------|------------------------------|-------------------|
| `timeScale` | `opts.timeScale ?? 1` at `OrcaController.ts:66` | **Only** as `elapsed * timeScale` passed to `track.sample()` at `OrcaController.ts:119` |
| `elapsed` | Parameter to `update(dt, elapsed, cameraWorldPos)` | **Only** as `track.sample(elapsed * timeScale)` at `OrcaController.ts:119` |

`elapsed` does **not** appear elsewhere in `update()`. Downstream logic uses **pose fields** from `sample()`, not wall time:

- `driveOrca(rig, pose, wupm * depthScale)` — `OrcaController.ts:128`
- `prevYaw` / `yawRate` from consecutive `pose.yaw` values — `OrcaController.ts:131-138`
- `physics.step(yawRate, pose.flukePhase, pose.flukeAmp, dt)` — `OrcaController.ts:140`
- Mouth foraging from `pose.depthM`, `pose.flukeAmp` — `OrcaController.ts:148-152`
- Eyes from `dt` and camera — `OrcaController.ts:155-156`

### Init-time `sample(0)` call

At `OrcaController.ts:114`:

```ts
let prevYaw = track.sample(0).yaw;
```

This seeds yaw-rate differencing before the first `update()`. For a live `PilotTrack` whose `sample(t)` ignores `t` and returns the current integrated pose, `sample(0)` returns the same pose as any other `t`. That is correct for the first-frame `yawRate` calculation (delta ≈ 0 on frame one).

### Caller `elapsed` semantics (existing routes)

- **SalishScene** (`SalishScene.tsx:991-994`): monotonic `ORCA_TRACK_START_S + (clock.elapsedTime - startRef)` with `ORCA_TRACK_START_S = 0` (`SalishScene.tsx:209`). Matches baked-track expectation.
- **OrcaSandboxScene** (`OrcaSandboxScene.tsx:171-174`): paused scrub uses fixed `params.t`; running uses `params.t + (clock - start)`. Matches baked-track expectation.
- **OrcaPool** (`OrcaPool.ts:111-112`): `elapsed = clipSampleTime(currentTimeS, clip, phaseOffsetS)` — timeline playhead mapped into measured driver window; **not** monotonic wall time, but intentional for biologging `sample()` (`clipSampleTime.ts:18-29`).

### Live `PilotTrack` hazard verdict

Per locked design (`waveset.md:128-131`): `PilotTrack.sample()` returns live computed pose and may ignore `t`.

- **`elapsed` non-monotonicity** (e.g. teleport snapping playhead): irrelevant if `sample()` ignores `t`. No other `update()` code reads `elapsed`.
- **`timeScale` default 1** multiplied into ignored `t`: harmless.
- **`prevYaw` / `yawRate`**: depend on frame-to-frame `pose.yaw` deltas, not on `elapsed` monotonicity. Live heading changes remain well-defined.
- **Horizontal position**: locked decision 5 (`waveset.md:125-132`) places x/z on `controller.root.position` outside `driveOrca`; `update()` does not integrate position from `elapsed`.

**Care line:** `OrcaController.ts:119` — any future track implementation that *does* honor `t` on the new route must ensure the strike scene passes an `elapsed` consistent with that contract. For the locked live-pose design, no `OrcaController.ts` change beyond the optional `track` param is required.

---

## perf budget applicability

### `web/lib/scene/ocean/perf.ts`

- Purpose: frame-time A/B harness for **spectrogram HUD + interpretive ocean layer** (`perf.ts:1-8`).
- Exports: `FRAME_BUDGETS`, `measureFrameTimes`, `runFrameTimeAB` (`perf.ts:21-130`).
- Documented budgets: 60 fps desktop (~16.67 ms), 30 fps laptop (~33.3 ms) (`perf.ts:21-24`).

### Imports / gating in the orca stack

Grep for `perf`, `measureFrameTimes`, `runFrameTimeAB`, `FRAME_BUDGETS` under `web/lib/scene/orca/`:

- **No imports** of `ocean/perf.ts` in `OrcaController.ts`, `OrcaRig.ts`, `secondaryDynamics.ts`, or any other `web/lib/scene/orca/**` file.

Consumers of `perf.ts`:

- `web/lib/scene/ocean/index.ts:35` re-exports perf helpers.
- `web/app/(sandbox)/spectro/SpectroSandboxScene.tsx:27,165` runs `runFrameTimeAB`.
- `web/lib/scene/hud/spectro/WIRING.md:183-184` documents the harness.

### Applicability to orca-strike / player-piloted route

**Unrelated.** The orca stack carries its own **documented cost model** on `OrcaController.cost` (`OrcaController.ts:41-47,106-112`) and distance LOD inside `update()` (`OrcaController.ts:121-125,139-156`), but nothing wires that into `perf.ts` assertions.

`OrcaPool.ts:6-13` notes per-instance `createOrcaController` load cost and deferred shared-asset optimization; that is spawn/memory commentary, not a `FRAME_BUDGETS` gate.

**Plain statement:** A new player-piloted orca route inherits **no documented frame-time budget obligation** from `perf.ts`. General discipline (LOD already in `update()`, cap `dt` at 1/30 in callers — e.g. `SalishScene.tsx:994`, `OrcaPool.ts:106`) is precedent; the spectrogram A/B harness does not apply.

---

## Type consumers blast radius

### `OrcaControllerOptions`

Grep across `web/`:

- Defined: `web/lib/scene/orca/OrcaController.ts:28-39`
- Used as parameter type: `OrcaController.ts:63` only
- **Not exported** from `web/lib/scene/orca/index.ts` (barrel exports `OrcaController`, `OrcaCost` at `index.ts:31`, not `OrcaControllerOptions`)

Adding `track?: BiologgingTrack` touches **one file** for the interface and factory. No external TypeScript import of `OrcaControllerOptions` exists today.

### `BiologgingTrack`

| Location | Role |
|----------|------|
| `web/lib/scene/orca/motion/biologging.ts:49-58` | Interface definition |
| `web/lib/scene/orca/OrcaController.ts:21,52` | Import; `OrcaController.track` field |
| `web/lib/scene/orca/index.ts:23` | Type re-export |
| `web/lib/scene/reenactment/OrcaPool.ts:8` | Comment only (shared-asset optimization note) |
| `web/lib/scene/reenactment/WIRING.md:63` | Doc only |

No other `.ts`/`.tsx` file imports the `BiologgingTrack` type by name. Runtime consumption of track **data** (not the type) occurs in `OrcaSandboxScene.tsx:135-148` via `c.track.manifest` etc., which assumes a loaded biologging track today.

### `OrcaPose`

| Location | Role |
|----------|------|
| `web/lib/scene/orca/motion/biologging.ts:40-47,57,81,83,109` | Definition; `sample()` return; `driveOrca()` parameter |
| `web/lib/scene/orca/index.ts:23` | Type re-export |

No other file imports `OrcaPose` by name. `driveOrca` is exported from `index.ts:22` but grep shows no external importers of `driveOrca` outside the orca module (only `OrcaController.ts:21,128` uses it).

### `OrcaController` interface (related)

Exported type used by:

- `SalishScene.tsx:108,944`
- `OrcaSandboxScene.tsx:29,109`
- `OrcaPool.ts:19,37`
- `index.ts:31`

The planned edit does not change the `OrcaController` surface (`track` field already exists at `OrcaController.ts:52`).

---

## Verdict

**The planned additive optional `track?: BiologgingTrack` edit to `OrcaController.ts` is safe for all existing callers** as described. Omitting `track` preserves current `loadBiologging(motionUrl)` behavior; no caller depends on fetch ordering side effects or on `motionUrl` being read when a track is injected.

The edit should **not** require changes to other existing files for backward compatibility. New work (not part of this one-line contract) will live in `web/lib/scene/orcaPilot/` per `waveset.md:188-190`.

### Lines requiring care in `OrcaController.ts`

| Line(s) | Risk | Mitigation |
|---------|------|------------|
| `70-73` | Branch must skip `loadBiologging` only when `opts.track` is defined; preserve parallel mesh load. Use `opts.track ?? await loadBiologging(motionUrl)` or `Promise.all([loadOrcaMesh(meshUrl), opts.track ? Promise.resolve(opts.track) : loadBiologging(motionUrl)])`. | Implementer must not accidentally skip mesh load or always fetch biologging. |
| `65` | `motionUrl` computed even when `track` supplied. | Harmless dead binding; optional lint-only concern. |
| `114` | `track.sample(0).yaw` seeds `prevYaw`. | Safe for live `sample()` that ignores `t`; ensure `PilotTrack.sample()` is valid at init. |
| `119` | `track.sample(elapsed * timeScale)`. | Safe when live `sample()` ignores `t`; document strike scene contract if a time-driven track is ever passed. |
| `28-39` | New optional field on `OrcaControllerOptions`. | No external importers; no `index.ts` export required unless desired. |

### Out-of-scope risks (do not block the one-file edit)

1. **No automated tests** for `createOrcaController` — regressions would not be caught by `npm run test:unit`.
2. **`PilotTrack` must structurally satisfy `BiologgingTrack`** (`manifest`, `data`, `duration`, `sampleRate`, etc.) even if only `sample()` is exercised at runtime — that is new-file work in `orcaPilot/`, not an OrcaController blast-radius issue.
3. **`OrcaPool` shared-track optimization** (`OrcaPool.ts:8-12`) becomes *possible* with optional `track` but is explicitly deferred; current per-instance `loadBiologging` path unchanged.
4. **`perf.ts` budgets** do not apply; strike route has no inherited A/B gate.

**Bottom line:** Proceed with the single-file optional-param change. No additional existing-file edits are mandated by this adversarial review.
