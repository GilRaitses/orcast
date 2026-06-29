# ACX-R2 finding: coarse call_type — ship-or-stay

**Lane:** BSWR-ACX (acoustic-heads-strengthen) · **Wave:** ACX-R (read-only research) · **Author:** ACX-R2
**Topic:** Can a coarse `call_type` head (CK/W/BP, or at minimum pulsed_call vs whistle) ship honestly cross-station, or must it stay diagnostic?

---

## Summary (recommendation)

**STAY DIAGNOSTIC. Do not ship `call_type` in ACX-Q.** Measured against the three present DCLDE-2027 originals, the only coarse class with ≥3-station support is `pulsed` (BoundaryPass + LimeKiln + Tekteksen). Every candidate minority class is too thin to be cross-station honest: `whistle` lives at only 2 stations (LimeKiln, Tekteksen), `buzz` at 2 (LimeKiln, Tekteksen), and `click` at exactly **1** (LimeKiln only). Because the minority class never appears in ≥2 *training* stations plus a held-out test station, any leave-one-station-out (LOSO) fold trains whistle on at most one station — which is exactly why the v1 diagnostic collapsed to majority class (whistle recall 0.0, f1 0.0, support 38; macro-f1 0.4296, split train=BoundaryPass+Tekteksen / test=LimeKiln). No relabel of existing annotations fixes this: the gap is missing *acoustic events* at the third station, not mislabeled text, so closing it requires a gated re-annotation pass, not numpy/sklearn work. `call_type` stays diagnostic and unwired; `heads.assert_shippable` should keep refusing it.

---

## 1. Coarse inventory by station (measured)

Read-only parse of the local originals (ad-hoc python, stdout only; `comments` columns never read — R02 PII). Mapping mirrors `modeling/acoustic/call_type_diag.py::coarse`: `signal_type` W/whistle→whistle, CK/click→click, BZ/buzz→buzz; `call_type`/`Call Type` exact "whistle"/"click"/"buzz"; any `S\d` code → pulsed.

| coarse class | BoundaryPass (vfpa) | LimeKiln (smru) | Tekteksen (simres) | # distinct stations |
|---|---:|---:|---:|---:|
| pulsed (S-codes) | 877 | 412 | 1975 | **3** |
| whistle | 0 | 40 | 321 | **2** |
| click | 0 | 39 | 0 | **1** |
| buzz | 0 | 11 | 50 | **2** |
| whistle/tone variant* | 0 | 0 | 220 | 1 |
| total annotation rows | 2032 | 1471 | 4319 | — |

Source files: `infra/acoustic/data/corpora/dclde-2027/originals/vfpa/annot_BP_man_det.csv` (BoundaryPass), `…/smru/annot_LimeKiln-Encounters_man_det.csv` (LimeKiln), `…/simres/*.selections.txt` (143 SIMRES Tekteksen Raven tables, tab-delimited).

\* `whistle/tone` (220 at Tekteksen) is a near-synonym the diagnostic drops; even if merged into `whistle` it adds **no new station** (Tekteksen already has whistle).

**Confirms v1.** The five strict numbers in `eval_report_dclde_v1.json::call_type_diagnostic.label_inventory` (BoundaryPass|pulsed 877, LimeKiln|pulsed 412, LimeKiln|whistle 40, Tekteksen|pulsed 1975, Tekteksen|whistle 321) reproduce exactly. New facts beyond v1: LimeKiln also carries click 39 and buzz 11; Tekteksen also carries buzz 50; **BoundaryPass `signal_type` is 100% empty (2032/2032 rows)** and its `call_type` has zero whistle/click/buzz — VFPA annotated only pulsed S-codes/Unk, so non-pulsed presence at BoundaryPass is *unannotated*, not confirmed absent.

---

## 2. Cross-station support — which taxonomy is evaluable

