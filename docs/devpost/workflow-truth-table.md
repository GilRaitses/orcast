# orcast workflow truth table

Labels:

- `live`: implemented and represented truthfully in current code or artifacts.
- `partially live`: implemented in part, conditional, manually triggered, or not fully connected.
- `planned`: documented or diagrammed as a target, but not implemented.
- `conceptual`: research framing without an operational contract.

## Diagram page truth labels

| Page | Component | Truth label | Evidence | Notes |
| --- | --- | --- | --- | --- |
| Page 1 | DynamoDB nine-table primary store | live | `infra/aws/template.yaml`, `src/aws_backend/storage.py`, `src/aws_backend/journal/store.py`, `src/aws_backend/casting/registry.py` | sightings, community-submissions, decision-records, user-journal, hotspots, reports, ingestion-runs, partner-api-keys, managed-agents. |
| Page 1 | `user-journal` → publish → `community-submissions` | live | `src/aws_backend/routers/journal.py`, ERD page 1 | WorkOS-scoped journal; publish copies to moderation queue. |
| Page 1 | Logical references between tables | partially live | `docs/devpost/figures/orcast-erd-workflows.drawio` | App-level references only; no enforced FK constraints. |
| Page 1 | `decision-records.kernel_version` → fitted-kernel artifact | partially live | `src/aws_backend/routers/kernel.py`, `modeling/fit_kernels.py` | New fits use `repr_id`; promotion marker links `decision_id` and `run_id` on promote. |
| Page 1 | `reports.hotspots[]` as denormalized embed | live | diagram page 1 | Snapshot embed rather than live composition. |
| Page 1 | Embedded `SourceEvidence` and raw refs | live | `src/aws_backend/models.py`, `src/aws_backend/storage.py` | Raw refs exist; full replay manifest remains future work. |
| Page 1 | Full DecisionDB-style f_map | conceptual | page 5 gap note | Decision records and promotion markers partially materialize the chain. |
| Page 2 | External adapters and normalized sightings | live | `src/aws_backend/sources/*`, `src/aws_backend/storage.py` | Adapters and storage paths exist. |
| Page 2 | S3 raw payloads and time-series NDJSON | partially live | time-series and raw payload code | Fits emit `snapshot_manifest.json`; full S3 version-pinned freeze is R1 future work. |
| Page 2 | `BathymetryAdapter` as static local data | live | diagram page 2 | Static read. |
| Page 2 | Separate reports bucket | live | `ORCAST_REPORTS_BUCKET`, storage code | Report bodies and metadata are split. |
| Page 2 | Fit container Lambda reads time-series and writes models | partially live | `modeling/lambda_handler.py`, `infra/aws/template.yaml` | Code/IaC exist; production depends on fit image deployment. |
| Page 2 | Versioned model/run artifact store | partially live | `modeling/fit_kernels.py`, `src/aws_backend/kernel_model/serve.py` | `representations/{repr_id}`, `runs/{run_id}`, `models/current.json`. |
| Page 3 | Scheduled ingestion and report refresh | live | `infra/aws/template.yaml` | EventBridge rules call App Runner endpoints. |
| Page 3 | Step Functions forecast orchestrator | partially live | `infra/aws/stepfunctions/forecast_orchestrator.asl.json` | Defined and triggerable. |
| Page 3 | FitAndGate retry/catch to hold | planned | diagram vs ASL | Retry exists in ASL; catch-to-hold needs code or relabel. |
| Page 3 | Human waitForTaskToken promotion loop | partially live | ASL, `src/aws_backend/routers/kernel.py` | Depends on pending approval state and token handling. |
| Page 3 | Manual `/api/decision-records` reviewer path | live | `tests/aws_backend/test_decision_records.py` | promote / hold / reject; server-stamps gates. |
| Page 3 | Reviewer identity from WorkOS | partially live | `web/app/api/be/[...path]/route.ts`, `src/aws_backend/auth.py` | Trusted proxy + `require_trusted_reviewer`; direct App Runner API key cannot govern alone. |
| Page 3 | Automation agent key (`ORCAST_AGENT_KEY`) | live | `web/lib/agentAuth.ts`, `web/app/api/be/[...path]/route.ts`, `web/app/components/AuthStatus.tsx`, `tools/testing/agent_smoke.py` | Server-side only; Playwright injects header; nav shows automation chip when valid. |
| Page 4 | Vercel proxy with public GET allow-list | live | `web/app/api/be/[...path]/route.ts` | Public reads; protected mutations require session or agent key. |
| Page 4 | WorkOS hosted AuthKit redirect | live | `web/middleware.ts`, auth routes | Requires Vercel env vars. |
| Page 4 | Server-side API key injection | live | `web/app/api/be/[...path]/route.ts` | Browser does not see backend key. |
| Page 4 | `/ask` sighting check (Bedrock Haiku) | live | `src/aws_backend/routers/sighting_assist.py`, `web/app/ask/` | Template fallback if Bedrock unavailable. |
| Page 4 | `/journal` field journal UI | live | `web/app/journal/`, `src/aws_backend/routers/journal.py` | Auth required via proxy. |
| Page 4 | Partner API gateway (`/api/v1`) | partially live | `web/app/api/v1/`, `docs/devpost/API_AGENTS.md` | Hashed-key verify + gateway rate limits; deploy + `ORCAST_PARTNER_DEV_KEY` required. |
| Page 4 | `/api/gates` / `serve.py` reads `models/*` | live | `src/aws_backend/kernel_model/serve.py` | `models/current.json` with fixed-key fallback. |
| Page 4 | Pending approval public shape | live | `src/aws_backend/routers/kernel.py` | Task tokens stay server-side. |
| Page 5 | DecisionDB conceptual mapping | live as diagram | `docs/devpost/figures/orcast-erd-workflows-page5.png` | Conceptual mapping and gaps stated. |
| Page 5 | `snap_id` frozen snapshot | partially live | `modeling/fit_kernels.py` | Manifest + `frozen_data` pin; fit reads snapshot when `dataset_snapshot_id` passed. |
| Page 5 | `repr_id` content-addressed representation | partially live | `modeling/fit_kernels.py`, `serve.py` | Content-addressed artifacts + current pointer. |
| Page 5 | `run_id` engine run manifest | partially live | `modeling/fit_kernels.py` | Run manifest emitted; replay check future work. |
| Page 5 | `dec_id` gate/human decision identity | partially live | `DecisionRecord.id` | UUID decisions; promotion links `decision_id`. |
| Page 5 | Materialized f_map table | conceptual | page 5 gap note | Future research-grade provenance layer. |

