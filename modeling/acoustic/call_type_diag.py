#!/usr/bin/env python3
"""BAM call_type DIAGNOSTIC (NOT a shipped head). The fetched per-provider
originals (VFPA Boundary Pass, SMRU Lime Kiln, SIMRES Tekteksen; CC-BY-SA-4.0)
carry call labels that are dominated by the SRKW S1-S40 catalog, which the
charter forbids claiming. The only acoustically-coarse labels are sparse
signal/whistle markers. This script measures the most honest coarse contrast the
data can support cross-station -- pulsed_call (any S-code) vs whistle -- so O0
gets a REAL number, then records it as a diagnostic + to_strengthen. It does NOT
wire call_type into classification.json (heads.assert_shippable refuses it).

free-text `comments` columns are never read (R02 PII). No torch, no new deps.

Appends a `call_type_diagnostic` block into eval_report_dclde_v1.json.

Run (after the main fetch): python3 modeling/acoustic/call_type_diag.py
"""
from __future__ import annotations

import collections
import concurrent.futures as cf
import csv
import json
import re
import urllib.parse
from pathlib import Path

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

from fetch_features_dclde import extract_feature, WIN_S
from heads import multiclass_eval
from train_dclde import minority_aware_group_split, MODELS, ATTR
import joblib

ROOT = Path(__file__).resolve().parents[2]
ORIG = ROOT / "infra" / "acoustic" / "data" / "corpora" / "dclde-2027" / "originals"
REPORT = ROOT / "infra" / "acoustic" / "eval_report_dclde_v1.json"
GCS = "https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales"
SCODE = re.compile(r"^S\d", re.I)


def coarse(label: str | None, signal: str | None = None) -> str | None:
    """Map raw labels to a coarse, honest signal class. click/buzz dropped
    (single-station, not cross-station evaluable). None = unusable label."""
    s = (signal or "").strip().lower()
    if s in ("w", "whistle"):
        return "whistle"
    if s in ("ck", "bz", "click", "buzz"):
        return None  # single-station, excluded from the cross-station contrast
    lab = (label or "").strip()
    if lab.lower() in ("whistle",):
        return "whistle"
    if SCODE.match(lab):
        return "pulsed_call"
    return None


def parse_csv_provider(path: Path, station: str, subdir: str):
    out = []
    with path.open(newline="") as fh:
        for r in csv.DictReader(fh):
            c = coarse(r.get("call_type"), r.get("signal_type"))
            if not c:
                continue
            try:
                t0 = float(r["start"]); t1 = float(r["end"])
            except (KeyError, ValueError):
                continue
            if t1 <= t0:
                continue
            url = f"{GCS}/{subdir}/{urllib.parse.quote(r['filename'])}"
            out.append((station, url, 0.5 * (t0 + t1), c))
    return out


def parse_simres():
    """Fetch + parse SIMRES Tekteksen Raven .selections.txt tables."""
    import urllib.request
    listing = urllib.request.urlopen(
        "https://storage.googleapis.com/storage/v1/b/noaa-passive-bioacoustic/o"
        "?prefix=dclde/2027/dclde_2027_killer_whales/simres/annotations/&maxResults=1000",
        timeout=30)
    import json as _j
    names = [i["name"] for i in _j.load(listing).get("items", []) if i["name"].endswith(".txt")]
    out = []
    for name in names:
        try:
            data = urllib.request.urlopen(f"https://storage.googleapis.com/noaa-passive-bioacoustic/{name}", timeout=30).read().decode("utf-8", "replace")
        except Exception:
            continue
        rdr = csv.DictReader(data.splitlines(), delimiter="\t")
        for r in rdr:
            c = coarse(r.get("Call Type"))
            if not c:
                continue
            try:
                off = float(r["File Offset (s)"])
                dur = float(r["End Time (s)"]) - float(r["Begin Time (s)"])
            except (KeyError, ValueError):
                continue
            bf = r.get("Begin File", "")
            if not bf or dur <= 0:
                continue
            url = f"{GCS}/simres/audio/eastpoint/{urllib.parse.quote(bf)}"
            out.append(("Tekteksen", url, off + dur / 2.0, c))
    return out


