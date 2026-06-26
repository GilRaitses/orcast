# Handoff Wave-Sets Charter

Date: 2026-06-25
Purpose: charter wave sets to close every remaining gap from the finalize handoff. Each wave set marks whether it is agent-addressable or operator-gated, and the loop-back condition.

Deadline context: Devpost submission June 29, 2026 5:00 PM ET.

---

## Gap inventory

| # | Gap | Owner | Wave set |
|---|-----|-------|----------|
| G1 | Vercel deploy failed (expired CLI token) | Agent | RESOLVED 2026-06-25 (token auto-refreshed; deploy READY) |
| G2 | interest endpoint 404 (App Runner pp-image health-check rollback) | Agent | Wave Set BX |
| G3 | Demo GIFs missing from galleries | Agent-assist + Operator | Wave Set MX |
| G4 | Post drafts not finalized | Agent | Wave Set PX |
| G5 | AWS DynamoDB console screenshot | Operator-only | Wave Set OX (gated) |
| G6 | Devpost submission | Operator-only | Wave Set OX (gated) |
| G7 | arXiv upload of both tarballs | Operator-only | Wave Set OX (gated) |

---

## Wave Set BX — Backend deploy remediation (interest endpoint) [AGENT]

Root symptom: `GET/POST /api/be/api/interest` returns 404. App Runner is running `ic6-20260624`; the `pp-2582240` image (which had `interest.py`) failed health checks and auto-rolled-back at 17:49. The pp image was built from a dirty working tree carrying unrelated uncommitted `src/aws_backend` changes — a likely startup-failure cause.

- **BX-1 Diagnose (parallel):** (a) pull App Runner application + deployment logs for the 17:49 rolled-back operation; identify the exact startup/health-check error. (b) static-analyze the currently-uncommitted `src/aws_backend/*.py` modifications (auth, config, geo_region, ingest_timeseries, models, routers, sources, storage) for import/startup-breaking changes. (c) attempt a local `python -c "import src.aws_backend.main"` / uvicorn boot to reproduce.
- **BX-2 Classify:** rank candidate root causes (import error, missing dep, env/config, schema mismatch, the uncommitted changes). Decide whether to commit, revert, or fix the uncommitted backend changes.
- **BX-3 Remediate:** fix the offending code. CRITICAL: build the image FROM A CLEAN COMMITTED STATE (commit or stash the dirty tree first) so the deployed image is reproducible.
- **BX-4 Deploy + verify:** ECR build + push a fresh tag; `aws apprunner update-service`; poll operation until `SUCCEEDED` (not `ROLLBACK_*`); curl `/health` (200), `/api/be/api/interest` POST (200), `/api/be/api/evidence/assets` (401), `/account` (200).
- **BX-5 Adversarial + loop:** if the operation rolls back again, return to BX-1 with the new logs. Repeat until interest endpoint is 200 and no rollback. Also check whether the CFN template pins `ic6-20260624` (if so, update the template image tag so future stack ops don't revert).

Loop exit: interest POST returns 200 and App Runner operation status is SUCCEEDED on the new image.

## Wave Set MX — Media capture (demo GIFs) [AGENT-ASSIST + OPERATOR]

Gallery placeholders ("demo coming") on the orcast homepage and aimez.ai need 4 captures.

- **MX-1 (browser subagent):** drive the live site through each flow and capture screenshots / short sequences: (1) forecast map → cell click → provenance drilldown; (2) `/explore?planner=1` routing; (3) `/ask` sighting check with evidence upload; (4) `/gates` integrity conditions + 0%.
- **MX-2:** assemble captures into GIFs (ffmpeg/static frames) and drop into the gallery `<img>` slots on both sites; rebuild/redeploy.
- **Operator fallback:** true animated 3D-behavior GIFs may need an operator screen recording where browser automation cannot reproduce the animation faithfully. MX flags any flow it cannot capture cleanly.

Loop exit: each gallery slot shows a real capture, both sites redeployed.

## Wave Set PX — Post drafts finalization [AGENT]

- **PX-1:** finalize `linkedin_post_v1.md`, `aimez_ai_post_v1.md`, `github_release_note_v1.md` against the current claim state (post prose-tightening, post source-selection). Insert capture-placeholder markers and an explicit "arXiv link pending" token.
- **PX-2:** claim-gate review of all three against `CLAIM_BOUNDARIES.md` (no overclaim; correct numbers/dates). 
- Operator posts after MX captures and arXiv IDs exist.

Loop exit: three drafts pass the claim-gate review and carry only the two known placeholders (capture, arXiv link).

## Wave Set OX — Operator-gated (NO agent wave can complete) [OPERATOR]

These require human credentials/sessions the agent does not have:
- **G5 AWS DynamoDB screenshot:** AWS Console → DynamoDB → Tables (us-west-2) → screenshot 9 tables → save to `~/Desktop/orcast-submission/figures/dynamodb-console.png`.
- **G6 Devpost:** paste `docs/devpost/DEVPOST_DRAFT.md` field-by-field, attach demo video + architecture.png + DynamoDB screenshot, set live URL, submit by Jun 29 5pm ET.
- **G7 arXiv:** upload `orcast_whitepaper1_arxiv.tar.gz` and `orcast_grounding_arxiv.tar.gz`; then backfill arXiv links into the PX drafts.

---

## Execution order recommendation

1. BX (backend) — only true technical gap; do first.
2. PX (post drafts) — quick, parallel-safe.
3. MX (captures) — needs live site stable (after BX).
4. OX (operator) — human, after BX/MX so artifacts exist.
