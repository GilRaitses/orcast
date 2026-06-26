"""Forecast-kernel serving (shippable).

This package holds only what the deployed service needs to turn pre-fitted
kernel coefficients into an encounter-intensity ``lambda(x, t)``. Fitting,
validation, and study code live in the offline ``modeling/`` package and are
never imported here, so this stays dependency-light (stdlib + covariates).

See ``docs/methodology/FORECAST_KERNELS.md`` for the model and
``docs/methodology/CALIBRATION_STUDIES.md`` for the estimation program.
"""

from .serve import KernelForecaster, FittedKernels, load_fitted_kernels

__all__ = ["KernelForecaster", "FittedKernels", "load_fitted_kernels"]
