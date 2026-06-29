# ORCAST Research Workflow Implementation Waves

**Waves registry:** [WAVES_REGISTRY.md](WAVES_REGISTRY.md) (canonical IDs I0–I7).

This plan converts the research workflow alignment target into implementation waves.

## Implementation Priorities

1. Demo-critical truth and audit fixes.
2. Research-critical provenance and replay.
3. Dossier UX and governance expansion.
4. Diagram and methodology synchronization.

## Wave I0 - Safety And Truth Fixes

Goal: remove misleading or unsafe workflow gaps before deeper architecture work.

Tasks:

- Redact task tokens and pending approval internals from public `/api/gates`.
- Fix `psth_vs_kernel_diagnostic` / `consistency` field mismatch in the gates API.
- Update gates and forecast copy so unpromoted confidence is described consistently with code.
- Add real-data caveats everywhere confidence is surfaced: unreviewed detections, single station, tide non-overlap, continuous effort assumption, negative/marginal CV skill.
- Update stale methodology/demo docs that still imply nothing is fitted or that re-fit runs automatically on a schedule.
- Decide and document the authoritative demo surface: Vercel H0 app vs legacy Angular/CloudFront.

Verification:

- `/api/gates` public response contains no `task_token`.
- Gates UI shows the PSTH-vs-kernel diagnostic or intentionally labels it unavailable.
- Docs match current `fit_report.json` state.

## Wave I1 - Identity Binding And Audit Visibility

Goal: make human decisions attributable and inspectable.

Tasks:

- Forward WorkOS user identity from the Vercel proxy to backend as trusted server-side headers.
- Stamp `reviewer_id`, `reviewer_email`, and `reviewer_role` server-side on `DecisionRecord`.
- Stop accepting browser-selected reviewer identity.
- Add `/decisions` read-only UI for authenticated reviewers.
- Add `hold` as an explicit reviewer action in the gates UI.
- Server-stamp supervisor recommendation from pending approval state instead of trusting client body.
- Link `promotion.json` to `decision_id`, `kernel_version`, and later `run_id` / `repr_id`.
- Add immutable moderation audit fields or `ModerationRecord` for community approve/reject actions.

Verification:

- A reviewer decision shows the signed-in WorkOS identity.
- A promotion marker resolves to exactly one decision record.
- Moderation actions show who reviewed, when, and why.

## Wave I2 - Fit Plan And Frozen Snapshot

Goal: make every fit reproducible at the input level.

Tasks:

- Add `fit_plan.json` generation before fit starts.
- Add `snapshot_manifest.json` generation before `run_fit`.
- Freeze input objects by copying or version-pinning S3 NDJSON partitions.
- Add `dataset_snapshot_id`, `fit_plan_id`, `data_window`, and input hashes to `fit_report.json`.
- Include contributing `ingest_run_ids`.
- Update Step Functions with a `FreezeSnapshot` stage before `FitAndGate`.

Verification:

- A fit report points to a frozen snapshot manifest.
- Re-hashing the snapshot manifest yields the same `snap_id`.
- Fit code can read from frozen snapshot inputs, not live streams.

## Wave I3 - Versioned Representations And Run Manifests

Goal: stop overwriting scientific evidence and introduce DecisionDB-style IDs.

Tasks:

- Generate `repr_id` from representation and coefficient content.
- Generate `run_id` from run manifest content.
- Write artifacts to versioned S3 keys:
  - `representations/{repr_id}/fitted_kernels.json`
  - `representations/{repr_id}/representation.json`
  - `runs/{run_id}/fit_report.json`
  - `runs/{run_id}/manifest.json`
- Add `models/current.json` as a pointer for serve compatibility.
- Switch `serve.py` to resolve current model through `models/current.json`.
- Add `snap_id`, `repr_id`, `run_id`, and artifact URIs to `/api/gates`.

Verification:

- A new fit does not overwrite prior representation/run artifacts.
- Serving still works through the current pointer.
- Gates and provenance show stable fit identity.

## Wave I4 - Review Dossier API And Export

