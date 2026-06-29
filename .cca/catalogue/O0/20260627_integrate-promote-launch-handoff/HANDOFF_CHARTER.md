# Handoff charter -- integrate / measure-on-served / promote-decision orchestrator

Date: 2026-06-27 (America/New_York). Repo: orcast `main` at `9a00e15` (in sync with `origin/main`); the
graduation waveset output is uncommitted decision-aid state on top of it. This charters a fresh thread
whose job is to ACT on `SYNTHESIS_graduation.md` -- the first work in this lane that edits convergence
files, runs SERVED-store fits, and leads toward a promotion decision. Hydrate from files, not from the
transcript linearly.

## A. Purpose

The signal & modeling research campaign + the graduation prototype-and-measure waves are DONE. Every
candidate was measured against the held-out, fold-stable +0.144 bar. The measured result
(`research/signal_modeling/graduation/SYNTHESIS_graduation.md`):
- **The two SYN flagships fell.** TA1 (2-state MMPP) is a per-fold re-leveling artifact that breaks PIT
  and does NOT repair the time-rescaling GOF. TB1 (Port Townsend + Bush Point) adds 25 net-new region
  presence-days but **0 in summer**, so it is off-season coverage, not a summer-gate lever.
- **One sleeper cleared the bar.** TA5 (physics smoothness shape prior) measured **+0.177 (5/5 folds,
  across-fold lower bound +0.111, PIT calibrated)** on the EXPERIMENT store -- but NOT yet on the served
  store.
- **The real new-observation lever is TB4** (ONC/JASCO Boundary Pass): summer coverage YES, independent
  operator/detector/corridor, disjoint 2015-2019 epoch; its summer SRKW count is unmeasured.
- TA2 (partial-pooling NB) + TA3 (AIS effort) are enablers (fold-stability + a non-flat `log E`), not
  skill levers. TA4, TB5-at-N, TB3-as-lever, and all drift-guard dead-ends held NO-GO.

This thread executes the §4 sequencing from `SYNTHESIS_graduation.md`, one operator-gated step at a time.
Nothing it does promotes confidence automatically: a confidence change is ALWAYS a passing SERVED gate
PLUS a recorded supervisor decision. The deliverable is a measured served-store verdict on TA5, a clean
fold-stable baseline (TA2+TA3), a measured TB4 summer count, and -- only if a step passes the served gate
-- a recommended supervisor promotion decision for the operator to make.

## B. Decisions that are LOCKED, do not reopen

Inherits the forecast ML-ops locks (`.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` section
B) and the signal-modeling-launch locks
(`.cca/catalogue/O0/20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md` section B). Restate them in
the section H ack. The ones that bind THIS lane most:

1. **Honesty / promotion gate (B.1).** `effective_confidence` is 0% and only rises on a passing SERVED
   gate PLUS a recorded human decision via `src/aws_backend/promotion/supervisor.py`. Never a refit side
   effect. This thread may RECOMMEND a promotion; the operator/supervisor makes it.
2. **The +0.144 fold-stable bar (B.2).** Judge every change by held-out, fold-stable CV mean-deviance-skill
   (>=4/5 folds, across-fold lower bound, PIT calibrated, beaten L1 null), never in-sample fit. The TA5
   experiment-store +0.177 means NOTHING until it reproduces on the SERVED store under this bar.
3. **Experiment store != served store.** All graduation numbers are on the 4-station experiment store
   (2089 det / ~300 effective onsets). The served gate is the single-station served fit and the post-ingest
   served 4-station fit. A graduate must clear the bar on SERVED data to count.
4. **Single convergence-file editor; serialize integrates.** The convergence files (`modeling/fit_kernels.py`,
   `modeling/estimator.py`, `modeling/design.py`, `modeling/studies/*`, `src/aws_backend/sources/*`,
   `src/aws_backend/ingest_multistation.py`) are edited ONE owner at a time. Do the TA5 integrate, then
   TA2, then TA3, then TB-side measurement -- not in parallel. Apply each lane's PATCH-SPEC verbatim where
   possible; keep defaults byte-identical (a no-op default, opt-in via flag).
