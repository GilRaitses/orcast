#!/usr/bin/env python3
"""BAM feature extraction: a real "acoustic-silhouette" feature vector per
analysis window, computed from REAL decoded hydrophone PCM with numpy + scipy
only (no librosa / no torch). Shared definition used by training and inference
so the demo-clip inference uses the exact same features as the held-out eval.

Window: 3.0 s, hop 1.5 s. Per window we compute a log-mel power spectrogram
(40 mel bands, 0-20 kHz, fftSize 2048, hop 512, Hann) and summarize it into a
fixed vector: per-band {mean, std, p90} over time plus a handful of global
spectral-shape statistics. This is the statistical silhouette of the sound;
it is NOT a per-call detector and carries no whale-count claim.
"""
from __future__ import annotations

import numpy as np
from scipy import signal
import scipy.io.wavfile as wavfile

SR = 48000
FFT = 2048
HOP = 512
N_MELS = 40
FMIN = 50.0
FMAX = 20000.0
WIN_S = 3.0
HOP_S = 1.5


def _hz_to_mel(f: np.ndarray | float) -> np.ndarray | float:
    return 2595.0 * np.log10(1.0 + np.asarray(f) / 700.0)


def _mel_to_hz(m: np.ndarray) -> np.ndarray:
    return 700.0 * (10.0 ** (m / 2595.0) - 1.0)


def mel_filterbank(sr: int = SR, fft: int = FFT, n_mels: int = N_MELS,
                   fmin: float = FMIN, fmax: float = FMAX) -> np.ndarray:
    """Triangular mel filterbank, shape (n_mels, fft//2 + 1)."""
    n_freqs = fft // 2 + 1
    fft_freqs = np.linspace(0, sr / 2, n_freqs)
    mel_pts = np.linspace(_hz_to_mel(fmin), _hz_to_mel(fmax), n_mels + 2)
    hz_pts = _mel_to_hz(mel_pts)
    bins = np.searchsorted(fft_freqs, hz_pts)
    fb = np.zeros((n_mels, n_freqs), dtype=np.float64)
    for m in range(1, n_mels + 1):
        lo, ctr, hi = hz_pts[m - 1], hz_pts[m], hz_pts[m + 1]
        for k in range(n_freqs):
            f = fft_freqs[k]
            if lo <= f <= ctr and ctr > lo:
                fb[m - 1, k] = (f - lo) / (ctr - lo)
            elif ctr < f <= hi and hi > ctr:
                fb[m - 1, k] = (hi - f) / (hi - ctr)
    return fb


_FB = mel_filterbank()


def read_wav_mono(path: str) -> tuple[int, np.ndarray]:
    sr, x = wavfile.read(path)
    if x.ndim > 1:
        x = x.mean(axis=1)
    if np.issubdtype(x.dtype, np.integer):
        x = x.astype(np.float64) / float(np.iinfo(x.dtype).max)
    else:
        x = x.astype(np.float64)
    return sr, x


def log_mel(x: np.ndarray, sr: int = SR) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (log_mel [n_mels, T], magnitude [freq, T], freqs)."""
    f, _, Z = signal.stft(x, fs=sr, window="hann", nperseg=FFT,
                          noverlap=FFT - HOP, boundary=None, padded=False)
    mag = np.abs(Z)
    power = mag ** 2
    mel = _FB @ power
    logm = np.log(mel + 1e-10)
    return logm, mag, f


def _global_feats(mag: np.ndarray, freqs: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Spectral-shape + energy statistics over the window's frames."""
    eps = 1e-10
    p = mag ** 2 + eps
    psum = p.sum(axis=0)
    centroid = (freqs[:, None] * p).sum(axis=0) / psum
    bandwidth = np.sqrt((((freqs[:, None] - centroid[None, :]) ** 2) * p).sum(axis=0) / psum)
    gmean = np.exp(np.log(p).mean(axis=0))
    flatness = gmean / (p.mean(axis=0) + eps)
    flux = np.sqrt(((np.diff(mag, axis=1)) ** 2).sum(axis=0))
    rms = np.sqrt((x ** 2).mean())
    hi = freqs >= 4000.0
    lo = ~hi
    hi_lo = p[hi, :].sum() / (p[lo, :].sum() + eps)
    zcr = np.mean(np.abs(np.diff(np.sign(x)))) / 2.0
    return np.array([
        centroid.mean(), centroid.std(),
        bandwidth.mean(),
        flatness.mean(),
        flux.mean() if flux.size else 0.0,
        rms, x.std(),
        np.log(hi_lo + eps),
        zcr,
    ], dtype=np.float64)


