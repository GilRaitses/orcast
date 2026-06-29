# QF — Final adversarial review

Date: 2026-06-25
Reviewer: automated + manual
Status: **ALL PASS**

## Gate re-runs

| Gate | Result |
|------|--------|
| `a-gate` (composite: doc-grep + maps-smoke + agent-smoke + demo-walkthrough + video-gate) | **PASS** |
| `q1b-api-schema.sh` | **PASS** |
| `q1c-ddb-schema.sh` | **PASS** |
| `q1f-wp-claims.sh` | **PASS** |
| `scrutiny.spec.ts` (7 Playwright assertions) | **PASS** |

Demo video: `demo-walkthrough.webm` — 8,970,470 bytes, recorded 2026-06-25.

## Layer-by-layer adversarial verdict

### UI/visual layer
- Gates page: integrity conditions surface correctly (single station, unreviewed acoustic, effort assumed continuous, deviance skill negative). Confidence meter shows 0% (no promotion — correct).
- Provenance modal: opens via deep-link URL, renders cell-level provenance data.
- Explore guide: cast-badge and chat layout render; surface planner mode ("Surface planner mode" banner) activates on `?planner=1`.
- Sighting check: Bedrock response visible with model badge within 60s.
- Moderation: queue loads with pending submission cards.
- Automation chip: "Automation" + "agent@orcast.dev" visible with agent key.

**Verdict: No gap.**

### API/backend layer
- `/api/be/api/gates`: returns `status`, `effective_confidence`, `caveats` — correct shape.
- `/api/be/api/hotspots`: 50 hotspots with `probability`, `confidence` fields.
- `/api/be/api/sightings`: 113 records.
- `/api/be/api/provenance`: returns `effective_confidence`, `confidence`.
- `/api/interactions/status`: `{"status":"success"}`.
- Live URL: 200 in 1.057s.

**Verdict: No gap.**

### Data layer (DynamoDB)
- All 9 tables confirmed in us-west-2.
- `managed-agents`: 4 items (4 cast roles).
- `decision-records`: 3 items.
- `hotspots`: 113 items.

**Verdict: No gap.**

### Submission copy
- All feature bullets in DEVPOST are demonstrable in the live app.
- AWS Lambda: confirmed in CloudFormation (`AWS::Lambda::Function`).
- EventBridge: `rate(30 minutes)` schedule confirmed.
- Grounding benchmark (91%/0%): numbers from 2026-06-24 run, unchanged.
- External links: orcast-h0.vercel.app (200), gilraitses.github.io PDFs (200), aimez.ai (200).

**Verdict: No gap.**

### Architecture diagram (fig-08)
- Q2 fix applied: Vercel AI Gateway box relabeled to "explore guide chat (claude-haiku-4.5)" with correct arrow to Bedrock.
- All other boxes (App Runner, DynamoDB, S3, Bedrock, RDS, Step Functions, EventBridge, Lambda) match deployed infrastructure confirmed in CloudFormation.

**Verdict: No gap (P2 closed).**

### Whitepaper claims vs. code (E1–E8)
- E1 PSTH: `modeling/psth.py` ✓
- E2 phase-shuffled null: `modeling/fit_kernels.py` ✓
- E3 time-rescaling KS: `modeling/fit_kernels.py` ✓
- E4 effective_confidence: `src/aws_backend/routers/kernel.py` ✓
- E5 deviance skill: `src/aws_backend/routers/kernel.py` ✓
- E6 PIT calibration: `modeling/fit_kernels.py` ✓
- E7 C/M graph: `ProvenanceGraph.tsx` ✓ (description updated in whitepaper to accurately state C/M rendered; X/D/R as step-log inline refs)
- E8 R_uncited: `tools/testing/grounding_parallel_rag.py` ✓

**Verdict: No gap (P2 closed).**

## Summary

| Severity | Found | Closed | Surviving |
|---------|-------|--------|-----------|
| P0 | 0 | — | 0 |
| P1 | 0 | — | 0 |
| P2 | 2 | 2 | 0 |

**Wave Set Q complete. No surviving gaps. Submission-ready.**
