# ACX-R4 — Adversarial audit of the planned TKW-lift and call_type strengthening

Lane: BSWR-ACX (acoustic-heads-strengthen). Wave: ACX-R (read-only research). Author: ACX-R4 (adversarial). Read-only; no pipeline/code/JSON/manifest edits; no download/train/commit. Evidence below is from ad-hoc read-only python over `infra/acoustic/data/corpora/dclde-2027/features_v1.npz`, the served `web/public/hydrophone/slice/classification.json`, the in-repo `infra/acoustic/eval_report_dclde_v1.json`, and the pipeline source under `modeling/acoustic/`.

## Adversarial verdict (summary)

The split mechanics are cleaner than the dispatch feared: under `minority_aware_group_split` whole station-day groups stay intact, and no soundfile or station-day appears in both train and test (measured: empty intersection). So there is **no window/soundfile/station-day leak**. The real traps are three confounds that a single held-out number hides. (1) The split is **leave-station-DAY-out, not leave-station-out**: all three TKW test stations (StrGeoN1, StrGeoS1, StraitofGeorgia) also carry TKW in train on other days — same hydrophone hardware, site reverberation, and noise floor on both sides — and TKW is almost entirely confined to JASCO/DFO AMAR Strait-of-Georgia recorders, so "recognize the recorder/site" is highly correlated with the TKW label. (2) TKW rests on **12 station-days across 6 stations**, and the held-out TKW positives are a **handful of continuous encounters** (seed-0 test TKW = 186 windows dominated by one ~36-min AMAR610 session); TKW test support swings 147→395 windows across seeds (≈2.7×), so the reported TKW f1 (logreg 0.434 / rf 0.277) is a high-variance point estimate of a few encounters, not generalizable Bigg's morphology. (3) The keep-all-TKW + SRKW-cap=40 sampling makes the test prevalence **16.7% TKW vs ~5% at deployment**, so reported TKW precision/f1 are **optimistic** and a raw `P(TKW|x)` confidence is overconfident by the prior odds ratio. **Safe to attempt:** keep presence and the SRKW-dominated ecotype estimate as low-confidence, eval-bounded, with confounds disclosed. **Trap:** shipping any standalone "Bigg's detected" claim, shipping call_type, or promoting `bam-dclde-salish-v1` into `classification.json` without an O0 contract decision.

## Split-leakage verdict — measured evidence

Verdict: **No leak at the window / soundfile / station-day level.** `minority_aware_group_split` builds `test` as a *set of whole groups* (it pools minority-bearing groups and non-minority groups separately, then picks ~`test_frac` of each pool); `train = complement`. Groups are therefore disjoint by construction, and because each soundfile maps to exactly one group, soundfiles are disjoint too.

Measured (ecotype head, SRKW vs TKW call windows, seed=0, the same split the eval report used):

| Check | Result |
|---|---|
| Soundfiles spanning >1 group (whole corpus) | **0** |
| Train groups / test groups | 64 / 28 |
| Group intersection (train ∩ test) | **∅ (empty)** |
| Soundfile intersection (train ∩ test) | **0 (empty)** |
| Test ecotype balance | SRKW 929 / TKW 186 |
| Train ecotype balance | SRKW 2076 / TKW 595 |

Seed-0 TKW test station-days `{StrGeoN1|2021-09-21, StrGeoS1|2021-11-11, StraitofGeorgia|2016-08-08, StraitofGeorgia|2018-01-17}` match the `ecotype.test_station_days` recorded in `eval_report_dclde_v1.json`, so this audit reproduces the shipped eval's split.

Caveat that downgrades the verdict from "clean" to "clean-but-confounded": the split controls station-DAY, not station. Same-recorder overlap between train and test:

- All stations overlap train/test (leave-day-out only): `BoundaryPass, HaroStraitNorth, HaroStraitSouth, LimeKiln, StrGeoN1, StrGeoS1, StraitofGeorgia, Tekteksen`.
- **TKW-bearing station overlap: `{StrGeoN1, StrGeoS1, StraitofGeorgia}` — every TKW test station is also a TKW train station.**

This is the leakage-adjacent risk to enforce: the model can key on per-recorder hardware/site signature (AMAR unit response, site noise/reverb) that is correlated with TKW, because TKW lives almost exclusively on the JASCO/DFO AMAR Strait-of-Georgia stations (TKW by station: StraitofGeorgia 248, StrGeoN1 237, StrGeoS1 168, HaroStraitSouth 57, BoundaryPass 47, SwanChan 24) while SRKW is spread across OrcaSound/Lime Kiln/Puget Sound sites. Ecotype label is confounded with provider/recorder. A leave-station-out (not leave-day-out) TKW number is the only one that disentangles Bigg's call morphology from "is this an AMAR recording."

