# ACX-R1: Lift envelope for the weak ecotype-TKW head

**Lane:** BSWR-ACX (acoustic-heads-strengthen) / read-only ACX-R research wave.
**Scope:** read-only. No code, JSON, manifest, or model touched. Ad-hoc read-only python on already-present local files only; no fit/train, no download, no install.

## Summary

The featurized v1 set already uses **every audio-backed TKW annotation in the Salish DCLDE-2027 subset**: 781 TKW windows over **12 station-days**, and the corpus holds only **3 more TKW station-days** (StrGeoN2/StrGeoS2, 245 annotations) which are audio-404 and not fetchable without an alternate audio source. So the TKW head cannot be lifted by simply pulling "more TKW data" from this corpus; the data path is essentially closed. Because `class_weight="balanced"` is already in place, naive reweighting is also spent. On the **existing 129-dim presence-oriented log-mel silhouette** the only honest near-term lever is operating-point/threshold selection (small, no new dep), which I estimate moves TKW f1 from the 0.434 logreg baseline to roughly **0.45 to 0.52** while trading SRKW recall, and adds **no new generalization**. A larger, durable lift requires **new numpy/scipy call-morphology / click features** (inter-click-interval, pulse-rate, Teager-Kaiser click energy, click peak/centroid frequency), which is literature-supported but needs re-featurization of audio (box compute, O0-gated) and is itself bounded by a biological ceiling: Bigg's/transients are click-sparse with no modal ICI, so they are intrinsically the hard ecotype. The recommended ACX-Q pass metric is a **median TKW f1 > 0.434 across >=3 leave-station-day-out seeds, with a TKW recall floor of 0.478 and SRKW f1 held >= 0.84**, reported with per-seed spread because the TKW test rests on only ~3 to 4 station-days.

## Measured facts

| Fact | Value | Source file |
|---|---|---|
| Salish TKW annotations (Ecotype=="TKW", KW=="1") | 1,035 | `infra/acoustic/data/corpora/dclde-2027/Annotations.csv` |
| Salish SRKW annotations (KW=="1") | 19,727 | `Annotations.csv` (grounding said ~19,725; 2-row diff at UTC edge) |
| TKW distinct station-days, all Salish | 15 | `Annotations.csv` |
| TKW distinct station-days, **audio-backed** | **12** | `Annotations.csv` x `fetch_features_dclde.py:DATASET_AUDIO` |
| TKW station-days NOT audio-backed (audio-404) | 3 (StrGeoN2: 2 days/194 ann; StrGeoS2: 1 day/51 ann) | `Annotations.csv`; `fetch_features_dclde.py` note |
| Per-station-day TKW annotation count (audio-backed), sorted | 196, 142, 108, 104, 60, 57, 47, 30, 24, 17, 4, 1 (median 52) | `Annotations.csv` |
| Featurized TKW windows (the EXACT set behind v1) | **781** over **12 station-days** | `infra/acoustic/data/corpora/dclde-2027/features_v1.npz` |
| Featurized SRKW windows | 3,005 over 80 station-days (SRKW capped at 40/day) | `features_v1.npz`; `fetch_features_dclde.py --srkw-cap-per-day 40` |
| Featurized background windows | 1,739 | `features_v1.npz` |
| TKW window concentration | top 5 station-days = 601/781 (77%); 6 of 12 days carry >=47 windows; 2 days carry <=4 | `features_v1.npz` |
| TKW window provider concentration | StrGeo* + StraitofGeorgia (DFO_WDLP/JASCO_VFPA_ONC) = 677/781 (87%) | `features_v1.npz` (`dataset` key) |
| TKW test support / split | 186 windows, leave-station-day-out, TKW held in train and test; ~3 to 4 test station-days (95+60+30+1) | `infra/acoustic/eval_report_dclde_v1.json` |
| Ecotype baseline (selected=logreg) | TKW f1 0.4341 (P 0.3973, R 0.4785), SRKW f1 0.8725, macro-f1 0.6533; rf TKW f1 0.2771 (P 0.7111, R 0.1720) | `eval_report_dclde_v1.json` |
| Reweighting already applied | both logreg and rf use `class_weight="balanced"` | `modeling/acoustic/train_dclde.py:train_one` |

