# ENV-R3 lifecycle and disposal findings

Role ENV-R3, read-only research, BSWR-ENV lane (env-handle-consolidation). Reports
to the ENV sub-orchestrator. No source edited. The only file written is this one.

Repo state verified against the charter pin `61ba1d69ee36cf605f7ba741bdaa1defa8762834`.
All citations are file and line as read at this state.

Scope of this finding. Establish who owns the env texture in each WFX handle, the
correct dispose order, and a grep/AST proof of the single `scene.environment`
writer invariant, then define the lifecycle contract a published-handle accessor
must honor so dropping the slice's second bake never leaves a disposed-texture
read and never frees an env that ORCA still owns.

---

## 1. Texture ownership in each handle today

### makeRealWfxEnv (the producer ORCA mounts, and the duplicate the slice mounts)

`web/lib/scene/wfx/realWfxEnv.ts`

- Line 53 constructs the generator, `const pmrem = new THREE.PMREMGenerator(opts.renderer)`.
- Line 59 bakes the render target, `const target = pmrem.fromScene(skyScene, 0, 0.1, 1000)`.
- Line 83 publishes the texture, `pmremEnvironment: target.texture`.
- Lines 93 to 96 are the disposer, `dispose() { target.dispose(); pmrem.dispose(); }`.

The published `pmremEnvironment` is `target.texture`, owned by the PMREM render
target. Its GPU lifetime is the render target's lifetime. The texture is freed
only when `target.dispose()` runs, and `target.dispose()` runs only inside this
handle's `dispose()`. Nothing else in the module holds `target`. So the texture
is freed only by `handle.dispose()`. Confirmed.

The dome and its sky scene are torn down at bake time, lines 60 to 61
(`skyScene.remove(dome.object3D)` then `dome.dispose()`), so they are not part of
the steady-state lifetime. Only `target` and `pmrem` survive in the closure, and
both are released together by `dispose()`.

### makeSandboxWfxEnv (the sandbox stand-in, not used by the live twin)

`web/lib/scene/orca/materials/wfxEnv.ts`

- Line 102 bakes, `const target = opts.pmrem.fromScene(skyScene, 0, 0.1, 100)`.
- Line 107 publishes, `pmremEnvironment: target.texture`.
- Lines 124 to 126 are the disposer, `dispose() { target.dispose(); }`.

Difference from the real producer. The sandbox does NOT own the generator. It
receives `opts.pmrem` from the caller (line 52, `pmrem: THREE.PMREMGenerator`) and
disposes only `target`, leaving the caller to dispose the generator. Again the
texture is `target.texture` and is freed only by `target.dispose()` inside this
`dispose()`. Confirmed.

### dispose is optional on the interface

`WfxEnvHandle.dispose` is declared optional at `web/lib/scene/orca/materials/wfxEnv.ts:42`,
`dispose?: () => void`. Every consumer therefore calls it as `env.dispose?.()`.
Both concrete producers above DO provide a real `dispose`, so today the optional
chaining is a no-op guard, not a missing free. This matters for the contract in
section 4. A published live handle must keep `dispose` defined on exactly one
owner and must not be invoked by borrowers.

Ownership summary for section 1. In both handles the env texture is owned by the
PMREM render target created at bake time, and it is freed exclusively by the
handle's own `dispose()`. There is no second owner and no shared registry.

---

## 2. No consumer ever disposes the env texture

Every consumer references `env.pmremEnvironment` as a material `envMap` or reads
the underwater optic. None calls `target.dispose()` or `texture.dispose()` on the
env texture. Reading each consumer's `dispose`.

- `makeOrcaMaterial.dispose` at `web/lib/scene/orca/materials/orcaMaterial.ts:147` to 149
  is `dispose() { material.dispose(); }`. The env texture is only assigned as a
  reference at line 61 (`material.envMap = env.pmremEnvironment`) and re-pointed in
  `setEnv` at line 144. `THREE.Material.dispose()` releases the material's program
  and fires its dispose event, and it does not dispose textures the material merely
  references such as `map`, `normalMap`, or `envMap`. `MeshPhysicalMaterial`
  inherits `Material.dispose` and adds no envMap disposal. So `material.dispose()`
  here does not free the env texture. Confirmed by reading the disposer plus the
  fact that the material never created the env texture, it only points at it.

