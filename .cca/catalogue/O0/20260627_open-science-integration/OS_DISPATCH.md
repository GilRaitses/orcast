# OS waveset dispatch (background subagent hydration + task)

Lane O0, forecast ML-ops. Read this in full, then execute the lanes in `WAVESET_CHARTER.md` section 2
IN PRIORITY ORDER, one findings doc per lane, then `OS_SYNTHESIS.md`. After each lane, append a
STEP_LOG entry and STOP for the orchestrator to review before the next lane (the orchestrator resumes
you). You are managed and steered by the O0 orchestrator thread.

## Hard rails (apply to every lane)

- Effective confidence stays 0.0. Nothing promotes. You RECOMMEND and SPEC only.
- READ-ONLY research (web + repo reads) + light bounded reachability probes. You WRITE ONLY your named
  findings doc under `.cca/catalogue/O0/20260627_open-science-integration/` (or `research/signal_modeling/`
  where the charter says "extends Sx").
- NO convergence-file edit (`modeling/**`, `src/aws_backend/**`), NO served-store / S3 write, NO
  production fetch-that-writes, NO ingest, NO deploy, NO promotion, NO commit, NO `git add`.
- No fabricated numbers (B.2/B.3). Every count/skill/coefficient is MEASURED from a cited source or
  marked NOT-MEASURED / ESTIMATED. Record license + provenance + reachability for every source.
- Judge any modeling claim by held-out fold-stable CV mean-deviance-skill toward +0.144, never
  in-sample fit.
- Keep `tools/waves/run-gate.sh mlops-gate` green at served confidence 0.0 if you run it (you should
  not need to; you make no model change).
- Style: plain, direct, observation-driven. Do not use the double-hyphen dash in prose; use commas,
  colons, or parentheses. Mark every unmeasured quantity explicitly.

## Doc conventions (match the existing graduation docs)

Each findings doc opens with: agent + date + repo + a one-line scope/rails statement (this doc only,
no edit/fetch-to-write/ingest/convergence-edit/deploy/promotion/commit, effective confidence 0.0).
Then numbered sections, a PATCH-SPEC section for the later single-editor integrate (no file edited
now), a DE drift note if it touches a DE-flagged doc, and a Return summary. Cite DOIs/URLs.

## Source pointers from the 2026-06-27 scan (verify license + reachability per source)

OS1 (effort / detectability log E):
- OSF `https://osf.io/6ctjq/` : open SPL + propagation-loss coefficient files behind the DFO Salish
  Sea detection-range study.
- PLOS One 2025, DOI `10.1371/journal.pone.0331942` : Monte Carlo detection-range framework for DFO
  Salish Sea listening stations (frequency-dependent source levels, ambient, propagation loss, per
  300 Hz band). Read for the method; map it to a per-(station,day) detection-probability -> `log E`.
- ONC Oceans 3.0 `https://data.oceannetworks.ca/SearchHydrophoneData` : hydrophone device
  data-availability (uptime/duty) for the effort mask. Token-gated; reachability NOT-MEASURED here.
- Repo anchors: `modeling/effort.py`, `modeling/design.py` (`build_design` exposure path),
  `modeling/ais_noise.py` (the TA3 detectability factor already landed as a no-op), and the TB4 verdict
  `.cca/catalogue/O0/20260627_integrate-promote-launch-handoff/TB4_PRESENCE_DAY_COUNT.md`.

OS2 (open node JJA presence screen):
- NCEI Passive Acoustic Archive `https://www.ncei.noaa.gov/products/passive-acoustic-data`; DCLDE-2027
  Killer Whales (NOAA Big Data Project on GCS `gs://noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/`,
  >225k annotations, 23 locations). The `Annotations.csv` schema is already known (see TB4 verdict).
- DORI-ONC `https://huggingface.co/datasets/DORI-SRKW/DORI-ONC` (CC-BY, ~1 TB, ONC).
- 30-year SRKW curation literature map: arXiv `2602.09295` (past per-deployment SRKW day-counts:
  Swiftsure 605 days 2018-2020, Lime Kiln 46 days 2018, northern Salish Sea 96 winter days 2015-2017,
  OrcaSound 122 public whale-days 2018-2022). Use these to ESTIMATE net-new JJA days per source.
- Repo anchors: `research/signal_modeling/S1_node_sources.md`, the served station set, and the W6
  "0 net-new" lesson (re-shelving the same cache adds nothing).

OS3 (forecast standards + scoring):
- EFI standards `https://ecoforecast.org/ecological-forecast-standards/`, repo `eco4cast/EFIstandards`
  (EML extension, netCDF/CSV tiers, FAIR archiving with DOI before observations land, R/Python vignettes).
- `scoringRules` (R) `https://cran.r-project.org/web/packages/scoringRules/`; `scoringrules` +
  `xskillscore` (Python) for CRPS / log score.
- Repo anchors: `modeling/validation/crossval.py` (the deviance-skill + PIT), `_confidence_from_gates`
  and the served disclosure in `modeling/fit_kernels.py`, `src/aws_backend/promotion/supervisor.py`.

OS4 (inlabru cross-check):
- inlabru `https://inlabru-org.github.io/inlabru/` (MEE DOI `10.1111/2041-210X.13168`), the SVC NB
  vignette is the template (per-station NB with a log-effort-hours covariate). R-INLA SPDE/LGCP is the
  POST-node-expansion path only; spatial LGCP at the current 4-station N is the SYN dead-end.
- Repo anchors: the landed `modeling/estimator.py` (`fit_glm` partial_pool + ridge), the TA2 verdict
  (served +0.155, PIT 0.61), `modeling/validation/crossval.py`.

OS5 (open detector cross-check):
- PAMGuard `https://www.pamguard.org/` (+ Tethys), ANIMAL-SPOT / ORCA-SPY (Sci Rep
  `10.1038/s41598-023-38132-7`), Ketos (MERIDIAN), Koogu.
- Repo anchors: the L0 detector ROC study, the OrcaHello feed posture.

## Per-lane exit bar

As in `WAVESET_CHARTER.md` section 2. Each lane lands a findings doc with: sourced + license + reachability,
a MEASURED-or-NOT-MEASURED quantity, a PATCH-SPEC for the later single-editor integrate, a DE drift note
where applicable, and a GO/NO-GO. Then a STEP_LOG line and STOP for orchestrator review.

## Return contract

After each lane, return: the doc path, the one-line GO/NO-GO, the single highest-value next action, and
any operator gate you hit (token, license, reachability). Do not proceed to the next lane until resumed.
