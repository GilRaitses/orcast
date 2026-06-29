# orcast forecast orchestrator

H0 "Hack the Zero Stack" build synthesis. Directive id: `h0_orcast_project_synthesis_v1`.

## Recommendation

Adapt the existing orcast work rather than start new. The kernel-forecast
pipeline (`modeling/`, `src/aws_backend/kernel_model/`), the community
moderation queue (`src/aws_backend/routers/community.py`), and the multi-source
provenance layer already match the directive's anti-chatbot requirements
(multiple reasoning components, external data, provenance, humans inside
consequential decisions). The hackathon work is an orchestration spine and a
provenance drill-down surface, not a new domain.

The "zero" we hack is zero unaudited assertions: the forecast is always shown,
but its sharpness is governed by automated fitness gates plus a human promotion
step, and any point on it traces back to its sources.

## Architecture template

### project_name
orcast forecast orchestrator.

### problem_statement
Wildlife and environmental forecasts present a smooth, confident surface that
hides how thin or biased the evidence is. Observers cannot tell whether a
"hotspot" reflects animal behavior or just where someone looked. ORCAST makes
the evidence chain and the model's earned confidence first-class.

### target_users
Shore and kayak whale watchers (public forecast), field scientists and
naturalists (gate dashboard and provenance drill-down), data stewards
(moderation queue and promotion approvals).

### user_journey
1. Open the map; a broad low-confidence forecast is already there with inline
   confidence.
2. Open the instrument overlay (acoustic, visual, stations) to see the evidence.
3. Tap a cell; a provenance trace shows the driving kernels, each kernel's gate
   status, and the raw detections.
4. Submit a shore sighting; it enters moderation, not the live map.
5. A moderator approves it; it becomes a low-reliability evidence source with
   attribution.
6. A re-fit is triggered through the orchestrator; scheduled jobs refresh source data, but model fitting is an explicit workflow.
7. A reviewer reads the auto-drafted decision record and approves or rejects a
   confidence promotion. Only on approval does displayed confidence rise.

### system_overview
An event-driven spine (AWS Step Functions) runs ingest, covariate, fit, gate,
decision-record, and human-promotion stages. A read API serves the forecast,
gate status, and provenance. A Vercel Next.js front end renders the map,
overlay, gate dashboard, moderation queue, and provenance drill-down. Storage is
DynamoDB for entities and S3 (NDJSON) for time series and fitted coefficients.

### agent_architecture
Reasoning components coordinated as a DAG, with no chat surface:
- Source adapters (`src/aws_backend/sources/*`): fetch, normalize, assign
  reliability, emit `SourceEvidence`.
- Ingestion orchestrator (`state.run_ingestion`): merge into normalized
  sightings with provenance and `IngestionRun` records.
- Covariate engine (`covariates.py`, `modeling/tide_phase.py`): ephemeris and
  tidal phase.
- Kernel estimator (`modeling/estimator.py`): joint Poisson-GLM (LNP) with
  station effects and an effort offset.
- Validation-gate referee (`modeling/validation/*`): time-rescaling GOF,
  time-blocked CV, phase-shuffle null, PIT calibration; emits confidence.
- Promotion supervisor (AWS Bedrock, structured output): drafts a promote/hold
  decision record citing gate evidence; a human makes the final call.
- Forecaster (`src/aws_backend/kernel_model/serve.py`): approved coefficients to
  `lambda(x,t)`.

### human_oversight_model
- Moderation gate: community sightings quarantined until a human approves
  (attribution + low reliability weight). Already built end to end.
- Promotion gate: automated gates are necessary but not sufficient; a reviewer
  must approve a confidence promotion, with the supervisor's draft and raw gate
  numbers in front of them. Rejections are recorded with reasons.

### observability_strategy
Step Functions execution history (per-stage status, retries, timings),
CloudWatch logs and metrics (ingestion volume, fit duration, gate pass rates),
the system's own `IngestionRun` / `SourceStatus` records and
`docs/methodology/KERNEL_FIT_STATUS.md`, and a front-end status page over
`/api/data-status` and `/api/gates`.