- `makeOrcaEyes.dispose` at `web/lib/scene/orca/eyes/orcaEyes.ts:121` to 125 is
  `eyeGeo.dispose(); corneaMat.dispose(); opts.headBone.remove(group);`. The cornea
  material's `envMap` is the same borrowed env texture (line 62,
  `corneaMat.envMap = opts.env.pmremEnvironment`). As above, `corneaMat.dispose()`
  does not dispose its `envMap`. So the eyes do not free the env texture.

- `OrcaController.dispose` at `web/lib/scene/orca/OrcaController.ts:168` to 173 is
  `eyes.dispose(); mouth.dispose(); matHandle.dispose(); rig.dispose();`. It chains
  the disposers above plus mouth and rig. None of these touch the env texture, so
  the controller never frees it. Confirmed.

- `OrcaPool` at `web/lib/scene/reenactment/OrcaPool.ts`. `clearPool` lines 70 to 76
  does `group.remove(p.wrapper); p.controller.dispose();` per instance. `dispose`
  lines 134 to 136 calls `clearPool()`. The pool never references `opts.env.dispose`
  and never disposes a texture. It only forwards `opts.env` into
  `createOrcaController({ env: opts.env, ... })` at line 82. Confirmed the pool is a
  pure borrower.

Consequence. The only place that frees the slice's texture today is the slice's
own dispose effect, `web/app/components/scene/SalishScene.tsx:1163`,
`useEffect(() => () => env.dispose?.(), [env])`. The only place that frees
OrcaRig's texture is OrcaRig's env-write effect cleanup,
`web/app/components/scene/SalishScene.tsx:914`, `env.dispose?.()`. These are two
independent textures from two independent `makeRealWfxEnv` calls today. After
consolidation there must be exactly one such free site, owned by OrcaRig, and the
slice must stop owning a free site. This is the heart of the disposal contract.

---

## 3. Single scene.environment writer invariant (grep proof)

The invariant the charter locks is exactly one `scene.environment` writer in the
live twin scene graph, and it is `OrcaRig`. ORCA removes a second BAKE, never a
second writer. Below are the literal commands run from the repo root and their
full output, then the classification.

### Commands

```bash
cd /Users/gilraitses/orcast
rg -n "\.environment\b" web/          # CMD 1: every .environment reference
rg -n "\.environment\s*=" web/        # CMD 2: assignments (candidate writes)
rg -n "scene\.environment" web/       # CMD 3: the scene.environment token
```

### CMD 2 output (assignments, the candidate writes)

```
web/app/workbench/WorkbenchScene.tsx:163:    scene.environment = env.pmremEnvironment;
web/app/workbench/WorkbenchScene.tsx:169:      scene.environment = prevEnv;
web/app/(sandbox)/orca/OrcaSandboxScene.tsx:95:    scene.environment = env.pmremEnvironment;
web/app/(sandbox)/orca/OrcaSandboxScene.tsx:104:      scene.environment = null;
web/lib/scene/orca/materials/OMAT-R_shading.md:116:- **Above water:** set `scene.environment = pmremEnvironment` (or pass it to the material's
web/app/(sandbox)/slice/SliceScene.tsx:165:    scene.environment = env.pmremEnvironment;
web/app/(sandbox)/slice/SliceScene.tsx:171:      scene.environment = prevEnv;
web/app/components/scene/SalishScene.tsx:911:    scene.environment = env.pmremEnvironment;
web/app/components/scene/SalishScene.tsx:913:      if (scene.environment === env.pmremEnvironment) scene.environment = prev;
web/app/(sandbox)/reenactment/ReenactmentSandboxScene.tsx:213:    scene.environment = env.pmremEnvironment;
web/app/(sandbox)/reenactment/ReenactmentSandboxScene.tsx:219:      scene.environment = prevEnv;
```

