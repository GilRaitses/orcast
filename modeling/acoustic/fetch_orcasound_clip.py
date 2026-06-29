#!/usr/bin/env python3
"""BAM data fetch: pull REAL Orcasound Lab HLS audio for the 2021-08-25 S10
L-pod SRKW bout (session 1629941419) and decode to 48 kHz mono WAV.

License of the fetched audio: CC BY-NC-SA 4.0 (Orcasound). NonCommercial use
authorized by owner sign-off (SIGN_OFF.md decision 1). Attribution string:
"Orcasound - orcasound.net". Heavy WAV/TS stay gitignored under data/.

Labels are BOUT-LEVEL weak labels, not per-window ground truth:
  positive pool = segments well inside the human + OrcaHello confirmed SRKW
    vocalization bout 210825_1922-2007_OS_SRKW_L.
  negative pool = segments well before the bout (no detections), with a margin
    that absorbs the ~10 min HLS/clock drift the Orcasound blog warns about.
The eval is grouped by time so train/test never share adjacent windows.

Run:  python3 modeling/acoustic/fetch_orcasound_clip.py
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import subprocess
import sys
from pathlib import Path

BUCKET = "audio-orcasound-net"
NODE = "rpi_orcasound_lab"
SESSION = "1629941419"  # 2021-08-25 18:30:19 PDT session folder
PREFIX = f"s3://{BUCKET}/{NODE}/hls/{SESSION}"

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "infra" / "acoustic" / "data" / "raw_ts"
WAV = ROOT / "infra" / "acoustic" / "data" / "wav"

# Segment ranges (10 s each from session start ~18:30:19 PDT). Centered to be
# robust to ~10 min drift: positives deep inside the 45-min bout, negatives
# well before the first detection (19:25:07 PDT).
POS_RANGE = range(360, 520)   # ~19:30-19:57 PDT, inside the SRKW bout
NEG_RANGE = range(0, 150)     # ~18:30-18:55 PDT, before any detection


def s3_key(n: int) -> str:
    return f"{PREFIX}/live{n:03d}.ts"


def fetch_one(n: int) -> tuple[int, bool]:
    dst = RAW / f"live{n:03d}.ts"
    if dst.exists() and dst.stat().st_size > 0:
        return n, True
    r = subprocess.run(
        ["aws", "s3", "cp", "--no-sign-request", s3_key(n), str(dst),
         "--only-show-errors"],
        capture_output=True, text=True,
    )
    return n, r.returncode == 0 and dst.exists()


def fetch_range(rng: range) -> list[int]:
    got: list[int] = []
    with cf.ThreadPoolExecutor(max_workers=16) as ex:
        for n, ok in ex.map(fetch_one, rng):
            if ok:
                got.append(n)
    return sorted(got)


def concat_to_wav(seg_ids: list[int], out_wav: Path) -> bool:
    if not seg_ids:
        return False
    listing = RAW / f"{out_wav.stem}_concat.txt"
    with listing.open("w") as f:
        for n in seg_ids:
            f.write(f"file '{(RAW / f'live{n:03d}.ts').as_posix()}'\n")
    # AAC-in-MPEG-TS -> 48 kHz mono PCM WAV (the in-repo OS1 decode target).
    r = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", str(listing),
         "-ac", "1", "-ar", "48000", "-vn", str(out_wav)],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        print("ffmpeg error:", r.stderr[-800:], file=sys.stderr)
        return False
    return out_wav.exists()


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    WAV.mkdir(parents=True, exist_ok=True)
    print(f">> fetching positives {POS_RANGE.start}-{POS_RANGE.stop - 1}")
    pos = fetch_range(POS_RANGE)
    print(f"   got {len(pos)} positive segments")
    print(f">> fetching negatives {NEG_RANGE.start}-{NEG_RANGE.stop - 1}")
    neg = fetch_range(NEG_RANGE)
    print(f"   got {len(neg)} negative segments")

    print(">> decoding positive pool -> wav")
    ok_pos = concat_to_wav(pos, WAV / "srkw_bout_pos.wav")
    print(">> decoding negative pool -> wav")
    ok_neg = concat_to_wav(neg, WAV / "ambient_neg.wav")

    # Also decode the tight demo window (segs ~339-356, 19:26:56-19:29:41 PDT)
    # for the precomputed inference JSON. Pull any missing segments first.
    demo_ids = list(range(339, 357))
    fetch_range(range(339, 357))
    demo_have = [n for n in demo_ids if (RAW / f"live{n:03d}.ts").exists()]
    ok_demo = concat_to_wav(demo_have, WAV / "demo_window.wav")

    manifest = {
        "session": SESSION,
        "node": NODE,
        "bucket": BUCKET,
        "license": "CC BY-NC-SA 4.0",
        "attribution": "Orcasound - orcasound.net",
        "bout_label": "210825_1922-2007_OS_SRKW_L",
        "pos_segments": pos,
        "neg_segments": neg,
        "demo_segments": demo_have,
        "pos_wav": "srkw_bout_pos.wav" if ok_pos else None,
        "neg_wav": "ambient_neg.wav" if ok_neg else None,
        "demo_wav": "demo_window.wav" if ok_demo else None,
        "label_basis": "bout-level weak labels; positives inside confirmed SRKW bout, negatives pre-bout ambient",
    }
    (WAV / "fetch_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(">> done:", json.dumps({k: (len(v) if isinstance(v, list) else v)
                                  for k, v in manifest.items()}, indent=2))
    return 0 if (ok_pos and ok_neg) else 1


if __name__ == "__main__":
    raise SystemExit(main())
