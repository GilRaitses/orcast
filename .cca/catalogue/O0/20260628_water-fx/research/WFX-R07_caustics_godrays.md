# WFX-R07 caustics and god-rays

Role WFX-R07, read-only research, WATER-FX Wave 1.
Owns this one file only. No code changed.
Honesty label holds: modeled, not measured. All perf numbers in this doc are
estimated from shader and pass structure, not measured, because the research
wave runs with no dev server and no build.

Topic: surface caustics projected on the seabed plus volumetric light shafts
(god-rays), both for the top-down/orbit view and for a future underwater dive
view. Survey of cheap versus accurate options, with a clear recommendation and a
budget-cut call.

## 1. Scope and current state, file-cited

What the twin renders today and what it does not.

The water surface is hand-written GLSL on `three` with a depth pre-pass. The
factory is `makeWater2` in `web/lib/scene/water2/depthWater.ts`. It already
reconstructs the seabed world position from the opaque-scene depth texture and
the inverse view-projection matrix, then derives a vertical water column
thickness:

```236:243:web/lib/scene/water2/depthWater.ts
    } else {
      vec4 ndc = vec4(uv * 2.0 - 1.0, sceneDepth * 2.0 - 1.0, 1.0);
      vec4 worldH = uInverseViewProjection * ndc;
      vec3 seabed = worldH.xyz / worldH.w;
      // Vertical water column from the surface plane down to the seabed. Terrain
      // at/above the surface yields <= 0 -> the water clears and land shows.
      column = uWaterLevel - seabed.y;
    }
```

The shader already has a Beer-Lambert column term, a sun-direction uniform, a
surface normal, and noise helpers. It computes `seabed.xyz` as an intermediate
and then discards everything but `seabed.y`. That discarded `seabed.xz` is the
exact hook a projected caustic would need, at zero extra cost.

```276:282:web/lib/scene/water2/depthWater.ts
    vec3 sun = normalize(uSunDirection);
    vec3 halfVec = normalize(sun + viewDir);
    float ndh = max(dot(n, halfVec), 0.0);
    float spec = pow(ndh, 90.0);
    float glitter = pow(ndh, 600.0) *
      step(0.55, noise(vPlanePos * 7.0 + vec2(uTime * 0.9, -uTime * 0.7)));
    float diff = clamp(dot(n, sun), 0.0, 1.0);
```

The sun direction comes from `makeSun` in
`web/app/components/scene/realism/sun.ts`, which returns a unit vector toward the
sun in scene frame and a solar elevation in degrees. Elevation drives intensity
and color, and is floored a few degrees above the horizon so the light never lies
flat along the ground.

```133:151:web/app/components/scene/realism/sun.ts
  const eUse = Math.max(elevationDeg, 4) * DEG;
  const aR = azimuthDeg * DEG;
  const direction = new THREE.Vector3(
    Math.cos(eUse) * Math.sin(aR),
    Math.sin(eUse),
    -Math.cos(eUse) * Math.cos(aR),
  ).normalize();
```

Render pipeline facts that bound this topic.

- The live scene renders directly to screen through react-three-fiber. There is
  no `EffectComposer`, no postprocessing pass, and no `toneMapping` set. A grep
  for `postprocessing`, `EffectComposer`, `UnrealBloom`, `ShaderPass` across
  `web/` returns nothing.
- The depth pre-pass already costs one full opaque scene render every frame. It
  is driven from `SalishScene.tsx`:

```319:323:web/app/components/scene/SalishScene.tsx
    const handle = handleRef.current;
    if (!handle) return;
    handle.renderDepthPrepass(gl, scene, camera as THREE.PerspectiveCamera);
    handle.update(state.clock.elapsedTime, camera);
```

- The default camera is an orbit/top-down view, positioned high above the water
  at roughly Y 28 with the water plane at Y 0, near 1, far 800.

```1008:1008:web/app/components/scene/SalishScene.tsx
        camera={{ position: [0, 28, 30], fov: 45, near: 1, far: 800 }}
```

- The seabed is the modeled CUDEM topobathy terrain. The water2 comments note
  that deep channels run only about 1.0 scene unit below the surface in this
  twin, so the on-screen water column is shallow in scene units and the camera is
  far from it.
