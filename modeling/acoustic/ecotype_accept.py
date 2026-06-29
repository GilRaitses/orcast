#!/usr/bin/env python3
"""ACX-ACCEPT: train the shippable binary SRKW-vs-Bigg's(TKW) ecotype head on the
cached Perch 2.0 embeddings (the path O0 promoted), persist the small in-repo
inference artifact, and run it on the SERVED Orcasound clip to produce the real
prior-recalibrated ecotype estimate + confidence that gets wired into
web/public/hydrophone/slice/classification.json.

Honesty: this is a cross-station estimate (the clip's Orcasound Lab recorder is
NOT in the DCLDE training stations) — exactly the generalization the v2 eval
measured (median TKW F1 0.80 / AUPRC 0.96, per-station variance). The confidence
is recalibrated toward the ~5% deployment TKW prior. No count / pod / individual
/ S1-S40 / call-type claim is produced.

Runs in the perch-venv (TF 2.20 + perch-hoplite). Writes:
  infra/acoustic/ecotype_head_v2.json   (small shippable head: scaler + logreg + priors)
and prints the served clip estimate for wiring.
"""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from perch_embed import embed_one, load_perch, PERCH_SR, PERCH_WIN_S

ROOT = Path(__file__).resolve().parents[2]
PERCH = ROOT / "infra" / "acoustic" / "data" / "corpora" / "dclde-2027" / "perch_embeddings_v1.npz"
HEAD_OUT = ROOT / "infra" / "acoustic" / "ecotype_head_v2.json"
CLASSIFICATION = ROOT / "web" / "public" / "hydrophone" / "slice" / "classification.json"
CLIP = ROOT / "web" / "public" / "hydrophone" / "slice" / "orcasound_lab_20210825_srkw.m4a"
PI_DEPLOY = 0.05


def recalibrate(p, pi_train, pi_deploy=PI_DEPLOY):
    p = np.clip(np.asarray(p, dtype=np.float64), 1e-6, 1 - 1e-6)
    num = p * (pi_deploy / pi_train)
    den = num + (1 - p) * ((1 - pi_deploy) / (1 - pi_train))
    return num / den


def train_head():
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    e = np.load(PERCH, allow_pickle=True)
    ok = e["ok"].astype(bool)
    ye = e["y_ecotype"].astype(str)
    pool = ok & np.isin(ye, ["SRKW", "TKW"])
    X = e["X"].astype(np.float64)[pool]
    y = ye[pool]
    scaler = StandardScaler().fit(X)
    clf = LogisticRegression(max_iter=5000, class_weight="balanced").fit(scaler.transform(X), y)
    pi_train = float((y == "TKW").mean())
    artifact = {
        "model_version": "bam-dclde-salish-v2-ecotype",
        "task": "binary SRKW vs Bigg's/Transient (TKW) on call windows",
        "feature": "Perch 2.0 embedding (EfficientNet-B3, 1536-dim, Apache-2.0)",
        "classes": list(clf.classes_),
        "tkw_index": int(list(clf.classes_).index("TKW")),
        "scaler_mean": [round(float(v), 6) for v in scaler.mean_],
        "scaler_scale": [round(float(v), 6) for v in scaler.scale_],
        "logreg_coef": [round(float(v), 6) for v in clf.coef_[0]],
        "logreg_intercept": round(float(clf.intercept_[0]), 6),
        "pi_train_tkw": round(pi_train, 4),
        "pi_deploy_tkw": PI_DEPLOY,
        "n_train": int(pool.sum()),
        "license": "head trained on CC-BY-SA-4.0 corpus embeddings; embedding model Apache-2.0",
        "eval_ref": "infra/acoustic/eval_report_dclde_v2.json (perch_embedding: median TKW f1 0.805, recall 0.788, SRKW f1 0.902, AUPRC 0.956)",
    }
    HEAD_OUT.write_text(json.dumps(artifact, indent=2))
    print(f">> trained shippable ecotype head -> {HEAD_OUT} (n_train={artifact['n_train']}, pi_train_tkw={artifact['pi_train_tkw']})")
    return scaler, clf, pi_train


def decode_window(t0: float) -> np.ndarray | None:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tf_:
        r = subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
             "-ss", f"{max(0.0, t0):.3f}", "-i", str(CLIP), "-t", f"{PERCH_WIN_S:.3f}",
             "-ac", "1", "-ar", str(PERCH_SR), "-y", tf_.name],
            capture_output=True, text=True)
        if r.returncode != 0 or Path(tf_.name).stat().st_size < 1000:
            return None
        import scipy.io.wavfile as wavfile
        sr, x = wavfile.read(tf_.name)
    if x.ndim > 1:
        x = x.mean(axis=1)
    x = (x.astype(np.float32) / np.iinfo(x.dtype).max) if np.issubdtype(x.dtype, np.integer) else x.astype(np.float32)
    need = int(PERCH_WIN_S * PERCH_SR)
    if len(x) < int(need * 0.8):
        return None
    return np.pad(x, (0, max(0, need - len(x))))[:need]


def main() -> int:
    scaler, clf, pi_train = train_head()
    cj = json.loads(CLASSIFICATION.read_text())
    present = [w for w in cj["windows"] if w["presence"]]
    print(f">> served clip: {CLIP.name}; {len(present)} present windows to ecotype-classify")

    model = load_perch()
    tkw_idx = list(clf.classes_).index("TKW")
    p_tkw_raw = []
    for w in present:
        wav = decode_window(float(w["tStartS"]))
        if wav is None:
            continue
        emb = embed_one(model, wav).reshape(1, -1)
        p = clf.predict_proba(scaler.transform(emb))[0, tkw_idx]
        p_tkw_raw.append(float(p))
    p_tkw_raw = np.array(p_tkw_raw)
    p_tkw_recal = recalibrate(p_tkw_raw, pi_train)
    p_srkw_recal = 1.0 - p_tkw_recal

    mean_srkw = float(p_srkw_recal.mean())
    mean_tkw = float(p_tkw_recal.mean())
    dominant = "SRKW" if mean_srkw >= mean_tkw else "TKW"
    clip_conf = max(mean_srkw, mean_tkw)
    frac_srkw_windows = float((p_srkw_recal >= 0.5).mean())

    print(f">> windows classified: {len(p_tkw_raw)}")
    print(f">> mean raw P(TKW)={p_tkw_raw.mean():.4f}  mean recal P(TKW)={mean_tkw:.4f}  mean recal P(SRKW)={mean_srkw:.4f}")
    print(f">> per-window SRKW-majority fraction={frac_srkw_windows:.4f}")
    print(f">> CLIP ECOTYPE ESTIMATE: {dominant}  confidence={clip_conf:.4f} (prior-recalibrated toward {PI_DEPLOY})")
    print(json.dumps({
        "dominant": dominant, "confidence": round(clip_conf, 4),
        "mean_recal_p_srkw": round(mean_srkw, 4), "mean_recal_p_tkw": round(mean_tkw, 4),
        "mean_raw_p_tkw": round(float(p_tkw_raw.mean()), 4),
        "n_windows": int(len(p_tkw_raw)),
        "srkw_majority_window_fraction": round(frac_srkw_windows, 4),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
