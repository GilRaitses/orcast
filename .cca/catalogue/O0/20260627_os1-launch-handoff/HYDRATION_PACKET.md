# Hydration packet, OS1 + beyond orchestrator

Ordered read list for the incoming thread. Read in order; do NOT read the chat transcript linearly.
Paths are repo-relative to `/Users/gilraitses/orcast`.

## 1. Governance / canon (read first)

- `.cca/catalogue/O0/20260627_os1-launch-handoff/HANDOFF_CHARTER.md` (this rotation's authority: §B
  locked/measured, §D the "beyond" decision, §H the ack)
- `.cca/catalogue/O0/20260627_open-science-integration/WAVESET_CHARTER.md` (the OS waveset frame +
  honesty rails the lane inherits)

## 2. The measured OS1 result (read before deciding anything)

- `.cca/catalogue/O0/20260627_open-science-integration/OS1_BUILD_NOTE.md` (the full technical
  provenance: OSF data, calculator + the sign-bug fix + validation table, ONC dead-end, OrcaSound DSP,
  391-day extraction, transducer, the first-measurement defect, the robustness fix, the kappa-sweep
  table, and the NO-GO conclusion)
- `data/external/os1_ambient/os1_skill_result.json` (the machine result: offset summary + full kappa
  sweep + conclusion)
- `.cca/catalogue/O0/20260627_open-science-integration/STEP_LOG.md` (the lane trace; the last entry is
  the OS1 build+measure arc)
- `.cca/catalogue/O0/20260627_open-science-integration/OS1_effort_detectability.md` (the original
  research finding that scoped OS1)

## 3. Beyond OS1 (the OS graduates, if the operator wants the next lever)

- `.cca/catalogue/O0/20260627_open-science-integration/OS_SYNTHESIS.md` (ranked graduation plan +
  dead-ends + consolidated operator gates; OS2 Tekteksen/SIMRES is the top open net-new lever)
- `.cca/catalogue/O0/20260627_open-science-integration/OS2_open_node_screen.md` (the net-new summer
  presence-day sources)

## 4. The OS1 code surface (gitignored; reads + reruns)

- `data/external/osf_6ctjq/validate_detection_range.py` (calculator validation)
- `data/external/os1_ambient/extract_daily_ambient.py` (OrcaSound audio -> daily band SPL; run per
  station to get other-station ambient for the §D option-1 confirmation)
- `data/external/os1_ambient/transducer.py` (band SPL -> robust log E_det offset)
- `data/external/os1_ambient/measure_os1_skill.py` (CV mean-deviance-skill with vs without the offset)
- `data/external/os1_ambient/ambient_orcasound_lab.json` (391-day ambient),
  `osf_eastpoint_summer_median.npy` (anchor)

## 5. The served model the offset plugs into (reference)

- `modeling/design.py` (`build_design`; the `exposure` column + `noise_by_station`/`ais_kappa` effort
  wire that OS1's offset mirrors)
- `modeling/validation/crossval.py` (`block_cv`; the mean-deviance-skill metric)
- `modeling/estimator.py` (`make_fit_predict`, families)
- `modeling/effort.py` (the `log E` effort term semantics OS1 extends)

## 6. Environments / footguns

- Run with system `python3` and `PYTHONPATH=/Users/gilraitses/orcast`. `aws`, `ffmpeg` present;
  `soundfile`/`librosa` absent (use ffmpeg->wav->scipy). The served S3 store + upload-disable rule are
  in HANDOFF_CHARTER §B.7. `.env` has `ONC_API_TOKEN` (unused; gitignored). Never `git add -A`.

## 7. Repo map (orientation)

- `data/external/` gitignored OS1 artifacts. `modeling/` offline model (local-only pipeline).
  `src/aws_backend/` backend + effort/serving. `.cca/catalogue/O0/` waveset homes (OS lane:
  `20260627_open-science-integration/`; this handoff: `20260627_os1-launch-handoff/`).
