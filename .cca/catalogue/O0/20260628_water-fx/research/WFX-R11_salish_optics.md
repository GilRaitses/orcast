# WFX-R11 salish-optics findings

Role WFX-R11, read-only research, WATER-FX Wave 1. Owner of this one file only.
Repo state verified against origin/main `915e4cc77923de93ed5f7e9a75feab9eb2e12896`.
Honesty label holds: modeled, not measured. Target water is the turbid green Salish
Sea (high CDOM, high turbidity, seasonal phytoplankton), not tropical blue.

Topic: the real optical properties of the Salish Sea, translated into truthful sRGB
color targets and per-channel extinction ratios that feed WFX-R09's RGB Beer-Lambert
honestly. The central claim I have to defend with citations is that this water is
green-grey because green light penetrates deepest here, the opposite of clear ocean
where blue wins.

---

## 1. Scope and current state (file-cited)

### 1.1 The too-blue defaults today

`web/lib/scene/water2/depthWater.ts` sets the live water palette at lines 110 to 113:

```110:113:web/lib/scene/water2/depthWater.ts
const DEFAULT_SHALLOW = new THREE.Color("#2e6f9e");
const DEFAULT_DEEP = new THREE.Color("#0a2540");
const DEFAULT_FOAM = new THREE.Color("#dfeef5");
const DEFAULT_SKY = new THREE.Color("#9fc4e0");
```

`#2e6f9e` is a medium ocean blue with the blue channel dominant (R 46, G 111, B 158).
`#0a2540` is a near-navy (R 10, G 37, B 64). Both are blue-dominant. Read against the
regional optics in section 2, both are too tropical-blue. The seabed read uses these
through the two-stop lerp at line 260:

```256:260:web/lib/scene/water2/depthWater.ts
    float colorT = 1.0 - exp(-column / max(uDepthColorScale, 1e-4));
    float depthAlpha = 1.0 - exp(-column / max(uDepthAlphaScale, 1e-4));
    depthAlpha *= uMaxOpacity;

    vec3 base = mix(uColorShallow, uColorDeep, colorT);
```

The WS-BATHY stylist already nudged the defaults toward teal in
`web/lib/scene/bathy/style/waterTuning.ts` at lines 28 to 41, `WATER_TUNED_SHALLOW =
"#2f8fa6"` and `WATER_TUNED_DEEP = "#0b2140"`. The shallow value `#2f8fa6` is a cyan
teal (R 47, G 143, B 166), still blue-dominant. The deep value `#0b2140` is even more
navy than the water2 default. Both still encode a blue-ocean assumption.

### 1.2 The proposed coefficients I have to ground or correct

`web/lib/scene/bathy/style/waterTuning.ts` lines 55 to 59 export the per-channel
extinction the absorption upgrade would adopt:

```55:59:web/lib/scene/bathy/style/waterTuning.ts
export const PROPOSED_RGB_EXTINCTION: { r: number; g: number; b: number } = {
  r: 3.0,
  g: 1.6,
  b: 0.9,
};
```

`web/lib/scene/bathy/style/WATER2_TUNING_REQUEST.md` lines 24 to 26 states the
rationale, "Real water absorbs red fastest and blue slowest, so deep water shifts
blue-green toward navy and violet by physics." That sentence is true for clear open
ocean. It is false for the Salish Sea. The proposed vector puts blue at the lowest
extinction (`b: 0.9`), so blue survives deepest and the deep read goes navy/violet.
Section 3 corrects this. The single wrong value is the blue coefficient. It must
become the highest channel, not the lowest.

---

## 2. Optics survey with URLs

### 2.1 The one regional, in-situ study that settles the ordering

Loos, Costa and Johannessen 2017, "Underwater optical environment in the coastal
waters of British Columbia, Canada," FACETS 2, 872-891, open access, CC BY 4.0.
https://doi.org/10.1139/facets-2017-0074

This is the directly applicable paper. It measured the underwater light field of the
Strait of Georgia, the northern half of the Salish Sea, in spring and summer, with
HydroLight radiative transfer closure. Its findings I rely on:

- Reflectance is lowest at 400 to 450 nm (purple to blue) and peaks at 520 to 640 nm
  (yellow to green). The yellow-green band is "the portion of the electromagnetic
  spectrum that penetrates the most deeply" (Abstract and Results, "Optical dynamics").
- Three optical water masses. OM1 is the turbid Fraser River plume. OM2 is mixed
  plume and Strait water. OM3 is the clearer northern and deeper water.
- Measured downwelling attenuation coefficient KEd by band, from Table 2, units per
  metre, listed mean by season as April and July:

| Band | wavelength | OM3 deep/clear | OM2 mixed | OM1 plume |
| --- | --- | --- | --- | --- |
| blue | 411 nm | 0.48 / 0.43 | 0.75 / 0.73 | 2.28 / 2.01 |
| green | 530 nm | 0.15 / 0.15 | 0.26 / 0.26 | 0.69 / 0.84 |
| red | 650 nm | 0.42 / 0.42 | 0.52 / 0.49 | 0.68 / 0.87 |
| red | 675 nm | 0.48 / 0.45 | 0.69 / 0.61 | 0.87 / 1.01 |

  Green at 530 nm is the lowest attenuation in every water mass and every season. Blue
  at 411 nm is the highest in the clearer and mixed water, and far the highest in the
  plume. This is the inversion that matters for the shader. Green penetrates deepest
  here, blue dies first.
- "Red and blue light were attenuated to <1% of their surface intensity within the
  uppermost 5 m, whereas green and yellow light persisted to about 20 m" (Conclusions).
- Euphotic depth Z1%, the depth of 1% surface PAR, was 6.0 to 22.0 m in spring and 4.0
  to 23.0 m in summer. Blue at 443 nm reached 1% always shallower than 9 m and often
  shallower than 5 m ("Scalar irradiance and the average cosine," and Conclusions).
- Jerlov classification of the masses. In July the clear OM3 matched Jerlov coastal
  Type 1. In April OM3 sat between Jerlov Types 3 and 5. The turbid plume OM1 exceeded
  the most turbid Jerlov coastal Type 9 above 500 nm. So the Salish Sea spans Jerlov
  coastal Type 1C through past 9C, with the typical non-plume water near Type 3C to 5C
  ("Optical dynamics," reading Fig. 3).
- The diffuse-light measure, average cosine at 411 nm, was about 0.7 in the turbid
  plume and rose to 0.9 in clear deep water, confirming a strongly scattering, hazy
  light field in the turbid surface layer (Table 2 and Conclusions).
- Drivers. High backscattering by inorganic suspended particles plus high CDOM
  absorption. Suspended particle load 6.9 mg/L in April and 9.9 mg/L in July, CDOM
  absorption 1.0 per metre in April and 0.53 per metre in July, citing Loos and Costa
  2010 (Results, "Hydrographic data" and "Optical dynamics").

The underlying IOP source the paper builds on is Loos and Costa 2010, "Inherent
optical properties and optical mass classification of the waters of the Strait of
Georgia," Progress in Oceanography 87, 144-156.
https://doi.org/10.1016/j.pocean.2010.09.004

### 2.2 CDOM source and seasonality

Most of the blue-killing absorption is terrestrial humic CDOM washed in by rivers, led
by the Fraser. The Bellingham Bay study confirms the source and the season.

Cawley et al. 2025, "Assessing riverine inputs versus in situ production as sources of
chromophoric dissolved organic matter in Bellingham Bay in the Salish Sea," Aquatic
Sciences. https://doi.org/10.1007/s00027-025-01264-1

It found riverine input the primary CDOM source year round, a dominant terrestrial
humic-like component in all samples, and the highest CDOM absorption at 300 nm in the
fall after the first rains flush the watershed. CDOM absorbs most strongly in the UV
and blue and falls off toward the red, which is exactly the spectral shape that
suppresses the blue channel in the Salish Sea.

### 2.3 Phytoplankton seasonality, the green

Spring diatom blooms run roughly April to May in the Salish Sea, with the surviving
in-water light field already green-dominant. The ferry-monitoring brief states the
"spring plankton blooms that occur between April and May" and confirms the optical
monitoring of chlorophyll, turbidity, and CDOM together on the Seattle to Victoria
transit. Washington Department of Ecology publication 18-03-017, Sackmann and Newton.
https://apps.ecology.wa.gov/publications/documents/1803017.pdf

Chlorophyll adds a green-leaning absorption with a red absorption dip near 675 nm and a
fluorescence bump near 685 nm, both observed in the reflectance spectra of the FACETS
paper. The net effect of CDOM plus chlorophyll plus inorganic turbidity is a
reflectance window centred on green, not blue.

### 2.4 Secchi depth and water clarity ranges

Direct marine Secchi numbers for the open Sound are sparse because the agencies prefer
beam transmissometers, but the magnitudes triangulate to a turbid, single-digit-metre
clarity.

- King County reports summer Secchi depth "typically around 3 to 5 meters" in the
  regional lakes, and the marine program reports clarity with transmissometers rather
  than Secchi. https://green2.kingcounty.gov/lakes/Sampling.aspx and
  https://green2.kingcounty.gov/marine/Monitoring/
- Washington Department of Ecology runs marine "water visibility" from CTD
  transmissometer profiles, framed for SCUBA horizontal visibility, with the worst
  visibility inside embayments such as Sinclair Inlet, Bellingham Bay, and Lynch Cove,
  and better visibility in South Sound. Ecology publication 17-03-017.
  https://apps.ecology.wa.gov/publications/documents/1703017.pdf