### Classification of every assignment hit

The invariant is per scene graph. Each Canvas route owns a distinct `THREE.Scene`,
so writers in separate routes are not writers in the live twin. The live twin is
`web/app/components/scene/SalishScene.tsx`. Separate routes are the four sandbox
and workbench scenes under `web/app/(sandbox)/**` and `web/app/workbench/**`.

| file:line | scene graph | kind | note |
| --- | --- | --- | --- |
| `SalishScene.tsx:911` | live twin | WRITE | the one true writer, set inside OrcaRig's effect |
| `SalishScene.tsx:913` | live twin | RESTORE | conditional restore of the prior value in cleanup, guarded by identity `=== env.pmremEnvironment`, not a second independent writer |
| `WorkbenchScene.tsx:163` | workbench route | write | separate scene, separate Canvas |
| `WorkbenchScene.tsx:169` | workbench route | restore | separate scene |
| `OrcaSandboxScene.tsx:95` | orca sandbox route | write | separate scene |
| `OrcaSandboxScene.tsx:104` | orca sandbox route | restore (to null) | separate scene |
| `SliceScene.tsx:165` | slice sandbox route | write | separate scene, not the homepage SliceRig |
| `SliceScene.tsx:171` | slice sandbox route | restore | separate scene |
| `ReenactmentSandboxScene.tsx:213` | reenactment sandbox route | write | separate scene |
| `ReenactmentSandboxScene.tsx:219` | reenactment sandbox route | restore | separate scene |
| `OMAT-R_shading.md:116` | docs | not code | markdown research note |

Within the live twin scene graph `SalishScene.tsx`, the assignment scan returns
exactly two lines, 911 and 913. Line 911 is the single write. Line 913 is a
restore of the captured `prev` inside the same effect cleanup, gated by
`scene.environment === env.pmremEnvironment`, so it only un-sets the value this
same effect set, and only if no later owner replaced it. A restore of a saved
prior value is not a second independent writer. Single-writer count in the live
twin is therefore exactly one, `OrcaRig` at `SalishScene.tsx:911`.

### CMD 1 and CMD 3 confirm no hidden read-write

Every other `scene.environment` occurrence inside `SalishScene.tsx` from CMD 1 and
CMD 3 is a read or a comment, not a write.

```
SalishScene.tsx:906:  // R03 env seam (E6): ... assign the WFX PMREM as scene.environment ...   (comment)
SalishScene.tsx:910:    const prev = scene.environment;                                        (READ, save prior)
SalishScene.tsx:911:    scene.environment = env.pmremEnvironment;                              (WRITE, the one writer)
SalishScene.tsx:913:    if (scene.environment === env.pmremEnvironment) scene.environment = prev;(READ guard + RESTORE)
SalishScene.tsx:993:  // ... scene.fog, or scene.environment -- SkyRig / FogTuneRig / OrcaRig ... (comment)
SalishScene.tsx:1002: // ... assigned to scene.environment, so OrcaRig remains the lone writer ... (comment)
SalishScene.tsx:1149: // ... it is NEVER assigned to scene.environment (OrcaRig is ...            (comment)
SalishScene.tsx:1450: // ... lit by the live twin (SkyRig sky, OrcaRig scene.environment) ...      (comment)
SalishScene.tsx:1467: // ... touches the water material, scene.fog, or scene.environment ...       (comment)
SalishScene.tsx:1643: // ... scene.environment (SEAM 4). worldUnitsPerMeter is the live fit ...    (comment)
```

The slice consumer code in `SliceRig` has no `scene.environment` assignment. Its
only env touch is line 1152 to 1162, the second `makeRealWfxEnv` useMemo, and line
1163, the dispose effect. It feeds that env into `createOrcaPool({ env })` at line
1342 only. So the grep proves the slice never writes `scene.environment` and
`OrcaRig` is the sole writer.

