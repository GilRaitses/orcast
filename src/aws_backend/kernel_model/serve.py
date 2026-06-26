"""Serve a fitted kernel forecast: coefficients in, ``lambda(x, t)`` out.

The offline ``modeling`` package fits the log-linear Poisson model

    log lambda(station, t) = b0 + a_station
                             + k_diel(diel_phase)
                             + k_tide(tide_phase)
                             + k_lunar(lunar_phase)
                             + k_season(season_phase)
                             + log effort

and writes the coefficients to a JSON file (``fitted_kernels.json``). This
module loads that file and evaluates the intensity. It depends only on the
stdlib plus :mod:`src.aws_backend.covariates` (itself stdlib-only), so it is
safe to ship in the request path.

Each cyclic kernel is stored as a truncated Fourier series on a unit-period
phase in ``[0, 1)`` and is mean-centred over the cycle, so the intercept ``b0``
carries the overall level and each kernel carries only shape. This mirrors the
identifiability constraint in CALIBRATION_STUDIES.md ("each cyclic kernel
mean-centered so b0 carries the level").
"""

from __future__ import annotations

import json
import logging
import math
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from .. import covariates
from ..config import settings

logger = logging.getLogger(__name__)


# Default location of the fitted coefficients, written by
# ``modeling/fit_kernels.py``. Override via :func:`load_fitted_kernels`.
DEFAULT_COEFFICIENTS_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "models" / "fitted_kernels.json"
)

# S3 object keys for the production artifacts (under the models bucket).
COEFFICIENTS_S3_KEY = "models/fitted_kernels.json"
FIT_REPORT_S3_KEY = "models/fit_report.json"
CURRENT_POINTER_S3_KEY = "models/current.json"
PROMOTION_S3_KEY = "models/promotion.json"
DEFAULT_PROMOTION_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "models" / "promotion.json"
)
DEFAULT_CURRENT_POINTER_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "models" / "current.json"
)
PENDING_APPROVAL_S3_KEY = "models/pending_approval.json"
DEFAULT_PENDING_APPROVAL_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "models" / "pending_approval.json"
)

# Small in-process TTL cache so the request path does not hit S3 every call.
_S3_CACHE_TTL_SECONDS = 60.0
_s3_cache: Dict[str, tuple] = {}

# S3 error codes that genuinely mean "the object/bucket is not there yet" (i.e.
# the model has not been fitted/published). These are the ONLY conditions we
# cache as a ``None`` ("not fitted") result.
_S3_NOT_FOUND_CODES = {"NoSuchKey", "NoSuchBucket", "404", "NotFound"}


class S3ReadError(RuntimeError):
    """A non-404 failure reading an S3 object (IAM, throttling, network, ...).

    Distinct from a genuine miss so callers can avoid caching a transient error
    as "not fitted" (which would otherwise pin the wrong answer for the TTL).
    """


