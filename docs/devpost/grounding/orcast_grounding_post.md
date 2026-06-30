# orcast grounding post

## Header

orcast is a Salish Sea southern resident killer whale explore platform. It pairs
a browser 3D twin of the San Juan and Salish Sea coastline with an adaptive
orchestrator console, a forecasting and modeling stack, a B-side acoustic and
behavior workbench, and two whitepapers. The forecast is modeled, not measured
against held-out skill at the promotion bar, and the live surface shows 0 percent
promoted confidence on screen rather than a synthetic number.

Live surfaces:

- Primary console, anonymous explore, the `/workbench` B-side slice, and the
  `/about` capabilities surface, at https://orcast-h0.vercel.app
- Backend, AWS App Runner service orcast-aws-backend in us-west-2, reached
  through the Vercel proxy routes `/api/be` and `/api/narrate-stream`
- Deprecated, the Cloudflare-fronted self-host endpoint orcast-api.aimez.ai,
  decommissioned and recorded for provenance only

Repo: orcast. repo_state_verified_against: `e794dbd`. Dates America/New_York.

## How to read this

This post is organized into nine fixed perspectives: critical gap, concept,
construction, costs, qualifications, limits and tracked boundaries, risks, future
direction, and outcomes. Outcomes are landed and verifiable. Future direction is
not-yet-shipped work. The two never overlap.

The full waveset-to-code matrix is in the catalog at
[CATALOG.md](../../../.cca/catalogue/O0/20260630_grounding-post/dispatch/CATALOG/CATALOG.md).
The decision ledger and the dated step-log timeline are in
[LEDGER.md](./LEDGER.md). The authoritative machine waveset index is
[waves.registry.yaml](../waves.registry.yaml).

## Critical gap

orcast addresses two gaps, each anchored on verified primary sources under the
project primary-anchor claim gate.

The forecasting gap. Southern resident killer whale occurrence in the Salish Sea
is inferred from opportunistic, effort-biased sightings and from sparse acoustic
detections at a single in-region hydrophone station. Opportunistic sighting data
oversamples observer locations and undersamples whales away from people. Olson
and colleagues 2018 document opportunistic hotspot bias for these whales. Diggle,
Menezes, and Su 2010 formalize preferential sampling as a log-Gaussian Cox
process correction. Thornton and colleagues 2022 apply an effort correction in
the same management context. orcast derives this gap rather than asserting it.

The grounding gap. Orchestrated AI reasoning chains produce claims with no
output-level metric for whether each claim is bound to evidence. Mozannar and
colleagues 2025 describe Magentic-UI as a human-in-the-loop orchestration system
that proposes no grounding metric. Horvitz 1999 frames mixed-initiative
interaction without one. orcast proposes an uncited-claim-rate measure and a
step-log world-model evaluation, and tests them in the second whitepaper.

## Concept

orcast is anonymous-first. A visitor lands on a live react-three-fiber twin built
from NOAA CUDEM topobathy, with land and seafloor as one integrated surface at the
NAVD88 datum. An adaptive orchestrator console transduces camera motion and a chat
slot into served forecasts and a trips planner grounded in open transit data. A
B-side acoustic and behavior workbench at `/workbench` plays a hydrophone station,
shows a scrubbable spectrogram, runs an acoustic classifier, and reenacts DTAG
dive and feeding behavior on a modeled orca. Write actions are gated. Read and
explore are open.

The backend is a FastAPI service on App Runner with Amazon Bedrock for the explore
guide chat, DynamoDB for nine tables, S3 for assets and raw payloads, and a Step
Functions forecast orchestrator. Honesty locks hold across the surface. The
forecast is modeled-not-measured. The orca is a modeled animal driven by simulated
DTAG kinematics. Acoustic detections are confidence scores, not reviewed ground
truth.

## Construction

The full waveset-to-code matrix is the
[catalog](../../../.cca/catalogue/O0/20260630_grounding-post/dispatch/CATALOG/CATALOG.md).
The major code areas and representative paths:

- Backend and API. `src/aws_backend/main.py`, `src/aws_backend/auth.py`,
  `src/aws_backend/routers/`, `src/aws_backend/casting/`,
  `src/aws_backend/exploration/`, and the forecast orchestrator at
  `infra/aws/stepfunctions/forecast_orchestrator.asl.json`.
- Modeling. `modeling/studies/level0_detector.py` through
  `level3_prey_space.py`, `modeling/fit_kernels.py`, and `modeling/acoustic/`.
