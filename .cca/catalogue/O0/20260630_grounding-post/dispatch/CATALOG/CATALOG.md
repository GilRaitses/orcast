# GND-R catalog: waveset to code to outcome

The traceability matrix for the orcast project. Every catalogued program under
`.cca/catalogue/O0/` and every family in `docs/devpost/waves.registry.yaml`,
traced to the code it produced and the outcome it reached. Each resulting-code
cell cites a real path and at least one commit, or states that nothing landed.

Built by four area shards (forecasting and backend, frontend and twin, B-side
and infra, demo and docs), then merged and reconciled here. The four detailed
area sections follow the rollup and the reconciliation.

## Coverage rollup

- Catalogued program directories: 38 (the 37 prior programs plus this grounding
  program). All 38 are covered. No catalogued directory was left out.
- Registry families: roughly 45 families across the `waves:` list are covered
  (CAND, MLM, MLO, WILDLIFE, OS, the R channels Alpha through Foxtrot and
  R-backlog, AT, E, M, IC and J, A, Q, U uploads, WS-COLDSTART, SELFHOST, SD,
  BSIDE, ORCA, BSW, BSWR, 3D-TWIN, WATER-FX, CXR, CVP, LGC, DEMO, DEMO-PROD,
  DPR, V, VX, render-host, S, W, MP, FA, R0 through R5, SC, P, H, and the
  CLOSEOUT set TLR, CAP, DGM).
- Status mix: the majority of families and programs shipped with traced
  commits. A defined set is planned and never shipped. A small set was
  superseded. The exact totals are approximate because several wavesets are
  counted once at the program level and span multiple lanes; see each area
  section for the per-row status.

### Shipped, with commits (representative)

Forecast candidates and the L0 detector and L1 diel model; the backend auth,
community, partner, casting, interactions, and explore routers; the FastAPI app
and Step Functions orchestrator; the live 3D console journey, intent transducer,
scenic and bathy and trips surfaces, and streamed narration; the terrain and
bathymetry twin, the water effects, and the modeled orca; the `/workbench`
B-side acoustic and behavior slice and its breadth lanes; the BSWR remediations;
the App Runner cold-start mitigation and the hosting consolidation; the GPU
render host; the narrated demo video and the XTTS voice clone; the architecture
and ERD figures, both whitepapers, the multi-panel and audited figure sets; the
scrutiny and probe gates; the tracked-limits register and the public
capabilities surface.

### Planned, never shipped

The MLO ML-ops platform; the L2 and L3 modeling frontier (measured no-go at the
current bar); the BSIDE breadth waves beyond B-API; the LGC focus model and
self-hide (only the glass tokens landed); the U uploads route and packaging; the
UX U1 through U6 backlog; the D1 through D4 data-wiring lane; the P1 through P3
probe panels; DGM-ARCH (the AWS4 diagram, in progress); the DPR recut (research
and a script draft exist on disk, nothing committed, no fresh cut promoted).

### Superseded

`orcast-selfhost-cutover` shipped, then was retired by
`hosting-consolidation-followups` once App Runner became the sole production
backend. `demo-waveset` was superseded by `demo-production`, whose render was in
turn recut by DPR.

## Reconciliation of cross-shard overlaps

The shards flagged these boundary cases. Resolved here so the catalog has one
canonical owner per item.

1. Two distinct `R` families share the letter. The early backend channels
   R-Alpha through R-Echo and R-backlog are backend work (section 1). The later
   R0 through R5 are whitepaper research (section 4). They are not the same
   family.
2. R-Foxtrot is the deploy lane and R-Delta scopes to docs. Canonical owner for
   R-Foxtrot is infra (section 3); R-Delta is docs (section 4). Section 1 lists
   the backend R channels only.
3. The casting and interactions families E, M, IC, A split across backend and
   console. The backend halves are canonical in section 1. The console UI halves
   are traced by commit in section 2. A1 agent auth is in section 1; the rest of
   the A family is the demo path in section 4.
4. The launch-handoff directories (orcast-handoff, integrate-promote,
   os1-launch, signal-modeling-launch, trips-launch, mlops-handoff,
   console-ws-stream-handoff, bsw-dispatch-handoff, sd-deploy-handoff) are O0
   rotation packets, not programs. Nothing lands in the packet directory; the
   resulting code lives in the program home it points to. Sections 1 and 3 both
   listed some packets. Canonical rule: the packet row notes the program home,
   and the code is credited to that home's row.
5. The infra and hosting packets (orcast-selfhost-cutover, sd-deploy-handoff,
   apprunner-coldstart, hosting-consolidation-followups) are canonical in
   section 3 (infra). Section 1 also listed them under backend hosting; treat
   section 3 as the owner.
6. `orca-biologging-twin` appears in section 2 (mounted in the twin surface) and
   section 3 (the biologging core). Both facets are real. Canonical owner for
   the biologging mesh, rig, and motion is section 3; the twin mounting is
   section 2.
