#!/usr/bin/env python3
"""SSIM + mean per-pixel delta between two captured frames, full-frame and over
an optional bounding box. numpy + PIL only (no skimage). Used by ENV-ACCEPT to
measure parity and the run-to-run determinism noise floor."""
import sys
import numpy as np
from PIL import Image


def load_gray(p):
    return np.asarray(Image.open(p).convert("L"), dtype=np.float64)


def load_rgb(p):
    return np.asarray(Image.open(p).convert("RGB"), dtype=np.float64)


def ssim_global(a, b):
    # Global (single-window) SSIM on grayscale, the standard constants.
    mu_a, mu_b = a.mean(), b.mean()
    va, vb = a.var(), b.var()
    cov = ((a - mu_a) * (b - mu_b)).mean()
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    return ((2 * mu_a * mu_b + c1) * (2 * cov + c2)) / (
        (mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2))


def ssim_windowed(a, b, win=8):
    # Mean of per-window global SSIM over non-overlapping winxwin tiles.
    h, w = a.shape
    vals = []
    for y in range(0, h - win + 1, win):
        for x in range(0, w - win + 1, win):
            vals.append(ssim_global(a[y:y+win, x:x+win], b[y:y+win, x:x+win]))
    return float(np.mean(vals))


def main():
    pa, pb = sys.argv[1], sys.argv[2]
    bbox = None
    if len(sys.argv) >= 7:
        bbox = tuple(int(v) for v in sys.argv[3:7])  # x0 y0 x1 y1
    ga, gb = load_gray(pa), load_gray(pb)
    ra, rb = load_rgb(pa), load_rgb(pb)
    if ga.shape != gb.shape:
        print(f"SHAPE MISMATCH {ga.shape} vs {gb.shape}")
        return 1
    print(f"A: {pa}")
    print(f"B: {pb}")
    print(f"shape: {ga.shape}")
    print(f"FULL  ssim_global={ssim_global(ga, gb):.5f} "
          f"ssim_win8={ssim_windowed(ga, gb):.5f} "
          f"mean_abs_delta(0-255)={np.abs(ra - rb).mean():.4f} "
          f"max_abs_delta={np.abs(ra - rb).max():.0f}")
    if bbox:
        x0, y0, x1, y1 = bbox
        ca, cb = ga[y0:y1, x0:x1], gb[y0:y1, x0:x1]
        cra, crb = ra[y0:y1, x0:x1], rb[y0:y1, x0:x1]
        print(f"BBOX {bbox} ssim_global={ssim_global(ca, cb):.5f} "
              f"ssim_win8={ssim_windowed(ca, cb):.5f} "
              f"mean_abs_delta={np.abs(cra - crb).mean():.4f} "
              f"max_abs_delta={np.abs(cra - crb).max():.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
