# ENV-R1 findings, ORCA env ownership and accessor shape

Role ENV-R1, read-only research. Lane BSWR-ENV (env-handle-consolidation).
Repo state grounded against the charter pin `61ba1d69ee36cf605f7ba741bdaa1defa8762834`.
Scope of this file: where the LIVE `WfxEnvHandle` is built and owned, its
lifecycle, and the cleanest additive ORCA-owned accessor to publish that single
existing handle to the homepage slice. No source was edited.

## TL;DR

The live `WfxEnvHandle` is built by `makeRealWfxEnv` in
`web/lib/scene/wfx/realWfxEnv.ts:51`, but it is instantiated and owned by the
`OrcaRig` React component in `web/app/components/scene/SalishScene.tsx:894`,
not by anything under `web/lib/scene/orca/**`. That is the ownership ambiguity:
the type and barrel are ORCA-owned, the builder lives in WFX, and the live
instance is owned by a React component in the convergence file. The recommended
accessor is a module-level ref registry added to the ORCA lib
(`web/lib/scene/orca/materials/wfxEnv.ts`, re-exported from
`web/lib/scene/orca/index.ts`) that `OrcaRig` sets after build and clears on
dispose, and that `SliceRig` reads with a null fallback. It is additive, keeps
`OrcaRig` as the single `scene.environment` writer, and does not touch when or
how ORCA builds the env.

## Q1. Where the live handle is built and who owns it

The handle TYPE is ORCA-owned. `WfxEnvHandle` is declared in
`web/lib/scene/orca/materials/wfxEnv.ts:23-43` and re-exported from the ORCA
barrel at `web/lib/scene/orca/index.ts:9`.

The BUILDER is WFX-owned. `makeRealWfxEnv` lives at
`web/lib/scene/wfx/realWfxEnv.ts:51`. It PMREMs the decor sky dome
(`realWfxEnv.ts:53-61`), derives the twin-unit Beer-Lambert absorption from the
owner-signed `PROPOSED_RGB_EXTINCTION` (`realWfxEnv.ts:69-73`), and returns the
handle with its own `dispose()` that frees the PMREM target and the generator
(`realWfxEnv.ts:93-96`). Note this module imports the `WfxEnvHandle` type FROM
the orca barrel (`realWfxEnv.ts:28`), so the dependency direction is WFX builder
depends on ORCA type, never the reverse.

The live INSTANCE is owned by a React component, not by the orca lib. The single
live handle for the live twin is created inside the `OrcaRig` component in the
convergence file `web/app/components/scene/SalishScene.tsx`. `OrcaRig` is defined
at `SalishScene.tsx:885`. It calls `makeRealWfxEnv` exactly once in a `useMemo`
at `SalishScene.tsx:894-904`. That memoized `env` is the live handle. The same
component is the SOLE writer of `scene.environment`: the assignment
`scene.environment = env.pmremEnvironment` happens in the `useEffect` at
`SalishScene.tsx:909-916`. The controller is built from this handle via
`createOrcaController({ env, ... })` at `SalishScene.tsx:930-937`.

`OrcaController` does NOT own the handle. `createOrcaController` takes
`env: WfxEnvHandle` at `OrcaController.ts:63` (option declared at line 29),
threads it into `makeOrcaMaterial` and `makeOrcaEyes` at `OrcaController.ts:78`
and `OrcaController.ts:83`, and exposes `setEnv(env)` at
`OrcaController.ts:164-166`. It never stores the handle as controller state and
its `dispose()` at `OrcaController.ts:168-173` frees eyes, mouth, material, and
rig but never calls `env.dispose()`. So the controller is a CONSUMER of the
handle, not its owner.

Ownership ambiguity for an ORCA-owned accessor. The thing the charter calls
"ORCA-owned" is split across three places. The TYPE and the barrel are in
`web/lib/scene/orca/**`, the BUILDER is in `web/lib/scene/wfx/**`, and the LIVE
INSTANCE plus its lifetime are owned by the `OrcaRig` React component in
`SalishScene.tsx`. There is no module under `web/lib/scene/orca/**` that holds a
reference to the live handle today. An ORCA-owned accessor therefore cannot
simply "read" an existing module-level value, because no orca module currently
holds one. The accessor has to be a publication channel that `OrcaRig` writes
into after it builds the handle, with the channel itself declared in the orca
lib so it stays ORCA-owned by the charter's definition.

## Q2. The handle lifecycle today

Creation. The handle is created lazily in the `useMemo` at
`SalishScene.tsx:894-904` with dependency array `[gl, sun]`. `gl` is the live
renderer from `useThree`, stable for the Canvas lifetime. `sun` comes from
`useScenicSun()` at `SalishScene.tsx:889`, and `useScenicSun` is
`useMemo(() => makeSun(SCENE_TIME, 48.5, -123), [])` at `SalishScene.tsx:709-710`
with an empty dependency array, so the sun object is stable for the component
instance. In practice both deps are stable across the life of one `OrcaRig`
mount, so the memo computes the handle once on first render and does not
recompute while `OrcaRig` stays mounted.

