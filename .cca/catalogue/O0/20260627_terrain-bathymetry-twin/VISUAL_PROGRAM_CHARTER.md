# Visual program charter: a believable Salish world, smoothly

Home: `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/`
Status: CONFIRMED 2026-06-27. Decision record in section 6 locked by the operator.
W2 integrate is the prerequisite and immediate next executable wave; W3 to W5
launch behind it after each stated gate.
Depends on: W2 (integrate real CUDEM tiles + agent A realism into the live scene).
Scope: how the terrain+bathymetry twin becomes a world that resembles ours, with a
sky, water that ripples and waves, underwater views of the bathymetry layers, and
modes for exploring it, while running very smoothly.

This charter does NOT launch anything. It proposes three deepening waves (W3, W4,
W5) that sit on top of the integrate wave, fills the decision record with
recommended values, and surfaces the genuine trade-offs for the operator.

---

## 0. What already exists (the substrate these waves build on)

- `web/app/components/scene/realism/` (agent A, on `three` only):
  - `water.ts` sum-of-four-Gerstner surface, analytic normals, Fresnel + Blinn sun
    specular, opacity. Sea level at scene Y 0. No render targets, no reflections yet.
  - `sun.ts` real solar position from date/lat/lng (elevation, azimuth, color,
    intensity). `atmosphere.ts` sky color + linear fog tracking solar elevation.
  - `palette.ts` ocean depth ramp and land elevation ramp. `applyRealism.ts` mounts
    lights + sky background + fog + water onto a scene and drives them per frame.
- `web/app/(sandbox)/tiles3d/useTilesRenderer.ts` (agent E): imperative
  `TilesRenderer` mounted in the r3f loop. The CUDEM pilot now serves correctly via
  CloudFront after a cache invalidation (glb 5.86 MB, box hx 5645/5671/274 m,
  NAVD88); see the S14 correction in `STEP_LOG.md` and `RESEARCH_SYNTHESIS.md` sec 0.
  IT IS STILL A SINGLE TILE (child geometricError 0.0, no LoD); a real multi-LoD
  bake (R1) is the W2 prerequisite. Tile meshes carry default material today.
- Coordinate frame: local EPSG:32610 (UTM 10N) meters, NAVD88 m elevation, Y up,
  sea level Y 0. Origin-shifted near zero at the pilot extent. Full extent will
  need explicit origin handling (precision, W5).
- Science: agent F proved one CUDEM surface feeds `s_space` via `BathymetryAdapter`
  (`infra/3dtwin/science/WIRING-science.md`). Depth/slope/aspect rasters exist.

Honesty constraint carries through every wave: derived color, depth bands, habitat
overlays, and any basemap are labeled "modeled, not measured" and kept separate
from measured data.

---

## 1. Target experience (the "what it should feel like")

1. A sky that reads as a real marine sky, lit by the same sun that lights the
   terrain, changing with time of day.
2. Land and seafloor that read as real ground: elevation and slope drive color and
   texture, not a flat gray mesh.
3. Water that ripples and waves, reflects the sky, lets you see the shallows, and
   foams where it meets the shore.
4. The ability to drop below the surface and see the seafloor as depth-coded
   bathymetry layers, in a believable underwater atmosphere.
5. Several ways to move through it: overview orbit, free flight, a dive, a
   cross-section slice, a guided flythrough, with a time-of-day control and layer
   toggles.
6. All of it at an interactive frame rate on ordinary hardware.

---

## 2. Architecture (how, technically)

Everything is built as self-contained modules and a sandbox route first, then a
single convergence editor wires it into the live scene at the wave gate. This is
the same discipline as W1: one file one owner, one convergence-file editor per
wave, one manifest editor per wave, type-check during the parallel phase, visual
verification at the gate.

