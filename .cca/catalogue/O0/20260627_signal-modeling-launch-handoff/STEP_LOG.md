# Step log, signal & modeling research campaign launch handoff

Synthesis trace, newest-last. Each step is the durable summary; full detail is in the campaign trace
(`.cca/catalogue/O0/20260627_mlops/STEP_LOG.md`) and the originating transcript (HANDOFF_CHARTER §I) --
search by keyword, do not transcribe. This log is written so the fresh thread has the COMPLETE context it
needs to launch and manage the campaign without replaying anything.

## Lineage the new thread inherits (how we got to the wall)

S01. **L0/L1 passed; L2 localized.** L0 detector PASS (ROC AUC 0.879), L1 PASS (diel/lunar/season beat
null). The L2 frontier failed at 0% on two blockers, which W1-W2 diagnostics localized precisely:
time-rescaling GOF fails from detection **burstiness/clustering** (a modeling problem, not effort), and
cross-station kernel consistency fails from **sparse counts** (a data-volume problem), NOT from missing
nodes. See `research/SYNTHESIS_L2_L3.md` for the corrected blocker map.

S02. **L3 grounded but still withheld.** W3 sourced the real, stock-aligned Fraser-summer Chinook signal
(DFO FOS Albion CPUE, cached `data/salmon/albion_fos/fos2019..2026.csv`, wired in
`src/aws_backend/sources/salmon.py`). Even with correct data all years, the daily-binary-presence lag scan
does not beat the null (p=0.394). A pre-registered summer-conditioned held-out is FLAGGED-FOR-DECISION but
fragile (LOYO 2/5). L3 stays WITHHELD.

S03. **Research waveset (RA-RF) ran and graduated to W4.** It answered: counts vs binary presence,
season/diel/temperature conditioning, burstiness/Hawkes timing, and the data-volume dependency. RE refuted
the assumption that the 3-node ingest was the binding L2 blocker -- scoring resolution + burstiness are.

S04. **W4 build + the P0 confidence-cliff fix.** W4 landed the cross-station consistency re-score, the
summer-conditioned L3 scan, and a bin-level L2 timing gate (ADOPTED by recorded supervisor decision,
DECISION_RECORD §4). P0 replaced the binary 0.25/quarter confidence sum with an effect-size-scaled,
saturating map capped at 0.75: `0.50*gate_factor*(1-exp(-skill/0.12)) + 0.15*PIT + 0.10*level1`. This is
why a single positive CV-skill no longer jumps to 1.0 -- it now scales with the held-out effect size.

S05. **Forward-path campaign W5-W8 chartered + grounded.** G1 produced the node-ingest runbook (and the
key finding that the ingest adds 0 net-new ANALYSIS observations); G2 produced the two-band promotion
protocol and the +0.144 derivation; G3 produced the L3 power analysis + the live 2026 Albion fetch design.

S06. **W6 DEPLOYED (commit `c11047d`).** Ran `ingest_multistation_acoustic(store, dry_run=False)` against
the served store (bucket §B.5). Served store is now 4-station: haro_strait 761 (unchanged), orcasound_lab
1029, andrews_bay 265, north_san_juan_channel 34 = 2089 det. Idempotent (station,t,id), reversible. NO fit
ran -> effective confidence stays 0.0. This is plumbing, not an L2 pass.

S07. **W7 MEASURED -> 0.49 HOLD, NOT promoted (commit `2a2c72f`).** Operator asked to "get the number for
the decision and if it passes a very good threshold ... promote it now." Ran the served 4-station refit
under `.venv-modeling` with `_maybe_write_s3` no-op'd and `write_outputs=False` (measurement only; served
`fit_report.json` untouched). Result: 4 stations / 2089 det, held-out CV mean-deviance-skill **+0.0778**
(4/5 folds, fold null-test p=0.1875 -> pass-rate NOT distinguishable from chance), PIT calibrated
(ks_pval 0.36), L1 beats null (diel/lunar/season), time-rescaling withheld (event-level). P0 map ->
**confidence 0.49** -> supervisor **HOLD** (< 0.6). NOT promoted, NOT ratified; `effective_confidence`
stays 0.0, L2 still FAIL. This is exactly G2's predicted ingest-alone HOLD case.

