# OS2 W1 findings: per-(node, day) `log E` effort frame for the net-new summer nodes

Agent: OS2 W1 background subagent, Open-Science Integration (OS) waveset, O0 forecast ML-ops lane.
Date: 2026-06-27 (America/New_York). Repo: `/Users/gilraitses/orcast`. This findings doc plus one
STEP_LOG line are the ONLY files written. READ-ONLY measurement: reads of repo, web, and `/tmp` scratch,
plus bounded local compute. No region-box edit, no ingest, no edit to `modeling/**` or
`src/aws_backend/**`, no store/S3 write, no fetch-to-store, no deploy, no promotion, no commit, no
`git add`. Effective confidence stays 0.0; NO CV-skill credit is claimed in W1. Every number is tagged
MEASURED / ESTIMATED / NOT-MEASURED.

Authoritative inputs read in full: `OS2_W1_DISPATCH.md`, `OS2_BUILD_CHARTER.md`,
`OS2_open_node_screen.md`, `OS1_BUILD_NOTE.md`, the banked calculator
`data/external/osf_6ctjq/validate_detection_range.py` and transducer
`data/external/os1_ambient/transducer.py`, the served effort scale in `modeling/design.py` and
`modeling/effort.py`, the DCLDE-2027 annotation corpus cached read-only at
`/tmp/orcast_tb4/Annotations.csv`, and the deployment-metadata source of record, Hildebrand et al. 2025
*Sci Data* (DOI 10.1038/s41597-025-05281-5, the dataset descriptor for the DCLDE-2027 corpus).

## 0. The served `log E` scale this frame must match

`build_design` (`modeling/design.py`) puts an `exposure` column on each (station, bin) row and uses
`log_exposure = log(exposure)` as the GLM offset, where `exposure = bin_hours * E_frac` and `E_frac` is
the relative effort fraction in `(0, 1]` (`modeling/effort.py`). So `log E` is an additive offset on the
log-rate: `log lambda = b0 + a_station + kernels + log E`. Two facts about the served side set the bar
for "same footing":

1. For the served four nodes the uptime stream does not bind (`effort_assumed_continuous` stays True;
   `modeling/effort.py` docstring), so the served `exposure` is effectively flat (a per-node constant
   absorbed by the intercept and the station fixed effect `a_station`).
2. The OS1 per-day detectability offset was MEASURED and came back NO-GO on the served cluster, so it was
   NOT adopted. The served stations therefore carry no detectability term today.

Consequence for W1: putting a new node "on the same `log E` footing" means producing its uptime term and
its detectability level on this same additive-log scale, with any per-node constant understood to be
absorbed by `a_station` and only within-node, per-day structure capable of moving the rate beyond the
fixed effect.

## 1. Uptime / duty cycle

### 1a. Tekteksen / SIMRES Boundary Pass (primary)

Source of record: Hildebrand et al. 2025 *Sci Data*, SIMRES deployment section, plus the SIMRES
hydrophone page and the Orcasound BC listening note.

| field | value | status |
|---|---|---|
| instrument | Ocean Sonics icListen HF smart hydrophone (RB9-ETH), cabled to a shore station | MEASURED |
| geometry | ~120 m from shore, 18 m hydrophone depth, Boundary Pass near a commercial shipping lane | MEASURED |
| recording window | June through October 2022 | MEASURED |
| sampling | continuously sampled at 128 kHz, 24-bit, decimated to 64 kHz in the released files | MEASURED |
| duty cycle (recorder) | continuous; cabled-to-shore, so no battery duty-cycling. SIMRES states the hydrophones record 24/7 | MEASURED (continuous), so `log(E_uptime) ~= 0` |
| per-day outage / gap log | not published per day; the Orcasound BC note records the SIMRES stream is "occasionally offline or appears to skip" | NOT-MEASURED (bounded near 0; small downward-only corrections possible) |
| annotation / observation selection | the released data and annotations "represent periods when SRKW were both acoustically AND visually detected within a few kilometers of the hydrophones" | MEASURED (this is the binding caveat, see below) |

Reading: the RECORDER uptime for Tekteksen is continuous (a cabled icListen, MEASURED), so the uptime
component of `log E` is ~0 across the JJA-2022 window, with only small downward-only outage corrections
possible (NOT-MEASURED at per-day resolution, bounded near 0). This is honest and does not require a
fabricated duty-cycle number.