5. **AWS store footgun (B.5) + refit-upload-disable (B.6).** The store is bucket
   `198456344617-us-west-2-orcast-aws-backend-raw-payloads` in `us-west-2` (NOT the config default). Run
   served fits with `ORCAST_STORAGE_BACKEND=aws ORCAST_RAW_PAYLOAD_BUCKET=198456344617-us-west-2-orcast-aws-backend-raw-payloads AWS_REGION=us-west-2`. Until the operator explicitly approves a promotion, keep
   the production artifact upload DISABLED (`fit_kernels._maybe_write_s3 = lambda: None` or
   `write_outputs=False`) -- measure first, write the served `fit_report.json` only as the explicit
   promotion step.
6. **Repo layout / environments (B.7/B.8).** `modeling/` + `data/models/` are local-only (untracked);
   only `modeling/studies/**` + `modeling/tide_harmonic.py` are tracked. Heavy fits use `.venv-modeling`;
   the stdlib ladder + `tools/waves/run-gate.sh mlops-gate` use system `python3`. mlops-gate is LOCAL and
   must stay green (served confidence must not exceed earned).
7. **No fetch-that-writes / ingest without an operator gate (B.9).** The TB4 summer measurement parses the
   PUBLISHED ECHO `Annotations.csv` read-only; any production ingest of TB4 (or a TB1 region expansion) is
   a separate operator-/deploy-gated step. DFO/external feeds via the aimez EC2 `i-04a649f91274e9fce`.
8. **No commit/push without an explicit operator ask (B.10).** Surgical staging only, never `git add -A`.
   The local modeling pipeline + `data/models/` are untracked by convention; do not commit them.
9. **Drift-guard holds.** The adjudicated dead-end set stands (LGCP/GP at N, ZI/hurdle-count, MMPP-as-skill,
   CUTI/BEUTI, HF-radar, terrain-on-temporal-gate, full PINN, etc.). The DE source-doc drift fixes
   (DE1/DE2/DE3) are RECOMMENDED-not-applied; landing them is a low-risk parallel cleanup, not a model
   change, and must preserve the Hawkes-as-GOF-diagnostic nuance.

## C. What this thread does (the §4 sequence)

