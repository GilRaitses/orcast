# ORCAST Review Dossier Schema

## Purpose

A review dossier is the evidence packet a reviewer should inspect before promoting, holding, or rejecting a forecast confidence update. It joins the fit, gates, caveats, raw evidence references, supervisor recommendation, human decision, and audit metadata into one inspectable artifact.

The v1 format is native JSON. It borrows structure from model cards, dataset datasheets, PROV-lite, workflow-run manifests, and investment committee memos without requiring RDF, BagIt, or full RO-Crate packaging.

## ReviewDossierV1

```yaml
ReviewDossierV1:
  dossier_id: string
  schema_version: "orcast/review_dossier/v1"
  workflow_stage: awaiting_human | decided | promoted | held
  created_at: datetime

  provenance:
    snap_id: string | null
    repr_id: string | null
    run_id: string | null
    fit_plan_id: string | null
    dec_id: string | null
    f_map_id: string | null
    kernel_version: string | null
    artifact_refs:
      fit_plan: uri | null
      snapshot_manifest: uri | null
      fit_report: uri
      fitted_kernels: uri
      representation: uri | null
      run_manifest: uri | null
      promotion: uri | null
      pending_approval: uri | null

  model_card:
    model_name: string
    model_family: string
    intended_use: string
    out_of_scope_use: string[]
    pilot_region: string
    modeled_dimensions: string[]
    unmodeled_dimensions: string[]
    covariates_fit: string[]
    covariates_excluded: object
    metrics: object
    confidence_raw: number
    confidence_effective: number | null
    promoted: boolean
    caveats: string[]

  gate_decision:
    data_inventory: object
    gates:
      level1_psth: object
      cross_validation: object
      time_rescaling: object
      pit: object
      consistency: object
    gate_pass_eligible: boolean
    configured_threshold: number
    recommendation_basis: string[]

  supervisor_recommendation:
    recommendation: promote | hold
    rationale: string
    cited_gates: string[]
    gates_summary: object
    source: deterministic | bedrock
    generated_at: datetime

  human_decision:
    id: string
    dec_id: string | null
    verdict: promote | hold | reject
    reviewer_id: string
    reviewer_email: string
    reviewer_role: string
    reason: string
    thesis_summary: string | null
    risk_items: RiskItem[]
    conditions: Condition[]
    dissent_notes: string | null
    created_at: datetime

  provenance_sample:
    cell:
      lat: number
      lng: number
      when: datetime | null
    kernel_contributions: object[]
    nearby_sample: object[]
    source_evidence_refs: object[]

  prov:
    entities: ProvEntity[]
    activities: ProvActivity[]
    agents: ProvAgent[]
    edges: ProvEdge[]

  source_sheets:
    - source: string
      reliability: number | null
      license: string | null
      collection_process: string
      limitations: string[]
      maintenance: string | null

  replay:
    replay_check_uri: uri | null
    replay_status: not_run | pass | fail
    replay_checked_at: datetime | null
```

## Supporting Types

```yaml
RiskItem:
  risk_id: string
  severity: low | medium | high
  description: string
  mitigation: string | null
  accepted: boolean

Condition:
  condition_id: string
  description: string
  due_at: datetime | null
  owner: string | null
  status: open | satisfied | waived

ProvEntity:
  id: string
  type: Dataset | Representation | Run | GateDecision | HumanDecision | Promotion | ForecastCell | SourceRecord
  label: string
  uri: uri | null
  sha256: string | null

ProvActivity:
  id: string
  type: FreezeSnapshot | FitModel | EvaluateGates | DraftRecommendation | Review | ApplyPromotion | ReplayCheck
  started_at: datetime | null
  ended_at: datetime | null

ProvAgent:
  id: string
  type: System | Reviewer | Supervisor | SourceAdapter
  label: string

ProvEdge:
  subject: string
  predicate: used | wasGeneratedBy | wasAttributedTo | wasDerivedFrom | reviewed | promoted
  object: string
```

## Minimum Demo-Critical Dossier

The first implementation can omit content-addressed IDs while still improving review quality. Minimum fields:

- `dossier_id`
- `kernel_version`
- `fit_report` URI
- `fitted_kernels` URI
- `model_card.status`, `confidence_raw`, `confidence_effective`, `promoted`, `caveats`
- `gate_decision.gates`
- `supervisor_recommendation`
- `human_decision.verdict`, `reviewer_email`, `reason`, `created_at`
- `prov.edges` for fit report, decision record, and promotion marker

## Required Security Rules

- Never expose `task_token` in public dossier output.
- Public dossiers may include redacted gate and caveat evidence, but reviewer identity and moderation PII require WorkOS authorization.
- Backend must stamp reviewer identity from WorkOS or trusted proxy headers. The browser should not choose `reviewer_email`.
- Backend must stamp gate summaries, fit identity, and promotion metadata server-side.

## AuditPacketExportV1

```yaml
AuditPacketExportV1:
  export_version: "1"
  export_type: audit_packet
  exported_at: datetime
  exported_by: string | null

  manifest:
    context: "orcast/audit/v1"
    has_part:
      - id: string
        uri: uri
        sha256: string | null
        media_type: string

  dossiers: ReviewDossierV1[]
  decision_records: object[]
  promotion_markers: object[]
  prov_graph:
    entities: ProvEntity[]
    activities: ProvActivity[]
    agents: ProvAgent[]
    edges: ProvEdge[]
  replay_status:
    run_id: string | null
    replay_check_passed: boolean | null
    replay_check_at: datetime | null
  integrity:
    content_hashes: object
    git_sha: string | null
    dependency_hash: string | null
```

## Reviewer Workflow

1. Reviewer opens `/gates` or `/review-dossier/latest`.
2. System assembles dossier from fit report, fitted kernels, caveats, supervisor recommendation, pending approval, and decision history.
3. Reviewer reads the model card, gates, caveats, source evidence, and supervisor memo.
4. Reviewer records `promote`, `hold`, or `reject` with rationale, risks, conditions, and dissent notes if needed.
5. Backend stamps reviewer identity and immutable decision metadata.
6. Promotion apply verifies the decision record and writes a promotion marker linked to `decision_id`.
7. Audit export includes the dossier and provenance graph.
