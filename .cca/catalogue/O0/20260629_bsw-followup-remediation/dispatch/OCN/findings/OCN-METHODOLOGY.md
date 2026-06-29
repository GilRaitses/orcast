# OCN-METHODOLOGY (qualified method, locked by O0 at the OCN-Q gate)

> OCN sub-orchestrator. Repo verified against `61ba1d69ee36cf605f7ba741bdaa1defa8762834`.
> This doc records the method O0 locked at OCN-Q and what the OCN-B and OCN-INT
> waves then built. No commit at any point. OCN-ACCEPT is staged, awaiting the
> GPU-host gate.

## Locked decisions carried from O0

1. CC0 download approved at O0 level. One selected raw cast pulled to the box,
   only the baked JSON plus provenance ship in-repo. Provenance carries the DOI
   10.25921/jgrz-v584 and NCEI Accession 0307188.
2. Cast selection. The NCEI accession's northernmost station reaches latitude
   48.486, south of the Orcasound Lab node at 48.558, so the accession holds no
   on-site San Juan Channel or Haro Strait cast. The nearest cast is in the
   eastern Strait of Juan de Fuca and is labeled in provenance as a nearby
   analog, not an on-site station.
3. Depth-clip. The cheap scalar surface-Y top-clip is implemented now, fed by
   the `surfaceY` prop already wired in `SalishScene.tsx`. The per-fragment
   Water2 seabed depth-texture clip is deferred behind a perf gate and a future
   dive POV.
4. Honesty label. `INTERPRETIVE_OCEAN_LABEL` and `INTERPRETIVE_OCEAN_DETAIL` are
   unchanged so the load-time guard is not re-entered. Only the profile
   provenance changed to the CC0-attributed string. The honesty stamp `measured`
   stays the literal false. The measured fact lives only in `dataSources` from
   the provenance.
5. Pass metric. Layer-off pixel-equivalence, layer-on plausibility, and a
   frame-time A/B with layer-on within the 33.3 ms laptop budget and the 16.67 ms
   desktop number reported alongside. The layer is excluded from the Water2 depth
   pre-pass when on.

## Dataset, format, access, license

| Field | Value |
|-------|-------|
| Product | SalishCruiseDataPackage_v2025 |
| Accession | NCEI 0307188 |
| DOI | 10.25921/jgrz-v584 |
| License | CC0 1.0 Universal Public Domain Dedication, verified on the NCEI metadata page |
| Raw file | `SalishCruiseDataPackage_v2025_data_09072025.csv`, 3.2 MB, plain CSV |
| Columns used | `CTDPRS_DBAR`, `CTDTMP_DEG_C_ITS90`, `CTDSAL_PSS78`, `CTDTMP_FLAG_W`, `CTDSAL_FLAG_W`, `LATITUDE_DEC`, `LONGITUDE_DEC`, `STATION_NO`, `CRUISE_ID`, `EXPOCODE`, `DATE_UTC` |

The download succeeded from the public NCEI URL with no credentials. The raw CSV
is staged at `infra/ocean/data/` and gitignored. Full provenance is in
`infra/ocean/PROVENANCE.md`.

## Chosen cast and its analog labeling

| Field | Value |
|-------|-------|
| CRUISE_ID | BOLD085 |
| EXPOCODE | 31B520081108, intact |
| STATION_NO | 25 |
| Date | 2008-08-14, summer |
| Location | 48.40 N, 123.01 W, eastern Strait of Juan de Fuca, about 21 km south of the demo node |
| Depth | 1.1 to 164.3 dbar, full column |
| Measured T/S samples | 9 bottle-fire depths, flags 2 |
| Surface | 10.81 C, 30.47 PSU |
| Deep | 7.66 C, 33.20 PSU |

The cast is monotonic, fresher and warmer over saltier and colder, with a clear
pycnocline between 50 and 81 m. It is a real estuarine halocline, not a
salt-fingering staircase, consistent with BSW-R09. The accession EXPOCODE column
is Excel-corrupted for several cruises, for example `3.25E+11` collapses three
distinct cruises, so the bake selects by `CRUISE_ID` plus `STATION_NO`, which are
reliable, and records the intact EXPOCODE only when it survives. BOLD085 keeps
its intact EXPOCODE.

The accession records bottle-fire depths, a sparse irregular ladder. The shipped
profile linearly resamples the 9 real measured samples to 64 even depths so the
baked texture width matches the analytic path. The interpolation is a resample
of real measurements, not synthetic data. The continuous 0.5 dbar downcasts on
the NANOOS portal are a later refinement.

## Ingestion and bake method

`infra/ocean/bake_ctd_profile.py`, Python standard library only, selects the cast
by `CRUISE_ID` plus `STATION_NO`, keeps acceptable T and S quality flags, sorts
by pressure, linearly resamples to 64 depths, and writes
`web/lib/scene/ocean/measured_cruisesalish_profile.json` with `origin`,
`provenance`, `maxDepthM`, and `samples`. The script runs the forbidden-claim
substring check on the provenance before writing, so a bad string fails the bake
offline.

The web loader `web/lib/scene/ocean/measuredProfile.ts` imports the baked JSON
and returns a `StratificationProfile` typed exactly like
`analyticHaloclineProfile`. It performs no bake of its own. The factory
`createDoubleDiffusionLayer` calls the shared `stratificationToTexture` so the
per-profile normalization stays identical to the analytic path, and it runs
`assertNoForbiddenClaim` on the provenance the same way it does for the analytic
profile.

