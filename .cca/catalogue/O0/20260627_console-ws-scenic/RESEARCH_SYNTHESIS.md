# WS-SCENIC Research Synthesis

Research wave for WS-SCENIC. Read-only, doc-producing. This synthesis names the
concrete techniques and open-data sources the implementation can use, with a
recommendation per problem, licensing and provenance notes, and the performance
constraints of the live react-three-fiber console.

## 0. What the live scene gives me to build on

The live scene fits the real full-extent CUDEM tileset into a synthetic frame.
`SCENE_WIDTH` is 120 units and the tileset is uniformly scaled so its bounding
sphere diameter equals 120, so the sphere radius is 60 units and true relief is
preserved with no vertical exaggeration. The served footprint is lat 48.40 to
48.70 and lng -123.25 to -122.75, a half-diagonal of about 24.8 km on the ground.
That gives a world scale of about 0.0024 scene units per metre, so a 700 m San
Juan ridge is about 1.7 units tall and a point 100 km away sits about 240 units
from the origin. The camera far plane in the live scene is 800 units and in the
journey scene is set to `radius * 100`, so a decorative horizon ring placed at
150 to 300 units is well inside the frustum. These numbers anchor every distance
and height recommendation below.

The realism rig already supplies sun, ambient, hemisphere lights, a linear
distance fog on `scene.fog`, and an elevation-driven sky color on
`scene.background`. The tile meshes load with their glTF standard materials and
the tiles hook flags them as shadow casters and receivers. The palette module
already defines the land color ramp the operator sees, `LAND_LOW` is `#3f6b3a`
and `LAND_HIGH` is `#9aa886`.

## 1. Land that reads as living, not bare tan relief (Terrain Stylist)

### 1.1 Problem

The tile glTF materials carry a near-uniform tan vertex or texture color, so the
islands read as bare relief. The fix is to make color, roughness, and surface
normal vary with elevation and slope so low flat ground reads as vegetated, steep
faces read as rock and bluff, and the shoreline reads as a distinct band, without
replacing the real CUDEM geometry.

### 1.2 Technique A, shader-injected elevation and slope biome tint (recommended)

Override or patch the tile material so the fragment color is a biome ramp driven
by world-space height and by slope, which is the dot of the surface normal with
up. Low and flat is forest green near `#3f6b3a`, mid elevation is a drier
grass-tan, steep faces blend toward a rock gray, and a narrow band just above
sea level reads as shoreline. This is the same height-and-slope masking that the
current production terrain libraries implement, for example the slope mask and
height layering in `@interverse/three-layered-material` and the default
slope-plus-height material in `@interverse/three-terrain-lod`. The same masking
is expressible in core three with `onBeforeCompile` on a `MeshStandardMaterial`
or in the Three.js Shading Language with `triplanarTexture` and a `dot(normal, up)`
slope term.

Why this is the recommendation. It needs no external imagery download, so it
carries no third-party provenance burden and no tile-alignment risk. It is honest,
the tint is derived from the rendered CUDEM geometry, not presented as a survey of
real vegetation. It is cheap, a per-fragment color computed from attributes
already on the mesh, no extra draw calls and no extra textures. It reuses the
existing palette so the live scene and the realism module agree on color.

Sources. Three.js Shading Language reference,
`https://github.com/mrdoob/three.js/wiki/Three.js-Shading-Language`, documents
`triplanarTexture(textureX, textureY, textureZ, scale, position, normal)` and the
material node hooks `colorNode`, `roughnessNode`, `normalNode`.
`@interverse/three-layered-material`,
`https://github.com/aiira-co/three-layered-material`, MIT, documents slope masks
`useSlope` with `slopeMin` and `slopeMax`, height masks `useHeight`, triplanar
mapping, and per-layer color tint. `@interverse/three-terrain-lod`,
`https://registry.npmjs.org/@interverse/three-terrain-lod`, documents a default
slope-and-height terrain material with `setSlopeThreshold`, `setSnowHeight`, and
Sobel normals.