7. `render-host` appears in section 3 (infra) and section 4 (demo capture). It
   is GPU capture infrastructure used by both. It has no charter doc in its
   directory, only proof captures, so intent is read from the registry note and
   the landed `infra/render_host/**` code, not guessed.
8. `LGC` is the one partial. The `--glass-*` tokens landed through the BSW
   integrate, not through an LGC lane run; the focus model and self-hide were
   never built.
9. The letter `U` is reused: the uploads-and-packaging family (section 4, charter
   only) and the UX U1 through U6 backlog (frontend, planned). They are
   different families.

## Gaps to pick up at synthesis

These are flagged for GND-LENS, not failures of the catalog.

- Catalogue directories with no registry family: explore3d-handoff and the
  console-journey wavesets WS-INTENT, WS-SCENIC, WS-BATHY, WS-TRIPS, WS-PERF,
  WS-STREAM. They are traced by commit instead.
- Registry families with no catalogue directory of their own: R0 through R5, S,
  W, MP, FA, SC, P, Q, U, H, V, VX, DEMO, DEMO-PROD, and the CLOSEOUT set. They
  live under `docs/` or the registry only.
- Families that no shard claimed as owner because they are planned-only and
  feature-oriented: D1 through D4 data wiring, the UX U1 through U6 backlog, and
  G1 through G4 AI gateway and explore-map. Their status should be confirmed at
  synthesis before the Outcomes lens.

---

## Forecasting, modeling, backend, API

Shard 1 of 4. Area: forecasting and modeling plus backend and API. Every
resulting-code cell cites a real path and at least one commit, or says nothing
landed. Rows keyed by the registry family or wave where code landed, anchored to
the catalogued program dir. Cells avoid parentheses to pass the prose gate.

### Forecasting and modeling

| id / family | charter path | intent | resulting code and commit | status | gate | outcome |
|---|---|---|---|---|---|---|
| CAND, C-GAP/C-BUILD/C-VERIFY | .cca/catalogue/O0/20260627_forecast-candidates/CANDIDATE_CHARTER.md | Build a confirmed-sighting candidate set reachable from the four in-region hydrophones | .cca/catalogue/O0/20260627_forecast-candidates/candidates.targets.json plus orcahello caches, commit e30d0ab | done | C-VERIFY passed | 200 candidates, 166 tier-A, validation and adversarial checks PASS |
| MLM, M-L0..M-L3 | .cca/catalogue/O0/20260627_mlops/MLM_CHARTER.md | Leveled covariate-modeling go/no-go ladder L0 detector, L1 diel, L2 joint, L3 prey-space | modeling/studies/level0_detector.py through level3_prey_space.py, commits e30d0ab, d4e6b06, 70526ee, 484580f | L0/L1 done, L2/L3 frontier | mlops-gate, L gates | L0 ROC AUC 0.879 PASS, L1 diel PSTH 1.79 PASS p=0.0005, L2 FAIL at 0% with multi-station held-out skill flipped to +0.078, L3 withheld on presence-days |
| MLO, MLO-FEAT..MLO-CI | .cca/catalogue/O0/20260627_mlops/MLO_CHARTER.md | Production ML-ops platform: feature store, registry, scheduler, monitor, CI | nothing landed as product code, platform chartered only, EventBridge and Step Functions deploy operator-gated | planned, chartered | mlops-gate waiting | Not shipped. Build and deploy gated on AWS approval |
| WILDLIFE, WL-PREY/SRKW/ACOUSTIC/PREYBASE/SYNTH | .cca/catalogue/O0/20260627_wildlife-sources/WILDLIFE_SOURCES_CHARTER.md | Research real Chinook, SRKW, PAM, and prey-base sources to replace climatology placeholders | research register WILDLIFE_SOURCES_REGISTER.md and WL-*.md, commit ca5fd6a, no served code | done, research | none | 34 sources ranked by gate impact with P0/P1/P2 acquisition order, nothing promoted to confidence |
| OS, OS1..OS5 open-science-integration | .cca/catalogue/O0/20260627_open-science-integration/WAVESET_CHARTER.md | Open-science effort and detectability cross-checks, detection-range calculator, OrcaSound DSP | charter and findings docs landed, commit ca5fd6a, validated physics and DSP not committed as served code | done, measured NO-GO | OS1 served-skill | Detectability offset does not improve held-out CV skill at any scale, measured NO-GO, physics banked, confidence 0.0 |
| integrate-promote-launch-handoff | .cca/catalogue/O0/20260627_integrate-promote-launch-handoff/HANDOFF_CHARTER.md | Judge served vs baseline forecast skill, count presence-days | verdict docs TA2_TA3, TA5_SERVED, TB2_TB5, TB4_PRESENCE_DAY_COUNT, commit ca5fd6a, no product code | done, verdicts | none | Served refit verdicts and presence-day counts recorded, no promotion |