Validity. The handle is fully built and assigned to `scene.environment` after
the `useEffect` at `SalishScene.tsx:909-916` runs, which is after first commit.
The handle object itself exists from the first `useMemo` evaluation, but the
scene-level publication (`scene.environment`) is set in the effect. The PMREM
texture inside the handle is valid for the whole mounted lifetime.

Disposal. The same effect's cleanup at `SalishScene.tsx:912-915` restores the
previous `scene.environment` if it still points at this handle, then calls
`env.dispose?.()`, which runs `makeRealWfxEnv`'s dispose at `realWfxEnv.ts:93-96`
and frees the PMREM target and generator. This cleanup fires on `OrcaRig`
unmount and on any change to `[scene, env]`. There is a second consumer effect at
`SalishScene.tsx:926-959` keyed `[env, worldUnitsPerMeter]` that builds and tears
down the controller, but that effect never disposes `env`. Env disposal is owned
solely by the assignment effect.

Could the memo recompute and replace it. Only if `gl` or `sun` changes identity.
Given `sun` is an empty-dep memo and `gl` is the stable renderer, a recompute
during a single mount is not expected in the current code. If it ever did, the
old handle would be disposed by the assignment-effect cleanup and a new handle
published, which is exactly the staleness hazard an accessor must tolerate. The
accessor contract below treats "the handle can be replaced or cleared at any
time" as a first-class case rather than assuming the memo is permanent.

## Q3. Accessor shapes and tradeoffs

The constraint set for every option: additive only, ORCA-owned channel declared
in `web/lib/scene/orca/**`, must not add a second `scene.environment` writer,
must not change when or how `makeRealWfxEnv` is called by `OrcaRig`, and must
give the slice a defined valid-after-build, cleared-on-dispose contract.

### (a) Module-level mutable ref registry in the orca lib

Shape. Add a tiny singleton to the orca lib, for example a `liveWfxEnvRef` object
with `setLiveWfxEnv(handle)`, `getLiveWfxEnv()` returning `WfxEnvHandle | null`,
and `clearLiveWfxEnv(handle)` that only clears if the current value is that exact
handle. Declared in `web/lib/scene/orca/materials/wfxEnv.ts`, re-exported from
`web/lib/scene/orca/index.ts`. `OrcaRig` calls `setLiveWfxEnv(env)` right after
build and `clearLiveWfxEnv(env)` in its dispose cleanup. `SliceRig` calls
`getLiveWfxEnv()` and falls back to its own bake or skips when null.

Additive. Yes. No existing signature changes, the ref is net-new.

ORCA-owned. Yes. The ref lives in the orca lib and is exported from the orca
barrel, matching the charter's `wfxEnv.ts` extend plus `index.ts` export.

Single writer preserved. Yes. The ref publishes only a reference to the existing
handle. The slice reads it and hands it to `createOrcaPool` for pool lighting.
Nothing in this option assigns `scene.environment`, so `OrcaRig` stays the sole
writer at `SalishScene.tsx:911`.

Lifecycle contract. Set after the handle is built in `OrcaRig`, cleared in the
`OrcaRig` cleanup before `env.dispose()` runs, so a reader never sees a disposed
texture through the ref as long as the slice reads it synchronously at pool-build
time and does not retain the handle past `OrcaRig` unmount.

Failure modes. The ref is global mutable state, so two simultaneous live twins on
one page would clash. That case does not exist in this app, the homepage mounts
one `TwinScene`. A stale read is possible if the slice caches the handle and
`OrcaRig` later disposes or replaces it, which the guarded `clearLiveWfxEnv(handle)`
plus a slice that re-reads on its own mount mitigates. If the slice reads before
`OrcaRig` has set the ref, it gets null and must fall back. This is the simplest
option that satisfies every constraint.

### (b) React context or provider owned by ORCA

Shape. An ORCA-owned context, for example `LiveWfxEnvContext`, provided by a
wrapper that `OrcaRig` populates and consumed by `SliceRig` via a hook.

Additive. Yes for the context object, but it forces a tree change. The provider
must wrap a node that is an ancestor of BOTH `OrcaRig` and `SliceRig`. Today they
are SIBLINGS in the `TwinScene` fragment at `SalishScene.tsx:1633` and
`SalishScene.tsx:1645`, so a sibling `OrcaRig` cannot provide context to its
sibling `SliceRig`. Making context work requires either lifting env creation out
of `OrcaRig` into a provider, which is option (c), or wrapping both siblings,
which edits the convergence file structure during ENV-B and is outside the
"no SalishScene edit yet" gate.

