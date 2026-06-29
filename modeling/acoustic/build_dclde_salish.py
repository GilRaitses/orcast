#!/usr/bin/env python3
"""BAM post-fetch BUILD (UNGATED, no training, no audio): turn the fetched
DCLDE-2027 collated Annotations.csv (CC-BY-4.0 OPEN) into a window-level
labelled dataset for the Salish-Sea subset, and report the leave-station-day-out
grouped-split structure.

This runs offline on the annotation CSV only. It does NOT read audio and does
NOT train. Feature extraction (features_at_starts) and model fitting are the
HUMAN-gated training step and happen later, once audio is fetched and a training
go is granted.

Heads buildable from the COLLATED CSV: `presence` (killer-whale call present,
KW==1) and `ecotype` (SRKW / NRKW / TKW / OKW / SAR on KW calls). `call_type`
needs the per-provider originals (the collated CSV has no Call.Type column) and
is not built here.

Window enumeration uses each clip's annotation span [0, max FileEndSec] as a
lower bound on file length, because true file duration needs the audio. So
non-background window counts are exact for the annotated span and background
counts are a LOWER BOUND until audio is fetched at training time.

Outputs:
  infra/acoustic/data/corpora/dclde-2027/salish_label_dataset.json  (box, gitignored)
  infra/acoustic/manifests/dclde_salish_v1.stats.json               (in-repo, small)

Run:  python3 modeling/acoustic/build_dclde_salish.py
"""
from __future__ import annotations

import collections
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from windows import (
    parse_dclde_annotations, label_windows, window_starts,
    class_balance, SALISH_DCLDE_DATASETS, BACKGROUND,
)
from train_eval import grouped_train_test_split

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "infra" / "acoustic" / "data" / "corpora" / "dclde-2027" / "Annotations.csv"
HEAVY = ROOT / "infra" / "acoustic" / "data" / "corpora" / "dclde-2027" / "salish_label_dataset.json"
STATS = ROOT / "infra" / "acoustic" / "manifests" / "dclde_salish_v1.stats.json"

CORPUS = {
    "name": "DCLDE-2027 collated Annotations.csv (killer whales)",
    "license": "CC-BY-4.0",
    "license_status": "OPEN",
    "attribution": "Palmer et al. 2025, NOAA passive bioacoustic open data; DCLDE-2027 collated annotations",
    "source_url": "https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales/Annotations.csv",
    "doi": "https://doi.org/10.25921/15ey-mh50",
    "box_pointer": "s3://198456344617-us-west-2-orcast-aws-backend-reports/bsw-acoustic/corpora/dclde-2027/",
    "scope": "Salish-Sea Dataset keys only (see windows.SALISH_DCLDE_DATASETS)",
}


