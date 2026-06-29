# ACX-ADV_VERDICT — adversarial audit of the v2 ecotype-TKW strengthen

- Lane: `BSWR-ACX`. Wave: `ACX-ADV` (post `ACX-B` / `ACX-TRAIN`).
- Verdict basis: `infra/acoustic/eval_report_dclde_v2.json` + the runnable assertion
  harness `modeling/acoustic/acx_adv_assert.py` (**55/55 checks PASS, 0 open P0/P1**).
  Every claim below cites a measured number, not an assertion.
- Honesty locks held: served `classification.json` UNCHANGED; `call_type` diagnostic;
  `single_vs_multiple` blocked; no whale count / pod-ID / S1–S40 claim; no commit.

## Result on the fixed pass metric (MEDIAN decides, per O0)

| path | median TKW f1 | median TKW recall | median SRKW f1 | median TKW AUPRC | verdict |
|------|---------------|-------------------|----------------|------------------|---------|
| feature-only (operating-point) | 0.704 | 0.803 | **0.693** | 0.818 | **MISS** (SRKW f1 < 0.84) |
| Perch 2.0 embedding | **0.805** | **0.788** | **0.902** | **0.956** | **PASS** (all three) |

Pass metric (fixed before training): median TKW f1 > 0.434 AND median TKW recall >= 0.478
AND median SRKW f1 >= 0.84, each seed >= ~186 TKW windows / >= 3 test station-days.