### Backend and API

| id / family | charter path | intent | resulting code and commit | status | gate | outcome |
|---|---|---|---|---|---|---|
| R-Alpha, R-Beta | docs/devpost/waves.registry.yaml R family | Auth plus community and partner API channels and the Vercel-to-backend proxy | src/aws_backend/auth.py, routers/community.py, routers/partner.py, web/app/api/be, web/app/api/v1, commits a6797a8, 1e4a6df, 8e5c6ee | done | R-echo verify | Reviewer auth and community and partner routers shipped |
| R-Gamma | docs/devpost/waves.registry.yaml R family | Kernel fit plus Step Functions forecast orchestrator | modeling/fit_kernels.py, infra/aws/stepfunctions/forecast_orchestrator.asl.json, commit 97b6397 | done | none | Kernel fit and ASL state machine committed |
| AT-0..AT-4 | docs/devpost/waves.registry.yaml AT family | FastAPI app, routers, and deploy | src/aws_backend/main.py, src/aws_backend/routers, commits 5a7e2e8, e30d0ab | done | AT-1 and AT-4 passed | Backend app and routers shipped, deploy and angular-build gates passed |
| E, E0..E5 | docs/devpost/waves.registry.yaml E family | Exploration backend, explore route, and /explore surface | src/aws_backend/exploration, routers/explore.py, commits 9b59e12, 87ff466, 7116caf | done | e2 and e-gate passed | Exploration surface shipped. Frontend half overlaps shard 3 |
| M, M0..M4 | docs/devpost/waves.registry.yaml M family | Central Casting managed-agents backend | src/aws_backend/casting, routers/managed_agents.py, routers/interactions.py, commits a6797a8, 5415b8c | done | m and m-gate passed | Managed agents and casting backend shipped |
| IC, IC0..IC7 and J0..J2 | docs/devpost/waves.registry.yaml IC family | Interactions concierge, skills manifest, keyed /plan planner | src/aws_backend/casting concierge.py, manifest.py, planner.py, panels.py, web/app/api/interactions, commits 874f830, fd50929, 7116caf | done | ic, ic4, ic6 passed | Interactions and planner backend shipped. Console UI half overlaps shard 3 |
| A1 | docs/devpost/waves.registry.yaml A family | Agent auth plus keyed API for the no-cred demo | web/lib/agentAuth.ts, web/app/api/be, web/app/api/interactions/plan, commit 8e5c6ee | done | a-gate passed | Agent auth shipped. Rest of A family is demo, shard 7 |
| Q1b, Q1c | docs/devpost/waves.registry.yaml Q family | API and backend plus DynamoDB schema scrutiny | tools/waves/gates/q1b-api-schema.sh, tools/waves/gates/q1c-ddb-schema.sh | done | passed | API and DynamoDB scrutiny passed, gaps Q1e-01 and Q1f-07 closed |
| U1 uploads family | docs/devpost/submission/U0_UPLOADS_AND_PACKAGING_CHARTER.md | Backend evidence upload route plus S3 storage | nothing landed yet | in progress | none | Not shipped. Uploads and packaging, overlaps shard 8 |

### Backend hosting and deploy

| id / family | charter path | intent | resulting code and commit | status | gate | outcome |
|---|---|---|---|---|---|---|
| WS-COLDSTART, CS1..CS5 | .cca/catalogue/O0/20260628_apprunner-coldstart/WAVESET_CHARTER.md | Drive the App Runner cold-start and recycle gap to zero user-visible impact | infra/aws warm pool config plus web/app/api/be proxy edge-blip retry, commits b9e2e13, 27e8a97 | done | CS4 acceptance | Measured max gap 0, 100 percent 2xx and 8 of 8 session-creates through rollover, warm pool MinSize 2 at about 10 dollars per month |
| SELFHOST, selfhost-cutover | .cca/catalogue/O0/20260626_orcast-selfhost-cutover/SELFHOST_CUTOVER_WAVESET_CHARTER.md | Cut production over to a self-hosted backend | infra self-host kit and .ddb baseline ledger, commit d97f798 | superseded | none | Shipped then retired by the hosting consolidation 1190fe7 and decommission 09a43ea onto Vercel plus App Runner |
| SD lane, sd-deploy-handoff | .cca/catalogue/O0/20260626_sd-deploy-handoff/HANDOFF_CHARTER.md | Fix the red Vercel deploy and write the Standing Decisions Register | web/vercel.json and .cca/STANDING_DECISIONS_REGISTER.md, commits 09684bf, 7a49961 | done | GP preflight | Verified-green deploy, root cause was the web app not tracked in git, register wired above CLAIM_BOUNDARIES.md |
| Rotation packets | .cca/catalogue/O0/20260627_mlops-handoff, signal-modeling-launch-handoff, os1-launch-handoff, orcast-handoff | Self-replacement orchestration packets for the forecast and modeling lanes | docs only, commit ca5fd6a, no product code | done, process docs | none | Rotation and hydration packets, no code landed from these dirs |