def main() -> int:
    anns = []
    anns += parse_csv_provider(ORIG / "vfpa" / "annot_BP_man_det.csv", "BoundaryPass", "vfpa/audio/boundarypass")
    anns += parse_csv_provider(ORIG / "smru" / "annot_LimeKiln-Encounters_man_det.csv", "LimeKiln", "smru/audio/lime-kiln")
    anns += parse_simres()

    by = collections.Counter((a[0], a[3]) for a in anns)
    print(">> coarse label inventory (station, class):")
    for k, v in sorted(by.items()):
        print(f"   {k}: {v}")

    # Keep all whistles; cap pulsed_call per station to <= 3x that station's whistle
    # count (or 250) to bound work and limit imbalance.
    rng = np.random.default_rng(0)
    whistle_per_st = collections.Counter(a[0] for a in anns if a[3] == "whistle")
    sampled = [a for a in anns if a[3] == "whistle"]
    for st in {a[0] for a in anns}:
        pc = [a for a in anns if a[0] == st and a[3] == "pulsed_call"]
        cap = min(len(pc), max(60, 3 * whistle_per_st.get(st, 0)), 250)
        if len(pc) > cap:
            pc = [pc[i] for i in rng.choice(len(pc), cap, replace=False)]
        sampled += pc
    print(f">> sampled windows: {len(sampled)}")

    def run(a):
        return a, extract_feature(a[1], a[2] - WIN_S / 2)

    X, y, groups = [], [], []
    done = 0
    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        for a, feat in ex.map(run, sampled):
            done += 1
            if done % 100 == 0:
                print(f"   extracted {done}/{len(sampled)}")
            if feat is None:
                continue
            X.append(feat); y.append(a[3]); groups.append(a[0])
    X = np.asarray(X, dtype=np.float64); y = np.asarray(y); groups = np.asarray(groups)
    print(f">> features {X.shape} class balance {dict(collections.Counter(y))} "
          f"stations {dict(collections.Counter(groups))}")

    classes = ["pulsed_call", "whistle"]
    tr, te, test_groups = minority_aware_group_split(groups, y, "whistle", test_frac=0.34, seed=0)
    scaler = StandardScaler().fit(X[tr])
    clf = RandomForestClassifier(n_estimators=400, class_weight="balanced", random_state=0, n_jobs=-1)
    clf.fit(scaler.transform(X[tr]), y[tr])
    proba_raw = clf.predict_proba(scaler.transform(X[te]))
    col = {c: i for i, c in enumerate(clf.classes_)}
    proba = np.zeros((len(te), len(classes)))
    for j, c in enumerate(classes):
        if c in col:
            proba[:, j] = proba_raw[:, col[c]]
    pred = np.array([classes[i] for i in proba.argmax(axis=1)])
    rep = multiclass_eval(y[te], pred, proba, classes,
                          split_desc="leave-station-out (BoundaryPass/LimeKiln/Tekteksen)",
                          groups_train=list(groups[tr]), groups_test=list(groups[te]))
    print(f">> call_type DIAGNOSTIC macro_f1={rep['macro_f1']} per_class={rep['per_class']}")

    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": clf, "scaler": scaler, "classes": classes, "head": "call_type_diagnostic",
                 "license": "CC-BY-SA-4.0", "attribution": ATTR},
                MODELS / "bam_call_type_diag_v1.joblib")

    block = {
        "status": "DIAGNOSTIC ONLY -- not shipped, not wired to classification.json",
        "contrast": "pulsed_call (any S-code) vs whistle; click/buzz dropped (single-station)",
        "why_not_shipped": "populated labels are the S1-S40 catalog (charter forbids claiming); coarse signal labels are sparse",
        "label_inventory": {f"{k[0]}|{k[1]}": v for k, v in sorted(by.items())},
        "stations_used": sorted(set(groups.tolist())),
        "test_stations": sorted(test_groups),
        "metrics": rep,
        "to_strengthen": "scoped relabel budget to a coarse CK/W/BP taxonomy across providers, or an O0-costed learned embedding; the 129-dim log-mel silhouette is presence-oriented",
    }
    if REPORT.exists():
        r = json.loads(REPORT.read_text())
        r.setdefault("heads", {})["call_type_diagnostic"] = block
        REPORT.write_text(json.dumps(r, indent=2))
        print(f">> merged call_type_diagnostic into {REPORT}")
    else:
        (REPORT.parent / "call_type_diag_v1.json").write_text(json.dumps(block, indent=2))
        print(">> wrote standalone call_type_diag_v1.json (run train_dclde first to merge)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