Key reading: the featurized TKW station-days (`StraitofGeorgia|2018-01-12`:196, `StrGeoN1|2021-09-25`:142, ...) match the audio-backed annotation station-days one-for-one. **All audio-backed TKW is already in the set.** The "additional TKW data the corpus holds" is 3 station-days behind audio-404, concentrated on two DFO_WDLP AMAR deployments.

## Lift options on the existing features

| Option | New dep? | Re-featurize / re-fetch? | Expected effect on TKW f1 |
|---|---|---|---|
| Operating-point / max-F1 threshold on logreg probs, threshold picked on a held-out group, applied cross-station | No (sklearn) | No | Small, real. ~0.43 to ~0.47-0.52, buys TKW recall by spending SRKW precision/recall. Bounded by TKW one-vs-rest PR curve (macro AUPRC 0.679, SRKW-easy so TKW lower). Adds no information; only chooses the operating point argmax misses. |
| Cost-sensitive threshold (explicit FN:FP cost) | No (sklearn) | No | Same lever as above expressed as a cost; same ceiling. |
| Probability calibration (`CalibratedClassifierCV`, sigmoid/isotonic) | No (sklearn) | No | ~0 direct f1 gain: monotone calibrators do not change ranking/AUC. Useful only to make the cost-sensitive threshold principled. |
| Model swap to `HistGradientBoostingClassifier` (sklearn-native gradient boosting, sample_weight) | No (sklearn) | No | Uncertain, likely modest. Captures nonlinear interactions logreg/RF miss, but RF already sits at high-precision/low-recall (0.711/0.172), i.e. the features under-separate TKW; a model swap cannot manufacture absent signal. |
| Random over/under-sampling | No (numpy) | No | ~0. Redundant with `class_weight="balanced"` already in place. |
| SMOTE / ADASYN | **Yes (imbalanced-learn)** | No | Uncertain and risky. Interpolating 781 TKW that rest on ~12 station-days will synthesize within-station-day neighbors, inflating cross-station-day optimism. Low expected durable value. |
| Change SRKW cap-per-day (uncap or lower) | No | **Yes (re-fetch)** | Marginal. With `class_weight="balanced"` already applied, prior change is largely absorbed by the weighting; lowering SRKW also discards majority data. SRKW audio is abundant so no download blocker, but low payoff. |
| New numpy/scipy **call-morphology / click features** (inter-click-interval histogram, pulse-rate, Teager-Kaiser click energy, click peak/centroid/bandwidth, high-band energy ratio) appended to the 129-dim vector | No (numpy/scipy) | **Yes (re-featurize audio)** | Highest structural upside and the only literature-supported durable lever. Capped by biology (see below). |

### Literature grounding for the feature lever (no downloads, search only)