def window_feature(x: np.ndarray, sr: int = SR) -> np.ndarray:
    logm, mag, freqs = log_mel(x, sr)
    per_band = np.concatenate([
        logm.mean(axis=1),
        logm.std(axis=1),
        np.percentile(logm, 90, axis=1),
    ])
    return np.concatenate([per_band, _global_feats(mag, freqs, x)])


N_FEATURES = 3 * N_MELS + 9


def feature_names() -> list[str]:
    names: list[str] = []
    for stat in ("mean", "std", "p90"):
        names += [f"logmel{b:02d}_{stat}" for b in range(N_MELS)]
    names += ["centroid_mean", "centroid_std", "bandwidth_mean", "flatness_mean",
              "flux_mean", "rms", "amp_std", "hi_lo_log", "zcr"]
    return names


def windows_from_wav(path: str, win_s: float = WIN_S, hop_s: float = HOP_S
                     ) -> tuple[np.ndarray, np.ndarray]:
    """Return (features [n_windows, N_FEATURES], window_start_times_s)."""
    sr, x = read_wav_mono(path)
    win = int(round(win_s * sr))
    hop = int(round(hop_s * sr))
    feats: list[np.ndarray] = []
    starts: list[float] = []
    for s in range(0, max(1, len(x) - win + 1), hop):
        seg = x[s:s + win]
        if len(seg) < win:
            break
        feats.append(window_feature(seg, sr))
        starts.append(s / sr)
    return np.asarray(feats, dtype=np.float64), np.asarray(starts, dtype=np.float64)


def feature_for_segment(x: np.ndarray, sr: int, t0: float, t1: float) -> np.ndarray | None:
    """Feature vector for one arbitrary time slice [t0, t1] of a loaded signal.
    Returns None if the slice is empty. Used by the window-level pipeline to
    featurize a window whose bounds come from windows.py (corpus-aligned), so
    training features and label windows share the exact same definition."""
    a, b = int(round(t0 * sr)), int(round(t1 * sr))
    seg = x[max(0, a):max(0, b)]
    if seg.size == 0:
        return None
    return window_feature(seg, sr)


def features_at_starts(path: str, starts_s, win_s: float = WIN_S
                       ) -> tuple[np.ndarray, np.ndarray]:
    """Compute features at a GIVEN set of window start times (seconds), instead
    of re-tiling internally. This is the compute-once contract with the
    window-level labeller (windows.py): pass it the same `starts` that produced
    the labels and the feature rows line up one-to-one with the label rows.

    Returns (features [n_kept, N_FEATURES], kept_starts_s). Windows that run past
    the end of the audio are dropped, and the matching label rows must be dropped
    with `kept_starts_s`."""
    sr, x = read_wav_mono(path)
    win = int(round(win_s * sr))
    feats: list[np.ndarray] = []
    kept: list[float] = []
    for ts in np.asarray(starts_s, dtype=np.float64):
        a = int(round(ts * sr))
        seg = x[a:a + win]
        if len(seg) < win:
            continue
        feats.append(window_feature(seg, sr))
        kept.append(float(ts))
    return np.asarray(feats, dtype=np.float64), np.asarray(kept, dtype=np.float64)


if __name__ == "__main__":
    import sys
    f, t = windows_from_wav(sys.argv[1])
    print("windows", f.shape, "n_features", N_FEATURES, "t0..tN", t[0], t[-1])
