# OS waveset step log

Lane O0. Append one entry per lane completion. Effective confidence 0.0 throughout.

- 2026-06-27: Waveset CHARTERED. `WAVESET_CHARTER.md`, `OS_DISPATCH.md`, `wave_shape.yml` written.
  Background subagent dispatched on OS1 (effort/detectability `log E`), highest value (closes the
  TB4/TA3 NOT-MEASURED denominator). Orchestrator steers: review each findings doc, resume to next lane.
- 2026-06-27: OS1 COMPLETE. `OS1_effort_detectability.md` written. GO (spec/build-gated) on the open
  detection-range `D_det` detectability term as a fixed per-(station,day) effort multiplier on `log E`
  (third factor after uptime and TA3 `D_ais`, zero presence params); NO-GO on skill credit / ingest until
  the OSF data license is confirmed, an ONC-token (or geoacoustic-transferred) ambient series lands, and
  fold-stable held-out CV-skill is measured. MEASURED: OSF `6ctjq` read-reachable via the published
  view-only token (holds `PL_coeffs.zip` ~242 KB Eq-2 A/n, `SPL_files.zip` ~42.8 MB ambient+source SPL),
  PLOS One DOI 10.1371/journal.pone.0331942 method fully characterized, ONC UI 200 / ONC API token-gated.
  Operator gates: OSF license untagged, ONC Oceans 3.0 token, served-station ambient + detector DT.
  Read-only research + bounded probes only; no edit/fetch-to-write/ingest/deploy/promotion/commit.
  Effective confidence 0.0. STOP for orchestrator review before OS2.
