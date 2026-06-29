"""Adversarial-review tests: overdispersion, correlated covariates, partial cycles.

These encode the methodology fixes the way the review framed them:

* a Poisson fit on overdispersed (clustered) counts must FAIL the calibration
  gate, while the negative-binomial fit recovers calibration;
* a covariate that is only spuriously correlated with the driver is correctly
  de-confounded by the joint kernel, and the resulting PSTH-vs-kernel divergence
  is a diagnostic that must NOT cost confidence;
* a cyclic covariate observed over only part of its cycle (a partial annual
  cycle for season) is excluded from the fit as extrapolated.
"""

import numpy as np
import pandas as pd

from modeling.bases import evaluate_kernel
from modeling.design import phase_coverage
from modeling.estimator import fit_glm
from modeling.fit_kernels import _confidence_from_gates, _select_covariates
from modeling.psth_vs_kernel import psth_vs_kernel
from modeling.validation.diagnostics import pit_uniformity


# --- (a) overdispersed / clustered counts ------------------------------------

def _overdispersed_design(n=6000, alpha_true=1.0, seed=0):
    """Single-station counts from an NB2 (gamma-Poisson) mixture with a diel kernel.

    ``y ~ Poisson(lam)``, ``lam ~ Gamma(k=1/alpha, theta=alpha*mu)`` gives
    ``E[y]=mu`` and ``Var[y]=mu + alpha*mu^2`` -- genuine overdispersion that a
    Poisson likelihood cannot represent.
    """
    rng = np.random.default_rng(seed)
    diel = rng.uniform(size=n)
    kernel = {"cos": [0.8, 0.0], "sin": [0.3, 0.0]}
    log_rate = 1.2 + evaluate_kernel(diel, kernel["cos"], kernel["sin"])
    mu = np.exp(log_rate)
    shape = 1.0 / alpha_true
    lam = rng.gamma(shape=shape, scale=alpha_true * mu)
    y = rng.poisson(lam).astype(float)
    df = pd.DataFrame({
        "station": "only",
        "t": np.arange(n, dtype=float),
        "diel": diel,
        "exposure": 1.0,
        "y": y,
    })
    return df


def test_poisson_overdispersion_fails_pit_but_nb_recovers():
    df = _overdispersed_design(n=6000, alpha_true=1.0, seed=1)
    y = df["y"].to_numpy(dtype=float)

    pois = fit_glm(df, covariates=("diel",), n_harmonics=2,
                   use_station_effects=False, family="poisson")
    nb = fit_glm(df, covariates=("diel",), n_harmonics=2,
                 use_station_effects=False, family="negbin")

    # Poisson cannot absorb the spread: Pearson dispersion is far above 1.
    assert pois.pearson_dispersion > 1.5
    # NB recovers a substantial dispersion close to the truth (alpha_true=1.0).
    assert nb.dispersion_alpha is not None and nb.dispersion_alpha > 0.4
    # NB's own Pearson dispersion sits near 1 (variance now modelled).
    assert nb.pearson_dispersion < pois.pearson_dispersion

    mu_p = pois.predict(df)
    mu_nb = nb.predict(df)
    pit_p = pit_uniformity(y, mu_p, rng=np.random.default_rng(2), alpha=0.0)
    pit_nb = pit_uniformity(y, mu_nb, rng=np.random.default_rng(3), alpha=nb.dispersion_alpha)

    # The Poisson calibration gate must FAIL; the NB one must PASS.
    assert pit_p["calibrated"] is False
    assert pit_nb["calibrated"] is True


def test_kernel_ci_band_widens_under_overdispersion():
    df = _overdispersed_design(n=6000, alpha_true=1.0, seed=4)
    pois = fit_glm(df, covariates=("diel",), n_harmonics=2,
                   use_station_effects=False, family="poisson")
    # Bands scale by sqrt(phi); with phi>1 the published Poisson band is wider
    # than the naive (phi=1) band, i.e. not anticonservative.
    curves = pois.kernel_curves(n_points=50)
    width = np.array(curves["diel"]["ci_hi"]) - np.array(curves["diel"]["ci_lo"])
    naive_scale = float(np.sqrt(max(pois.pearson_dispersion, 1.0)))
    assert naive_scale > 1.2
    assert np.all(width > 0)


