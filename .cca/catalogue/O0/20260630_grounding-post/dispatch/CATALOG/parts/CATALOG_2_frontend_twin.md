# Catalog shard 2 of 4, frontend, console, 3D twin, water

Area: frontend and console, plus the 3D twin and water effects. Code home is
`web/app/`, `web/app/components/scene/`, `web/lib/`, and `web/lib/scene/`. Live
surface is the anonymous explore console on `https://orcast-h0.vercel.app`.

## Frontend, console, 3D twin, water

### Founding handoff and the 3D-twin template

| id / family | charter | intent | resulting code | status | gate | outcome |
|---|---|---|---|---|---|---|
| explore3d-handoff (Wave Set EX, no registry family) | `.cca/catalogue/O0/20260626_explore3d-handoff/HANDOFF_CHARTER.md` | Make Explore the landing surface as a react-three-fiber Salish Sea twin driven by an adaptive orchestrator console, anonymous-first, gate only write actions. | The whole `web/` Next.js app first committed for Git deploy at `8e5c6ee`; executed downstream by the console-journey program and the twin program. | shipped (as a handoff that the later lanes executed) | none in this dir | Live 3D explore console on orcast-h0.vercel.app. |
| 3d-twin (reusable template) | `.cca/catalogue/O0/20260627_3d-twin/README.md`, `WAVESET_CHARTER_TEMPLATE.md` | Reusable charter template for a geospatial 3D digital twin plus a downstream spatial-science consumer, generalized from the pax NYC viewer. | No product code. Template only. Instantiated by `20260627_terrain-bathymetry-twin/`. | shipped (template, not product code) | operator gates defined in template | Spawned the live terrain plus bathymetry twin. |

### Console journey program and its wavesets

| id / family | charter | intent | resulting code | status | gate | outcome |
|---|---|---|---|---|---|---|
| console-journey-trips (program umbrella) | `.cca/catalogue/O0/20260627_console-journey-trips/README.md` | Continuous intent loop on the live 3D console where camera motion plus the chat slot transduce intent into served forecasts and a trips planner grounded in open transit data. | `web/lib/scene/camera/director.ts`, scene modules, trips surfacing. Commits `5415b8c` (live map_viewport camera plus scenic and bathy scene plus trips planner), `643eef7` (surface trips on the anonymous home). | shipped | program visual gate, acceptance_screenshots | Camera-driven console plus trips live on the home route. |
| console-ws-intent (WS-INTENT) | `.cca/catalogue/O0/20260627_console-ws-intent/README.md` | Make the dead `map_viewport` ui_intent and search drive the live console camera, factor the fly-through into a reusable controller. | `web/lib/intent/transducer.ts`, `web/lib/journey/controller.ts`, `web/lib/adaptiveConsole.ts`, viewport bridge in `web/app/components/scene/SalishScene.tsx`. Commit `5415b8c`. | shipped (README marks COMPLETE) | folded into program visual gate, PASS | Search and planner turns move the live camera. |
| console-ws-scenic (WS-SCENIC) | `.cca/catalogue/O0/20260627_console-ws-scenic/README.md` | Make the world read right above sea level, land materials plus horizon and atmosphere decor. | `web/lib/scene/terrain/terrainStylist.ts`, `web/lib/scene/decor/` (sky, fog, horizon ring), `web/lib/scene/atmosphere/transition.ts`. Commit `5415b8c`. | shipped (README marks research and discovery complete; code landed in the program batch) | program visual gate | Terrain styling plus horizon and sky decor live. |
| console-ws-bathy (WS-BATHY) | `.cca/catalogue/O0/20260627_console-ws-bathy/README.md` | Make the seafloor and depth-driven water read truthfully, measured vs modeled labeled. | `web/lib/scene/water2/depthWater.ts`, `web/lib/scene/bathy/` (style, honesty). Commits `5415b8c`, `fa9da22` (owner-ratified green-survives water tint retarget). | shipped | program visual gate | Depth-driven water over the CUDEM topobathy seabed. |
| console-ws-trips (WS-TRIPS) | `.cca/catalogue/O0/20260627_console-ws-trips/README.md` | Real multi-step trips planner on the live console, connections honesty-labeled measured, modeled, or published. | Frontend panel registry in `web/app/components/ActiveSurfaceHost.tsx`; surfaced via `643eef7`. Backend `planner.py` is the backend shard. | shipped (frontend part); README marks only research and discovery ran in this dir | program gate | Trips journey surfaced on the anonymous home. |
| console-ws-perf (WS-PERF) | `.cca/catalogue/O0/20260628_console-ws-perf/README.md`, `WAVESET_CHARTER.md` | Charter the 2026-06-28 benchmark into perf tracks: connection fan-out concurrency, traffic_flows off the request path, tile first-paint LOD, streamed narration. | No new lane commit landed here. The panels-first split predates it at `fd50929`. T3 tile LOD overlaps the twin perf win `d3ab16a`. T4 graduated to WS-STREAM. | planned, not run as a lane | program orchestrator gate, not entered | Panels-first split already live; T4 moved to WS-STREAM. |
| console-ws-stream (WS-STREAM) | `.cca/catalogue/O0/20260628_console-ws-stream/README.md`, `WAVESET_CHARTER.md` | A reusable real-time streaming channel for the console, streamed narration as consumer one. | `web/lib/adaptiveConsole.ts` streaming. Commit `874f830` (streamed narration via a dedicated Vercel to App Runner SSE lane). | shipped | benchmark gate (measure-first) | Streamed narration over SSE live; non-streamed path kept as fallback. |
| console-ws-stream-handoff | `.cca/catalogue/O0/20260628_console-ws-stream-handoff/README.md`, `HANDOFF_CHARTER.md` | Rotation packet so a fresh thread can take over the WS-STREAM lane. | No code of its own. | shipped (handoff doc) | WS1 launch gate | The WS-STREAM work it framed landed at `874f830`. |