Gate (locked): `call_type` ships only at a coarse taxonomy that clears a held-out, cross-station eval with **non-trivial minority recall** (not a majority collapse). For honest LOSO that means the minority class must appear in the held-out test station **and** in ≥2 training stations (so the model learns a station-invariant cue rather than memorizing one station's channel/noise).

LOSO feasibility per minority class (measured):

| minority | present at | leave-out=BoundaryPass | leave-out=LimeKiln | leave-out=Tekteksen | verdict |
|---|---|---|---|---|---|
| whistle | LimeKiln, Tekteksen | test has 0 whistle | train=1 whistle station | train=1 whistle station | **never ≥2 train + test** |
| buzz | LimeKiln, Tekteksen | test has 0 buzz | train=1 buzz station | train=1 buzz station | **never ≥2 train + test** |
| click | LimeKiln only | test has 0 click | no train minority | test has 0 click | **never cross-station** |

- **pulsed_call vs whistle (2-class):** NOT honestly LOSO-evaluable. whistle exists at only 2 of 3 stations, so every fold trains whistle on ≤1 station; testing on BoundaryPass yields zero whistle (undefined recall), testing on LimeKiln/Tekteksen trains whistle on the single remaining station — reproducing the v1 majority collapse (whistle recall 0.0 / f1 0.0 / support 38; pulsed_call f1 0.8593 / support 116; macro-f1 0.4296).
- **3-way CK/W/BP (click/whistle/pulsed):** strictly worse. `click` is single-station (LimeKiln, 39), so the click class cannot be cross-station at all. Collapses on two of three classes.
- **Only `pulsed` is ≥3-station** — but a one-class head is not a classifier.

**Conclusion:** no coarse taxonomy on the present data clears a ≥3-station LOSO with non-trivial minority recall. The honest contrast remains diagnostic.

---

## 3. Honest relabel budget

Framed as the dispatch asks — how many annotations need coarse relabeling to give the minority class a third station:

- **S-code → `pulsed`: already complete and free.** 3264 pulsed annotations total (877 + 412 + 1975) across all 3 stations. No further relabel needed; pulsed is not the bottleneck.
- **whistle → 3rd station: not relabelable.** A 3-station whistle requires whistle at BoundaryPass. BoundaryPass `signal_type` is empty for all 2032 rows and `call_type` contains zero whistle/W tokens — there is **no existing label to remap**. Closing it means a fresh listening/spectrogram **re-annotation** pass over BoundaryPass (provider VFPA) audio; review surface ≈ 2032 BoundaryPass detections (or the underlying audio, larger). This is an annotation/data task, not numpy/sklearn, and is **O0-gated** (outside ungated scope).
- **click → 2nd station: not relabelable.** click exists only at LimeKiln (39). BoundaryPass and Tekteksen carry zero click tokens (Tekteksen `Call Type` has no click value; BoundaryPass `signal_type` empty). A 2nd click station also requires fresh re-annotation of BoundaryPass or Tekteksen audio.
- **Latent merges that do NOT help:** Tekteksen `whistle/tone` (220) and LimeKiln `W?` (8, low-confidence) can fold into `whistle`, but both sit at stations that already have whistle — they raise within-station count, not station count.

**Net:** the pure label-remap budget that adds a cross-station minority is **0** (nothing remappable lives at a new station). The real cost is a re-annotation campaign on ≥1 additional station for whistle (and ≥1 more for click) — a gated proposal for O0, not an ACX-B/numpy deliverable.

---

## 4. Openly-licensed coarse KW call-type corpus survey (no download)

| Source | Coarse call-type labels? | New cross-station whistle/click? | License | Verdict |
|---|---|---|---|---|
| DCLDE-2027 per-provider `signal_type` (in hand) | yes (sparse) | no — only BP/LK/TK exist; BP empty | CC-BY-SA-4.0 | OPEN, but exhausted (this is the present data) |
| Watkins Marine Mammal Sound Database (WHOI) | species/location/date metadata; not systematic whistle/click/pulsed call-type | low — global KW populations, not SRKW; clip-level, no station grid | free for personal/academic, **commercial prohibited**, attribution required | **NC** |
| Orcasound `acoustic-sandbox` / Pod.Cast (AWS Open Data) | mostly **binary presence** (call vs no-call); wiki says labels "may also indicate call type, whistles, clicks" but open archive is positive/negative segments | possibly new stations for *presence*, not for coarse call-type; **Lime Kiln was an Orcasound node → station overlap risk, not independent** | **CC-BY-NC-SA-4.0** (data); tools repo AGPL-3.0 | **NC + SA** |
| Ford / OrcaLab NRKW call catalogues (e.g. Ford catalog) | fine call-type catalog | n/a | copyrighted catalog, not openly licensed | **ND / closed** |

Notes: no download performed (web verdicts only). Watkins and Orcasound are both **non-commercial**; Orcasound additionally carries **ShareAlike**. The BSW workbench `SIGN_OFF.md` authorizes NC scope for that workbench, but whether an NC/SA corpus may feed a head whose output lands in the served `classification.json` is a **licensing decision for O0** (NC compatibility + SA copyleft on derived artifacts). None of these surveyed sources is confirmed to add an *independent third station of coarse whistle/click call-type labels* without a fetch + re-annotation effort.

---

## 5. Recommendation for ACX-Q

**STAY DIAGNOSTIC.** Select no `call_type` method for training in ACX-Q. Keep the v1 `call_type_diagnostic` block as the honest record; keep `heads.assert_shippable` refusing `call_type`; the HUD makes no call-type claim.

Rejected alternatives (and why):
- **Ship pulsed_call vs whistle now** — rejected: whistle is 2-station, every LOSO fold trains whistle on ≤1 station → majority collapse (v1 already demonstrated recall 0.0). Would violate the "no majority collapse" lock.
- **Ship 3-way CK/W/BP** — rejected: click is single-station (LimeKiln only); class is not cross-station evaluable at all.
- **Merge `whistle/tone` + `W?` to inflate whistle** — rejected: adds count, not stations; does not change LOSO feasibility.
- **Pull Watkins / Orcasound to backfill whistle/click** — deferred to O0: NC (and SA for Orcasound) licensing, SRKW/station-independence questions, and a required re-annotation step; not an ungated numpy/sklearn action.
- **Train on a learned embedding to rescue minority recall** — out of this finding's scope; that is the separate ACX costed-embedding research item and a torch dependency is O0-costed, never self-approved.

---

## 6. Recommended PASS METRIC for `call_type` (checkable, BEFORE training)

`call_type` may be wired into `classification.json` **only if** a held-out eval clears **all** of:

1. **Coverage:** the chosen coarse taxonomy has **every class present at ≥3 distinct stations**, and the held-out test station contains the minority class (so the minority is trained on ≥2 stations and tested on a third).
2. **Split:** leave-one-station-out across **≥3 stations**, reported with per-class support and the train/test station lists and confounds.
3. **Minority recall:** **minority-class recall ≥ 0.50** on the held-out station (non-trivial, not majority collapse).
4. **Balance:** **macro-f1 ≥ 0.60** across the LOSO folds.

If any condition fails, `call_type` **stays diagnostic, not wired**, and the HUD makes no call-type statement. (Thresholds 0.50 / 0.60 are proposed defaults for O0 to confirm; the structural condition #1 is the hard gate and is currently **unmet** on the present data.)

---

## 7. Gated items for O0

- **G1 — Relabel/re-annotation budget (PRIMARY BLOCKER):** a 3rd whistle station and a 2nd click station require a fresh annotation pass on BoundaryPass (VFPA, ≈2032 detections / underlying audio) and on BoundaryPass-or-Tekteksen audio for click. This is a data-collection task, not numpy/sklearn — needs O0 authorization, owner, and effort estimate before `call_type` can ever be cross-station.
- **G2 — Corpus fetch (deferred):** any Watkins or Orcasound pull is gated. Resolve license first: Watkins = NC; Orcasound = CC-BY-NC-SA (NC + ShareAlike). Confirm NC-compatibility with the served `classification.json` claim and SA copyleft on any derived weights/artifact, plus station-independence (Lime Kiln overlaps Orcasound) and SRKW relevance (Watkins is global KW).
- **G3 — New dependency:** none requested in this finding. Any embedding/torch route is a separate O0-costed proposal, never a default.
- **No commit, no served-JSON edit, no training performed.** This wave wrote only this findings file.
