# BSW-R09 - Ocean-process (double-diffusion) layer

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent 98500247; written by the BSW sub-orchestrator.

## Summary

- **Greenfield module.** `web/lib/scene/ocean/` does not exist yet. BSH owns it. The live twin already has one expensive opaque depth pre-pass in `Water2Rig`. The ocean-process layer must reuse that pass or be costed explicitly. A third full-scene render is ruled out by mount order.
- **Licensed stratification data is available.** Best demo-slice sources: **NANOOS CruiseSalish / NCEI Accession 0307188** (CC0, measured CTD T/S/density profiles) and **SalishSeaCast ERDDAP 3D physics fields** (Apache 2.0, modeled T/S). **LiveOcean** is experimental with no clear redistribution license; escalate to O0.
- **Honest oceanography.** Salish Sea stratification (halocline, thermocline, estuarine circulation, tidal mixing) is real and well documented. **Salt-fingering thermohaline staircases are not the dominant process** in the open Salish basin; they appear in narrow BC fjords under specific intrusion conditions (e.g. Belize Inlet). The bidirectional "lava lamp" is a **stylized interpretive metaphor**, grounded in real T/S structure but not a direct map of measured double-diffusive microstructure.
- **No WFX regression path.** Implement as a separate additive transparent mesh/shader reading the existing `DepthTexture` and WFX color constants. Do not mutate `depthWater.ts` uniforms, `makeRealWfxEnv`, or `scene.fog`.
- **Interpretive honesty is locked.** PROGRAM.md and BSW-SPECTRO-HUD_CHARTER.md require on-screen `interpretive` labeling. "Orca biosonar perceives it" is speculative and must never read as measured cognition.
- **Perf (estimated).** Baseline twin already pays ~2U per frame. Recommended layer adds 0 full scene renders, ~0.3-0.8 ms at 1080p when gated on and camera submerged. Raymarch/froxel volumes are out of budget.

## In-repo findings (cited)

### WFX environment handle (`realWfxEnv.ts`)

```17:19:web/lib/scene/wfx/realWfxEnv.ts
// HONESTY. The sky is a modeled atmosphere, the absorption is a rendering optic,
// not measured water clarity. The shared handle keeps the modeled animal lit by
// the same modeled atmosphere as the modeled water.
```

Supplies `pmremEnvironment` + `underwater.{absorption, inScatterColor, waterLevelY, visibility}` (`PROPOSED_RGB_EXTINCTION`). The ocean-process layer must consume these optics for color harmony, not redefine them.

### Atmosphere transition (`transition.ts`)
Pure tween factories over caller-owned `THREE.Fog`/`FogExp2` + lights. The layer should not drive `scene.fog` directly (WFX E5 already couples fog to water via `Water2Rig.setFog`).

### SalishScene mount order + depth pre-pass

```369:380:web/app/components/scene/SalishScene.tsx
  useFrame((state) => {
    const handle = handleRef.current;
    if (!handle) return;
    handle.renderDepthPrepass(gl, scene, camera as THREE.PerspectiveCamera);
    handle.update(state.clock.elapsedTime, camera);
    const f = scene.fog;
    if (f instanceof THREE.FogExp2) handle.setFog({ color: f.color, density: f.density });
    else handle.setFog(null);
  });
```

```762:763:web/app/components/scene/SalishScene.tsx
// No second per-frame depth pass is added: the Water2Rig
// pre-pass stays the only one.
```

`FogTuneRig` swaps linear fog for `FogExp2` density 0.012, read by water shader. OrcaRig mounts after Water2Rig to join the opaque pre-pass without a third render.

### Existing shader passes (`water2/depthWater.ts`)
Single merged WFX water shader. Depth pre-pass RT hides water mesh, renders opaque scene to color+depth RT; column thickness from `uDepthTexture`; per-channel absorption (green-survives {3,1,3}); horizon fog; dive underside stub. **No volumetric ocean-process module exists** (`web/lib/scene/ocean/` returns 0 files).

### Honesty label precedent
`attachModeledLabel` stamps `userData.bathyHonestyLabel`/`modeledNotMeasured`. BSH should add a parallel `attachInterpretiveLabel` following the same `userData` pattern (`web/lib/scene/bathy/honesty/attach.ts`).

### Perf baseline
`WaterSandboxScene.tsx`: depth pre-pass = second full opaque render -> baseline ~2U. No measured SalishScene numbers; treat 2U ~16.6 ms at 60 fps desktop as the ceiling new passes must respect.

## Real Salish Sea stratification data sources (with licenses) + honest note on salt-fingering

### Recommended sources (license-first, demo viable)