## Cross-cutting truth labels

| Workflow claim | Truth label | Required correction |
| --- | --- | --- |
| orcast has an auditable human promotion log | live | `/decisions` and `GET /api/decision-records`. |
| orcast has research-grade replay | partially live | Snapshot/run manifests exist; full replay check remains future work. |
| orcast has WorkOS-bound reviewer identity | partially live | Vercel proxy stamps identity; backend requires trusted proxy in production. |
| orcast has transparent integrity conditions | live | Gates, provenance, dossier, sighting-assist use server-derived conditions. |
| orcast has a scientific validation pipeline | partially live | L1/L2 live; Level 0 QC partial; L3–L5 planned. |
| orcast has immutable moderation audit trail | partially live | Submission fields + 409 + DDB conditional; append-only `ModerationRecord` table deferred. |
| orcast has investment-committee style review | partially live | Dossier, decision log, supervisor memo exist; quorum/dissent future. |
| External agents can query forecast intelligence | partially live | `API_AGENTS.md`, partner verify route, `tools/partner-cli/`; deploy pending. |

## Diagram update rule

- Solid boxes for `live`.
- Dashed boxes for `partially live`, `planned`, `conceptual`.
- Show `snap_id`, `repr_id`, `run_id` as partially live until full frozen S3 pin and replay checks exist.