### Sky and image-based lighting
Procedural sky from the `three/addons` `Sky` object, its sun position bound to
`makeSun().direction`, so the existing solar model drives the sky. Generate an
environment map from the sky with `PMREMGenerator` and set `scene.environment`, so
every physically based material gets sky reflections and ambient light for free.
Regenerate the environment only when the sun or date changes, never per frame, so
it stays cheap. No new dependency. An optional equirectangular HDRI sky is a swap
behind the same interface for a more photoreal static look.

### Land and seafloor materials
On each `load-model` event from the tiles renderer, swap a shared material onto the
streamed tile meshes:
- Above 0 m: elevation banded albedo from `palette.ts` (lowland green to rock to
  high pale), slope-based rock blend so steep faces read as rock, a faint triplanar
  detail normal so surfaces are not glassy.
- Below 0 m: a depth ramp plus optional isobath contour lines computed in the
  shader from world Y, plus slope-based sediment versus rock. These are the
  bathymetry layers the underwater views show.
This is one material module plus one applier module that bridges materials to the
tiles lifecycle. Cheap, applied as tiles stream, no second geometry.

### Water upgrade
Extend agent A water without breaking it (deliver a v2, keep the v1 path):
- Sky reflection through `scene.environment` and Fresnel, no extra render pass.
- Depth-based color and see-through shallows. Recommended path is analytic, from
  the known terrain height under each surface point, so no extra pass. A
  screen-space refraction depth target is the higher-fidelity alternative at the
  cost of one pass.
- Shoreline foam where the water column is thin, animated.
- High-frequency detail ripples from scrolling normal maps layered over the
  Gerstner base, and sun glitter tied to the solar direction.

### Underwater
When the camera goes below Y 0, blend into an underwater state across a small band
so there is no hard pop:
- Exponential blue-green fog whose density grows with depth.
- The water surface seen from below with a silvered underside.
- Optional drifting suspended particles and light shafts, both gated by the quality
  preset.
- The depth-banded seafloor material becomes the focus, so the descent reveals the
  bathymetry layers.

### Bathymetry layers and section
- Continuous depth ramp on the seafloor with a toggleable isobath overlay at chosen
  intervals, for example 10, 20, 50 m.
- A cross-section mode using clipping planes plus a cap shader, so a movable
  vertical slice reveals the water column and seabed profile as a true section.
- The science habitat field `s_space` from agent F as a separate toggleable colored
  overlay on the seafloor, labeled modeled.

### Exploration modes
A camera mode state machine with smooth transitions:
- Overview orbit, the current default.
- Free flight with keyboard and mouse look, above or below water.
- Dive, a constrained underwater roam that hugs the seafloor.
- Cinematic tour, a keyframed flythrough, for example through Haro Strait, with
  play and pause.
- Top-down map for orientation.
- Section, the clip-plane slice above.
A heads-up layer gives a mode switcher, a time-of-day slider that drives
`makeSun`, a depth and position readout, layer toggles, and a quality preset.

### Performance, the cross-cutting constraint
A frame budget per subsystem, enforced by a perf harness from W3 onward:
- Tiles LoD via `errorTarget`, `maxDepth`, cache size, demand frameloop with
  invalidation, already wired.
- Float precision via origin shift at full extent, so UTM coordinates near five
  million do not jitter (W5).
- Texture compression with KTX2 or Basis for normal maps, environment, and
  overlays (W5), added by the single manifest editor.
- Prefer environment-map reflection over planar reflection. Reuse a single depth
  target if screen-space refraction is chosen. Keep post-processing selective and
  behind the quality preset.
- Water mesh segment count scales down when far or underwater. Particles and
  overlays are instanced or merged.

---

## 3. Wave W3, world materials and shading

Parallelism 6. Builds modules plus a `/sandbox/world` route. No edits to
`SalishScene.tsx` this wave. Gate is visual on the sandbox.