### Notes and overlaps

- Two distinct registry families share the letter R. The early R channels Alpha
  through Echo and R-backlog are this shard's backend and modeling work. The
  later R0 through R5 are whitepaper research and belong to the documentation
  shard.
- R-Foxtrot and R-Delta sit in the R family but scope to infra/aws and
  docs/devpost, so they belong to the infra-and-hosting and
  documentation shards.
- The casting and interactions families E, M, IC, A split across backend and
  console. The backend halves are traced here. The web UI halves belong to the
  frontend-and-console shard.
- BSW-BAM and BSWR-ACX scope to modeling/acoustic and infra/acoustic, and
  BSWR-STU scopes to src/aws_backend/routers. These touch this shard's code
  areas but belong to the B-side acoustic and behavior workbench shard. Commits
  b983976, 61ba1d6, 5bebddc.
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
<!-- Catalog shard 3 of 4. Area: B-side acoustic + behavior workbench, infra + hosting.
     Every claim traces to a charter path, a code path, or a git commit. No guessing. -->

## B-side workbench, infra, hosting

### B-side, workbench, biologging programs and families

| id / family | charter | intent (one line) | resulting code | status | gate | outcome |
|---|---|---|---|---|---|---|
| BSIDE (bside-build) | `.cca/catalogue/O0/20260627_bside-build/BSIDE_CHARTER.md` | Research-backend whale-tagger B-side on the orcast stack, DTAG dive and feeding read API, simulated-only until a partnership data agreement | `src/aws_backend/routers/dtag.py` (`e30d0ab`) | B-API done, B-SKILLS / B-REPLAY / B-ANNOT / B-PANELS / B-INGEST / B-MCP chartered | run-gate, test_dtag.py green | B-API shipped (4 dtag endpoints, simulated flag, feeding returns `not_trained`). The six breadth waves never shipped (planned). |
| ORCA (orca-biologging-twin) | `.cca/catalogue/O0/20260628_orca-biologging-twin/PROGRAM.md` | Animated orca for the underwater twin, open-licensed mesh plus anatomical rig plus biologging-driven motion, modeled animal with simulated or partnership-gated motion | `web/lib/scene/orca/**`, `web/public/orca/**`, `infra/orca/**` (`a914ad1` Wave-0 mesh + motion, `0639103` real SRKW driver, `240570e` mounted into twin) | Mesh, rig, motion driver, materials shipped; eyes / mouth / physics partial | `SIGN_OFF.md` O0 operator | orca.glb plus biologging driver landed and mounted in SalishScene. Note: also a 3D-twin shard surface; biologging core is this shard. |
| BSW (bside-acoustic-behavior-workbench) | `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/PROGRAM.md` | B-side acoustic and behavior workbench, hydrophone station player plus scrubbable spectrogram HUD plus real acoustic classifier plus DTAG-driven reenactment, no standins | `web/app/workbench/**` (`b983976` slice), `web/lib/scene/hydrophone/**`, `web/lib/scene/hud/spectro/**`, `web/lib/scene/reenactment/**`, `web/lib/scene/ocean/**`, `infra/acoustic/**`, `modeling/acoustic/**`, `infra/tagtools/**`, `src/aws_backend/casting/**` (`61ba1d6` breadth) | Slice plus breadth (BST / BAM / BSH / BRE / BSS) shipped | `SIGN_OFF.md`, accepted on the T4 render host | Real demo slice landed at `/workbench` (`b983976`); breadth lanes landed on the homepage (`61ba1d6`). SLICE-INTEGRATE / SLICE-ACCEPT remain gated packets. |
| (bsw-dispatch-handoff) | `.cca/catalogue/O0/20260629_bsw-dispatch-handoff/HANDOFF_CHARTER.md` | O0 self-replacement rotation packet to run the six BSW breadth and integrate lanes from a fresh thread | nothing landed directly; packet committed at `61ba1d6` | Rotation packet | n/a | Handoff packet only. The lanes it hands off landed at `61ba1d6`. |
| BSWR (bsw-followup-remediation) | `.cca/catalogue/O0/20260629_bsw-followup-remediation/PROGRAM.md` | Remediation round closing the BSW STOP-to-O0 follow-ups across six lanes (ACX, STU, OCN, ENV, PRF, STX) | `web/lib/scene/ocean/**`, `web/lib/scene/orca/**`, `infra/acoustic/**`, `modeling/acoustic/**`, `infra/aws/**`, `src/aws_backend/routers/**`, `web/lib/annotation/**` (`5bebddc` remediation, `337b36c` STU-ACCEPT) | ACX / OCN / ENV / PRF / STU shipped; STX deferred (optional) | Per-lane R, Q, B, ADV, INT, ACCEPT | Five lanes remediated (`5bebddc`); STU live round-trip PASS (`337b36c`); STX deferred with cost stated. |