### traceability_strategy
The hero. Every normalized sighting carries `SourceEvidence` (source,
reliability, raw S3 pointer, ingestion-run id). Every fit writes
`fitted_kernels.json` + `fit_report.json` with the gate record, confidence,
covariates, and data spans (including disclosures such as "currents do not
overlap acoustics, tide kernel is null"). Every promotion writes an immutable
decision record. The UI drill-down goes cell -> kernels -> gates -> raw
detections; no surface element exists without a back-link.

### data_sources
OrcaHello acoustic detections (the spike train), OBIS and iNaturalist visual
sightings, NOAA CO-OPS tides/currents, salmon run-timing index, ETOPO1
bathymetry, moderated community submissions.

### aws_services
App Runner (API), Step Functions (spine), Lambda (stage workers, scheduled
refresh), EventBridge (cron), DynamoDB (sightings, hotspots, reports,
ingestion-runs, community, decision-records), S3 (raw payloads, reports,
time-series NDJSON, fitted coefficients), ECR, Bedrock (promotion supervisor),
CloudWatch, IAM.

### vercel_components
Next.js App Router app (forecast map, instrument overlay, gate dashboard,
moderation queue, provenance drill-down), Vercel serverless/edge functions as
the read-API proxy and auth boundary, ISR for cached forecast snapshots,
optional Vercel Cron to poke the refresh endpoint, optional Vercel KV for
reviewer session state.

### demo_scenario
About 3 minutes, live: show the always-on low-confidence forecast and its inline
confidence, open the instrument overlay, tap a cell for the provenance trace,
open the gate dashboard (lunar beats its null, CV passes by fold majority but
mean skill is negative, PIT calibrates under the negative-binomial model, and
time-rescaling fails honestly), submit a shore sighting, approve it in
moderation, trigger the Step Functions re-fit, watch gates update, read the
Bedrock decision record, and approve a promotion so the forecast sharpens with a
full audit trail.

### three_day_build_plan
- Day 1 (spine and surface): wrap existing ingestion + `modeling/fit_kernels.py`
  in a Step Functions state machine; expose `/api/gates`, `/api/provenance`,
  `/api/decision-records`; stand up the Next.js app on Vercel reading the live
  API; render the forecast map and instrument overlay.
- Day 2 (provenance and gates): build the cell drill-down, the gate dashboard
  from `fit_report.json`, and the moderation dashboard over the community
  endpoints; add the Bedrock promotion supervisor.
- Day 3 (human-in-the-loop and polish): build the promotion approval UI writing
  immutable decision records; wire CloudWatch and Step Functions views into an
  observability page; rehearse and record the demo; freeze scope.

### future_expansion_path
Level 3 (salmon + spatial habitat for a full `lambda(x,t)` field) and Level 4
(population decoding across stations); fix overdispersion with a negative-binomial
or AR(1) term (the real run shows acoustic bouts violate Poisson); onboard more
acoustic stations and an overlapping current series; learn an acoustic-to-visual
encounter bridge; partner data sharing with per-source licenses.

## Implementation outline

Reuse, do not rebuild: backend, ingestion, storage, scheduling, the full kernel
pipeline, and the community moderation queue already exist. Fitted coefficients
and the gate report already generate.

Net-new for the hackathon (bounded):
1. Step Functions definition: `infra/aws/stepfunctions/forecast_orchestrator.asl.json`
   (done as a stub), each Task a thin Lambda over existing functions.
2. Read endpoints `/api/gates`, `/api/provenance`, `/api/decision-records`
   (done as a stub: `src/aws_backend/routers/kernel.py`).
3. Bedrock supervisor `src/aws_backend/promotion/supervisor.py`: structured in,
   structured out, deterministic fallback.
4. Promotion write path + DynamoDB `decision-records` table (stub keeps records
   in-process today).
5. Vercel Next.js app `web/` with four views.

## Risk assessment

- Data sparsity is real and visible (one acoustic station, ~7.5 months, gates
  mostly fail). Mitigation: make honesty the feature; the demo shows the system
  declining to oversell, which is the differentiator.
- Build-window scope: every stage wraps an existing tested function; if Bedrock
  slips, the supervisor degrades to a deterministic rule with the same output.
- Bedrock latency/access: keep it off the request path (orchestration stage
  only).
- Google Maps billing/referrers (a prior failure mode): pre-verify before demo.
- Provenance sprawl: bound to one cell -> kernels -> gates -> detections path.
- Two clouds in one demo: rehearse the Vercel-to-AWS path early; cache a forecast
  snapshot via ISR so the demo survives a backend hiccup.

## Evaluation scorecard
- novelty: high (gate-governed, human-promoted confidence with end-to-end
  provenance).
- feasibility: high (most components exist and are tested).
- differentiation: high (anti-chatbot, provenance-first, honesty-by-construction).
- ecosystem_fit: strong on both clouds.
- long_term_value: high (it is the real research roadmap, Levels 3 to 4).