| Source | What it provides | Access | License | Demo use |
|---|---|---|---|---|
| **NANOOS CruiseSalish** | 1,238+ CTD profiles, T/S/O2, sigma-theta, 0.5 dbar bins | https://nvs.nanoos.org/CruiseSalish | **CC0 1.0** | Primary measured anchor (one profile near demo station) |
| **NCEI Accession 0307188** | Same cruises, CSV + metadata | https://doi.org/10.25921/jgrz-v584 | **CC0 1.0** | Offline bake of 1D T/S texture |
| **SalishSeaCast ERDDAP 3D physics** | Hourly 3D T, S, density on NEMO grid | https://salishsea.eos.ubc.ca/erddap/info/ubcSSg3DPhysicsFields1hV21-11/index.html | **Apache 2.0** | Volumetric envelope; label modeled |
| **ONC SoG CTD (SalishSeaCast obs)** | 15-min mean T/S at Central Node | https://salishsea.eos.ubc.ca/erddap/info/ubcONCSCVIPCTD15mV1/index.html | **Apache 2.0** | Time series at fixed location |
| **ONC Oceans 3.0 (raw CTD)** | High-res instrument data | https://www.oceannetworks.ca/data/ | **CC-BY 4.0** (ONC-owned; partner sets may differ) | Verify per-dataset metadata before ship |

### Escalate before ship
- **LiveOcean (UW)**: "experimental product, research use only"; **no explicit open license**. O0 must confirm before redistribution.
- **ONC partner-restricted sets**: may be CC-BY-NC; **NC -> STOP**.

### What the data actually show
Real and strong: estuarine halocline, seasonal thermocline, tidal mixing, water-mass intrusions at sills. Double-diffusive convection is a real process where one component is unstably stratified. **Salt fingering specifically** requires warm/salty over cold/fresh with net stable density - dominates tropical/subtropical thermoclines, **not** the Salish estuary (often fresher-over-saltier, favoring diffusive convection at some interfaces). Documented BC salt-fingering staircases exist in Belize Inlet (narrow fjord), not the open Strait of Georgia. **Verdict:** ground the layer in real CruiseSalish T/S profiles + halocline depth (measured, cited); render stylized finger/plume motion as interpretive; do not claim the Salish routinely exhibits classic thermohaline staircases or that an orca "sees" this.

## Stylized volumetric render approach (no WFX regression; compute-neutral)

1. `web/lib/scene/ocean/makeOceanProcessLayer.ts` factory returning `{ mesh, update, setEnabled, dispose }`.
2. Separate render object: large box/view-aligned mesh, `depthWrite:false`, `depthTest:true`, `transparent:true`, additive/low-alpha blending, `renderOrder:2` (after water at 1).
3. Shared depth pre-pass (compute-neutral): read-only access to `Water2Handle.depthTarget` + `depthTexture`; fragment shader samples same reconstruction math as `depthWater.ts`.
4. Procedural "lava lamp" field: 2-3 octave 3D noise advected on opposed vertical velocities (warm/salty amber-rose downward; cold/fresh blue-green upward); modulate by a baked 1D T/S gradient texture from one CC0 CruiseSalish profile (not live fetch).
5. WFX color lock: plume tints lerped toward `WATER_TUNED_SHALLOW`/`WATER_TUNED_DEEP`, attenuated with same `exp(-absorption*depth)` so it sits inside the green-survives optic.
6. Gating: default off; enabled in hydrophone POV or explicit toggle; zero draw cost when off.
7. Camera gate: only render when camera Y < `SEA_LEVEL_Y` (director currently clamps above water; BRE/BST dive POV must relax clamp first, or layer stays dormant).

**WFX regression risks to avoid:** editing `depthWater.ts` shader; mutating `scene.fog`; standing up `EffectComposer` for this layer alone; true raymarch/froxel volume; a third `render(scene, camera)`.

**Perf estimates (labeled estimated):** reuse existing pre-pass 0 ms added; additive box shader submerged ~40% screen 0.3-0.8 ms; CPU uniform/noise updates <0.05 ms; optional `THREE.Points` sparkle <0.5 ms (preset-gated). Total when enabled ~0.35-0.85 ms; when disabled 0 ms.

**Optional costed dependency (not default):** `@react-three/postprocessing` ShaderPass ~0.1 ms only if a composer already exists; do not introduce solely for this layer.

## Interpretive honesty framing (exact on-screen label wording proposal)

Primary HUD chip (always visible when on): `Interpretive · stratified ocean mixing`

Secondary line: `Salish Sea temperature and salinity structure comes from cited oceanographic profiles and models. The moving layers are a stylized view of water-mass mixing. This is not measured orca biosonar perception.`

Object graph stamp:
```typescript
userData.oceanProcessHonestyLabel = {
  kind: "interpretive", measured: false, modeledNotMeasured: false,
  label: "interpretive · stratified ocean mixing",
  dataSources: ["NANOOS CruiseSalish CTD (CC0)", "optional SalishSeaCast model (Apache 2.0)"],
  speculativeClaim: "orca biosonar perception - not measured",
};
```