### 1.3 Technique B, draped open landcover imagery (richer, flagged for decision)

Drape a real landcover classification over the terrain as a color or splat
texture, projected by lat and lng, so forest, grassland, cropland, built-up, and
water classes each map to a tuned tint and roughness. This reads as place-true
land cover rather than a procedural guess.

Open-data sources and licenses.

- ESA WorldCover 10 m 2021 v200. Eleven-class global land cover at 10 m. License
  Creative Commons Attribution 4.0 International. Delivered as Cloud Optimized
  GeoTIFF tiles in EPSG:4326 and also available as a Terrascope WMS at
  `https://services.terrascope.be/wms/v2` with layer `WORLDCOVER_2021_MAP`, and on
  the AWS Open Data Registry buckets `s3://esa-worldcover-s1` and
  `s3://esa-worldcover-s2`. Required attribution text, "© ESA WorldCover project
  2021 / Contains modified Copernicus Sentinel data 2021 processed by ESA
  WorldCover consortium". Source, `https://esa-worldcover.org/en/data-access`.
- USGS Annual NLCD, Collection 1.1. Land cover for the conterminous United States
  at 30 m, 1985 to 2024. License Creative Commons Zero 1.0 Universal, public
  domain. Available via the MRLC WMS, EarthExplorer, and Amazon S3. Source,
  `https://www.mrlc.gov/data/project/annual-nlcd`. Note that NLCD covers the US
  side only, so the Canadian Gulf Islands inside the extent would need WorldCover.

Recommendation on B. ESA WorldCover is the better fit because it covers the whole
Salish extent including the Canadian islands at 10 m, where NLCD stops at the
border. The cost is a one-time fetch of the 3 by 3 degree tile that contains the
extent, a reproject and crop to the served bounds, hosting the cropped raster
next to the existing tileset, and a UV projection that matches `projectToScene`.
The honesty label is "land cover draped from ESA WorldCover 2021, CC BY 4.0, real
classification, color is decorative". I flag the imagery source as an operator
decision because it adds a hosted asset and an attribution surface.

### 1.4 Vegetation, instanced and billboard (optional, performance-gated)

Adding discrete vegetation, low scattered tree clumps near the shoreline and on
low ground, raises the living-land read further. The current performant pattern is
`THREE.InstancedMesh` for one draw call per vegetation type, divided into spatial
chunks so native frustum culling drops off-screen chunks, with distance level of
detail that swaps full geometry for octahedral or billboard impostors in the far
field, and alpha-cutout cards for grass and canopy. Sources, the Codrops fluffy
grass tutorial `https://tympanus.net/codrops/2025/02/04/how-to-make-the-fluffiest-grass-with-three-js/`,
the three.js InstancedMesh docs, the three.js billboards manual
`https://threejs.org/manual/en/billboards.html`, and the three.js impostor pull
request `https://github.com/mrdoob/three.js/pull/22043`.

Recommendation. Defer discrete vegetation to a later pass. The console already
runs a tile-streaming load and a per-frame water depth pre-pass, so adding
hundreds of thousands of instances competes for the same frame budget. The biome
tint in 1.2 buys most of the living-land read for almost no cost. If vegetation is
wanted, scope it to a small instanced count placed by raycast onto the streamed
surface, chunked and impostor-swapped, behind a toggle, and label it decorative.

## 2. A framed horizon, not empty water (Scenic Decorator)

### 2.1 Problem

Beyond the served 24.8 km extent the scene is open water to the far plane, so the
horizon reads as an empty ring. The real Salish horizon is ringed by the Olympics
to the south and southwest, the Cascades and Mount Baker to the east, and
Vancouver Island to the north and northwest. The fix adds decorative surrounding
geometry that is clearly labeled not surveyed.

### 2.2 Technique A, a low-resolution decorative DEM ring (recommended)

