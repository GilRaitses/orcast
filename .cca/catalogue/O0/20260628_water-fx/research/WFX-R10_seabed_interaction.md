# WFX-R10 seabed interaction

Owner WFX-R10, Wave 1 research, read-only. Topic is seabed interaction quality. This covers depth pre-pass quality, refraction of the modeled seabed through the surface, soft shoreline contact, and the concrete artifacts in the current `uInverseViewProjection` reconstruction. Honesty label holds. The seabed is the modeled CUDEM topobathy, not measured depth.

Repo state grounded against `web/lib/scene/water2/depthWater.ts`, `web/app/(sandbox)/water/WaterSandboxScene.tsx`, `web/app/components/scene/SalishScene.tsx`, `web/lib/scene/bathy/style/WATER2_TUNING_REQUEST.md` as read 2026-06-28.

## 1. Scope and current state, file-cited

### The depth pre-pass setup

The depth target is created once in `makeWater2` with a 24-bit unsigned integer depth texture and nearest sampling.

```313:325:web/lib/scene/water2/depthWater.ts
  const depthTexture = new THREE.DepthTexture(1, 1);
  depthTexture.type = THREE.UnsignedIntType;
  depthTexture.format = THREE.DepthFormat;
  depthTexture.minFilter = THREE.NearestFilter;
  depthTexture.magFilter = THREE.NearestFilter;

  const depthTarget = new THREE.WebGLRenderTarget(1, 1, {
    minFilter: THREE.NearestFilter,
    magFilter: THREE.NearestFilter,
    depthTexture,
    depthBuffer: true,
    stencilBuffer: false,
  });
```

The pre-pass hides the water mesh, renders the full opaque scene into `depthTarget`, then restores state.

```375:383:web/lib/scene/water2/depthWater.ts
    renderDepthPrepass(renderer, scene, camera) {
      const prevTarget = renderer.getRenderTarget();
      const wasVisible = mesh.visible;
      mesh.visible = false;
      renderer.setRenderTarget(depthTarget);
      renderer.render(scene, camera);
      renderer.setRenderTarget(prevTarget);
      mesh.visible = wasVisible;
    },
```

Key fact that drives section 4. `THREE.WebGLRenderTarget` always allocates a color texture at `depthTarget.texture` unless explicitly told not to, and this code does not opt out. So `renderer.render(scene, camera)` already writes the full opaque scene COLOR into `depthTarget.texture` every frame, and that color is currently discarded. The shader samples only `depthTarget.depthTexture`. The color copy refraction needs is therefore already being produced and thrown away.

### The reconstruction block (quoted)

```225:244:web/lib/scene/water2/depthWater.ts
  void main() {
    // Screen-space UV of this fragment, matching the depth target resolution.
    vec2 uv = gl_FragCoord.xy / uResolution;

    // Reconstruct the seabed WORLD position from the opaque-scene depth buffer.
    float sceneDepth = texture2D(uDepthTexture, uv).x; // window-space [0,1]
    float column;
    if (sceneDepth >= 0.9999) {
      // No opaque geometry behind this fragment (open water / horizon): treat as
      // deep so it reads as solid blue rather than clearing to nothing.
      column = 50.0;
    } else {
      vec4 ndc = vec4(uv * 2.0 - 1.0, sceneDepth * 2.0 - 1.0, 1.0);
      vec4 worldH = uInverseViewProjection * ndc;
      vec3 seabed = worldH.xyz / worldH.w;
      // Vertical water column from the surface plane down to the seabed. Terrain
      // at/above the surface yields <= 0 -> the water clears and land shows.
      column = uWaterLevel - seabed.y;
    }
    column = max(column, 0.0);
```

The inverse view-projection is rebuilt each frame from the live camera.

```384:393:web/lib/scene/water2/depthWater.ts
    update(elapsedSeconds, camera, sunDirection) {
      material.uniforms.uTime.value = elapsedSeconds;
      camera.updateMatrixWorld();
      // inverse(P * V) = inverse(V) * inverse(P) = matrixWorld * projInverse.
      camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();
      invViewProj.multiplyMatrices(camera.matrixWorld, camera.projectionMatrixInverse);
```

