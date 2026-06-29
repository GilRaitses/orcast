#!/usr/bin/env python3
"""ACX-ADV adversarial assertion harness (ACX-R4 P0/P1 checklist).

Re-runs the leave-station-OUT split used by the v2 eval and ASSERTS the
structural honesty invariants the ACX-adversarial.md checklist requires, then
audits the served contract + promotion.json. Prints one PASS/FAIL per check and
exits non-zero on any FAIL so the verdict cites a measured result, not a claim.

Offline; numpy + sklearn only. Touches nothing served. Run:
  python3 modeling/acoustic/acx_adv_assert.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from train_eval import leave_station_out_indices

ROOT = Path(__file__).resolve().parents[2]
FEATS = ROOT / "infra" / "acoustic" / "data" / "corpora" / "dclde-2027" / "features_v1.npz"
V2 = ROOT / "infra" / "acoustic" / "eval_report_dclde_v2.json"
CLASSIFICATION = ROOT / "web" / "public" / "hydrophone" / "slice" / "classification.json"
PROMOTION = ROOT / "data" / "models" / "promotion.json"
SEEDS = (0, 1, 2, 3, 4)

fails: list[str] = []
results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    if not ok:
        fails.append(name)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))


def main() -> int:
    d = np.load(FEATS, allow_pickle=True)
    ye = d["y_ecotype"].astype(str)
    pool = np.isin(ye, ["SRKW", "TKW"])
    y = ye[pool]
    station = d["dataset"].astype(str)[pool]
    station_day = d["groups"].astype(str)[pool]
    soundfile = d["soundfile"].astype(str)[pool]

    print("== P0: split-leakage + leave-station-OUT (per seed) ==")
    for seed in SEEDS:
        tr, te, test_stations, floor = leave_station_out_indices(
            station, station_day, y, seed=seed)
        tr_st, te_st = set(station[tr]), set(station[te])
        tr_sd, te_sd = set(station_day[tr]), set(station_day[te])
        tr_sf, te_sf = set(soundfile[tr]), set(soundfile[te])
        tkw_tr_st = {s for s in tr_st if (y[tr][station[tr] == s] == "TKW").any()}
        tkw_te_st = {s for s in te_st if (y[te][station[te] == s] == "TKW").any()}

        check(f"seed{seed} station intersection empty",
              tr_st.isdisjoint(te_st), f"shared={tr_st & te_st}")
        check(f"seed{seed} station-day intersection empty",
              tr_sd.isdisjoint(te_sd), f"n_shared={len(tr_sd & te_sd)}")
        check(f"seed{seed} soundfile intersection empty",
              tr_sf.isdisjoint(te_sf), f"n_shared={len(tr_sf & te_sf)}")
        check(f"seed{seed} leave-station-OUT for TKW (no TKW test station in TKW train)",
              tkw_tr_st.isdisjoint(tkw_te_st), f"overlap={tkw_tr_st & tkw_te_st}")
        check(f"seed{seed} >=2 TKW stations retained in train",
              len(tkw_tr_st) >= 2, f"tkw_train_stations={sorted(tkw_tr_st)}")
        check(f"seed{seed} support floor met (>=186 TKW windows AND >=3 station-days)",
              floor["meets_floor"],
              f"win={floor['test_min_windows']} days={floor['test_min_station_days']}")

    print("== P0: served contract - presence UNCHANGED + ecotype WIRED (O0 ACX-ACCEPT) ==")
    cj = json.loads(CLASSIFICATION.read_text())
    check("presence model_version still bam-srkw-presence-v0 (presence head unchanged)",
          cj["model_version"] == "bam-srkw-presence-v0", cj["model_version"])
    check("classes == ['srkw_call_presence'] (presence head contract unchanged)",
          cj["classes"] == ["srkw_call_presence"], str(cj["classes"]))
    nc = cj.get("honesty", {}).get("not_claimed", [])
    # ecotype is now SERVED as an estimate (O0-approved), so it must NO LONGER be
    # in the document-level not_claimed; but everything else stays locked.
    check("ecotype removed from document not_claimed (now SERVED as an estimate)",
          not any("ecotype" in s.lower() for s in nc), str(nc))
    check("whale count still in not_claimed", any("whale count" in s.lower() for s in nc), "")
    check("pod / individual ID still in not_claimed",
          any("pod" in s.lower() or "individual id" in s.lower() for s in nc), "")
    check("call type still in not_claimed", any("call type" in s.lower() for s in nc), "")
    check("single vs multiple still in not_claimed",
          any("single vs multiple" in s.lower() for s in nc), "")
    check("spawnCountBasis still 'presence_only'",
          cj.get("summary", {}).get("spawnCountBasis") == "presence_only",
          str(cj.get("summary", {}).get("spawnCountBasis")))
    check("spawnCount unchanged (presence-only, == 1)",
          cj.get("summary", {}).get("spawnCount") == 1, str(cj.get("summary", {}).get("spawnCount")))

    print("== P0: ecotype block is an estimate (no overclaim), with provenance ==")
    eco = cj.get("ecotype", {})
    check("ecotype.served is true and claim == 'estimate'",
          eco.get("served") is True and eco.get("claim") == "estimate", str(eco.get("claim")))
    check("ecotype.estimate is SRKW or TKW (coarse ecotype only)",
          eco.get("estimate") in ("SRKW", "TKW"), str(eco.get("estimate")))
    check("ecotype.confidence present, in [0,1]",
          isinstance(eco.get("confidence"), (int, float)) and 0.0 <= eco["confidence"] <= 1.0,
          str(eco.get("confidence")))
    check("ecotype wording is exactly the O0-approved estimate phrasing",
          eco.get("wording") in (
              "Estimated ecotype: Southern Resident (SRKW)",
              "Estimated ecotype: Bigg's / Transient (TKW)"), eco.get("wording", ""))
    chip = eco.get("provenanceChip", "")
    check("ecotype provenance chip cites Perch 2.0 + cross-station eval + variance",
          "Perch 2.0" in chip and "cross-station" in chip and "variance" in chip, chip)
    check("ecotype eval ref points at the shipped v2 evidence",
          eco.get("eval", {}).get("ref") == "infra/acoustic/eval_report_dclde_v2.json", "")
    eco_nc = eco.get("not_claimed", [])
    for tok in ("whale count", "pod / individual id", "s1-s40", "call type", "single vs multiple"):
        check(f"ecotype.not_claimed still forbids {tok!r}",
              any(tok in s.lower() for s in eco_nc), str(eco_nc))

    # Pod / individual-ID / matriline must appear ONLY inside not_claimed disclaimers.
    # Bigg's / Transient are now the APPROVED ecotype labels (not a forbidden claim).
    cj_wo_disclaimer = json.loads(json.dumps(cj))
    cj_wo_disclaimer.get("honesty", {}).pop("not_claimed", None)
    cj_wo_disclaimer.get("ecotype", {}).pop("not_claimed", None)
    blob = json.dumps(cj_wo_disclaimer).lower()
    check("no pod / individual-ID / matriline CLAIM outside the not_claimed disclaimers",
          not any(t in blob for t in ["matriline", "individual id", "pod "]), "")
    check("no S1-S40 catalog call as a served class",
          not any(f"s{n}" in cj.get("classes", []) for n in range(1, 41)), "")
    check("presence classes contain no ecotype/Bigg's presence-assertion class",
          all(c == "srkw_call_presence" for c in cj["classes"]), "")

    print("== P0: heads guard - ecotype PERMITTED; call_type + single_vs_multiple REFUSED ==")
    from heads import assert_shippable
    eco_ok = False
    try:
        h = assert_shippable("ecotype")
        eco_ok = h.eval_supported and h.hud_claimable
    except ValueError:
        eco_ok = False
    check("assert_shippable('ecotype') PERMITS (cleared the bar)", eco_ok, "")
    for h in ("call_type", "single_vs_multiple"):
        refused = False
        try:
            assert_shippable(h)
        except ValueError:
            refused = True
        check(f"assert_shippable({h!r}) still REFUSES", refused, "")

    print("== P0: v2 eval verdict is honest (no overclaim baked in) ==")
    rep = json.loads(V2.read_text())
    fo = rep["paths"]["feature_only"]
    check("feature_only verdict.passes == False (SRKW f1 guard fails under leave-station-OUT)",
          fo["verdict"]["passes"] is False,
          f"median={fo['median']}")
    pe = rep["paths"]["perch_embedding"]
    check("perch_embedding was evaluated on the SAME protocol (has verdict + per_seed)",
          "verdict" in pe and len(pe.get("per_seed", [])) >= 3, "")
    # The Perch path clears the MEDIAN pass metric (O0: median decides). That is a
    # PROPOSAL only; shipping is the separate ACX-ACCEPT gate, NOT this eval.
    check("any ship decision is flagged PROPOSED + held at ACX-ACCEPT (not auto-served)",
          "PROPOSED" in rep["overall"]["note"] and "ACX-ACCEPT" in rep["overall"]["note"],
          rep["overall"]["note"])
    check("perch median meets the FIXED metric (TKW f1>0.434, recall>=0.478, SRKW f1>=0.84)",
          pe["verdict"]["passes"] is True, f"median={pe['median']}")

    print("== P0: promotion.json cannot flip the static acoustic contract ==")
    promo = json.loads(PROMOTION.read_text())
    check("promotion.json is kernel track (kernel_version present, no acoustic/classification key)",
          "kernel_version" in promo and not any(
              k in promo for k in ("classification", "acoustic", "ecotype", "model_version")),
          f"keys={sorted(promo.keys())}")
    loaders = (ROOT / "web" / "lib" / "scene" / "reenactment" / "loaders.ts").read_text().lower()
    check("classification.json loader has NO promotion linkage",
          "promotion" not in loaders, "")

    print("== P1: confounds + spread + variance disclosed in v2 eval ==")
    conf = " ".join(rep["honesty"]["known_confounds"]).lower()
    check("recorder/encounter + few-station confound disclosed",
          "few-encounter" in conf or "few encounter" in conf or "encounter" in conf, "")
    check("prior mismatch / recalibration disclosed",
          "prior" in conf and "recalibrat" in conf, "")
    check("per-fold variance + threshold-free AUPRC evidence disclosed",
          ("variance" in conf and "auprc" in conf), "")
    check("site/habitat confound explicitly checked + reported",
          "site" in conf and ("habitat" in conf or "strait" in conf), "")
    check("per-seed spread present for TKW f1 / recall / SRKW f1 (both paths)",
          all(k in fo["spread"] for k in ("TKW_f1", "TKW_recall", "SRKW_f1"))
          and all(k in pe["spread"] for k in ("TKW_f1", "TKW_recall", "SRKW_f1")), "")
    check("threshold-free TKW AUPRC recorded for the shippable path",
          "TKW_auprc" in pe and pe["TKW_auprc"]["median"] >= 0.84,
          f"median AUPRC={pe.get('TKW_auprc', {}).get('median')}")
    check("per-fold full-pass count disclosed (median-decides honesty)",
          "per_fold_full_pass" in pe, pe.get("per_fold_full_pass", ""))
    check("recalibrated confidence recorded per seed",
          all("recalibrated_confidence" in s for s in pe["per_seed"]), "")

    print()
    n = len(results)
    print(f"== ADV SUMMARY: {n - len(fails)}/{n} checks PASS, {len(fails)} FAIL ==")
    if fails:
        print("OPEN (P0/P1):")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("ZERO open P0/P1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