- 2026-06-27: OS2 COMPLETE. `OS2_open_node_screen.md` written (extends S1). GO (conditional,
  region-expansion + effort gated) on the DCLDE-2027 CC-BY-4.0 open corpus as the net-new summer
  presence-day source; NO-GO on skill credit until per-deployment effort/`log E` (OS1 term + ONC/SIMRES
  duty cycle) is measured; NO-GO on OrcaSound (re-shelving, W6) and DORI-ONC (net-new NOT-MEASURED, ~1 TB,
  amateur labels Jaccard 0.7 over data DCLDE already covers). TOP-RANKED net-new JJA source (MEASURED):
  Tekteksen / SIMRES Boundary Pass off Saturna Island = 11 JJA-2022 SRKW-certain presence-days (largest
  single net-new summer payload, alone bigger than TB4's 6). Open-corpus net-new JJA total ~26 days. DCLDE
  screen re-used TB4's `/tmp` scratch read-only and cross-checks TB4 exactly (StGeo 6, BoundaryPass 0).
  Operator gates: region expansion (all strong sources out of SAN_JUAN_BOUNDS), effort NOT-MEASURED,
  OrcaSound label license CC-BY-NC-SA. Read-only; no store write/ingest/deploy/promotion/commit.
  Effective confidence 0.0. STOP for orchestrator review before OS3.
- 2026-06-27: OS3 COMPLETE. `OS3_forecast_standards_scoring.md` written. GO (spec/build-gated) on (a) an
  EFI-compliant metadata sidecar for the served forecast and (b) a report-only NB2-CRPS block alongside
  the deviance-skill gate and PIT, both byte-identical no-op-default additions that leave
  `_confidence_from_gates`, the 0.6/+0.144 promotion bar, and the Hawkes GOF untouched; NO-GO on treating
  it as a skill lever (does not move +0.144, earns no confidence). Licenses MEASURED: EFIstandards
  BSD-2-Clause, scoringrules (Py) Apache-2.0 `crps_negbinom`, scoringRules (R) GPL>=2 `crps_nbinom`,
  xskillscore Apache-2.0 (ensemble only). Served NB2 count predictive maps to parametric closed-form CRPS
  via the existing `_nbinom_nq` (n,p); no ensemble needed. Operator gate: FAIR DOI archiving
  (forecast-before-observations + code DOI + optional container) is the only EFI field set not already
  filled. Read-only; no edit/fetch-to-write/ingest/deploy/promotion/commit. Effective confidence 0.0.
  STOP for orchestrator review before OS4.
- 2026-06-27: OS4 COMPLETE. `OS4_inlabru_crosscheck.md` written. GO (spec/benchmark, operator-gated on an
  R runtime) on running the inlabru `iid`-random-intercept NB cross-check against the landed statsmodels
  TA2 (same 4-station design, same `block_cv` folds, same deviance-skill metric, plus CPO/WAIC and
  calibrated intervals); NO-GO on any served swap or skill credit (expected to REPRODUCE, not beat, the
  served +0.1547; earns no confidence). LGCP/SPDE at the current 4-clustered-station N stays a NO-GO
  dead-end until spatially separated nodes (TB1/TB4/OS2) land. MEASURED correspondence: the landed
  `partial_pool` ridge `1/(tau^2*nobs)` on station dummies IS the MAP of inlabru's `f(station,
  model="iid")` precision `1/tau^2`; inlabru adds the full posterior + WAIC/CPO/PIT. Licenses: inlabru
  CRAN GPL>=2 (v2.14.1); R-INLA GPL, NOT on CRAN (404), installs from r-inla.org (reachable 200). Operator
  gate: R runtime + R-INLA install (R-runtime reachability NOT-MEASURED; `.venv-modeling` is Python). MEE
  paper DOI 10.1111/2041-210X.13168. Read-only; no edit/fetch-to-write/ingest/deploy/promotion/commit; no
  fit run. Effective confidence 0.0. STOP for orchestrator review before OS5.
- 2026-06-27: OS5 COMPLETE. `OS5_open_detector_crosscheck.md` written. GO (spec/runbook, operator-gated on
  model weights + audio + compute) on running an open detector (ANIMAL-SPOT/ORCA-SPOT pretrained orca,
  GPL-3.0, standalone or via the PAMGuard Raw Deep Learning Classifier) on a public OrcaSound node to
  produce an independent L0 ROC (AUC + 1000-sample bootstrap CI, comparable to the served OrcaHello AUC
  0.8794 / d' 1.6197) plus an OrcaHello-vs-open Jaccard, and on a DCLDE/Tekteksen-SIMRES deployment to
  realize detector-independence at an OS2 net-new node. NO-GO on any temporal-skill credit (not a +0.144
  lever; outputs feed the L0 ROC and OS2 presence-day extraction, never the kernels; earns no confidence);
  NO-GO on trusting out-of-domain pretrained output as truth (NRKW/Orchive weights are out-of-domain for
  SRKW Salish Sea; domain shift NOT-MEASURED, must be characterized). Stack licenses MEASURED via repo API:
  PAMGuard / ANIMAL-SPOT / ORCA-SPOT / ORCA-SPY / Koogu all GPL-3.0; Ketos GPL-3.0 per MERIDIAN (SPDX not
  exposed by the GitLab probe). Sci Rep DOIs 10.1038/s41598-019-47335-w and 10.1038/s41598-023-38132-7;
  weights via Edmond DOI 10.17617/3.KQPPXF. Operator gates: model weights (out-of-domain), audio
  access/size (NOT-MEASURED), compute (PyTorch CPU feasible, GPU optional, NOT-MEASURED). Read-only; no
  detector run; no edit/fetch-to-write/ingest/deploy/promotion/commit. Effective confidence 0.0. STOP for
  orchestrator review; do NOT start OS-SYN.
- 2026-06-27: OS-SYN COMPLETE; OS WAVESET COMPLETE. `OS_SYNTHESIS.md` written (ranked graduation plan +
  dead-ends + consolidated operator gates + single next action), and `WAVESET_CHARTER.md` section 5 status
  set to COMPLETE (the single permitted charter edit). Top 3 graduates: (1) OS1 `D_det` effort wire
  (keystone, closes the TB4/TA3 `log E` denominator, maps to the TA3 effort wire); (2) OS2 net-new summer
  nodes led by Tekteksen/SIMRES (MEASURED 11 JJA-2022 days, strongest open lever, maps to TB4/TB1 ingest +
  region expansion); (3) OS3 NB2-CRPS report-only block (cheapest, no gate, in-repo no-op). Consolidated
  gates: OSF reuse license (OS1), ONC token (OS1/OS2), region expansion outside SAN_JUAN_BOUNDS (OS2),
  R+R-INLA runtime (OS4), open-detector weights/audio/compute (OS5), FAIR DOI archiving (OS3). Single
  highest-value next action: confirm the OSF `6ctjq` reuse license + ONC token to unblock the OS1 effort
  frame on which the de-biased kernels and honest OS2 scoring depend. Dead-ends held: spatial LGCP at
  current N, DORI-ONC for now, OrcaSound re-shelving, CRPS/EFI/inlabru as skill levers, out-of-domain
  detector output as truth. Nothing promoted; +0.144 bar and `_confidence_from_gates` unchanged; effective
  confidence 0.0. Read-only; no convergence edit/fetch-to-write/ingest/deploy/promotion/commit. WAVESET
  CLOSED; STOP.

- 2026-06-27: OS1 BUILD + MEASURE (post-research; operator authorized internal use of OSF data and said
  "assume license confirmation"). Full provenance in `OS1_BUILD_NOTE.md`. Arc:
  1. OSF `6ctjq` fetched (PL_coeffs.zip + SPL_files.zip) to gitignored `data/external/osf_6ctjq/`. License
     still untagged on the node; operator approved internal-only use (do NOT redistribute / publish the raw
     data or derived artifacts without author confirmation).
  2. Detection-range calculator built from Eq 1-5 (transcribed from the article EQUATION IMAGES, not the
     lossy text). Found + fixed a sign bug (`-A` vs `+A` in Eq 4, ~9 dB term -> ranges ~100x too large).
     VALIDATED vs the paper's East Point summer ranges within ~5-15% (14,967 m low-noise / 1,425 m high-noise
     at 10 m vs paper ~15,500 / ~1,640). `osf_6ctjq/validate_detection_range.py`. Calculator TRUSTED.
  3. ONC East Point ambient PROXY REJECTED (not a license/token problem -- data geometry): no ONC cabled
     hydrophone at East Point or in Haro Strait; nearest continuous node ECHO3 (Strait of Georgia) is
     ~35-55 km away in a different sub-basin, raw audio only, and returned zero archive files on the standard
     query; SEVIP ended 2020-03 and exposes no SPL series. ONC token IS stored/working in `.env`
     (`ONC_API_TOKEN`) but went unused after the proxy was rejected.
  4. Pivot to OrcaSound DSP (operator chose the faithful path): audio public on
     `s3://audio-orcasound-net/<node>/hls/<session>/live*.ts` for all 3 served nodes, ~110 sessions/month
     across every detection-heavy month 2020-2026. 48 kHz AAC -> ffmpeg -> scipy Welch -> 46x300 Hz bands;
     proven ocean-like spectrum (highest at 1 kHz). `os1_ambient/extract_daily_ambient.py`.
  5. EXTRACTION complete: orcasound_lab 2020-09..2021-09, 391 days (4 segments/day), all with audio.
     `os1_ambient/ambient_orcasound_lab.json`.
  6. Transducer: uncalibrated band SPL -> per-band anchor to OSF East Point summer median
     (`osf_eastpoint_summer_median.npy`) -> Eq 4-5 (East Point summer PL, 15 m) -> detection area ->
     log E_det = log(area/median). `os1_ambient/transducer.py`.
  7. First measurement was a DEFECT not a result: log E_det std ~5.0, p99 ~ +24.7 (area swings ~1e10x), CV
     mean -1.4e10 (median spuriously up). Cause: 4-seg/day band noise + uncapped R_max + max-over-46-bands.
  8. ROBUSTNESS FIX (this step): smooth daily spectrum across frequency (window 5), clamp R_max to
     [500 m, 20 km], winsorize offset to +/-2. std -> 1.50, physical range, median R_max 7.5 km.
  9. RE-MEASURE (negbin; diel+lunar+season; 5 folds; orcasound_lab; 725 det; 8563 bins; 99.2% coverage)
     with a kappa sweep on the offset scale: mean CV deviance-skill = +0.2776 (k=0 baseline), +0.2747 (0.1),
     +0.2608 (0.25), +0.1989 (0.5), +0.0821 (0.75), -0.1300 (1.0). Mean DECREASES monotonically with kappa;
     median wobbles up slightly at k 0.1-0.25 then falls; no k beats baseline on the mean bar.
  10. VERDICT: NO-GO on served skill (measured). OS1 detectability-as-effort-offset does not improve, and at
     full scale degrades, held-out CV mean-deviance-skill on the dominant station. The validated calculator +
     proven DSP pipeline are reusable for future spatially-separated nodes with co-located ambient (OS2/TB).
     Nothing promoted; effective confidence 0.0. Result artifact `os1_ambient/os1_skill_result.json`.
     Rotation package for the next orchestrator: `.cca/catalogue/O0/20260627_os1-launch-handoff/`.