- The underwater module `web/lib/scene/underwater/` and the post module
  `web/lib/scene/post/` do not exist yet. Both globs return zero files. They are
  the future homes for WFX-R08 W4 underwater work and a W5 post stack.
- `web/package.json` pins `three@^0.169.0` with `three-mesh-bvh@0.9.10` and no
  postprocessing dependency. The renderer is the default WebGL renderer, not
  WebGPU.

The honest framing this sets up: in the default above-water orbit view there is
no underwater medium on screen and no sun disk in frame, so god-rays have nothing
to scatter through and nothing to radiate from, and projected seabed caustics
would be sub-pixel detail seen through a thin, turbid column from far away. Both
effects only earn their cost inside a future underwater dive view.

## 2. Technique survey with URLs

### 2a. Projected caustic texture

Idea: precompute or author an animated tiling caustic pattern and project it
along the sun direction onto the seabed, attenuated by water depth. This is the
standard cheap game approach. It is modeled light, not computed refraction.

- `three` WebGPU `ProjectorLight` projects a `.map` or a procedural TSL node
  inside a spotlight cone, and the official demo uses a Worley-noise caustic
  node. This is the cleanest built-in path, but it is WebGPU only.
  https://threejs.org/docs/pages/ProjectorLight.html
  https://github.com/mrdoob/three.js/pull/31022
  Demo source:
  https://github.com/mrdoob/three.js/blob/dev/examples/webgpu_lights_projector.html
- The widely-copied WebGL pattern for animated caustics is two scrolling samples
  of a caustic texture multiplied together to break the tiling, tinted and added
  to the lit surface. Reference write-ups and the classic look:
  https://medium.com/@martinRenou/real-time-rendering-of-water-caustics-b99a36c33013
  https://www.shadertoy.com/view/MdlXz8 (Caustics, Dave Hoskins / TDM)
- Computed (accurate) caustics render a caustic intensity map by tracing the
  refraction of the surface mesh onto a receiver, then sample that map on the
  seabed. This is the martinRenou approach above. It needs an extra render pass
  and is far more than this turbid, far-camera scene can justify.

### 2b. Screen-space god-rays (radial blur from the sun)

Idea: estimate occlusion of the light source per pixel by summing samples along a
screen-space ray toward the sun position, then radial-blur the bright pixels.
This is the GPU Gems 3 chapter 13 post-process, the cheapest god-ray family.

- NVIDIA GPU Gems 3 chapter 13, volumetric light scattering as a post-process:
  https://developer.nvidia.com/gpugems/gpugems3/part-ii-light-and-shadows/chapter-13-volumetric-light-scattering-post-process
- `three` ships a WebGL example of exactly this, `GodRaysPass` built on
  `EffectComposer`:
  https://github.com/mrdoob/three.js/blob/master/examples/webgl_postprocessing_godrays.html
- Hard requirement: the sun must be on screen and partly occluded by a darker
  silhouette for the radial blur to read. In a top-down water view the sun is not
  in frame, so this technique produces nothing useful there.

### 2c. Raymarched volumetric shafts

Idea: march the view ray through a participating medium, accumulating in-scatter
weighted by whether each step is lit or shadowed. This is the accurate light-shaft
look for an underwater dive view.

- `three-good-godrays`, screen-space raymarched god-rays on the pmndrs
  `postprocessing` library. New dependency, needs shadow maps enabled, recommends
  `PCFSoftShadowMap` or `BasicShadowMap`:
  https://github.com/ameobea/three-good-godrays
- `three` WebGPU `GodraysNode`, the node port of the raymarched effect, WebGPU
  only, also needs a full shadow setup:
  https://threejs.org/docs/pages/GodraysNode.html
  https://github.com/mrdoob/three.js/pull/32888
- A hand-written underwater shaft is the three-only version: in the dive-view
  water fragment, march along the view ray a fixed number of steps, sample a
  noise mask scrolled along the sun direction, and accumulate in-scatter with
  Beer-Lambert falloff. No new dependency, but it is the most expensive option
  per pixel.

## 3. Recommendations with cost and three-only fallback

The renderer is WebGL, so every WebGPU node path (`ProjectorLight`,
`GodraysNode`) is out unless O0 chooses a renderer migration, which is a much
larger decision than this lane should make. The recommendations below are all
three-only WebGL.

