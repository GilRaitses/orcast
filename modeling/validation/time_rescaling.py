"""Time-rescaling goodness-of-fit (Brown et al. 2002).

Ported from INDYsim ``time_rescaling_test.py`` / ``compute_time_rescaling.py``
and made model-agnostic: it takes detection event times and an intensity
function ``lambda(t)`` (the fitted encounter rate for a station), integrates the
cumulative intensity between consecutive detections, and tests whether the
rescaled inter-event intervals follow ``Exp(1)``.

If the model captures the temporal structure, the rescaled IEIs are ``Exp(1)``
(equivalently ``1 - exp(-dtau)`` is ``Uniform(0, 1)``). This is the gold-standard
point-process GOF that sits behind every fitness gate in CALIBRATION_STUDIES.md.

The intensity is supplied as a piecewise representation on a grid
(``grid_times``, ``grid_intensity``) so the test is independent of how the model
was fit. Times are in arbitrary consistent units (hours since epoch is the
convention used by the orcast pipeline) and the intensity is a rate per that
same unit.
"""

from __future__ import annotations

from typing import Callable, Dict, Optional, Union

import numpy as np
from scipy import stats

IntensitySpec = Union[Callable[[np.ndarray], np.ndarray], tuple]


def cumulative_hazard(
    event_times: np.ndarray,
    grid_times: np.ndarray,
    grid_intensity: np.ndarray,
) -> np.ndarray:
    """Cumulative intensity ``Lambda(t) = integral_0^t lambda(s) ds`` at events.

    The intensity is treated as piecewise on ``grid_times`` and integrated with
    the trapezoid rule; ``Lambda`` is then interpolated to the event times.
    """
    event_times = np.asarray(event_times, dtype=float)
    grid_times = np.asarray(grid_times, dtype=float)
    grid_intensity = np.asarray(grid_intensity, dtype=float)
    if event_times.size == 0 or grid_times.size < 2:
        return np.zeros(event_times.shape)

    # Cumulative trapezoid of intensity over the grid.
    dt = np.diff(grid_times)
    avg = 0.5 * (grid_intensity[1:] + grid_intensity[:-1])
    cum = np.concatenate([[0.0], np.cumsum(avg * dt)])
    return np.interp(event_times, grid_times, cum)


def time_rescaling_test(
    event_times: np.ndarray,
    cum_hazard: np.ndarray,
    min_ieis: int = 10,
) -> Dict[str, object]:
    """KS test that rescaled IEIs ``dtau = diff(Lambda)`` are ``Exp(1)``.

    Returns the rescaled IEIs alongside the KS statistics against both ``Exp(1)``
    and (via ``1 - exp(-dtau)``) ``Uniform(0, 1)``, plus pass flags at p > 0.05.
    """
    event_times = np.asarray(event_times, dtype=float)
    rescaled = np.diff(np.asarray(cum_hazard, dtype=float))
    rescaled = rescaled[rescaled > 0]

    if rescaled.size < min_ieis:
        return {
            "n_events": int(event_times.size),
            "n_rescaled_ieis": int(rescaled.size),
            "error": "too few rescaled IEIs for a stable KS test",
            "pass_exp": False,
            "pass_unif": False,
            "rescaled_ieis": rescaled,
        }

    uniform_vals = 1.0 - np.exp(-rescaled)
    ks_exp = stats.kstest(rescaled, "expon", args=(0, 1))
    ks_unif = stats.kstest(uniform_vals, "uniform")

    return {
        "n_events": int(event_times.size),
        "n_rescaled_ieis": int(rescaled.size),
        "rescaled_iei_mean": float(np.mean(rescaled)),
        "rescaled_iei_std": float(np.std(rescaled)),
        "expected_mean": 1.0,
        "ks_exp_stat": float(ks_exp.statistic),
        "ks_exp_pval": float(ks_exp.pvalue),
        "ks_unif_stat": float(ks_unif.statistic),
        "ks_unif_pval": float(ks_unif.pvalue),
        "pass_exp": bool(ks_exp.pvalue > 0.05),
        "pass_unif": bool(ks_unif.pvalue > 0.05),
        "rescaled_ieis": rescaled,
    }


def _resolve_intensity(intensity: IntensitySpec, grid_times: np.ndarray) -> np.ndarray:
    if callable(intensity):
        return np.asarray(intensity(grid_times), dtype=float)
    grid_t, grid_lambda = intensity
    return np.interp(grid_times, np.asarray(grid_t, dtype=float), np.asarray(grid_lambda, dtype=float))


def run_time_rescaling(
    event_times: np.ndarray,
    intensity: IntensitySpec,
    grid_times: Optional[np.ndarray] = None,
    grid_step: float = 0.1,
    min_ieis: int = 10,
) -> Dict[str, object]:
    """Convenience wrapper: build the grid, integrate, and run the KS test.

    ``intensity`` is either a callable ``lambda(t_array) -> rate_array`` or a
    tuple ``(grid_t, grid_lambda)`` to interpolate. ``grid_step`` controls the
    integration resolution when ``grid_times`` is not supplied.
    """
    event_times = np.sort(np.asarray(event_times, dtype=float))
    if event_times.size < 2:
        return {"n_events": int(event_times.size), "pass_exp": False, "pass_unif": False,
                "error": "need >= 2 events"}

    if grid_times is None:
        lo = float(min(event_times[0], event_times[0] - grid_step))
        hi = float(event_times[-1] + grid_step)
        grid_times = np.arange(lo, hi + grid_step, grid_step)

    grid_intensity = _resolve_intensity(intensity, grid_times)
    cum = cumulative_hazard(event_times, grid_times, grid_intensity)
    return time_rescaling_test(event_times, cum, min_ieis=min_ieis)


def plot_time_rescaling(result: Dict[str, object], output_path) -> None:
    """Write the QQ / histogram diagnostic panel (matplotlib imported lazily)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rescaled = np.asarray(result.get("rescaled_ieis", []), dtype=float)
    if rescaled.size < 2:
        return

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    sorted_ieis = np.sort(rescaled)
    n = sorted_ieis.size
    theo = stats.expon.ppf(np.arange(1, n + 1) / (n + 1))

    ax = axes[0]
    ax.scatter(theo, sorted_ieis, alpha=0.5, s=10)
    m = max(theo.max(), sorted_ieis.max())
    ax.plot([0, m], [0, m], "r--", label="perfect fit")
    ax.set_xlabel("Theoretical Exp(1) quantiles")
    ax.set_ylabel("Rescaled IEI quantiles")
    ax.set_title("Time-rescaling QQ vs Exp(1)")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    ax.hist(rescaled, bins=30, density=True, alpha=0.7, label="observed")
    x = np.linspace(0, rescaled.max(), 200)
    ax.plot(x, stats.expon.pdf(x), "r-", lw=2, label="Exp(1)")
    pval = result.get("ks_exp_pval")
    ax.set_title(f"Rescaled IEIs (KS p={pval:.3f})" if pval is not None else "Rescaled IEIs")
    ax.set_xlabel("Rescaled IEI")
    ax.set_ylabel("Density")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