- Frontend and twin. The Next.js app under `web/app/`, the scene library under
  `web/lib/scene/` including `tiles/`, `terrain/`, `bathy/`, `water2/`, `wfx/`,
  `orca/`, `hydrophone/`, `hud/spectro/`, and `reenactment/`, and the B-side
  surface at `web/app/workbench/`.
- Infra and hosting. `infra/shared_host/`, `infra/aws/`, `infra/render_host/`,
  `infra/acoustic/`, `infra/orca/`, and `infra/tagtools/`.
- Demo, media, and docs. Beat captures under `web/e2e/beats/`, the whitepapers
  under `docs/whitepaper/` and `docs/whitepaper2/`, figures under `docs/figures/`,
  and submission copy under `docs/devpost/`.

## Costs

Real cloud services in production:

- Vercel hosts the Next.js frontend, the edge proxy route, and the dedicated Node
  server-sent-events stream route. Pricing basis is the Vercel project plan for
  orcast-h0.
- AWS App Runner runs the FastAPI backend in us-west-2 account 198456344617. A
  dedicated AutoScaling configuration named orcast-warm holds MinSize 2, MaxSize
  25, and MaxConcurrency 100, so a sibling instance always serves during a deploy
  or recycle. The warm-pool delta over a single instance is about 10.22 dollars
  per month. That figure is an estimate.
- Amazon Bedrock serves the explore guide chat on claude-haiku-4.5. DynamoDB
  holds nine tables. S3 holds two buckets for assets and raw payloads. AWS Step
  Functions runs the forecast orchestrator state machine. Pricing basis is
  on-demand usage in us-west-2.
- The GPU render host is a Tesla T4 instance named aimez-gpu-capture, driven
  headless through SSM with frames staged to S3. It is started only for capture
  under an operator gate, not always on. The exact EC2 instance type for the T4
  host is not recorded in the ledger and is marked UNVERIFIED. Pricing basis is
  on-demand GPU time during capture windows only.
- Amazon SES sends in sandbox mode to verified recipients only. Production access
  is an operator request that was not granted in this window.

## Qualifications

Measured results and their sources, with model figures labeled as estimates.

- Uncited-claim-rate benchmark. The second whitepaper defines the R_uncited
  measure and an eight-scenario table. The Maps-only baseline scenarios span 60
  to 100 percent uncited claims, reconciled from the benchmark methodology table.
  A separate three-query maps grounding probe averages about 85 and 89 percent on
  evidence scenarios. These are benchmark estimates.
- Level 0 detector. ROC AUC 0.879, gate PASS.
- Level 1 diel model. PSTH ratio 1.79, PASS at p equals 0.0005.
- Level 2 joint model. Measured no-go at the promotion bar, 0 percent promoted.
  A multi-station held-out skill experiment flipped a held-out lift of about
  0.078 positive, and a served-store experiment recorded about 0.177, neither on
  the served store at the fold-stable bar. These are estimates and nothing was
  promoted. Effective confidence stays 0 percent.
- Forecast candidate set. 200 candidates, 166 tier-A, validation and adversarial
  checks PASS.
- Wildlife sources. 34 real Chinook, southern resident, passive-acoustic, and
  prey-base sources ranked by gate impact. Nothing was promoted to confidence.
- Cold-start mitigation. A forced App Runner instance transition with the warm
  pool active produced a measured maximum user-visible gap of 0 milliseconds, 100
  percent 2xx status, and 8 of 8 session creates through the rollover. This is a
  measured result from `tools/testing/coldstart_gap_probe.py`.
- Adversarial final gate. The campaign AX-0 through AX-8 and the prose sweep
  reached a clean pass. One P0 authorization bypass on the evidence and journal
  routers was found and fixed with a router-level API key requirement, commit
  `d866e48`, re-verified 401.

CV figures are estimates. Simulated-user paths are proxies. No canonical sigma is
introduced. Forecast presence-gating and representativeness are stated as written
in the model card and the tracked-limits register.

## Limits and tracked boundaries

These are ratified in the tracked-limits register, decision
`orcast_tracked_limits_register_v1_20260628`. Each is marked surmountable or
unsurmountable for the submission window.

Unsurmountable for the window, ratified scope or honesty limits:

- TL-01 single hydrophone station, sparse acoustic detections.
- TL-02 acoustic detections are confidence scores, not reviewed ground truth.
- TL-03 effort-biased opportunistic sightings.
- TL-04 the gates decline to promote, an honest 0 percent promoted confidence in
  the pilot.
- TL-05 San Juan and Salish core pilot spatial scope.
- TL-07 the 3D twin is modeled in the research sandbox, not a shipped route.
- TL-08 DTAG replay and full annotation are direction, while review and
  hydrophone annotation are live.