- **feature-only MISS** is structural, not a tuning failure: under leave-station-OUT the
  held-out test stations are exactly the TKW-bearing ones, so test folds are TKW-enriched
  (SRKW fraction 0.33–0.69 vs the v1 day-out test's ~0.83). Any threshold that lifts TKW
  recall costs SRKW precision, so SRKW f1 >= 0.84 is nearly unreachable on the TKW-heavy
  folds. Only the most SRKW-balanced fold (seed 1, test=StraitofGeorgia) reaches SRKW f1 0.878.
- **Perch PASS**: the learned embedding lifts BOTH classes (SRKW f1 rises to 0.90 while TKW
  f1 rises to 0.805), so the operating point no longer has to trade the majority away.

## P0 (ship-blocking) — ZERO open

1. **Split leakage / leave-station-OUT integrity — CLEAN (measured, all 5 seeds).** Train∩test
   station, station-day, AND soundfile intersections are all empty; no TKW test station appears
   in the TKW train set; >= 2 TKW stations always retained in train; per-seed support floor met
   (248–405 TKW windows / 3–5 station-days). This closes the v1 leave-station-DAY-out
   "recognize the recorder" confound the R4 audit flagged.
2. **Served-contract integrity — CLEAN.** `web/public/hydrophone/slice/classification.json` is
   byte-unchanged: still `bam-srkw-presence-v0`, `classes == ["srkw_call_presence"]`,
   `spawnCountBasis == "presence_only"`; ecotype / call type / single-vs-multiple still in
   `honesty.not_claimed`; no pod / individual-ID / S1–S40 / Bigg's-presence class anywhere
   outside the disclaimer. v2 is an EVAL artifact only.
3. **Heads guard — CLEAN.** `heads.assert_shippable("call_type")` and `("single_vs_multiple")`
   both still raise. The Perch lift is on the ecotype head only.
4. **promotion.json contract-flip — CANNOT HAPPEN.** `data/models/promotion.json`
   (`promoted:true, effective_confidence:0.0, repr_id:null, kernel_version:"fit-v1"`) is the
   **kernel/forecast (kinematic) track**: written by `routers/promotion.py`, read by
   `kernel_model/serve.py` for the forecast kernel's served confidence. It has no
   `classification`/`acoustic`/`ecotype`/`model_version` key. The acoustic `classification.json`
   is a static public asset; its loader (`web/lib/scene/reenactment/loaders.ts`) has **no**
   promotion linkage. The two ML tracks are disjoint (PROGRAM lock #8), so promoting an ecotype
   head is a deliberate edit of `classification.json` at `ACX-ACCEPT` — `promotion.json` cannot
   silently flip it.
5. **Overclaim baked into the eval — NONE.** feature-only `verdict.passes == false`; any ship
   is flagged `PROPOSED` and explicitly held at `ACX-ACCEPT`; the report never writes a served
   field.

## P1 (disclose / robustness) — all DISCLOSED in the v2 eval; none block the median verdict

1. **High per-fold variance (DISCLOSED).** The MEDIAN passes (O0 lock), but only **3/5**
   individual folds meet all three per-fold: seed 0 (test=StrGeoN1+StrGeoS1) SRKW f1 0.674;
   seed 1 (test=StraitofGeorgia) TKW recall 0.323. The variance is **operating-point
   instability** (validation-chosen threshold swings 0.02–0.96 across stations), not a
   separation failure — the **threshold-free TKW AUPRC is 0.90–0.98 on every fold (median
   0.956)**, a large lift over v1's 0.679. AUPRC is the robust single indicator; f1 at a single
   point is fold-sensitive. *Recommended (optional B-loop, O0 to decide): a more stable threshold
   policy (e.g. averaging the operating point over multiple inner-val stations, or cutting on the
   prior-recalibrated posterior) to tighten the weak folds. Not required to meet the locked median.*
2. **Site/habitat confound — CHECKED and NOT supported (DISCLOSED).** TKW is geographically
   concentrated (Strait of Georgia), raising the worry that Perch reads site acoustics as a TKW
   proxy. Evidence rejects it: the within-Strait-of-Georgia fold (seed 1) is the **weakest**
   (recall 0.32, the opposite of what a site shortcut predicts), and a cross-region fold (seed 4,
   test=Haro Strait South + StrGeoN1) generalizes (TKW f1 0.805). The lift tracks call morphology,
   not recorder site.
3. **Prior mismatch (DISCLOSED, mitigated).** Sampled TKW prior ~20% of the SRKW/TKW pool vs the
   ~5% deployment prior. Reported confidence is prior-recalibrated toward 5% (e.g. Perch TKW mean
   posterior 0.84 raw → 0.79 recalibrated); raw precision/f1 remain prior-sensitive, so the HUD
   must report the recalibrated, median-level estimate + confidence, never a raw per-fold f1.
4. **Few-encounter base (DISCLOSED).** TKW still rests on 6 stations / 12 station-days / a handful
   of encounters; metrics are reported as per-seed spread, not a point estimate.
5. **Compute provenance (DISCLOSED).** Perch 2.0 ran via the `perch_v2_cpu` variant on CPU on the
   dev host (no GPU needed, no Kaggle credentials needed — `kagglehub` public model). 5,485/5,525
   windows embedded (40 audio-fetch failures; 23 in the SRKW/TKW pool, dropped). Weights +
   `perch_embeddings_v1.npz` are in the gitignored box; only the 24 KB eval ships in-repo.

## License guard (Perch 2.0 + transitive deps) — PASS

- Perch 2.0 weights: **Apache-2.0** (HF `cgeorgiaw/Perch` card; `chirp/models/perch_2.py` header; arXiv 2508.04665). Served from Kaggle Models `google/bird-vocalization-classifier/.../perch_v2_cpu`.
- `perch-hoplite` 1.0.2: **Apache-2.0**. `google-research/perch`: **Apache-2.0**.
- `tensorflow` 2.20.0, `tensorflow-hub`, `kagglehub`: **Apache-2.0**.
- No NC / NC-SA / ND / unclear artifact encountered → no STOP-to-O0 triggered. The corpus
  CC-BY-SA-4.0 ShareAlike + attribution travel onto the embedding cache (a derivative) and onto
  any classifier trained on it; permissive Apache-2.0 inputs are compatible.

## Proposed honest HUD wording (for the ACX-ACCEPT gate — NOT yet applied)

If O0 promotes the Perch ecotype head, the served wording should stay at estimate + confidence,
median-level, prior-recalibrated, and add no count/ID claim. Proposed exact strings:

- Primary: `"Estimated ecotype: Southern Resident (SRKW)"` / `"Estimated ecotype: Bigg's / Transient (TKW)"`, with `"confidence <p>"` where `<p>` is the prior-recalibrated posterior.
- Provenance chip: `"ecotype: learned-embedding estimate (Perch 2.0), cross-station eval — median TKW F1 0.80, AUPRC 0.96; per-station variance"`.
- Honesty (unchanged): keep whale count, pod / individual ID, call type, and single-vs-multiple in `not_claimed`; `spawnCountBasis` stays `presence_only` unless O0 rules the count-basis change.

## Verdict

- **feature-only: does NOT clear the bar** (median SRKW f1 0.693 < 0.84; structural to leave-station-OUT).
- **Perch 2.0 embedding: CLEARS the fixed median pass metric** (TKW f1 0.805, recall 0.788, SRKW
  f1 0.902, TKW AUPRC 0.956), leak-free, license-clear, with high per-fold variance honestly
  disclosed and the site-confound checked and rejected. **Zero open P0/P1.**
- Recommendation to O0: the Perch path is the proposed ship candidate. The serve / count-basis
  change to `classification.json` + the exact HUD wording is the **`ACX-ACCEPT`** gate. **PAUSED there.**