The decisive effort caveat is NOT the recorder: it is that the SIMRES presence-day labels are gated on
acoustic AND visual co-detection within a few km. The "effort" that produced these 11 presence-days is
therefore the observer/sighting effort (daylight, weather, observer present), which is NOT-MEASURED, and
non-presence days are not verified absence. This is the same TB4 caveat the charter already accepted,
amplified here by the explicit visual-sighting gate. No skill credit is claimed in W1, so this caveat is
disclosed rather than blocking; it is the reason W3 must measure skill, not assume it.

### 1b. CarmanahPt / DFO WDLP (optional second)

| field | value | status |
|---|---|---|
| instrument | SoundTrap ST600 HF (autonomous recorder) | MEASURED |
| deployment | one deployment, ~3 to 5 months, September 2021 through June 2022 | MEASURED |
| sampling | continuously sampled at 192 kHz | MEASURED (continuous, no duty cycle) |
| detector | PAMGuard Whistle and Moan Detector (SNR 8 dB), then expert-validated; "annotation labels are considered weak for all species"; calls not detected by the detector were not added | MEASURED |
| location | exact location not public (DFO policy); general descriptor only ("Carmanah Point", W Juan de Fuca entrance) | NOT-MEASURED (point coords) |
| JJA-2022 presence-days | 4 SRKW-certain, all in June 2022 (Jun 17, 22, 29, 30); deployment ended June 2022 so the JJA window is the June tail only | MEASURED |

Reading: CarmanahPt recorder uptime is MEASURED-continuous, so its uptime `log E` is also ~0 over its
window. Its JJA exposure is one partial month (June 2022 only). The blocker for CarmanahPt is
detectability, not uptime (section 2b).

Cross-check (MEASURED): re-parsing `/tmp/orcast_tb4/Annotations.csv` reproduces the screen exactly,
Tekteksen 11 JJA-2022 SRKW-certain days and CarmanahPt 4, confirming the input.

## 2. Per-node detectability (banked OS1 calculator, native at Tekteksen)

### 2a. Tekteksen: NATIVE East Point calibration (not a transfer)

The OSF `6ctjq` propagation-loss coefficients and ambient are calibrated at East Point, Saturna Island.
"Tekteksen" (SENCOTEN ṮEḴTEḴSEN) IS East Point. So the validated calculator runs natively here: the East
Point Summer PL coefficients and the East Point Summer ambient describe the actual Tekteksen site, with
no cross-site geoacoustic transfer. This is the structural reason OS1's NO-GO (which leaned on an East
Point -> Haro Strait transfer plus a noisy OrcaSound ambient) does not carry to Tekteksen.

Method (MEASURED): reuse `validate_detection_range.py` Eq 4 to 5 with East Point Summer PL coefficients
at a 15 m source depth (the OS1 default representative call depth), the OSF East Point Summer ambient
(`Data_Data.1.64000.icListen_ch0__20150720_20150819__customBands.csv`, 43,119 clean per-minute spectra
over 31 days, 20 Jul to 19 Aug 2015), and the OS1 robustness guards (smooth-in-frequency window 5, R_max
clamp [500 m, 20 km], winsorize the per-day offset to +/-2).

Validation anchor (MEASURED, reproduced this wave): the calculator reproduces the published East Point
summer ranges (median R_max ~14,967 m low-noise and ~1,425 m high-noise at 10 m source depth, vs paper
~15,500 / ~1,640), so the native run is trusted.

Per-minute R_max (East Point summer, 15 m source), 43,119 minutes:

| stage | median R_max | p10 | p90 | notes |
|---|---:|---:|---:|---|
| raw (no smooth, no clamp) | 7,927 m | 737 m | 22,991 m | bare Eq 5 max-over-bands |
| smoothed in frequency | 7,667 m | 688 m | 22,744 m | smoothing barely moves the median |
| smoothed + clamped | 7,667 m | 688 m | 20,000 m | clamp caps a high tail |

Guard binding at the per-MINUTE level: 13.9% of minutes exceed the 20 km clamp and 8.0% fall below the
0.5 km floor. The smoothing changes the median by only ~3% (7,927 -> 7,667 m), so the lone-noisy-band
amplification that drove OS1's blow-up is largely absent in this high-quality per-minute SPL series.

