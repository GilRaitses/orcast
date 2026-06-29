#!/usr/bin/env python3
"""BAM segment-targeted audio fetch + feature extraction for the DCLDE-2027
Salish subset (CC-BY-SA-4.0; ShareAlike + attribution carried on every
derivative). For each sampled annotation we pull ONLY a 3 s window around it via
ffmpeg HTTP input-seek (range request, not the whole file), decode to 48 kHz
mono, and compute the existing 129-dim scipy log-mel silhouette feature. Plus a
matched set of background windows sampled from non-annotated regions.

NOT a whole-file fetch. Audio bytes are transient (decoded per window, hashed
into the feature, the temp wav deleted). Only the feature matrix is cached, to
the gitignored box. No torch. No new deps.

Outputs (box, gitignored):
  infra/acoustic/data/corpora/dclde-2027/features_v1.npz
    X (n,129) float32, y_presence, y_ecotype, groups (station-day), dataset, t0, soundfile

Run:  python3 modeling/acoustic/fetch_features_dclde.py [--smoke] [--srkw-cap-per-day N]
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures as cf
import csv
import subprocess
import tempfile
import urllib.parse
from pathlib import Path

import numpy as np

from features import window_feature, read_wav_mono, WIN_S, N_FEATURES
from windows import SALISH_DCLDE_DATASETS

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "infra" / "acoustic" / "data" / "corpora" / "dclde-2027" / "Annotations.csv"
OUT = ROOT / "infra" / "acoustic" / "data" / "corpora" / "dclde-2027" / "features_v1.npz"
GCS = "https://storage.googleapis.com/noaa-passive-bioacoustic/dclde/2027/dclde_2027_killer_whales"

# Salish datasets that actually have audio in the bucket. StrGeoN2 (AMAR617) and
# StrGeoS2 (AMAR779) are annotation-only (audio 404) and are dropped.
DATASET_AUDIO = {
    "orcasound_lab": ("orcasound", "orcasound_lab"),
    "bush_point": ("orcasound", "bush_point"),
    "port_townsend": ("orcasound", "port_townsend"),
    "BoundaryPass": ("vfpa", "boundarypass"),
    "HaroStraitNorth": ("vfpa", "vfpa-harostrait-nb"),
    "HaroStraitSouth": ("vfpa", "vfpa-harostrait-sb"),
    "StraitofGeorgia": ("vfpa", "straitofgeorgia_globus-robertsbank"),
    "LimeKiln": ("smru", "lime-kiln"),
    "Tekteksen": ("simres", "eastpoint"),
    "StrGeoN1": ("dfo_wdlp", "strgeon1"),
    "StrGeoS1": ("dfo_wdlp", "strgeos1"),
    "SwanChan": ("dfo_wdlp", "swanchan"),
}
SR = 48000


def audio_url(dataset: str, soundfile: str) -> str:
    prov, sub = DATASET_AUDIO[dataset]
    return f"{GCS}/{prov}/audio/{sub}/{urllib.parse.quote(soundfile)}"


def extract_feature(url: str, start_s: float) -> np.ndarray | None:
    """ffmpeg HTTP input-seek a WIN_S window, decode mono 48k, featurize."""
    start_s = max(0.0, start_s)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tf:
        r = subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
             "-ss", f"{start_s:.3f}", "-i", url, "-t", f"{WIN_S:.3f}",
             "-ac", "1", "-ar", str(SR), "-y", tf.name],
            capture_output=True, text=True,
        )
        if r.returncode != 0 or Path(tf.name).stat().st_size < 1000:
            return None
        try:
            sr, x = read_wav_mono(tf.name)
        except Exception:
            return None
    need = int(WIN_S * SR)
    if len(x) < int(need * 0.8):
        return None
    return window_feature(x[:need], SR).astype(np.float32)


def file_duration_s(url: str) -> float | None:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", url],
        capture_output=True, text=True,
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def load_salish_annotations():
    """Collated KW annotations on audio-available Salish datasets, plus all
    annotation spans per soundfile (to avoid them when sampling background)."""
    kw = []                      # (dataset, soundfile, t0, t1, ecotype)
    spans = collections.defaultdict(list)   # soundfile -> [(t0,t1)]
    meta = {}                    # soundfile -> (dataset, date)
    with CSV.open(newline="") as fh:
        for row in csv.DictReader(fh):
            ds = row["Dataset"]
            if ds not in DATASET_AUDIO:
                continue
            sf = row["Soundfile"]
            try:
                t0 = float(row["FileBeginSec"]); t1 = float(row["FileEndSec"])
            except ValueError:
                continue
            if t1 <= t0:
                continue
            spans[sf].append((t0, t1))
            date = (row["UTC"][:10] if len(row["UTC"]) >= 10 else "unknown")
            meta[sf] = (ds, date)
            if row["KW"] == "1":
                eco = row["Ecotype"]
                kw.append((ds, sf, t0, t1, eco if eco not in ("NA", "") else None))
    return kw, spans, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="tiny run to validate the pipeline")
    ap.add_argument("--srkw-cap-per-day", type=int, default=40,
                    help="max SRKW positives per station-day (keep all TKW)")
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()

    kw, spans, meta = load_salish_annotations()
    rng = np.random.default_rng(0)

    # Stratified positive sampling for the ecotype head: keep ALL TKW (minority),
    # cap SRKW per station-day. KW windows WITHOUT a known ecotype are excluded
    # from this set so they cannot pollute the ecotype classes (they would still
    # be valid presence positives, but the ecotype-known calls already give
    # thousands of multi-station positives for the presence head too).
    by_day_srkw = collections.defaultdict(list)
    positives = []   # (dataset, soundfile, center, ecotype, group)
    for ds, sf, t0, t1, eco in kw:
        if eco not in ("SRKW", "TKW"):
            continue
        date = meta[sf][1]
        group = f"{ds}|{date}"
        center = 0.5 * (t0 + t1)
        if eco == "SRKW":
            by_day_srkw[group].append((ds, sf, center, eco, group))
        else:
            positives.append((ds, sf, center, eco, group))  # all TKW
    for group, lst in by_day_srkw.items():
        if len(lst) > args.srkw_cap_per_day:
            idx = rng.choice(len(lst), args.srkw_cap_per_day, replace=False)
            lst = [lst[i] for i in idx]
        positives.extend(lst)

    # Background: per soundfile, sample up to k windows avoiding annotated spans.
    pos_files = sorted({(p[0], p[1]) for p in positives})
    if args.smoke:
        positives = positives[:24]
        pos_files = pos_files[:6]

    print(f">> positive windows planned: {len(positives)}")
    print(f">> files needing duration (for background): {len(pos_files)}")

    # Durations (one ffprobe per file, parallel).
    durs = {}
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(file_duration_s, audio_url(ds, sf)): (ds, sf) for ds, sf in pos_files}
        for fut in cf.as_completed(futs):
            ds, sf = futs[fut]
            durs[(ds, sf)] = fut.result()

    backgrounds = []   # (dataset, soundfile, start, group)
    k_bg = 1 if args.smoke else 3
    for ds, sf in pos_files:
        dur = durs.get((ds, sf))
        if not dur or dur < WIN_S + 1:
            continue
        group = f"{ds}|{meta[sf][1]}"
        ann = spans.get(sf, [])
        tries = 0
        got = 0
        while got < k_bg and tries < 40:
            tries += 1
            st = float(rng.uniform(0, dur - WIN_S))
            if any(not (st + WIN_S < a0 or st > a1) for a0, a1 in ann):
                continue
            backgrounds.append((ds, sf, st, group))
            got += 1
    print(f">> background windows planned: {len(backgrounds)}")

    # Extract features in parallel.
    tasks = ([("pos", p[0], p[1], p[2] - WIN_S / 2, p[3], p[4]) for p in positives]
             + [("bg", b[0], b[1], b[2], None, b[3]) for b in backgrounds])

    def run(task):
        kind, ds, sf, start, eco, group = task
        feat = extract_feature(audio_url(ds, sf), start)
        return (task, feat)

    X, yp, ye, groups, dsl, t0l, sfl = [], [], [], [], [], [], []
    done = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for task, feat in ex.map(run, tasks):
            done += 1
            if done % 200 == 0:
                print(f"   extracted {done}/{len(tasks)}")
            if feat is None:
                continue
            kind, ds, sf, start, eco, group = task
            X.append(feat)
            yp.append("present" if kind == "pos" else "background")
            ye.append(eco if (kind == "pos" and eco) else "background")
            groups.append(group); dsl.append(ds); t0l.append(start); sfl.append(sf)

    X = np.asarray(X, dtype=np.float32)
    print(f">> features extracted: {X.shape} (expected dim {N_FEATURES})")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        OUT, X=X, y_presence=np.asarray(yp), y_ecotype=np.asarray(ye),
        groups=np.asarray(groups), dataset=np.asarray(dsl),
        t0=np.asarray(t0l, dtype=np.float32), soundfile=np.asarray(sfl),
        license="CC-BY-SA-4.0", attribution="DCLDE-2027 (DFO Canada / NOAA NCEI); cite doi:10.25921/15ey-mh50",
    )
    pp = collections.Counter(yp); ee = collections.Counter(ye)
    print(f">> presence balance: {dict(pp)}")
    print(f">> ecotype balance:  {dict(ee)}")
    print(f">> station-days: {len(set(groups))}")
    print(f">> cached -> {OUT} (gitignored, BY-SA)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
