# ORCAST Research Workflow Alignment

## Executive Summary

ORCAST has the right workflow shape for a gated research forecast: source evidence enters through adapters, kernels are fit and gated, confidence is capped, and a human promotion step writes an audit record. The workflow is strongest where it is explicit about uncertainty: caveats, gate dashboards, human review, and public provenance.

The remaining gap is not diagram polish. The gap is research workflow integrity: fits read mutable inputs, model artifacts overwrite fixed S3 keys, decisions are not linked to stable snapshot/run IDs, reviewer identity is not bound server-side to WorkOS, and there is no exportable review dossier.

The target is a compact research-grade workflow:

`fit_plan -> frozen_snapshot -> engine_run -> gate_decision -> review_dossier -> human_decision -> promotion -> replay_check`

## Wave 1 Findings

### P0: Demo-Critical Gaps

| Area | Current state | Gap | Artifact needed | Priority |
| --- | --- | --- | --- | --- |
| Fit input provenance | Fit reads live S3 time-series and raw payloads | No frozen `snap_id` or input manifest, so replay cannot prove same inputs | `dataset_snapshot_id`, `snapshot_manifest.json` | demo-critical, research-critical |
| Model artifact identity | `models/fitted_kernels.json` and `models/fit_report.json` are fixed overwrite keys | Prior fits can be lost; `kernel_version` is timestamp/constant rather than content identity | versioned `repr_id` / `run_id` S3 keys and manifest | demo-critical, research-critical |
| Scientific truth | Live fit has weak real-data support: one station, unreviewed detections, no tide overlap, time-rescaling fail, negative mean CV skill | UI/docs can overstate validation if this is not surfaced consistently | gate caveats, updated methodology status, stricter gate policy | demo-critical |
| API/UI consistency | Fit writes `psth_vs_kernel_diagnostic`; gates UI/API expect `consistency` | Diagnostic evidence can disappear from review surface | API field alias or schema rename | demo-critical |
| Reviewer identity | WorkOS gates proxy access and the proxy now forwards reviewer identity headers | Backend stamps reviewer id/email/role on decision records; browser-selected reviewer strings are ignored | keep this covered by decision-record tests | demo-critical, research-critical |
| Public pending approval | `/api/gates` can expose pending approval data too broadly depending on response shape | Task-token or pending state must not be public | protected pending-approval endpoint and token redaction | demo-critical |
| Promotion linkage | Human decision and `promotion.json` are separate; apply trusts client metadata | Audit cannot prove which decision authorized promotion | `decision_id`, `run_id`, `repr_id` in promotion marker | demo-critical |
| Audit visibility | `GET /api/decision-records` exists, but no UI/export | Judges/reviewers cannot inspect decision history in-app | `/decisions` page and audit export | demo-critical |

### P1: Research-Critical Gaps

| Area | Current state | Gap | Artifact needed |
| --- | --- | --- | --- |
| Fit plan | Methodology docs describe intended gates | No locked, machine-readable plan per fit | `fit_plan.json` |
| Run manifest | Fit report has status and gates | No git SHA, dependency hash, execution ARN, input hashes, output hashes | `fit_run_manifest.json` |
| DecisionDB mapping | Page 5 maps concepts | Operational IDs do not exist: `snap_id`, `repr_id`, `run_id`, `dec_id`, `f_map_id` | content-addressed ID scheme |
| Validation | L1/L2 pipeline is partially live | L0 detector QC, held-out time-rescaling, extra baselines, L3 spatial/prey remain missing | level-specific validation artifacts |
| Moderation governance | Community approvals update status | No moderator identity, reason, immutable moderation record | `ModerationRecord` |
| Dossier workflow | Gates and provenance exist separately | No single evidence packet for a reviewer | `review_dossier_schema` and dossier API |
| Replay | Pipeline can be rerun manually | No pinned snapshot replay check | `modeling/replay_check.py` or equivalent endpoint |

### P2: Nice-To-Have Gaps

| Area | Current state | Gap |
| --- | --- | --- |
| Full f_map | `decision-records` partially materializes human decisions | No full `(repr_id, run_id) -> dec_id` materialized map |
| Committee process | Single reviewer workflow | No quorum, dissent workflow, conditions, appeal/supersession chain |
| External packaging | Native JSON/S3 artifacts | No RO-Crate / PROV JSON-LD compatibility |
| UX polish | Provenance modal and gates page exist | No orchestration status page, audit packet download, map intensity layer |

## Priority Map

### Demo-Critical

- Redact task tokens and pending approval internals from public reads.
- Bind reviewer identity from WorkOS server-side.
- Add a read-only decisions/audit surface.
- Fix gates API consistency field mapping.
- Link `promotion.json` to the accepted `decision_id`.
- Update methodology and demo copy to say exactly what is live, partial, planned, or conceptual.
- Surface real-data caveats wherever confidence is shown.

### Research-Critical

- Freeze a dataset snapshot before each fit.
- Generate a fit plan before each fit and stamp it into the fit report.
- Write versioned model/run artifacts instead of overwriting fixed S3 keys.
- Add content-addressed IDs for snapshot, representation, run, and decision artifacts.
- Add a replay check against a pinned snapshot.
- Extend validation with Level 0 detector characterization, held-out time-rescaling, and stronger baselines.
- Produce a review dossier that joins fit evidence, gate results, caveats, raw evidence, reviewer identity, and final decision.

### Nice-To-Have

- Add full DecisionDB `f_map` materialization.
- Add quorum, dissent, conditions, and appeals.
- Add RO-Crate / PROV-compatible export after the native JSON audit packet exists.
- Add orchestration status and downloadable audit packet UI.

## External Pattern Fit

| Pattern | Adopt now | How ORCAST should use it |
| --- | --- | --- |
| Model Card Lite | Yes | One card per promoted kernel/model version: intended use, factors, metrics, caveats, promotion status |
| Datasheet Lite | Yes | One source sheet per data source: collection, reliability, license, maintenance, known limitations |
| W3C PROV-lite | Yes | Native JSON edge list using entity/activity/agent terms; no RDF/SPARQL now |
| Workflow Run RO-Crate-lite | Yes, native JSON first | Use the structure as an audit packet manifest in S3 |
| OSF/preregistration ideas | Yes | `fit_plan.json`: planned covariates, exclusions, gates, splits, baselines |
| Investment committee memo | Yes, compact | Add recommendation, thesis, evidence, risks, conditions, dissent, reviewer identity |
| Full RO-Crate / BagIt / PROV-O | Not yet | Too heavy until replayable native artifacts exist |

## Target Design Principle

Every promoted forecast should answer five questions without leaving the audit packet:

1. What frozen data did the model see?
2. What representation and engine produced the result?
3. What gates passed or failed?
4. Who reviewed the evidence, under what role, and with what rationale?
5. Can the package be replayed or independently inspected later?
