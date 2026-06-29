# ENV-R2 findings: slice consumer of the WfxEnvHandle

- Role: ENV-R2 (read-only research, BSWR-ENV lane)
- Owns: this file only. No source edited.
- Repo state grounded against charter `repo_state_verified_against` 61ba1d69ee36cf605f7ba741bdaa1defa8762834.
- Question: how does SliceRig feed createOrcaPool today, and what is the minimal slice-side change to consume a published live WfxEnvHandle from ORCA instead of baking a second PMREM via makeRealWfxEnv.

## 1. Exact data flow today (env memo to material)

The slice builds its own handle and threads it down four hops into the pool materials.

Hop 1. SliceRig builds the handle with a `useMemo<WfxEnvHandle>` that calls `makeRealWfxEnv`.

```1152:1163:web/app/components/scene/SalishScene.tsx
  const env = useMemo<WfxEnvHandle>(
    () =>
      makeRealWfxEnv({
        renderer: gl,
        sunDirection: sun.direction,
        sunColor: sun.color,
        sunIntensity: sun.intensity,
        waterLevelY: SEA_LEVEL_Y,
      }),
    [gl, sun],
  );
  useEffect(() => () => env.dispose?.(), [env]);
```

Hop 2. Inside the presence-gated reenactment `useEffect`, the slice passes that `env` into `createOrcaPool`.

```1342:1348:web/app/components/scene/SalishScene.tsx
      pool = createOrcaPool({
        env,
        bounds: TILESET_BOUNDS,
        sceneDepth: SCENE_DEPTH,
        worldUnitsPerMeter: worldUnitsPerMeter ?? 1,
        depthScale: 1,
      });
```

That effect lists `env` in its dependency array.

```1375:1375:web/app/components/scene/SalishScene.tsx
  }, [authority, env, station.lat, station.lng, worldUnitsPerMeter, demoCount]);
```

Hop 3. `createOrcaPool` stores `opts.env` and threads it into each per-instance `createOrcaController` call inside `setSpawn`.

```78:88:web/lib/scene/reenactment/OrcaPool.ts
  async function setSpawn(record: ReenactmentSpawnRecord): Promise<void> {
    clearPool();
    const built = await Promise.all(
      record.instances.map(async (spec) => {
        const controller = await createOrcaController({
          env: opts.env,
          motionUrl: REAL_SRKW_MOTION_URL, // ALWAYS the real SRKW driver
          worldUnitsPerMeter: wupm,
          depthScale,
          timeScale: 1,
        });
```

Hop 4. `createOrcaController` reads `opts.env` in exactly two builders, `makeOrcaMaterial` and `makeOrcaEyes`.

```75:83:web/lib/scene/orca/OrcaController.ts
  const matHandle: OrcaMaterialHandle = makeOrcaMaterial({
    map: sourceMaterial.map,
    normalMap: sourceMaterial.normalMap,
    env: opts.env,
  });

  const rig = buildOrcaRig(geometry, matHandle.material, DEFAULT_LIMITS);

  const eyes: OrcaEyesHandle = makeOrcaEyes({ headBone: rig.bones.head, env: opts.env });
```

What the pool actually consumes from the handle. The material reads four fields and nothing else. It assigns `env.pmremEnvironment` as the `envMap` and clones the three underwater fields into shader uniforms.

```61:66:web/lib/scene/orca/materials/orcaMaterial.ts
  if (env.pmremEnvironment) material.envMap = env.pmremEnvironment;

  // Underwater uniforms shared into the patched shader.
  const uAbsorption = { value: env.underwater.absorption.clone() };
  const uInScatter = { value: env.underwater.inScatterColor.clone() };
  const uWaterLevelY = { value: env.underwater.waterLevelY };
```

The eyes read one field, `env.pmremEnvironment`, as the cornea `envMap`.

```62:62:web/lib/scene/orca/eyes/orcaEyes.ts
  if (opts.env.pmremEnvironment) corneaMat.envMap = opts.env.pmremEnvironment;
```