## Read-only depth-clip seam shape

The scalar surface-Y top-clip lives in `doubleDiffusion.ts`. The fragment shader
reconstructs each fragment's world Y from `uSurfaceY`, `uColumnHeight`, and the
existing depth fraction, discards any fragment above the surface, and fades the
plume to zero across `uSurfaceFade` just below the waterline so the additive
field dies at the surface. `uSurfaceY` is fed from the layer's `surfaceY` option,
which `OceanProcessRig` already passes as `SEA_LEVEL_Y`. The clip consumes the
surface position read-only and writes nothing back to the water. The migration to
`WfxEnvHandle.underwater.waterLevelY`, once the ENV lane publishes the single
live handle, is a one-line change to where `surfaceY` is sourced.

The per-fragment seabed clip would read `Water2Handle.depthTarget.texture`
read-only, which is already exposed, but it couples to water2 internals and adds
cost, so it is deferred per O0 behind a perf gate and a dive POV.

## Exact honesty label and provenance

The on-screen label and detail are unchanged. The profile provenance, shipped in
the baked JSON and surfaced through `dataSources`, is:

```text
Measured CTD cast of depth, temperature, and salinity. NANOOS CruiseSalish, NCEI Accession 0307188, CC0 1.0, DOI 10.25921/jgrz-v584. Cruise BOLD085 station 25, 2008-08-14, eastern Strait of Juan de Fuca near 48.40 N 123.01 W. This is a nearby analog cast, not an on-site San Juan Channel / Orcasound Lab node station. Halocline depth and density gradient are derived from the cast. The mixing motion is a stylized interpretation, not measured microstructure and not how an animal senses its surroundings.
```

This carries none of the five forbidden substrings, keeps the two words of every
forbidden phrase apart, names the measured variables, attributes CC0 and the
accession, labels the cast a nearby analog, and keeps the motion interpretive. It
is verified by the CI test and by the offline bake guard.

## Pre-pass exclusion

The WFX Water2 depth pre-pass renders the whole scene into an offscreen target
with the water hidden. The layer suppresses its color writes while the renderer
draws into any offscreen target and restores them for the on-screen pass, through
`onBeforeRender` and `onAfterRender` on its own meshes. depthWrite is already
false, so with colorWrite off the layer contributes nothing to the pre-pass. This
reads the render state only and mutates no WFX water, `scene.environment`,
`scene.fog`, or `scene.background`. When the layer is disabled the rig is not
mounted, so these callbacks never fire.

## CI test and a faithful deviation to flag

`web/lib/scene/ocean/measuredProfile.test.mts` reproduces the exact mount-time
guard call `assertNoForbiddenClaim(INTERPRETIVE_OCEAN_LABEL, INTERPRETIVE_OCEAN_DETAIL, profile.provenance)`
against the shipped baked profile, asserts the guard is live on a known-bad
string, and checks the profile shape.

Deviation from the literal O0 wording, flagged honestly. O0 asked the CI test to
construct the layer. The node test runner cannot import `doubleDiffusion.ts`
because that file uses extensionless relative imports that the web bundler
resolves but node does not, verified empirically. The test therefore runs the
exact guard call the factory runs, against the real shipped artifact, which is
the crash vector O0 named. The full construct path is still compiled by
`tsc --noEmit` and by the web build, and OCN-ACCEPT exercises the real layer on
the GPU host.

## Files produced

| File | Role | In git |
|------|------|--------|
| `infra/ocean/bake_ctd_profile.py` | offline bake, stdlib only, guard check | yes |
| `infra/ocean/PROVENANCE.md` | provenance, license, cast selection, reproduce | yes |
| `infra/ocean/data/SalishCruiseDataPackage_v2025_data_09072025.csv` | raw CC0 cast | no, box |
| `web/lib/scene/ocean/measured_cruisesalish_profile.json` | baked 64-sample profile | yes, small |
| `web/lib/scene/ocean/measuredProfile.ts` | dependency-free loader | yes |
| `web/lib/scene/ocean/doubleDiffusion.ts` | surface-Y top-clip + pre-pass exclusion | yes, edit |
| `web/lib/scene/ocean/index.ts` | barrel re-export of the loader | yes, edit |
| `web/lib/scene/ocean/measuredProfile.test.mts` | CI guard test | yes |
| `web/app/components/scene/SalishScene.tsx` | OceanProcessRig consumes the measured profile | yes, edit |

## Validation results

- `tsc --noEmit` on the web workspace is clean.
- ESLint on every edited file reports no errors.
- `node --test lib/scene/ocean/**/*.test.mts` passes all four tests.
- `interpretiveOceanLayer.ts` is intentionally unchanged, so the load-time label
  guard is not re-entered.

## Gated items returned to O0

- The convergence edit on `SalishScene.tsx` was taken in the single-editor OCN-INT
  slot. HEAD is in sync with origin/main and no concurrent edit to that file
  exists, verified by fetch.
- OCN-ACCEPT, the GPU render-host capture, is a human gate for cost and host
  time. It is staged and paused.
- The ENV-handle migration for the surface-Y source is an ordering dependency on
  the ENV lane, not a blocker now.
