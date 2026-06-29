# DE1/DE2/DE3 text-only drift remediation log (step 5)

Orchestrator O0 (integrate / measure-on-served / promote). Date: 2026-06-27. Repo `main` at `9a00e15`.
Text-only (prose + machine-readable charter + code COMMENTS); **no model change**. Hawkes preserved as
an event-level GOF diagnostic everywhere. `mlops-gate` ALL PASS at served confidence 0.0;
`data/models/fit_report.json` untouched. Effective confidence 0.0.

## Applied (the plan's named priorities + the prioritized DE lists)

### LGCP supersession (DE1 #1-3, DE3 #1-2)
- `research/signal_modeling/M2_nonlinear_physics.md`: top SUPERSEDED banner; section-8 table row 2
  reclassified `PROMISING AT OUR N / GO` -> `DEAD-END AT OUR N / NO-GO at current N`; section-9 split
  moved LGCP to NEEDS-FAR-MORE-DATA and added hierarchical NB partial pooling (TA2) as the promising-now
  substitute; Return summary go/no-go reconciled with SYN section 2.
- `20260627_orcast-handoff/ORCHESTRATOR_NOTES.md` section 4: LGCP backbone reframed to a conditional
  prototype / dead-end at current N, with TA2 partial-pooling NB as the default; section 6 experiment 3
  re-gated to `block_cv` fold-stable skill (not PIT/in-sample), sequenced after MMPP/NB.

### wave_shape.yml objectives (DE1 #4, #9)
- `20260627_mlops/wave_shape.yml` `signal_modeling_research.objectives`: M1_sparse / M2_nonlinear /
  M3_derived now point to SYNTHESIS_signal_modeling.md sections 1-2 as authoritative, name the
  dead-ends (LGCP/GP, ZI/hurdle count upgrade, Hawkes-as-skill, full PINN/reservoir/ESN/EDM/neural-TPP),
  and state the B.2 covariate roles (terrain = `s_space`-only; subtidal currents = SalishSeaCast residual
  only, HF radar NO-GO; SST = season-orthogonalized gradient only).

### CUTI/BEUTI WITHHELD (DE1 #5, DE3 #13)
- `20260627_wildlife-sources/WILDLIFE_SOURCES_REGISTER.md` Tier-1 row: CUTI/BEUTI marked
  **WITHHELD / NO-GO** (product covers 31-47 N; region ~48.5 N out of coverage; require a locally
  computed in-region index if ever wanted). Also covered in `wave_shape.yml` M3_derived and
  `M3_derived_covariates.md`.

### L3 = presence-days reframe (DE3 #3-9, #14; DE1 #6-8)
- `20260627_mlops-handoff/`: `HANDOFF_CHARTER.md` (A purpose, C registry M-L3 row, D primer, E dispatch
  rows), `README.md`, `ORCHESTRATOR_DISPATCH_PROMPT.md`, `HYDRATION_PACKET.md` -- all updated from
  "L3 needs a real Chinook feed" to G3/SYN: L3's binding lever is summer presence-days from new in-region
  nodes (TB1/TB4); the Albion feed is already real/stock-aligned; refresh (TB3) is supporting-only; L3
  stays WITHHELD on the LOYO/power bar, not the feed.
- `WILDLIFE_SOURCES_REGISTER.md`: SUPERSEDED banner + acquisition-order #2 (real Chinook index) marked
  MET/supporting-only; SYN cross-link added.
- L3 GATE SPLIT footnotes added to `20260627_mlops/MLM_CHARTER.md` (M-L3 row),
  `docs/methodology/METHODOLOGY.md` (section 7.2 L3 row), `docs/methodology/CALIBRATION_STUDIES.md`
  (Level 3): `k_salmon` judged on the temporal acoustic CV; static bathymetry enters `s_space` ONLY and
  does NOT move the +0.144 temporal acoustic gate at the 4-station cluster.

### HF-radar / currents role (DE1 #10)
- `research/signal_modeling/M3_derived_covariates.md` section 0.3: HF radar struck as a candidate
  ("SalishSeaCast only; HF radar NO-GO in-region, S2 section 3 #8").

### Hawkes-as-GOF-diagnostic preserved + clarified (DE1 #11-12, DE2 M2)
- `20260627_mlops/README.md` and `20260627_mlops/RESEARCH_DISPATCH.md`: "Hawkes timing fix" / "hurdle
  terms" reworded -- bin-level timing gate with Hawkes retained as an event-level GOF diagnostic ONLY;
  "hurdle" = onset-dedup diagnostic, NOT a NB->ZI/hurdle count upgrade (a dead-end).
- `20260627_orcast-handoff/ORCHESTRATOR_NOTES.md` section 4: ZI/hurdle bullet split -- TA2 presence-hurdle
  REFRAME (GO) vs ZI/hurdle COUNT upgrade (NO-GO).
- `modeling/fit_kernels.py` (COMMENT-only, DE2 row M2): the stale "ADOPT_BIN_LEVEL_TIMING_GATE NOT
  adopted / flag defaults OFF" comments at the `bin_count_gof` readout and `_bin_level_timing_readout`
  docstring/note synced to the actual `ADOPT_BIN_LEVEL_TIMING_GATE = True` (2026-06-27 supervisor
  decision). No behavior change; the Hawkes diagnostic containment is unchanged (DE2 confirms it is
  isolated in `_time_rescaling_report`, `diagnostic_only: True`).

### PINN legacy copy (DE1 #13)
- `docs/README.md`: the two "PINN" marketing lines relabeled to the kernel-forecast (LNP/GLM) program
  with a note that "PINN" is legacy hackathon copy, not the modeling approach (per SYN/M2).

## Deliberately NOT changed (out of "text-only, no model change" scope)

- DE2 P1 #1 (API diagnostic remapping of `routers/kernel.py` / `exploration/tools.py` to
  `diagnostics.self_exciting_hawkes`) and P1 #3 (regression guard test) are CODE changes -> belong to a
  later integrate wave, not this text-only pass. Hawkes is already correctly contained (DE2 confirms).
- `docs/methodology/methodology.tex` (LaTeX SOURCE of the rendered PDF): left untouched to avoid creating
  md/tex/pdf drift; the canonical doc DE1 #7 named is `METHODOLOGY.md` (updated). The .tex L3 gate
  language should be synced when the PDF is next re-rendered.
- DE2 L4 (`time_rescaling_diag.json` aspirational-Hawkes wording) is a GENERATED static artifact; a study
  README caveat is the right home and is deferred-low. DE2 L6 is a CONFIRM (NOAA currents = `k_tide`
  phase only; SalishSeaCast TB5-gated) -- already true, no edit needed.
- DE3 P3 (#16) low-priority pointer left as-is.

## Rails confirmed

No model/behavior change (prose + YAML + code comments only). No deploy, promotion, ingest, store write,
S3 write, or commit. Hawkes-as-GOF-diagnostic preserved throughout. `mlops-gate` ALL PASS at served
confidence 0.0; `data/models/fit_report.json` untouched; `modeling/` stays untracked. Effective
confidence 0.0.