Surmountable, a fix path exists and is owned:

- TL-06 excluded covariates in signal modeling.
- TL-09 the orchestration console is chartered, not shipped.
- TL-10 SES sandbox, verified recipients only.
- TL-11 no clean warm rollback, although the cold-start gap itself is closed.
- TL-12 the self-host inert checkout teardown is deferred.
- TL-13 ONC is disabled in production, enable-on-demand after SSRF validation.
- TL-14 the explore3d twin frontend is not deployed.
- TL-15 host access is SSM-only.
- TL-16 SDR O-2, O-3, O-4 drift.
- TL-17 demo narration is not prose-gated and gallery GIFs are open, which the
  demo-production recut lane addresses.

Recently closed and recorded in the same register:

- The App Runner cold-start user-visible gap, measured gap 0.
- The self-host and Cloudflare primary path, consolidated onto Vercel and App
  Runner.
- The explore-session RDS write path, now 200, resolving the DD-6 console impact.
- The P0 authorization bypass on the evidence and journal routers, commit
  `d866e48`.

## Risks

- App Runner is the sole production backend with no warm self-host fallback. The
  measured cold-start gap is 0 with the warm pool, but a reversion to the
  self-host would require re-provisioning the host service and the Cloudflare
  ingress and repairing the DD-6 RDS path first. Tracked as TL-11.
- The Open Network for Complex Networks hydrophone integration is shipped but
  disabled in production until an SSRF validation pass clears it. Tracked as
  TL-13.
- SES can only reach verified recipients until an operator obtains production
  access. Tracked as TL-10.
- The Software Defined Radio O-2, O-3, and O-4 doc-grep reds persist as known
  drift. Tracked as TL-16.
- The demo narration is not prose-gated and the gallery GIFs are open. The
  demo-production recut lane is the owner. Tracked as TL-17.
- The AWS4 architecture diagram is the one in-progress closeout item, family
  DGM-ARCH. The canonical TikZ architecture figure is current. This is the single
  open item, not a landed outcome.

## Future direction

Not-yet-shipped work, labeled as direction.

- The MLO production ML-ops platform. Chartered, build and deploy gated on AWS
  approval.
- The Level 2 and Level 3 modeling frontier, gated behind a fold-stable held-out
  lift bar of about 0.144.
- The B-side breadth waves beyond the B-API, B-SKILLS, B-REPLAY, B-ANNOT,
  B-PANELS, B-INGEST, and B-MCP.
- The liquid-glass console focus model and self-hide. Only the glass tokens
  landed.
- The uploads route and packaging family, and the UX U1 through U6 backlog.
- The D1 through D4 data-wiring lane and the P1 through P3 probe panels.
- The explore3d twin frontend, modeled in the sandbox and not deployed, TL-14.
- DTAG replay and full annotation, TL-08, and the excluded covariates, TL-06.
- The demo-production recut, where research and a script draft exist on disk and
  nothing is committed or promoted yet.
- The AWS4 architecture diagram, DGM-ARCH.

## Outcomes

Landed and verifiable work, each with a commit and a live surface or code path.
All commits resolve in the orcast git log at `e794dbd`.

- Live anonymous 3D explore console on orcast-h0.vercel.app. Commits `8e5c6ee`,
  `5415b8c`.
- Trips planner surfaced on the anonymous home. Commit `643eef7`.
- Terrain and bathymetry twin from CUDEM topobathy at the NAVD88 datum. Commits
  `665c808`, `d3ab16a`.
- Water effects and a modeled orca in the twin. Commits `240570e`, `61ba1d6`,
  `5bebddc`.
- B-side acoustic and behavior workbench at `/workbench`. Commit `b983976` for
  the slice, `61ba1d6` for the breadth lanes.
- B-side follow-up remediations across five lanes plus the STU live round-trip.
  Commits `5bebddc`, `337b36c`.
- Streamed narration over a dedicated server-sent-events route. Commit `874f830`.
- FastAPI backend, routers, and the Step Functions forecast orchestrator.
  Commits `5a7e2e8`, `e30d0ab`, `97b6397`.
- Forecast candidate set, 200 candidates, 166 tier-A. Commit `e30d0ab`.
- Level 0 detector and Level 1 diel model. Commits `e30d0ab`, `d4e6b06`.
- App Runner cold-start mitigation, measured gap 0. Commits `b9e2e13`, `27e8a97`.
- Hosting consolidation onto Vercel and App Runner, and the self-host
  decommission. Commits `1190fe7`, `85675c0`, `09a43ea`.
