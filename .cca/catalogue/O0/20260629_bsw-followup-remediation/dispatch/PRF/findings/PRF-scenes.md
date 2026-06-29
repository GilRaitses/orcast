# PRF-R3 findings: scenes to measure for the client-tier frame-time verify

Read-only research (PRF-R wave, BSWR-PRF "client-tier-frametime-verify" lane).
Every param and toggle claim below cites file:line. No host run, no edits, no
commit. Where a toggle does not exist in code I say so rather than invent one.

## 1. Homepage twin route + component

The homepage Salish Sea twin is the default route `/`.

- `web/app/page.tsx:9` `HomePage` renders `<AdaptiveExplore signedIn={signedIn} />` (`web/app/page.tsx:20`).
- `AdaptiveExplore` mounts the scene through `SceneHost` at `web/app/components/AdaptiveExplore.tsx:301` (`<SceneHost onIntent=... focus=... />`).
- `SceneHost` lazy-loads the r3f twin: `const SalishScene = dynamic(() => import("./SalishScene"), { ssr: false, ... })` at `web/app/components/scene/SceneHost.tsx:11`, and renders `<SalishScene onIntent={onIntent} focus={focus} />` at `web/app/components/scene/SceneHost.tsx:75`.
- The scene component under test is `web/app/components/scene/SalishScene.tsx` (default export `SalishScene` at `web/app/components/scene/SalishScene.tsx:1738`). The composed in-Canvas graph is `TwinScene` (`web/app/components/scene/SalishScene.tsx:1505`), mounted inside the r3f `<Canvas>` at `web/app/components/scene/SalishScene.tsx:1891`.

So the route to measure is `/` and the component is
`web/app/components/scene/SalishScene.tsx`. There is no separate homepage page
for the twin; `/explore` is a different route and the `(sandbox)` scenes
(`/spectro`, `/reenactment`, `/slice`, `/water`, `/station`) and `/workbench`
are reference surfaces, NOT the homepage target.

## 2. BSW features and their real toggles

The BSW (B-side acoustic/behavior) slice is the in-scene mount block
`SliceRig` (`web/app/components/scene/SalishScene.tsx:1114`), rendered ONLY when
a station is selected: `{selectedStation && (<SliceRig ... />)}` at
`web/app/components/scene/SalishScene.tsx:1645`. With no station selected the
whole slice (rig, spectro HUD, reenactment pool) never mounts, so it costs zero
on first paint (SEAM 6, header at `web/app/components/scene/SalishScene.tsx:1005`).

All query params are read in one `useEffect` in `SalishScene`
(`web/app/components/scene/SalishScene.tsx:1788`) via
`new URLSearchParams(window.location.search)` at
`web/app/components/scene/SalishScene.tsx:1790`. The viewport params are read
separately by `AdaptiveExplore` (`web/app/components/AdaptiveExplore.tsx:94`)
through `parseViewport` (`web/lib/viewport.ts:7`).

| BSW feature | Real toggle | What it enables | file:line |
| --- | --- | --- | --- |
| Slice mount (BST rig + everything downstream) | `?station=<lat>,<lng>[,<name>]` query param, or a beacon click | Sets `selectedStation`, which mounts `SliceRig` (modeled equipment rig anchored on the seabed) | param read `SalishScene.tsx:1791`, parse `1793-1796`, `setSelectedStation` `1797-1803`, conditional mount `1645` |
| Spectrogram HUD (BSH) | implied by the selected station having an archived clip; no independent param | `createSpectroTimeline` bakes a WebAudio STFT and mounts the HUD into the DOM host | gate `SalishScene.tsx:1220` (`if (!hasClip \|\| !clipUrl) ... return`), bake `1253-1271`; clip binding only for Orcasound Lab `web/lib/scene/hydrophone/catalog.ts:128-138,169` |
| Reenactment orca pool (BRE) | mounts with the slice once the spectro authority exists; presence-gated | `createOrcaPool` + `createTimelineDriver`, presence-gated visibility | gate `SalishScene.tsx:1308` (`if (!authority) return`), pool build `1342-1360` |
| Multi-orca capability demo | `?bsw_demo=N` (N clamped 1..3) | Overrides the presence-only 0/1 count and spawns up to 3 orcas across the DTAG ethogram | param read `SalishScene.tsx:1814`, clamp/set `1815-1818`, applied as `demoCount` `buildSpawnRecord` branch `1324-1335` |
| Interpretive ocean layer (double-diffusion) | `?ocean=1` | Sets `oceanOn`, mounts `OceanProcessRig` (additive transparent layer, depthWrite false) and the mandatory chip | param read `SalishScene.tsx:1809`, `setOceanOn(true)` `1809`, conditional mount `1666`, rig `1480-1500`, also flips via the in-scene toggle button `1951-1958` |
| Top-down POV | `?view=topdown` | Sets `pov` to top-down so the station camera flies to a 180 m overview with a slow orbit instead of the seabed dive-in | param read `SalishScene.tsx:1806`, `setPov("topdown")` `1806`, POV controller `1392-1399`, camera moves `web/lib/scene/hydrophone/stationCamera.ts:55-87` |
| Station selection (which node) | the `<lat>,<lng>,<name>` payload of `?station=` | Picks the catalog entry; only Orcasound Lab carries the archived clip, so only it bakes the spectro HUD + reenactment | resolve `SalishScene.tsx:1090-1112`, clip-bearing entry `catalog.ts:155-170`; other two nodes are live-listen only `catalog.ts:171-200` |
| Camera viewport focus | `?lat=&lng=&zoom=` | Sets `focus`, which supersedes the resting orbit with a `runPlaceJourney` fly-to | `parseViewport` `web/lib/viewport.ts:10-18`, consumed `AdaptiveExplore.tsx:94-96`, journey trigger `SalishScene.tsx:679-685` |

