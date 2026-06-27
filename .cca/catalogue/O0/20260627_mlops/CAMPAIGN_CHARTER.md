# Forward-path campaign charter (ground + activate the path off 0%)

Date: 2026-06-27 (America/New_York)
Lane: O0 orchestrator, forecast ML-ops (MLM + MLO)
Home: `.cca/catalogue/O0/20260627_mlops/`
Authority above this doc: `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section B.
Inputs: W1-W4 results, `research/SYNTHESIS_L2_L3.md`, `DECISION_RECORD.md` (incl. sec 4, the
adopted bin-level timing gate).

## 0. Why this campaign exists

After W4 + the recorded supervisor adoption of the bin-level timing gate, the entire path off 0%
collapses onto ONE binding fact: the served L2 timing gate now earns credit the moment the **served**
fit's held-out CV mean-deviance-skill turns positive. Served single-station skill is `-0.047`; the
4-station experiment is `+0.078`. The gap is closed only by putting the 3 extra Orcasound nodes into
the production `acoustic_detections` stream. That move is deploy-gated and, on the current scoring,
would slam confidence to 1.0. This campaign grounds every step of that path before any of it runs, and
executes in parallel the one piece that is safe today (the confidence-cliff fix).

Honesty is unchanged (B.1): nothing here promotes `effective_confidence`. Research grounds; build is
gated; promotion needs a passing gate on SERVED data + a recorded supervisor decision.

## 1. Objectives (the forward path, from the recommended path)

- **O1 -- Production multi-station ingest.** Land orcasound_lab / andrews_bay / north_san_juan_channel
  into the production `acoustic_detections` stream (`src/aws_backend/ingest_multistation.py`,
  dry-run validated). This is the single binding, deploy-gated dependency for BOTH L2 blockers.
- **O2 -- Confidence-cliff fix.** Graduate `_confidence_from_gates` so a positive multi-station fit
  promotes to a defensible, effect-size-scaled value rather than a binary jump to 1.0. Code-only,
  local, no deploy -- **executed in parallel with this charter (P0 below).**
- **O3 -- Honest multi-station promotion.** After O1, refit multi-station SERVED, re-score
  cross-station consistency on the denser data, and route a promotion through
  `promotion/supervisor.py` ONLY if the held-out CV-skill is robustly (fold-stable) positive.
- **O4 -- L3 grounding.** Extend the real Fraser-summer Chinook series (live 2026 Albion via the
  aimez EC2) and re-test the pre-registered Jun-Sep window with more presence-years before any decision
  on the FLAGGED-FOR-DECISION L3 result. Otherwise L3 stays WITHHELD honestly.

## 2. Shape: one parallel deploy + a research/grounding wave that gates three build waves

```
P0 (NOW, parallel, no deploy) ----> confidence-cliff fix (O2)            [code-only, served stays 0.0]

W5  research / grounding (parallel, no production write, no deploy)
  G1 ingest-deploy grounding   --> deploy runbook + pre-deploy gate + rollback   (grounds W6/O1)
  G2 promotion-protocol ground --> fold-stable skill def + served-refit spec +
                                   supervisor decision-record format +
                                   consistency-after-ingest projection           (grounds W7/O3)
  G3 L3 grounding              --> live-2026-Albion fetch design + presence-year
                                   power analysis + provenance                    (grounds W8/O4)