- 2026-06-27: OS1 CLOSED + OS2 CHARTERED (operator decision). Operator chose §D option 4: CLOSE OS1 as a
  measured NO-GO and bank the validated detection-range calculator + proven OrcaSound DSP pipeline for the
  spatially-separated OS2/TB nodes where co-located ambient exists and detectability genuinely varies. OS1
  lane is CLOSED; nothing promoted; effective confidence 0.0. OS2 picked as the next lever but LAUNCH-HELD:
  operator chose "charter only, hold launch until the region-expansion + effort gates are confirmed".
  Wrote `OS2_BUILD_CHARTER.md` (status CHARTERED_LAUNCH_HELD) + `OS2_wave_shape.yml`. The charter records
  why OS1's NO-GO does not pre-empt OS2 (served cluster is co-located + detections above ambient, so
  detectability barely moves the count; OS2 nodes are spatially separated with their own ambient, so the
  banked OS1 physics is exactly the effort tool they need). Two launch-blocking gates spelled out: (1)
  region expansion outside SAN_JUAN_BOUNDS via the TB1 two-box pattern; (2) per-deployment effort/`log E`
  measured FIRST (SIMRES/JASCO duty cycle + banked OS1 detection-range per node), no skill credit until it
  lands. Wave shape W1 effort-frame -> W2 ingest net-new presence-days (led by Tekteksen/SIMRES 11 JJA-2022
  days) -> W3 summer CV skill vs +0.144 -> SYN. No code edited in `modeling/**` or `src/aws_backend/**`;
  no launch; no commit (awaiting operator ask). STOP: holds until operator confirms the two gates.