### Console copy and visual baseline

| id / family | charter | intent | resulting code | status | gate | outcome |
|---|---|---|---|---|---|---|
| console-copy-redaction (CXR-1, CXR-2, CXR-ACCEPT) | `.cca/catalogue/O0/20260628_console-copy-redaction/WAVESET_CHARTER.md` | Redact internal and reviewer copy leaking on the anonymous public console, promotion, effective confidence, raw agent IDs, skill manifest. Anonymous tier only. | `web/app/components/AdaptiveExplore.tsx`, `web/app/components/ActiveSurfaceHost.tsx`, `web/app/components/console/OrchestratorTrace.tsx` and `SidequestPanel.tsx`, `src/aws_backend/exploration/guide.py`. Commits `7116caf` (redact reviewer-only copy, harden /plan), `2655109` (rename public reply bubble). | shipped | cxr-deny-terms grep, copy gate | Anonymous render free of reviewer lexicon. |
| console-visual-pass (CVP-W1..W4) | `.cca/catalogue/O0/20260628_console-visual-pass/README.md`, `WAVESET_CHARTER.md` | Baseline design layer for web, base controls and forms CSS, layout and Get-access form, a net-new buoy marker, fixing the cone beacon that dominated the frame. | `web/app/styles/cvp-controls.css`, `web/app/styles/cvp-layout.css` (imported by `web/app/globals.css`), `web/lib/scene/markers/buoyMarker.tsx`. Commit `240570e`. | shipped (build files landed and wired; registry still marks the waves chartered) | cvp-preflight, before-and-after frames | Styled controls and buoy marker in the live scene. |
| liquid-glass-console (LGC-W0..W7) | `.cca/catalogue/O0/20260628_liquid-glass-console/README.md`, `WAVESET_CHARTER.md`, `TOKEN_HANDOFF.md` | Port the pax liquid-glass console, frosted surfaces, single-focus center model, self-hiding chat, edge panels, consent-gated persistence. | The `--glass-*` token family landed in `web/app/globals.css` via the BSW integrate at `61ba1d6`. `web/lib/focus/` is empty, the focus model and GlassSurface component were not built. | partial. Tokens shipped via BSW, the focus model and self-hide never shipped. Registry marks all LGC waves chartered. | design-acceptance and final M1-M10 gates, not run | Glass tokens available; the standalone liquid-glass console lane did not execute. |

