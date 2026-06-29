# Hydration packet, signal & modeling research campaign launch orchestrator

Ordered read list for the incoming thread. Read in order; do not read the chat transcript linearly. Paths
are repo-relative to `/Users/gilraitses/orcast` unless noted.

## 1. Governance / canon (read first)

- `.cca/catalogue/O0/20260627_signal-modeling-launch-handoff/HANDOFF_CHARTER.md` (this rotation's authority
  doc -- §B locked decisions, §D the launch instruction, §H the ack)
- `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` (the forecast ML-ops locks this inherits)
- `.cca/catalogue/O0/20260627_orcast-handoff/ORCHESTRATOR_NOTES.md` (operator intent, PIML strategy,
  recommended literature -- directly relevant to W10 modeling literature)

## 2. The campaign this thread launches (read before dispatching)

- `.cca/catalogue/O0/20260627_mlops/SIGNAL_MODELING_CHARTER.md` (the +0.144 lever, the wave shape, the
  honesty rails, the anti-overfitting discipline, the gates)
- `.cca/catalogue/O0/20260627_mlops/SIGNAL_MODELING_DISPATCH.md` (the five self-contained subagent prompts:
  S1, S2, M1, M2, M3, SYN -- dispatch these)
- `.cca/catalogue/O0/20260627_mlops/wave_shape.yml` -> `signal_modeling_research:` block (machine-readable
  shape, agent ownership, gates)

## 3. Why the campaign exists (the measured wall)

- `.cca/catalogue/O0/20260627_mlops/STEP_LOG.md` (newest-first top entries: the campaign charter, the W7
  measured-HOLD, the W6 deploy -- read these three)
- `.cca/catalogue/O0/20260627_mlops/research/forward/G2_promotion_protocol.md` (the two-band promote
  protocol + the +0.144 derivation; the bar every graduate is judged against)
- `.cca/catalogue/O0/20260627_mlops/research/forward/G1_ingest_deploy.md` (the W6 node-ingest pattern S1
  must follow + the "0 net-new analysis observations" finding)
- `.cca/catalogue/O0/20260627_mlops/research/forward/G3_l3_grounding.md` (L3 power analysis + the live
  2026 Albion fetch design; relevant to S2 prey signals)
- `.cca/catalogue/O0/20260627_mlops/research/SYNTHESIS_L2_L3.md` (the prior research synthesis + corrected
  blocker map: burstiness + scoring resolution, NOT the 3-node ingest)

## 4. Methodology (the modeling canon)

- `docs/methodology/FORECAST_KERNELS.md` (kernel model form, current covariates, effort-bias principle)
- `docs/methodology/CALIBRATION_STUDIES.md` (LNP/PSTH/GLM, the leveled gate plan, time-rescaling GOF)

## 5. Code surface the subagents read (reads only; nothing writes/deploys)

- `src/aws_backend/ingest_multistation.py` (`EXTRA_NODES`, the cached-index ingest pattern -- S1's grounding
  template), `src/aws_backend/timeseries.py` (S3 + memory stores)
- `src/aws_backend/sources/` (`orcahello_history.py`, `salmon.py`, `noaa.py`) -- existing source adapters
- `modeling/studies/common.py` (STATION_COORDS), `modeling/tide_harmonic.py` (tracked harmonic example)
- `modeling/fit_kernels.py` (local-only) + `modeling/studies/level2_multistation.py` -- the fit/scoring a
  graduate would later plug into (reference only; no fit runs in this campaign)

## 6. Evidence / artifacts (latest verdicts)

- `modeling/studies/reports/level2_multistation.json` (the multi-station frontier evidence)
- `modeling/studies/reports/L2_burstiness_timing.json`, `l2_data_volume.json` (RA-RF research outputs)
- `data/models/fit_report.json` (local-only; the served fit, confidence 0.0)

## 7. Where findings land + gates / environments

- Findings dir (subagents create on launch):
  `.cca/catalogue/O0/20260627_mlops/research/signal_modeling/` (S1/S2/M1/M2/M3 + SYNTHESIS)
- `tools/waves/run-gate.sh mlops-gate` (local; stdlib ladder + honesty guard) -- must stay green/0.0
- Heavy fit/studies: `.venv-modeling/bin/python`. Stdlib ladder: system `python3`. AWS store: bucket +
  region in HANDOFF_CHARTER §B.5. DFO/external fetch: aimez EC2 `i-04a649f91274e9fce` (§B.9).

## 8. Repo map (orientation)

- `modeling/` offline fit + studies (pipeline local-only; studies + reports tracked). `src/aws_backend/`
  FastAPI backend, sources, ingest, serving, promotion. `docs/methodology/` modeling canon.
  `.cca/catalogue/O0/` waveset homes (campaign: `20260627_mlops/`; this handoff:
  `20260627_signal-modeling-launch-handoff/`; prior rotation: `20260627_mlops-handoff/`). `tools/`
  harnesses + gates. The repo also has large untracked demo/figures/voice trees -- never `git add -A`.