The math is standard and correct. UV to NDC xy is `uv * 2 - 1`, window-space depth to NDC z is `depth * 2 - 1`, multiply by inverse view-projection, divide by w. This matches the textbook reconstruction at therealmjp.github.io and the Unity URP reference in section 2. Column is the vertical drop from `uWaterLevel` to the reconstructed seabed Y, which is the right datum because the visible waterline plane sits at that same Y.

### Risks in the current reconstruction

R1. Depth precision is set by the camera near and far, not by the texture alone. In the live scene the camera range is reset on first fit.

```550:554:web/app/components/scene/SalishScene.tsx
    if (camera instanceof THREE.PerspectiveCamera) {
      camera.near = Math.max(fitRadius / 2000, 0.01);
      camera.far = fitRadius * 100;
      camera.updateProjectionMatrix();
    }
```

That is a far over near ratio of 200000. A perspective depth buffer packs almost all of its resolution just past the near plane, so at a 200000 ratio the seabed near Y equals 0 lands in a region where each 24-bit code spans a large world-Z slab. Reconstructed `seabed.y` then quantizes, and `column = uWaterLevel - seabed.y` shows stair-step banding in the shallow color and alpha gradients. The `/water` sandbox uses `near: 1, far: 800`, a ratio of 800, so the sandbox looks cleaner than the live scene will. Anyone tuning only in the sandbox will under-estimate live banding.

R2. Nearest sampling on the depth texture is the correct choice for depth, because linear filtering would average two unrelated depths across a silhouette and invent a mid-depth that exists nowhere. The cost is aliased, jagged column transitions exactly at terrain silhouettes against open water. This is acceptable for depth but it means the seabed read is hard-edged at island outlines.

R3. The `0.9999` open-water fallback is a fixed window-space threshold against a buffer cleared to 1.0. It correctly catches empty sky pixels. With the huge far plane in R1, genuine distant terrain can also reconstruct to a window-space depth above 0.9999 and be misread as open water, snapping `column` to 50.0 and flipping a far shoreline to fully opaque deep water. Risk is low at `far = fitRadius * 100` but real at the far horizon.

R4. Half-texel alignment is currently fine but fragile. `uv = gl_FragCoord.xy / uResolution` samples at pixel centers, and `setSize` sets both the depth target and `uResolution` to `round(cssSize * pixelRatio)`, the same integer drawing-buffer size the main canvas uses. So depth texels and screen pixels line up one to one with no half-texel skew today. The dependency to flag is that this only holds while the depth target resolution exactly equals the main drawing buffer. Any future half-res depth target, or a DPR rounding mismatch, reintroduces a half-texel offset that smears the column by one seabed sample at silhouettes.

R5. Logarithmic depth mismatch is not a present bug but is a latent trap. `WebGLRenderer` defaults `logarithmicDepthBuffer` to false and a repo search finds no enablement. The reconstruction assumes standard projective NDC depth. If W3 or a later renderer change turns on `logarithmicDepthBuffer` for the main render to fight z-fighting on the tiles, the pre-pass depth would be written with the logarithmic formula while this shader still unprojects it as linear projective z, breaking every reconstructed `seabed.y`. This must be checked before any renderer-level depth change lands.

R6. The shoreline edge is soft in color through Beer-Lambert but the foam band is a narrow `smoothstep` window on column, and the underlying contact between water and rising terrain is still an analytic column-to-zero, not a true depth-difference feather against the surface fragment's own depth. The result reads acceptable but the intersection of the wavy surface mesh with steep terrain can still show a thin hard seam where the surface plane geometry crosses the seabed.

## 2. Technique survey with URLs