### 3D twin, water, and orca

| id / family | charter | intent | resulting code | status | gate | outcome |
|---|---|---|---|---|---|---|
| terrain-bathymetry-twin (3D-TWIN: W2.6, W-CAM, W-PERFUX, W-PERFUX-BUILD, W-CAM-REG, W-LABELS) | `.cca/catalogue/O0/20260627_terrain-bathymetry-twin/README.md`, `WAVESET_CHARTER.md` | Live San Juan and Salish Sea coastal twin, one integrated land plus seafloor surface from NOAA CUDEM topobathy in react-three-fiber, same geometry feeding the s_space science consumer. | `web/app/components/scene/SalishScene.tsx`, `web/lib/scene/tiles/useTilesLayer.ts`, `web/lib/scene/water2/`. Commits `665c808` (W2.6 datum fix, NAVD88 0m to scene Y0), `d3ab16a` (W-PERFUX-BUILD, cut first-paint load and tighten the default view). | shipped (W2.6 and W-PERFUX-BUILD). W-PERFUX research complete. W-CAM, W-CAM-REG, W-LABELS chartered, not shipped, no `web/lib/scene/labels/` exists. | commit gated to O0, M10 frames | Twin renders with coastline at the waterline and a lighter first paint. |
| water-fx (WFX-RESEARCH, WFX-BUILD, WFX-INTEGRATE, WFX-ACCEPT) | `.cca/catalogue/O0/20260628_water-fx/README.md`, `WAVESET_CHARTER.md`, `SIGN_OFF.md` | Water and atmosphere shading realism for the twin, surface BRDF, waves, reflections, sky and sun and fog, and underwater per-channel absorption over the modeled seabed. | `web/lib/scene/wfx/realWfxEnv.ts`, scene decor and atmosphere modules. Commit `240570e` (land WFX plus real-SRKW orca into the Salish Sea twin). | shipped | O0 gate, Read-examined before-and-after frames | Physical-reading water and sky in the live twin. |
| orca-biologging-twin (ORCA: OM, OR, OG, OMAT, OEYE, OMOU, OPHYS, BUILD, OINT) | `.cca/catalogue/O0/20260628_orca-biologging-twin/README.md`, `PROGRAM.md`, `SIGN_OFF.md` | An animated orca for the underwater view, license-clean mesh plus anatomical rig plus motion from biologging telemetry, honesty label modeled animal with simulated motion. | `web/lib/scene/orca/` (OrcaController, rig, materials, eyes, mouth, physics, motion), `web/public/orca/orca.glb` plus `LICENSE.md` plus `motion/`. Commit `240570e`, refined in `61ba1d6` and `5bebddc`. | shipped | O0 and operator gates, mesh download signed off | Modeled orca driven by simulated DTAG kinematics in the twin. |

## Notes on traceability

1. The console-journey wavesets WS-INTENT, WS-SCENIC, WS-BATHY, WS-TRIPS,
   WS-PERF, WS-STREAM are catalogued program directories. They are not mirrored
   as their own families in `waves.registry.yaml`. Their code is traced by commit
   above, mainly `5415b8c`, `643eef7`, `fd50929`, `874f830`, and `fa9da22`.
2. The big landing commits in this area are `5415b8c` (console journey, intent,
   scenic, bathy, trips), `240570e` (WFX plus orca plus the CVP build files),
   `665c808` and `d3ab16a` (twin datum and perf), `7116caf` (CXR redaction), and
   `874f830` (WS-STREAM narration).
3. LGC is the one partial in this area. The token contract landed through BSW,
   not through an LGC lane run, and the focus model and self-hide were never
   built.