- Leu et al. 2022, JASA 151(5):3197 (`doi:10.1121/10.0010450`): resident vs offshore killer-whale echolocation clicks separate on **spectral characteristics and modal ICI**, but **transients are click-sparse with no distinguishable modal ICI**; transient identification is "limited due to low numbers of clicks." This is the biological ceiling on TKW.
- SFU thesis (summit.sfu.ca etd23894, 2025): SRKW vs WCT (Bigg's) in Boundary Pass using a **Teager-Kaiser click detector + 12 click features** (click rate, duration, peak/centroid/bandwidth frequencies) reached **event-level** P 0.83 / R 1.00 / F2 0.96 with XGBoost/RF, and used class weights for imbalance (same as us). The lift came from **click-feature engineering**, not the classifier or the weighting. Note the metric is **event-level**, not per-3s-window, so it is not directly comparable to our window f1.
- Sharpe et al. 2017 (Bioacoustics) and Salish call-type-balancing work (`doi:10.1111/mms.70126`): ecotype/dialect discrimination rests on **pulsed-call type structure**, again a morphology signal the presence-oriented log-mel silhouette does not target.

The Teager-Kaiser energy operator and ICI extraction are pure numpy/scipy, so the feature lever needs **no new dependency**; it needs **compute to re-featurize audio**.

## Recommended methodology for ACX-Q

**Primary path: operating-point selection on the existing logreg, evaluated for durability.**
Keep the existing 129-dim features and the existing logreg (`class_weight="balanced"`). Replace argmax decision with a TKW decision threshold chosen to maximize TKW f1 on a held-out station-day group inside the train fold, then apply the frozen threshold to the leave-station-day-out test. Repeat over >=3 split seeds and report the spread. This is zero-new-dep, zero-re-fetch, and directly answers "how far does operating-point tuning carry the existing head." Expected outcome: TKW f1 ~0.45-0.52, with SRKW recall the explicit cost.

**Fallback / upside path (gated): add numpy/scipy click-morphology features, then re-fit.**
If the primary path stalls below the pass metric (likely, given the ceiling), append ICI-histogram / pulse-rate / Teager-Kaiser click-energy / click peak-frequency features to the vector, re-featurize the same 12 audio-backed TKW station-days plus matched SRKW/background, and re-fit logreg and `HistGradientBoostingClassifier`. This is the only route with structural headroom and stays inside numpy/scipy/sklearn, but it requires box compute to re-featurize and is itself research (the new features must be defined and validated). It does **not** add station-days, so the cross-station-day variance ceiling is unchanged.

**Rejected alternatives:**
- *SMOTE/imbalanced-learn:* rejected as a primary lever. It is a new dependency and, with TKW resting on ~12 concentrated station-days, synthetic interpolation produces near-duplicate within-day neighbors that leak into a station-day-blocked eval and overstate lift. If trialed at all, only as a sensitivity check behind the O0 dep gate.
- *Calibration as a lift mechanism:* rejected; monotone calibration does not move f1 or AUC, only probability quality.
- *"Fetch more TKW":* rejected as infeasible from this corpus. Only 3 additional Salish TKW station-days exist (StrGeoN2/StrGeoS2, 245 annotations) and they are audio-404; obtaining them needs an alternate audio source and a license re-check, for a thin, provider-concentrated gain.
- *Uncapping SRKW:* rejected as low-payoff because `class_weight="balanced"` already neutralizes most of the prior shift.

## Recommended PASS METRIC for the TKW head (checkable, before training)

A candidate TKW head **passes ACX-Q** only if, on the existing leave-station-day-out protocol (TKW held in train and test, TKW test support >= ~186 windows across >= 3 test station-days):

1. **median TKW f1 across >=3 split seeds > 0.434** (strictly beats the logreg baseline; a single-seed bump does not count), and
2. **TKW recall >= 0.478** at the reported operating point (recall floor = baseline; f1 may not be bought by trading recall away), and
3. **SRKW f1 >= 0.84** (majority head degraded by no more than ~0.03 from the 0.8725 baseline), and
4. **per-seed TKW f1 spread is reported**, because the TKW test rests on only ~3 to 4 station-days and is high-variance; the median, not the best seed, is the decision number.

This is the floor; it does not assert any specific achievable f1, which only the gated ACX-B / ACX-TRAIN fit can measure.

## Gated items for O0

- **imbalanced-learn (SMOTE/ADASYN):** NEW dependency. O0 dep-gate required. Recommendation: do not add; low expected durable value plus station-day leakage risk.
- **More TKW station-days (StrGeoN2/StrGeoS2):** audio-404 in the DCLDE bucket; needs an alternate audio source and a license re-check, i.e. an O0-gated re-fetch. Only 3 station-days / 245 annotations, provider-concentrated; recommend deprioritize.
- **New numpy/scipy click-morphology features:** no new dependency, but requires **box compute** to re-featurize the audio windows (ffmpeg input-seek + decode), an O0 box-compute gate.
- **`HistGradientBoostingClassifier`:** sklearn-native, **no gate**.

## Honesty locks

- Every number above carries its split and support; the eval-backed numbers are leave-station-day-out.
- No claim exceeds what a held-out eval supports. The 0.45-0.52 and 0.50-0.65 ranges are analytic/literature-grounded expectations, not fitted results; only ACX-B/ACX-TRAIN can confirm a fitted number.
- `single_vs_multiple` stays **BLOCKED** (no source-count labels).
- HUD wording stays at or below the eval: TKW remains "estimate + confidence, SRKW-dominated (low-confidence TKW)."