| Role | Owns | Deliverable |
|---|---|---|
| sky-env | `web/lib/scene/sky/` | procedural Sky bound to `makeSun`, PMREM environment, optional HDRI swap |
| terrain-material | `web/lib/scene/materials/terrain/` | elevation and slope PBR land material with triplanar detail |
| seafloor-material | `web/lib/scene/materials/seafloor/` | depth ramp, isobath contour shader, slope sediment versus rock |
| water-upgrade | `web/lib/scene/water2/` | reflections, depth color, foam, detail ripples, glitter; v2 next to agent A v1 |
| tile-material-applier | `web/lib/scene/tiles/applyTileMaterials.ts` | bridge that swaps materials onto streaming tiles on load-model |
| perf-harness | `web/app/(sandbox)/world/` plus `infra/3dtwin/perf/` | sandbox compositing the above, stats overlay, scripted camera sweep, budget doc; sole manifest editor if a stats lib is added |

Gate: the `/sandbox/world` route renders sky, lit land, depth-banded seafloor, and
upgraded water together, at or above the frame budget, verified by screenshots and
captured frame times.

---

## 4. Wave W4, underwater and exploration modes

Parallelism 6. This wave lands the experience in the live scene through a single
convergence editor. Depends on W2 and W3.

| Role | Owns | Deliverable |
|---|---|---|
| integrator | `web/app/components/scene/SalishScene.tsx` (or a new `SceneRoot`) | wire sky, materials, water2, underwater, modes, section, layers, HUD; sole convergence-file editor |
| underwater | `web/lib/scene/underwater/` | below-surface fog and tint, smooth surface transition, underside water, optional particles and shafts |
| camera-modes | `web/lib/scene/camera/` | mode state machine: overview, fly, dive, cinematic, top-down, with smooth transitions |
| section-tool | `web/lib/scene/section/` | clip-plane cross-section plus cap shader revealing the layers |
| layers-overlay | `web/lib/scene/layers/` | isobath toggle, `s_space` habitat overlay from agent F, hydrophone layer, toggling |
| explore-ui | `web/app/components/scene/hud/` | mode switcher, time-of-day slider, depth and position readout, layer toggles, quality preset (copy follows the prose gate) |

Gate: in the live scene the operator can switch modes, dive and see the depth-coded
bathymetry layers and a section, toggle overlays, and scrub time of day, all
smoothly. Visual verification by screenshots and a short capture.

---

## 5. Wave W5, performance hardening, hosting, science calibration

Parallelism 6. Folds the prior W3 science and host work in `wave_shape.yml` into one
hardening wave. Depends on W4.

| Role | Owns | Deliverable |
|---|---|---|
| precision-origin-shift | `web/lib/scene/precision/` plus tiles config | origin shift or RTC for full-extent float stability |
| texture-compression | `infra/3dtwin/textures/` plus loaders | KTX2 or Basis pipeline and manifest loaders; recompress env, normals, overlays; sole manifest editor |
| post-fx | `web/lib/scene/post/` | selective bloom for sun glitter, optional SSAO and shafts, quality presets, perf-bounded, gated |
| full-extent-host | `infra/3dtwin/host/` | bake full extent on the EC2 box, host on CloudFront, wire the live URL |
| science-calibration | `infra/3dtwin/science2/` plus `docs/` | calibrate `s_space` rasters, provenance and error band, cross-check external bathymetry |
| perf-audit-capture | `docs/` plus harness | VRAM and draw-call audit, frame times across modes and devices, final QA, demo capture |

Gate: the full twin is hosted and validated with provenance, every mode is within
the frame budget on the target hardware, and a capture exists.

---

## 6. Decision record (CONFIRMED by operator 2026-06-27)