## Within-session / encounter confound — counts

TKW positives in `features_v1.npz`: **781 windows**, spanning only:

- **12 distinct station-days** (groups),
- **6 stations**,
- nominally 90 "soundfiles" — but these are mostly **consecutive ~4-minute slices of the same continuous deployment/encounter**, so distinct-soundfile count overstates independent encounters.

TKW windows per station-day are dominated by a few sessions: `StrGeoN1|2021-09-25` (142), `StraitofGeorgia|2018-01-12` (196), `StrGeoN1|2021-09-21` (95), `StrGeoS1|2021-11-18` (108). The seed-0 held-out TKW set (186 windows) is essentially **3–4 encounters**, e.g. `StrGeoN1|2021-09-21` is consecutive `AMAR610.20210921T0226…→0302…` files (one ~36-min continuous encounter contributing ~95 windows).

High-variance proof — TKW test support by seed (same function, different seed):

| seed | TKW test station-days | n_TKW_test |
|---|---|---|
| 0 | 4 | 186 |
| 1 | 4 | 310 |
| 2 | 4 | 147 |
| 3 | 4 | 153 |
| 4 | 4 | 395 |
| 5 | 4 | 224 |

TKW test denominator swings 147→395 (≈2.7×) on seed alone. Therefore the reported TKW metrics (logreg f1 0.434 / recall 0.479; rf f1 0.277 / recall 0.172) are a **single-seed point estimate over a few encounters**, with no confidence interval. Warning: even a leave-station-day-out TKW number can reflect one encounter's acoustics (one group of animals, one propagation geometry, one recorder), not Bigg's-vs-resident call morphology in general.

## Sampling-prior bias

`fetch_features_dclde.py` keeps **all** TKW and caps SRKW at **40 per station-day** (`--srkw-cap-per-day 40`). Effect on the corpus and eval:

- Natural/deployment ratio stated as ~19:1 SRKW:TKW → TKW prevalence **~5%**.
- Sampled corpus ratio: SRKW 3005 / TKW 781 = **3.85:1**.
- Ecotype **test-set TKW prevalence = 16.7%** (186 / 1115).

Consequence for honesty:

- **Recall** (TKW 0.479 logreg) is prevalence-independent and transfers to deployment.
- **Precision / F1** are measured at 16.7% TKW. At the ~5% deployment prevalence, the ~3.8× more abundant SRKW produces ~3.8× more false-positive opportunities per true TKW, so deployment TKW precision is materially **lower** than the reported 0.397 (logreg) / 0.711 (rf). The reported TKW F1 is therefore **optimistic** for deployment.
- A HUD confidence emitted as the raw model posterior `P(TKW|x)` (with `class_weight="balanced"` on a 3.85:1 set) is calibrated to the resampled prior and is **overconfident on TKW** by roughly the prior-odds ratio; it must be recalibrated to the deployment prior before any TKW confidence is shown.
- Minor internal inconsistency to flag: `eval_report_dclde_v1.json` discloses the confound as "~19:1" while its metrics are computed at 3.85:1; the disclosed prior and the measured prior do not match.

## Dishonesty conditions

### (a) A stronger TKW / ecotype claim is DISHONEST if any of:

1. **Leave-station-out is not enforced for TKW.** Any TKW metric where a TKW test station also appears (any day) in TKW train is confounded by recorder/site identity (measured: 3/3 TKW test stations overlap train). Reporting it as "Bigg's call detection" overclaims recorder recognition as morphology.
2. **The HUD wording exceeds the held-out TKW eval** — e.g. naming "Bigg's/Transient", asserting presence of TKW, or any wording stronger than a low-confidence SRKW-vs-Bigg's *estimate*. With rf TKW recall 0.172 the model misses ~83% of TKW; with logreg precision 0.397 most "TKW" calls are wrong. A definite-sounding TKW label is dishonest.
3. **Confidence is the raw posterior, not recalibrated to the ~19:1 deployment prior** (overconfident by the prior ratio).
4. **The TKW number is a single-seed point estimate** presented without disclosing it rests on ≤12 station-days / a few encounters and is ±2.7× seed-sensitive on support.
5. **TKW is promoted from "low-confidence estimate" to a standalone alert/spawn/count** in the served contract.
6. Any drift toward **pod (J/K/L) or individual ID** off the ecotype head — never supported.

### (b) A shipped call_type head is DISHONEST if any of:

