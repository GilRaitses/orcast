# Q — Gap register

Updated: 2026-06-25
Status: Q1 complete — 2 gaps found (both P2)

## Severity key
- **P0**: Demo or submission breaks on camera
- **P1**: Claim not demonstrable or not code-grounded
- **P2**: Minor inconsistency — accurate but suboptimal

---

## Q1a — UI/visual layer

| ID | Surface | Finding | Severity | Status |
|----|---------|---------|---------|--------|
| Q1a-01 | Gates page | integrity conditions render correctly; caveats surface (single station, unreviewed acoustic, effort assumed) | OK | closed |
| Q1a-02 | Provenance modal | `data-demo="provenance-modal"` opens on deep-link URL | OK | closed |
| Q1a-03 | Explore guide | `.cast-badge` and `.ask-layout` render on /explore | OK | closed |
| Q1a-04 | Surface planner | "Surface planner mode" banner visible on /explore?planner=1 | OK | closed |
| Q1a-05 | Sighting check | Bedrock badge ("haiku"/"claude") visible after sighting check | OK | closed |
| Q1a-06 | Moderation | Queue loads with .card items | OK | closed |
| Q1a-07 | Automation chip | "Automation" + "agent@orcast.dev" visible with agent key | OK | closed |

**Result: 0 gaps in UI/visual layer.**

---

## Q1b — API/backend layer

| ID | Endpoint | Finding | Severity | Status |
|----|---------|---------|---------|--------|
| Q1b-01 | /api/be/api/gates | Returns status + effective_confidence + caveats — all fields present | OK | closed |
| Q1b-02 | /api/be/api/hotspots | Returns 50 hotspots with probability and confidence fields | OK | closed |
| Q1b-03 | /api/be/api/sightings | Returns 113 sightings | OK | closed |
| Q1b-04 | /api/be/api/provenance | Returns effective_confidence and confidence fields | OK | closed |
| Q1b-05 | /api/interactions/status | Returns `{"status":"success"}` | OK | closed |
| Q1b-06 | Live URL | orcast-h0.vercel.app returns 200 in 1.057s | OK | closed |

**Result: 0 gaps in API/backend layer.**

---

## Q1c — Data layer (DynamoDB)

| ID | Table / check | Finding | Severity | Status |
|----|---------|---------|---------|--------|
| Q1c-01 | All 9 tables | All 9 orcast-aws-backend-* tables FOUND in us-west-2 | OK | closed |
| Q1c-02 | managed-agents count | 4 items (4 cast roles: explore-guide-v1, surface-planner-v1, dossier-explainer-v1, promotion-clerk-v1) | OK | closed |
| Q1c-03 | decision-records count | 3 items | OK | closed |
| Q1c-04 | hotspots count | 113 items | OK | closed |

**Result: 0 gaps in data layer.**

---

## Q1d — Submission copy

| ID | Claim | Finding | Severity | Status |
|----|-------|---------|---------|--------|
| Q1d-01 | AWS Lambda in Built-with | `AWS::Lambda::Function` in CloudFormation template.yaml — Lambda IS deployed | OK | closed |
| Q1d-02 | EventBridge schedule | `ScheduleExpression: rate(30 minutes)` in template.yaml — deployed | OK | closed |
| Q1d-03 | Grounding benchmark 91%/0% | Numbers in DEVPOST match benchmark run 2026-06-24 | OK | closed |
| Q1d-04 | Live URL | Returns 200 in 1.057s | OK | closed |
| Q1d-05 | gilraitses.github.io PDF links | Both whitepaper PDFs return 200 | OK | closed |
| Q1d-06 | aimez.ai link | Returns 200 | OK | closed |

**Result: 0 gaps in submission copy.**

---

## Q1e — Architecture diagram vs. deployed

| ID | Box/arrow | Finding | Severity | Status |
|----|---------|---------|---------|--------|
| Q1e-01 | "Vercel AI Gateway narration" label | `web/app/api/interactions/route.ts` uses `createGateway` from `@ai-sdk/gateway` for the **explore guide chat** endpoint, not for Central Casting narrate. The fig-08 label says "narrate" but should say "explore guide chat". The Vercel AI Gateway calls Claude (anthropic/claude-haiku-4.5) directly, not App Runner narrate. | **P2** | open — Q2 |
| Q1e-02 | RDS PostgreSQL box | `exploration/db.py` and `exploration/session_store.py` use PostgreSQL — deployed and in use | OK | closed |
| Q1e-03 | EventBridge box | `rate(30 minutes)` and `rate(1 hour)` schedules confirmed in CloudFormation | OK | closed |
| Q1e-04 | Lambda box | Multiple `AWS::Lambda::Function` confirmed in CloudFormation | OK | closed |

**Result: 1 gap (P2) — fig-08 Vercel AI Gateway label incorrect.**

---

## Q1f — Whitepaper claims vs. code

| ID | Equation | Code match | Severity | Status |
|----|---------|---------|---------|--------|
| Q1f-01 | E1 PSTH kernel | `modeling/psth.py` — FOUND | OK | closed |
| Q1f-02 | E2 phase-shuffled null | `modeling/fit_kernels.py:120` `level1_psth_phase_shuffle` gate key + `null_test` dict | OK | closed |
| Q1f-03 | E3 time-rescaling KS | `modeling/fit_kernels.py:884` `stats.kstest(pooled_arr, "expon")` | OK | closed |
| Q1f-04 | E4 effective_confidence | `src/aws_backend/routers/kernel.py:93` `def effective_confidence(...)` | OK | closed |
| Q1f-05 | E5 deviance skill | `src/aws_backend/routers/kernel.py:156` `mean_deviance_skill` | OK | closed |
| Q1f-06 | E6 PIT calibration | `modeling/fit_kernels.py:852` `stats.kstest(pit, "uniform")` | OK | closed |
| Q1f-07 | E7 C/M/X/D/R graph | ProvenanceGraph.tsx renders C (claims from annotations) and M (methods from skill_invocations). X/D/R nodes are not separately rendered as visual nodes — they appear as text refs within M rows. Whitepaper describes "C/M/X/D/R" but UI renders C/M only. | **P2** | open — Q2 |
| Q1f-08 | E8 R_uncited | `tools/testing/grounding_parallel_rag.py` — FOUND | OK | closed |

**Result: 1 gap (P2) — ProvenanceGraph renders C/M only, not the full C/M/X/D/R described in the whitepaper.**

---

## Summary

| Severity | Count | Closed |
|---------|-------|--------|
| P0 | 0 | — |
| P1 | 0 | — |
| P2 | 2 | 0 |

**No P0 or P1 gaps. Two P2 gaps — both closed in Q2:**
- Q1e-01: fig-08 Vercel AI Gateway relabeled to "explore guide chat (claude-haiku-4.5)" connecting to Bedrock. CLOSED.
- Q1f-07: Whitepaper Section 6 updated to accurately describe C/M rendered nodes and X/D/R as inline refs in step-log. CLOSED.

| Severity | Count | Closed |
|---------|-------|--------|
| P0 | 0 | — |
| P1 | 0 | — |
| P2 | 2 | 2 |

**All gaps closed. Ready for QF adversarial review.**