- 2026-06-27: OS2 W1 LAUNCHED (operator confirmed). Operator confirmed OS1 close + OS2 pickup. Split the
  two gates: gate-2 (effort-measured-first) is satisfied by running W1, which is read-only measurement
  with no region change/ingest/store-write, so it launched; gate-1 (region expansion outside
  SAN_JUAN_BOUNDS) is the real scope change and lives in W2, which is HELD for a separate explicit go once
  W1 effort numbers are in. Structural unlock recorded: the OSF 6ctjq calibration site is East Point on
  Saturna Island = the SAME Boundary Pass location as the SIMRES Tekteksen deployment, so the banked OS1
  detection-range calculator applies to OS2's primary node NATIVELY (not a cross-site transfer) -- the
  reason OS1's NO-GO does not carry over. Wrote `OS2_W1_DISPATCH.md`; dispatched a background subagent to
  produce `OS2_W1_effort_frame.md` (per-(node,day) log E = uptime x detectability for Tekteksen/SIMRES,
  optional CarmanahPt; MEASURED/ESTIMATED tagged; GO/HOLD-to-W2 verdict). Read-only; no convergence edit,
  no ingest, no store write, no promotion, no commit. Effective confidence 0.0. STOP after W1 doc; W2 held.

- 2026-06-27: OS2 W1 COMPLETE. `OS2_W1_effort_frame.md` written. Per-(node,day) `log E` effort frame
  measured for the net-new summer nodes. VERDICT: GO to W2 for Tekteksen / SIMRES Boundary Pass; HOLD for
  CarmanahPt. Tekteksen uptime MEASURED-continuous (Ocean Sonics icListen HF cabled to shore, 128 kHz,
  Jun-Oct 2022, SIMRES 24/7; per-day gap log NOT-MEASURED, bounded near 0); detectability run NATIVELY
  (East Point = Tekteksen, not a transfer) with the banked validated calculator + OS1 guards: per-day
  median R_max 7,423 m, area ~173-185 km^2 (equals the served orcasound_lab reference 177.8 km^2 within
  3%, absorbed by a_station), `log E_det` std 0.589 / range [-1.62,+1.13], 0% winsorized, guards do NOT
  bind (vs OS1's std 1.50 / 23.5% winsorized on the noisy transfer). Combined `log E` = a per-node
  constant ~0.0 on the served additive-log scale, bounded by a native summer per-day envelope with no
  unphysical tails. Disclosed caveats (no skill credit in W1): 2022 per-day ambient NOT-MEASURED (per-
  deployment median assigned, no fetch-to-store); SIMRES presence labels are acoustic+visual encounter-
  selected (inherited TB4 caveat). CarmanahPt single blocker: detectability is a cross-site transfer
  (nearest OSF class Port Renfrew/Sheringham/Swiftsure) with no co-located SoundTrap ambient and no public
  location (OS1 failure mode); uptime is fine (SoundTrap ST600 HF, 192 kHz continuous, Sep21-Jun22, JJA =
  June tail only). Deployment metadata source of record: Hildebrand et al. 2025 Sci Data (DOI
  10.1038/s41597-025-05281-5). DCLDE screen re-confirmed (Tekteksen 11, CarmanahPt 4 JJA-2022 certain).
  Read-only; DCLDE re-used from /tmp, OSF read-only from gitignored data/external, compute in /tmp; no
  region edit, no ingest, no convergence edit, no store write, no deploy, no promotion, no commit, no
  `git add`. Effective confidence 0.0. STOP after W1 doc; W2 (region expansion + ingest) HELD for operator.
