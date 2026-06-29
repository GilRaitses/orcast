# R5 — AI material & shader generation: is it real, and is it usable for orcast?

Agent: R5 (ai-materials-shaders). Spike home: `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/`.
Scope: research-only brief. No code edits, no commits.

Question (from charter): is AI material and shader generation real and usable in 2026, and
could it author the terrain / seafloor / kelp / shoreline / water-detail materials for our
Next.js + react-three-fiber + three@0.169 + `3d-tiles-renderer@0.4.28` scene? What is real
vs hype, and what are the licensing / provenance / honesty constraints for a science project
where modeled outputs are labeled "modeled, not measured"?

Short answer: **AI text-to-PBR material generation is real, mature, and production-usable in
2026** for *decorative* tileable surface materials. **AI/LLM shader-code generation is real
but unreliable** and should be treated as an assistant, not an author, for our hand-tuned
water and depth shaders. Detailed below, then "Implications for orcast".

---

## 1. AI material / texture generation (text-to-PBR)

The maturity here is high. The standard pattern is: a diffusion model emits a tileable
basecolor (and often a full PBR stack — basecolor / normal / roughness / metallic / height /
AO), which then feeds an ordinary engine material. That is exactly the `MeshStandardMaterial`
input set three.js wants.

**Commercial / production tools (usable today):**

- **Adobe Substance 3D Sampler — Text-to-Texture / Text-to-Pattern / Image-to-Texture**
  (Firefly-powered, still labeled "beta" but shipping in 4.4; docs build-dated Apr 2026).
  Generates a tileable texture from a prompt, then converts it to a full PBR material
  (basecolor, height, normal, roughness, AO) via the existing Image-to-Material system.
  Subscription-only, requires an Adobe account (not on the Steam/perpetual license).
  Crucially for us: **Sampler auto-attaches C2PA Content Credentials marking the asset as
  AI-generated**, and Firefly is trained on licensed Adobe Stock + public-domain content with
  IP indemnification on qualifying paid plans.
  https://experienceleague.adobe.com/en/docs/substance-3d-sampler/using/features-and-workflows/generative-workflows ,
  https://www.cgchannel.com/2024/05/adobe-releases-substance-3d-sampler-4-4/ ,
  https://business.adobe.com/products/firefly-business/firefly-ai-approach.html
- **WithPoly (withpoly.com, "Poly")** — browser tool dedicated to PBR. Text or image prompt →
  seamless tileable maps up to 8K, 32-bit, with Color/Normal/Height/AO/Roughness/Metalness;
  can also tile/upscale existing maps. Free tier up to 2K; "Poly Infinity" ~$20/mo unlocks 8K
  + royalty-free commercial license.
  https://www.awn.com/news/poly-introduces-new-generative-ai-texture-generator
- **Dream Textures** (open-source Blender add-on, `carson-katri/dream-textures`) — runs Stable
  Diffusion locally, supports a "Seamless" tiling option and projection. Free, no cloud, but
  PBR accuracy is uneven: independent comparisons note that metallic/roughness frequently need
  manual correction and **diffusion-derived normal maps are often physically incorrect**, and
  tiling is unreliable without prompt/post work.
  https://github.com/carson-katri/dream-textures/ ,
  https://www.strayspark.studio/blog/text-to-material-comparison-ai-tools-blender-2026
- **Polycam / Luma / RealityScan** — these are photogrammetry/scan-to-3D tools, not
  text-to-material; useful if we ever had *real* photographs of San Juan seafloor/shoreline to
  scan, but out of scope for decorative tileable surfaces.
- **NVIDIA** ships two relevant but heavier things: **RTX Neural Shaders / RTX Kit** (train an
  MLP material, run it inside the shader via cooperative vectors / Tensor Cores) and the
  research **Real-Time Neural Appearance Models** (below). These target native RTX path tracers,
  not a WebGL/WebGPU three.js MeshStandardMaterial, so they are not a near-term fit for us.

**Diffusion-based PBR research that is now download-and-run:**

- **StableMaterials** (Vecchio et al., arXiv:2406.09293; weights on Hugging Face
  `gvecchio/StableMaterials`) — LDM that emits basecolor + normal + height + roughness +
  metallic from text *or* image, with a `tileable=True` flag. Its "feature rolling" trick
  produces genuinely seamless maps even in fast (4-step) generation. This is the clearest
  example that **open, runnable, tileable PBR generation exists**.
  https://huggingface.co/gvecchio/StableMaterials , https://arxiv.org/html/2406.09293v3
