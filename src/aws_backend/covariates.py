"""Environmental / temporal covariate computation.

Pure-Python (stdlib only: ``math`` + ``datetime``) computation of solar and
lunar covariates used as features for forecasting. No external dependencies
(no numpy / astral) so the module is trivially importable everywhere.

All public functions accept a timezone-aware UTC ``datetime`` plus latitude /
longitude in decimal degrees (north and east positive). Inputs that carry a
non-UTC tzinfo are converted to UTC; naive datetimes are assumed to already be
UTC.

Algorithm sources
-----------------
* Solar position / sunrise-sunset: NOAA Solar Calculator equations, derived
  from Jean Meeus, *Astronomical Algorithms* (2nd ed.). See
  https://gml.noaa.gov/grad/solcalc/ and
  https://gml.noaa.gov/grad/solcalc/solareqns.PDF . Accuracy is ~0.5 deg for
  the elevation/azimuth over the modern era, which is ample for habitat
  covariates.
* Lunar phase: mean-synodic-month approximation anchored to a known new-moon
  epoch (Meeus, ch. 49). Phase age is exact to within a few hours, which is
  well inside the tolerances used by the consumers of these features.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

# --- constants ---------------------------------------------------------------

# Mean length of the synodic (new-moon-to-new-moon) month, in days. (Meeus.)
_SYNODIC_MONTH = 29.53058867

# Reference new moon: 2000-01-06 18:14 UTC == Julian Day 2451550.1. (Meeus.)
_NEW_MOON_EPOCH_JD = 2451550.1

# Standard refraction + solar-disk correction: the geometric center of the sun
# is 0.833 deg below the horizon at apparent sunrise/sunset. (NOAA.)
_SUNRISE_ZENITH_DEG = 90.833


# --- helpers -----------------------------------------------------------------


def _to_utc(dt: datetime) -> datetime:
    """Return ``dt`` as an aware UTC datetime (naive inputs assumed UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _julian_day(dt: datetime) -> float:
    """Julian Day (including fractional day) for an aware UTC datetime.

    Uses the standard Gregorian-calendar conversion (Meeus, ch. 7).
    """
    dt = _to_utc(dt)
    year = dt.year
    month = dt.month
    day = (
        dt.day
        + (dt.hour + dt.minute / 60.0 + (dt.second + dt.microsecond / 1e6) / 3600.0)
        / 24.0
    )
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    return (
        math.floor(365.25 * (year + 4716))
        + math.floor(30.6001 * (month + 1))
        + day
        + b
        - 1524.5
    )


def _minutes_of_day_utc(dt: datetime) -> float:
    dt = _to_utc(dt)
    return dt.hour * 60.0 + dt.minute + (dt.second + dt.microsecond / 1e6) / 60.0


def _solar_params(dt: datetime) -> Dict[str, float]:
    """Core NOAA intermediate quantities: declination and equation of time.

    Returns declination in degrees and the equation of time in minutes.
    """
    jc = (_julian_day(dt) - 2451545.0) / 36525.0  # Julian century since J2000.0

    geom_mean_long = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360.0
    geom_mean_anom = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    eccent = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)

    m = math.radians(geom_mean_anom)
    sun_eq_ctr = (
        math.sin(m) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
        + math.sin(2 * m) * (0.019993 - 0.000101 * jc)
        + math.sin(3 * m) * 0.000289
    )
    sun_true_long = geom_mean_long + sun_eq_ctr
    sun_app_long = sun_true_long - 0.00569 - 0.00478 * math.sin(
        math.radians(125.04 - 1934.136 * jc)
    )

    mean_obliq = 23.0 + (
        26.0 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60.0
    ) / 60.0
    obliq_corr = mean_obliq + 0.00256 * math.cos(math.radians(125.04 - 1934.136 * jc))

    declination = math.degrees(
        math.asin(
            math.sin(math.radians(obliq_corr)) * math.sin(math.radians(sun_app_long))
        )
    )

    var_y = math.tan(math.radians(obliq_corr / 2.0)) ** 2
    gl = math.radians(geom_mean_long)
    eq_of_time = 4.0 * math.degrees(
        var_y * math.sin(2 * gl)
        - 2 * eccent * math.sin(m)
        + 4 * eccent * var_y * math.sin(m) * math.cos(2 * gl)
        - 0.5 * var_y * var_y * math.sin(4 * gl)
        - 1.25 * eccent * eccent * math.sin(2 * m)
    )

    return {"declination_deg": declination, "eq_of_time_min": eq_of_time}


def _clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


# --- public API --------------------------------------------------------------