Forbidden copy: "Orca biosonar reveals..."; "What the whale sees underwater"; "Measured thermohaline structure"; "Salt fingering observed here" (unless tied to a specific cited cast and labeled interpretive).

## Recommendations with cost + standin-free fallback

| Rec | Detail | Cost | Fallback |
|---|---|---|---|
| R1 Primary data | Bake one CC0 CruiseSalish CTD profile near demo station into 256x1 RGBA texture; ship attribution in HUD | ~0.5 eng-day | Analytic halocline curve (two-layer linear T/S), same label |
| R2 Render | Additive `OceanProcessRig` in BSH mount; read shared `depthTarget`; gate off default | ~1.5-2.5 eng-days | Layer disabled; spectrogram HUD ships without 3D layer |
| R3 WFX coordination (O0) | Narrow export on `Water2Handle` for depth texture; no material edits | O0 gate ~0.5 day | Duplicate depth sample via callback from Water2Rig ref |
| R4 Label | `attachInterpretiveLabel` + drei `Html` chip | ~0.5 eng-day | Static corner badge via CSS |
| R5 Do not use LiveOcean until license cleared | Experimental, unclear redistribution | 0 if skipped | SalishSeaCast Apache 2.0 grid |
| R6 Acceptance | Visual A/B: water frame identical with layer off; layer on shows label + plumes without changing water alpha/Fresnel | GPU-host gate | n/a |

**Standin-free fallback is R2 disabled + R1 analytic profile.** No fabricated "measured perception", no canned loop labeled as data.

## Open questions / overclaim-risk flags for O0

1. WFX depthTarget export: may BSH read `Water2Handle.depthTarget.texture`, or must water2 expose a formal read-only seam?
2. Underwater camera: `director.ts` has no dive mode yet. Ship dormant or after POV-underwater lands?
3. LiveOcean license: confirm CC-BY/Apache or exclude.
4. Salt fingering wording: operator intent "salt going down, cold mineral-rich coming up" vs real estuarine direction (surface fresher, deep saltier; diffusive convection). O0 approves metaphor vs physically accurate direction.
5. Model vs measured stacking: if SalishSeaCast modeled grid drives visuals, measured CTD must remain the cited "grounded in data" source.
6. Convergence collision: `SalishScene.tsx` shared with WFX/ORCA/LGC/CVP; serialize slot after Water2Rig.
7. Perf gate: BSH-ACCEPT runs GPU-host A/B with layer on/off; target <1 ms incremental.
8. NC partner ONC datasets: verify license metadata; NC -> STOP.

## Sources

### In-repo (commit 240570e)
`web/lib/scene/wfx/realWfxEnv.ts`, `web/lib/scene/atmosphere/transition.ts`, `web/app/components/scene/SalishScene.tsx`, `web/lib/scene/water2/depthWater.ts`, `web/lib/scene/bathy/style/waterTuning.ts`, `web/lib/scene/bathy/honesty/{attach.ts,labels.ts}`, `web/app/(sandbox)/water/WaterSandboxScene.tsx`, `PROGRAM.md`, `BSW-SPECTRO-HUD_CHARTER.md`, `.cca/catalogue/O0/20260628_water-fx/research/{WFX-R08_underwater_volumetrics.md,WFX-R11_salish_optics.md}`, `research/R4_ocean_water_rendering.md`

### External (URLs + licenses)

| URL | License / terms |
|---|---|
| https://nvs.nanoos.org/CruiseSalish | CC0 1.0 (via NCEI 0307188) |
| https://doi.org/10.25921/jgrz-v584 | CC0 1.0 |
| https://www.ncei.noaa.gov/data/oceans/ncei/ocads/metadata/0307188.html | CC0 1.0 |
| https://salishsea.eos.ubc.ca/erddap/info/ubcSSg3DPhysicsFields1hV21-11/index.html | Apache 2.0 |
| https://salishsea.eos.ubc.ca/erddap/info/ubcONCSCVIPCTD15mV1/index.html | Apache 2.0 |
| https://www.oceannetworks.ca/data/data-policy/ | CC-BY 4.0 (ONC-owned; partner sets may differ) |
| https://faculty.washington.edu/pmacc/LO/LiveOcean.html | Experimental, research only; **no clear open license** |
| https://doi.org/10.1139/facets-2017-0074 | CC-BY 4.0 (SoG underwater optics, Loos et al. 2017) |
| https://doi.org/10.1175/2011jpo4540.1 | AMS journal (Salish estuarine circulation model) |
| https://doi.org/10.1080/07055900.2011.649034 | Taylor & Francis (BC fjord salt fingering; Belize Inlet, not open Salish) |
| Schmitt 1994, Annu. Rev. Fluid Mech. 26, 231-264 | Review of double diffusion |