AST note. The token search above is sufficient because `scene.environment` is the
only member-write surface. Any write must be a `MemberExpression` assignment whose
property is `environment` on the scene. CMD 2's `\.environment\s*=` regex catches
exactly those assignment shapes, and the only scene object that receives them in
the live twin is the `useThree((s) => s.scene)` scene at `SalishScene.tsx:886`.
There is no aliased write such as `const s = scene; s.environment = ...`, and no
`Object.assign(scene, ...)` against environment anywhere in the CMD 1 surface.

Invariant proof verdict. Exactly one `scene.environment` writer in the live twin,
`OrcaRig` at `SalishScene.tsx:911`, plus an identity-guarded restore at line 913.
Grep-proven, not asserted.

---

## 4. Lifecycle contract for the published handle after consolidation

After consolidation ORCA publishes the live `WfxEnvHandle` that `OrcaRig` already
builds at `SalishScene.tsx:894` to 904, and the slice borrows it for the pool
instead of baking a second PMREM. The contract below is what that published-handle
accessor must honor.

### 4.1 Validity window

The handle is valid from the moment `OrcaRig`'s env memo produces it until
`OrcaRig`'s env-write effect cleanup disposes it.

- Built at `SalishScene.tsx:894` to 904, `useMemo<WfxEnvHandle>(() => makeRealWfxEnv({...}), [gl, sun])`.
- Becomes live (assigned to `scene.environment`) at the effect setup, line 909 to 911.
- Freed at the effect cleanup, line 912 to 915, where line 914 calls `env.dispose?.()`.

So the published texture is GPU-valid for the whole interval between OrcaRig env
memo creation and OrcaRig env-write effect cleanup. The accessor must report the
handle as present only inside this window and must clear it on dispose, matching
the charter's locked decision 2 (valid after build, cleared on dispose).

### 4.2 Ownership and the sole disposer

`OrcaRig` is the producer and the SOLE disposer. The published handle is owned by
OrcaRig and freed only at `SalishScene.tsx:914`. The slice is a BORROWER. After
consolidation the slice must NEVER call `dispose` on the borrowed handle. Concretely
the slice's current free site, the dispose effect at `SalishScene.tsx:1163`
(`useEffect(() => () => env.dispose?.(), [env])`), must be removed together with the
slice's own `makeRealWfxEnv` memo at lines 1152 to 1162. If the slice kept calling
`env.dispose?.()` on a borrowed handle it would free the texture OrcaRig still owns
and still has assigned to `scene.environment`, which is exactly the double-free the
charter forbids.

### 4.3 Dispose-order hazard and how stable the trigger is

The hazard is a disposed-texture read. If the published handle's identity changes
or OrcaRig unmounts while the slice pool still holds `material.envMap = oldTexture`,
the next rendered frame samples a freed texture.

How likely is the env memo to recompute at runtime. The memo deps are `[gl, sun]`.

- `gl` is `useThree((s) => s.gl)`, `SalishScene.tsx:887`. The R3F renderer is created
  once per Canvas and is stable for the canvas lifetime. It does not change between
  frames or on prop changes. So `gl` does not trigger a recompute at runtime.
- `sun` is `useScenicSun()`, defined at `SalishScene.tsx:709` to 711 as
  `useMemo(() => makeSun(SCENE_TIME, 48.5, -123), [])` with an EMPTY dependency
  array. It is a stable reference for the component's mounted lifetime. So `sun`
  does not change at runtime either.

Therefore in a steady production session the env memo never recomputes, and the
published handle identity is stable for the OrcaRig mount lifetime. Runtime
recompute risk is effectively zero.

The real triggers that DO change identity or run the disposer are mount-lifecycle
events, not runtime dep churn.

- React Strict Mode is enabled, `web/next.config.mjs:3`, `reactStrictMode: true`.
  In development React double-invokes effects as setup, cleanup, setup. OrcaRig's
  env-write effect cleanup at line 914 calls `env.dispose?.()` during the simulated
  unmount, freeing `target.texture`, then a fresh handle is built on the second
  mount. A borrower that cached the first texture now points at a disposed texture.
  This is the concrete development-time manifestation of the hazard.
