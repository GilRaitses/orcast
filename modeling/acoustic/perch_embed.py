#!/usr/bin/env python3
"""ACX-TRAIN Perch 2.0 embedding extraction (BOX step; gated, license-cleared).

Re-fetches the SAME segment-targeted audio windows behind features_v1.npz (via
ffmpeg HTTP input-seek, range request, NOT whole-file) and computes a Perch 2.0
embedding per window, aligned 1:1 to the features_v1 rows by (dataset, soundfile,
t0). The embedding matrix is the feature input for the Perch path in
train_dclde_v2.py and is evaluated on the identical leave-station-out protocol.

LICENSE GUARD (confirmed before any download, recorded in
dispatch/ACX/findings/ACX-METHODOLOGY.md and ACX-ADV_VERDICT.md):
  - Perch 2.0 weights : Apache-2.0 (Kaggle Models / HF cgeorgiaw/Perch)
  - perch-hoplite     : Apache-2.0   - perch repo : Apache-2.0
  - tensorflow / tensorflow-hub / kagglehub : Apache-2.0
All license-clear vs the CC-BY-SA-4.0 corpus. The corpus ShareAlike + attribution
travel onto the embedding cache (a derivative) and onto any classifier trained on
it. If ANY artifact resolves to NC / NC-SA / ND / unclear at download time, STOP
and return to O0.

Heavy outputs -> the gitignored box (infra/acoustic/data/corpora/, .gitignored):
  perch_embeddings_v1.npz : X (n,1536) float32 + carried row identity + license.
Weights cache -> the box (kagglehub / TF cache dir). Re-fetch pointer recorded.

Requires: a Python <=3.12 env with `tensorflow~=2.20` + `perch-hoplite` (Perch 2.0
needs TF 2.20 and, per the model card, a GPU; a CPU run is slower but valid).
This will NOT run on the repo's default Python 3.14 (no TF wheel). Run on the box.

  python perch_embed.py [--smoke N] [--workers 8]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import subprocess
import tempfile
from pathlib import Path

import numpy as np

# Reuse the EXACT audio-URL map + segment fetch used to build features_v1, so the
# Perch windows are the same windows (1:1 row alignment).
from fetch_features_dclde import audio_url, DATASET_AUDIO  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
FEATS = ROOT / "infra" / "acoustic" / "data" / "corpora" / "dclde-2027" / "features_v1.npz"
OUT = ROOT / "infra" / "acoustic" / "data" / "corpora" / "dclde-2027" / "perch_embeddings_v1.npz"

PERCH_SR = 32000          # Perch 2.0 input sample rate
PERCH_WIN_S = 5.0         # Perch 2.0 analysis window length
ATTR = "DCLDE-2027 killer whale annotations (DFO Canada / NOAA NCEI), CC-BY-SA-4.0; cite doi:10.25921/15ey-mh50"


def load_perch():
    """Load Perch 2.0 via perch-hoplite. Downloads Apache-2.0 weights to the box
    cache. Raises a clear error if the env / credentials are missing (escalate)."""
    from perch_hoplite.zoo import model_configs
    return model_configs.load_model_by_name("perch_v2")


def fetch_window(dataset: str, soundfile: str, t0: float) -> np.ndarray | None:
    """ffmpeg HTTP input-seek a PERCH_WIN_S window at PERCH_SR mono. Transient
    audio: decoded, embedded, deleted. Returns float32 mono or None."""
    url = audio_url(dataset, soundfile)
    start = max(0.0, float(t0))
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tf_:
        r = subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
             "-ss", f"{start:.3f}", "-i", url, "-t", f"{PERCH_WIN_S:.3f}",
             "-ac", "1", "-ar", str(PERCH_SR), "-y", tf_.name],
            capture_output=True, text=True,
        )
        if r.returncode != 0 or Path(tf_.name).stat().st_size < 1000:
            return None
        import scipy.io.wavfile as wavfile
        try:
            sr, x = wavfile.read(tf_.name)
        except Exception:
            return None
    if x.ndim > 1:
        x = x.mean(axis=1)
    if np.issubdtype(x.dtype, np.integer):
        x = x.astype(np.float32) / float(np.iinfo(x.dtype).max)
    else:
        x = x.astype(np.float32)
    need = int(PERCH_WIN_S * PERCH_SR)
    if len(x) < int(need * 0.8):
        return None
    if len(x) < need:
        x = np.pad(x, (0, need - len(x)))
    return x[:need]


def embed_one(model, wav: np.ndarray) -> np.ndarray:
    """Single 1536-dim embedding for one window (mean-pool any frame axis)."""
    out = model.embed(wav.astype(np.float32))
    emb = getattr(out, "embeddings", out)
    emb = np.asarray(emb, dtype=np.float32).reshape(-1, 1536)
    return emb.mean(axis=0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", type=int, default=0, help="only the first N rows (pipeline check)")
    ap.add_argument("--workers", type=int, default=8, help="parallel audio fetch workers")
    args = ap.parse_args()

    if not FEATS.exists():
        raise FileNotFoundError(f"missing {FEATS}")
    d = np.load(FEATS, allow_pickle=True)
    dataset = d["dataset"].astype(str)
    soundfile = d["soundfile"].astype(str)
    t0 = d["t0"].astype(np.float64)
    n = len(dataset) if not args.smoke else min(args.smoke, len(dataset))
    print(f">> rows to embed: {n} (of {len(dataset)})  align 1:1 to features_v1.npz")

    print(">> loading Perch 2.0 (Apache-2.0)…")
    model = load_perch()

    # Fetch audio in parallel, embed serially (model not guaranteed thread-safe).
    idx = list(range(n))

    def fetch(i):
        return i, fetch_window(dataset[i], soundfile[i], t0[i])

    wavs: dict[int, np.ndarray] = {}
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        done = 0
        for i, w in ex.map(fetch, idx):
            done += 1
            if done % 200 == 0:
                print(f"   fetched {done}/{n}")
            if w is not None:
                wavs[i] = w

    X = np.zeros((n, 1536), dtype=np.float32)
    ok = np.zeros(n, dtype=bool)
    for c, i in enumerate(idx):
        if i not in wavs:
            continue
        X[i] = embed_one(model, wavs[i])
        ok[i] = True
        if (c + 1) % 200 == 0:
            print(f"   embedded {c + 1}/{n}")

    print(f">> embedded {int(ok.sum())}/{n} windows ({n - int(ok.sum())} failed fetch/decode)")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        OUT,
        X=X,
        ok=ok,
        y_presence=d["y_presence"][:n] if not args.smoke else d["y_presence"][:n],
        y_ecotype=d["y_ecotype"][:n],
        groups=d["groups"][:n],
        dataset=dataset[:n],
        t0=t0[:n].astype(np.float32),
        soundfile=soundfile[:n],
        model_version="perch_v2 (EfficientNet-B3, 1536-dim, Apache-2.0)",
        license="CC-BY-SA-4.0 (corpus ShareAlike travels onto this embedding derivative); embedding model Apache-2.0",
        attribution=ATTR,
        perch_weights_license="Apache-2.0 (Kaggle Models perch_v2)",
    )
    print(f">> embeddings -> {OUT} (gitignored, box)")
    print(">> next: python3 train_dclde_v2.py  (will pick up the Perch path)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