Params that DO NOT exist (not invented here): there is no param to turn the
always-on single orca off, no param to disable the base water/sky/bathy/terrain,
and no param to mount the slice WITHOUT also driving the station camera POV. The
`SHOW_PERF_HUD` flag is hardcoded `false` (`SalishScene.tsx:236`), so there is
no in-scene FPS overlay; frame-time must be sampled out of band.

The proof PNG filenames under `.cca/catalogue/O0/20260628_render-host/proof/`
confirm these are the real captured URLs, for example
`?station=48.5583362,-123.1735774,Orcasound%20Lab&bsw_demo=3&view=topdown`,
`...&ocean=1`, `...&view=topdown`, the bare `?station=...` slice, the two
live-listen-only nodes, and bare-homepage captures (`_*.png`).

## 3. Concrete BSW-on vs BSW-off A/B

Honest constraint first: a clean toggle of the FULL BSW feature set against a
held-constant camera does NOT exist. Selecting a station both mounts the slice
AND hands the camera to the station POV controller, which cancels the resting
orbit (`SalishScene.tsx:1385-1404`, `stationCamera.ts:53-87`). So the two
options below trade off which variable is held constant. I recommend running
both and reporting both.

### A/B pair 1 (isolates the TOTAL BSW cost; camera differs, flagged)

- BSW-off baseline: `http://localhost:3000/`
  - No query params. `selectedStation` is null, so `SliceRig` never mounts
    (`SalishScene.tsx:1645`). Camera is the resting slow orbit
    (`SalishScene.tsx:662-673`). Base twin only: tiles, Water2, sky, fog,
    terrain tint, bathy tint, and the single always-on `OrcaRig`
    (`SalishScene.tsx:1633`).
- BSW-on: `http://localhost:3000/?station=48.5583362,-123.1735774,Orcasound%20Lab&bsw_demo=3&ocean=1`
  - Mounts the slice on Orcasound Lab (the only clip-bearing node, so the
    spectro HUD + reenactment actually bake), spawns 3 orcas, and turns the
    interpretive ocean layer on. Camera is the seabed dive-in POV.
- Held constant: same route, same build, same device, same tileset, same base
  twin rigs, same Orcasound Lab station coordinates as the only realistic
  full-feature target.
- Confound to report: camera path differs (resting orbit vs station dive-in),
  and detail LoD lifts when the slice journey fires (`SalishScene.tsx:1614-1618`),
  so this pair measures BSW feature cost AND the camera/LoD change together.

### A/B pair 2 (holds station + camera constant; isolates the incremental ocean + multi-orca cost)

- BSW lighter: `http://localhost:3000/?station=48.5583362,-123.1735774,Orcasound%20Lab&view=topdown`
  - Slice mounted, spectro HUD baked, presence-only count, ocean off, top-down
    orbit camera.
- BSW heavier: `http://localhost:3000/?station=48.5583362,-123.1735774,Orcasound%20Lab&view=topdown&ocean=1&bsw_demo=3`
  - Same station, same top-down orbit camera, plus the ocean layer and 3 orcas.
- Held constant: station, POV (`view=topdown` in both, so the same fly-to + slow
  orbit), spectro HUD, base twin. The ONLY differences are `ocean=1` and
  `bsw_demo=3`.
- This pair cannot isolate the base slice + spectro HUD cost (both sides carry
  them); it isolates the ocean layer and the multi-orca pool only.

Use Orcasound Lab coordinates `48.5583362,-123.1735774` in every BSW-on URL:
the other two in-extent nodes (North San Juan Channel, Andrews Bay) are
live-listen only and bake NO spectrogram and NO reenactment pool
(`catalog.ts:171-200`), so they would understate BSW cost.

## 4. Scene settle / animation timing

The scene never reaches a static steady state. It animates continuously, so the
rAF sample window must start AFTER the establishing motion settles, then run for
a fixed duration while motion is steady.

- BSW-off resting orbit is a continuous orbit at `RESTING_ORBIT_SPEED = 0.05`
  rad/s (`SalishScene.tsx:205`, started `662-673`). It starts only once the
  tileset reports its fit (`fitRadius != null`, `SalishScene.tsx:648,662`), so
  do not sample before the first `onFit`.
