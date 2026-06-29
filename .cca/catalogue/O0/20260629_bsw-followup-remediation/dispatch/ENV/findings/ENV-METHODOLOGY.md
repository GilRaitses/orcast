# ENV-Q methodology (env-handle-consolidation)

- Lane `ENV` (BSWR), wave `ENV-Q` (qualify methodology). Owner the dispatched ENV sub-orchestrator (answers to O0).
- Repo state verified against the charter pin `61ba1d69ee36cf605f7ba741bdaa1defa8762834`.
- Inputs: the four `ENV-R` findings under `dispatch/ENV/findings/` (orca-ownership, slice-consumer, lifecycle-disposal, adversarial).
- Status: O0 ruled the gate. The decisions below are LOCKED. This doc records the chosen method, the rejected alternatives, the parity metric, and the ORCA-ownership coordination. It changes no `web/**` source.

## Decision 1, the accessor API and readiness mechanism (locked)

The accessor is an additive, ORCA-owned module-level registry in
`web/lib/scene/orca/materials/wfxEnv.ts`, re-exported from
`web/lib/scene/orca/index.ts`. The published surface is:

- `setLiveWfxEnv(handle: WfxEnvHandle): void`. Called by `OrcaRig` after the live
  handle is built. Stores the handle and notifies subscribers.
- `getLiveWfxEnv(): WfxEnvHandle | null`. The snapshot reader. Returns the current
  live handle, or null before build and after clear. Reference-stable between
  notifications so it is safe as a `useSyncExternalStore` snapshot.
- `clearLiveWfxEnv(handle: WfxEnvHandle): void`. Called by `OrcaRig` on dispose,
  BEFORE `env.dispose?.()`. Identity-guarded, it only nulls the registry when the
  current value is that exact handle, so a recompute or out-of-order teardown
  cannot wipe a newer handle.
- `subscribeLiveWfxEnv(listener: () => void): () => void`. Registers a listener and
  returns an unsubscribe. Paired with `getLiveWfxEnv` so a consumer reads the
  registry through `useSyncExternalStore(subscribeLiveWfxEnv, getLiveWfxEnv, getLiveWfxEnv)`.

The slice reads readiness via `useSyncExternalStore`, so when `OrcaRig` publishes
the handle the slice re-renders and its spawn effect re-runs. The third argument
(server snapshot) is `getLiveWfxEnv`, which returns null during any non-client
render because the registry is empty there. The accessor module stays React-free.
It exports plain functions only, the `useSyncExternalStore` call lives in the
slice.

Rejected alternatives (from ENV-R1, confirmed by O0):
- React context. Rejected. `OrcaRig` and `SliceRig` are siblings
  (`SalishScene.tsx:1633` and `:1645`), so a sibling cannot provide context to a
  sibling without a tree restructure the ENV-B gate forbids.
- Provider lift of the env build. Rejected. It moves the builder and the
  `scene.environment` write, violating charter locked decisions 1 and 2.
- Parent props ref. Rejected. The ref would be created in the convergence file
  rather than the orca lib, so it is not ORCA-owned, and threading props forces a
  `SalishScene` edit that belongs to ENV-INT.

## Decision 2, ORCA-ownership coordination (granted by O0)

ENV owns this consolidation on ORCA's behalf. It is the follow-up the WIRING note
left (`web/lib/scene/wfx/WIRING-slice-note.md`), and there is no concurrent ORCA
editor. ENV may extend the ORCA-owned `wfxEnv.ts` and `index.ts` now in `ENV-B`,
and place the `setLiveWfxEnv` and `clearLiveWfxEnv` calls inside `OrcaRig` during
`ENV-INT`. The `SalishScene.tsx` edit is still serialized by O0 against the other
lanes that touch it.

## Decision 3, lifecycle contract (locked)

- Valid after build, cleared on dispose. `getLiveWfxEnv()` returns the live handle
  only between `OrcaRig`'s env memo build (`SalishScene.tsx:894-904`) and its
  env-write effect cleanup (`:914`).
- `OrcaRig` is the sole owner and sole disposer. The only free site stays
  `SalishScene.tsx:914`.
- The slice is a borrower and NEVER disposes the handle.
- On null the slice skips the spawn, mirroring the existing `authority` gate at
  `SalishScene.tsx:1308`.
- On handle-identity change the slice re-keys by REBUILDING the pool.

## Decision 4, hard build rules for the two P0 disposal hazards (locked)

- (a) Double-free. The slice deletes its second-bake `useMemo`
  (`SalishScene.tsx:1152-1162`) and its dispose effect (`:1163`) and must never
  call `env.dispose` on the borrowed handle. A double free of the handle
  `OrcaRig` still owns and still has on `scene.environment` blacks the WHOLE scene.