- **ControlMat / MatGen** (Vecchio et al., ACM TOG; https://doi.org/10.1145/3688830) — LDM +
  ControlNet for material *capture* from a photo, with patched diffusion + **noise rolling** to
  get high-resolution (to 4K) tileable maps, and border-inpainting to make a non-tileable
  photo tile.
- **MatFusion** (Sartor & Peers, SIGGRAPH Asia 2023; https://doi.org/10.1145/3610548.3618194) —
  unconditional SVBRDF diffusion backbone (312k synthetic materials) refined into conditional
  estimators; the conceptual parent of much of the above.
- **MatLat** (CVPR 2026; arXiv:2512.17302) — a material-latent VAE + diffusion for multi-view
  consistent PBR texture generation; shows the field is still actively improving into 2026.

**Honest limitations.** Diffusion normal/height maps are perceptual, not photometrically
correct — they look right but are not measurements. Free/local SD pipelines (Dream Textures)
need manual cleanup of roughness/metallic and tiling. The Firefly/Poly commercial tools are
the reliable path and they bake provenance metadata, which matters for us.

---

## 2. AI / LLM shader-code generation (GLSL / WGSL / three.js / TSL)

This is real but materially less reliable than material-image generation, because the output
is *code that must compile and run correctly*, not an image we can eyeball.

- **General experience:** practitioners report LLMs (Claude, GPT, DeepSeek-R1) can produce
  visually interesting fragment shaders from prompts, but with a high failure rate. A
  documented gallery using DeepSeek "fails to produce working code about 50% of the time" and
  the author just regenerates rather than debugging.
  https://discourse.threejs.org/t/a-gallery-of-my-deepseek-generated-fragment-shaders/77660
- **14islands' GLSL-from-prompt experiment:** Claude was the most consistent; common failure
  modes are syntax errors, and **performance blowups** (raymarch loops too heavy for
  real-time). Strong system prompts, a "plan first" step, and naming the intended algorithm
  (SDF/raymarching) measurably reduced compile failures.
  https://www.14islands.com/journal/ai-generated-glsl-shaders
- **three.js TSL specifically (relevant since we may move toward WebGPU/TSL):** LLMs reliably
  hallucinate here because TSL is new and fast-moving — training data still uses old imports
  (`three/nodes` vs `three/tsl`), deprecated functions (`timerGlobal` vs `time`), and GLSL
  builtins (`position`, `gl_FragColor`) that don't exist in TSL. A curated reference doc / skill
  in the prompt is reported to eliminate "~90% of the hallucinated garbage".
  https://threejsroadmap.com/blog/getting-ai-to-write-tsl-that-works ,
  https://threejsroadmap.com/blog/how-to-convert-glsl-shaders-to-tsl
- **Neural shading** (NVIDIA Real-Time Neural Appearance Models, arXiv:2305.02678; Zeltner et
  al. 2023) replaces an analytic BRDF with a baked MLP decoder over a latent texture, run
  inside the path tracer — >1M queries/s, up to ~order-of-magnitude faster than layered PBR.
  This is "AI shaders" in a different sense (learned appearance, not LLM-written code) and is
  RTX-native, not a WebGL fit. https://research.nvidia.com/labs/rtr/neural_appearance_models/

**Takeaway:** use an LLM as a co-pilot to scaffold/convert/explain shader code, but every
generated shader must be compiled, perf-profiled, and visually verified by a human. Do not let
an LLM be the source of truth for our Gerstner water / depth-fade / shoreline shaders, which
are physically meaningful and already hand-tuned by Agent A.

---

## 3. Academic literature (for grounding the above)

- **Deep SVBRDF Acquisition and Modelling: A Survey** (STAR, Computer Graphics Forum 2024;
  https://doi.org/10.1111/cgf.15199) — the authoritative overview: single-/few-image material
  capture, categorized into inference-based (feed-forward), optimization-based, and hybrid
  methods; recovers diffuse albedo, specular, roughness, normal.
- **Single-Image SVBRDF Capture with a Rendering-Aware Deep Network** (Deschaintre et al.,
  SIGGRAPH Asia 2018; https://github.com/valentin-deschaintre/Single-Image-SVBRDF-Capture-rendering-loss)
  — the seminal feed-forward result; per-pixel normal/albedo/specular/roughness from one
  flash-lit photo, trained on procedural materials with a differentiable rendering loss.
- **Diffusion-Guided Relighting for Single-Image SVBRDF Estimation** (SIGGRAPH Asia 2025;
  https://xingyouxin.github.io/works/DGRSISE/paper/SigA-2025.pdf) — current frontier: uses a
  diffusion model to relight and remove saturated highlights before estimating highlight-free
  reflectance maps.
- Procedural material-graph inference: "Controlling Material Appearance…" / MatFormer-style
  work (referenced from MatFusion's bibliography) infers editable node graphs rather than flat
  maps — relevant only if we later want *parametric* materials.

These confirm the science is mature and peer-reviewed; the commercial tools in §1 are direct
descendants.

---

## 4. Practical pipeline for orcast

Yes, this maps cleanly onto our stack. Concrete pipeline for the decorative surfaces
(seafloor sediment, rock, kelp, shoreline gravel, and a water detail-normal):

1. **Generate** a tileable PBR set per surface from a prompt (e.g. "fine grey-brown marine
   sediment with scattered pebbles, top-down, even lighting") using **WithPoly** or
   **Substance 3D Sampler Text-to-Texture → Image-to-Material**, or run **StableMaterials**
   locally for a no-subscription / fully-auditable path. Output: basecolor, normal (GL
   convention), roughness, AO, height — 2K or 4K, seamless.
2. **Verify tiling and convention.** Confirm GL-style normals (three.js expects OpenGL Y+),
   sanity-check roughness/metallic ranges (sediment ≈ non-metal, high roughness), and visually
   confirm no seams. Diffusion normals are perceptual — fine for decoration.
3. **Wire into three.js** as a standard `MeshStandardMaterial`:
   `map` = basecolor (sRGB), `normalMap` = normal (linear), `roughnessMap`, `aoMap`,
   optional `displacementMap`/`bumpMap` from height; set `repeat`/`wrapS=wrapT=RepeatWrapping`
   and `colorSpace` correctly. For the **water detail normal**, the generated normal map can
   drive a scrolling detail-normal layered on top of Agent A's Gerstner displacement — purely
   cosmetic high-frequency ripple, not a new water model.
4. **Keep them decorative and clearly separated** from the topobathy geometry, which stays the
   measured CUDEM-derived surface. Materials tint/texture the surface; they never alter
   elevation or depth values that carry scientific meaning.

**Realistic vs hype:**
- Realistic now: tileable decorative PBR sets for sediment/rock/kelp/shore, and a cosmetic
  water detail-normal. Good visual quality, fast, cheap.
- Hype / not for us: AI-generated *measured-accurate* seafloor appearance; AI authoring our
  physically-meaningful water/depth shaders unattended; NVIDIA neural materials in a WebGL
  scene.

**Licensing / provenance / honesty (critical for a science project):**
- **Provenance is solvable and should be mandatory.** Firefly/Sampler auto-embeds **C2PA
  Content Credentials** marking assets AI-generated; C2PA is an open, royalty-free provenance
  standard (now backed by Adobe, Google, Meta). https://spec.c2pa.org/ . We should retain that
  metadata and additionally record provenance in our own asset manifest.
- **Licensing:** Firefly = commercially safe + IP indemnity on qualifying paid plans; WithPoly
  = royalty-free commercial rights on the paid tier; StableMaterials = open weights (check the
  model card license before shipping). Each generated material we ship should record tool,
  prompt, date, and license.
- **Honesty:** AI materials are **decorative skins** and must never be presentable as measured
  data. They should sit behind the same "modeled, not measured" labeling the charter already
  mandates, and ideally an even stronger "decorative texture, AI-generated, not survey imagery"
  note so a viewer cannot mistake a pretty seafloor texture for real backscatter / imagery.
- **Free, zero-AI fallback exists:** CC0 photoscanned PBR from **Poly Haven** (e.g.
  `coast_sand_rocks_02`, `seaside_rock`) and **ambientCG** (Ground/Rocks/Sand categories) give
  real-world-derived, public-domain, no-attribution tileable sets that sidestep AI-provenance
  questions entirely. https://polyhaven.com/ , https://ambientcg.com/

---

## Implications for orcast

- **AI-generated tileable PBR texture sets for decorative materials: GO (conditional).** Use
  them for seafloor sediment / rock / kelp / shoreline and a cosmetic water detail-normal,
  consumed by ordinary three.js `MeshStandardMaterial`. Prefer **WithPoly** or **Substance 3D
  Sampler** (provenance baked in) or **StableMaterials** (open/auditable). Condition: these
  texture the *measured* CUDEM geometry and must never modify elevation/depth.
- **Strongly consider the CC0 path (Poly Haven / ambientCG) first or in parallel.** For a
  science project it is the lowest-risk option — real-photoscan-derived, public domain, no AI
  provenance debate. Use AI generation mainly where no suitable CC0 tile exists or where we
  need an art-directed look.
- **Shaders: keep hand-written, AI-assisted only.** Our Gerstner water, depth-fade, shoreline,
  and underwater shaders are physically meaningful and already authored (Agent A); an LLM may
  scaffold, convert (GLSL↔TSL), or explain, but every shader must be compiled, perf-checked,
  and visually verified by a human. ~50% LLM failure rate and TSL hallucination make unattended
  generation unacceptable for science-facing rendering. Do **not** adopt NVIDIA neural
  materials (RTX-native, not WebGL).
- **Provenance labeling (required):** retain C2PA Content Credentials on every AI asset; add an
  `assets/MATERIALS_PROVENANCE` manifest recording per-material {tool, prompt, date, license,
  AI-generated yes/no, source-if-CC0}. Surface a UI note that surface textures are
  **decorative, not measured/survey imagery**, layered under the existing "modeled, not
  measured" honesty constraint.