- Fast Refresh / HMR while editing scene modules unmounts and remounts OrcaRig and
  rebuilds the handle the same way.
- Any future change that makes OrcaRig conditional, or that adds a real dep to the
  env memo, would recompute the handle at runtime and free the old texture.

Mitigation the contract must require. The accessor must expose handle IDENTITY, not
just the texture, and the slice must react to identity change.

- The slice reads the published handle each render and treats a new handle identity
  as a re-key. On identity change it must either rebuild the pool, which already
  threads `env` through its build path, or push the new handle into the live
  controllers and materials via the existing `OrcaController.setEnv`
  (`OrcaController.ts:164` to 166) which calls `matHandle.setEnv`
  (`orcaMaterial.ts:140` to 146) and re-points `material.envMap` to the new texture.
- The slice must never sample a frame against a texture from a stale handle
  identity. Since `gl` and `sun` are runtime-stable, in production the handle does
  not change mid-session, so the re-key path is the development and HMR safety net
  plus future-proofing, and it is cheap because identity equality is the only check
  per render.

### 4.4 Mount ordering guarantee

`OrcaRig` is unconditional and mounts before, and outlives, the conditional
`SliceRig` in normal flow.

- `OrcaRig` is rendered unconditionally at `SalishScene.tsx:1633`,
  `<OrcaRig worldUnitsPerMeter={scenicWorldUnitsPerMeter} />`.
- `SliceRig` is rendered only when a station is selected, `SalishScene.tsx:1645`,
  `{selectedStation && (<SliceRig .../>)}`, sibling and AFTER OrcaRig in source
  order.

Two guarantees follow. First, sibling source order places OrcaRig's subtree before
SliceRig's, so on initial commit OrcaRig's env exists before SliceRig mounts and can
read the published handle. Second, SliceRig is gated on `selectedStation`, so it
mounts only on station select and unmounts on deselect, while OrcaRig stays mounted
across those transitions. The only way OrcaRig unmounts is the whole fragment
unmounting, which also unmounts SliceRig. So OrcaRig cannot be torn down while
SliceRig alone survives. In a full-tree unmount no frame is rendered between the two
cleanups, so even if OrcaRig's env free runs before SliceRig's pool teardown there
is no frame that samples the freed texture. The partial case that would be unsafe,
OrcaRig unmounting alone, is structurally impossible given the unconditional mount.

For completeness on OrcaRig's own two effects. The env-write effect is defined first
(lines 909 to 916), the controller-build effect second (lines 926 to 959, deps
`[env, worldUnitsPerMeter]`). React runs cleanups in reverse declaration order, so
on unmount the controller cleanup (line 949 to 958, `c.dispose()`, which does not
touch env) runs before the env free at line 914. So OrcaRig already tears down its
own consumers before freeing its own texture. The slice must adopt the same order
relative to the borrowed handle, teardown of pool consumers before any handle
release, except the slice releases nothing because it is a borrower.

---

## 5. Recommended rules for ENV-B and ENV-INT, and what ENV-ADV must verify

### ENV-B (implement the ORCA-owned accessor)

1. Publish the live handle plus its identity through an ORCA-owned accessor or
   shared ref. Expose enough for a borrower to detect a new identity, for example
   the handle object reference itself, so a `===` check re-keys the consumer.
2. Keep `dispose` defined on exactly the producer's handle and document that
   borrowers must not call it. Do not widen the optional `dispose` into something a
   borrower would invoke.
3. Do not change when or how OrcaRig builds env. The accessor is additive. The
   validity window stays exactly lines 894 to 915 of `SalishScene.tsx`.
4. If `OrcaPool` needs to accept a re-keyable handle, prepare that input shape so a
   handle-identity change drives a controller `setEnv` or a pool rebuild, without
   editing `SalishScene.tsx` yet.