### Infra and hosting programs

| id / family | charter | intent (one line) | resulting code | status | gate | outcome |
|---|---|---|---|---|---|---|
| (orcast-selfhost-cutover) | `.cca/catalogue/O0/20260626_orcast-selfhost-cutover/SELFHOST_CUTOVER_WAVESET_CHARTER.md` | Co-tenant the orcast FastAPI backend on the pax aimez-services EC2 host, repoint the frontend via Cloudflare tunnel, keep App Runner as rollback | `infra/shared_host/**` (`d97f798` cutover kit plus .ddb baseline) | Done (executed 2026-06-26) | WS-VERIFY end-to-end green | Self-host served `orcast-api.aimez.ai`, prod verified, App Runner kept as rollback. Later superseded by hosting-consolidation. |
| (sd-deploy-handoff) | `.cca/catalogue/O0/20260626_sd-deploy-handoff/HANDOFF_CHARTER.md` | Rotation packet, deploy hardening first (fix the red Vercel build) plus the Standing Decisions Register | `web/vercel.json`, root `vercel.json` removed (`09684bf`) | Done | Vercel prod build green | Root vercel.json deleted, minimal `web/vercel.json` added, red prod build fixed; STANDING_DECISIONS_REGISTER written (`09684bf`). |
| WS-COLDSTART (apprunner-coldstart) | `.cca/catalogue/O0/20260628_apprunner-coldstart/WAVESET_CHARTER.md` | Drive the App Runner cold-start and instance-recycle gap to zero user-visible impact | `infra/aws/**` (`b9e2e13` CS4 PASS MinSize=2 warm pool) plus a Vercel proxy edge-blip retry | COMPLETE, gap = 0 | CS4 measured a forced transition, max_gap_while_health_up_ms = 0.0 | orcast-warm AutoScaling MinSize=2 (about +$10/mo, estimate) plus bounded retry; gap measured 0 (`b9e2e13`). DDB `orcast_coldstart_mitigation_v1_20260628`. |
| WS-HOSTFOLLOWUP (hosting-consolidation-followups) | `.cca/catalogue/O0/20260628_hosting-consolidation-followups/WAVESET_CHARTER.md` | Discharge the DD-10 hosting-consolidation open items, make App Runner canonical, retire the self-host as primary | `infra/shared_host/**` (`85675c0` charter plus FW1, `09a43ea` FW2 decommission) | COMPLETE (2026-06-28) | FW2 operator-gated destructive, pre and post proof | Self-host and Cloudflare ingress retired (`09a43ea`); App Runner is the sole prod backend; the shared EC2 host was not terminated because pax co-tenants run on it. DDB `orcast_selfhost_decommission_v1_20260628`. |
| (render-host) | no charter doc in the dir (only `proof/` gate captures) | From registry and code, a reliable headless GPU render host on aimez-services driving the Tesla T4 `aimez-gpu-capture` via SSM and S3 for B-side frame capture | `infra/render_host/**` (`3ae716a` reliable headless render via SSM+S3, `08b89df` real-GPU Tesla T4 via SSM) | Code shipped; the dir itself is a proof and capture folder | n/a | Render-host tooling landed (`3ae716a`, `08b89df`); the dir holds proof PNGs of the `/workbench` B-side slice. No charter doc present, so intent is read from the registry note and the code. |
| R-Foxtrot (registry deploy family) | registry `docs/devpost/waves.registry.yaml` (no catalogue dir) | The deploy lane, AWS infra plus deployment tooling | `infra/aws/**`, `tools/deployment/aws/**` (`9adaf05`, `2ac3d78`, `97b6397`) | done | n/a in registry | Infra and deploy scope landed across the listed commits. Shared with the backend shard; listed here for the infra scope_globs. |

### Launch-handoff rotation packets

These directories are O0 self-replacement packets, not programs. They hand a downstream program to a fresh thread. Nothing lands in the packet directory itself; the resulting code is in the program home it points to.