Depth to world reconstruction and its artifacts.
- MJP, Reconstructing Position From Depth, the canonical treatment of projective vs linear view-space reconstruction and precision. https://therealmjp.github.io/posts/reconstructing-position-from-depth/
- Unity URP, Reconstruct world space positions in a shader, shows the `depth > 0.9999` sky guard for non-reversed-Z and the NDC convention this code already follows. https://docs.unity3d.com/Manual/urp/writing-shaders-urp-reconstruct-world-position.html
- ompuco, Worldspace Reconstruction, the same `H = float4(uv*2-1, depth, 1); D = invViewProj * H` form used here. https://ompuco.wordpress.com/2018/03/21/9/

Screen-space refraction through a transparent surface.
- lettier, 3D Game Shaders For Beginners, Screen Space Refraction, foreground vs background positions and a depth-driven tint, directly reusable. https://lettier.github.io/3d-game-shaders-for-beginners/screen-space-refraction.html
- devfault, Screen-space Water Rendering, the standard `refract_uv = grabUV + N.xy * strength` offset of the opaque color texture. https://devfault.wordpress.com/2018/08/07/screen-space-water-rendering/
- Froyok, Refracting Pixels, why engines copy the opaque color buffer before transparents and distort its UVs, and the foreground-bleed problem. https://www.froyok.fr/blog/2024-12-refraction/
- Crest water docs, render-order notes for refraction sampling an opaque-only color texture and depth-sorting waves. https://crest.readthedocs.io/en/4.20/user/rendering-notes.html
- JCGT 2025, Ultrafast Screen-Space Refractions via Newton's Method, the accurate end of the spectrum if a flat-offset refraction is ever judged too cheap. https://jcgt.org/published/0015/01/03/paper-lowres.pdf

Soft edges and soft particles.
- NVIDIA, Soft Particles whitepaper, the original depth-difference fade and the contrast-power smoother fade. https://developer.download.nvidia.com/whitepapers/2007/SDK10/SoftParticles_hi.pdf
- Blightbound postmortem, depth fade applied beyond particles to kill hard intersection lines, the exact shoreline case. https://www.gamedeveloper.com/programming/softening-polygon-intersections-in-blightbound
- Unity VFX atlas, Soft Particles node setup, `saturate((sceneDepth - selfDepth) * scale)` then multiply alpha. https://unity-trouble-atlas.7colorsgame.com/en/article/unity-shader-graph-soft-particles/

## 3. Recommendations ranked by realism per millisecond

### Rec A, seabed refraction by reusing the discarded color attachment. Highest realism per ms

The pre-pass already renders the opaque scene color into `depthTarget.texture` and throws it away, as shown in section 1. Refraction needs exactly that buffer. So the dominant cost of refraction, an extra full-scene color render, is already paid in this architecture. The added work is one texture sample plus a screen-space UV offset.

Approach. Expose the existing color texture as a uniform `uSceneColor` bound to `depthTarget.texture`. In the fragment shader, offset the screen UV by the surface normal and read the seabed color, with a depth guard so foreground geometry never bleeds into the water.

```glsl
// uniform sampler2D uSceneColor;        // = depthTarget.texture
// uniform float uRefractStrength;        // scene units of max UV push, small

// surface normal already available as n; viewDir as viewDir.
vec2 refrUV = uv + n.xz * (uRefractStrength / max(uResolution.y, 1.0));
// guard: only accept the refracted sample if its seabed is BEHIND this fragment.
float refrDepth = texture2D(uDepthTexture, refrUV).x;
vec2 sampleUV = (refrDepth >= sceneDepth) ? refrUV : uv;   // else no bleed
vec3 seabedColor = texture2D(uSceneColor, sampleUV).rgb;
```

The seabed color then feeds the underwater term instead of, or modulated with, the two-stop `base`. With the WFX-R09 per-channel extinction this becomes `seabedColor * exp(-uAbsorption * column)` plus in-scatter, which is the physically meaningful read of a modeled seabed seen through turbid water.

Cost, estimated. One added dependent texture fetch for `uSceneColor` and one for the guard depth, plus a few ALU ops, in the water fragment shader only. The water plane covers a fraction of the screen, so on the order of 0.1 to 0.3 ms at 1080p on an integrated GPU, well under one millisecond. No new render pass, no new render target, no new dependency. One required change to the target itself, set the color texture filter to `THREE.LinearFilter` so the refracted read is smooth rather than blocky. Linear filtering of the color attachment does not harm the separate nearest-filtered depth read.

