# ACX-METHODOLOGY — qualified methodology + fixed pass metrics (O0-ruled)

- Lane: `BSWR-ACX` (acoustic-heads-strengthen). Wave: `ACX-Q` (closed).
- Authority: O0 ruling on the ACX-Q gate (operator pre-approved the embedding upside).
- `repo_state_verified_against`: `61ba1d69ee36cf605f7ba741bdaa1defa8762834`.
- Inputs: the four `findings/ACX-*.md` research docs; `infra/acoustic/eval_report_dclde_v1.json`; `features_v1.npz` (present locally, gitignored).

This doc freezes the method per head and the pass metric **before any training**. It
is the contract `ACX-B` / `ACX-TRAIN` / `ACX-ADV` are measured against.

## Locked decisions (O0)

1. **Ecotype-TKW, feature-only path — APPROVED.** Operating-point / decision-threshold
   selection on the existing logistic regression over the 129-dim log-mel silhouette.
   Split is **leave-station-OUT** (whole stations held out, *not* leave-station-day-out),
   `>= 3` seeds, report the **median** (never the best seed). Posterior confidence is
   **recalibrated toward the ~5% natural TKW prior**. No new dependency, no download, no
   box: runs offline on `features_v1.npz`.
2. **Ecotype-TKW, Perch 2.0 embedding path — APPROVED (operator).** New dependency
   TensorFlow + Perch 2.0 (Apache-2.0) weights + a one-time box embedding extraction over
   the ~5,525 windows, feeding the **same** sklearn head, evaluated on the **same**
   protocol as path 1. **License guard (hard):** confirm the actual Perch 2.0 weights and
   every transitive dependency are Apache-2.0 / CC-BY (license-clear against the
   CC-BY-SA-4.0 corpus). If any artifact is NC / NC-SA / ND / unclear, **STOP and return to
   O0 before downloading it.** Weights + extracted embeddings → box, gitignored; only the
   small inference artifact + eval ship in-repo.
3. **Ship whichever path clears the pass metric** on the shared protocol. If both miss,
   return the honest **"no reliable lift; ecotype wording unchanged."** TensorFlow/Perch is
   the chosen framework over torch.
4. **call_type STAYS DIAGNOSTIC, not wired** (`heads.assert_shippable` keeps refusing it).
   **single_vs_multiple stays BLOCKED.** No whale count / pod-ID / S1–S40 catalog claim.
5. **Contract change is held at `ACX-ACCEPT`.** Promoting any improved ecotype head into the
   served `web/public/hydrophone/slice/classification.json` is a count-basis/contract change,
   a SEPARATE O0 gate — not a model swap. During `ACX-B`/`ACX-ADV` we AUDIT that
   `data/models/promotion.json` cannot silently flip the served acoustic contract and report
   the finding. No served-contract change without `ACX-ACCEPT`.

## Pass metric (FIXED before training; identical for both paths)

A path **ships** only if, on the shared **leave-station-OUT**, `>= 3`-seed protocol, the
**MEDIAN across seeds** satisfies ALL of:

- **TKW f1 > 0.434** (the v1 logreg leave-station-day-out baseline), AND
- **TKW recall >= 0.478** (the v1 recall floor; lift must not be bought by trading recall away), AND
- **SRKW f1 >= 0.84** (the majority class is not degraded by more than ~0.03 from the v1 0.8725).

Each seed must additionally meet the support floor: **TKW test support >= ~186 windows AND
>= 3 test station-days**. **Per-seed spread is reported** (min / median / max per metric).
The **median decides** — never the best seed. If neither path clears the bar, the honest
return is "no reliable lift; ecotype wording unchanged" and `classification.json` is untouched.

## Shared evaluation protocol (both paths)

- **Split: leave-station-OUT.** Whole stations are held out for test, so the test
  recorders are never seen in training (closes the R4 "recognize the recorder" confound that
  leave-station-day-out left open). TKW appears in BOTH train and test because TKW spans 6
  stations; remaining TKW stations stay in train.
  - TKW geography (measured from `features_v1.npz`): TKW windows = 781 over **6 stations** /
    12 station-days: StraitofGeorgia 248 (5 TKW-days), StrGeoN1 237 (2), StrGeoS1 168 (2),
    HaroStraitSouth 57 (1), BoundaryPass 47 (1), SwanChan 24 (1). SRKW = 3005, background = 1739.
  - Per seed: shuffle the 6 TKW stations, greedily move whole stations into the test fold
    until `test TKW windows >= 186` and `test TKW station-days >= 3`, always leaving `>= 2`
    TKW stations in train. The held-out stations contribute ALL their windows (TKW/SRKW/bg)
    to test; everything else trains. This yields genuinely distinct folds across seeds.
- **Head:** binary SRKW vs TKW on call windows (same task as v1 ecotype head). `StandardScaler`
  fit on train only. Logistic regression (`class_weight="balanced"`, as v1).