Goal: let a reviewer inspect one packet instead of stitching evidence manually.

Tasks:

- Implement `GET /api/review-dossier/latest`.
- Implement `GET /api/review-dossier/{dossier_id}`.
- Implement `GET /api/review-dossier/{dossier_id}/export`.
- Assemble `ReviewDossierV1` from fit report, fitted kernels, caveats, supervisor recommendation, decision records, promotion marker, and provenance sample.
- Add `AuditPacketExportV1` JSON export.
- Add PROV-lite edges for fit, gate, review, promotion, and replay.
- Add source datasheet references for each evidence source.

Verification:

- A dossier answers: data, model, gates, reviewer, decision, replay status.
- Export strips task tokens and PII unless authenticated.
- Export validates against the documented schema.

## Wave I5 - Modeling Rigor

Goal: align scientific gates with the research methodology.

Tasks:

- Add Level 0 detector characterization artifact.
- Add held-out time-rescaling, or clearly keep current time-rescaling labeled in-sample.
- Add single-covariate, persistence, and recent-density baselines.
- Tighten confidence semantics so negative mean skill cannot look like a clean pass.
- Improve station uptime exposure handling.
- Add visual-sighting held-out validation path when data coverage supports it.

Verification:

- Fit report separates in-sample diagnostics from held-out gates.
- Baseline scorecard is visible in `/api/gates`.
- Confidence can be explained from gate components without ambiguity.

## Wave I6 - Dossier UX

Goal: make the review workflow visible in the app.

Tasks:

- Add `/review-dossier/latest` page.
- Add `/decisions` page.
- Add a promotion breadcrumb: `fit -> gates -> decision -> promotion`.
- Add source/evidence drill-down links in `ProvenanceModal`.
- Add downloadable audit packet button.
- Show truth labels for partially live or conceptual workflow pieces where needed.

Verification:

- A reviewer can navigate from map cell to gates, evidence, decision, and audit export without AWS console access.
- Demo path can be completed with no manual curl commands.

## Wave I7 - Diagram And Documentation Sync

Goal: make the diagrams and docs match implementation truth.

Tasks:

- Update `orcast-erd-workflows.drawio` after IDs, manifests, and dossier APIs are live.
- Add fit plan, snapshot manifest, run manifest, dossier, and audit export artifacts to diagrams.
- Mark any remaining conceptual DecisionDB pieces as conceptual.
- Update `FORECAST_KERNELS.md`, `CALIBRATION_STUDIES.md`, and Devpost docs to reference the target workflow.
- Add generated or manual model-card-lite and source-datasheet-lite docs.

Verification:

- Diagram truth table no longer lists implemented artifacts as planned.
- Visual exports are re-rendered and checked after diagram updates.
- Docs do not contradict current fit artifacts.

## Suggested First Sprint

The first practical sprint should do Waves I0 and I1:

1. Token redaction.
2. Gates consistency alias.
3. WorkOS reviewer identity stamping.
4. Decision audit UI.
5. Promotion marker linked to decision record.
6. Stale docs/copy cleanup.

This gives immediate demo credibility while preparing the path for the research-critical snapshot/run-manifest work.

## Status snapshot (2026-06-22)

| Wave | Status | Notes |
|------|--------|-------|
| I0 | live | Gates redaction, caveats, H0 as demo surface |
| I1 | live | Journal, WorkOS/agent auth, hold action, moderation audit, promotion→decision |
| I2 | partial | `snapshot_manifest.json` + `frozen_data` pin + ASL `snap_id` wire |
| I3 | partial | `repr_id` / `run_id` in fit_report; versioned S3 keys in fit_kernels |
| I4 | live | Review dossier + export with PII redaction; unredacted needs signed-in |
| I5 | partial | Level 0 QC fields + standalone artifact on fit write |
| I6 | partially live | H0 UX pages live; partner `/api/v1` deployed on Vercel with rate limits |
| I7 | partial | Truth table + architecture.mmd updated; drawio re-export pending |

See [workflow-truth-table.md](workflow-truth-table.md) for route-level truth labels.