1. **`pulsed_call` is shipped while it is literally "any S-code."** Measured label inventory: BoundaryPass `pulsed_call` 877, Tekteksen `pulsed_call` 1975, LimeKiln `pulsed_call` 412 — these are the S1–S40 stereotyped-call catalog collapsed coarse. Shipping `pulsed_call` re-labels and ships the forbidden S1–S40 catalog under a coarse alias.
2. **Minority (whistle) recall ≈ 0 / collapse to majority.** Diagnostic: whistle recall **0.0**, f1 **0.0**, pulsed_call recall **1.0** on the LimeKiln test (confusion `[[116,0],[38,0]]`) — the model predicts the majority for every window. Any shipped head with this behavior claims a contrast it cannot make.
3. **Single-/two-station support.** Whistle appears at only 2 stations (LimeKiln 40, Tekteksen 321); click/buzz at one station (dropped). Test is a single held-out station (LimeKiln). No honest cross-station call_type generalization exists.
4. **macro_f1 0.4296 is presented as a usable head** rather than a diagnostic; it is below a trivial majority baseline on the minority class.
5. Wiring call_type into `classification.json` at all — `heads.assert_shippable("call_type")` is designed to refuse it (`eval_supported=False`); overriding that guard is the dishonesty trigger.

(Standing lock, restated: `single_vs_multiple` has no source-count labels and **stays BLOCKED**; reviving it as a claim is dishonest by definition.)

## P0 / P1 critique checklist for the later ACX-ADV wave

**P0 — block ship / fail the wave if any are true:**

- [ ] Any train/test **soundfile or station-day intersection** is non-empty for a shipped head (re-run the split, assert empty; currently empty — must stay empty).
- [ ] A shipped TKW metric is reported **without leave-station-OUT** (no TKW test station may also be a TKW train station).
- [ ] Any **HUD/served wording exceeds the measured eval** — names Bigg's/Transient as detected, asserts TKW presence, or states confidence above the held-out TKW number.
- [ ] **call_type is wired into `classification.json`** or `assert_shippable` is bypassed; or `pulsed_call` (= any S-code) is shipped in any form; or a head shipped with minority recall ≈ 0 (majority collapse).
- [ ] **`single_vs_multiple` revived** as a claim.
- [ ] Any **whale count / pod / individual ID / S1–S40 catalog call** surfaced.
- [ ] `classification.json` `model_version` flipped to `bam-dclde-salish-v1` or an ecotype/call_type field added **without an O0 contract-change decision and matching `spawnCountBasis`** (see gated items).

**P1 — must be fixed / disclosed before ship:**

- [ ] TKW metric **rests on < N station-days** (current: 12 total, ~4 in any test split) — require a disclosed station-day/encounter count and a **multi-seed or LOSO confidence interval**, not a single-seed point estimate (current support is ±2.7× seed-sensitive).
- [ ] TKW **confidence not recalibrated** to the ~19:1 deployment prior (raw posterior is overconfident).
- [ ] **Prior mismatch** between disclosed confound (~19:1) and measured prior (3.85:1; test prevalence 16.7%) left unreconciled in the eval/HUD.
- [ ] **Confound disclosure missing**: recorder/site identity correlation with TKW, encounter concentration, presence-oriented 129-dim log-mel feature being weak for fine morphology.
- [ ] Eval `split.train_groups/test_groups` recorded as `null` for the shipped heads (presence/ecotype) — station-day membership is not machine-checkable from the report; require it populated so the split is auditable.

## Gated items / warnings for O0

1. **classification.json contract change (primary gate).** The served slice is still `bam-srkw-presence-v0` with `classes:["srkw_call_presence"]`, `honesty.not_claimed` including ecotype/call type, and `summary.spawnCountBasis:"presence_only"`. Promoting `bam-dclde-salish-v1` or adding an ecotype/call_type field is a **contract/count-basis change**, not a model swap: it changes what the HUD claims and the basis of `spawnCount`. This requires an explicit O0 decision and a synchronized update to `honesty.not_claimed`, `classes`, and `spawnCountBasis`. (Note: `data/models/promotion.json` shows `promoted:true, effective_confidence:0.0, repr_id:null` — promotion plumbing exists but is not yet bound to this model; confirm it cannot silently flip the served contract.)
2. **TKW honesty cap.** If ecotype ships at all, it ships only as a low-confidence SRKW-vs-Bigg's *estimate*, confidence recalibrated to deployment prior, with the recorder/encounter confounds disclosed and a leave-station-out TKW number. No standalone Bigg's alert/spawn.
3. **call_type stays diagnostic-only.** `pulsed_call = any S-code` is the forbidden catalog in disguise; whistle collapses to recall 0 on the only held-out station. Do not ship. `to_strengthen` (coarse CK/W/BP relabel budget or O0-costed learned embedding) is an O0 cost decision, not an ACX ship.
4. **single_vs_multiple BLOCKED** — unchanged; no source-count labels (BSW-R02).
5. **Honesty lock restated:** HUD claim never exceeds the held-out eval; estimate + confidence only; no whale count, no pod/individual ID, no S1–S40 catalog call.