So the pool consumes only `pmremEnvironment`, `underwater.absorption`, `underwater.inScatterColor`, and `underwater.waterLevelY`. The handle fields `sunDirection`, `sunColor`, `sunIntensity`, and `underwater.visibility` are NOT read anywhere on the pool path. Note that the material clones the underwater fields once at build time and the eyes copy the texture reference once, so the pool binds to whatever handle it was handed at spawn and does not re-read it per frame. There is no live tracking of env changes on this path, only `setEnv` exists for that and the pool never calls it.

## 2. Are the two makeRealWfxEnv option sets identical

Yes. OrcaRig and SliceRig pass the same five inputs from the same sources.

OrcaRig call.

```894:904:web/app/components/scene/SalishScene.tsx
  const env = useMemo<WfxEnvHandle>(
    () =>
      makeRealWfxEnv({
        renderer: gl,
        sunDirection: sun.direction,
        sunColor: sun.color,
        sunIntensity: sun.intensity,
        waterLevelY: SEA_LEVEL_Y,
      }),
    [gl, sun],
  );
```

SliceRig call is the same five fields (cited above at lines 1152 to 1162).

Field-by-field equivalence.

- `renderer: gl`. Both read `gl` from `useThree((s) => s.gl)`, OrcaRig at line 887, SliceRig at line 1143. Same live renderer.
- `sun.direction`, `sun.color`, `sun.intensity`. Both read `useScenicSun()`, OrcaRig at line 889, SliceRig at line 1145. That hook is `useMemo(() => makeSun(SCENE_TIME, 48.5, -123), [])` at line 710, so each component instance gets a distinct object with byte-identical numeric content (same time, same lat, same lng). The values are equal even though the object references differ per instance.
- `waterLevelY: SEA_LEVEL_Y`. `SEA_LEVEL_Y = 0` at line 174. Same constant in both.
- `visibility`. Neither call passes it, so both fall to the `makeRealWfxEnv` default of 1.5 (`web/lib/scene/wfx/realWfxEnv.ts:91`). Same default, and unused on the pool path anyway.

`makeRealWfxEnv` derives its absorption and in-scatter from module constants `PROPOSED_RGB_EXTINCTION`, `WATER_TUNED_DEEP`, `WATER_TUNED_SHALLOW` (`web/lib/scene/wfx/realWfxEnv.ts:69-80`), not from any per-call input, so those underwater fields are identical between the two handles by construction.

Conclusion. The OrcaRig handle is a valid byte-equivalent drop-in for the slice handle on every field the pool reads. No difference flagged. The only behavioral difference between the two call sites is what OrcaRig does AFTER building, it assigns the handle to `scene.environment` (lines 909 to 916) and the slice does not. That difference is outside the handle and is preserved by the planned change (see section 6).

## 3. Minimal slice-side change to consume a published handle

The mechanical change is the same regardless of accessor shape. Replace the local bake with a read of the published handle, gate the spawn on the handle being ready, and stop owning disposal. The accessor shape that ENV-R1 recommends only changes how the slice obtains the handle reference and how it subscribes to readiness.

### 3a. Replace the bake and its dispose

- Remove the `useMemo<WfxEnvHandle>(() => makeRealWfxEnv(...), [gl, sun])` at lines 1152 to 1162.
- Remove the dispose effect `useEffect(() => () => env.dispose?.(), [env])` at line 1163. The slice must not dispose a handle ORCA owns (section 5).
- Replace both with a read of the published handle. The shape depends on ENV-R1.

Option A, module-level ref or accessor function. The slice imports an ORCA-owned reader, for example `getPublishedWfxEnv()` from `web/lib/scene/orca`, and resolves the current handle plus a readiness flag. Because the handle becomes available asynchronously after OrcaRig mounts and builds, the slice needs a readiness signal it can put in React state, not just a bare module read, otherwise the spawn effect will not re-run when the handle arrives. This pairs a module accessor with a subscribe or a polled `useState`.

Option B, React context. ORCA provides a `WfxEnvContext` and the slice reads `const env = useContext(WfxEnvContext)`. The context value is `null` until OrcaRig publishes, then the provider re-renders consumers with the handle. This gives the slice a natural readiness signal (the value flips from null to the handle) and the spawn effect can depend on it directly. This is the cleanest fit for the existing slice pattern because it mirrors how `authority` already gates the spawn.