### R07-A caustics, recommended, in-shader projected texture

Add an animated caustic brightening term to the seabed read, not a new pass and
not a new light. Two viable hosts:

1. Inside the existing water2 fragment shader, reusing the already-reconstructed
   `seabed.xz` to sample a tiling caustic texture, modulating by the existing
   `column` Beer-Lambert term, by sun diffuse `diff`, and by sun elevation so it
   fades at low sun. This reuses the discarded `seabed.xyz` and the existing
   `uSunDirection`, so the only new work is one or two texture fetches.
2. Inside the W3 seabed material directly, so caustics live with the surface they
   land on. Cleaner ownership, same cost, but it needs the seabed material to
   know the water level and sun. Prefer this if W3 builds a dedicated seabed
   material.

Caustic credibility for turbid water: sample the texture twice at different
scroll speeds and multiply to hide tiling, then attenuate hard with depth so the
pattern is gone within roughly one secchi depth of column. See section 6 and the
honesty note: do not push contrast or this becomes a tropical-reef look that the
charter forbids.

- Estimated cost: under 0.2 ms at 1080p on a desktop discrete GPU, roughly
  0.3 to 0.5 ms on a laptop integrated GPU, for two extra texture fetches plus a
  multiply over the water (or seabed) fragments. No extra render pass. Estimated,
  not measured.
- Asset cost: one tiling caustic texture, 256 or 512 px, as KTX2, roughly 64 to
  256 KB. A single channel is enough since the tint comes from the sun color.
- Three-only fallback if even a texture fetch is unwanted: synthesize the caustic
  from the cheap value `noise()` already in the shader, two layers multiplied.
  Lower quality but zero new asset and almost zero cost.

### R07-B god-rays, recommended action is defer or skip for the default view

For the top-down/orbit view, recommend skip. The sun is not in frame and there is
no on-screen medium, so screen-space god-rays have nothing to act on and a
raymarch would scatter through empty air above the water. Realism-per-ms here is
effectively zero.

If god-rays are wanted at all, scope them to the underwater dive view only and
gate them behind a quality preset:

- Cheapest dive-view option: a hand-written half-resolution radial blur or a
  short raymarch in the underwater fragment, owned by W4, not the default view.
  Estimated 1 to 3 ms at half resolution on desktop, more on a laptop, plus it
  forces an offscreen target because the app currently renders straight to
  screen. Estimated.
- Library option `three-good-godrays`: a new runtime dependency, pmndrs
  `postprocessing` plus the godrays package, and it requires shadow maps which
  the scene does not currently enable. Estimated 2 to 5 ms plus shadow-map cost
  plus bundle growth. This is an O0 dependency decision, not a default.
- Three-only fallback that avoids a composer entirely: a few additive cone or
  quad meshes faking shafts under the surface in the dive view, billboarded to
  the sun. Crude, but cheap and within house style.

### Net recommendation

Ship R07-A caustics as a small term in the W3 seabed or water material, tuned
weak for turbid water. Do not build god-rays for the default view. Defer any
god-ray or volumetric shaft to W4 dive view behind a quality preset, and treat it
as cuttable for the demo. See section 6 for the explicit cut question to O0.

## 4. Frame-budget impact against the existing depth pre-pass

Budget is 16.6 ms per frame at 60fps desktop and 33.3 ms at 30fps laptop. The
depth pre-pass already spends one full opaque scene render inside that budget
every frame, so the headroom for added effects is already reduced before this
topic starts.

- R07-A caustics: no new pass. It rides fragments that already run. It also
  reuses the depth reconstruction the pre-pass already paid for, so it adds no
  geometry and no render target. Estimated marginal cost under 0.5 ms on the
  laptop target. This fits the budget comfortably.
- R07-B screen-space god-rays: needs an `EffectComposer`, which means the main
  scene must render into an offscreen target and then run an occlusion pass and a
  radial-blur pass, then blit to screen. That is a structural change to the
  current direct-to-screen pipeline, and it stacks new fullscreen passes on top
  of the existing depth pre-pass. This is the expensive path and the one most
  likely to break the laptop budget once it is combined with reflections,
  volumetrics, and sky work from the other WFX agents.