| id / family | charter | intent (one line) | resulting code | status | gate | outcome |
|---|---|---|---|---|---|---|
| (orcast-handoff) | `.cca/catalogue/O0/20260627_orcast-handoff/HANDOFF_CHARTER.md` | Rotation packet resuming the orcast B-side build, forecast ML-ops, and demo capture | nothing landed in the dir; packet committed at `ca5fd6a` | Handoff | n/a | Packet only. Downstream B-side B-API landed (`e30d0ab`). |
| (integrate-promote-launch-handoff) | `.cca/catalogue/O0/20260627_integrate-promote-launch-handoff/HANDOFF_CHARTER.md` | Rotation packet to act on the graduation synthesis, run served-store fits, and reach a promotion decision | convergence files under `modeling/` are local-only and untracked, so nothing landed in the tracked repo; packet committed at `ca5fd6a` | Handoff (forecast / modeling lane) | served gate plus supervisor decision | Measured verdicts only (TA5 +0.177 on the experiment store, not on the served store); nothing promoted, effective confidence 0%. Note: forecast and modeling area, overlaps the modeling shard. |
| (os1-launch-handoff) | `.cca/catalogue/O0/20260627_os1-launch-handoff/HANDOFF_CHARTER.md` | Rotation packet for the open-science effort and detectability lane (OS1) | program home `.cca/catalogue/O0/20260627_open-science-integration/`; nothing landed in this dir | Handoff, OS1 measured NO-GO | served-skill held-out CV | Detectability offset showed no served-skill improvement at any scale; validated physics and DSP pipeline banked; nothing promoted. Note: open-science and modeling area, overlaps another shard. |
| (signal-modeling-launch-handoff) | `.cca/catalogue/O0/20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md` | Rotation packet to launch the signal and modeling research campaign | program home `.cca/catalogue/O0/20260627_mlops/`; nothing landed in this dir | Handoff, campaign chartered | +0.144 fold-stable bar | Planned and chartered, effective confidence 0%, nothing promoted. Note: modeling area, overlaps the modeling shard. |
| (trips-launch-handoff) | `.cca/catalogue/O0/20260627_trips-launch-handoff/HANDOFF_CHARTER.md` | Rotation packet for the Console Journey and Trips program | program home `.cca/catalogue/O0/20260627_console-journey-trips/`; nothing landed in this dir | Handoff, program chartered | W1 launch pending | Planned and chartered. Note: console area, overlaps the console shard. |

### Notes on coverage and ambiguity

- Registry families covered: BSIDE, ORCA, BSW, BSWR, and the R-Foxtrot deploy family. The cold-start and hosting-consolidation work is registered as DDB decisions, not as named registry families.
- render-host has no charter doc in its directory; intent is read from the registry note and the landed `infra/render_host/**` code, not guessed.
- The launch-handoff packets for OS1, signal-modeling, integrate-promote, and trips point at forecast, modeling, open-science, and console program homes that belong to other shards. They are listed here only because they are launch-handoff rotation packets in this shard's assignment; the underlying program code is the other shards' to catalog.
## Demo, media, documentation, governance

Catalog shard 4 of 4. Area is demo and media plus documentation and governance.
Each row traces a charter to the code it produced, a commit, status, gate, and
outcome. No claim without a trace. Planned-never-shipped says so.

### Demo and media

Catalogued program directories under `.cca/catalogue/O0/` plus the registry
families that drive the submission video, the per-beat captures, the voice
clone, the agent demo, and the GPU render host.

| id or family | charter | intent | resulting code and commit | status | gate | outcome |
|---|---|---|---|---|---|---|
| DEMO, demo-waveset | `.cca/catalogue/O0/20260627_demo-waveset/DEMO_CAPTURE_CHARTER.md` | orcast-side execution mirror of the pax DEMO design. Lock the A-side and B-side script, then capture the first beats. Honesty locks: nothing unbuilt shown as live, forecast effective confidence 0 percent stays on screen. | `W-STORY.md`, beats under `web/e2e/beats/`. Commit `e30d0ab`. | done for the story lock and first beats | none formal, capture had an operator green-light | shipped the locked script. The render was blocked then superseded by DEMO-PROD and DPR. |
| DEMO-PROD, demo-production | `.cca/catalogue/O0/20260628_demo-production/PROGRAM.md` | Director-based demo production modeled on the pax briefing. Four-stage chain SET, BLK, CAM, SCR, render, with a binary R1 to R5 screen-test rubric and eight orcast honesty locks. Replaces the old A-side cut and the blocked B-side DEMO render. | program and stage docs under `.cca/catalogue/O0/20260628_demo-production/`, beat specs under `web/e2e/beats/`, `tools/testing/build_ddb_proof_slide.py`. Commits `d19fd56`, `ca5fd6a`. | program shipped, render chartered not rendered | DSCR screen-test-binary-R1-R5, DRENDER v-beat plus v-stitch plus v-render, render is operator-gated | shipped the production framework and beat captures. DRENDER stayed chartered, then recut by DPR. |
| DPR, demo-production-recut | `.cca/catalogue/O0/20260629_demo-production-recut/PROGRAM.md` | Re-cut the stale narrated demo, which predates the `/workbench` B-side and the BSWR remediations. Research first, then a script gate, then the DEMO-PROD director chain, then a written submission description. | research findings, `SCRIPT_DRAFT.md`, `PROGRAM.md` present on disk under the program dir, none committed. | research on disk, all else planned | DPR-S script operator gate, DPR-CAP and DPR-PROMOTE operator gates | nothing landed in git. Research and a script draft exist uncommitted, no fresh cut promoted yet. |
| V, per-beat video | registry `V0` to `V3`, output `docs/devpost/figures/_demo-run/demo-final.webm` | Per-beat Playwright capture, beat-check and stitch gates, then the stitched narrated demo. | `web/e2e/beats/`, `docs/devpost/figures/_demo-run/`. Commits `c306e41`, `52637f5`, `070b24d`. | done | v-beat, v-stitch | shipped the narrated demo video and its beat captures. |
| VX, voice clone | registry `VX0` to `VX3`, output `docs/devpost/figures/_demo-run/demo-final-cloned.webm` | XTTS voice clone narration over the demo, rendered to a cloned-voice cut. | `tools/testing/tts_clone.py`, `tools/testing/tts_narrate.py`, `tools/waves/gates/vx-render.sh`. Commits `c306e41`, `070b24d`, `97b6397`. | done | manual | shipped the XTTS narration tooling and the narrated cut. |
| A, agent demo | registry `A0` to `A5`, charter `docs/devpost/submission/A0_AGENT_DEMO_CHARTER.md` | No-credential agent demo path, demo slides, maps smoke and video gates. Mostly demo and submission media, with auth pieces that overlap the frontend area. | `web/public/demo-slides/`, `docs/devpost/DEMO_NO_CRED_STORYBOARD.md`, `web/lib/agentAuth.ts`, `tools/waves/gates/a-video-gate.sh`. Commits `f36da3f`, `8e5c6ee`, `722d676`. | done | a-gate, a-maps, a-video-gate | shipped demo slides, the no-cred storyboard, and the agent auth path. |
| render-host | `.cca/catalogue/O0/20260628_render-host/` proof frames, registry note on the Tesla T4 host | Reliable headless GPU render and capture host on aimez-gpu-capture Tesla T4 via SSM and S3, used to capture twin and B-side frames. | `infra/render_host/`, proof PNGs under the program dir. Commits `3ae716a`, `08b89df`, `fa6c0f2`. | done | none formal, GPU start is an operator gate | shipped the real GPU capture host and refreshed proof frames. |