- **Operating point:** the decision threshold on `P(TKW)` is chosen on a **held-out
  train station** (inner validation, never the test stations) to maximize TKW f1, then
  **frozen and applied to test**. No test-set threshold tuning.
- **Confidence recalibration:** reported `P(TKW)` is corrected from the sampled training prior
  (TKW ≈ 20% of the SRKW/TKW pool, the keep-all-TKW + SRKW-cap=40 sampling) toward the ~5%
  deployment prior via the prior-odds transform. This affects only the reported confidence
  (honesty), recorded alongside — the f1/recall/precision pass metric is measured at the
  frozen operating point.
- **Metrics emitted per seed and aggregated:** per-class precision / recall / f1 / support,
  confusion, macro-f1, AUPRC (one-vs-rest), the explicit leave-station-out train/test station
  lists, the recalibrated-confidence summary, and the stated confounds. Median + min/max spread
  across seeds. Output: `infra/acoustic/eval_report_dclde_v2.json`.
- **Perch path** is identical except the feature matrix is the Perch 2.0 embedding per window
  (extracted on the box from re-fetched segment audio, aligned 1:1 to the `features_v1.npz`
  rows via `(dataset, soundfile, t0)`), fed into the same logreg + threshold + recalibration.

## Method selected per head, with rejected alternatives

### ecotype-TKW — run BOTH paths on the shared protocol; ship the one that clears the bar
- **Path A (feature-only operating-point):** threshold/operating-point selection + prior
  recalibration on the existing 129-dim features. Expected analytic envelope (R1): TKW f1
  ~0.45–0.52 by buying recall with SRKW precision; no new generalization. Zero new risk.
- **Path B (Perch 2.0 embedding):** learned embedding as features into the same head.
  Higher potential ceiling (R3: license-clear embeddings reach few-shot orca-ecotype ROC-AUC
  0.90–0.945 on a *different* split/metric — plausible but **unverified until trained**).
- **Rejected (R1/R3):** SMOTE / `imbalanced-learn` (new dep + station-day leakage);
  calibration-as-lift (monotone, ~0 f1 gain); "fetch more TKW station-days" (the only
  unfetched Salish TKW days, StrGeoN2/StrGeoS2, are audio-404); SRKW uncap (neutralized by
  the existing `class_weight="balanced"`); torch/NC embeddings BirdNET / AVES2 / NatureLM
  (CC-BY-NC-SA — conflicts with the CC-BY-SA-4.0 corpus, STOP-to-O0).

### call_type — STAY DIAGNOSTIC, not wired
- Only `pulsed` has ≥3-station support; whistle (2 stations), click (1), buzz (2) cannot be
  leave-one-station-out evaluated → reproduces the v1 majority collapse (whistle recall 0.0).
  `pulsed_call` = "any S-code" is the forbidden S1–S40 catalog in disguise. `assert_shippable`
  keeps refusing it; HUD makes no call-type claim. A coarse head would need a re-annotation
  pass to add a 3rd whistle / 2nd click station first (R2) — a future O0 data decision.

### single_vs_multiple — BLOCKED, unchanged
- No source-count labels. Stays blocked; never revived without an O0-approved counting corpus.

## promotion.json contract-flip audit (preliminary; re-confirmed in ACX-ADV)

`data/models/promotion.json` (`promoted:true, effective_confidence:0.0, repr_id:null,
kernel_version:"fit-v1"`) belongs to the **kernel/forecast (kinematic) track**: it is written
by `src/aws_backend/routers/promotion.py` and read by `src/aws_backend/kernel_model/serve.py`
to set the served *forecast kernel* confidence. The acoustic `classification.json` is a
**static public asset** under `web/public/hydrophone/slice/`, loaded directly by the web slice
(`web/lib/scene/reenactment/loaders.ts`, `hydrophone/catalog.ts`) with **no promotion linkage**.
The two systems are disjoint (PROGRAM lock #8: the acoustic and BRE/BSS tracks stay separate),
so `promotion.json` **cannot** flip the served acoustic ecotype contract. Promoting an ecotype
head is a deliberate edit of `classification.json`, gated at `ACX-ACCEPT`. (Full verdict in
`ACX-ADV_VERDICT.md`.)

## Gated items already cleared / still open

- Cleared by O0: feature-only run (offline); the Perch embedding upside (new dep TF + weights +
  one-time box extraction).
- Hard guard still binding: the Perch 2.0 + transitive-dep **license confirmation** must pass
  (Apache-2.0 / CC-BY) before any weights download; any NC/ND/unclear artifact STOPs to O0.
- Held for `ACX-ACCEPT`: the `classification.json` contract/count-basis change + the exact HUD
  wording.

Paused state after this doc: proceed to `ACX-B` (implement both paths offline-reproducible),
then `ACX-TRAIN` (license guard → Perch download → box extraction → train+eval both → v2 eval),
then `ACX-ADV`. PAUSE before `ACX-ACCEPT`.