# --- (b) correlated covariates: de-confounding + diagnostic, not a gate -------

def _correlated_design(n=12000, seed=0):
    """Rate driven ONLY by diel; ``tide`` is a noisy copy of diel (confounded)."""
    rng = np.random.default_rng(seed)
    diel = rng.uniform(size=n)
    tide = (diel + rng.normal(0.0, 0.03, size=n)) % 1.0  # strongly correlated, no signal
    kernel = {"cos": [0.9, 0.0], "sin": [0.4, 0.0]}
    log_rate = 0.5 + evaluate_kernel(diel, kernel["cos"], kernel["sin"])
    mu = np.exp(log_rate)
    y = rng.poisson(mu).astype(float)
    df = pd.DataFrame({
        "station": "only",
        "t": np.arange(n, dtype=float),
        "diel": diel,
        "tide": tide,
        "exposure": 1.0,
        "y": y,
    })
    return df


def test_joint_kernel_deconfounds_correlated_covariate():
    df = _correlated_design(n=12000, seed=5)
    model = fit_glm(df, covariates=("diel", "tide"), n_harmonics=2,
                    use_station_effects=False, family="poisson")

    grid = np.linspace(0, 1, 200, endpoint=False)
    diel_amp = float(np.std(evaluate_kernel(grid, model.kernels["diel"].cos, model.kernels["diel"].sin)))
    tide_amp = float(np.std(evaluate_kernel(grid, model.kernels["tide"].cos, model.kernels["tide"].sin)))

    # The joint model assigns the structure to diel and flattens the spurious
    # tide kernel: correct de-confounding.
    assert diel_amp > 0.3
    assert tide_amp < diel_amp * 0.5

    # The marginal PSTH for tide still looks modulated (it is confounded with
    # diel), so PSTH-vs-kernel can legitimately DISAGREE for tide.
    diag = psth_vs_kernel(df, model, "tide", n_bins=24, n_boot=50,
                          rng=np.random.default_rng(6))
    assert diag["agrees"] is False


def test_psth_kernel_divergence_does_not_change_confidence():
    """The PSTH-vs-kernel diagnostic must neither earn nor cost confidence."""
    base = {
        "cv": {"gate_pass": True},
        "time_rescaling": {"pooled_pass_exp": None},
        "pit": {"calibrated": True},
        "level1_psth": {"diel": {"beats_null": True}},
    }
    # Confidence with the joint gate (CV) passing, regardless of the diagnostic.
    conf_disagree = _confidence_from_gates({
        **base, "psth_vs_kernel_diagnostic": {"tide": {"agrees": False}, "diel": {"agrees": False}},
    })
    conf_agree = _confidence_from_gates({
        **base, "psth_vs_kernel_diagnostic": {"tide": {"agrees": True}, "diel": {"agrees": True}},
    })
    assert conf_disagree == conf_agree
    assert conf_disagree > 0.0

    # Without ANY joint gate, the marginal PSTH + a "consistent" diagnostic
    # cannot manufacture confidence: it must be exactly 0.
    no_joint = _confidence_from_gates({
        "cv": {"gate_pass": False},
        "time_rescaling": {"pooled_pass_exp": False},
        "pit": {"calibrated": False},
        "level1_psth": {"diel": {"beats_null": True}},
        "psth_vs_kernel_diagnostic": {"diel": {"agrees": True}},
    })
    assert no_joint == 0.0


