# ENV-ADV verdict (env-handle-consolidation)

- Lane `ENV` (BSWR), wave `ENV-ADV` (adversarial review). Owner the dispatched ENV sub-orchestrator (answers to O0).
- Audited against the working tree after the ENV-INT edit. Repo state base pin `61ba1d69ee36cf605f7ba741bdaa1defa8762834`.
- Validation: `tsc --noEmit` exit 0, no lint errors on the edited file. No commit.
- Scope of the edit: `web/lib/scene/orca/materials/wfxEnv.ts` (+81), `web/lib/scene/orca/index.ts` (+10), `web/app/components/scene/SalishScene.tsx` (+69 / -30). `OrcaPool.ts` and `OrcaController.ts` unchanged.

## Verdict

Zero open P0 and zero open P1. The two locked P0 disposal hazards are closed, the single `scene.environment` writer invariant is grep-proven intact, one PMREM bake is removed, and the null and identity-churn paths are statically safe. ENV-ADV passes. The lane is staged for ENV-ACCEPT (GPU parity), which is the human-gated render-host capture.

## Proof 1, single scene.environment writer (grep)

Command, scoped to the homepage scene graph as the charter requires:

```bash
rg -n "scene\.environment\s*=" web/app/components/scene web/lib/scene
```

Output:

```
web/app/components/scene/SalishScene.tsx:934:    scene.environment = env.pmremEnvironment;
web/app/components/scene/SalishScene.tsx:937:      if (scene.environment === env.pmremEnvironment) scene.environment = prev;
web/lib/scene/orca/materials/OMAT-R_shading.md:116:- **Above water:** set `scene.environment = pmremEnvironment` ...
```

Classification. `SalishScene.tsx:934` is the single write, inside `OrcaRig`'s
env-write effect. `SalishScene.tsx:937` is the identity-guarded restore of the
saved prior value in the same effect cleanup, not a second independent writer.
`OMAT-R_shading.md:116` is a markdown research note, not code. The accessor file
`web/lib/scene/orca/materials/wfxEnv.ts` returns zero (verified separately). The
`SliceRig` body returns zero. The line numbers moved from `:911`/`:913` to
`:934`/`:937` because publication comments and the `setLiveWfxEnv` call were added
above; the writer is unchanged. Single-writer invariant holds, proven not asserted.

Accessor purity check:

```bash
rg -n "scene\.environment\s*=" web/lib/scene/orca/materials/wfxEnv.ts   # -> no matches (PASS)
```

## Proof 2, one fewer PMREM bake

```bash
rg -n "makeRealWfxEnv\(" web/app web/lib
```

Output:

```
web/lib/scene/wfx/realWfxEnv.ts:51:export function makeRealWfxEnv(opts: RealWfxEnvOptions): WfxEnvHandle {
web/app/components/scene/SalishScene.tsx:912:      makeRealWfxEnv({
```

Before this wave there were two call sites in `SalishScene.tsx`, `OrcaRig` and
`SliceRig`. Now there is exactly one, `OrcaRig` at `:912`. The slice's second bake
is removed. One fewer PMREM bake at slice mount, confirmed by grep. The remaining
`realWfxEnv.ts:51` line is the function definition.

## Proof 3, P0 hazard (a) closed, slice never disposes the borrowed handle

The slice's old self-bake `useMemo` and its `useEffect(() => () => env.dispose?.(), [env])`
dispose effect are both deleted. The slice now reads the borrowed handle through
`useSyncExternalStore(subscribeLiveWfxEnv, getLiveWfxEnv, getLiveWfxEnv)` and never
calls `dispose` on it. A scan of the `SliceRig` body for `env.dispose` and for any
`dispose` of the borrowed handle returns nothing. The only `dispose` calls in the
slice body are `pool.dispose()`, `driver.dispose()`, `tl.dispose()`, and the
equipment `rig.dispose()`, none of which touch the env texture (confirmed in
ENV-R3, the pool dispose path disposes controllers only).

Sole owner and disposer is `OrcaRig`. Its env-write effect cleanup runs, in order,
the guarded `scene.environment` restore, then `clearLiveWfxEnv(env)`, then
`env.dispose?.()` (`SalishScene.tsx:936-940`). The clear runs BEFORE the dispose,
so no borrower can read a freed texture through the registry. The clear is
identity-guarded (`clearLiveWfxEnv` only nulls when the held value is that exact
handle), so an out-of-order teardown or a rebuild cannot wipe a newer handle. There
is exactly one free site for the live handle, `SalishScene.tsx:939`. The double-free
that would black the whole scene cannot occur, because the slice owns no free site.

## Proof 4, P0 hazard (b) closed, re-key rebuilds the pool, never setEnv