Build a coarse terrain ring or skirt that surrounds the served extent out to about
100 to 150 km, sampled from an open global DEM, placed at true scale and true
bearing so Mount Baker sits east and the Olympics sit south. At about 0.0024 units
per metre a 100 km radius is about 240 units, inside the far plane, and Mount Baker
at 3286 m is about 7.9 units tall, a believable distant peak. A skirt ring drops
the outer edge below sea level so there is no visible gap where the served tiles
end. Sources for the skirt-ring pattern, the hello-terrain geometry docs
`https://hello-terrain.kenny.wtf/docs/advanced/terrain-geometry` and the
`@interverse/three-terrain-lod` edge-skirt feature.

Open-data DEM source. AWS Terrain Tiles, the Mapzen-derived global bare-earth DEM
on the Registry of Open Data on AWS, bucket `s3://elevation-tiles-prod`, no AWS
account required, Terrarium PNG height encoding at
`https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png`. It
aggregates open sources, SRTM and NASADEM at mid latitudes, GMTED at low zooms,
NED and 3DEP over the United States, with ETOPO1 for bathymetry. Source,
`https://registry.opendata.aws/terrain-tiles/`. License note, the dataset is a
composite of open providers and the consumer is responsible for the per-source
attribution, so the honesty label reads "distant terrain decorative, sampled from
AWS Terrain Tiles, derived from SRTM, NASADEM, GMTED, not surveyed". A low zoom,
roughly z7 to z9, is enough for a distant silhouette and keeps the fetch and the
mesh small.

### 2.3 Technique B, billboard mountain silhouettes (lighter fallback)

Render the surrounding ranges as a small set of camera-facing billboard cards with
alpha-cutout silhouettes, or impostors rendered once from the low-res DEM, smeared
across the far edge. This is the classic open-world far-horizon trick, lower cost
than a ring mesh and good when the camera stays low and does not fly high enough to
reveal the flat cards. Sources, the GameDev far-horizon thread
`https://gamedev.net/forums/topic/711289-far-away-objects-and-horizon-in-an-open-world-game/`
and the three.js billboards manual. Cost, it does not hold up under the journey's
high establishing shot at about 2500 m, where a flat card reads as flat.

Recommendation. Use the DEM ring in 2.2 as the primary horizon because the journey
includes a high establishing pass that would expose flat billboards, and the ring
holds at true scale and bearing. Keep billboards as a documented fallback for low
end devices behind a toggle.

### 2.4 Aerial perspective and distance fade

Whatever ring is used must fade into the sky toward the horizon so it does not read
as a hard wall. The existing linear `scene.fog` already does distance fade, and the
realism `fogColorForSky` already tints fog toward sea haze. The ring should share
that fog and that tint so it dissolves into the horizon the way the served tiles
do. This is the aerial-perspective read without a post-processing pass.

## 3. Sky, fog, and sun-tinted haze refinement (Scenic Decorator)

### 3.1 Current state

The sky is a single elevation-driven flat color on `scene.background`, blended from
night navy to marine day blue, and the fog is a linear distance fog tinted toward
sea haze. There is no sun disc, no horizon glow, and no Rayleigh or Mie gradient,
so the sky reads as a flat gradient.

### 3.2 Technique A, the core three Sky object, Preetham model (recommended)

The three.js distribution ships a procedural physical-sky object, `Sky` from
`three/addons/objects/Sky.js`, which implements the Preetham analytic daylight
model with `turbidity`, `rayleigh`, `mieCoefficient`, `mieDirectionalG`, and a
`sunPosition` uniform. It is a single large dome mesh, one draw call, no
post-processing, and it produces the sun disc, the horizon glow, and the
sky-to-horizon gradient that give an aerial-perspective read for free. Crucially it
is part of the three addons already vendored with `three`, the same import family
as the `three/addons/libs/meshopt_decoder.module.js` the tiles hook already uses,
so it adds no new npm dependency and respects the no-new-engine lock. The decorator
drives `sunPosition` from the existing `makeSun().direction` so the sky, the
directional light, and the water glitter all agree. Sources, the three.js sky
example `https://github.com/mrdoob/three.js/blob/dev/examples/webgl_shaders_sky.html`
and the Preetham reference shader `https://github.com/Tw1ddle/Sky-Shader`.

