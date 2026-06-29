"""Level 2 consistency gate: joint kernel vs marginal PSTH.

Ported from INDYsim ``generate_psth_vs_kernel_verification.py``. The joint LNP
fit must agree with the simple marginal (PSTH) estimate of the same covariate;
disagreement means the joint model is imposing structure the raw data does not
support. We compare the mean-centred log-PSTH shape to the fitted (already
mean-centred) Fourier kernel at the phase-bin centres.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

from .bases import evaluate_kernel
from .psth import psth

_EPS = 1e-9


def psth_vs_kernel(
    df,
    fitted,
    covariate: str,
    n_bins: int = 24,
    n_boot: int = 200,
    agreement_threshold: float = 0.7,
    rng=None,
) -> Dict[str, object]:
    """Correlate the marginal PSTH shape with the joint kernel for ``covariate``."""
    if covariate not in fitted.kernels:
        return {"covariate": covariate, "error": "covariate not in fitted model", "agrees": False}

    out = psth(
        df[covariate].to_numpy(dtype=float),
        df["y"].to_numpy(dtype=float),
        df["exposure"].to_numpy(dtype=float),
        n_bins=n_bins,
        n_boot=n_boot,
        rng=rng,
    )
    centers = out["phase_centers"]
    rate = np.clip(out["rate"], _EPS, None)
    log_psth = np.log(rate)
    log_psth_centered = log_psth - log_psth.mean()

    kernel = fitted.kernels[covariate]
    kernel_at_centers = evaluate_kernel(centers, kernel.cos, kernel.sin)

    if np.std(log_psth_centered) < _EPS or np.std(kernel_at_centers) < _EPS:
        corr = 0.0
    else:
        corr = float(np.corrcoef(log_psth_centered, kernel_at_centers)[0, 1])

    rmse = float(np.sqrt(np.mean((log_psth_centered - kernel_at_centers) ** 2)))
    return {
        "covariate": covariate,
        "phase_centers": centers,
        "log_psth_centered": log_psth_centered,
        "kernel_at_centers": kernel_at_centers,
        "correlation": corr,
        "rmse": rmse,
        "agrees": bool(corr >= agreement_threshold),
    }