Three-only fallback. This recommendation is already three-only. There is no library to add. If even the single color sample is rejected on the lowest tier, the fallback is the current two-stop `base` with no refraction, gated by a `uRefract` flag defaulting off on a perf budget.

Caveat to honor the honesty label. Refraction changes how the modeled seabed looks through the surface. It asserts no measured depth. Keep the modeled-not-measured label intact.

### Rec B, soft shoreline contact by a depth-difference feather. High realism per ms

Replace the implicit hard contact at the water-terrain intersection with an explicit soft-particle fade driven by the difference between the seabed depth and the water surface fragment's own depth, the technique in the NVIDIA and Blightbound references. This removes the thin hard seam in R6 where the wavy plane crosses steep terrain, and it makes the waterline read as a soft wet contact rather than a drawn line.

```glsl
// linearize both depths to view space, or reuse the world column directly.
// cheap world-space version using the value already computed:
float contactFade = smoothstep(0.0, uContactSoftness, column);
// fold into alpha so the surface vanishes into the shore, not onto a hard line.
alpha *= contactFade;
```

`uContactSoftness` is a small scene-unit distance tuned in `/water`. This reuses `column`, which already exists, so it is nearly free. For a more correct feather at steep terrain where the surface mesh itself dips below the seabed, compare the surface fragment view-space depth to the reconstructed seabed view-space depth and feather on that difference, which costs one extra linearize.

Cost, estimated. Under 0.05 ms, a handful of ALU ops, no new sample if it reuses `column`. Three-only, no dependency.

### Rec C, fix live-scene depth precision. Medium realism per ms, removes banding

The banding in R1 is a near and far problem, not a texture problem. Two levers, in order of payoff.

C1. Tighten `camera.far` in the live scene. `far = fitRadius * 100` is far past any geometry. Bringing far down toward the actual scene extent, on the order of `fitRadius * 4` to `fitRadius * 8`, recovers a large share of the depth codes for the seabed band and directly reduces the column banding. This is a one-line change in `SalishScene.tsx` and belongs to the integrate wave, not research, but it is the cheapest realism win in this whole doc.

C2. If banding persists after C1, switch the depth texture to `THREE.FloatType` with `THREE.DepthFormat`, which requests a 32-bit float depth where supported. Float depth spends more bits near the camera, helping the shallow band. It is not a cure for an extreme far over near ratio by itself, so do C1 first. Float depth textures are widely supported on WebGL2 through `WEBGL_color_buffer_float` and depth-texture extensions, but support must be feature-detected with a fallback to the current `UnsignedIntType`.

Cost. C1 is free, it only changes the projection. C2 trades a small bandwidth increase on the depth attachment, on the order of memory doubling for that one texture, for smoother gradients. Three-only.

### Rec D, guard the open-water fallback. Low cost, removes a horizon artifact

Make the `0.9999` test robust to R3 by combining the threshold with a reconstructed-Y sanity check, so a far terrain pixel that quantizes near 1.0 does not flip to `column = 50`. A cheap form is to keep the threshold but clamp the reconstructed column to a sane max derived from the scene extent rather than jumping to a literal 50.0 at the boundary. Near-zero cost, three-only.

## 4. Frame budget impact

Budget is 60fps desktop and 30fps laptop, so roughly 16.6 ms and 33.3 ms per frame. The existing depth pre-pass already costs one full opaque-scene render, the single largest item WFX adds, and that is accepted in the charter.

The headline for this topic. Refraction in Rec A does NOT add a second full color render in this codebase, contrary to the usual assumption that refraction needs an extra color copy. The reason is concrete and file-cited in section 1. `renderDepthPrepass` calls `renderer.render(scene, camera)` into a `WebGLRenderTarget` that always carries a color attachment, so the opaque color is already rendered and currently discarded. Refraction reuses that attachment. The marginal cost is one or two extra texture samples in the water fragment shader over the screen fraction the water covers, estimated at 0.1 to 0.3 ms, plus the one-time flip of the color filter to linear.

