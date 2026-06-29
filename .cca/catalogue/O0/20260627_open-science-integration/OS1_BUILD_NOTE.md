# OS1 build note: validated detection-range calculator

Date: 2026-06-27 (America/New_York). Lane: O0 forecast ML-ops, OS waveset, OS1 effort/detectability.
Status: calculator IMPLEMENTED and VALIDATED against the source paper. Not yet wired to the served
model. Effective confidence 0.0; nothing promoted.

## Provenance (honest)

- Data: OSF node `6ctjq` (`PL_coeffs.zip`, `SPL_files.zip`), fetched via the published anonymous
  view-only link in the paper's open-access (CC-BY) Data Availability statement.
- License: data-file reuse license UNCONFIRMED (the OSF node carries no license tag). OSF "Request
  access" submitted + author email (X. Mouy) pending. INTERNAL VALIDATION ONLY; do NOT redistribute
  or publish the raw data or any derived artifact until the authors confirm reuse terms.
- Storage: `data/external/osf_6ctjq/` (gitignored; never committed).
- Method source: Mouy, Austin, Wladichuk, Yurk (2025), PLoS One 20(9):e0331942,
  DOI 10.1371/journal.pone.0331942. Source level: Holt et al. 2009 (JASA-EL), SRKW pulsed-call
  broadband SL mean 155.3 dB +/- 7.4 SD re 1 uPa @ 1 m (range 133-174, 1-40 kHz band).

## Equations (transcribed from the article equation images, not the lossy plain text)

- Eq 1: RL = SL - PL
- Eq 2: PL(f, z, R) = A(f, z) - n(f, z) * log10(R)        [A = CSV col 2; n = CSV col 3]
- Eq 3: RL(f, z, R) >= NL(f) + DT,   DT = 5 dB
- Eq 4: R(f) = 10 ^ ((A + SL(f) - NL(f) - DT) / n)        [A enters with a PLUS sign]
- Eq 5: R_max = argmax over the 46 bands of R(f)

Bug found and fixed: an initial implementation subtracted A (`-A`) instead of adding it (`+A` per
Eq 4). Because A ~ -9, this flipped the sign of a ~9 dB term and inflated ranges ~18x (and the
band-max compounded it to ~100x). Corrected after reading the equation images.

## Validation result (East Point, summer; SL = 155.3 dB point value, deterministic depth)

| source depth | low-noise median R_max | high-noise median R_max |
|---|---|---|
| 10 m | 14,967 m | 1,425 m |
| 15 m | 17,474 m | 1,483 m |
| 20 m | 18,064 m | 1,502 m |
| **paper target (P=0.5)** | **~15,500 m** | **~1,640 m** |

Reproduces the published ranges within ~5-15% at a representative 10-15 m source depth. Residual is
the paper's source-level + log-logistic depth Monte Carlo, which the validation approximated with
point values. The relative noise response (low/high ~10x) matches. Calculator TRUSTED.

## What this unlocks / next steps

1. Detection AREA transducer: map ambient (broadband or per-band) -> R_max -> detection area, for the
   Mouat Point / East Point geoacoustic class (the nearest class to the served Haro Strait cluster).
2. Per-day ambient at the served stations: ONC East Point / Boundary Pass ambient as a regional
   daily-noise proxy via the ONC Oceans 3.0 token (operator decision 2026-06-27), matched to the
   served detection-record date range.
3. log E offset: log(area_day / reference_area), regionally shared across the 4 clustered Haro
   stations -> per-DAY (within-station) variation that station fixed effects cannot absorb.
4. Measure: refit kernels with the offset as a KNOWN effort offset (zero new presence parameters) and
   report held-out CV mean-deviance-skill vs the clean baseline. Promotion stays a separate B.1 gate.

## Per-day ambient: pivot to OrcaSound DSP (operator decision 2026-06-27)

The originally-planned ONC East Point ambient proxy was checked and REJECTED: there is no ONC cabled
hydrophone at East Point or in Haro Strait. The nearest continuous node (ECHO3, Strait of Georgia) is
~35 km from East Point / ~55 km from the served cluster, in a different acoustic sub-basin, exposes
raw audio only (no broadband-SPL series), and returned zero archive files on the standard query.
External license/token were not the blocker -- the data geometry was.

Operator chose the faithful path: per-day band-level SPL computed from OrcaSound raw audio at the
ACTUAL served stations.

DSP pipeline PROVEN end-to-end:
- OrcaSound audio is public on `s3://audio-orcasound-net/<node>/hls/<session_ts>/live*.ts` for all
  three served nodes (`rpi_orcasound_lab`, `rpi_north_sjc`, `rpi_andrews_bay`), ~110 sessions/month
  across every detection-heavy month 2020-2026.
- 48 kHz AAC segment -> ffmpeg decode -> scipy Welch PSD -> 46 x 300 Hz bands yields a physically
  correct ocean spectrum (highest at 1 kHz, decreasing with frequency), matching the paper's site
  ambient description. Day-to-day band-0 (1 kHz) varied ~13 dB over a 5-day smoke test.
- Levels are UNCALIBRATED dB. For an effort OFFSET this is sound: a constant per-band calibration
  shifts log E by a constant the GLM intercept absorbs; only the day-to-day anomaly drives the term.