### Documentation and figures

Registry families with no catalogue directory of their own. They live under
`docs/`. Whitepaper, figures, submission copy, research sync.

| id or family | charter | intent | resulting code and commit | status | gate | outcome |
|---|---|---|---|---|---|---|
| S, submission sync | charter `docs/devpost/submission/S0_SUBMISSION_SYNC_CHARTER.md` | Architecture figure, the ERD workflows diagram, and the submission copy set kept in sync. | `docs/devpost/figures/architecture.png`, `docs/devpost/figures/orcast-erd-workflows.drawio`, `docs/devpost/SUBMISSION.md`. Commits `e64b78a`, `0eefcee`, `722d676`. | done | s-gate | shipped the architecture and ERD figures plus the synced submission copy. |
| W, whitepaper | charter `docs/whitepaper/W0_WHITEPAPER_CHARTER.md` | Build the orcast whitepaper LaTeX, references, equations, figures, and the compiled PDF. | `docs/whitepaper/`, output `docs/whitepaper/Build/Raitses_orcast_2026.pdf`. Commits `3c74c35`, `97b6397`, `9fe0a69`. | W1 in progress per registry, W6 PDF verified done | manual-pdf-verify | shipped the compiled PDF. W1 build still flagged in_progress in the registry. |
| MP, multi-panel figures | output `docs/figures/mp-benchmark-results.json` and `docs/figures/MP4_MULTI_PANEL_REVIEW.md` | Benchmark-backed multi-panel problem, mechanism, and benchmark-scope figures. | `docs/figures/`. Commit `f0feb7a`. | done | none | shipped the benchmark figures and the multi-panel review. |
| FA, figure audit | output `docs/figures/FA0_DEFECT_REGISTER.md` | Audit, remediate, validate, and adversarially review the TikZ figures. | `docs/figures/fig-*/figure.tex`. Commits `f36da3f`, `e13d091`. | done | none formal | shipped the corrected figure set with validation and adversarial reports. |
| R0 to R5, research sync | charter `docs/devpost/submission/R0_RESEARCH_SYNC_CHARTER.md` | Research-source files for the whitepaper, the second grounding whitepaper, and refreshed demo storyboards and devpost copy. Distinct from the backend R-Alpha to R-backlog channel family, which belongs to another shard. | `docs/whitepaper/research/`, `docs/whitepaper2/`, `docs/devpost/DEMO_STORYBOARD.md`. Commits `f0feb7a`, `3c74c35`. | done | none | shipped the research sources and the second whitepaper PDF. |
| SC, search cycle | charter `docs/devpost/submission/SC0_SEARCH_CYCLE_CHARTER.md` | Literature search-cycle research files SF-01 to SF-16, folded into both whitepapers. | `docs/whitepaper/research/SF-*`, `docs/whitepaper2/LX/`. Commits `f0feb7a`, `3c74c35`. | done | SC6 gate | shipped the search-cycle sources and the updated PDFs. |

