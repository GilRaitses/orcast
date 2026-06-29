#!/usr/bin/env python3
"""BAM window-level label alignment (the eval_report.json "to_strengthen"
follow-on). Turns per-annotation time intervals from an openly-licensed corpus
into TRUE window-level labels aligned to the same 3 s / 1.5 s analysis windows
the features module already produces, so a head can be trained on real
per-window ground truth instead of bout-level weak labels.

This module is pipeline scaffolding only. It defines the common annotation
record, the overlap-based labeller, the grouping keys used for an honest
cross-station / cross-day split, and parsers for the documented schemas of the
candidate corpora (DCLDE-2027 collated Annotations.csv is the OPEN anchor per
BSW-R02; Pod.Cast TSV is included but its audio+labels are CC-BY-NC-SA and stay
STOP-to-O0). No corpus is downloaded here. Parsers run only when a real,
license-cleared annotation file is present, which is an O0-gated step.

numpy + scipy + scikit-learn only. No torch, no librosa.

Self-test (synthetic intervals, writes nothing):
  python3 modeling/acoustic/windows.py --selftest
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import numpy as np

from features import WIN_S, HOP_S

# Background / no-call class label, shared across multiclass heads.
BACKGROUND = "background"

# Core Salish Sea DCLDE-2027 `Dataset` keys (verified against the fetched
# Annotations.csv). Used to scope the OPEN corpus to the SRKW domain. Excluded
# as non-Salish: DFO_CRP NorthBc / WVanIsl (open BC coast), ONC BarkleyCanyon
# (offshore Pacific), SIO Cpe_Elz / Quin_Can (WA outer coast), UAF Alaska
# fields, and DFO_WDLP CarmanahPt (Juan de Fuca entrance edge, dropped for a
# clean core-Salish domain).
SALISH_DCLDE_DATASETS = frozenset({
    "orcasound_lab", "port_townsend", "bush_point",          # OrcaSound, Puget Sound / San Juan
    "BoundaryPass", "HaroStraitNorth", "HaroStraitSouth",    # JASCO_VFPA, Haro Strait / Boundary Pass
    "StraitofGeorgia",                                       # JASCO_VFPA_ONC
    "LimeKiln",                                              # SMRU, San Juan Island
    "Tekteksen",                                             # SIMRES, Saturna Island
    "StrGeoN1", "StrGeoN2", "StrGeoS1", "StrGeoS2", "SwanChan",  # DFO_WDLP, Strait of Georgia + Swanson Channel
})


@dataclass
class Annotation:
    """One corpus annotation, normalized to a common record. Times are seconds
    from the start of `clip_id`'s audio file. Optional fields are populated only
    when the source corpus carries them; a missing field stays None so a head
    that needs it can be honestly skipped rather than fabricated."""
    t0: float
    t1: float
    clip_id: str                      # audio file / segment key the window times index into
    label: str | None = None          # corpus-native primary label (call type or ecotype)
    call_type: str | None = None      # DCLDE Call.Type category (CK / W / BP), not S1-S40
    ecotype: str | None = None        # SRKW / NRKW / TKW / OKW / SAR
    kw: bool | None = None            # killer-whale present flag (DCLDE KW)
    kw_certain: bool | None = None    # DCLDE KW_certain
    dataset: str | None = None        # provider / station key, used as a split group
    provider: str | None = None
    date: str | None = None           # YYYY-MM-DD, used as a split group (cross-day)
    source_row: int | None = None     # row index in the source file, for provenance


@dataclass
class WindowLabels:
    """Window-level labels aligned to feature windows for one clip."""
    clip_id: str
    starts_s: np.ndarray              # window start time (s), shape (n_windows,)
    labels: np.ndarray                # str labels, shape (n_windows,)
    overlap: np.ndarray               # max annotation overlap fraction per window
    n_concurrent: np.ndarray          # distinct annotations overlapping each window
    groups: np.ndarray                # split-group key per window (str)
    meta: dict = field(default_factory=dict)


def window_starts(duration_s: float, win_s: float = WIN_S, hop_s: float = HOP_S) -> np.ndarray:
    """Window start times that tile [0, duration_s], matching features.windows_from_wav."""
    if duration_s < win_s:
        return np.asarray([], dtype=np.float64)
    n = int((duration_s - win_s) // hop_s) + 1
    return np.arange(n, dtype=np.float64) * hop_s


def _overlap_s(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def label_windows(
    clip_id: str,
    starts_s: np.ndarray,
    annotations: Iterable[Annotation],
    scheme: str,
    win_s: float = WIN_S,
    min_overlap_frac: float = 0.5,
    group_by: tuple[str, ...] = ("dataset", "date"),
    group: str | None = None,
) -> WindowLabels:
    """Assign a label to every analysis window by time overlap with annotations.

    scheme:
      "presence"           -> {"present", BACKGROUND} by any sufficient overlap.
      "call_type"          -> the call_type of the max-overlap annotation, else BACKGROUND.
      "ecotype"            -> the ecotype of the max-overlap annotation, else BACKGROUND.
      "single_vs_multiple" -> {"single", "multiple", BACKGROUND} by count of
                              distinct annotations overlapping the window. NOTE:
                              BSW-R02 finds NO corpus supplies true source-count
                              labels, so concurrent-annotation count is a proxy,
                              not a verified caller count. heads.py marks this
                              head eval-unsupported; this labeller exists so the
                              claim can be measured, never asserted blind.

    A window is labelled by the annotation with the largest overlap, gated by
    min_overlap_frac of the window length. Windows below the gate are BACKGROUND.
    Group keys (dataset, date by default) drive the cross-station / cross-day
    split so train and test never share a station-day. Pass an explicit `group`
    to set the station-day from the CLIP rather than deriving it from the
    (possibly head-filtered) annotation list, which is the correct behaviour when
    a clip has windows but no annotations for the current head.
    """
    starts = np.asarray(starts_s, dtype=np.float64)
    n = len(starts)
    labels = np.full(n, BACKGROUND, dtype=object)
    overlaps = np.zeros(n, dtype=np.float64)
    n_concurrent = np.zeros(n, dtype=np.int64)
    min_overlap_s = min_overlap_frac * win_s

    anns = [a for a in annotations if a.clip_id == clip_id]
    if group is not None:
        group_val = group
    else:
        group_val = "|".join(str(_first_group(anns, k)) for k in group_by) if anns else "unknown"
    groups = np.full(n, group_val, dtype=object)

    for i, ws in enumerate(starts):
        we = ws + win_s
        best_ov = 0.0
        best_ann: Annotation | None = None
        concurrent = 0
        for a in anns:
            ov = _overlap_s(ws, we, a.t0, a.t1)
            if ov >= min_overlap_s:
                concurrent += 1
            if ov > best_ov:
                best_ov, best_ann = ov, a
        overlaps[i] = best_ov / win_s
        n_concurrent[i] = concurrent
        if best_ann is None or best_ov < min_overlap_s:
            continue
        labels[i] = _scheme_label(scheme, best_ann, concurrent)

    return WindowLabels(
        clip_id=clip_id, starts_s=starts, labels=labels.astype(str),
        overlap=overlaps, n_concurrent=n_concurrent, groups=groups.astype(str),
        meta={"scheme": scheme, "min_overlap_frac": min_overlap_frac,
              "n_annotations": len(anns), "win_s": win_s},
    )


def _scheme_label(scheme: str, a: Annotation, concurrent: int) -> str:
    if scheme == "presence":
        return "present"
    if scheme == "call_type":
        return a.call_type or a.label or BACKGROUND
    if scheme == "ecotype":
        return a.ecotype or a.label or BACKGROUND
    if scheme == "single_vs_multiple":
        return "multiple" if concurrent >= 2 else "single"
    raise ValueError(f"unknown scheme {scheme!r}")


def _first_group(anns: list[Annotation], key: str) -> str:
    for a in anns:
        v = getattr(a, key, None)
        if v:
            return str(v)
    return "unknown"


def class_balance(wl: WindowLabels) -> dict[str, int]:
    vals, counts = np.unique(wl.labels, return_counts=True)
    return {str(v): int(c) for v, c in zip(vals, counts)}


# --------------------------------------------------------------------------
# Corpus parsers. Each is written against the documented schema in BSW-R02 and
# runs ONLY against a real, license-cleared file that an O0-approved BAM-DATA
# fetch has placed under infra/acoustic/data/corpora/. None of these download.
# --------------------------------------------------------------------------

def parse_dclde_annotations(
    csv_path: str | Path,
    datasets_allow: frozenset[str] | None = None,
) -> list[Annotation]:
    """DCLDE-2027 collated Annotations.csv (CC-BY-4.0 open artifact, BSW-R02).

    Verified columns in the fetched artifact: Soundfile, Dataset, LowFreqHz,
    HighFreqHz, FileEndSec, UTC, FileBeginSec, ClassSpecies (HW / KW / UndBio /
    AB, species not call type), KW, KW_certain, Ecotype (SRKW / NRKW / TKW / OKW
    / SAR), Provider, AnnotationLevel, FilePath, FileOk. The collated CSV carries
    NO Call.Type column, so `call_type` stays None here and that head needs the
    per-provider originals. Column-name aliases are still mapped so an updated
    collation does not break the parser.

    `datasets_allow` (e.g. SALISH_DCLDE_DATASETS) restricts to those Dataset
    keys; rows outside are skipped. clip_id is the per-file audio key
    (Soundfile) that window times index into."""
    path = Path(csv_path)
    rows: list[Annotation] = []
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        cols = {c.lower(): c for c in (reader.fieldnames or [])}

        def col(*names: str) -> str | None:
            for nm in names:
                if nm.lower() in cols:
                    return cols[nm.lower()]
            return None

        c_t0 = col("filebeginsec", "start_time_s", "starttime", "begin_time_s", "start", "offset_s")
        c_t1 = col("fileendsec", "end_time_s", "endtime", "end")
        c_dur = col("duration_s", "duration")
        c_file = col("soundfile", "filename", "file", "audio_file", "begin_file")
        c_ct = col("call.type", "call_type", "calltype")
        c_sp = col("classspecies", "class_species", "species")
        c_eco = col("ecotype")
        c_kw = col("kw")
        c_kwc = col("kw_certain")
        c_ds = col("dataset")
        c_prov = col("provider")
        c_utc = col("utc", "date")

        for i, r in enumerate(reader):
            ds = _norm(r.get(c_ds)) if c_ds else None
            if datasets_allow is not None and ds not in datasets_allow:
                continue
            t0 = _to_float(r.get(c_t0)) if c_t0 else None
            if t0 is None:
                continue
            if c_t1 and _to_float(r.get(c_t1)) is not None:
                t1 = _to_float(r.get(c_t1))
            elif c_dur and _to_float(r.get(c_dur)) is not None:
                t1 = t0 + _to_float(r.get(c_dur))
            else:
                continue
            if t1 <= t0:
                continue
            rows.append(Annotation(
                t0=float(t0), t1=float(t1),
                clip_id=str(r.get(c_file, f"row{i}")) if c_file else f"row{i}",
                label=_norm(r.get(c_sp)) if c_sp else None,
                call_type=_norm(r.get(c_ct)) if c_ct else None,
                ecotype=_norm(r.get(c_eco)) if c_eco else None,
                kw=_to_bool(r.get(c_kw)) if c_kw else None,
                kw_certain=_to_bool(r.get(c_kwc)) if c_kwc else None,
                dataset=ds,
                provider=_norm(r.get(c_prov)) if c_prov else None,
                date=_date_only(r.get(c_utc)) if c_utc else None,
                source_row=i,
            ))
    return rows


def parse_podcast_tsv(tsv_path: str | Path) -> list[Annotation]:
    """Orcasound Pod.Cast round TSV (train.tsv / test.tsv). Columns per BSW-R02:
    start_time_s, duration_s, location, dataset (round). Binary SRKW call
    presence only. LICENSE: CC-BY-NC-SA 4.0 -> STOP-to-O0; this parser exists so
    that, IF O0 clears NC, the same alignment path applies. It never downloads."""
    path = Path(tsv_path)
    rows: list[Annotation] = []
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        cols = {c.lower(): c for c in (reader.fieldnames or [])}
        c_t0 = cols.get("start_time_s") or cols.get("start_time")
        c_dur = cols.get("duration_s") or cols.get("duration")
        c_loc = cols.get("location") or cols.get("wav_filename") or cols.get("location_filename")
        c_ds = cols.get("dataset")
        for i, r in enumerate(reader):
            t0 = _to_float(r.get(c_t0)) if c_t0 else None
            dur = _to_float(r.get(c_dur)) if c_dur else None
            if t0 is None or dur is None:
                continue
            rows.append(Annotation(
                t0=float(t0), t1=float(t0 + dur),
                clip_id=str(r.get(c_loc, f"row{i}")) if c_loc else f"row{i}",
                label="present", call_type="present",
                dataset=_norm(r.get(c_ds)) if c_ds else "podcast",
                provider="orcasound_podcast", source_row=i,
            ))
    return rows


def _to_float(v) -> float | None:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def _to_bool(v) -> bool | None:
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in {"1", "true", "yes", "y"}:
        return True
    if s in {"0", "false", "no", "n"}:
        return False
    return None


def _norm(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.upper() == "NA":   # DCLDE missing-value marker
        return None
    return s


def _date_only(v) -> str | None:
    s = _norm(v)
    if not s:
        return None
    return s[:10]


def _selftest() -> int:
    """Offline logic check on synthetic intervals. Writes nothing, trains
    nothing, ships nothing. Confirms the labeller and grouping behave."""
    anns = [
        Annotation(t0=2.0, t1=5.0, clip_id="clipA", call_type="CK",
                   ecotype="SRKW", dataset="orcasound_lab", date="2021-08-25"),
        Annotation(t0=4.0, t1=7.5, clip_id="clipA", call_type="W",
                   ecotype="SRKW", dataset="orcasound_lab", date="2021-08-25"),
        Annotation(t0=20.0, t1=23.0, clip_id="clipA", call_type="BP",
                   ecotype="TKW", dataset="orcasound_lab", date="2021-08-25"),
    ]
    starts = window_starts(duration_s=27.0)
    for scheme in ("presence", "call_type", "ecotype", "single_vs_multiple"):
        wl = label_windows("clipA", starts, anns, scheme)
        bal = class_balance(wl)
        assert len(wl.labels) == len(starts)
        assert BACKGROUND in bal, f"expected some background windows for {scheme}"
        non_bg = sum(c for k, c in bal.items() if k != BACKGROUND)
        assert non_bg > 0, f"expected some labelled windows for {scheme}"
        print(f"  scheme={scheme:18s} windows={len(starts):3d} "
              f"groups={set(wl.groups)} balance={bal}")
    print("windows.py self-test OK (synthetic, nothing written)")
    return 0


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    print(__doc__)