## Transducer + calibration anchor

`data/external/os1_ambient/transducer.py`: daily uncalibrated band spectrum -> per-band anchor to the
OSF East Point summer median (`osf_eastpoint_summer_median.npy`; 81.3 dB @1 kHz .. 64.7 @13.6 kHz),
preserving each day's anomaly -> Eq 4-5 R_max (East Point summer PL coeffs, 15 m source) -> detection
area -> `log E_det(day) = log(area_day / median_area)`. On the 5-day sample: median R_max ~6.9 km,
area ~148 km^2 (consistent with the validated East Point physics), with substantial per-day variation.

## Measurement harness (ready; awaiting full ambient)

`data/external/os1_ambient/measure_os1_skill.py`: builds the served design from the OrcaHello
candidate cache, runs `block_cv` (negbin; diel+lunar+season) with the baseline flat-effort exposure
vs OS1 exposure multiplied by `exp(log E_det[station, day])`, and reports the delta in
mean-deviance-skill. Identical covariates/estimator both runs; only the effort offset differs, so the
delta isolates OS1. Offline + read-only (writes nothing to the served store).

Status 2026-06-27: full orcasound_lab ambient extraction (2020-09..2021-09, the dominant station's
dense window, 1029 of 1359 served detections) RUNNING in background (~17 s/day). Measurement runs on
completion.

## Extraction complete + measurement (2026-06-27)

Extraction finished: orcasound_lab, 2020-09-01..2021-09-30, 391 days, 4 audio segments/day (2 sessions
x 2 segments), all 391 with audio. Output `os1_ambient/ambient_orcasound_lab.json`.

First measurement was catastrophic and surfaced a defect, not a result: log E_det std ~5.0, p99 ~ +24.7
(area swings ~1e10x). The CV mean blew up to -1.4e10 even though the median fold skill spuriously rose
(the offset was overfitting to extreme days). Root cause: only ~4 segments/day make an individual
300 Hz band several dB noisy, and a pure max-over-46-bands amplifies any single quiet-band outlier into
an unphysical detection range.

Robustness fix (in `transducer.py`): (1) smooth the daily spectrum across frequency (moving median,
window 5) since ocean ambient is smooth in f but single-band sampling noise is not; (2) clamp R_max to
a physical [500 m, 20 km] window (paper East Point summer ranges run ~1.5-15.5 km); (3) winsorize the
final offset to +/-2 as a backstop. Result: log E_det std 1.50, range [-2, 2], median R_max 7.5 km,
23.5% of days at the winsor bound.

Re-measurement (negbin; diel+lunar+season; 5 time-blocked folds; orcasound_lab; 725 detections in
window; 8563 station-bins; 99.2% offset coverage):

| kappa (offset scale) | mean CV deviance-skill | median | folds pass |
|---|---|---|---|
| 0.00 (baseline) | **+0.2776** | +0.1222 | 3/5 |
| 0.10 | +0.2747 | +0.1360 | 3/5 |
| 0.25 | +0.2608 | +0.1692 | 3/5 |
| 0.50 | +0.1989 | +0.0288 | 3/5 |
| 0.75 | +0.0821 | +0.0382 | 3/5 |
| 1.00 (full offset) | -0.1300 | -0.0635 | 2/5 |

## Conclusion: NO-GO on served skill (measured)

The mean CV deviance-skill (the load-bearing promotion metric) DECREASES monotonically with the
detectability offset scale; no positive kappa beats the baseline mean. The only positive sign is a
small, fold-unstable median wobble at kappa 0.1-0.25 (+0.05 vs baseline) that does not move the mean.
So the OS1 hypothesis -- that per-day acoustic detectability (East Point geoacoustic transfer, OrcaSound
ambient) improves the served temporal forecast -- FAILS on the dominant station. OS1 is a NO-GO for
promotion and the offset is not adopted.

Honest reasons (for the next orchestrator): OrcaHello detections are SRKW calls typically well above
ambient, so per-day noise may not gate the count; the East Point geoacoustic transfer is an
approximation to orcasound_lab's true site; the 4-seg/day ambient is noisy (a noisy offset adds
variance); and a fixed area->count multiplicative effort model may be too stiff (23.5% winsorized).

What remains valuable regardless: the validated detection-range calculator and the proven OrcaSound DSP
pipeline are reusable for any future spatially-separated node that has co-located ambient and where
detectability genuinely varies (OS2 / TB nodes).

Result artifact: `os1_ambient/os1_skill_result.json` (offset summary + full kappa sweep + conclusion).

## Scripts (all gitignored under data/external/)

- `osf_6ctjq/validate_detection_range.py` -- calculator validation vs the paper (table above).
- `os1_ambient/extract_daily_ambient.py` -- OrcaSound audio -> per-(station,day) band SPL.
- `os1_ambient/transducer.py` -- band SPL -> per-day log E_det offset (robust: smooth + clamp + winsorize).
- `os1_ambient/measure_os1_skill.py` -- CV mean-deviance-skill with vs without the offset.
- `os1_ambient/ambient_orcasound_lab.json` -- 391-day ambient. `osf_eastpoint_summer_median.npy` -- anchor.
- `os1_ambient/os1_skill_result.json` -- the measured verdict.