The pool-build effect dependency array is
`[authority, wfxEnv, station.lat, station.lng, worldUnitsPerMeter, demoCount]`
(was `env`, now `wfxEnv`). A change in the borrowed handle identity changes the
`wfxEnv` dep, which fires the effect cleanup at `SalishScene.tsx` (the cleanup
calls `pool.dispose()` and removes the group) and then re-runs the effect body,
which calls `createOrcaPool({ env: wfxEnv, ... })` and `pool.setSpawn(record)` to
build a fresh pool against the new handle. This is a teardown plus rebuild, not an
in-place update. `OrcaController.setEnv` is never called on the pool path, before
or after this edit. This is the required path because the pool eyes pin
`corneaMat.envMap` once at construction with no live update (`orcaEyes.ts:62`), and
`setEnv` updates the skin material only, so a rebuild is the only way to re-light
the eyes against a new handle. Re-key rebuilds, confirmed.

## Proof 5, null handle is skipped, no crash

The spawn effect guard is `if (!authority || !wfxEnv) return;`. When `OrcaRig` has
not yet published a handle, `getLiveWfxEnv()` returns null, `wfxEnv` is null, and
the effect returns before any pool build, exactly mirroring the existing
`authority` gate. No null dereference reaches `createOrcaPool` or
`createOrcaController`. When `OrcaRig` later publishes, `setLiveWfxEnv` notifies the
`useSyncExternalStore` subscriber, the slice re-renders with a non-null `wfxEnv`,
the dep changes, and the effect re-runs and spawns. No crash on null, deterministic
spawn on readiness.

## Proof 6, StrictMode and HMR identity churn re-key cleanly (static trace)

Production steady state. The `OrcaRig` env memo deps are `[gl, sun]`. `gl` is the
stable R3F renderer and `sun` is an empty-dep memo (`useScenicSun`), so the memo
does not recompute at runtime and the published handle identity is stable for the
`OrcaRig` mount. The registry holds one handle, the slice reads a stable snapshot,
and the pool is built once. No churn.

StrictMode and HMR. These remount `OrcaRig` and rebuild the handle. The safety
properties that hold across the churn:

1. Initial-mount ordering. `OrcaRig` is unconditional and mounts on first paint,
   while `SliceRig` mounts only when a station is selected, which is a later user
   gesture. So the StrictMode initial-mount double-invoke of `OrcaRig` completes
   before any pool exists, and there is no pool to read a disposed texture at that
   point.
2. Newest-handle-wins. If a rebuild publishes a new handle `env2` while a stale
   cleanup runs `clearLiveWfxEnv(env1)`, the identity guard leaves `env2` in the
   registry. The snapshot then reflects `env2`.
3. Re-key on identity. Any handle-identity change notifies the
   `useSyncExternalStore` subscriber, the slice re-renders, the `wfxEnv` dep
   changes, the pool effect cleanup disposes the old pool, and a fresh pool is
   built against the new handle. The pool never retains a reference to a disposed
   texture across a settled render.

The residual is a possible dev-only transient console warning during a full
unmount if sibling cleanup order frees `OrcaRig`'s texture a tick before the pool
teardown. This paints nothing (a full unmount renders no further frame) and is a
P2 cosmetic at most, not a production regression. The locked contract handles it
by ownership staying with `OrcaRig` and the slice never disposing.

## Failure-mode ledger after the edit

| Rank | Failure mode | Status | Evidence |
| --- | --- | --- | --- |
| P0 | Double-free of the borrowed handle | CLOSED | slice deletes its bake + dispose effect; no `env.dispose` in `SliceRig`; sole free site `SalishScene.tsx:939`; clear is identity-guarded and pre-dispose |
| P0 | Stale pool read on handle-identity change | CLOSED | pool effect dep `wfxEnv` re-keys; cleanup `pool.dispose()` then rebuild; never `setEnv` |
| P0 | Second `scene.environment` writer | CLOSED | scoped grep returns only `:934` write + `:937` guarded restore in `OrcaRig`; accessor and slice return zero |
| P1 | Lighting mismatch | DEFERRED to ENV-ACCEPT | inputs proven byte-identical in ENV-R4; parity must still be shown on Read-examined GPU frames |
| P1 | Transient stale read on full unmount | CLOSED (downgraded) | mount-order guarantee plus no-paint-after-unmount; at most a P2 dev console warning |
| P2 | Frame-time regression | DEFERRED to ENV-ACCEPT | one fewer bake expected to improve mount cost; measure in A/B |

## Staged for ENV-ACCEPT (human-gated GPU capture)

The one P1 that cannot be closed by static audit is lighting parity, which the
charter requires be proven on Read-examined GPU frames, not asserted. It is staged
for ENV-ACCEPT under the human render-host gate. The parity bar, locked at ENV-Q:
GPU before and after at
`?station=48.5583362,-123.1735774,Orcasound%20Lab&bsw_demo=3`, default dive-in plus
a `&view=topdown` pair, captured at `SLICE_DEFAULT_T=61.5`, same host and viewport,
SSIM at or above 0.99 AND near-zero mean per-pixel delta over the pool bounding box,
with a deliberately-wrong-env control frame to prove the comparator moves. Parity
is the bar, with a small mount-time improvement expected from the removed bake but
not required.