ORCA-owned. The context type can live in the orca lib, but the wiring lives in
`SalishScene.tsx`.

Single writer preserved. Yes, context only passes a reference.

Lifecycle contract. Context value is null until the provider sets it, then the
handle, then null on dispose. React re-render semantics give consumers a clean
update, which is nicer than a mutable ref for staleness. The cost is the required
tree restructure.

Failure modes. The sibling tree means this option cannot be implemented without
either restructuring the mount or moving env creation. That collides with the
locked single-builder and the ENV-B "no SalishScene edit" gate. Rejected for ENV
on tree-shape grounds, not on correctness.

### (c) Lift env creation into a shared parent or dedicated ORCA provider

Shape. A new ORCA provider component that calls `makeRealWfxEnv` once, assigns
`scene.environment`, exposes the handle by context or ref, and renders both the
orca controller and the slice as descendants.

Additive. No in spirit. This MOVES where and by whom the env is built and where
`scene.environment` is written. The charter locks exactly one writer as the
`OrcaRig` component and forbids changing when or how ORCA builds the env. Moving
the build into a new provider violates locked decisions 1 and 2 of the charter
and reopens the single-writer question.

Verdict. Rejected. Cleanest in the abstract, but it changes the builder and the
writer, which the charter forbids.

### (d) Ref passed by props from the common parent

Shape. A `MutableRefObject<WfxEnvHandle | null>` created in `TwinScene`, passed
to `OrcaRig` to set and to `SliceRig` to read.

Additive. Partly. The ref object is net-new, but threading it requires editing
`OrcaRig` and `SliceRig` props in `SalishScene.tsx`, which is the convergence
file. The ENV-B gate forbids a `SalishScene` edit, that belongs to ENV-INT.

ORCA-owned. Weak. The ref is created in `TwinScene` in the convergence file, not
in the orca lib, so it is not ORCA-owned by the charter's definition. It would
have to be typed by an ORCA-exported type to claim partial ownership.

Single writer preserved. Yes, props only pass a reference.

Lifecycle contract. Same valid-after-build, cleared-on-dispose shape as (a), with
`TwinScene` holding the ref. The downside is that the ownership lives in the
convergence file rather than the orca lib, and it front-loads `SalishScene` edits
into ENV-B.

## Q4. Sibling ordering and lifetime guarantees

Tree shape. `OrcaRig` and `SliceRig` are siblings rendered by `TwinScene`. The
return fragment is at `SalishScene.tsx:1620`. `OrcaRig` is rendered
unconditionally at `SalishScene.tsx:1633`. `SliceRig` is rendered only when
`selectedStation` is truthy at `SalishScene.tsx:1645-1656`. So `OrcaRig` mounts
on first paint of `TwinScene` and stays mounted, while `SliceRig` mounts later on
a station selection and unmounts on deselection or station change.

Ordering and outliving. Because `OrcaRig` is unconditional and `SliceRig` is
conditional on a user-driven `selectedStation`, `OrcaRig` always mounts before
any `SliceRig` instance and outlives it in the normal flow. A user selects a
station after the scene is up, which mounts `SliceRig` while `OrcaRig` is already
live, and deselecting unmounts `SliceRig` while `OrcaRig` remains. The one risk
to call out is teardown of the whole `TwinScene`, where React unmount order of
siblings is not a guarantee the slice should depend on. The accessor must not
assume `SliceRig` is gone before `OrcaRig` clears its ref, which is why the clear
must be guarded by handle identity.

Read-before-build. If the slice reads the accessor before `OrcaRig` finished
building, the env handle exists from the `useMemo` at first render of `OrcaRig`,
which is earlier than any user-driven `SliceRig` mount, so under (a) the ref
should already be set by the time a station is selected. Even so the contract
must define the null case, because effect ordering across a single commit is not
something the slice should rely on. The slice reads, and if null, falls back to
its own bake or skips the pool spawn for that frame and retries on the next mount
dependency change.

Read-after-recompute or after-dispose. If `OrcaRig`'s env memo ever recomputed,
the old handle would be disposed by the assignment-effect cleanup at
`SalishScene.tsx:912-915`. A slice that cached the old handle would then read a
disposed texture. Mitigation: the slice does not cache across `OrcaRig` lifetime,
it reads the ref at pool-build time inside its own effect keyed on its own deps,
and the ORCA clear is identity-guarded so a recompute publishes the NEW handle
and a stale clear of the old handle cannot wipe the new one.

## Q5. Recommendation

Primary recommendation: option (a), a module-level mutable ref registry in the
ORCA lib.