Quantified against the existing pre-pass. If the pre-pass full-scene render is taken as the unit cost of the depth read, Rec A adds well under one tenth of that unit, because it adds zero geometry passes and only fragment samples on the water region. Rec B and Rec D are ALU-only, sub 0.05 ms each. Rec C1 is free. Rec C2 adds depth-attachment bandwidth only, no extra pass.

Net. The full seabed-interaction upgrade in this doc fits inside the existing depth-pre-pass budget with no new render target and no new pass. The only true new GPU work is a few fragment samples. This is the cheap end of the WFX stack and should be sequenced early.

One budget watch item for the cross-cutting WFX-R13 accounting. Reusing the pre-pass color means the pre-pass render must keep producing usable color, so the pre-pass cannot later be optimized into a depth-only render without restoring a color path for refraction. Flagging that coupling now.

## 5. Collision and sequencing

W3 water-upgrade owns `web/lib/scene/water2/`. Recs A, B, and D are edits to `depthWater.ts` shader and uniform wiring, plus the color-filter flip on the render target, all inside that W3-owned module. They do not touch the convergence file. They must be authored as W3 build-wave work, not research, and must be coordinated so a single editor owns `depthWater.ts` to avoid colliding with the WFX-R09 per-channel absorption edit, which lands in the same fragment shader's color path. Rec A and R09 are complementary and should land together, because Rec A produces the `seabedColor` that R09's `exp(-uAbsorption * column)` should attenuate. Sequence R09 and Rec A as one combined color-path rewrite of `depthWater.ts`.

Rec C1, the `camera.far` tightening, lives in `SalishScene.tsx`, the locked convergence file. It must serialize through O0 against W-CAM, W-LABELS, W3, W4, and LGC. C1 also interacts with camera framing owned by W-CAM, since far-plane changes affect any culling or framing math, so W-CAM must sign off. Treat C1 as an integrate-wave edit, not a build-wave edit.

The pre-pass wiring in `SalishScene.tsx` Water2Rig at `web/app/components/scene/SalishScene.tsx` lines 275 to 326 already calls `renderDepthPrepass` then `update`. Reusing the color attachment needs no change to that call site, because the color is already rendered. Only the new uniform `uSceneColor` must be bound inside `makeWater2`, which is W3-owned, so the integrate site stays untouched for Rec A. That keeps the convergence-file surface area minimal.

Sandbox `web/app/(sandbox)/water/WaterSandboxScene.tsx` is the safe tuning surface for `uRefractStrength` and `uContactSoftness`, but note its `near: 1, far: 800` hides the live banding from Rec C, so any precision tuning must be validated against the live `SalishScene.tsx` near and far, not only the sandbox.

## 6. Open questions for O0

Q1. Combine WFX-R09 per-channel absorption and Rec A seabed refraction into one `depthWater.ts` color-path rewrite under a single build-wave editor, or land them as two serialized edits. Recommendation is one combined edit, because they share the same fragment color path and refraction without absorption is half a feature.

Q2. Approve the Rec C1 `camera.far` tightening as an integrate-wave edit to `SalishScene.tsx`, and assign the W-CAM sign-off, since far-plane changes touch camera framing. This is the cheapest realism win in the doc but it edits the convergence file.

Q3. Set the realism floor for refraction. Flat normal-offset refraction in Rec A is sub-millisecond and three-only. The Newton's-method screen-space refraction in the JCGT reference is more accurate but heavier. Confirm the flat-offset is the target and the iterative method is out of scope for WFX.

Q4. Confirm `logarithmicDepthBuffer` stays false across W3 and W4. If any lane plans to enable it on the renderer to fight tile z-fighting, the reconstruction in `depthWater.ts` must be updated in the same change, per R5.

Q5. Decide whether Rec C2 float depth is worth feature-detecting now, or deferred until C1 is measured. Recommendation is defer, do C1 first and re-measure banding.