W6  DEPLOY ingest (gated: W5-G1 PASS + operator deploy approval)      --> O1
W7  PROMOTE multi-station (gated: W6 done + W5-G2 PASS)               --> O3 (promotion supervisor-gated)
W8  L3 live feed + re-test (gated: W5-G3 PASS)                        --> O4 (L3 decision operator-gated)
```

W5 is investigation-first (mirrors `research_dispatch`): each agent writes ONE grounding doc with
measured numbers + a runbook/spec + a go/no-go. No agent edits a convergence file, deploys, or
promotes. The three downstream waves do not launch until their grounding doc passes AND the operator
opens the gate.

## 3. P0 -- the parallel deploy (running now)

A single modeling agent graduates `modeling/fit_kernels.py::_confidence_from_gates` so confidence
scales with held-out CV-skill magnitude/stability and is capped below 1.0 until skill is large and
stable; the 0.0 floor and all gate pass/fail definitions are unchanged. Invariants: served confidence
stays EXACTLY 0.0, `mlops-gate` green, no production write, local-only/untracked (B.6), no commit. This
is safe because it can only make promotion MORE conservative and nothing is promoted today.

## 4. W5 grounding agents (canonical scope; prompts in `CAMPAIGN_DISPATCH.md`)

- **G1 ingest-deploy grounding** -- owns `research/forward/G1_ingest_deploy.md`. Read
  `ingest_multistation.py` + `ingest_timeseries.py`. Produce: the production deploy runbook
  (idempotency / dedup by station+window, backfill window + oldest-first `fetch_history` handling,
  partition/schema into `acoustic_detections`, cost + rate-limit + OrcaHello 403 handling,
  observability, ROLLBACK), a PRE-DEPLOY GATE checklist, and an estimate of how many net new
  detections each node adds to the SERVED store (this is what flips served CV-skill, not the cached
  index). No write; dry-run reads only.
- **G2 promotion-protocol grounding** -- owns `research/forward/G2_promotion_protocol.md`. Define
  "robustly positive" held-out CV-skill (fold count, stability/variance bound, min margin),
  the multi-station SERVED refit reproduction spec (env, S3 bucket B.4, `write_outputs=False`,
  upload disabled), the exact `promotion/supervisor.py` decision-record this would generate
  (confidence >= 0.6 + cv + pit), how it composes with the P0 confidence map, and a projection of
  cross-station consistency at 12 bins AFTER the ingest's added counts (will diel/lunar clear; tide
  stays flagged). Output: the promotion protocol + a go/no-go template. No refit that writes; analysis
  + spec only.
- **G3 L3 grounding** -- owns `research/forward/G3_l3_grounding.md`. Design the live 2026 Albion fetch
  (extend `WIRING-salmon-albion.md`; via aimez EC2 i-04a649f91274e9fce; provenance + refresh cadence).
  Power analysis: how many more Jun-Sep presence-years are needed for the pre-registered test to be
  robust (current LOYO 2/5, 5-9 presence-days/yr), and what out-of-sample bar the L3 flag must clear
  to graduate from FLAGGED-FOR-DECISION. Output: the L3 advancement plan + the decision bar. No
  promotion; L3 stays WITHHELD.

## 5. Locked constraints (HANDOFF_CHARTER section B; unchanged)

- B.1 No promotion without a passing gate on SERVED data + a recorded supervisor decision. W5 grounds
  only; W7 promotion is supervisor-gated; W8 L3 decision is operator-gated.
- B.4 SERVED store is bucket `198456344617-us-west-2-orcast-aws-backend-raw-payloads`, us-west-2.
- B.5 Any refit sets `fk._maybe_write_s3 = lambda: None` + `write_outputs=False`; no production write.
- B.6 `modeling/` pipeline + `data/models/` are local-only/untracked; only `modeling/studies/**` +
  reports and `tide_harmonic.py` are tracked.
- B.7 Heavy fits `.venv-modeling`; ladder/gate system python3; backend `.venv`.
- B.8 `tools/waves/run-gate.sh mlops-gate` stays green + honest after every change.
- B.10 No commit/push without an explicit operator ask; surgical staging.
- External feeds via aimez EC2 (`i-04a649f91274e9fce`).

## 6. Gates

- P0 exit: served confidence still 0.0; `mlops-gate` green; new confidence curve documented.
- W5 exit: G1/G2/G3 each land a grounding doc with measured numbers + a runbook/spec + a go/no-go.
- W6 gate (O1): G1 PASS + operator deploy approval + the production store write (deploy-gated).
- W7 gate (O3): W6 done + G2 PASS + a SERVED multi-station fit with fold-stable positive CV-skill +
  a recorded supervisor decision -> only then does `effective_confidence` rise.
- W8 gate (O4): G3 PASS + extended series clears the pre-registered out-of-sample bar + operator
  decision -> otherwise L3 stays WITHHELD.
- Any commit/push: explicit operator ask (B.10).

## 7. Return contract

Each W5 agent returns its grounding doc, the measured numbers, the runbook/spec, and a go/no-go for
its downstream wave. The orchestrator assembles the three go/no-go calls into the W6/W7/W8 launch
decision and surfaces the deploy/promotion gates to the operator. No agent deploys, promotes, or
commits.

## 8. Status

CHARTERED. P0 executing in parallel. W5 dispatch in `CAMPAIGN_DISPATCH.md`; W5 launch is the next
operator gate. W6/W7/W8 are gated behind W5 + the operator deploy/promotion gates.
