"""Residual, skill, and calibration diagnostics for the Poisson model.

Ported from INDYsim ``compute_deviance_residuals.py`` and
``add_model_metrics.py`` and specialized to the Poisson family orcast uses
(INDYsim used negative binomial). Provides:

* Poisson deviance + deviance residuals,
* McFadden pseudo-R^2 against an intercept-only (climatology) null,
* randomized PIT for count data (the calibration gate: PIT ~ Uniform(0,1)).
"""

from __future__ import annotations

from typing import Dict

import numpy as np
from scipy import stats

_EPS = 1e-9


def poisson_deviance_unit(y: np.ndarray, mu: np.ndarray) -> np.ndarray:
    """Per-observation Poisson deviance contribution ``d_i`` (always >= 0).

    ``D = sum d_i`` where ``d_i = 2 [ y log(y/mu) - (y - mu) ]`` and the
    ``y log y`` term is taken as 0 when ``y == 0``.
    """
    y = np.asarray(y, dtype=float)
    mu = np.clip(np.asarray(mu, dtype=float), _EPS, None)
    # Compute y*log(y/mu) only where y>0 so y==0 never hits log(0).
    term = np.zeros_like(y)
    pos = y > 0
    term[pos] = y[pos] * np.log(y[pos] / mu[pos])
    return 2.0 * (term - (y - mu))


def poisson_deviance(y: np.ndarray, mu: np.ndarray) -> float:
    """Total Poisson deviance ``sum_i d_i``."""
    return float(np.sum(poisson_deviance_unit(y, mu)))


def deviance_residuals(y: np.ndarray, mu: np.ndarray) -> np.ndarray:
    """Signed deviance residuals ``sign(y - mu) * sqrt(d_i)``."""
    y = np.asarray(y, dtype=float)
    mu = np.asarray(mu, dtype=float)
    d = poisson_deviance_unit(y, mu)
    return np.sign(y - mu) * np.sqrt(np.clip(d, 0.0, None))


def poisson_loglik(y: np.ndarray, mu: np.ndarray) -> float:
    """Poisson log-likelihood ``sum log P(y | mu)``."""
    mu = np.clip(np.asarray(mu, dtype=float), _EPS, None)
    return float(np.sum(stats.poisson.logpmf(np.asarray(y, dtype=float), mu)))


def null_loglik(y: np.ndarray, exposure: np.ndarray | None = None) -> float:
    """Log-likelihood of the intercept-only model (constant rate per effort).

    With an effort/exposure offset the null is ``mu_i = rate_hat * E_i`` where
    ``rate_hat = sum y / sum E``; without exposure it is the grand mean count.
    This is the climatology baseline McFadden's R^2 is measured against.
    """
    y = np.asarray(y, dtype=float)
    if exposure is None:
        mu = np.full(y.shape, max(y.mean(), _EPS))
    else:
        exposure = np.clip(np.asarray(exposure, dtype=float), _EPS, None)
        rate = max(y.sum() / exposure.sum(), _EPS)
        mu = rate * exposure
    return poisson_loglik(y, mu)


def mcfadden_r2(loglik_model: float, loglik_null: float) -> float:
    """McFadden pseudo-R^2 ``1 - ll_model / ll_null`` (both negative)."""
    if loglik_null == 0:
        return 0.0
    return float(1.0 - (loglik_model / loglik_null))


def model_metrics(
    y: np.ndarray,
    mu: np.ndarray,
    exposure: np.ndarray | None = None,
    n_params: int = 1,
) -> Dict[str, float]:
    """Bundle deviance, log-likelihood, pseudo-R^2, AIC/BIC into one dict."""
    y = np.asarray(y, dtype=float)
    ll = poisson_loglik(y, mu)
    ll0 = null_loglik(y, exposure)
    n = y.size
    return {
        "n": int(n),
        "deviance": poisson_deviance(y, mu),
        "loglik": ll,
        "null_loglik": ll0,
        "mcfadden_r2": mcfadden_r2(ll, ll0),
        "aic": float(2 * n_params - 2 * ll),
        "bic": float(n_params * np.log(max(n, 1)) - 2 * ll),
    }


def _nbinom_nq(mu: np.ndarray, alpha: float):
    """Convert NB2 (mu, alpha) to scipy nbinom (n, p): Var = mu + alpha*mu^2."""
    n = 1.0 / float(alpha)
    p = n / (n + mu)
    return n, p


def randomized_pit(
    y: np.ndarray,
    mu: np.ndarray,
    rng: np.random.Generator | None = None,
    alpha: float = 0.0,
) -> np.ndarray:
    """Randomized probability-integral-transform values for count data.

    For discrete data the PIT is randomized so that, under a correct model, the
    values are exactly ``Uniform(0, 1)``:
    ``u_i = F(y_i - 1; mu_i) + v_i * P(y_i; mu_i)``, ``v_i ~ U(0, 1)``.
    Feeding the result to a KS-vs-uniform test is the reliability/PIT gate.

    When ``alpha > 0`` the predictive distribution is negative binomial (NB2,
    ``Var = mu + alpha*mu^2``) rather than Poisson, so an overdispersed model is
    scored against its own predictive law instead of being penalised as if it
    were Poisson.
    """
    rng = rng or np.random.default_rng()
    y = np.asarray(y, dtype=float)
    mu = np.clip(np.asarray(mu, dtype=float), _EPS, None)
    if alpha and alpha > 0:
        n, p = _nbinom_nq(mu, alpha)
        lower = stats.nbinom.cdf(y - 1, n, p)
        pmf = stats.nbinom.pmf(y, n, p)
    else:
        lower = stats.poisson.cdf(y - 1, mu)
        pmf = stats.poisson.pmf(y, mu)
    v = rng.uniform(size=y.shape)
    return lower + v * pmf


def pit_uniformity(
    y: np.ndarray,
    mu: np.ndarray,
    rng: np.random.Generator | None = None,
    alpha: float = 0.0,
) -> Dict[str, object]:
    """KS test that the randomized PIT is ``Uniform(0, 1)`` (calibration gate)."""
    pit = randomized_pit(y, mu, rng=rng, alpha=alpha)
    ks = stats.kstest(pit, "uniform")
    return {
        "ks_stat": float(ks.statistic),
        "ks_pval": float(ks.pvalue),
        "calibrated": bool(ks.pvalue > 0.05),
        "pit": pit,
    }
