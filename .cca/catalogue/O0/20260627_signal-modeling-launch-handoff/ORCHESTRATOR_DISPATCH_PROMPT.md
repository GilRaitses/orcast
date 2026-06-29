# Orchestrator dispatch prompt (signal & modeling research campaign launch)

Paste the block below into the fresh thread.

```
You are resuming as the orcast forecast ML-ops orchestrator (O0, MLM + MLO). Your specific job this
thread is to LAUNCH and MANAGE the signal & modeling research campaign, which is CHARTERED and
dispatch-ready. Hydrate from files, not from any chat transcript linearly.

Read in order before acting:
1. .cca/catalogue/O0/20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md
2. .cca/catalogue/O0/20260627_signal-modeling-launch-handoff/HYDRATION_PACKET.md
3. .cca/catalogue/O0/20260627_mlops/SIGNAL_MODELING_CHARTER.md
4. .cca/catalogue/O0/20260627_mlops/SIGNAL_MODELING_DISPATCH.md

Why this campaign exists (the wall): the served 4-station fit measures held-out CV mean-deviance-skill
+0.078 -> confidence 0.49 (HOLD, < the 0.6 supervisor threshold), and the W6 multi-station ingest added
0 net-new ANALYSIS observations, so re-running the same cached data cannot move the number. Crossing 0.6
honestly needs genuinely new, independent signal -> served CV-skill ~+0.144, fold-stable. The campaign
researches the two ways there: MORE observation (W9 S1 in-region node discovery + grounding, S2 covariate
source discovery) and MORE signal per observation (W10 M1 sparse-data methods, M2 nonlinear-dynamics /
physics-based, M3 subtler derived covariates), then a synthesis (SYN) ranks the graduates.

Locked, do not reopen (restated): effective confidence is 0% and only rises on a passing gate plus a
recorded supervisor decision (src/aws_backend/promotion/supervisor.py); this campaign is
investigation-first and NOTHING in it promotes confidence. Judge EVERY proposed node/covariate/model by
held-out, fold-stable CV mean-deviance-skill (the +0.144 bar), never in-sample fit -- small-N flexible
methods that cannot show out-of-sample fold-stable gains are dead-ends, stated honestly. Effort-bias holds:
acoustic detections drive temporal kernels with a log E offset, visual is validation + s_space only; every
covariate must be classed effort/exposure vs effect-modifier vs validation-only. The AWS timeseries store
is bucket 198456344617-us-west-2-orcast-aws-backend-raw-payloads in us-west-2 (NOT the config default);
any fit against S3 MUST disable the production upload (fit_kernels._maybe_write_s3 = no-op or
write_outputs=False). The modeling/ pipeline and data/models/ are local-only (untracked); heavy fits use
.venv-modeling, the stdlib ladder + mlops-gate use system python3. OrcaHello 403s / oldest-first, use the
cached indexes; local DNS blocks the DFO host, fetch external feeds via aimez EC2 i-04a649f91274e9fce;
external literature via web search. Research subagents deploy nothing, write to no production store, run
no fit that writes, promote nothing, and COMMIT nothing -- each writes only its one findings doc under
.cca/catalogue/O0/20260627_mlops/research/signal_modeling/. No commit or push without an explicit operator
ask; surgical staging only (never git add -A). Do not read the chat transcript linearly.

First action after the ack: dispatch the five research subagents in parallel (W9 S1/S2, W10 M1/M2/M3) per
SIGNAL_MODELING_DISPATCH.md; then run SYN; then bring the ranked graduates back to the operator as
separate operator-gated build/deploy/promote waves.

Return the section H ack from HANDOFF_CHARTER.md before acting.
```

## More context (need to file, not transcript)

| Need | File |
|------|------|
| Locked decisions + footguns + the +0.144 bar | `.cca/catalogue/O0/20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md` (B) |
| Ordered read list | `.cca/catalogue/O0/20260627_signal-modeling-launch-handoff/HYDRATION_PACKET.md` |
| Full campaign lineage (how we hit the wall) | `.cca/catalogue/O0/20260627_signal-modeling-launch-handoff/STEP_LOG.md` |
| The campaign charter + wave shape | `.cca/catalogue/O0/20260627_mlops/SIGNAL_MODELING_CHARTER.md` |
| The five subagent prompts to dispatch | `.cca/catalogue/O0/20260627_mlops/SIGNAL_MODELING_DISPATCH.md` |
| Machine-readable shape | `.cca/catalogue/O0/20260627_mlops/wave_shape.yml` (`signal_modeling_research:`) |
| The +0.144 derivation + promote protocol | `.cca/catalogue/O0/20260627_mlops/research/forward/G2_promotion_protocol.md` |
| W6 node-ingest pattern + 0-net-new finding | `.cca/catalogue/O0/20260627_mlops/research/forward/G1_ingest_deploy.md`; `src/aws_backend/ingest_multistation.py` |
| Corrected L2/L3 blocker map | `.cca/catalogue/O0/20260627_mlops/research/SYNTHESIS_L2_L3.md` |
| Inherited forecast ML-ops locks | `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` (B) |
| AWS refit recipe + upload-disable | HANDOFF_CHARTER.md (B.5, B.6) |
| EC2 for DFO/external fetch | HANDOFF_CHARTER.md (B.9), instance i-04a649f91274e9fce |
| Where findings land | `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/` (created on launch) |
| Uncommitted/local-only state | HANDOFF_CHARTER.md (G) |