## The wall, stated precisely (the reason this campaign exists)

S08. The W6 ingest reproduced the +0.078 multi-station experiment but added **0 net-new analysis
observations** (same cached rows), so re-running cached data cannot reach 0.6. The P0 curve puts conf 0.6
at served CV-skill **~+0.144 AND fold-stable**. Therefore the only honest path off 0.49 is GENUINELY NEW
signal: (a) more independent observation (new in-region nodes / accrued summers / a real new covariate), or
(b) more signal per observation (better sparse-data / nonlinear modeling / subtler derived covariates).

## This rotation

S09. **Signal & modeling research campaign CHARTERED + pushed (commit `9a00e15`).** Operator: *"commit and
push the record charter waveset with parallel target research agents for source discovery for grounding all
the additional in-region nodes ... make waves to explore creative and physics-based modeling literature for
sparse data and non-linear dynamics ... subtler covariates computed from existing or available-to-source
signals."* Wrote `SIGNAL_MODELING_CHARTER.md` + `SIGNAL_MODELING_DISPATCH.md`, added the
`signal_modeling_research:` block to `wave_shape.yml`, updated the campaign `STEP_LOG.md`/`README.md`.
Shape: **W9 source discovery** (S1 in-region node catalog + grounding; S2 covariate source catalog) +
**W10 modeling literature** (M1 sparse-data; M2 nonlinear-dynamics/physics; M3 subtler derived covariates)
+ **SYN** synthesis. Investigation-first; nothing deploys/promotes/commits. Load-bearing rail: judge every
proposal by held-out, fold-stable CV mean-deviance-skill, never in-sample fit (small-N overfitting trap).
Status CHARTERED, dispatch-ready.

S10. **Orchestrator rotation requested (this handoff).** Operator: *"use the orchestrated rotation skill
once the charter is ready to launch and I would like to have a new fresh orchestra thread kick that off and
manage it make sure you include all the context that needs in the step logs and everything."* Wrote this
handoff home (`.cca/catalogue/O0/20260627_signal-modeling-launch-handoff/`, five files) via the
orchestrator-rotation skill. The fresh thread's job: ack per §H, then LAUNCH the five research subagents
(W9 S1/S2, W10 M1/M2/M3) per `SIGNAL_MODELING_DISPATCH.md`, manage them to completion, run SYN, and bring
the ranked graduates back to the operator as SEPARATE operator-gated build/deploy/promote waves. Nothing
committed in this rotation (per write policy; flagged uncommitted in HANDOFF_CHARTER §G).

## What the new thread does first (the launch plan)

1. Return the §H ack (restate §B locks, gate state, launch plan, one risk).
2. Dispatch the five research subagents in parallel using the prompts in `SIGNAL_MODELING_DISPATCH.md`
   (each writes ONE doc under `research/signal_modeling/`; none deploy/commit/promote). W9 (S1, S2) can
   lead so S2's covariate list feeds M3; W10 (M1, M2, M3) can run concurrently if M3 assumes a candidate
   list.
3. On completion, run SYN -> `research/signal_modeling/SYNTHESIS_signal_modeling.md`: a ranked plan toward
   fold-stable +0.144 (each graduate tagged data-vs-model + its B.2 role) + the single cheapest high-value
   experiment.
4. Bring the ranked graduates to the operator. Any build/deploy/prototype/promote is a NEW gated wave;
   nothing in this campaign promotes confidence.

## Open / awaiting

- W9 + W10 research launch <- the new thread's first action after the ack.
- Commit of this handoff home + (later) the research findings: only on an explicit operator ask
  (surgical staging; the findings dir does not exist until the subagents run).
- Effective confidence stays 0.0 throughout; promotion still requires a passing gate on served data + a
  recorded supervisor decision.