- Tiles stream progressively. The resting frame starts at the coarse LoD caps
  `RESTING_ERROR_TARGET = 32` / `RESTING_MAX_DEPTH = 2` (`SalishScene.tsx:215-216`)
  and only lifts to full detail (`DETAIL_*`, `217-218`) when the user grabs the
  controls (`handleUserGrab`, `1604-1612`) or a focus journey fires
  (`1616-1618`). A headless capture that never grabs stays on the coarse caps,
  so settle should wait for tile streaming to quiesce (the `load-model` tick,
  `useModelLoadTick` `299-308`) before sampling.
- BSW-on station POV is a `flyTo` with `durationMs` default 2500 ms
  (`stationCamera.ts:62,76`), and top-down optionally chains into a slow orbit
  after the fly-in resolves (`stationCamera.ts:78-86`). The director tweens use
  `DEFAULT_FLY_MS = 2500` and `DEFAULT_DESCEND_MS = 3000`
  (`web/lib/scene/camera/director.ts:41-42`). So allow at least ~3 s of settle
  after the station mount before starting the sample.
- BSW-on slice work is async and lands after first paint: the spectro STFT bake
  (`createSpectroTimeline`, `SalishScene.tsx:1253`) and the reenactment pool load
  (`loadClassification` / `loadClipManifest` / `pool.setSpawn`, `1312-1349`)
  both resolve later, and the per-frame driver only runs once they exist
  (`1416-1418`). Sampling too early would miss the full BSW per-frame cost. Wait
  until the chip state reports `status: "ready"` (`1431`) before sampling.
- Per-frame steps are time-capped (`Math.min(dt, 1/30)` in OrcaRig `969`, the
  reenactment driver `1420`, and the orca controller), so a slow frame does not
  fast-forward animation, which keeps the sample honest under load.

Recommended settle: wait for first `onFit`, then wait for tile `load-model`
ticks to stop arriving, and for BSW-on additionally wait for the camera fly-to
(~3 s) and the slice `status: "ready"` chip, then sample rAF deltas over a fixed
window (for example 10 s) for both arms.

## 5. Gaps (features with no clean off-toggle)

- No slice-off toggle while a station is selected. The slice mounts whenever
  `selectedStation` is set; there is no param to keep a station selected but the
  slice unmounted (`SalishScene.tsx:1645`). So "BSW fully off" can only mean "no
  station", which also means the resting-orbit camera, not the station POV.
- Camera cannot be held identical across the full-feature A/B. Station selection
  forces the station POV and cancels the resting orbit
  (`SalishScene.tsx:1385-1404`). A true underwater/identical-camera comparison is
  explicitly noted as unbuilt in the slice block header
  (`SalishScene.tsx:1018-1021`: the no-dunk altitude clamp keeps the eye above
  the water, and a true submerged POV needs a WS-INTENT opt-out).
- Spectro HUD has no independent param. It is implied by the station having an
  archived clip, and only Orcasound Lab has one (`catalog.ts:128-138,169`). You
  cannot toggle the HUD on a clip-less station, and you cannot turn it off on
  Orcasound Lab while keeping the rest of the slice.
- The single always-on orca (`OrcaRig`, `SalishScene.tsx:1633`) is part of the
  base twin, not the BSW slice, and has no off-toggle. It is present in BOTH
  arms, so it is not isolated by either A/B.
- Detail LoD lift is coupled to engagement. A BSW-on focus/grab lifts the LoD
  caps (`SalishScene.tsx:1604-1618`), so an honest A/B must control for whether
  each arm is on coarse or full LoD.

## 6. TL;DR

- Route to measure: `/` (homepage), component
  `web/app/components/scene/SalishScene.tsx` (`page.tsx:20` then
  `AdaptiveExplore.tsx:301` then `SceneHost.tsx:75`).
- Real BSW toggles, all query params read at `SalishScene.tsx:1788-1819`:
  `?station=<lat>,<lng>,<name>` (mounts the slice), `?bsw_demo=N` 1..3
  (multi-orca), `?ocean=1` (interpretive ocean layer), `?view=topdown` (POV);
  the spectro HUD + reenactment are implied by selecting the clip-bearing
  Orcasound Lab station. Viewport `?lat=&lng=&zoom=` sets the camera focus
  (`viewport.ts:7`).
- Recommended A/B. Total cost: `/` vs
  `/?station=48.5583362,-123.1735774,Orcasound%20Lab&bsw_demo=3&ocean=1`
  (camera differs, flagged). Incremental cost with camera held:
  `/?station=48.5583362,-123.1735774,Orcasound%20Lab&view=topdown` vs the same
  plus `&ocean=1&bsw_demo=3`.
- Gaps: no slice-off toggle while a station is selected, camera cannot be held
  identical against full BSW-off, the spectro HUD has no independent param and
  only Orcasound Lab bakes it, and the single always-on orca is in both arms.