Per-DAY detectability (aggregate per-minute R_max to a daily median over the 31 native summer days, the
resolution that matters for a per-day `log E`):

| quantity | value | status |
|---|---|---|
| daily median R_max | 7,423 m (range 3,306 to 13,039 m) | MEASURED (native) |
| detection area at the daily-median R_max | ~173 km^2 (pi * R_max^2) | MEASURED (native) |
| `log E_det` = log(area_day / median_area) | std 0.589, range [-1.618, +1.127] | MEASURED (native) |
| fraction winsorized at +/-2 | 0.0% | MEASURED |
| guards bind at the per-day level | NO (0% winsorized, daily R_max entirely inside the published 1.5 to 15.5 km envelope) | MEASURED |

This is the key defensibility result. At the native, well-sampled site (1,439 minutes per day), the
per-day detectability term is well-behaved: `log E_det` std 0.589 vs OS1's 1.50, and 0% winsorized vs
OS1's 23.5%. The clamp and winsor guards that bound heavily on the noisy OS1 transfer do NOT bind here.
There are no unphysical tails: every daily R_max sits inside the paper's published East Point summer
range envelope.

Cross-node level (the quantity that puts Tekteksen on the served footing): Tekteksen's native detection
area (~173 to 185 km^2, depending on per-minute vs daily-median aggregation) is essentially equal to the
served orcasound_lab reference area MEASURED in OS1 (177.8 km^2 median; `os1_skill_result.json`). This is
expected, because the served cluster used the East Point PL transfer and Tekteksen IS East Point. So the
cross-node area level shift needed to place Tekteksen on the served scale is ~log(173/178) ~= -0.03, i.e.
~0, and is absorbed by `a_station` regardless.

Depth sensitivity (MEASURED): the median R_max is stable across plausible source depths (6,703 m at 10 m,
7,531 m at 15 m, 7,696 m at 20 m), so the 15 m choice does not drive the result.

### 2b. CarmanahPt: detectability would be a TRANSFER (not native)

CarmanahPt is in the W Juan de Fuca entrance, not at any OSF calibration site. The nearest OSF
geoacoustic classes are Port Renfrew, Sheringham Point, and Swiftsure (also W Juan de Fuca / JdF
entrance), so a detectability estimate for CarmanahPt would be a cross-site geoacoustic TRANSFER, exactly
the construction OS1 found unreliable, and there is no co-located ambient series for the SoundTrap (the
OSF ambient is East Point, a different basin). The exact location is also not public (DFO). So a native
detectability term for CarmanahPt is NOT-MEASURED, and a transfer-based one would inherit the OS1 caveat.

## 3. Combined `log E` per (node, day)

Combined `log E(node, day) = log(E_uptime) + log E_det`, on the served additive-log offset scale.

### Tekteksen, the 11 JJA-2022 SRKW-certain presence-days (Jun 28; Jul 10, 11, 12, 13, 23, 25, 26, 29; Aug 4, 9)

- Uptime term: `log(E_uptime) ~= 0` for all 11 days (continuous cabled recorder, MEASURED), with only
  small downward-only outage corrections possible (NOT-MEASURED, bounded near 0).
- Detectability term: the per-day 2022 ambient at Tekteksen is NOT-MEASURED (the OSF ambient is a 2015
  summer month; obtaining 2022 per-day ambient would need a fetch of 2022 Tekteksen/Orcasound East Point
  audio, out of scope and explicitly barred by the no-fetch-to-store rail). For the exact 11 days the
  detectability anomaly is therefore assigned the per-deployment MEDIAN (`log E_det = 0`), and the native
  2015 summer distribution (std 0.589, range [-1.62, +1.13], 0% winsorized) is reported as the MEASURED
  envelope of plausible per-day variation at this exact site.

So the combined per-(node, day) `log E` for Tekteksen, at the resolution actually MEASURABLE in W1, is a
per-node constant ~= 0.0 on the served scale (area ~173 to 185 km^2, within 3% of the served reference,
absorbed by `a_station`), bounded by a native, physically-sane per-day envelope of std ~0.59.
Distribution shape: no unphysical tails (every implied daily R_max is inside 1.5 to 15.5 km), no winsor
binding, no degenerate blow-up. This is the opposite of the OS1 failure profile.

