# Adversarial probe playbook

Readonly multi-wave hostile review for orcast. Canonical wave IDs: [WAVES_REGISTRY.md](WAVES_REGISTRY.md).

**Rule:** probe subagents are `readonly`. Fix agents run only after the parent runs a gate and assigns write lanes.

## Gate rules

| Severity | Action before next wave |
|----------|-------------------------|
| **P0** | Auth bypass, secret leak, public PII — **stop**; remediation wave required |
| **P1** | Doc lies, misleading UI, ghost endpoints — fix or downgrade [workflow-truth-table.md](workflow-truth-table.md) |
| **P2** | Backlog or next probe wave |

After P1 panels complete, parent runs:

```bash
./tools/waves/run-gate.sh P1-gate
```

No open P0 findings → may launch implement waves or P2.

## P0 — Deconflict (coordinator only)

Before launching parallel panels:

1. Confirm authoritative URLs in [HANDOFF_STATUS.md](../../HANDOFF_STATUS.md) (Vercel H0 primary).
2. Update [workflow-truth-table.md](workflow-truth-table.md) if implementation changed.
3. Confirm [LANE_OWNERSHIP.md](../../infra/aws/state/LANE_OWNERSHIP.md) has no overlapping write paths.
4. Exclude `archive/quarantine/**` unless explicitly assigned.

**Output:** short lane table + list of live URLs to curl.

## P1 — Surface probes (six parallel panels)

Launch all six in one parent turn. Each panel is read-only.

### Panel prompt template

```text
Full Repository Path: /Users/gilraitses/orcast
Mode: READ-ONLY adversarial probe — do not fix anything

Lane: [P1-X]
Scope (only these paths): [glob list]
Live URLs to curl: [from HANDOFF_STATUS.md]

Adversarial question: [one sharp question]

Deliver:
1. Findings table: severity (P0/P1/P2), evidence (file:line or curl output), exploit story
2. Doc vs code mismatches (cite doc path)
3. Tweet quote — what a hostile reviewer would post in one sentence
4. False positives you rejected

Use the alignment charter output sections where applicable:
- Scope, Current State, Truth Table Rows, Gaps, Recommended Artifacts, Priority Map

Do NOT read outside scope except imports needed to understand scope.
```

### P1-A — H0 auth

| Field | Value |
|-------|--------|
| Scope | `web/app/api/be/`, `web/middleware.ts`, `src/aws_backend/auth.py`, `src/aws_backend/routers/community.py`, `src/aws_backend/routers/kernel.py` |
| Live URLs | `https://orcast-h0.vercel.app` |
| Question | Can I approve moderation or write decision records without a real WorkOS reviewer? |

### P1-B — API truth

| Field | Value |
|-------|--------|
| Scope | `src/aws_backend/routers/`, `docs/API.md`, `docs/devpost/API_AGENTS.md`, active docs only (`!archive/**`) |
| Live URLs | `https://pjrftm3bkv.us-west-2.awsapprunner.com` |
| Question | Which documented endpoints 404, leak tokens, or overclaim "live"? |

### P1-C — CloudFront pilot

| Field | Value |
|-------|--------|
| Scope | Live `https://d2gslju5drx74c.cloudfront.net` + `orcast-angular/src/app/` routed pages only |
| Question | What stale copy, broken maps, or fake "live API" labels survive on CloudFront? |

### P1-D — Gates honesty

| Field | Value |
|-------|--------|
| Scope | `modeling/fit_kernels.py`, `src/aws_backend/kernel_model/serve.py`, `web/app/gates/`, `data/models/fit_report.json` |
| Live URLs | `/api/gates` on App Runner and via Vercel proxy |
| Question | Where does UI confidence exceed what gates actually passed? |

### P1-E — Partner surface

| Field | Value |
|-------|--------|
| Scope | `web/app/api/v1/`, `src/aws_backend/routers/partner.py`, `docs/devpost/API_AGENTS.md` |
| Live URLs | `https://orcast-h0.vercel.app/api/v1` |
| Question | Can I impersonate a partner, brute keys, or bypass rate limits? |

### P1-F — Provenance and audit

| Field | Value |
|-------|--------|
| Scope | `src/aws_backend/routers/review_dossier.py`, `promotion/`, `storage.py`, `web/app/moderation/`, `web/app/review-dossier/` |
| Question | Can I export PII, double-approve moderation, or promote without audit trail? |

### P1 parent synthesis

Merge panel outputs into `docs/devpost/adversarial-findings-YYYY-MM-DD.md`:

1. Dedupe by root cause.
2. Sort P0 → P1 → P2.
3. Map each finding to a wave ID (R-*, I-*, truth-table row).
4. Run `./tools/waves/run-gate.sh P1-gate`.

## P2 — Deep probes (after P1 gate)

Run sequentially or as four parallel panels:

| Panel | Scope | Question |
|-------|--------|----------|
| P2-A | `modeling/`, ASL, `lambda_handler.py` | Does `dataset_snapshot_id` flow end-to-end or still read live streams? |
| P2-B | `infra/aws/stepfunctions/`, `template.yaml` | Does ASL match deployed ARNs and diagram page 3? |
| P2-C | schedulers, ingest, billing docs | Empty ingest, cost footguns, silent failures? |
| P2-D | `SUBMISSION.md`, `DEVPOST_DRAFT.md`, figures, truth table | Devpost pack vs implementation truth? |

## P3 — Diff review

After remediation branch is ready:

1. Launch `bugbot` subagent on branch diff (readonly).
2. Launch `security-review` subagent on branch diff (readonly).
3. Parent resolves P0/P1 from both before merge/deploy.

## Agent output template (from alignment charter)

Each probe panel must return:

1. **Scope** — files and workflow components reviewed.
2. **Current state** — what orcast does today in this lane.
3. **Truth table rows** — component, label (`live` / `partially live` / `planned` / `conceptual`), evidence path, rationale.
4. **Gaps** — ranked P0/P1/P2.
5. **Recommended artifacts** — APIs, fields, UI, S3 manifests, docs, diagram updates.
6. **Priority map** — demo-critical / research-critical / nice-to-have.
7. **Tweet quote** — one-sentence hostile summary (P1 panels only).

Truth labels: see [research-workflow-alignment-charter.md](research-workflow-alignment-charter.md).

## Pre-Devpost checklist (probe-derived)

- [ ] P1 panels run; dossier filed
- [ ] `./tools/waves/run-gate.sh P1-gate` green
- [ ] No open P0
- [ ] P1 either fixed or truth-table downgraded
- [ ] `./tools/waves/run-gate.sh H0` green
- [ ] H1 manual items in [HACKATHON_SUBMIT_CHECKLIST.md](HACKATHON_SUBMIT_CHECKLIST.md)
