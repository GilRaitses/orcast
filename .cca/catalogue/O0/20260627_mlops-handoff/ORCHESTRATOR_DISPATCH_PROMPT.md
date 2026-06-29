# Orchestrator dispatch prompt (forecast ML-ops lane)

Paste the block below into the fresh thread.

```
You are resuming as the orcast forecast ML-ops orchestrator (O0, MLM + MLO). Hydrate from
files, not from any chat transcript linearly.

Read in order before acting:
1. .cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md
2. .cca/catalogue/O0/20260627_mlops-handoff/HYDRATION_PACKET.md
3. .cca/catalogue/O0/20260627_orcast-handoff/ORCHESTRATOR_NOTES.md
4. docs/methodology/FORECAST_KERNELS.md and CALIBRATION_STUDIES.md

Locked, do not reopen (restated): effective confidence is 0% and only rises on a passing gate
plus a recorded supervisor decision (src/aws_backend/promotion/supervisor.py); temporal kernels
come from acoustic detections with a log E offset, visual sightings are validation + s_space only,
acoustic is not whale GPS; insufficient coverage is reported withheld, never faked. The AWS
timeseries store is bucket 198456344617-us-west-2-orcast-aws-backend-raw-payloads in us-west-2
(NOT the config default); when you refit against S3 you MUST disable the production artifact upload
(fit_kernels._maybe_write_s3 = no-op or write_outputs=False) so a refit cannot auto-promote
confidence. The modeling/ fit pipeline and data/models/ are local-only (untracked); only
modeling/studies/** + reports and modeling/tide_harmonic.py are tracked; run heavy fits/studies
with .venv-modeling, the stdlib ladder and mlops-gate under system python3. OrcaHello 403s and
fetch_history is oldest-first, so use the reviewed-outcome endpoints + the cached indexes for
multi-station. No commit or push without an explicit operator ask; surgical staging only.

Current frontier: L0 PASS, L1 PASS, L2 FAIL at 0% but the multi-station experiment flips held-out
skill POSITIVE (+0.078); the two remaining L2 blockers are time-rescaling (per-station effort /
log E) and cross-station kernel consistency. L3 withheld pending summer PRESENCE-DAYS from new
in-region nodes (SYN/G3; the Albion Chinook feed is already real, so L3 is presence-day/power-gated,
not feed-gated). Next: TB1 node dry-run (Port Townsend/Bush Point) + TA1 MMPP in parallel; productionize
multi-station (ingest the 3 extra Orcasound nodes into the acoustic_detections stream), fix effort so
time-rescaling passes, lift cross-station consistency; Albion refresh (TB3) is supporting-only.
MLO platform is operator/deploy-gated. The 3d-twin, DEMO, and BSIDE
lanes are out of scope (3d-twin has its own orchestrator; DEMO/BSIDE are dormant). Do not read the
chat transcript linearly.

Return the section H ack from HANDOFF_CHARTER.md before acting.
```

## More context (need to file, not transcript)

| Need | File |
|------|------|
| Locked decisions + footguns | `.cca/catalogue/O0/20260627_mlops-handoff/HANDOFF_CHARTER.md` (B) |
| Ordered read list | `.cca/catalogue/O0/20260627_mlops-handoff/HYDRATION_PACKET.md` |
| MLM/MLO charters + trace | `.cca/catalogue/O0/20260627_mlops/` |
| Frontier evidence | `modeling/studies/reports/level2_multistation.json` |
| Sources to aggregate | `.cca/catalogue/O0/20260627_wildlife-sources/WILDLIFE_SOURCES_REGISTER.md` |
| Multi-station study | `modeling/studies/level2_multistation.py` |
| AWS refit recipe + upload-disable | HANDOFF_CHARTER.md (B.4, B.5) |
| Gate runner | `tools/waves/run-gate.sh` (`mlops-gate`, local) |
| Uncommitted/local-only state | HANDOFF_CHARTER.md (G) |
