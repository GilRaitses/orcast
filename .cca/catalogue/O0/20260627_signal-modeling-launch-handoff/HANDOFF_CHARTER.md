# Handoff charter, signal & modeling research campaign launch orchestrator

Date: 2026-06-27 (America/New_York). Repo: orcast `main` at `9a00e15` (in sync with `origin/main`).
This charters a fresh thread whose job is to LAUNCH and MANAGE the signal & modeling research campaign
(the `signal_modeling_research` waveset in `.cca/catalogue/O0/20260627_mlops/`), which is CHARTERED and
dispatch-ready as of `9a00e15`. Hydrate from files, not from the transcript linearly.

## A. Purpose

The forecast ML-ops frontier is stuck at an honest wall: the served 4-station fit measures held-out
CV-skill **+0.078 -> confidence 0.49 (HOLD)**, below the 0.6 supervisor promotion threshold, and the W6
multi-station ingest added **0 net-new analysis observations**, so re-running the same cached data cannot
move the number. Crossing 0.6 honestly needs **genuinely new, independent signal -> served CV mean-
deviance-skill ~+0.144, fold-stable.** The signal & modeling research campaign researches the two ways to
get there. The new thread:
1. Launches the five research subagents in two parallel waves + a synthesis (W9 S1/S2, W10 M1/M2/M3, SYN)
   per `SIGNAL_MODELING_DISPATCH.md`.
2. Manages them to completion, collecting findings under `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/`.
3. Runs the synthesis (SYN) and brings the ranked graduates back to the operator as SEPARATE,
   operator-gated build/deploy/promote waves.

Nothing in this campaign promotes confidence. Every graduate earns confidence later only via a passing
gate on SERVED data + a recorded supervisor decision. The new thread's deliverable is decision-grade
findings + a ranked plan, NOT a confidence change.

## B. Decisions that are LOCKED, do not reopen

These carry the forecast ML-ops locks (`.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` §B)
plus the campaign-specific ones. Restate them in the §H ack.

1. **Honesty gate.** Effective confidence is 0% and is shown with the gate caveat. `effective_confidence`
   only rises on a passing gate PLUS a recorded human decision via `src/aws_backend/promotion/supervisor.py`.
   This campaign is investigation-first: findings are decision aids, nothing it produces promotes (B.1).
2. **The +0.144 bar (the whole point of the campaign).** W7 measured served CV-skill +0.078 -> 0.49 HOLD.
   Under the P0 confidence map, conf 0.6 is reached at skill ~+0.144 AND fold-stable (>=4/5 folds with a
   fold pass-rate that beats chance, an across-fold lower bound, PIT calibrated, a beaten L1 null). Judge
   EVERY proposed node/covariate/model by held-out, fold-stable CV mean-deviance-skill, NEVER in-sample
   fit. The frontier is small-N and the confidence map saturates quickly, so flexible methods that cannot
   show out-of-sample fold-stable gains are dead-ends, stated honestly.
3. **W6 reality.** The served store is now 4-station (haro_strait 761, orcasound_lab 1029, andrews_bay 265,
   north_san_juan_channel 34 = 2089 det), but the W6 ingest added 0 net-new ANALYSIS observations (same
   cached rows). It is plumbing/forward-accumulation, NOT an L2 pass and NOT a confidence change. So new
   skill must come from genuinely new observation (new in-region nodes / accrued summers) or more signal
   per observation (better models / subtler covariates) -- not a re-run.
4. **Effort-bias / covariate-role honesty (B.2 in §B of mlops).** Temporal kernels come from continuous
   acoustic detections (effort-stable) with a `log E` offset; visual sightings are validation + `s_space`
   only; the hydrophone is a fixed position, not a whale GPS fix. Every proposed covariate (S2/M3) MUST be
   classed honestly as effort/exposure term vs effect-modifier vs validation-only. Acoustic stays the
   temporal driver; nothing is laundered into whale GPS.
5. **AWS store footgun.** The timeseries store is S3 bucket
   `198456344617-us-west-2-orcast-aws-backend-raw-payloads` (region `us-west-2`), NOT the config default
   `orcast-raw-payloads`. Reproduce any fit with:
   `ORCAST_STORAGE_BACKEND=aws ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads AWS_REGION=us-west-2 PYTHONPATH=. .venv-modeling/bin/python -m modeling.fit_kernels`.
6. **Refit safety.** When refitting against S3, DISABLE the production artifact upload
   (`fit_kernels._maybe_write_s3 = lambda: None` in a driver, or `write_outputs=False`). A confidence
   change must be a recorded supervisor decision, never a refit side effect. This applies if any graduate
   gets prototyped against served data.