- The FACETS euphotic depths of 4 to 23 m convert to an approximate Secchi range. Using
  the standard relation Secchi is about 1.7 divided by Kd(PAR) and euphotic depth is
  about 4.6 divided by Kd(PAR), Secchi is roughly 0.37 of euphotic depth, so about 1.5
  to 8.5 m across the masses and seasons. That matches the single-digit-metre clarity
  the agency lake and marine numbers imply. I label this a derived estimate, not a
  measured Secchi dataset.

### 2.5 Jerlov coastal IOP reference, for R09 to extend

Solonenko and Mobley 2015, "Inherent optical properties of Jerlov water types,"
Applied Optics 54(17), 5392-5401. https://doi.org/10.1364/AO.54.005392

This gives a self-consistent table of absorption a and scattering b spectra and
chlorophyll for every Jerlov type 1C through 9C, the values that reproduce the Jerlov
Kd spectra in HydroLight. Read with the FACETS classification, the Salish non-plume
water sits near coastal Type 3C to 5C, the plume past 9C. The spectral shape in this
table confirms the regional finding. For the more turbid coastal types the Kd at 450 nm
is roughly double the Kd at 550 nm, so blue attenuation exceeds green attenuation, the
green-deepest ordering again. The Ocean Optics Web Book classification page is the open
companion. https://oceanopticsbook.info/view/inherent-and-apparent-optical-properties/classification-schemes

---

## 3. Recommendations, concrete sRGB targets and extinction ordering

### 3.1 The extinction ordering, stated explicitly

Clear open ocean, Jerlov I to II, attenuates red fastest and blue slowest, so blue
survives to depth and the water reads blue. The proposed vector `{r:3.0,g:1.6,b:0.9}`
and the `WATER2_TUNING_REQUEST.md` rationale encode that clear-ocean ordering. The
Salish Sea inverts it. Pure water still kills the red, but terrestrial CDOM and high
turbidity kill the blue even harder, so the surviving transmission window is green near
530 to 560 nm. The correct ordering for this water is green slowest, then red, with
blue fastest. Source for the ordering is the measured KEd table in section 2.1, Loos,
Costa and Johannessen 2017, https://doi.org/10.1139/facets-2017-0074.

### 3.2 Per-channel extinction ratios for WFX-R09

I normalize the measured KEd to green equals 1.0, because the shader vector is relative
extinction over a column in scene units and the absolute scale stays under
`uDepthColorScale`.

| Water mass | source KEd R,G,B used | ratio R : G : B |
| --- | --- | --- |
| OM3 clear and deep | 0.45, 0.15, 0.46 | 3.0 : 1.0 : 3.0 |
| OM2 mixed nearshore | 0.50, 0.26, 0.74 | 1.9 : 1.0 : 2.8 |
| OM1 turbid plume | 0.80, 0.77, 2.15 | 1.0 : 1.0 : 2.8 |

For the bathymetric depth read the right water mass is OM3, because the deep channels
the shader cares about, the deep Haro Strait channel called out in
`WATER2_TUNING_REQUEST.md` line 52, are exactly the vigorous-tidal-mixing Pacific-fed
water that the paper classed as the clearer OM3 near Jerlov Type 1 to 5.

Recommended replacement for `PROPOSED_RGB_EXTINCTION`, keeping the proposal's overall
magnitude near 3.0 so the existing `uDepthColorScale` tuning still lands:

```
recommended deep-channel vector  { r: 3.0, g: 1.0, b: 3.0 }   // OM3, green wins
nearshore / turbid variant       { r: 2.0, g: 1.0, b: 2.9 }   // OM2, blue dies first
```

Over a 1.0 scene-unit deepest column the recommended vector transmits green at
exp(-1.0) about 0.37, red at exp(-3.0) about 0.05, blue at exp(-3.0) about 0.05, so the
deep read converges to a dark green-grey. The proposed vector instead transmits blue at
exp(-0.9) about 0.41 and green at exp(-1.6) about 0.20, converging to navy. The
difference between the two is the whole bug. Source for the ratios is the KEd table,
Loos, Costa and Johannessen 2017.

### 3.3 sRGB color targets

These are modeled perceptual targets matched to the measured reflectance window, green
peak 520 to 640 nm and blue minimum 400 to 450 nm, from Loos, Costa and Johannessen
2017. They are not CIE conversions from spectra. Each is green-dominant, the green
channel highest, so none of them can read tropical blue.