- (b) Re-key rebuilds the pool, not `setEnv`. The pool eyes pin
  `corneaMat.envMap` once at construction (`web/lib/scene/orca/eyes/orcaEyes.ts:62`)
  with no update path, and `OrcaController.setEnv` updates the skin material only
  (`web/lib/scene/orca/OrcaController.ts:164-166` to `orcaMaterial.ts:140-146`).
  A handle-identity change therefore re-keys by tearing down and rebuilding the
  pool, never by calling `setEnv`. The pool-build effect re-keys on the published
  handle identity in its dependency array.

## Decision 5, single scene.environment writer (locked)

`OrcaRig` at `SalishScene.tsx:911` plus the identity-guarded restore at `:913`
stays the only writer in the live twin. After the ENV-INT edit, prove it with a
grep scoped to `web/app/components/scene` and `web/lib/scene`. The new accessor
file and the `SliceRig` body must return zero `scene.environment` assignments.
Sandbox and workbench route scenes are separate scene graphs and are out of scope
for the homepage invariant.

## Decision 6, parity bar (locked)

GPU before and after at
`?station=48.5583362,-123.1735774,Orcasound%20Lab&bsw_demo=3`, the default dive-in
plus a `&view=topdown` pair, captured at `SLICE_DEFAULT_T=61.5`, same render host
and viewport. Read-examine both frames, then require SSIM at or above 0.99 AND a
near-zero mean per-pixel delta over the pool bounding box, with a
deliberately-wrong-env control frame to prove the comparator actually moves.
Parity is the bar, not the small expected mount-time speedup. Frame-time A and B
is reported as evidence, a small improvement at slice mount is expected because one
PMREM bake plus one sky-dome build and one VRAM render target are removed, and
steady-state frame time is unchanged.

## ENV-B scope (this wave)

- Extend `web/lib/scene/orca/materials/wfxEnv.ts` with the registry described in
  Decision 1. No change to `makeSandboxWfxEnv`, `makeRealWfxEnv` (it lives in
  `web/lib/scene/wfx/`), or the `WfxEnvHandle` type shape.
- Re-export the four functions from `web/lib/scene/orca/index.ts`.
- `OrcaPool` needs NO change. It is already env-agnostic and takes a plain
  `WfxEnvHandle` (ENV-R2). ENV-B2 is a no-op on the pool.
- The `SliceRig` consumer logic is prepared as an exact edit plan only. No
  `SalishScene.tsx` edit in ENV-B.
- Validation, `tsc --noEmit` clean, no `next dev` or `next build` during the
  parallel wave.

## ENV-INT edit plan (prepared, NOT executed in ENV-B)

All slice edits land in `web/app/components/scene/SalishScene.tsx` inside
`SliceRig`, by the single ENV-INT editor, after O0 grants the slot.

- `:1152-1162` delete the second-bake `useMemo<WfxEnvHandle>(() => makeRealWfxEnv(...))`.
- `:1163` delete the dispose effect `useEffect(() => () => env.dispose?.(), [env])`.
- Replace both with the read,
  `const wfxEnv = useSyncExternalStore(subscribeLiveWfxEnv, getLiveWfxEnv, getLiveWfxEnv);`
  importing `subscribeLiveWfxEnv` and `getLiveWfxEnv` from `@/lib/scene/orca`.
- `:1308` extend the spawn guard from `if (!authority) return;` to
  `if (!authority || !wfxEnv) return;`.
- `:1342` keep `createOrcaPool({ env: wfxEnv, ... })` structurally identical, it
  passes the borrowed handle instead of the local memo.
- `:1375` in the pool-effect dependency array, replace `env` with `wfxEnv` so a new
  handle identity rebuilds the pool (Decision 4b re-key, the effect cleanup already
  calls `pool.dispose()` so the rebuild is a teardown plus rebuild, not `setEnv`).
- Also in `OrcaRig`, add `setLiveWfxEnv(env)` after build and `clearLiveWfxEnv(env)`
  in the env-write effect cleanup BEFORE `env.dispose?.()`. This is the publication
  side, ORCA-owned per Decision 2, placed in the same convergence file under the
  ENV-INT slot.

Untouched by ENV. `OrcaRig`'s `makeRealWfxEnv` bake (`:894-904`) and its
`scene.environment` write (`:909-916`) are unchanged except for the two
publish/clear calls. `OrcaPool.ts` and `OrcaController.ts` need no change.

## Gate

ENV-B implements the accessor and prepares the consumer. The lane then PAUSES at
the ENV-INT gate and returns to O0 to REQUEST the `SalishScene.tsx` single-editor
slot, because OCN-INT also edits `SalishScene.tsx` and O0 must serialize the two.
No commit at any point.