### Governance and probes

Probe, scrutiny, packaging, hackathon-submit, and closeout families. These set
or check the project's locks and the submission posture.

| id or family | charter | intent | resulting code and commit | status | gate | outcome |
|---|---|---|---|---|---|---|
| P, probes | playbook `docs/devpost/ADVERSARIAL_PROBE_PLAYBOOK.md` | Adversarial probe family. P0 the workflow truth table and lane ownership, P1 to P3 planned probe panels. | `docs/devpost/workflow-truth-table.md`, `infra/aws/state/LANE_OWNERSHIP.md`, the playbook. Commit `97b6397`. | P0 done, P1 to P3 planned | P1-gate, P2 and P3 manual | shipped the truth table and playbook. P1 to P3 never ran. |
| Q, scrutiny | charter `docs/devpost/submission/Q0_SCRUTINY_CHARTER.md` | Six-layer scrutiny pass Q1a to Q1f, remediation Q2, and the adversarial review gate QF. | `docs/devpost/QF_ADVERSARIAL_REVIEW.md`, `tools/waves/gates/q1b-api-schema.sh`, `tools/waves/gates/q1c-ddb-schema.sh`, `tools/waves/gates/q1f-wp-claims.sh`. Commit `97b6397`. | done | QF gate | shipped the scrutiny gates and the adversarial review, gaps Q1e-01 and Q1f-07 closed. |
| U, uploads and packaging | charter `docs/devpost/submission/U0_UPLOADS_AND_PACKAGING_CHARTER.md` | Evidence upload route plus S3, account content management, media-upload UI, content-only share PDFs, and arXiv tarballs. Distinct from the planned UX U1 to U6 family, which belongs to the frontend area. | charter committed under `docs/devpost/submission/`. Commit `97b6397`. | U0 charter done, U1 in_progress, U2 to UF planned | U5 gate, UF review | shipped the charter only. The upload route and packaging never landed. |
| H, hackathon submit | checklist `docs/devpost/HACKATHON_SUBMIT_CHECKLIST.md` | Hackathon submit verification and the manual submit record. | `docs/devpost/HACKATHON_SUBMIT_CHECKLIST.md`, output `docs/devpost/submission/H1_MANUAL_SUBMIT.md`. Commit `915e4cc`. | H0 on_demand, H1 manual | H0 gate | shipped the submit checklist. H1 is a manual operator step. |
| CLOSEOUT, WS-CLOSEOUT | registry families `TLR`, `CAP-*`, `DGM-*` | Ratify the tracked-limits register, publish the capabilities, limits, risks, and future surface in docs and on `/about`, rebuild the nine-table DynamoDB proof slide, and add the AWS4 architecture diagram. | `.sst/tracked_limits_register_v1.json`, `docs/devpost/SUBMISSION.md`, `web/app/about/page.tsx`, `tools/testing/build_ddb_proof_slide.py`, `docs/devpost/figures/architecture-aws4.drawio`. Commits `0eefcee`, `d19fd56`, `f36da3f`. | TLR, CAP-DOCS, CAP-WEB, DGM-DDB done, DGM-ARCH in_progress | ddb-register, cxr-deny-terms, read-verified-frame | shipped the limits register, the public capabilities surface, and the proof slide. The AWS4 diagram is the in_progress item. |
| GND, project grounding surface | `.cca/catalogue/O0/20260630_project-grounding-surface/PROGRAM.md` and `POST_SPEC.md` | The umbrella for this catalog. Build one grounding surface across nine lenses that traces every waveset to its code and outcome. This shard is GND-R catalog work. | `.cca/catalogue/O0/20260630_project-grounding-surface/`, this file under `dispatch/CATALOG/parts/`. No commit yet, the program is in flight. | in progress | post-gate, operator consolidate gate | the catalog and the grounding post are being authored now. Nothing committed yet. |

### Families and dirs this shard did not take, with reasons

- `D1` to `D4`, data wiring, planned only, doc target `docs/methodology/DATA_WIRING.md`. Folded into `G4` per the registry note. Data and modeling oriented, so it belongs to the modeling shard.
- UX `U1` to `U6`, planned only, doc `docs/ux/IMPLEMENTATION_BACKLOG.md`. Frontend and UX, belongs to the frontend shard. Note that the letter U is reused by the uploads family above.
- `E` and `F`, backend exploration and probe features under `src/aws_backend/exploration/`. Belong to the backend shard. Their doc outputs `E3`, `E5`, `F0`, `F4` under `docs/devpost/exploration/` are docs but track backend work.
- `G1` to `G4`, AI gateway and explore-map features. Belong to the backend or frontend shard. `G3` probe dossier `docs/devpost/adversarial-findings-2026-06.md` and `G4` `docs/devpost/G4_DATA_WIRING_STATUS.md` are governance and docs outputs but track feature work.