| Use | shader uniform | recommended sRGB | channels R,G,B | rationale and source |
| --- | --- | --- | --- | --- |
| shallow tint | `uColorShallow` | `#4f8c79` | 79,140,121 | thin water over the seabed reads as living jade green-teal, green peak of the reflectance window, lighter and greener than the blue defaults `#2e6f9e` and `#2f8fa6`. Loos 2017 reflectance peak 520-640 nm. |
| intrinsic deep | `uColorDeep` | `#13302b` | 19,48,43 | a thick column converges to a dark desaturated green-grey, not navy, because only green survives at depth. Replaces `#0a2540` and `#0b2140`. Loos 2017 green-deepest finding. |
| underwater fog | fog color for R08 | `#356f5d` | 53,111,93 | the in-scattered ambient a diver sees, a brighter turbid green, matches the high-scattering hazy light field, average cosine about 0.7 in turbid water. Loos 2017 Table 2 and Conclusions. |

Seasonal and plume variants, optional, same sources:

```
summer bloom / plume shallow   #5fa07a   greener and slightly brighter, peak chlorophyll
clearer winter deep            #15332c   marginally bluer-grey when CDOM and turbidity ebb
turbid plume fog               #4a7a58   more yellow-green, OM1 high inorganic load
```

Leave the Fresnel sky color to WFX-R03 and WFX-R04. I note only that the Pacific
Northwest sky is usually overcast and grey, so the marine-haze `#9fc4e0` should not be
forced to a bright tropical sky blue. That is their call, not mine.

### 3.4 Honesty note

Modeled, not measured. The numbers in section 2 are measured oceanography from the
cited papers. The colors in section 3.3 are modeled targets I chose to match the
measured reflectance shape, they are not a colorimetric inversion and they assert no
measured water color at any specific tile. The extinction vector reads the modeled
CUDEM seabed depth, it asserts no measured depth, consistent with the locked honesty
label in the charter and in `waterTuning.ts` lines 6 to 16. The single defensible claim
is qualitative and well supported, this water is turbid and green because green light
penetrates deepest here.

---

## 4. Frame budget

Not applicable to this topic. My outputs are three sRGB constants and one three-element
extinction vector that feed shader uniforms already present in the
`makeWater2` material at lines 348 to 351 and the requested `uAbsorption` addition.
They add no pass and no per-frame cost. Frame-budget accounting for the absorption math
and the underwater fog belongs to WFX-R13.

---

## 5. Collision and sequencing

This doc is read-only and edits nothing. It feeds four consumers.

- WFX-R09 rgb-absorption. Primary consumer. Takes the extinction ratios in 3.2 and the
  corrected ordering in 3.1 to replace `PROPOSED_RGB_EXTINCTION` in
  `web/lib/scene/bathy/style/waterTuning.ts` lines 55 to 59 and to extend
  `WATER2_TUNING_REQUEST.md`. R09 owns the shader-level Beer-Lambert change in
  `depthWater.ts`, I do not.
- WFX-R08 underwater-volumetrics. Takes the underwater fog color `#356f5d` and the
  green-dominant in-scatter for the `web/lib/scene/underwater/` module W4 will build.
- 3D-TWIN W3 water-upgrade. Takes the shallow and deep sRGB targets as the new defaults
  to replace `DEFAULT_SHALLOW` and `DEFAULT_DEEP` in `depthWater.ts` lines 110 to 111
  and the tuned values in `waterTuning.ts` lines 28 to 35.
- WFX-R13 perf-adversarial. Should sanity-check that recoloring to green did not break
  the foam line, the Fresnel sky blend, or the alpha read in the `/water` sandbox.

No convergence-file edits here. `SalishScene.tsx` and `globals.css` are untouched by
this research. Any later landing of these colors serializes via O0 against W3, W4,
W-CAM, W-LABELS, and LGC, per the charter lock.

---

## 6. Open questions for O0

1. Two water looks or one. The Salish Sea genuinely spans clear OM3 green-grey to
   turbid OM1 yellow-green plume. Do we ship one fixed palette, the OM3 deep-channel
   set, or expose a turbidity lever so the plume look is reachable in the sandbox. My
   default recommendation is one fixed OM3-grounded palette for the live scene.
2. Scale coupling. The recommended vector keeps the max coefficient near 3.0 to match
   the existing `uDepthColorScale` tuning. If R09 retires `uDepthColorScale` in favor
   of the per-channel vector, as `WATER2_TUNING_REQUEST.md` lines 40 to 42 allow, the
   absolute values need a re-tune in the `/water` sandbox against the full tileset, read
   through the `uDebug` thickness mode at lines 246 to 250 of `depthWater.ts`.
3. Colorimetric upgrade. If anyone wants the colors to be measured rather than modeled,
   that needs a CIE conversion from the published reflectance or Kd spectra under a
   chosen illuminant, a larger task than this research wave. Flagging it as a possible
   later spike, not a Wave 1 deliverable.