Why it wins. It is the only option that is fully additive, keeps the channel
ORCA-owned under `web/lib/scene/orca/**`, leaves `OrcaRig` as the single
`scene.environment` writer, does not change when or how `makeRealWfxEnv` is
called, and does not require a `SalishScene` structural edit in ENV-B beyond the
two-line set and clear that `OrcaRig` adds when ENV-INT wires it. It also matches
the charter's named extension points exactly,
`web/lib/scene/orca/materials/wfxEnv.ts` extend plus
`web/lib/scene/orca/index.ts` export.

Rejected alternatives and reasons.
- Option (b) React context. Rejected because `OrcaRig` and `SliceRig` are
  siblings at `SalishScene.tsx:1633` and `SalishScene.tsx:1645`, so a sibling
  cannot provide context to a sibling without a tree restructure that the ENV-B
  gate forbids.
- Option (c) lift env creation into a provider. Rejected because it moves the
  builder and the `scene.environment` write, violating charter locked decisions 1
  and 2 and reopening the single-writer question.
- Option (d) ref by props from `TwinScene`. Rejected for ENV-B because the ref
  would be created in the convergence file rather than the orca lib, so it is not
  ORCA-owned, and threading props forces a `SalishScene` edit that belongs to
  ENV-INT.

Exact lifecycle contract for option (a).
- Valid after build. `getLiveWfxEnv()` returns the live `WfxEnvHandle` only after
  `OrcaRig` has built `env` and called `setLiveWfxEnv(env)`. Before that it
  returns null.
- Cleared on dispose. `OrcaRig`'s cleanup calls `clearLiveWfxEnv(env)` BEFORE
  `env.dispose?.()` runs, and `clearLiveWfxEnv` only nulls the registry if the
  current value is that exact handle, so a recompute or out-of-order teardown
  cannot clear a newer handle.
- Consumer obligation on null or absent. The slice must treat null as expected,
  not an error. It reads at pool-build time and, when null, either falls back to
  its current `makeRealWfxEnv` bake or skips the pool spawn and lets its own
  effect re-run when its deps change. The slice must NOT cache the handle across
  `OrcaRig`'s lifetime and must NOT call `env.dispose()` on a handle it read from
  the registry, since ORCA owns disposal.
- Single writer untouched. The registry never assigns `scene.environment`.
  `OrcaRig` at `SalishScene.tsx:911` remains the sole writer.

Files and exports the ENV-B build wave would add or extend.
- Extend `web/lib/scene/orca/materials/wfxEnv.ts`: add the registry, for example
  `setLiveWfxEnv(handle: WfxEnvHandle): void`, `getLiveWfxEnv(): WfxEnvHandle |
  null`, and `clearLiveWfxEnv(handle: WfxEnvHandle): void`, plus an internal
  module-level holder. No change to `makeSandboxWfxEnv` or the `WfxEnvHandle`
  type shape.
- Extend `web/lib/scene/orca/index.ts`: re-export `setLiveWfxEnv`,
  `getLiveWfxEnv`, and `clearLiveWfxEnv` alongside the existing
  `WfxEnvHandle` type export at line 9.
- No `OrcaController.ts` change is required for publication, since the controller
  is a consumer and not the owner. The set and clear calls live in `OrcaRig` and
  are added during ENV-INT, not ENV-B. The slice read replaces the second
  `makeRealWfxEnv` call at `SalishScene.tsx:1152-1163` during ENV-INT, with the
  pool input at `SalishScene.tsx:1342-1348` taking the published handle.

## Citations index

- Handle type: `web/lib/scene/orca/materials/wfxEnv.ts:23-43`
- Barrel exports: `web/lib/scene/orca/index.ts:8-9`
- Live builder: `web/lib/scene/wfx/realWfxEnv.ts:51`, dispose `:93-96`, type
  import `:28`
- `OrcaRig` component: `SalishScene.tsx:885`
- Live env memo, deps [gl, sun]: `SalishScene.tsx:894-904`
- Sole `scene.environment` write + cleanup dispose: `SalishScene.tsx:909-916`
- Controller build effect, deps [env, worldUnitsPerMeter]: `SalishScene.tsx:926-959`
- `useScenicSun` stable memo: `SalishScene.tsx:709-710`
- Controller env option and setEnv: `OrcaController.ts:29`, `:63`, `:164-166`
- Controller dispose, no env dispose: `OrcaController.ts:168-173`
- `SliceRig` component: `SalishScene.tsx:1114`
- Slice second bake + dispose: `SalishScene.tsx:1152-1163`
- Slice pool env input: `SalishScene.tsx:1342-1348`
- Sibling mounts in `TwinScene`: `SalishScene.tsx:1620`, `:1633`, `:1645-1656`
- Pool env option: `web/lib/scene/reenactment/OrcaPool.ts:26-27`, `:83`