| # | Decision | Confirmed value |
|---|---|---|
| V1 | Sky | procedural `Sky` bound to `makeSun` plus PMREM environment map. No HDRI. |
| V2 | Water reflection and refraction | environment-map reflection plus analytic depth color, zero extra render passes. |
| V3 | Bathymetry layers | continuous depth ramp plus toggleable isobaths, plus the clip-plane section tool. |
| V4 | Exploration modes in scope | all of: overview, free flight, dive, cross-section, time-of-day, cinematic flythrough, top-down map. |
| V5 | Frame budget | 60 fps desktop, 30 fps mid laptop. Post-processing allowed only inside the quality preset. |
| V6 | Wave numbering | insert visual W3 and W4, push science and host hardening to W5. W2 integrate runs first. |
| V7 | Orca-specific | none for now. Terrain and ocean focused. Whale-track and hydrophone flythrough deferred. |
| V8 | Build discipline | modules plus sandbox first, single convergence editor lands the experience in W4. |

Note on V4: cinematic flythrough and top-down map are now in scope for W4, so the
camera-modes deliverable in section 4 covers all seven modes, not five.

---

## 7. Status and next step

Decision record confirmed. Folded into `wave_shape.yml` as W3 to W5 on 2026-06-27.
The immediate next executable wave is W2 integrate, the prerequisite for all visual
work. W3 dispatch is prepared once W2 closes its gate. Nothing launches without an
explicit operator go, and nothing is committed without an explicit operator ask.

---

## 8. Research-spike amendments (2026-06-27, folds R1..R6)

Full synthesis: `RESEARCH_SYNTHESIS.md`. These AMEND, not replace, sections 1 to 6.

| # | Amendment | Source |
|---|---|---|
| A1 | W2 prerequisite hardened: the integrator does NOT mount a single-tile pilot. It mounts a real multi-LoD tileset (root-largest, monotonically halving geometricError, leaves near 0). The full-extent `batch-conversion` bake produces this; the single-tile pilot is for sanity only. | R1, R6 |
| A2 | Every bake-and-upload MUST end with a CloudFront invalidation, then a cache-busted re-fetch to confirm bytes. The S14 stale-cache incident is the reason. | ground truth |
| A3 | V2 strengthened: water color/alpha become DEPTH-DRIVEN from the opaque depth buffer (Beer-Lambert), so shallow/dry areas reveal land instead of being painted over. This is the durable fix for "water washes over terrain". Reflection stays env-map/Fresnel; one optional depth target for refraction; no SSR. | R4 |
| A4 | New W4 deliverable, soundings-overlay: a MEASURED-soundings layer rendered OVER (never blended INTO) the modeled CUDEM. Sources for the bbox: NOS H-surveys, NOAA ENC SOUNDG/DEPARE, CHS NONNA (Canadian strip), San Juan MBES compilation, 2019 WA DNR lidar. MLLW->NAVD88 only via NOAA VDatum. Tag each source with its GEBCO TID. Keeps "modeled vs measured" verifiable. | R2 |
| A5 | V3 expanded: portrayal gets a swappable preset, a "chart" preset (S-52-inspired stepped depth shades + emphasised safety contour) and a "scientific" preset (cmocean), plus NW hillshade and two-tier isobaths (procedural minor + precomputed standard). S-52-inspired, NOT certified ECDIS; legend reconciles LAT/MLLW vs NAVD88. seafloor-material (W3) and layers-overlay (W4) own this. | R3 |
| A6 | New W3 capability, AI/CC0 materials: AI text-to-PBR (or CC0 from Poly Haven/ambientCG, preferred) for DECORATIVE tileable sets (sediment, rock, kelp, shore, cosmetic water detail-normal). Shaders stay hand-written. Every AI asset carries C2PA + a provenance manifest entry, labeled decorative-not-measured. Materials never alter elevation or depth. terrain-material + seafloor-material own this. | R5 |
| A7 | Quick-win already landed (independent of W2): the live placeholder `SalishScene` vanishing-land bug is fixed (terrain winding reversed; water set depthWrite=false, biased below Y0, renderOrder 1) and visually verified. This is a stopgap; the placeholder is still slated for retirement when the integrator lands. | R6 |