def solar_position(dt: datetime, lat: float, lng: float) -> Dict[str, object]:
    """Solar elevation/azimuth for a UTC time and location (NOAA equations).

    Returns a dict with ``solar_elevation_deg`` (degrees above the horizon,
    negative below), ``solar_azimuth_deg`` (degrees clockwise from true north),
    ``is_daytime`` (sun center above the apparent horizon) and
    ``hour_angle_deg`` (degrees, negative before solar noon).
    """
    dt = _to_utc(dt)
    params = _solar_params(dt)
    decl = math.radians(params["declination_deg"])
    eot = params["eq_of_time_min"]

    # True solar time in minutes; 4*lng converts degrees of longitude to minutes.
    true_solar_time = (_minutes_of_day_utc(dt) + eot + 4.0 * lng) % 1440.0
    hour_angle = true_solar_time / 4.0 - 180.0  # degrees, 0 at solar noon

    lat_r = math.radians(lat)
    ha_r = math.radians(hour_angle)

    cos_zenith = _clamp(
        math.sin(lat_r) * math.sin(decl)
        + math.cos(lat_r) * math.cos(decl) * math.cos(ha_r)
    )
    zenith = math.acos(cos_zenith)
    elevation = 90.0 - math.degrees(zenith)

    sin_zenith = math.sin(zenith)
    if sin_zenith < 1e-9:
        azimuth = 0.0  # sun directly overhead/underfoot; azimuth undefined
    else:
        cos_az = _clamp(
            (math.sin(lat_r) * cos_zenith - math.sin(decl))
            / (math.cos(lat_r) * sin_zenith)
        )
        az = math.degrees(math.acos(cos_az))
        # Mirror about the meridian for the afternoon (positive hour angle).
        azimuth = (180.0 + az) % 360.0 if hour_angle > 0 else (540.0 - az) % 360.0

    return {
        "solar_elevation_deg": elevation,
        "solar_azimuth_deg": azimuth,
        "is_daytime": elevation > -0.833,
        "hour_angle_deg": hour_angle,
    }


def sun_times(dt: datetime, lat: float, lng: float) -> Dict[str, object]:
    """Sunrise / sunset (UTC) and daylight length for the date of ``dt``.

    ``sunrise_utc`` / ``sunset_utc`` are aware UTC datetimes, or ``None`` for
    polar day/night when the sun does not cross the horizon. ``daylight_hours``
    is the length of daylight (0.0 for polar night, 24.0 for polar day).
    """
    dt = _to_utc(dt)
    params = _solar_params(dt)
    decl = math.radians(params["declination_deg"])
    eot = params["eq_of_time_min"]
    lat_r = math.radians(lat)

    cos_ha = (
        math.cos(math.radians(_SUNRISE_ZENITH_DEG))
        / (math.cos(lat_r) * math.cos(decl))
        - math.tan(lat_r) * math.tan(decl)
    )

    midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)

    if cos_ha > 1.0:
        # Sun stays below the horizon all day: polar night.
        return {"sunrise_utc": None, "sunset_utc": None, "daylight_hours": 0.0}
    if cos_ha < -1.0:
        # Sun stays above the horizon all day: polar day.
        return {"sunrise_utc": None, "sunset_utc": None, "daylight_hours": 24.0}

    ha_sunrise = math.degrees(math.acos(_clamp(cos_ha)))  # degrees

    # NOAA: solar-noon and event times expressed in minutes past UTC midnight.
    solar_noon_min = 720.0 - 4.0 * lng - eot
    sunrise_min = solar_noon_min - 4.0 * ha_sunrise
    sunset_min = solar_noon_min + 4.0 * ha_sunrise

    sunrise = midnight + timedelta(minutes=sunrise_min)
    sunset = midnight + timedelta(minutes=sunset_min)
    daylight_hours = (8.0 * ha_sunrise) / 60.0

    return {
        "sunrise_utc": sunrise,
        "sunset_utc": sunset,
        "daylight_hours": daylight_hours,
    }


def diel_phase(dt: datetime, lng: float) -> float:
    """Local mean-solar day fraction in ``[0, 1)`` (0 == local solar midnight).

    Uses longitude to shift UTC to local mean solar time (4 minutes per degree
    of longitude). 0.5 corresponds to local solar noon.
    """
    local_solar_min = (_minutes_of_day_utc(dt) + 4.0 * lng) % 1440.0
    return local_solar_min / 1440.0


def lunar_phase(dt: datetime) -> Dict[str, float]:
    """Moon phase via the mean-synodic-month approximation (Meeus, ch. 49).

    Returns ``phase`` in ``[0, 1)`` (0 == new, 0.5 == full), the
    ``illumination_fraction`` of the lunar disk in ``[0, 1]``, and ``age_days``
    (days since the most recent new moon, ``0 .. 29.53``).
    """
    days_since_epoch = _julian_day(dt) - _NEW_MOON_EPOCH_JD
    age_days = days_since_epoch % _SYNODIC_MONTH
    phase = age_days / _SYNODIC_MONTH
    # Illuminated fraction of a sphere lit at phase angle 2*pi*phase.
    illumination_fraction = (1.0 - math.cos(2.0 * math.pi * phase)) / 2.0
    return {
        "phase": phase,
        "illumination_fraction": illumination_fraction,
        "age_days": age_days,
    }


def covariate_vector(dt: datetime, lat: float, lng: float) -> Dict[str, object]:
    """Merge the key scalar solar/lunar features into one flat dict.

    Convenience wrapper combining :func:`solar_position`, :func:`sun_times`,
    :func:`diel_phase` and :func:`lunar_phase`.
    """
    sun = solar_position(dt, lat, lng)
    times = sun_times(dt, lat, lng)
    moon = lunar_phase(dt)
    return {
        "solar_elevation_deg": sun["solar_elevation_deg"],
        "is_daytime": sun["is_daytime"],
        "daylight_hours": times["daylight_hours"],
        "diel_phase": diel_phase(dt, lng),
        "lunar_illumination": moon["illumination_fraction"],
        "lunar_phase": moon["phase"],
    }