### ENV-INT (single-editor convergence in SalishScene.tsx)

1. Remove the slice's second bake, the `makeRealWfxEnv` memo at lines 1152 to 1162,
   and remove the slice's free site, the dispose effect at line 1163. The slice
   stops owning a texture.
2. Wire `SliceRig` to read OrcaRig's published handle and pass it into
   `createOrcaPool({ env })` at line 1342. Add the published handle identity to the
   pool effect deps so an identity change re-keys the pool. The pool effect deps are
   currently `[authority, env, station.lat, station.lng, worldUnitsPerMeter, demoCount]`
   at line 1375, where `env` was the slice's own memo. Replace that `env` with the
   published handle so the same re-key path now follows the producer.
3. Never call `dispose` on the borrowed handle anywhere in `SliceRig`.
4. Keep exactly one `scene.environment` writer. Do not add any assignment to
   `scene.environment` in the slice. Re-run the CMD 2 grep after the edit and confirm
   the live-twin assignment set is still only lines 911 and 913.

### ENV-ADV (adversarial verification)

1. Re-run the section 3 grep and confirm exactly one live-twin writer at line 911
   plus the guarded restore at 913, and zero `scene.environment` writes inside
   `SliceRig`.
2. Confirm the slice no longer calls `makeRealWfxEnv` and no longer calls
   `env.dispose?.()`. One free site only, OrcaRig line 914.
3. Verify no disposed-texture read across the lifecycle transitions, station select,
   station deselect, full unmount, and the Strict Mode and HMR double-mount, by
   confirming the handle-identity re-key path drives `OrcaController.setEnv` or a
   pool rebuild so `material.envMap` is never left pointing at a freed texture.
4. Verify no double free, the borrowed handle is freed exactly once by OrcaRig, and
   confirm one fewer PMREM bake at slice mount.

---

## Executive summary

Texture ownership. In both `makeRealWfxEnv` (`realWfxEnv.ts:59`, `:83`, `:93-96`)
and `makeSandboxWfxEnv` (`wfxEnv.ts:102`, `:107`, `:124-126`) the published
`pmremEnvironment` is the PMREM render target's `target.texture`, owned by that
target and freed only by the handle's own `dispose()`. No consumer frees it.
`OrcaController.dispose`, `makeOrcaMaterial.dispose`, `makeOrcaEyes.dispose`, and
`OrcaPool.dispose` all only reference `material.envMap`, and three's
`Material.dispose` does not dispose `envMap`. Today the slice texture is freed only
at `SalishScene.tsx:1163` and OrcaRig's only at `SalishScene.tsx:914`.

Single-writer proof. Grep-proven, not asserted. `rg -n "\.environment\s*=" web/`
returns one write in the live twin, `SalishScene.tsx:911`, plus an
identity-guarded restore at `:913`. All other writes are in separate sandbox and
workbench scene graphs. Live-twin `scene.environment` writer count is exactly one,
`OrcaRig`.

Validity window. The published handle is valid from OrcaRig's env memo build
(`SalishScene.tsx:894-904`) until OrcaRig's env-write effect cleanup
(`:914`). OrcaRig is the sole owner and sole disposer. The slice borrows and must
never dispose it.

Key hazard and mitigation. A disposed-texture read if the handle is freed while the
pool still holds `material.envMap = oldTexture`. The env memo deps `[gl, sun]` are
both runtime-stable (`gl` is the stable R3F renderer, `sun` is an empty-dep memo at
`:709-711`), so runtime recompute risk is near zero, but `reactStrictMode: true`
(`next.config.mjs:3`), Fast Refresh, and a full unmount do dispose and rebuild the
handle. Mitigation contract. The slice borrows by identity, never disposes, and
re-keys on handle-identity change by rebuilding the pool or calling
`OrcaController.setEnv`. Mount order is safe because OrcaRig is unconditional at
`:1633` and outlives the `selectedStation`-gated `SliceRig` at `:1645`, so OrcaRig
can never be torn down while only the slice survives.