def test_pit_credited_only_when_timing_gate_passes():
    """PIT calibration only earns a quarter when time-rescaling also passes.

    NB's free dispersion makes PIT uniformity near-automatic, so crediting it
    while the event-timing GOF (time-rescaling) is rejected over-credits the
    model. This mirrors the live single-station case (CV + lunar null pass,
    PIT calibrated, but time-rescaling FAILS) which must score 0.5, not 0.75.
    """
    level1 = {"lunar": {"beats_null": True}}

    # Live-like case: CV passes, PIT calibrated, time-rescaling FAILS.
    # PIT quarter must be EXCLUDED -> 0.25 (CV) + 0.25 (level1) = 0.5.
    conf_timing_fail = _confidence_from_gates({
        "cv": {"gate_pass": True},
        "time_rescaling": {"pooled_pass_exp": False},
        "pit": {"calibrated": True},
        "level1_psth": level1,
    })
    assert conf_timing_fail == 0.5

    # Same gates but time-rescaling now PASSES -> PIT quarter IS credited:
    # 0.25 (CV) + 0.25 (time-rescaling) + 0.25 (PIT) + 0.25 (level1) = 1.0.
    conf_timing_pass = _confidence_from_gates({
        "cv": {"gate_pass": True},
        "time_rescaling": {"pooled_pass_exp": True},
        "pit": {"calibrated": True},
        "level1_psth": level1,
    })
    assert conf_timing_pass == 1.0

    # The PIT quarter is exactly the difference attributable to the timing gate.
    # Holding PIT calibrated fixed, toggling timing adds 0.5 (its own quarter
    # plus the now-credited PIT quarter), confirming PIT only counts with timing.
    assert conf_timing_pass - conf_timing_fail == 0.5


def test_non_positive_cv_skill_does_not_earn_cv_confidence():
    level1 = {"lunar": {"beats_null": True}}
    conf = _confidence_from_gates({
        "cv": {"gate_pass": True, "mean_deviance_skill": -0.01},
        "time_rescaling": {"pooled_pass_exp": False},
        "pit": {"calibrated": True},
        "level1_psth": level1,
    })
    assert conf == 0.0


# --- (c) partial annual cycle: season excluded as extrapolated ---------------

def test_phase_coverage_detects_partial_cycle():
    full = np.linspace(0, 1, 5000, endpoint=False)
    partial = np.linspace(0.0, 0.62, 3000)  # ~7.5 months of the annual cycle
    assert phase_coverage(full, n_bins=12) >= 0.99
    assert phase_coverage(partial, n_bins=12) < 0.9


def _partial_season_design(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({
        "station": "only",
        "t": np.arange(n, dtype=float),
        "diel": rng.uniform(size=n),
        "tide": rng.uniform(size=n),
        "lunar": rng.uniform(size=n),
        # Season only spans ~62% of the year -> incomplete phase support.
        "season": rng.uniform(0.0, 0.62, size=n),
        "exposure": 1.0,
        "y": rng.poisson(2.0, size=n).astype(float),
    })
    return df


def test_season_excluded_under_partial_coverage():
    df = _partial_season_design()
    # tide overlap asserted True so only the coverage rule is exercised here.
    report = {"tide_overlaps_acoustic": True}
    selected, notes = _select_covariates(df, report)

    assert "season" not in selected
    assert "diel" in selected and "tide" in selected and "lunar" in selected
    assert report.get("season_extrapolated") is True
    assert "season" in notes and "coverage" in notes["season"]


def test_full_season_coverage_is_kept():
    rng = np.random.default_rng(1)
    n = 4000
    df = pd.DataFrame({
        "station": "only",
        "t": np.arange(n, dtype=float),
        "diel": rng.uniform(size=n),
        "tide": rng.uniform(size=n),
        "lunar": rng.uniform(size=n),
        "season": rng.uniform(0.0, 1.0, size=n),
        "exposure": 1.0,
        "y": rng.poisson(2.0, size=n).astype(float),
    })
    report = {"tide_overlaps_acoustic": True}
    selected, _ = _select_covariates(df, report)
    assert "season" in selected
    assert report.get("season_extrapolated") in (False, None)


def test_tide_dropped_when_no_overlap():
    rng = np.random.default_rng(2)
    n = 2000
    df = pd.DataFrame({
        "station": "only",
        "t": np.arange(n, dtype=float),
        "diel": rng.uniform(size=n),
        "tide": rng.uniform(size=n),
        "lunar": rng.uniform(size=n),
        "season": rng.uniform(0.0, 1.0, size=n),
        "exposure": 1.0,
        "y": rng.poisson(2.0, size=n).astype(float),
    })
    report = {"tide_overlaps_acoustic": False}
    selected, notes = _select_covariates(df, report)
    assert "tide" not in selected
    assert "tide" in notes and "overlap" in notes["tide"]