def read_s3_json(key: str, bucket: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Read a JSON object from the models bucket, cached briefly.

    Returns ``None`` only for a genuine miss (NoSuchKey/NoSuchBucket == "not
    fitted yet"), which is cached for the TTL. Any other botocore error (IAM
    denial, throttling, network) raises :class:`S3ReadError` and is NOT cached,
    so a transient blip cannot pin "not_fitted" for 60s.

    Lazily imports boto3/botocore so the module stays importable without AWS
    deps in dev/test.
    """
    bucket = bucket or settings.models_bucket
    cache_key = f"{bucket}/{key}"
    now = time.monotonic()
    cached = _s3_cache.get(cache_key)
    if cached is not None and (now - cached[0]) < _S3_CACHE_TTL_SECONDS:
        return cached[1]

    try:
        import boto3  # lazy: only needed in aws mode
        from botocore.exceptions import BotoCoreError, ClientError
    except ImportError:
        # No AWS deps available (dev/test). Treat as "not fitted" but do not
        # cache, since this is an environment condition, not a confirmed miss.
        logger.warning("read_s3_json: boto3/botocore unavailable; treating %s as not fitted", cache_key)
        return None

    s3 = boto3.client("s3", region_name=settings.aws_region)
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        payload = json.loads(obj["Body"].read())
    except ClientError as exc:
        code = (getattr(exc, "response", None) or {}).get("Error", {}).get("Code")
        if code in _S3_NOT_FOUND_CODES:
            # Confirmed miss: safe to cache the "not fitted" answer.
            _s3_cache[cache_key] = (now, None)
            return None
        logger.warning("read_s3_json: non-404 S3 error for %s (code=%s): %s", cache_key, code, exc)
        raise S3ReadError(f"S3 read failed for {cache_key} (code={code})") from exc
    except BotoCoreError as exc:
        logger.warning("read_s3_json: transient S3/network error for %s: %s", cache_key, exc)
        raise S3ReadError(f"S3 read failed for {cache_key}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        logger.warning("read_s3_json: malformed JSON for %s: %s", cache_key, exc)
        raise S3ReadError(f"Malformed JSON at {cache_key}") from exc

    _s3_cache[cache_key] = (now, payload)
    return payload


@dataclass(frozen=True)
class FourierKernel:
    """A mean-centred truncated Fourier series on a unit-period phase.

    ``cos`` and ``sin`` hold the harmonic coefficients (index 0 == first
    harmonic). There is no constant term: the kernel integrates to ~0 over the
    cycle so the model intercept owns the level.
    """

    cos: List[float] = field(default_factory=list)
    sin: List[float] = field(default_factory=list)

    def value(self, phase: float) -> float:
        """Evaluate the kernel at ``phase`` in ``[0, 1)`` (wraps automatically)."""
        p = phase - math.floor(phase)
        total = 0.0
        for h, c in enumerate(self.cos, start=1):
            total += c * math.cos(2.0 * math.pi * h * p)
        for h, s in enumerate(self.sin, start=1):
            total += s * math.sin(2.0 * math.pi * h * p)
        return total

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "FourierKernel":
        return cls(
            cos=[float(v) for v in (payload.get("cos") or [])],
            sin=[float(v) for v in (payload.get("sin") or [])],
        )


@dataclass(frozen=True)
class FittedKernels:
    """Container for a fitted model's coefficients and metadata."""

    intercept: float
    kernels: Dict[str, FourierKernel]
    station_effects: Dict[str, float] = field(default_factory=dict)
    bin_hours: float = 1.0
    version: str = "0"
    fitted_at: Optional[str] = None
    confidence: float = 0.0
    gates: Dict[str, object] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "FittedKernels":
        kernels_raw = payload.get("kernels") or {}
        kernels = {
            name: FourierKernel.from_dict(spec)
            for name, spec in kernels_raw.items()
            if isinstance(spec, Mapping)
        }
        station_effects = {
            str(k): float(v) for k, v in (payload.get("station_effects") or {}).items()
        }
        return cls(
            intercept=float(payload.get("intercept", 0.0)),
            kernels=kernels,
            station_effects=station_effects,
            bin_hours=float(payload.get("bin_hours", 1.0)),
            version=str(payload.get("version", "0")),
            fitted_at=payload.get("fitted_at"),  # type: ignore[arg-type]
            confidence=float(payload.get("confidence", 0.0)),
            gates=dict(payload.get("gates") or {}),
        )


def load_fitted_kernels(path: Optional[Path] = None) -> Optional[FittedKernels]:
    """Load fitted coefficients, or ``None`` when no fit has been produced yet.

    Resolution order: an explicit ``path`` (dev/tests) wins; otherwise in aws
    mode the coefficients are read from S3; otherwise the local default file.
    A ``None`` result means "no kernel forecast available yet, fall back to the
    prior/broad surface", not an error.
    """
    if path is not None:
        target = Path(path)
        if not target.exists():
            return None
        try:
            return FittedKernels.from_dict(json.loads(target.read_text()))
        except (json.JSONDecodeError, OSError):
            return None

    if settings.storage_backend.lower() == "aws":
        try:
            current = read_s3_json(CURRENT_POINTER_S3_KEY)
            key = (current or {}).get("fitted_kernels") or COEFFICIENTS_S3_KEY
            payload = read_s3_json(str(key))
        except S3ReadError:
            # Transient/IAM error: fall back to "no forecast" for this call
            # without poisoning the cache (already logged in read_s3_json).
            return None
        return FittedKernels.from_dict(payload) if payload else None

    local_path = _current_local_path("fitted_kernels", DEFAULT_COEFFICIENTS_PATH)
    if local_path is not None:
        try:
            return FittedKernels.from_dict(json.loads(local_path.read_text()))
        except (json.JSONDecodeError, OSError):
            return None

    if not DEFAULT_COEFFICIENTS_PATH.exists():
        return None
    try:
        return FittedKernels.from_dict(json.loads(DEFAULT_COEFFICIENTS_PATH.read_text()))
    except (json.JSONDecodeError, OSError):
        return None


def _current_local_path(pointer_key: str, fallback: Path) -> Optional[Path]:
    if not DEFAULT_CURRENT_POINTER_PATH.exists():
        return None
    try:
        pointer = json.loads(DEFAULT_CURRENT_POINTER_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    rel = pointer.get(pointer_key)
    if not rel:
        return None
    path = DEFAULT_CURRENT_POINTER_PATH.parent / str(rel)
    return path if path.exists() else fallback


def load_fit_report() -> Optional[Dict[str, Any]]:
    """Load the current fit report via models/current.json when available."""
    if settings.storage_backend.lower() == "aws":
        try:
            current = read_s3_json(CURRENT_POINTER_S3_KEY)
            key = (current or {}).get("fit_report") or FIT_REPORT_S3_KEY
            return read_s3_json(str(key))
        except S3ReadError:
            return None

    local = _current_local_path("fit_report", Path(__file__).resolve().parents[3] / "data" / "models" / "fit_report.json")
    if local is None:
        local = Path(__file__).resolve().parents[3] / "data" / "models" / "fit_report.json"
    if not local.exists():
        return None
    try:
        return json.loads(local.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _load_marker(s3_key: str, local_path: Path) -> Optional[Dict[str, Any]]:
    if settings.storage_backend.lower() == "aws":
        try:
            return read_s3_json(s3_key)
        except S3ReadError:
            return None
    if not local_path.exists():
        return None
    try:
        return json.loads(local_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def load_promotion() -> Optional[Dict[str, Any]]:
    """Read the latest human-approved promotion marker, or None if unpromoted."""
    return _load_marker(PROMOTION_S3_KEY, DEFAULT_PROMOTION_PATH)


def load_pending_approval() -> Optional[Dict[str, Any]]:
    """Read a pending human-approval request (task token + supervisor draft)."""
    return _load_marker(PENDING_APPROVAL_S3_KEY, DEFAULT_PENDING_APPROVAL_PATH)


# Phases the model understands; tide must be supplied by the caller (it depends
# on NOAA current/water-level state, which is not derivable from the clock).
_CLOCK_KERNELS = {"diel", "lunar", "season"}


class KernelForecaster:
    """Evaluate ``lambda(x, t)`` from fitted kernels and computed covariates."""

    def __init__(self, fit: FittedKernels) -> None:
        self.fit = fit

    @classmethod
    def from_path(cls, path: Optional[Path] = None) -> Optional["KernelForecaster"]:
        fit = load_fitted_kernels(path)
        return cls(fit) if fit is not None else None

    def clock_phases(self, when: datetime, lat: float, lng: float) -> Dict[str, float]:
        """Compute diel/lunar/season phases in ``[0, 1)`` from time + location."""
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        diel = covariates.diel_phase(when, lng)
        lunar = covariates.lunar_phase(when)["phase"]
        season = _season_phase(when)
        return {"diel": float(diel), "lunar": float(lunar), "season": float(season)}

    def log_intensity(
        self,
        when: datetime,
        lat: float,
        lng: float,
        station: Optional[str] = None,
        tide_phase: Optional[float] = None,
    ) -> float:
        """Return ``log lambda`` at a point (effort offset excluded: rate, not count)."""
        total = self.fit.intercept
        if station is not None:
            total += self.fit.station_effects.get(station, 0.0)

        phases = self.clock_phases(when, lat, lng)
        if tide_phase is not None:
            phases["tide"] = float(tide_phase)

        for name, kernel in self.fit.kernels.items():
            phase = phases.get(name)
            if phase is not None:
                total += kernel.value(phase)
        return total

    def intensity(
        self,
        when: datetime,
        lat: float,
        lng: float,
        station: Optional[str] = None,
        tide_phase: Optional[float] = None,
    ) -> float:
        """Expected encounter rate per bin (``exp`` of :meth:`log_intensity`)."""
        return math.exp(self.log_intensity(when, lat, lng, station, tide_phase))


def _season_phase(when: datetime) -> float:
    """Day-of-year mapped to ``[0, 1)`` (Jan 1 == 0). Leap years use 366."""
    start = datetime(when.year, 1, 1, tzinfo=when.tzinfo or timezone.utc)
    days_in_year = 366.0 if _is_leap(when.year) else 365.0
    elapsed = (when - start).total_seconds() / 86400.0
    return (elapsed / days_in_year) % 1.0


def _is_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