- R07-C raymarched shafts: most expensive per pixel. Only acceptable at reduced
  resolution and only in the dive view, where the rest of the frame is cheaper
  because the above-water terrain extent is largely off screen.

Stacking note for WFX-R13: caustics are nearly free and additive to the existing
pre-pass, while any god-ray or shaft option introduces a composer or an extra
render target. The composer is the real budget line item, and it should be
costed once at the W5 post layer rather than charged to this topic alone.

## 5. Collision and sequencing

This topic does not own a convergence file and edits none. It feeds three later
seams.

- W3 world-materials-and-shading owns the seabed material and the water upgrade.
  R07-A caustics belong here. Place the caustic term in the seabed material or in
  `makeWater2`, reusing `seabed.xz`, `column`, and `uSunDirection`. Coordinate
  ownership with the twin W3 seabed-material and water-upgrade agents through O0
  so the caustic term has one owner, not two.
- W4 underwater-and-exploration-modes owns `web/lib/scene/underwater/`, which
  does not exist yet. Any raymarched or radial-blur shaft belongs here, scoped to
  the dive view, and should share the absorption and visibility model that
  WFX-R08 defines so shafts attenuate with the same turbid-green coefficients as
  the fog. Transition continuity runs through
  `web/lib/scene/atmosphere/transition.ts`.
- W5 post owns `web/lib/scene/post/`, which does not exist yet. If a screen-space
  god-ray ever ships, it lands here as a composer pass, and it must be sequenced
  against tonemapping and bloom from WFX-R05 so there is exactly one composer,
  not several competing ones.
- Convergence lock: when any of this later lands in `SalishScene.tsx`, it
  serializes through O0 against W-CAM, W-LABELS, W3, W4, and LGC, per the charter.
  Research touches none of these.

Dependency on sibling research: this doc assumes WFX-R11 supplies the real Salish
optics and WFX-R09 supplies the per-channel absorption coefficients. The caustic
attenuation in R07-A should reuse those exact coefficients rather than inventing
its own depth falloff, so caustics fade on the same curve as the water color.

## 6. Open questions for O0, including the cut question

1. Cut question, primary. Is an underwater dive camera view actually in scope for
   the demo, or is the demo exclusively the top-down/orbit above-water view? If
   the demo never goes underwater, cut god-rays and volumetric shafts entirely
   and keep only R07-A caustics as a weak seabed term. This is the single biggest
   realism-per-ms decision in this topic.
2. Caustic ownership. Should the caustic term live in `makeWater2` or in the new
   W3 seabed material? Recommend the seabed material if W3 builds one, otherwise
   water2. O0 to assign one owner to avoid a duplicate seam with the twin W3
   agents.
3. Composer decision. Does W5 intend to introduce an `EffectComposer` at all for
   tonemap and bloom? Screen-space god-rays are only worth considering if a
   composer already exists for other reasons, since the composer is the dominant
   cost. If W5 stays direct-to-screen, god-rays are off the table on WebGL.
4. Renderer. The WebGPU `ProjectorLight` and `GodraysNode` are the cleanest
   built-in caustic and god-ray paths, but the app runs the WebGL renderer. A
   WebGPU migration is out of scope for this lane. Confirm WebGL stays the
   target so the node paths can be formally dropped from the build plan.
5. Quality preset. Is there any quality-preset infrastructure to defer effects
   to? If not, the cleanest outcome is to ship caustics always-on and weak, and
   to not build god-rays at all until a preset exists.

## Honesty note on turbid-water realism

Salish Sea and Puget Sound secchi depth typically runs about 3 to 8 m and drops
below 2 m in river plumes and plankton blooms. UW Tacoma Commencement Bay and
Quartermaster Harbor surveys report secchi roughly 3 to 7.3 m, at
courses.washington.edu/uwtoce03 and courses.washington.edu/uwtoce14. Caustic
contrast collapses within
roughly one secchi depth because the same scattering that limits secchi visibility
also smears the focused light pattern. So in this water, caustics are weak and
short-range and god-rays are short and diffuse. The honest target is a faint,
low-contrast caustic that is gone within a meter or two of turbid column and no
crisp tropical-reef pattern. This matches the charter lock that the Salish Sea is
turbid and green, not tropical blue.