Option C, prop drilled from a common parent. A parent that mounts both OrcaRig and SliceRig holds the handle and passes it as a `wfxEnv` prop. This requires the parent to learn the handle from ORCA, so it still needs one of A or B underneath, and it widens the SliceRig prop surface. Least minimal of the three.

ENV-R1 owns the accessor-shape recommendation. ENV-R2 recommendation for the consumer, independent of shape: the slice needs a readiness value that lives in React state (a context value flipping from null to handle, or a `useState` fed by an accessor subscription), so the spawn effect re-runs when ORCA's handle appears. A bare synchronous module read is insufficient on its own because the slice spawn effect must react to readiness.

### 3b. The spawn effect dependency

Today the effect depends on `env` (line 1375). After the change, replace `env` with the published-handle value or its readiness signal.

- Option B (context): depend on the context handle value directly, for example `[authority, wfxEnv, station.lat, station.lng, worldUnitsPerMeter, demoCount]`, where `wfxEnv` is the context value that is null until ready.
- Option A (accessor plus useState readiness): depend on the readiness state value, for example a `wfxEnvReady` handle held in `useState`.

Either way the dependency stays a single value that changes when the handle becomes available, so the effect re-runs and spawns once the handle is live. Keep the other deps unchanged.

### 3c. If the published handle is null when the slice wants to spawn

The slice already gates the spawn on `authority` with an early return.

```1307:1309:web/app/components/scene/SalishScene.tsx
  useEffect(() => {
    if (!authority) return;
    let alive = true;
```

Mirror that for the handle. Add a guard `if (!authority || !wfxEnv) return;` at the top of the spawn effect and put the handle in the dep array. When OrcaRig has not yet built and published its handle, the slice does nothing, the same way it does nothing before the timeline authority exists. When the handle arrives the effect re-runs and spawns the pool lit by ORCA's single bake. This adds no new spawn path, it extends the existing readiness gate by one term.

## 4. Does OrcaPool need any change

No. OrcaPool is already env-agnostic. Its input is a plain `WfxEnvHandle` and it only forwards `opts.env` into `createOrcaController`.

```26:32:web/lib/scene/reenactment/OrcaPool.ts
export interface OrcaPoolOptions {
  env: WfxEnvHandle;
  bounds: HeightmapBounds;
  sceneDepth: number;
  worldUnitsPerMeter: number;
  depthScale?: number;
}
```

The pool never builds, never inspects beyond passing it through, and never disposes the env. ORCA's published handle satisfies the `WfxEnvHandle` type, so the pool accepts it unchanged. The wave_shape says ENV-B2 edits OrcaPool only if the pool input needs adapting. Per this trace the input does not need adapting. The env stays a plain `WfxEnvHandle` passed in, so ENV-B2 should be a no-op on OrcaPool unless ENV-Q decides to fold readiness or ownership semantics into the pool API, which this trace does not require.

## 5. Disposal and the ownership flip

Today the slice owns and disposes its handle (`useEffect(() => () => env.dispose?.(), [env])` at line 1163). After consuming ORCA's handle the slice must NOT dispose it, because OrcaRig owns it and frees it on its own unmount.

OrcaRig is the owner and disposer.

```909:916:web/app/components/scene/SalishScene.tsx
  useEffect(() => {
    const prev = scene.environment;
    scene.environment = env.pmremEnvironment;
    return () => {
      if (scene.environment === env.pmremEnvironment) scene.environment = prev;
      env.dispose?.();
    };
  }, [scene, env]);
```

Removing the slice dispose is safe because the pool never disposes the env. The pool dispose path only disposes controllers.

```70:76:web/lib/scene/reenactment/OrcaPool.ts
  function clearPool() {
    for (const p of pooled) {
      group.remove(p.wrapper);
      p.controller.dispose();
    }
    pooled = [];
  }
```

```134:136:web/lib/scene/reenactment/OrcaPool.ts
    dispose() {
      clearPool();
    },
```

The controller dispose disposes eyes, mouth, material, and rig, and nothing else.

```168:173:web/lib/scene/orca/OrcaController.ts
    dispose() {
      eyes.dispose();
      mouth.dispose();
      matHandle.dispose();
      rig.dispose();
    },
```

