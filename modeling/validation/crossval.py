"""Time-blocked cross-validation with a go/no-go fitness gate.

Ported from INDYsim ``validate_factorial_cv.py`` (leave-one-experiment-out) and
adapted to orcast's requirement that splits are blocked by time (whole cycles
held out) to prevent leakage, and that the gate is held-out Poisson deviance
versus a climatology baseline rather than a rate-ratio window.

The estimator is injected as ``fit_predict(train_df, test_df) -> mu`` so the
harness stays decoupled from the GLM and is trivially testable.
"""

from __future__ import annotations

from typing import Callable, Dict, List

import numpy as np
import pandas as pd

from .diagnostics import poisson_deviance
from .null_tests import binomial_pass_test

FitPredict = Callable[[pd.DataFrame, pd.DataFrame], np.ndarray]

_EPS = 1e-9


def assign_time_blocks(times: np.ndarray, n_blocks: int) -> np.ndarray:
    """Assign each row to one of ``n_blocks`` contiguous time blocks.

    Blocks are equal-width in time (not equal-count), so a whole stretch of the
    timeline is held out together, which is what prevents cycle leakage.
    """
    t = np.asarray(times, dtype=float)
    if t.size == 0:
        return np.array([], dtype=int)
    lo, hi = t.min(), t.max()
    if hi <= lo:
        return np.zeros(t.size, dtype=int)
    edges = np.linspace(lo, hi, n_blocks + 1)
    # Right-closed final edge so the max value lands in the last block.
    blocks = np.clip(np.digitize(t, edges[1:-1]), 0, n_blocks - 1)
    return blocks.astype(int)


def _climatology_mu(train: pd.DataFrame, test: pd.DataFrame, y_col: str, exposure_col: str | None) -> np.ndarray:
    """Baseline prediction: constant rate per effort estimated on the train fold."""
    y_train = train[y_col].to_numpy(dtype=float)
    if exposure_col and exposure_col in train:
        e_train = np.clip(train[exposure_col].to_numpy(dtype=float), _EPS, None)
        e_test = np.clip(test[exposure_col].to_numpy(dtype=float), _EPS, None)
        rate = max(y_train.sum() / e_train.sum(), _EPS)
        return rate * e_test
    return np.full(len(test), max(y_train.mean(), _EPS))


def block_cv(
    df: pd.DataFrame,
    fit_predict: FitPredict,
    n_blocks: int = 5,
    time_col: str = "t",
    y_col: str = "y",
    exposure_col: str | None = "exposure",
) -> Dict[str, object]:
    """Run time-blocked CV; a fold passes when the model beats climatology.

    For each held-out time block the model is fit on the remaining blocks and
    scored by held-out Poisson deviance. The fold passes when the model deviance
    is below the climatology-baseline deviance (positive deviance skill). The
    overall gate is a one-sided binomial test that the pass rate beats chance.
    """
    if y_col not in df or time_col not in df:
        raise ValueError(f"df must contain '{time_col}' and '{y_col}' columns")

    blocks = assign_time_blocks(df[time_col].to_numpy(dtype=float), n_blocks)
    df = df.assign(_block=blocks)
    unique_blocks = sorted(df["_block"].unique())

    folds: List[Dict[str, object]] = []
    for b in unique_blocks:
        test = df[df["_block"] == b]
        train = df[df["_block"] != b]
        if len(test) == 0 or len(train) == 0:
            continue

        y_test = test[y_col].to_numpy(dtype=float)
        mu_model = np.clip(np.asarray(fit_predict(train, test), dtype=float), _EPS, None)
        mu_base = _climatology_mu(train, test, y_col, exposure_col)

        dev_model = poisson_deviance(y_test, mu_model)
        dev_base = poisson_deviance(y_test, mu_base)
        skill = 1.0 - (dev_model / dev_base) if dev_base > 0 else 0.0
        rate_ratio = float(mu_model.sum() / max(y_test.sum(), _EPS))

        folds.append({
            "block": int(b),
            "n_test": int(len(test)),
            "deviance_model": dev_model,
            "deviance_baseline": dev_base,
            "deviance_skill": float(skill),
            "rate_ratio": rate_ratio,
            "passed": bool(dev_model < dev_base),
        })

    n_pass = sum(1 for f in folds if f["passed"])
    n_folds = len(folds)
    skills = [f["deviance_skill"] for f in folds]

    return {
        "n_folds": n_folds,
        "n_pass": n_pass,
        "mean_deviance_skill": float(np.mean(skills)) if skills else 0.0,
        "median_deviance_skill": float(np.median(skills)) if skills else 0.0,
        "folds": folds,
        "null_test": binomial_pass_test(n_pass, n_folds) if n_folds else {},
        "gate_pass": bool(n_folds > 0 and n_pass > n_folds / 2.0),
    }
