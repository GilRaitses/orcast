"""Joint Poisson-GLM (LNP) estimator -- the Level 2 fit.

Ported from INDYsim ``hazard_model.py`` (cyclic sin/cos covariates, exposure
offset, cluster-robust SEs, kernel reconstruction with delta-method CI bands)
and specialized to orcast:

    log lambda(station, t) = b0 + a_station
                             + sum_j fourier_j(phase_j(t))
                             + log effort(station, t)

* Family is selectable: Poisson (the historical default) or negative binomial
  (NB2, ``Var = mu + alpha*mu^2``). NB is the recommended primary on the real
  single-station data because acoustic detection counts are overdispersed
  relative to Poisson; the dispersion ``alpha`` is estimated from the data.
* Cyclic covariates use a mean-zero Fourier basis, so b0 carries the level and
  each kernel carries only shape (identifiability).
* Station effects are fixed-effect dummies (INDYsim's primary posture) with
  cluster-robust SEs by station; a GLMM random-intercept is a documented
  follow-up.

The fitted object serializes straight into the serving schema
(``src/aws_backend/kernel_model/serve.py``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .bases import fourier_columns, split_coefficients, evaluate_kernel, kernel_curve

DEFAULT_COVARIATES = ("diel", "tide", "lunar", "season")
_EPS = 1e-9
# Floor for the estimated NB dispersion so NegativeBinomial(alpha) stays valid
# even when the data are (near-)Poisson and the auxiliary estimate collapses.
_MIN_ALPHA = 1e-6

# A Fourier coefficient column is named ``{cov}__cos_{h}`` / ``{cov}__sin_{h}``.
_FOURIER_HARMONIC = re.compile(r"__(?:cos|sin)_(\d+)$")


@dataclass
class KernelFit:
    name: str
    n_harmonics: int
    cos: List[float]
    sin: List[float]
    columns: List[str] = field(default_factory=list)

    def curve(self, n_points: int = 200):
        return kernel_curve(self.cos, self.sin, n_points=n_points)


@dataclass
class FittedModel:
    intercept: float
    kernels: Dict[str, KernelFit]
    station_effects: Dict[str, float]
    covariates: List[str]
    n_harmonics: int
    reference_station: Optional[str]
    result: object = None  # statsmodels GLMResults (offline only)
    column_names: List[str] = field(default_factory=list)
    family: str = "poisson"
    # NB2 dispersion ``alpha`` (None for Poisson). Var = mu + alpha*mu^2.
    dispersion_alpha: Optional[float] = None
    # Pearson dispersion phi = sum(pearson_resid^2)/df_resid; used to widen the
    # published CI bands when a Poisson fit is overdispersed (anticonservative).
    pearson_dispersion: float = 1.0
    # True when the fit used a smoothness (roughness) penalty
    # (``fit_regularized``). A penalized fit has no valid MLE covariance, so the
    # delta-method kernel CI bands are suppressed (TA5: do not emit
    # unpenalized-MLE bands for a penalized fit).
    penalized: bool = False
    # The smoothness penalty strength used for this fit (0.0 = unpenalized).
    smoothness_lambda: float = 0.0
    # APERIODIC linear covariates (TB2/TB5): each enters as a SINGLE standardized
    # linear column ``{name}__lin`` (an effect-modifier with the ``log E`` offset),
    # NOT a Fourier kernel. ``linear_scalers[name] = (mean, sd)`` is the train-fold
    # standardization reused at predict time; ``linear_effects[name]`` is the fitted
    # coefficient. Empty by default -> strict no-op (byte-identical to the cyclic-
    # only fit). The covariate FEED is operator-gated (no reachable source here), so
    # this is the landed-but-inert wire; serving is not driven by it until a feed
    # lands and a passing served gate + supervisor decision graduate it.
    linear_covariates: List[str] = field(default_factory=list)
    linear_scalers: Dict[str, tuple] = field(default_factory=dict)
    linear_effects: Dict[str, float] = field(default_factory=dict)

    # --- prediction ----------------------------------------------------------
    def _design(self, df: pd.DataFrame) -> pd.DataFrame:
        X = _build_features(df, self.covariates, self.n_harmonics)
        # Aperiodic linear columns, standardized by the stored TRAIN scalers (so
        # the test fold never re-estimates the mean/sd -- leakage-safe).
        for name in self.linear_covariates:
            if name in df.columns:
                v = df[name].to_numpy(dtype=float)
                mu, sd = self.linear_scalers.get(name, (0.0, 1.0))
                X[f"{name}__lin"] = (v - mu) / (sd if sd > _EPS else 1.0)
        X["const"] = 1.0
        # Station dummies aligned to training columns (unseen station -> reference).
        for col in self.column_names:
            if col.startswith("st__") and col not in X.columns:
                station = col[len("st__"):]
                X[col] = (df["station"].astype(str) == station).astype(float)
        # Keep exactly the trained columns in order (const filled above).
        return X.reindex(columns=self.column_names, fill_value=0.0)

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        X = self._design(df)
        offset = np.log(np.clip(df["exposure"].to_numpy(dtype=float), _EPS, None))
        return np.asarray(self.result.predict(X, offset=offset), dtype=float)

    def log_rate(self, phases: Dict[str, float], station: Optional[str] = None) -> float:
        """log lambda (per unit effort) for a single covariate phase dict."""
        total = self.intercept + (self.station_effects.get(station, 0.0) if station else 0.0)
        for name, kernel in self.kernels.items():
            if name in phases:
                total += float(evaluate_kernel(np.array([phases[name]]), kernel.cos, kernel.sin)[0])
        # Aperiodic linear effect-modifiers (TB2/TB5), standardized by the stored
        # train scaler. Only contributes when the covariate value is supplied.
        for name, coef in self.linear_effects.items():
            if name in phases:
                mu, sd = self.linear_scalers.get(name, (0.0, 1.0))
                total += coef * (float(phases[name]) - mu) / (sd if sd > _EPS else 1.0)
        return total

    # --- serialization -------------------------------------------------------
    def kernel_curves(self, n_points: int = 200) -> Dict[str, dict]:
        out: Dict[str, dict] = {}
        # A penalized (smoothness-prior) fit has no valid MLE covariance, so the
        # delta-method bands would be meaningless -- suppress them (TA5 §6).
        cov = None
        if self.result is not None and not self.penalized:
            try:
                cov = self.result.cov_params()
            except Exception:
                cov = None
        # Inflate the delta-method SEs by sqrt(phi) when the (Poisson) fit is
        # overdispersed, so the published bands are not anticonservative on the
        # single-station data. NB already absorbs dispersion into the variance
        # function, so its phi is ~1 and the inflation is a no-op there.
        se_scale = float(np.sqrt(max(self.pearson_dispersion, 1.0)))
        for name, kernel in self.kernels.items():
            grid, values = kernel.curve(n_points=n_points)
            entry = {"phase": grid.tolist(), "value": values.tolist()}
            if cov is not None:
                lo, hi = _kernel_ci(grid, kernel, cov, se_scale=se_scale)
                entry["ci_lo"] = lo.tolist()
                entry["ci_hi"] = hi.tolist()
            out[name] = entry
        return out

    def to_fitted_dict(self, confidence: float = 0.0) -> dict:
        return {
            "version": "0.1",
            "model": f"{self.family}_glm_lnp",
            "family": self.family,
            "dispersion_alpha": self.dispersion_alpha,
            "pearson_dispersion": self.pearson_dispersion,
            "intercept": self.intercept,
            "station_effects": self.station_effects,
            "kernels": {
                name: {"cos": k.cos, "sin": k.sin}
                for name, k in self.kernels.items()
            },
            "kernel_curves": self.kernel_curves(),
            "covariates": self.covariates,
            "n_harmonics": self.n_harmonics,
            "reference_station": self.reference_station,
            "confidence": confidence,
        }


def _build_features(df: pd.DataFrame, covariates, n_harmonics: int) -> pd.DataFrame:
    """Fourier feature columns for each usable covariate (no const/station)."""
    cols: Dict[str, np.ndarray] = {}
    for name in covariates:
        if name not in df.columns:
            continue
        phase = df[name].to_numpy(dtype=float)
        if not np.all(np.isfinite(phase)):
            continue  # covariate unavailable (e.g., no tidal series): skip it
        X, names = fourier_columns(phase, n_harmonics)
        for j, cname in enumerate(names):
            cols[f"{name}__{cname}"] = X[:, j]
    return pd.DataFrame(cols, index=df.index)


def usable_covariates(df: pd.DataFrame, covariates=DEFAULT_COVARIATES) -> List[str]:
    out = []
    for name in covariates:
        if name in df.columns and np.all(np.isfinite(df[name].to_numpy(dtype=float))):
            out.append(name)
    return out


def _estimate_nb_alpha(y: np.ndarray, mu: np.ndarray) -> float:
    """Estimate the NB2 dispersion ``alpha`` from a Poisson fit (Cameron-Trivedi).

    The standard auxiliary OLS regresses ``((y-mu)^2 - y)/mu`` on ``mu`` through
    the origin; the slope is the NB2 ``alpha`` in ``Var = mu + alpha*mu^2``.
    """
    mu = np.clip(np.asarray(mu, dtype=float), _EPS, None)
    y = np.asarray(y, dtype=float)
    aux = ((y - mu) ** 2 - y) / mu
    # Regress aux on mu with no intercept; slope estimates alpha.
    denom = float(np.sum(mu * mu))
    if denom <= 0:
        return _MIN_ALPHA
    alpha = float(np.sum(aux * mu) / denom)
    return max(alpha, _MIN_ALPHA)


def _fit_result(X: pd.DataFrame, y: np.ndarray, offset: np.ndarray, sm_family, groups):
    """Fit an sm.GLM with cluster-robust SEs when there are multiple stations."""
    model = sm.GLM(y, X, family=sm_family, offset=offset)
    if groups is not None and len(set(groups)) > 1:
        return model.fit(cov_type="cluster", cov_kwds={"groups": groups})
    return model.fit()


def _penalty_vector(
    columns: Sequence[str],
    smoothness_lambda: float = 0.0,
    smoothness_order: int = 2,
    ridge_lambda: float = 0.0,
    station_lambda: float = 0.0,
    station_cols: Optional[Sequence[str]] = None,
) -> Optional[np.ndarray]:
    """Per-column L2 penalty weights for the regularized GLM, or ``None``.

    Combines, additively, three independent priors (any subset may be active):

    * **Smoothness (TA5)** -- a roughness penalty on the Fourier coefficients with
      per-coefficient weight ``smoothness_lambda * h^(2*order)`` (the integrated
      squared ``order``-th derivative of a mean-zero Fourier series), penalizing
      high harmonics = a variance reducer on the existing kernels.
    * **Flat kernel ridge (TA2 PATCH-2)** -- a constant ``ridge_lambda`` on every
      Fourier coefficient (``lambda_k = 1/s_k^2``).
    * **Partial-pooling station ridge (TA2 PATCH-1)** -- ``station_lambda`` (=
      ``1/tau^2``) on the all-station deviation dummies in ``station_cols``, the
      MAP form of a Gaussian random intercept (shrinks sparse/absent stations to
      the population mean; coding-invariant).

    ``const`` is always unpenalized (it owns the level). Fixed-effect station
    dummies (NOT in ``station_cols``) are unpenalized too. Returns ``None`` when
    every weight is zero, so the caller keeps the historical unpenalized ``.fit()``
    path (byte-identical default).
    """
    pen = np.zeros(len(columns), dtype=float)
    scols = set(station_cols or [])
    any_nonzero = False
    for i, col in enumerate(columns):
        if col == "const":
            continue
        if col in scols:
            if station_lambda > 0:
                pen[i] = float(station_lambda)
                any_nonzero = True
            continue
        if col.startswith("st__"):
            continue  # fixed-effect station dummies stay unpenalized
        m = _FOURIER_HARMONIC.search(col)
        if m:
            h = int(m.group(1))
            w = 0.0
            if smoothness_lambda > 0:
                w += float(smoothness_lambda) * (h ** (2 * int(smoothness_order)))
            if ridge_lambda > 0:
                w += float(ridge_lambda)
            if w > 0:
                pen[i] = w
                any_nonzero = True
    return pen if any_nonzero else None


def _fit_regularized_result(X: pd.DataFrame, y: np.ndarray, offset: np.ndarray, sm_family, penalty_vec):
    """Pure-L2 (ridge) fit = the smoothness penalty in the Fourier basis.

    ``L1_wt=0.0`` makes elastic-net a pure ridge; ``alpha`` is the per-coefficient
    penalty vector. ``fit_regularized`` returns no covariance, so the caller must
    suppress the delta-method CI bands (``FittedModel.penalized``).
    """
    model = sm.GLM(y, X, family=sm_family, offset=offset)
    return model.fit_regularized(alpha=penalty_vec, L1_wt=0.0)


def fit_glm(
    df: pd.DataFrame,
    covariates=DEFAULT_COVARIATES,
    n_harmonics: int = 2,
    use_station_effects=True,
    family: str = "poisson",
    smoothness_lambda: float = 0.0,
    smoothness_order: int = 2,
    ridge_lambda: float = 0.0,
    pooling_tau: float = 0.0,
    linear_covariates: Sequence[str] = (),
) -> FittedModel:
    """Fit the joint GLM (``family`` in {"poisson", "negbin"}) and reconstruct kernels.

    For ``negbin`` the model is NB2: a Poisson fit seeds the dispersion ``alpha``
    via the Cameron-Trivedi auxiliary regression, then a negative-binomial GLM is
    refit at that ``alpha``. NB absorbs overdispersion that fails the Poisson GOF
    gates on the single-station data.

    Optional priors (all opt-in; the all-zero default is byte-identical to the
    historical unpenalized fit):

    * ``smoothness_lambda > 0`` -- TA5 roughness prior, ``lambda * h^(2*order)``
      on the Fourier coefficients (a variance reducer on the existing kernels).
    * ``ridge_lambda > 0`` -- TA2 flat ridge ``1/s_k^2`` on the Fourier coefs.
    * ``use_station_effects == "partial_pool"`` + ``pooling_tau > 0`` -- TA2
      partial-pooling random station intercept: all-station deviation dummies with
      a ridge ``1/pooling_tau^2`` (global intercept unpenalized). This shrinks
      sparse/absent stations to the population mean (coding-invariant), curing the
      fixed-effect held-out-station extrapolation fragility. ``use_station_effects``
      also accepts ``True`` (fixed-effect dummies, default) or ``False`` (none).
    * ``linear_covariates`` -- TB2/TB5 APERIODIC effect-modifiers (e.g. the
      season-orthogonalized ``sst_front`` gradient, or SalishSeaCast
      ``subtidal_conv``). Each enters as ONE standardized linear column, NOT a
      Fourier kernel, only when present and finite. The empty default is a strict
      no-op. The covariate feed is operator-gated; for the B.2 season-orthogonal
      role the residualization is applied per fold upstream (``make_fit_predict``).
    """
    family = (family or "poisson").lower()
    if family not in ("poisson", "negbin"):
        raise ValueError(f"family must be 'poisson' or 'negbin', got {family!r}")

    partial_pool = isinstance(use_station_effects, str) and use_station_effects == "partial_pool"
    use_fe = bool(use_station_effects) and not partial_pool
    if partial_pool and not (pooling_tau and pooling_tau > 0):
        raise ValueError("partial_pool requires pooling_tau > 0 (the random-intercept group SD)")

    covariates = usable_covariates(df, covariates)
    feats = _build_features(df, covariates, n_harmonics)

    # APERIODIC linear covariates (TB2/TB5 effect-modifiers): one standardized
    # column each, only when the column exists and is fully finite (handled like
    # the cyclic finite-guard). Empty default -> no columns -> byte-identical.
    lin_used: List[str] = [
        c for c in linear_covariates
        if c in df.columns and np.all(np.isfinite(df[c].to_numpy(dtype=float)))
    ]
    linear_scalers: Dict[str, tuple] = {}
    lin_feats: Dict[str, np.ndarray] = {}
    for c in lin_used:
        v = df[c].to_numpy(dtype=float)
        mu = float(np.mean(v))
        sd = float(np.std(v))
        linear_scalers[c] = (mu, sd)
        lin_feats[f"{c}__lin"] = (v - mu) / (sd if sd > _EPS else 1.0)

    X = pd.DataFrame(index=df.index)
    X["const"] = 1.0

    reference_station = None
    station_cols: List[str] = []
    stations = sorted(df["station"].astype(str).unique()) if "station" in df.columns else []
    if partial_pool and len(stations) > 1:
        # All-station deviation dummies; the ridge (1/tau^2) breaks the
        # const/station collinearity and is the MAP random intercept.
        for st in stations:
            col = f"st__{st}"
            X[col] = (df["station"].astype(str) == st).astype(float)
            station_cols.append(col)
        reference_station = None
    elif use_fe and len(stations) > 1:
        reference_station = stations[0]
        for st in stations[1:]:
            col = f"st__{st}"
            X[col] = (df["station"].astype(str) == st).astype(float)
            station_cols.append(col)
    elif stations:
        reference_station = stations[0]

    X = pd.concat([X, feats], axis=1)
    for cname, col in lin_feats.items():
        X[cname] = col
    y = df["y"].to_numpy(dtype=float)
    offset = np.log(np.clip(df["exposure"].to_numpy(dtype=float), _EPS, None))
    groups = df["station"].astype(str).to_numpy() if "station" in df.columns else None

    # statsmodels GLM.fit_regularized minimizes (1/nobs)*(-loglik) + alpha*pen, so
    # the random-intercept MAP penalty 0.5*(1/tau^2)*sum(beta_s^2) added to the
    # FULL negative log-likelihood maps to a per-observation alpha = 1/(tau^2*nobs)
    # (without the nobs factor, tau loses its group-SD meaning and over-shrinks by
    # ~nobs). The kernel ridge/smoothness terms are passed in already-normalized
    # units (their grids are nested-CV-selected in those units), so only the
    # station term carries the nobs scaling here.
    nobs = max(int(len(df)), 1)
    station_lambda = (1.0 / (float(pooling_tau) ** 2 * nobs)) if partial_pool else 0.0
    penalty_vec = _penalty_vector(
        list(X.columns),
        smoothness_lambda=smoothness_lambda, smoothness_order=smoothness_order,
        ridge_lambda=ridge_lambda, station_lambda=station_lambda,
        station_cols=station_cols if partial_pool else None,
    )
    penalized = penalty_vec is not None

    # NB2 alpha seed + Pearson-phi source. The all-station partial-pool design is
    # collinear (const + every station dummy), so it cannot be fit unpenalized --
    # seed from the same penalized design in that case; otherwise the historical
    # unpenalized Poisson seed.
    if partial_pool:
        poisson_result = _fit_regularized_result(X, y, offset, sm.families.Poisson(), penalty_vec)
    else:
        poisson_result = _fit_result(X, y, offset, sm.families.Poisson(), groups)

    dispersion_alpha: Optional[float] = None
    if family == "negbin":
        mu_p = np.asarray(poisson_result.fittedvalues, dtype=float)
        dispersion_alpha = _estimate_nb_alpha(y, mu_p)
        nb_family = sm.families.NegativeBinomial(alpha=dispersion_alpha)
        if penalized:
            result = _fit_regularized_result(X, y, offset, nb_family, penalty_vec)
        else:
            result = _fit_result(X, y, offset, nb_family, groups)
    else:
        if penalized:
            result = _fit_regularized_result(X, y, offset, sm.families.Poisson(), penalty_vec)
        else:
            result = poisson_result

    # Pearson dispersion phi from THIS family's fit (used to widen CI bands).
    try:
        df_resid = float(result.df_resid) if result.df_resid else 1.0
        pearson_dispersion = float(result.pearson_chi2 / df_resid) if df_resid > 0 else 1.0
    except Exception:
        pearson_dispersion = 1.0

    params = result.params
    intercept = float(params["const"])

    station_effects: Dict[str, float] = {}
    if partial_pool:
        # All stations carry a (shrunken) deviation; the level is in const.
        for st in stations:
            col = f"st__{st}"
            if col in params:
                station_effects[st] = float(params[col])
    elif reference_station is not None:
        station_effects[reference_station] = 0.0
        for st in stations[1:]:
            col = f"st__{st}"
            if col in params:
                station_effects[st] = float(params[col])

    kernels: Dict[str, KernelFit] = {}
    for name in covariates:
        cols = []
        for h in range(1, n_harmonics + 1):
            cols.append(f"{name}__cos_{h}")
            cols.append(f"{name}__sin_{h}")
        coefs = np.array([params[c] for c in cols])
        cos, sin = split_coefficients(coefs, n_harmonics)
        kernels[name] = KernelFit(name=name, n_harmonics=n_harmonics, cos=cos, sin=sin, columns=cols)

    linear_effects: Dict[str, float] = {}
    for c in lin_used:
        col = f"{c}__lin"
        if col in params:
            linear_effects[c] = float(params[col])

    return FittedModel(
        intercept=intercept,
        kernels=kernels,
        station_effects=station_effects,
        covariates=list(covariates),
        n_harmonics=n_harmonics,
        reference_station=reference_station,
        result=result,
        column_names=list(X.columns),
        family=family,
        dispersion_alpha=dispersion_alpha,
        pearson_dispersion=pearson_dispersion,
        penalized=penalized,
        smoothness_lambda=float(smoothness_lambda),
        linear_covariates=list(lin_used),
        linear_scalers=linear_scalers,
        linear_effects=linear_effects,
    )


def _kernel_ci(grid: np.ndarray, kernel: KernelFit, cov_params, se_scale: float = 1.0):
    """Delta-method 95% band for a kernel curve from the coef covariance.

    ``se_scale`` multiplies the standard errors (e.g. ``sqrt(phi)`` for an
    overdispersed Poisson fit) so the band is not anticonservative.
    """
    # Basis rows for the grid, ordered like kernel.columns (cos_h, sin_h, ...).
    rows = []
    for p in grid:
        row = []
        for h in range(1, kernel.n_harmonics + 1):
            row.append(np.cos(2 * np.pi * h * p))
            row.append(np.sin(2 * np.pi * h * p))
        rows.append(row)
    B = np.array(rows)  # (n_points, 2H)

    cov = np.asarray(cov_params.loc[kernel.columns, kernel.columns].to_numpy(), dtype=float)
    var = np.einsum("ij,jk,ik->i", B, cov, B)
    se = float(se_scale) * np.sqrt(np.clip(var, 0.0, None))
    center = evaluate_kernel(grid, kernel.cos, kernel.sin)
    return center - 1.96 * se, center + 1.96 * se


def make_fit_predict(
    covariates=DEFAULT_COVARIATES,
    n_harmonics: int = 2,
    family: str = "poisson",
    smoothness_lambda: float = 0.0,
    smoothness_lambda_grid: Optional[Sequence[float]] = None,
    smoothness_order: int = 2,
    selection_log: Optional[List[float]] = None,
    use_station_effects=True,
    ridge_lambda: float = 0.0,
    pooling_tau: float = 0.0,
    baseline_grid: Optional[Dict[str, Sequence[float]]] = None,
    baseline_selection_log: Optional[List[dict]] = None,
    linear_covariates: Sequence[str] = (),
    season_orthogonalize: bool = False,
) -> Callable[[pd.DataFrame, pd.DataFrame], np.ndarray]:
    """Build a ``(train, test) -> mu`` closure for the cross-validation harness.

    Smoothness prior (TA5):
      * ``smoothness_lambda_grid`` set -> select ``smoothness_lambda`` by NESTED
        ``block_cv`` inside ``train`` (no peeking at the outer held-out fold),
        then refit at the selected lambda. Per-fold selections are appended to
        ``selection_log`` when provided.
      * else -> fit at the fixed ``smoothness_lambda`` (default ``0.0`` =
        unpenalized = byte-identical to the historical behavior).

    Baseline enablers (TA2):
      * ``baseline_grid`` set (keys ``pooling_tau`` and/or ``ridge_lambda``) ->
        select those hypers by NESTED ``block_cv`` inside ``train`` (per fold),
        with the partial-pooling random intercept; selections appended to
        ``baseline_selection_log`` when provided.
      * else -> fit at the fixed ``use_station_effects`` / ``ridge_lambda`` /
        ``pooling_tau`` (defaults reproduce the fixed-effect unpenalized fit).

    Aperiodic covariates (TB2/TB5):
      * ``linear_covariates`` -> aperiodic effect-modifier columns (empty default
        = no-op). When ``season_orthogonalize`` is set, each is regressed on the
        season Fourier basis on the TRAIN fold ONLY and the train-estimated
        seasonal component is subtracted from BOTH train and test (the B.2 RAIL:
        only the season-orthogonal part of ``sst_front`` is admissible, and the
        residualization must be per fold to stay leakage-safe).
    """
    def fit_predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
        if linear_covariates and season_orthogonalize:
            train, test = _season_orthogonalize(
                train, test, linear_covariates, n_harmonics=n_harmonics,
            )
        lam = float(smoothness_lambda or 0.0)
        if smoothness_lambda_grid is not None:
            lam = _select_smoothness_lambda(
                train, covariates, family, smoothness_lambda_grid,
                n_harmonics=n_harmonics, smoothness_order=smoothness_order,
            )
            if selection_log is not None:
                selection_log.append(lam)

        use_se = use_station_effects
        tau = float(pooling_tau or 0.0)
        rl = float(ridge_lambda or 0.0)
        if baseline_grid is not None:
            tau, rl = _select_baseline_hypers(
                train, covariates, family, baseline_grid, n_harmonics=n_harmonics,
            )
            use_se = "partial_pool" if (tau and tau > 0) else use_station_effects
            if baseline_selection_log is not None:
                baseline_selection_log.append({"pooling_tau": tau, "ridge_lambda": rl})

        model = fit_glm(
            train, covariates=covariates, n_harmonics=n_harmonics, family=family,
            smoothness_lambda=lam, smoothness_order=smoothness_order,
            use_station_effects=use_se, ridge_lambda=rl, pooling_tau=tau,
            linear_covariates=linear_covariates,
        )
        return model.predict(test)

    return fit_predict


def _season_orthogonalize(
    train: pd.DataFrame,
    test: pd.DataFrame,
    linear_covariates: Sequence[str],
    n_harmonics: int = 2,
) -> tuple:
    """Residualize each aperiodic covariate against ``k_season`` (B.2 RAIL, TB2 §2.5).

    Absolute level signals (e.g. SST) are collinear with ``k_season``; only the
    season-orthogonal residual is the admissible independent driver. The seasonal
    component is estimated by OLS on the TRAIN fold's season Fourier basis and the
    SAME train coefficients are subtracted from both train and test (applying the
    train fit to the test covariate), so the credited skill is the season-orthogonal
    part and the transform is leakage-safe. Covariates absent/non-finite on train
    are left untouched. Returns ``(train_copy, test_copy)``.
    """
    if "season" not in train.columns:
        return train, test
    tr = train.copy()
    te = test.copy()
    s_tr = tr["season"].to_numpy(dtype=float)
    if not np.all(np.isfinite(s_tr)):
        return tr, te
    Btr, _ = fourier_columns(s_tr, n_harmonics)
    Atr = np.column_stack([np.ones(len(s_tr)), Btr])  # const + season harmonics
    s_te = te["season"].to_numpy(dtype=float) if "season" in te.columns else None
    Ate = None
    if s_te is not None and np.all(np.isfinite(s_te)):
        Bte, _ = fourier_columns(s_te, n_harmonics)
        Ate = np.column_stack([np.ones(len(s_te)), Bte])
    for c in linear_covariates:
        if c not in tr.columns:
            continue
        v = tr[c].to_numpy(dtype=float)
        if not np.all(np.isfinite(v)):
            continue
        beta, *_ = np.linalg.lstsq(Atr, v, rcond=None)
        tr[c] = v - Atr @ beta
        if Ate is not None and c in te.columns:
            ve = te[c].to_numpy(dtype=float)
            te[c] = ve - Ate @ beta
    return tr, te


def _select_baseline_hypers(
    train: pd.DataFrame,
    covariates,
    family: str,
    grid: Dict[str, Sequence[float]],
    n_harmonics: int = 2,
    n_inner_blocks: int = 3,
) -> tuple:
    """Nested-CV selection of (pooling_tau, ridge_lambda) on a training fold (TA2).

    Scores each (tau, ridge) combination by held-out ``block_cv`` mean-deviance-
    skill INSIDE ``train`` (partial-pooling random intercept) and returns the best
    pair. ``tau`` grid defaults to {0.5,1,2,5}; ``ridge_lambda`` grid defaults to
    {1.0, 0.25, 0.0} (= 1/s_k^2, s_k in {1,2,inf}). Inner folds default to 3 so
    the nested selection stays tractable on small sub-folds (TA2 §1.2).
    """
    from .validation.crossval import block_cv

    tau_grid = list(grid.get("pooling_tau", (0.5, 1.0, 2.0, 5.0)))
    ridge_grid = list(grid.get("ridge_lambda", (1.0, 0.25, 0.0)))
    best = (tau_grid[0] if tau_grid else 1.0, ridge_grid[0] if ridge_grid else 0.0)
    best_skill = -np.inf
    for tau in tau_grid:
        for rl in ridge_grid:
            fp = make_fit_predict(
                covariates=covariates, n_harmonics=n_harmonics, family=family,
                use_station_effects="partial_pool", pooling_tau=float(tau), ridge_lambda=float(rl),
            )
            try:
                res = block_cv(train, fp, n_blocks=n_inner_blocks)
            except Exception:
                continue
            skill = res.get("mean_deviance_skill")
            if isinstance(skill, (int, float)) and skill > best_skill:
                best_skill = float(skill)
                best = (float(tau), float(rl))
    return best


def _select_smoothness_lambda(
    train: pd.DataFrame,
    covariates,
    family: str,
    grid: Sequence[float],
    n_harmonics: int = 2,
    smoothness_order: int = 2,
    n_inner_blocks: int = 5,
) -> float:
    """Nested-CV selection of the smoothness lambda on a training fold.

    Scores each candidate lambda by held-out ``block_cv`` mean-deviance-skill
    INSIDE ``train`` and returns the best (ties -> the smaller lambda, since the
    grid is ascending and strict ``>`` keeps the first/earlier winner). Selection
    never sees the outer held-out fold (the anti-overfitting-safe number).
    """
    # Imported here to avoid a circular import at module load (crossval imports
    # diagnostics/null_tests only; estimator is imported by fit_kernels).
    from .validation.crossval import block_cv

    best_lambda = float(grid[0]) if len(grid) else 0.0
    best_skill = -np.inf
    for lam in grid:
        fp = make_fit_predict(
            covariates=covariates, n_harmonics=n_harmonics, family=family,
            smoothness_lambda=float(lam), smoothness_order=smoothness_order,
        )
        try:
            res = block_cv(train, fp, n_blocks=n_inner_blocks)
        except Exception:
            continue
        skill = res.get("mean_deviance_skill")
        if isinstance(skill, (int, float)) and skill > best_skill:
            best_skill = float(skill)
            best_lambda = float(lam)
    return best_lambda
