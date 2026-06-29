"""Offline kernel-estimation package for orcast.

Ports the kernel/PSTH/point-process methodology audited in
``docs/methodology/INDYSIM_AUDIT.md`` into orcast's forecast-kernel program
(``docs/methodology/FORECAST_KERNELS.md`` and ``CALIBRATION_STUDIES.md``).

This package is offline only. It reads the existing time-series store
(``src/aws_backend/timeseries.py``) and computes covariates with the stdlib
``src/aws_backend/covariates.py``, fits the kernels with numpy/scipy/statsmodels,
and emits fitted coefficients as JSON. The deployed service never imports this
package; it loads the coefficients through
``src/aws_backend/kernel_model/serve.py``.
"""
