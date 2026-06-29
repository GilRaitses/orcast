"""Periodic (Fourier) bases for cyclic kernels.

Each cyclic covariate (diel, tide, lunar, season) is represented on a phase in
``[0, 1)`` by a truncated Fourier series with no constant term, so the basis is
mean-zero over the cycle and the model intercept owns the level (the
identifiability constraint in CALIBRATION_STUDIES.md). This mirrors INDYsim's
``compute_phase_covariates`` (sin/cos terms) generalized to arbitrary harmonics.

The fitted coefficients map directly onto the ``FourierKernel`` the serving
module evaluates (``src/aws_backend/kernel_model/serve.py``): column order is
``[cos_1, sin_1, cos_2, sin_2, ...]``.
"""

from __future__ import annotations

from typing import List, Tuple

import numpy as np


def fourier_columns(phase: np.ndarray, n_harmonics: int) -> Tuple[np.ndarray, List[str]]:
    """Design columns for a phase in ``[0, 1)``: ``[cos_h, sin_h]`` for h=1..H.

    Returns the ``(n, 2H)`` matrix and the column names, interleaved as
    ``cos_1, sin_1, cos_2, sin_2, ...`` so coefficients split cleanly into the
    cos/sin lists the serving kernel expects.
    """
    phase = np.asarray(phase, dtype=float)
    cols = []
    names: List[str] = []
    for h in range(1, n_harmonics + 1):
        angle = 2.0 * np.pi * h * phase
        cols.append(np.cos(angle))
        names.append(f"cos_{h}")
        cols.append(np.sin(angle))
        names.append(f"sin_{h}")
    if not cols:
        return np.empty((phase.size, 0)), names
    return np.column_stack(cols), names


def split_coefficients(coefs: np.ndarray, n_harmonics: int) -> Tuple[List[float], List[float]]:
    """Split interleaved ``[cos_1, sin_1, ...]`` coefficients into cos/sin lists."""
    coefs = np.asarray(coefs, dtype=float).ravel()
    cos = [float(coefs[2 * h]) for h in range(n_harmonics)]
    sin = [float(coefs[2 * h + 1]) for h in range(n_harmonics)]
    return cos, sin


def evaluate_kernel(phase: np.ndarray, cos: List[float], sin: List[float]) -> np.ndarray:
    """Evaluate a Fourier kernel at ``phase`` (matches serve.FourierKernel.value)."""
    phase = np.asarray(phase, dtype=float)
    total = np.zeros_like(phase)
    for h, c in enumerate(cos, start=1):
        total += c * np.cos(2.0 * np.pi * h * phase)
    for h, s in enumerate(sin, start=1):
        total += s * np.sin(2.0 * np.pi * h * phase)
    return total


def kernel_curve(
    cos: List[float],
    sin: List[float],
    n_points: int = 200,
) -> Tuple[np.ndarray, np.ndarray]:
    """Sample a kernel over one cycle for plotting: ``(phase_grid, values)``."""
    grid = np.linspace(0.0, 1.0, n_points, endpoint=False)
    return grid, evaluate_kernel(grid, cos, sin)
