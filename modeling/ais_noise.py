"""TA3 AIS-derived detectability factor ``D_ais`` for the ``log E`` offset.

Vessel noise masks SRKW calls and LOWERS detection probability, so it is an
EFFORT / EXPOSURE term (charter B.2), never a presence kernel. This module turns
a per-station proximity-noise index into a multiplicative detectability factor
``D_ais(s, t) in (min_d, 1]`` (1 = no masking) that the design multiplies into
the exposure and the time-rescaling intensity adds as ``log D_ais``. It adds
ZERO presence parameters: ``kappa`` is a fixed offset knob, not estimated.

Honesty (B.2/B.3): this module NEVER fabricates AIS. With no index, an unknown
station, or ``kappa == 0`` it returns ``D = 1`` (an exact no-op) and a
``missing_ais`` note rather than inventing masking. The real Marine Cadastre
fetch + ingest is a SEPARATE operator-/deploy-gated step (TA3 §2/§8); this
module is the pure, side-effect-free consumer of an already-ingested index.

Pure: no I/O, no S3, no global state. ``numpy`` + stdlib only.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence, Tuple

import numpy as np

# Floor on the detectability factor so ``log D_ais`` stays finite under heavy
# masking. ``log(1e-2) ~= -4.6``.
DEFAULT_MIN_D = 1e-2

# Coverage flag carried on any index built from US-side-only Marine Cadastre AIS
# (the dominant Haro Strait lane straddles the BC boundary; US NAIS under-counts
# purely-Canadian traffic, so the masking index is a LOWER bound). TA3 §3.
COVERAGE_US_SIDE_PARTIAL = "us_side_partial"

# A noise index is ``{station: (times_hours, I_norm)}`` where ``I_norm`` is the
# per-bin proximity load normalized to its own region-wide 95th percentile.
NoiseIndex = Dict[str, Tuple[np.ndarray, np.ndarray]]


def _interp_load(grid_t: np.ndarray, I_norm: np.ndarray, times: np.ndarray) -> np.ndarray:
    """Carry-forward (step) lookup of the normalized load at ``times``.

    Times before the first sample or after the last carry the nearest endpoint;
    a bottom-mounted index is a coarse per-bin series, not a smooth field.
    """
    if grid_t.size == 0:
        return np.zeros(times.shape, dtype=float)
    idx = np.searchsorted(grid_t, times, side="right") - 1
    idx = np.clip(idx, 0, grid_t.size - 1)
    return I_norm[idx].astype(float)


def detectability_factor(
    noise_index: Optional[NoiseIndex],
    station: str,
    times: Sequence[float],
    *,
    kappa: float = 0.0,
    min_d: float = DEFAULT_MIN_D,
) -> np.ndarray:
    """``D_ais(s, t) = exp(-kappa * I_norm(s, t))`` clipped to ``[min_d, 1]``.

    ``kappa == 0`` (the default) OR a missing index/station returns all-ones (an
    EXACT no-op), so wiring this in is byte-identical until a real AIS index and a
    non-zero ``kappa`` are supplied by the operator-gated build (TA3 §4 variant A).
    """
    t = np.atleast_1d(np.asarray(times, dtype=float))
    if not noise_index or float(kappa) <= 0.0 or station not in noise_index:
        return np.ones(t.shape, dtype=float)
    grid_t, I_norm = noise_index[station]
    grid_t = np.asarray(grid_t, dtype=float)
    I_norm = np.asarray(I_norm, dtype=float)
    load = _interp_load(grid_t, I_norm, t)
    return np.clip(np.exp(-float(kappa) * load), float(min_d), 1.0)


def log_detectability(
    noise_index: Optional[NoiseIndex],
    station: str,
    times: Sequence[float],
    *,
    kappa: float = 0.0,
    min_d: float = DEFAULT_MIN_D,
) -> np.ndarray:
    """``log D_ais(s, t)`` for the intensity grid; ``0.0`` (no-op) when inactive."""
    return np.log(detectability_factor(noise_index, station, times, kappa=kappa, min_d=min_d))


def is_active(noise_index: Optional[NoiseIndex], kappa: float = 0.0) -> bool:
    """True only when a non-empty index AND a positive ``kappa`` are both present."""
    return bool(noise_index) and float(kappa) > 0.0