Honest implication: because both the measurable uptime (continuous) and the measurable detectability (a
per-deployment median, since 2022 per-day ambient is absent) are per-node constants, the Tekteksen `log
E` reduces to a single per-node level that `a_station` absorbs, and it lands within 3% of the served
reference. That is exactly "the same footing as the served stations" (whose exposure is itself flat per
section 0). What W1 CANNOT supply is a date-resolved within-node 2022 effort series, so W2/W3 must attach
the per-node constant and must not claim per-day effort resolution it does not have.

### CarmanahPt

Combined `log E` is NOT defensible at this time: uptime is fine (continuous, June-2022 tail), but the
detectability term is unavailable natively and a transfer carries the OS1 caveat with no co-located
ambient and no public location.

## 4. Gate verdict to W2

- Tekteksen / SIMRES Boundary Pass: GO. The effort frame is defensible. Recorder uptime is
  MEASURED-continuous (`log E_uptime ~= 0`); detectability is computed NATIVELY with the validated
  calculator, has no unphysical tails, the robustness guards do NOT bind at the per-day level (0%
  winsorized, std 0.589 vs OS1's 1.50 / 23.5%), and the detection-area level matches the served reference
  to within 3%. The per-(node, day) `log E` W2 should attach is the per-node constant ~0.0 on the served
  scale, with the native summer envelope (std ~0.59) recorded as the bound on unmeasured per-day
  variation. Disclosed, inherited caveats (no new blocker): the 2022 per-day detectability anomaly is
  NOT-MEASURED (median assigned), and the presence labels are acoustic+visual encounter-selected (TB4
  caveat), so NO skill credit until W3 measures it.

- CarmanahPt / DFO WDLP: HOLD. Single blocker: detectability is not natively calibrated (nearest OSF
  class is a Port Renfrew / Sheringham / Swiftsure cross-site transfer, the OS1 failure mode) and there
  is no co-located ambient for the SoundTrap, so its counts cannot be put on the served `log E` footing
  honestly. Uptime is fine; the deployment also contributes only the June-2022 JJA tail.

## 5. Return summary

- Per-node effort frame. Tekteksen: uptime MEASURED-continuous (icListen HF cabled, 128 kHz, Jun to Oct
  2022) so `log E_uptime ~= 0`; detectability NATIVE (East Point = Tekteksen) median R_max 7.42 km, area
  ~173 to 185 km^2, equal to the served reference (177.8 km^2) within 3%. CarmanahPt: uptime
  MEASURED-continuous (SoundTrap ST600 HF, 192 kHz, Sep 2021 to Jun 2022, JJA = June tail); detectability
  NOT-MEASURED natively (would be a transfer).
- Duty-cycle status. Recorder duty cycle MEASURED = continuous for both nodes (no battery duty-cycling;
  SIMRES cabled-to-shore + SIMRES "24/7", DFO SoundTrap "continuously sampled"). Per-day outage/gap log
  NOT-MEASURED (bounded near 0). The SIMRES presence labels are acoustic+visual encounter-selected
  (MEASURED caveat), so the label-gating observation effort is NOT-MEASURED (inherited TB4 caveat).
- Detectability numbers (native East Point, MEASURED): per-day median R_max 7,423 m (range 3,306 to
  13,039 m); detection area ~173 km^2; `log E_det` std 0.589, range [-1.618, +1.127]; 0% winsorized;
  guards do not bind; validated against the published envelope.
- Combined `log E` distribution: a per-node constant ~= 0.0 on the served additive-log scale (absorbed by
  `a_station`), bounded by a native per-day envelope of std ~0.59 with no unphysical tails, no winsor
  binding, no blow-up. Defensible.
- Verdict: GO to W2 for Tekteksen / SIMRES; HOLD for CarmanahPt. Single CarmanahPt blocker:
  detectability is a cross-site transfer with no co-located ambient (not native, OS1 failure mode).
- Rails honored: no region-box edit, no ingest, no `modeling/**` or `src/aws_backend/**` edit, no
  store/S3 write, no fetch-to-store, no deploy, no promotion, no commit, no `git add`. DCLDE annotations
  re-used read-only from `/tmp/orcast_tb4/`; OSF coefficients + ambient read-only from gitignored
  `data/external/`; compute in `/tmp` scratch. NO CV-skill credit claimed. One findings doc plus one
  STEP_LOG line written. Effective confidence 0.0. W2 not started.