7. **Repo layout.** The `modeling/` fit pipeline (`fit_kernels.py`, `design.py`, `estimator.py`,
   `bases.py`, `tide_phase.py`, `validation/`) and `data/models/` are local-only (untracked). Only
   `modeling/studies/**` + `modeling/studies/reports/*.json` are tracked, plus `modeling/tide_harmonic.py`.
   Do not expect the harmonic-tide integration or `fit_report.json` on a clean checkout.
8. **Environments.** `.venv-modeling/bin/python` (numpy/pandas/scipy/matplotlib/boto3) runs heavy fits +
   heavy studies. The stdlib ladder (`modeling/studies/run_studies.py`) and `tools/waves/run-gate.sh
   mlops-gate` run under system `python3`. `.venv` (py3.14) has the backend deps. mlops-gate is LOCAL, not
   in GitHub CI; it runs L0-L3 + the honesty guard (served confidence must not exceed earned).
9. **External flake + EC2 escape hatch.** OrcaHello history 403s / SSL-EOFs on heavy paging and
   `fetch_history` is oldest-first; for multi-station use the reviewed-outcome endpoints + cached indexes
   (`.cca/catalogue/O0/20260627_forecast-candidates/orcahello_index*.cache.json`). Local DNS BLOCKS the DFO
   FOS host (`www-ops2.pac.dfo-mpo.gc.ca`); fetch DFO/external feeds via the aimez EC2
   `i-04a649f91274e9fce` (SSH/SSM), which CAN resolve it. External literature (W10) via web search/fetch.
10. **Write policy.** No commit or push without an explicit operator ask. Surgical staging only (never
    `git add -A`; the repo has heavy untracked dirs -- demo, figures, modeling pipeline). Research subagents
    deploy nothing, write to no production store, run no fit that writes, promote nothing, and COMMIT
    nothing (B.10) -- they only write their one findings doc. The launching orchestrator commits the
    findings only on an explicit operator ask.

## C. Registry snapshot

| Slice | What shipped | Status |
|-------|--------------|--------|
| W1-W2 frontier (de-risk + integrate) | L2 blockers localized: burstiness (modeling) + sparse counts (volume) | done |
| W3 L3 (real Albion Fraser Chinook) | stock-aligned FOS 2019-2026 cached + wired; lag scan still withheld | done |
| Research waveset (RA-RF) | counts/conditioning/diel-temp/burstiness/data-volume + synthesis | done, graduated to W4 |
| W4 build | consistency re-score + summer-conditioned L3 + bin-level timing gate | done; gate ADOPTED (supervisor) |
| P0 confidence-cliff fix | effect-size-scaled saturating map, cap 0.75; +0.078 -> 0.49 | done |
| W5 grounding (G1/G2/G3) | ingest runbook + promotion protocol + L3 power analysis | done |
| W6 deploy 3-node ingest | served store now 4-station (2089 det); 0 net-new analysis obs | done, DEPLOYED |
| W7 promote (measured) | served refit +0.078 -> 0.49; supervisor HOLD; NOT promoted | done, measured-HOLD |
| W8 L3 live feed + re-test | GO on the 2026 Albion fetch; NO-GO on L3 promotion | gated |
| **signal_modeling_research** | **the +0.144 lever: W9 S1/S2 + W10 M1/M2/M3 + SYN** | **CHARTERED, dispatch-ready <- THIS LANE** |

## D. PRIMER, open items

Operator's verbatim launch instruction (this rotation): *"use the orchestrated rotation skill once the
charter is ready to launch and I would like to have a new fresh orchestra thread kick that off and manage
it make sure you include all the context that needs in the step logs and everything."*

The charter that this thread launches was created on the operator's verbatim request: *"commit and push
the record charter waveset with parallel target research agents for source discovery for grounding all the
additional in-region nodes ... make waves to explore creative and physics-based modeling literature for
sparse data and non-linear dynamics to capture more granularity and maybe subtler covariates computed from
existing or available-to-source signals."*

So the new thread's first action after the §H ack is to LAUNCH W9 + W10 (five parallel research subagents)
per `SIGNAL_MODELING_DISPATCH.md`, then run SYN. Two research directions, both honest-gated:
- MORE observation: S1 in-region node discovery + grounding (genuinely new nodes beyond the 4), S2
  covariate source discovery.
- MORE signal per observation: M1 sparse-data methods, M2 nonlinear-dynamics / physics-based, M3 subtler
  derived covariates.

## E. Dispatch table