def main() -> int:
    if not CSV.exists():
        raise FileNotFoundError(f"fetch the OPEN CSV first: {CSV}")

    anns = parse_dclde_annotations(CSV, datasets_allow=SALISH_DCLDE_DATASETS)
    by_clip: dict[str, list] = collections.defaultdict(list)
    for a in anns:
        by_clip[a.clip_id].append(a)

    clips_out = []
    presence_balance: collections.Counter = collections.Counter()
    ecotype_balance: collections.Counter = collections.Counter()
    presence_groups: list[str] = []
    presence_win_labels: list[str] = []
    eco_groups: list[str] = []
    eco_win_labels: list[str] = []
    dataset_counts: collections.Counter = collections.Counter()
    stationday: set[str] = set()
    n_kw_ann = 0
    n_eco_ann = 0

    for clip_id, clip_anns in by_clip.items():
        ds = next((a.dataset for a in clip_anns if a.dataset), "unknown")
        date = next((a.date for a in clip_anns if a.date), "unknown")
        group = f"{ds}|{date}"
        stationday.add(group)
        dataset_counts[ds] += 1

        kw_anns = [a for a in clip_anns if a.kw]
        eco_anns = [a for a in kw_anns if a.ecotype]
        n_kw_ann += len(kw_anns)
        n_eco_ann += len(eco_anns)

        file_span = max((a.t1 for a in clip_anns), default=0.0)
        starts = window_starts(file_span)
        if len(starts) == 0:
            continue

        wl_p = label_windows(clip_id, starts, kw_anns, "presence", group=group)
        wl_e = label_windows(clip_id, starts, eco_anns, "ecotype", group=group)

        presence_balance.update(wl_p.labels.tolist())
        ecotype_balance.update(wl_e.labels.tolist())
        presence_groups.extend(wl_p.groups.tolist())
        presence_win_labels.extend(wl_p.labels.tolist())
        eco_groups.extend(wl_e.groups.tolist())
        eco_win_labels.extend(wl_e.labels.tolist())

        clips_out.append({
            "clip_id": clip_id,
            "dataset": ds,
            "date": date,
            "group": group,
            "file_span_s_lower_bound": round(file_span, 3),
            "n_windows_over_span": int(len(starts)),
            "presence_balance": class_balance(wl_p),
            "ecotype_balance": class_balance(wl_e),
            "annotations": [
                {"t0": round(a.t0, 3), "t1": round(a.t1, 3),
                 "kw": a.kw, "kw_certain": a.kw_certain,
                 "ecotype": a.ecotype, "species": a.label}
                for a in clip_anns
            ],
        })

    # Honest cross-station / cross-day split design on the ecotype head windows.
    eco_g = np.asarray(eco_groups, dtype=object)
    tr, te, gtr, gte = grouped_train_test_split(eco_g, test_frac=0.30, seed=0)
    eco_lab = np.asarray(eco_win_labels, dtype=object)

    def balance(labels) -> dict:
        vals, counts = np.unique(np.asarray(labels, dtype=object), return_counts=True)
        return {str(v): int(c) for v, c in zip(vals, counts)}

    split_design = {
        "policy": "leave-station-day-out",
        "head_used_for_design": "ecotype",
        "n_station_days": len(set(eco_g.tolist())),
        "train_station_days": sorted(set(gtr)),
        "test_station_days": sorted(set(gte)),
        "n_train_windows": int(len(tr)),
        "n_test_windows": int(len(te)),
        "train_class_balance": balance(eco_lab[tr]) if len(tr) else {},
        "test_class_balance": balance(eco_lab[te]) if len(te) else {},
    }

    # Heavy per-clip label dataset -> box (gitignored).
    HEAVY.write_text(json.dumps({
        "schema": "bam-dclde-salish-label-dataset/v1",
        "corpus": CORPUS,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "window": {"win_s": 3.0, "hop_s": 1.5, "min_overlap_frac": 0.5},
        "note": "window labels tiled over [0, max annotation end] as a file-length "
                "PROXY; true windows (especially background) are recomputed from "
                "audio durations at training. Annotation-level counts are the "
                "reliable label signal here.",
        "clips": clips_out,
    }, indent=2))

    # Small in-repo stats summary.
    stats = {
        "schema": "bam-dclde-salish-stats/v1",
        "corpus": CORPUS,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "salish_datasets": sorted(SALISH_DCLDE_DATASETS),
        "totals": {
            "n_clips": len(clips_out),
            "n_station_days": len(stationday),
            "n_kw_annotations": n_kw_ann,
            "n_ecotype_annotations": n_eco_ann,
            "clips_per_dataset": dict(dataset_counts),
        },
        "heads_buildable_from_collated_csv": {
            "presence": {"supported": True, "basis": "KW==1 killer-whale call present"},
            "ecotype": {"supported": True, "basis": "Ecotype on KW calls (SRKW/NRKW/TKW/OKW/SAR)"},
            "call_type": {"supported": False, "reason": "collated CSV has no Call.Type column; needs per-provider originals (further gated fetch)"},
            "single_vs_multiple": {"supported": False, "reason": "no source-count labels (BSW-R02); dropped for v1 per O0"},
        },
        "window_class_balance": {
            "presence": dict(presence_balance),
            "ecotype": dict(ecotype_balance),
        },
        "ecotype_annotation_balance": _eco_ann_balance(anns),
        "grouped_split_design": split_design,
        "background_caveat": "window counts tile [0, max annotation end] as a "
            "file-length proxy (clip span median ~112s, p90 ~1225s). Background "
            "counts are provisional and are recomputed from true audio durations "
            "at training; ~500 Salish clips whose only detection is under 3s get "
            "no window under the proxy but would at training with real durations. "
            "Annotation-level counts (KW and ecotype) are the authoritative label "
            "signal at this stage.",
    }
    STATS.write_text(json.dumps(stats, indent=2))

    print(f">> Salish clips: {len(clips_out)}  station-days: {len(stationday)}")
    print(f">> KW annotations: {n_kw_ann}  ecotype-labelled: {n_eco_ann}")
    print(f">> presence window balance: {dict(presence_balance)}")
    print(f">> ecotype window balance:  {dict(ecotype_balance)}")
    print(f">> split design: {split_design['n_station_days']} station-days "
          f"-> {len(split_design['test_station_days'])} held out for test")
    print(f">>   train windows={split_design['n_train_windows']} "
          f"test windows={split_design['n_test_windows']}")
    print(f">>   test class balance: {split_design['test_class_balance']}")
    print(f">> heavy dataset -> {HEAVY} (gitignored)")
    print(f">> stats -> {STATS} (in-repo)")
    return 0


def _eco_ann_balance(anns) -> dict:
    c = collections.Counter(a.ecotype for a in anns if a.kw and a.ecotype)
    return {str(k): int(v) for k, v in c.items()}


if __name__ == "__main__":
    raise SystemExit(main())