- GPU render host on a Tesla T4 driven via SSM and S3. Commits `3ae716a`,
  `08b89df`.
- Narrated demo video and the XTTS voice clone tooling. Commits `c306e41`,
  `52637f5`, `070b24d`.
- Architecture and ERD figures, both whitepapers, and the multi-panel and audited
  figure sets. Commits `e64b78a`, `0eefcee`, `3c74c35`, `9fe0a69`, `f0feb7a`,
  `f36da3f`, `e13d091`.
- Scrutiny and probe gates. Commit `97b6397`.
- Tracked-limits register and the public capabilities surface at `/about`.
  Commits `0eefcee`, `d19fd56`.
- P0 authorization bypass fix on the evidence and journal routers. Commit
  `d866e48`.
- Adversarial final-gate clean pass at backend commit `87ff466`.

## Charter index

Catalogued programs under `.cca/catalogue/O0/`, each linking to its charter and
its catalog row. The catalog area sections are linked once at the head of each
group.

Forecasting, modeling, and backend, cataloged in
[CATALOG.md section 1](../../../.cca/catalogue/O0/20260630_grounding-post/dispatch/CATALOG/CATALOG.md):

- forecast-candidates, [CANDIDATE_CHARTER.md](../../../.cca/catalogue/O0/20260627_forecast-candidates/CANDIDATE_CHARTER.md)
- mlops, [MLM_CHARTER.md](../../../.cca/catalogue/O0/20260627_mlops/MLM_CHARTER.md) and MLO_CHARTER.md
- wildlife-sources, [WILDLIFE_SOURCES_CHARTER.md](../../../.cca/catalogue/O0/20260627_wildlife-sources/WILDLIFE_SOURCES_CHARTER.md)
- open-science-integration, [WAVESET_CHARTER.md](../../../.cca/catalogue/O0/20260627_open-science-integration/WAVESET_CHARTER.md)
- integrate-promote-launch-handoff, [HANDOFF_CHARTER.md](../../../.cca/catalogue/O0/20260627_integrate-promote-launch-handoff/HANDOFF_CHARTER.md)
- the backend families R-Alpha through R-Gamma, AT, E, M, IC and J, A1, and Q1
  in [waves.registry.yaml](../waves.registry.yaml)

Frontend, console, twin, and water, cataloged in CATALOG.md section 2:

- explore3d-handoff, [HANDOFF_CHARTER.md](../../../.cca/catalogue/O0/20260626_explore3d-handoff/HANDOFF_CHARTER.md)
- 3d-twin, [README.md](../../../.cca/catalogue/O0/20260627_3d-twin/README.md)
- console-journey-trips, [README.md](../../../.cca/catalogue/O0/20260627_console-journey-trips/README.md)
- console-ws-intent, console-ws-scenic, console-ws-bathy, console-ws-trips,
  console-ws-perf, console-ws-stream, and console-ws-stream-handoff
- console-copy-redaction, [WAVESET_CHARTER.md](../../../.cca/catalogue/O0/20260628_console-copy-redaction/WAVESET_CHARTER.md)
- console-visual-pass, [WAVESET_CHARTER.md](../../../.cca/catalogue/O0/20260628_console-visual-pass/WAVESET_CHARTER.md)
- liquid-glass-console, [WAVESET_CHARTER.md](../../../.cca/catalogue/O0/20260628_liquid-glass-console/WAVESET_CHARTER.md)
- terrain-bathymetry-twin, [WAVESET_CHARTER.md](../../../.cca/catalogue/O0/20260627_terrain-bathymetry-twin/WAVESET_CHARTER.md)
- water-fx, [WAVESET_CHARTER.md](../../../.cca/catalogue/O0/20260628_water-fx/WAVESET_CHARTER.md)
- orca-biologging-twin, [PROGRAM.md](../../../.cca/catalogue/O0/20260628_orca-biologging-twin/PROGRAM.md)

B-side workbench and infra, cataloged in CATALOG.md section 3:

- bside-build, [BSIDE_CHARTER.md](../../../.cca/catalogue/O0/20260627_bside-build/BSIDE_CHARTER.md)
- bside-acoustic-behavior-workbench, [PROGRAM.md](../../../.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/PROGRAM.md)
- bsw-dispatch-handoff, [HANDOFF_CHARTER.md](../../../.cca/catalogue/O0/20260629_bsw-dispatch-handoff/HANDOFF_CHARTER.md)
- bsw-followup-remediation, [PROGRAM.md](../../../.cca/catalogue/O0/20260629_bsw-followup-remediation/PROGRAM.md)
- orcast-selfhost-cutover, [SELFHOST_CUTOVER_WAVESET_CHARTER.md](../../../.cca/catalogue/O0/20260626_orcast-selfhost-cutover/SELFHOST_CUTOVER_WAVESET_CHARTER.md)
- sd-deploy-handoff, [HANDOFF_CHARTER.md](../../../.cca/catalogue/O0/20260626_sd-deploy-handoff/HANDOFF_CHARTER.md)
- apprunner-coldstart, [WAVESET_CHARTER.md](../../../.cca/catalogue/O0/20260628_apprunner-coldstart/WAVESET_CHARTER.md)
- hosting-consolidation-followups, [WAVESET_CHARTER.md](../../../.cca/catalogue/O0/20260628_hosting-consolidation-followups/WAVESET_CHARTER.md)
- render-host, proof captures only, intent read from the registry note and
  `infra/render_host/`
- R-Foxtrot, the registry deploy family in [waves.registry.yaml](../waves.registry.yaml)

Demo, media, docs, and governance, cataloged in CATALOG.md section 4:

- demo-waveset, [DEMO_CAPTURE_CHARTER.md](../../../.cca/catalogue/O0/20260627_demo-waveset/DEMO_CAPTURE_CHARTER.md)
- demo-production, [PROGRAM.md](../../../.cca/catalogue/O0/20260628_demo-production/PROGRAM.md)
- demo-production-recut, [PROGRAM.md](../../../.cca/catalogue/O0/20260629_demo-production-recut/PROGRAM.md)
- the registry families V, VX, A, S, W, MP, FA, R0 through R5, SC, P, Q, U, H,
  and the CLOSEOUT set TLR, CAP, and DGM in [waves.registry.yaml](../waves.registry.yaml)
- the rotation packets orcast-handoff, os1-launch-handoff,
  signal-modeling-launch-handoff, trips-launch-handoff, and mlops-handoff
- grounding-post, this lane, [WAVESET_CHARTER.md](../../../.cca/catalogue/O0/20260630_grounding-post/WAVESET_CHARTER.md)

## Code index

The landing commits by area, with key files. All resolve in the git log.

- Backend and orchestrator. `5a7e2e8`, `e30d0ab`, `97b6397`, `a6797a8`,
  `1e4a6df`, `9b59e12`, `87ff466`, `7116caf`, `5415b8c`, `874f830`, `fd50929`.
  Files under `src/aws_backend/` and `infra/aws/stepfunctions/`.
- Modeling. `e30d0ab`, `d4e6b06`, `70526ee`, `484580f`, `ca5fd6a`. Files under
  `modeling/`.
- Frontend, console, twin, water, orca. `8e5c6ee`, `5415b8c`, `643eef7`,
  `665c808`, `d3ab16a`, `240570e`, `fa9da22`, `7116caf`, `2655109`. Files under
  `web/app/` and `web/lib/scene/`.
- B-side workbench and remediation. `b983976`, `61ba1d6`, `5bebddc`, `337b36c`,
  `a914ad1`, `0639103`. Files under `web/app/workbench/`, `web/lib/scene/`,
  `modeling/acoustic/`, `infra/acoustic/`, and `src/aws_backend/casting/`.
- Infra and hosting. `d97f798`, `1190fe7`, `85675c0`, `09a43ea`, `b9e2e13`,
  `27e8a97`, `3ae716a`, `08b89df`, `09684bf`, `7a49961`, `9adaf05`, `2ac3d78`.
  Files under `infra/shared_host/`, `infra/aws/`, and `infra/render_host/`.
- Demo, media, figures, whitepapers, gates. `c306e41`, `52637f5`, `070b24d`,
  `f36da3f`, `722d676`, `e64b78a`, `0eefcee`, `3c74c35`, `9fe0a69`, `f0feb7a`,
  `e13d091`, `d19fd56`, `915e4cc`, `d866e48`. Files under `web/e2e/beats/`,
  `docs/whitepaper/`, `docs/whitepaper2/`, `docs/figures/`, `docs/devpost/`, and
  `tools/waves/gates/`.

## Provenance pointer

The decision ledger, the dated step-log timeline, and the dependency and
supersession graph are in [LEDGER.md](./LEDGER.md), rendered from
[GP-LEDGER.json](../../../.cca/catalogue/O0/20260630_grounding-post/findings/GP-LEDGER.json).
The ledger holds 9 decisions, 9 registered state artifacts, 9 receipts, and 30
step logs across an action timeline of 2026-06-24 to 2026-06-30. Seven decisions
are active and two are superseded.