The material dispose disposes the material only, not the env texture.

```147:149:web/lib/scene/orca/materials/orcaMaterial.ts
    dispose() {
      material.dispose();
    },
```

The eyes dispose disposes the eye geometry and cornea material and removes the group, not the env texture.

```121:125:web/lib/scene/orca/eyes/orcaEyes.ts
    dispose() {
      eyeGeo.dispose();
      corneaMat.dispose();
      opts.headBone.remove(group);
    },
```

So `env.pmremEnvironment` is the texture from the PMREM render target that `makeRealWfxEnv` allocates, and only `WfxEnvHandle.dispose()` frees it (`web/lib/scene/wfx/realWfxEnv.ts:93-96`). Nothing on the pool path calls that. The ownership flip is therefore clean: the slice stops calling `env.dispose?.()`, OrcaRig keeps calling it on its own unmount, and the pool keeps reading a live texture for as long as OrcaRig is mounted.

Ownership lifetime caveat for ENV-Q and ENV-ADV. After the flip the pool texture lifetime is tied to OrcaRig, not to the slice. If OrcaRig can unmount while the slice pool is still mounted, the pool would read a disposed texture. In the current tree both rigs are part of the same live twin mount, so this is a lifecycle invariant to assert rather than a code change here. ENV-R3 owns the disposal-order audit and ENV-R4 owns the disposed-texture failure mode. Flagged for them, not resolved here.

## 6. Minimal diff surface for the future INT wave

All slice edits land in `web/app/components/scene/SalishScene.tsx` inside SliceRig, done by the single ENV-INT editor. The exact touch points:

- Lines 1152 to 1162: delete the `useMemo<WfxEnvHandle>(() => makeRealWfxEnv(...))` bake. Replace with the published-handle read per the ENV-R1 accessor shape.
- Line 1163: delete the dispose effect `useEffect(() => () => env.dispose?.(), [env])`. The slice no longer owns the handle.
- Line 1308: extend the spawn guard from `if (!authority) return;` to also gate on the handle, for example `if (!authority || !wfxEnv) return;`.
- Line 1342: the `createOrcaPool({ env, ... })` call stays structurally identical, it just passes the published handle reference instead of the local memo. Local rename only.
- Line 1375: in the dep array swap `env` for the published-handle value or readiness signal. Keep the other five deps.

Untouched by ENV. OrcaRig (lines 885 to 978) is not edited, in particular its `makeRealWfxEnv` bake at lines 894 to 904 and its `scene.environment` write at lines 909 to 916 are unchanged. There remains exactly one `scene.environment` writer, OrcaRig. ENV removes a second BAKE, never a second writer. OrcaPool.ts and OrcaController.ts need no change for the slice to consume the handle.

---

## Executive summary

The slice today bakes its own `WfxEnvHandle` in SliceRig via `makeRealWfxEnv` at `SalishScene.tsx:1152-1162`, owns its disposal at line 1163, and threads it through `createOrcaPool({env})` at line 1342 into per-instance `createOrcaController`, where only `pmremEnvironment` and the three `underwater` fields are read by `makeOrcaMaterial` and `makeOrcaEyes`. The slice and OrcaRig pass byte-identical options to `makeRealWfxEnv` (same `gl`, same numeric `useScenicSun` output, same `SEA_LEVEL_Y`, same default visibility), so ORCA's published handle is a valid drop-in. The minimal slice change is to delete the bake at 1152-1162 and the dispose effect at 1163, read ORCA's published handle instead, extend the spawn guard at line 1308 to also require the handle (`if (!authority || !wfxEnv) return;`), swap `env` for the handle or its readiness signal in the dep array at line 1375, and keep the `createOrcaPool` call at 1342 structurally identical. OrcaPool needs no adapting, it is already env-agnostic and takes a plain `WfxEnvHandle`, so ENV-B2 is effectively a no-op on the pool. The disposal ownership flips: the slice stops calling `env.dispose?.()` and OrcaRig keeps owning and freeing the texture, which is safe because the pool dispose path only disposes controllers, eyes, mouth, material, and rig, never the env texture. OrcaRig stays untouched, including its lone `scene.environment` write at lines 909-916, so the single-writer invariant holds.