### 3.3 Technique B, precomputed atmospheric scattering with aerial perspective (flagged, heavier)

`@takram/three-atmosphere`, `https://www.npmjs.com/package/@takram/three-atmosphere`,
is the current production implementation of Bruneton precomputed atmospheric
scattering for three and r3f, with a `Sky`, a `SkyLight`, a `SunLight`, and an
`AerialPerspectiveEffect` post-processing pass, and it is what the recent three.js
3D-tiles example uses for sky and aerial perspective. It is more physically correct
than Preetham, including true distance inscatter on the terrain.

Recommendation against B for this waveset. It is a new npm dependency, it requires a
full post-processing pipeline with a deferred lighting pass and unlit albedo
materials, and that pipeline collides with the existing per-frame water2 depth
pre-pass and the no-new-engine lock. The cost-to-fit is high. I record it as the
upgrade path if the operator later lifts the no-new-dependency posture.

### 3.4 Fog refinement without new dependencies

Keep the realism linear fog as the distance-haze base. Refine it as set dressing by
tuning near and far to the new horizon ring distance and by tinting the fog color
toward the sun azimuth so the haze warms on the sun side, using the existing
`fogColorForSky` and `skyColor` helpers and the existing
`web/lib/scene/atmosphere/transition.ts` tweens, which already operate on a
`THREE.Fog` or `THREE.FogExp2` without touching realism internals. A switch to
`THREE.FogExp2` gives a softer, more exponential horizon falloff if the linear fog
reads as a hard band against the new ring, and the transition module already
supports a `density` target.

## 4. Performance budget and constraints

- The console is a live r3f scene already carrying tile streaming and a per-frame
  opaque depth pre-pass for water2. New work must not add a second full-screen pass.
- Terrain tint in 1.2 is per-fragment on existing meshes, effectively free.
- The Sky object in 3.2 is one dome mesh, one draw call.
- The horizon ring in 2.2 is one low-poly mesh built once from a small low-zoom DEM
  fetch, frustum-culled, and shares the existing fog.
- Discrete vegetation in 1.4 is the only item that can blow the frame budget, which
  is why it is deferred and toggle-gated.
- All new geometry shares the existing camera far plane of 800 units in the live
  scene, so the ring radius stays at or below about 300 units.

## 5. Honesty and provenance summary

| Surface | Source | License or basis | Honesty label |
| --- | --- | --- | --- |
| Terrain biome tint | derived from rendered CUDEM height and slope | no external data | derived tint, real CUDEM geometry, color is interpretive |
| Optional landcover drape | ESA WorldCover 2021 v200 | CC BY 4.0, attribution required | land cover from ESA WorldCover 2021, real classification, color decorative |
| Optional US-only landcover | USGS Annual NLCD | CC0 1.0 public domain | land cover from USGS NLCD, US side only |
| Horizon DEM ring | AWS Terrain Tiles, Mapzen-derived | composite of SRTM, NASADEM, GMTED, attribution per source | distant terrain decorative, not surveyed |
| Sky and sun glow | three Sky object, Preetham | core three addon, no new dep | atmosphere effect, not a measured sky |
| Fog and haze | realism rig, retuned | existing module | atmosphere effect |

## 6. Recommendation in one line per problem

- Living land, ship the elevation-and-slope biome tint by shader injection on the
  tile material. Offer the ESA WorldCover drape as an operator-gated upgrade.
- Framed horizon, ship a true-scale decorative DEM ring from AWS Terrain Tiles that
  shares the scene fog. Keep billboard silhouettes as a low-end fallback.
- Sky and haze, ship the core three Sky object driven by the existing sun, retune
  the existing fog, no post-processing and no new dependency.
