# R3: Chart and Topographic Cartography for a 3D Bathymetry+Terrain Twin

Agent: R3 chart-cartography. Spike: `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/`.
Question: how to give a 3D bathymetry+terrain model a cartographic look ("styled like the map"),
covering nautical-chart portrayal (IHO S-52 / S-57 / S-101) and topographic/bathymetric
cartography (hypsometric tints, hillshade), and how to do it in a real-time three.js/WebGL scene.

Stack this maps onto: Next.js + react-three-fiber + three@0.169 + `3d-tiles-renderer@0.4.28`,
OGC 3D Tiles baked from NOAA NCEI CUDEM 1/9 arc-second topobathy, NAVD88 m, EPSG:32610,
San Juan Islands / Haro Strait, Gerstner water plane at scene Y 0. Modeled, not measured.

---

## 1. Nautical chart portrayal standards

### 1.1 IHO S-52 (the ECDIS presentation standard)

S-52 is the IHO "Specifications for Chart Content and Display Aspects of ECDIS". The relevant
current edition is **S-52 Edition 6.1.1, June 2015**, with the colour and symbol rules carried in
its annexed **Presentation Library**
(https://iho.int/uploads/user/pubs/standards/s-52/S-52%20Edition%206.1.1%20-%20June%202015.pdf).
S-52 defines *how* the vector data of an ENC is drawn, separate from the data standard itself.

Key portrayal mechanics relevant to a styled 3D model:

- **Colour tokens, not raw RGB.** S-52 specifies ~63-64 named colour tokens given as CIE Yxy
  chromaticity + luminance, which the manufacturer converts to RGB per display palette. There are
  five palettes for ambient light: DAY BRIGHT, DAY WHITE BACK, DAY BLACK BACK, DUSK, NIGHT. The
  palette swap (bright greyish-blue by day, dark violet/near-black by night) exists to preserve a
  mariner's night vision, the same idea as a car GPS dimming at night
  (http://corbajava.waveman.com/2014/05/s-57-styling-enc-group-1-classes-skin.html).

- **The depth-area shades.** The water body (feature class `DEPARE`, depth area) is filled with a
  small ordered set of depth-zone tokens. With concrete DAY-BRIGHT RGB values from the published
  S-52 Appendix A tables
  (https://440148.fs1.hubspotusercontent-na1.net/hubfs/440148/ECDIS%20white%20paper.pdf):

  | Token | Meaning | Day-bright RGB | Note |
  |---|---|---|---|
  | `DEPIT` | Intertidal (dries) | 85,157,112 | yellow-green |
  | `DEPVS` | Very shallow | 105,156,206 | medium blue (darkest water) |
  | `DEPMS` | Medium shallow | 127,177,203 | light blue |
  | `DEPMD` | Medium deep | 154,195,190 | pale blue |
  | `DEPDW` | Deep water | 185,214,192 | near-white (safe water = white) |
  | `LANDA` | Land | soft yellow / light brown | |

  The defining convention: **deeper = whiter, shallower = bluer**, the opposite of the intuitive
  "ocean is dark blue". This is deliberate so the dangerous shallow water is the visually loud
  colour. Land is a buff yellow.

- **Two-shade vs four-shade banding.** The number of shades is driven by mariner-set contours, not
  by a fixed ramp
  (https://north-standard-staging.s3.eu-west-2.amazonaws.com/wp-content/uploads/2024/04/04091156/NS-ECDIS-Safety-Settings-SHIPS.pdf,
  https://knowledgeofsea.com/ecdis-contour-settings/):
  - **Two-shade (default):** one **safety contour** divides the sea into blue (unsafe, shoaler than
    safety contour) and white (safe, deeper). Simple anti-grounding view.
  - **Four-shade (optional):** mariner also sets a **shallow contour** (default ~2 m) and **deep
    contour** (default ~30 m). The blue splits into dark/light blue, the white splits into grey/white,
    giving the five-zone ramp above. The standard warns four shades reduce safe/unsafe contrast and
    are not recommended at night.
  - The **safety contour is always emphasised** (a thicker, bolder line) and is redundantly coded
    (both a heavy line and a sharp colour step), per S-52's ergonomics rules. If the mariner's chosen
    safety value is not present in the data, ECDIS defaults to the **next deeper** available contour.

- **Depth contours / isobaths.** Drawn by line class `DEPCNT`. Standard ENC contour set is sparse
  (e.g. 2, 5, 10, 20, 30, 50, 100, 200 m), not an even ramp. Contours are foreground over the area
  fills.

- **Soundings.** Point class `SOUNDG`, drawn as small depth-number labels using a dedicated digit
  font; in "Standard" display the sounding layer is often omitted because the four area shades carry
  enough anti-grounding info. Soundings are referenced to chart datum (typically Lowest Astronomical
  Tide), not the depth-area datum.

- **Layering / display priority.** S-52 assigns each feature a Display Priority 0-9; areas (skin of
  the earth) lay down first, then lines, then point symbols on top. For a 3D drape this maps directly
  to render order / polygon offset.

### 1.2 S-57 and S-101 (the data standards under the portrayal)

- **S-57** is the legacy ENC vector transfer standard. With S-52 it forms today's ECDIS pair: S-57 =
  data, S-52 = portrayal via fixed Conditional Symbology Procedures (CSPs).

- **S-101** is the next-generation ENC product specification built on the **S-100** Universal
  Hydrographic Data Model; S-101 Edition 2.0.0 (2024-12-27, S-100 v5.2.0) is the first operational
  edition (https://registry.iho.int/productspec/view.do?product_ID=S-101). It will replace S-57.
  Differences that matter for styling
  (https://www.hydro-international.com/content/article/s-101-the-new-iho-electronic-navigational-chart-product-specification,
  https://docs.iho.int/mtg_docs/com_wg/TSMAD/TSMAD24/TSMAD24-DIPWG4-10.3C_S-101_info_paper_JLP.pdf):
  - Portrayal moves from S-52's rigid CSPs to a **machine-readable Portrayal Catalogue** (rule-based,
    Lua-scripted) shipped as part of the S-100 ecosystem. Depth areas are feature `DepthArea` with
    `depthRangeMinimumValue` / `depthRangeMaximumValue` attributes, so a renderer can band by range.
  - Pre-computed feature relationships (e.g. a wreck and its surrounding depth area) are encoded in
    the data, reducing on-the-fly symbology computation.
  - Crucially, S-101 is designed to keep the **same familiar look and feel** as S-57/S-52 charts, so
    the depth-shade conventions above are still the visual target.

- **S-102 Bathymetric Surface** is the companion S-100 product for high-resolution **gridded
  bathymetry** (HDF5; band 1 = depth, band 2 = uncertainty), GDAL-readable
  (https://gdal.org/en/latest/drivers/raster/s102.html). This is the natural format for a continuous
  surface drape (it is what R2's sounding/grid work feeds), with S-101 supplying the chart vectors on
  top.

---

## 2. Topographic / bathymetric cartography (the "map" look on a continuous surface)

Where S-52 bands a vector polygon into a few safety-driven zones, topo/bathy cartography colours a
*continuous* elevation surface. The two combine well: a continuous tint underneath, chart isobaths
on top.

- **Hypsometric tints (land) + bathymetric tints (sea).** Elevation-driven colour ramps: land low =
  green, rising through tan to brown/white at peaks; sea light blue at the shore to dark blue/purple
  at depth. A **combined topo-bathy** map runs one diverging ramp across the 0 m coastline. The
  oceanographic reference colormaps are **cmocean** (Thyng et al., "True colors of oceanography",
  *Oceanography* 29(3):9-13, 2016, https://matplotlib.org/cmocean/): `deep` (light yellow-green to
  dark blue/purple with depth) for bathymetry and `topo` (a fused land+sea diverging map). The
  classic GMT bathymetry palette is `gmt/gebco`
  (https://github.com/GenericMappingTools/gmt/blob/master/src/gmt_cpt_masters.h). These are
  perceptually uniform, unlike the S-52 ENC ramp which is tuned for safety contrast rather than
  perceptual evenness.

- **Hillshade / relief shading.** The detail that makes terrain read as terrain. Compute a surface
  gradient and light it from an artificial sun (azimuth + elevation), then multiply the intensity
  into the colour. GMT's reference workflow is `grdgradient` (gradient, with an inverse-tangent
  normalisation so bathymetric slopes fall sensibly in [-1, 1]) feeding the `-I` intensity input of
  `grdimage`/`grdview`
  (https://docs.generic-mapping-tools.org/6.5/tutorial/bash/session-4.html,
  https://docs.generic-mapping-tools.org/dev/grdview.html). Same azimuth-light shading is what
  `grdview` uses for its 3-D perspective surfaces.

- **Contour generation.** Two routes: (a) precompute isolines from the grid as vector geometry
  (marching squares), or (b) derive them on the fly from height. For a chart look, precomputed
  isobaths at standard chart depths give clean, labelable lines; procedural in-shader banding gives
  cheap dense contours that always match the rendered surface.

- **Combined topo-bathy 3-D.** GMT `grdview` is the canonical reference for the exact thing we want:
  a colour-coded, artificially illuminated 3-D perspective surface with contours drawn on top and an
  optional *drape* of a separate raster over the relief (`-G drapegrid`)
  (https://docs.generic-mapping-tools.org/dev/grdview.html). Our three.js scene is effectively a
  real-time `grdview`.

---

## 3. Doing it in a real-time three.js / WebGL scene

All of the above reduces to a `ShaderMaterial` on the terrain/tiles, driven by world height (Y), plus
optional draped textures and billboarded labels.

### 3.1 Depth/height color ramp from world height
Pass world-space height as a varying and sample a 1-D gradient texture (or `mix()` between stops) in
the fragment shader (https://stackoverflow.com/questions/75961582/how-to-color-a-steep-plane-based-on-its-height-using-vertex-shader):

```glsl
// vertex
varying float vWorldY;
void main() {
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWorldY = wp.y;                 // metres, NAVD88-ish in scene units
  gl_Position = projectionMatrix * viewMatrix * wp;
}
// fragment
uniform sampler2D uRamp;          // 1xN gradient: cmocean deep / topo, or S-52 zone LUT
uniform float uMinY, uMaxY;
varying float vWorldY;
void main() {
  float t = clamp((vWorldY - uMinY) / (uMaxY - uMinY), 0.0, 1.0);
  gl_FragColor = texture2D(uRamp, vec2(t, 0.5));
}
```
A gradient **texture** beats a chain of `if`s and lets us hot-swap "cmocean smooth" vs "S-52 stepped"
by just changing the LUT (use `NearestFilter` on the LUT for hard S-52 bands, `LinearFilter` for
smooth hypsometric tints).

### 3.2 Isobath contour lines in-shader (mod/fract banding)
The community-standard trick: take `fract(height / interval)`, measure its screen-space derivative
with `fwidth()`, and `smoothstep()` to draw a constant-pixel-width antialiased line regardless of
camera distance or slope
(https://discourse.threejs.org/t/drawing-isolines-using-shaders/54382,
https://stackoverflow.com/questions/73630925/contour-line-and-contour-tree,
https://www.gamedev.net/forums/topic/529926-terrain-contour-lines-using-pixel-shader/):

```glsl
uniform float uInterval;   // e.g. 10.0 m between isobaths
uniform float uThickness;  // line width in px
varying float vWorldY;
float contour(float h) {
  float f  = fract(h / uInterval);
  float w  = fwidth(h / uInterval);
  return 1.0 - smoothstep(w, w * uThickness, min(f, 1.0 - f));
}
```
Needs screen-space derivatives: in three@0.169 / WebGL2 `fwidth` is available by default
(`#extension GL_OES_standard_derivatives` only for the old WebGL1/RawShaderMaterial path
(https://discourse.threejs.org/t/shader-to-create-an-offset-inward-growing-stroke/6060)).
Trade-off: in-shader contours are free and always match the surface but cannot carry depth labels and
shimmer on near-vertical faces; **precomputed contour geometry** (marching squares to a `LineSegments`)
gives crisp, labelable, chart-standard isobaths at the cost of an offline pass and draw calls. For
orcast: use both, procedural for dense minor contours, precomputed only for the few labeled standard
isobaths and the emphasised safety contour.

### 3.3 Hillshade in-shader
Reconstruct the normal (from the tile's geometry normals or via `dFdx/dFdy` of world position) and
dot it with a fixed sun direction; multiply the result into the ramp colour. This reproduces GMT's
azimuth lighting without a precomputed intensity grid. Standard three.js lighting on the tiles also
works, but an explicit hillshade term gives the cartographic, sun-from-NW relief look and is what the
Cesium bathymetry guide recommends adding for legibility (see 3.5).

### 3.4 Chart raster drape vs procedural shading
- **Procedural (recommended primary):** shade from height/normal in the shader as above. Resolution-
  independent, no tiles to stream, restyleable live, and it always lines up with the geometry. This is
  the analogue of GMT colouring the surface directly.
- **Raster drape:** sample an existing rendered chart/map image (S-57 WMS tiles, OpenSeaMap,
  topo WMTS) as a texture in UV/world space, the analogue of `grdview -G drape`. Gives "exactly the
  official chart" pixels and real symbology for free, but is a flat picture: it does not re-light, can
  misregister against the mesh, and adds a tile pipeline. This is exactly how the S-102 Demonstrator
  drapes S-57 chart tiles + topo WMTS over its bathymetry (see 3.5). For orcast, treat a chart-raster
  drape as an **optional toggle layer** over the procedural surface, not the base look.
- **Hybrid:** procedural depth tint + hillshade as the base, precomputed isobath/safety-contour
  vector overlay, optional chart-raster drape blended on top with an opacity slider.

### 3.5 Labels and soundings as billboards
Depth numbers (`SOUNDG`) and contour labels are screen-facing text. In r3f use
`@react-three/drei` `<Billboard>` + `<Text>` (SDF text), or sprite-based labels, anchored at world
positions sampled from the grid, with distance-based culling/declutter so labels do not pile up. Keep
them as a togglable layer, consistent with S-52 "Standard" display hiding soundings by default.

---

## 4. Prior art / examples

- **Cesium World Bathymetry + CesiumJS** (Jan 2024): a global fused GEBCO+high-res bathymetry+land
  tileset, with an official guide on styling it for the cartographic look: scene **lighting** for
  relief, **vertical exaggeration**, a procedural **oceanographic colour ramp**, and **elevation
  contour lines** with invertible colour, plus the advice to ship a **legend**
  (https://cesium.com/blog/2024/01/23/introducing-cesium-world-bathymetry/,
  https://cesium.com/blog/2024/01/29/cesium-world-bathymetry-in-cesiumjs/). The single closest match
  to orcast's goal and a confirmation of the recipe in section 3.
- **deck.gl `ContourLayer`**: GPU isoline/isoband generation from gridded values, an alternative for
  the contour layer if we ever move bathymetry into deck.gl
  (https://matom.ai/insights/cesium-vs-deck-gl/).
- **S-102 Demonstrator (s102.no, Kongsberg "Cogs" 3D toolbox)**: real 3-D viewer of S-102 gridded
  bathymetry with a dynamic LOD tile pyramid, draping **S-57 chart tiles (ECC WMS)** plus land
  imagery and topographic WMTS, and explicitly handling **mixed vertical datums** (LAT for sea, MSL
  for land) by displaying them at a common origin (https://s102.no/3d-visualisation-tool/). Direct
  precedent for the raster-drape + datum-reconciliation issues orcast faces.
- **GMT `grdview`/`grdimage`**: the canonical non-real-time reference for colour ramp + hillshade +
  contours + drape on a 3-D surface (https://docs.generic-mapping-tools.org/dev/grdview.html); good
  for generating baked reference imagery / a legend / a "ground truth" comparison render.
- **OpenSeaMap**: free, OSM-based nautical chart tiles (with GEBCO bathymetry) usable as a drape layer
  source. **Navionics 3D / Garmin and C-MAP** are commercial nautical apps with 3-D
  "SonarChart"/relief views; useful as visual targets but proprietary and not navigation-authoritative
  for our purposes.

---

## Implications for orcast

**Recommended portrayal (base look):**

1. **Procedural depth+elevation tint from world height** via a swappable 1-D LUT texture, with two
   presets:
   - *Cartographic-chart preset:* the **S-52 depth-shade convention** (deep = near-white, shallow =
     blue, land = buff, intertidal = yellow-green), implemented as a **stepped** LUT
     (`NearestFilter`) banded at standard chart isobaths. This makes the model read unmistakably as a
     nautical chart.
   - *Scientific preset:* **cmocean `topo`/`deep`** continuous tint (`LinearFilter`) for a clean
     combined topo-bathy look when the audience wants realism over chart styling.
2. **Hillshade term in the shader** (sun from the NW, gentle exaggeration) multiplied into the tint,
   so terrain and seafloor relief is legible. This is the single most important fix for the "land
   looks flat/wrong" complaint and is exactly what the Cesium bathymetry guide prescribes.
3. **Isobaths as a two-tier overlay:** procedural `fwidth`-based minor contours for dense, always-
   matching banding, plus a small set of **precomputed standard isobaths** (2, 5, 10, 20, 30, 50, 100,
   200 m) as `LineSegments`, with the **safety contour emphasised** (thicker, distinct colour) per
   S-52.
4. **Optional layers, off by default:** sounding/contour **labels as billboards**, and an optional
   **chart-raster drape** (OpenSeaMap or NOAA ENC tiles) blended over the procedural surface with an
   opacity slider, following the S-102 Demonstrator pattern.

**Which standard to follow:** target the **S-52 depth-shade portrayal convention** for the
chart-styled look (it is the recognised "looks like a nautical chart" aesthetic, and S-101 keeps the
same look), but implement it as a **simplified, inspired-by** style, not a certified ECDIS renderer:
we are not ECDIS, the data is CUDEM-derived and labeled "modeled, not measured", and full S-52 CSP
compliance is out of scope. Where orcast wants scientific realism instead of chart styling, fall back
to **cmocean** (Thyng et al. 2016) for perceptually uniform tints. Treat **S-102** as the right target
format for the underlying continuous bathymetry grid and **S-101** as the vector source if we later
ingest real ENC features.

**Caveats to honour:** the S-52 ramp is "deeper is whiter", the opposite of intuitive ocean colour,
so a legend is mandatory; S-52 colours are CIE-defined per day/dusk/night palette, so the RGB values
above are the day-bright approximation only; and chart datum for soundings (LAT) differs from our
NAVD88 surface datum, so any sounding labels and any draped chart raster must be datum-reconciled (as
the S-102 Demonstrator does) before they line up with the mesh.