| Lane | Owner | Inputs | Exit bar | Status |
|------|-------|--------|----------|--------|
| W9-S1 node source discovery | research subagent | `SIGNAL_MODELING_DISPATCH.md` S1; `src/aws_backend/ingest_multistation.py`; `research/forward/G1_ingest_deploy.md` | node catalog + per-node access/provenance + W6-style grounding plan + independent-vs-duplicate flag + ranked go/no-go | chartered |
| W9-S2 covariate source discovery | research subagent | dispatch S2; `docs/methodology/FORECAST_KERNELS.md`; `modeling/tide_harmonic.py` | covariate source catalog + per-signal B.2 role + collinearity + ranked go/no-go | chartered |
| W10-M1 sparse-data methods | research subagent | dispatch M1 | ranked method shortlist + held-out payoff + data-volume need + feasibility | chartered |
| W10-M2 nonlinear / physics | research subagent | dispatch M2 | shortlist + HONEST small-N over-fitting risk + promising-now vs needs-more-data | chartered |
| W10-M3 derived covariates | research subagent | dispatch M3 (uses S2 if available) | derived-covariate list + recipe + B.2 role + collinearity + expected held-out contribution | chartered |
| SYN synthesis | orchestrator or subagent | S1+S2+M1+M2+M3 | ranked plan toward fold-stable +0.144 (data vs model, B.2 role) + the cheapest high-value experiment | chartered (depends on W9+W10) |
| Graduate -> build/deploy/promote | operator-gated | SYN ranked plan | a separate gated wave; nothing here promotes | gated |

## F. Open gate / metric state (numbers)

- Effective confidence **0.0**. L0 PASS (ROC AUC 0.879), L1 PASS (diel/lunar/season beat null), L2 FAIL,
  L3 WITHHELD.
- W7 served 4-station refit: n_stations=4, n_detections=2089, held-out CV mean-deviance-skill **+0.078**
  (4/5 folds, fold null-test p=0.1875 NOT distinguishable from chance), PIT calibrated (ks_pval 0.36),
  time-rescaling withheld (event-level Exp(1) fails). P0 map -> **confidence 0.49** -> supervisor **HOLD**
  (< 0.6). NOT promoted; `write_outputs=False` so served `fit_report.json` untouched.
- P0 confidence curve: +0.078 -> 0.49, +0.120 -> 0.57, **+0.144 -> 0.60**, +0.200 -> 0.66, cap 0.75; if
  PIT not calibrated max reachable 0.35 (never promotes). Consistency is NOT a confidence-map input.
- The bin-level L2 timing gate is ADOPTED (recorded supervisor decision, DECISION_RECORD §4) but does not
  promote alone (the load-bearing CV-skill half still gates).
- L3: real Albion (Fraser-summer Chinook) FOS series cached 2019-2026 + wired; pre-registered summer
  held-out is FLAGGED-FOR-DECISION (fragile, LOYO 2/5); the live 2026 fetch is GO (cache stops 2026-06-26
  before the peak), L3 promotion is NO-GO.

## G. Pending uncommitted local state

Everything through `9a00e15` is committed and pushed (the W7 record `2a2c72f` and the campaign charter
`9a00e15`). This handoff home is new and uncommitted until the operator asks. The
`research/signal_modeling/` findings directory does NOT exist yet -- the research subagents create their
docs there on launch; those docs are uncommitted decision aids until an explicit operator commit ask.
The `modeling/` fit pipeline and `data/models/` stay local-only (untracked) by repo convention (B.7); a
cross-actor rehydration that needs to reproduce a fit must re-run from S3 (B.5). Same-machine rehydration
keeps the local pipeline.

## H. Return contract (ack on first response)

Before acting, the new thread returns:
- Hydration confirmed + the list of files read.
- The locked items (§B) restated in your own words, especially: the honesty/promotion gate (B.1), the
  **+0.144 fold-stable bar** and judge-by-held-out-skill rule (B.2), the W6 0-net-new reality (B.3), the
  covariate-role honesty (B.4), the AWS bucket footgun (B.5), the refit-upload-disable rule (B.6), the
  local-only modeling pipeline (B.7), the EC2-for-DFO escape hatch (B.9), and agents-commit-nothing (B.10).
- Gate state in one line (confidence 0%, W7 0.49 HOLD, need fold-stable +0.144).
- The launch plan: which subagents you are about to dispatch (W9 S1/S2, W10 M1/M2/M3) and that SYN follows.
- One risk still needing attention (e.g. small-N overfitting of flexible methods).

## I. Transcript / provenance pointer

Originating session: `~/.cursor/projects/Users-gilraitses-orcast/agent-transcripts/ea277340-2008-4d24-9390-cc3db27db138/ea277340-2008-4d24-9390-cc3db27db138.jsonl`.
Search by keyword (signal_modeling, +0.144, W7, measured-HOLD, W6 ingest, P0 confidence, +0.078, EC2,
Albion), do NOT read linearly. Campaign home: `.cca/catalogue/O0/20260627_mlops/`. Prior forecast ML-ops
rotation: `.cca/catalogue/O0/20260627_mlops-handoff/`.
