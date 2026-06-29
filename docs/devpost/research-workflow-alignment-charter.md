# ORCAST Research Workflow Alignment Charter

**Waves registry:** [WAVES_REGISTRY.md](WAVES_REGISTRY.md) · **Probe playbook:** [ADVERSARIAL_PROBE_PLAYBOOK.md](ADVERSARIAL_PROBE_PLAYBOOK.md)

## Purpose

This charter guides the research workflow alignment wave set. The goal is to test the workflow shown in `docs/devpost/figures/orcast-erd-workflows.drawio` against research-grade provenance, scientific validation, and due-diligence governance standards, then turn the findings into implementation-ready changes.

## Evidence Sources

Agents should ground findings in the repository wherever possible:

- Workflow diagrams: `docs/devpost/figures/orcast-erd-workflows.drawio` and `docs/devpost/figures/orcast-erd-workflows-page*.png`
- Diagram style and reference mapping: `docs/devpost/figures/_pages/STYLE_SPEC.md`, `docs/devpost/figures/_ref/decisiondb-fig2.png`
- Modeling workflow: `modeling/fit_kernels.py`, `docs/methodology/FORECAST_KERNELS.md`, `docs/methodology/CALIBRATION_STUDIES.md`
- Backend workflow: `src/aws_backend/models.py`, `src/aws_backend/storage.py`, `src/aws_backend/routers/*.py`, `src/aws_backend/promotion/supervisor.py`, `src/aws_backend/kernel_model/serve.py`
- Orchestration and infra: `infra/aws/stepfunctions/forecast_orchestrator.asl.json`, `infra/aws/template.yaml`
- Frontend workflow: `web/app/gates/page.tsx`, `web/app/moderation/page.tsx`, `web/app/api/be/[...path]/route.ts`, `web/middleware.ts`
- Demo/submission framing: `docs/devpost/README.md`, `docs/devpost/SUBMISSION.md`, `docs/devpost/DEMO_STORYBOARD.md`, `docs/devpost/H0_ARCHITECTURE.md`

## Truth Labels

Every referenced workflow component must be labeled:

- `live`: implemented and represented truthfully in the current code or generated artifacts.
- `partially live`: implemented in part, but incomplete, conditional, manually triggered, or not fully connected.
- `planned`: documented or diagrammed as a target, but not implemented.
- `conceptual`: research framing or future architecture without an operational contract.

## Priority Labels

Every recommendation must be prioritized:

- `demo-critical`: improves judging credibility, demo clarity, or avoids misleading claims.
- `research-critical`: required for replayable, publishable, or scientifically defensible workflow integrity.
- `nice-to-have`: useful governance, UX, or operational polish that can follow after the core alignment work.

## Agent Output Template

Each probe panel agent (P1) should return:

1. `Scope`: the files and workflow components reviewed.
2. `Current State`: what ORCAST currently does.
3. `Truth Table Rows`: component, truth label, evidence path, and short rationale.
4. `Gaps`: missing or misleading parts, ranked P0/P1/P2.
5. `Recommended Artifacts`: tables, fields, APIs, UI pages, S3 manifests, docs, or diagram updates required.
6. `Priority Map`: demo-critical, research-critical, and nice-to-have recommendations.
7. `External Pattern Fit` when relevant: adopted pattern, rejected pattern, and reason.

## Alignment Lenses

- DecisionDB provenance: snapshot, representation, engine run, decision, f_map, content addressing, immutable artifacts, and replay.
- Scientific workflow: frozen datasets, fit plans, baselines, nulls, held-out validation, confidence gates, uncertainty, and caveats.
- Research governance: reproducibility, preregistration-like plans, versioned evidence, replay checks, and audit exports.
- Due-diligence governance: thesis, risk, dissent, conditions, role separation, reviewer identity, and committee-style decision memos.
- UX/workflow: reviewer ability to trace from a map cell to evidence, fit report, gate status, raw data, and decision.
- Infrastructure truth: what Step Functions, S3, DynamoDB, WorkOS, Vercel, and App Runner actually enforce today.