| Step | Action | Convergence files | Gate | Outcome |
|------|--------|-------------------|------|---------|
| 1 | **Re-measure TA5 smoothness prior on the SERVED store** (single-station + post-ingest served 4-station) under G2. Integrate `estimator.py` + `fit_kernels.py` per TA5 patch-spec (nested-CV lambda, default byte-identical). | estimator.py, fit_kernels.py | served G2 (+0.144 fold-stable) | served verdict; if it clears the bar, a RECOMMENDED supervisor promotion for the operator |
| 2 | **Land TA2 + TA3 as the clean baseline** (partial pooling for station-held-out fold-stability; AIS/effort wire so `log E` is non-flat). Neither promotes alone. | fit_kernels.py, design.py, sources/* | fold-stability + calibration (not +0.144) | a clean, honest baseline future covariates are judged against |
| 3 | **Measure the TB4 summer SRKW presence-day count** (parse the published ECHO `Annotations.csv` UTC column; reconstruct ULS effort). Read-only. | none (measurement) | summer count materially positive? | go/no-go on grounding TB4 as the new-observation lever (ingest is a later operator gate) |
| 4 | **Re-judge TB2 (SST-front) and TB5 (currents)** against the clean baseline -- only after steps 1-2. TB2 needs estimator support for an aperiodic per-fold season-orthogonalized covariate. | estimator.py (TB2), sources/* | marginal fold-stable served CV-skill | keep / drop each covariate honestly |
| 5 (parallel, low-risk) | **Apply DE source-doc drift remediations** (DE1/DE2/DE3 prioritized lists), preserving Hawkes-as-diagnostic. | docs/methodology/*, .cca prose, wave_shape.yml | text-only | the adjudicated dead-ends stop reading as live paths |

Steps 1-4 are serialized (single-editor). Step 5 is text-only and can run alongside. NOTHING promotes
without a passing served gate + a recorded supervisor decision; ingest/region-expansion/deploy stay
operator-gated.

## D. Inputs (read these; the lane docs carry the patch-specs)

- `research/signal_modeling/graduation/SYNTHESIS_graduation.md` (the ranked measured plan + section 4 sequence)
- `research/signal_modeling/graduation/TA5_shape_priors.md` (the GO lever + its estimator/fit_kernels patch-spec)
- `research/signal_modeling/graduation/TA2_hierarchical_nb.md`, `TA3_ais_effort.md` (the baseline enablers + patch-specs)
- `research/signal_modeling/graduation/TB4_onc_boundary_pass.md` (the summer-count measurement plan)
- `research/signal_modeling/graduation/TB2_sst_front.md`, `TB5_salishseacast_currents.md` (conditional covariates + patch-specs)
- `research/signal_modeling/graduation/DE1_text_drift.md`, `DE2_method_drift.md`, `DE3_strategy_drift.md` (drift remediations)
- `research/forward/G2_promotion_protocol.md` (the +0.144 bar + fold-stability definition + the served gate)
- `docs/methodology/FORECAST_KERNELS.md`, `CALIBRATION_STUDIES.md` (model form, effort-bias, gates)

## E. Open gate / metric state (numbers)

- Effective confidence **0.0**. L0 PASS, L1 PASS, L2 FAIL (time-rescaling), L3 WITHHELD.
- Served W7 4-station refit: held-out CV mean-deviance-skill **+0.078 -> P0 confidence 0.49 -> supervisor
  HOLD** (< 0.6). NOT promoted; served `fit_report.json` untouched.
- P0 curve: +0.078 -> 0.49, **+0.144 -> 0.60**, +0.200 -> 0.66, cap 0.75; PIT-uncalibrated caps at 0.35.
- Graduation measured (EXPERIMENT store, NOT served): TA5 +0.177 (5/5, LB +0.111, PIT ok); TA1 artifact
  NO-GO; TA2 +0.047 enabler; TA4 negative; TB1 0 summer; TB4 summer-coverage-yes/count-unmeasured.

## F. Pending uncommitted local state

Everything through `9a00e15` is committed/pushed. This handoff home + the entire
`research/signal_modeling/graduation/` directory (13 lane docs + `SYNTHESIS_graduation.md`) + the
`STEP_LOG.md`/`wave_shape.yml` graduation updates are UNCOMMITTED decision aids until an explicit operator
commit ask (surgical staging only). The `modeling/` pipeline + `data/models/` stay local-only (untracked).
A cross-machine rehydration that must reproduce a fit re-runs from S3 (B.5).

## G. Return contract (ack on first response)

Before acting, the new thread returns:
- Hydration confirmed + the list of files read.
- The locked items (section B) restated in your own words -- especially the served-vs-experiment store
  distinction (B.3), the single-editor serialize rule (B.4), the upload-disable-until-promotion rule
  (B.5/B.6), and that nothing promotes without a passing served gate + a supervisor decision (B.1).
- Gate state in one line (confidence 0%, served +0.078 -> 0.49 HOLD, need served fold-stable +0.144).
- The plan: step 1 (TA5 served re-measure) first, the serialized order of 2-4, and that step 5 (DE drift
  fixes) can run alongside.
- One risk still needing attention (e.g. the experiment-store +0.177 not reproducing on the served
  single-station store; or TA5 shrinkage biasing published kernel curves toward flat).

## H. Transcript / provenance pointer

Originating session (graduation waveset): `~/.cursor/projects/Users-gilraitses-orcast/agent-transcripts/d1a6e144-e8c4-4fd5-b258-2b14a7213a9b/d1a6e144-e8c4-4fd5-b258-2b14a7213a9b.jsonl`.
Search by keyword (graduation, TA5, +0.177, TA1 MMPP artifact, TB1 0 summer, TB4 Boundary Pass,
SYNTHESIS_graduation, drift-guard), do NOT read linearly. Lane home:
`.cca/catalogue/O0/20260627_mlops/`. Prior rotations: `.cca/catalogue/O0/20260627_signal-modeling-launch-handoff/`,
`.cca/catalogue/O0/20260627_mlops-handoff/`.
