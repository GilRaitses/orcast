# Orchestrator dispatch prompt

Paste the block below into the fresh thread.

```
You are resuming as the orcast-lane orchestrator (O0). Hydrate from files, not from any chat
transcript linearly.

Read in order before acting:
1. .cca/catalogue/O0/20260627_orcast-handoff/HANDOFF_CHARTER.md
2. .cca/catalogue/O0/20260627_orcast-handoff/ORCHESTRATOR_NOTES.md
3. .cca/catalogue/O0/20260627_orcast-handoff/HYDRATION_PACKET.md
4. docs/methodology/FORECAST_KERNELS.md and CALIBRATION_STUDIES.md

Locked, do not reopen (restated): forecast effective confidence is 0% and shown with the gate
caveat; never render sharper than the gates support; confirmed sighting = cross_validation
verified/likely; estimate temporal kernels from acoustic detections with a log E offset, visual
sightings are validation + s_space only; acoustic is not whale GPS; DTAG is partnership-gated and
the feeding classifier is not_trained; CI needs python-multipart (fixed locally, uncommitted);
the OrcaHello history API 403s intermittently so use the cached index; the console is at / but the
provenance modal is on /explore + MapHero (demo capture is blocked on a target decision).

Active lanes: DEMO capture (blocked, needs operator target decision), MLM L0/L2/L3 + PIML design,
MLO platform (operator/deploy-gated), BSIDE B-SKILLS onward, and committing this session's work
(operator-gated). Do NOT commit or push without an explicit operator ask. Do not write pax
surfaces. Do not read the chat transcript linearly.

Return the section H ack from HANDOFF_CHARTER.md before acting.
```

## More context (need to file, not transcript)

| Need | File |
|------|------|
| Locked decisions + footguns | `.cca/catalogue/O0/20260627_orcast-handoff/HANDOFF_CHARTER.md` (B) |
| Intent, PIML strategy, critique, literature | `.cca/catalogue/O0/20260627_orcast-handoff/ORCHESTRATOR_NOTES.md` |
| Modeling canon | `docs/methodology/FORECAST_KERNELS.md`, `CALIBRATION_STUDIES.md` |
| Current gate numbers | `data/models/fit_report.json`; `modeling/studies/reports/` |
| Candidate data foundation | `.cca/catalogue/O0/20260627_forecast-candidates/` |
| Demo capture blocker | `.cca/catalogue/O0/20260627_demo-waveset/STEP_LOG.md` |
| Whale-tagger API | `src/aws_backend/routers/dtag.py`; `.cca/catalogue/O0/20260627_bside-build/` |
| Gate runner | `tools/waves/run-gate.sh` (`mlops-gate`) |
| Uncommitted state | HANDOFF_CHARTER.md (G) |
