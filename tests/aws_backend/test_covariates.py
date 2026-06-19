"""Tests for the solar/lunar covariate module against known references."""

from datetime import datetime, timezone

from src.aws_backend import covariates as cov

# San Juan Island pilot region.
SAN_JUAN_LAT = 48.5
SAN_JUAN_LNG = -123.0

# Local solar noon at -123 deg longitude is ~12:00 + 123/15 h = 20:12 UTC
# (mean solar time, 4 minutes per degree of longitude).
LOCAL_NOON_UTC_HOUR = 20
LOCAL_NOON_UTC_MIN = 12


def _utc(year, month, day, hour=0, minute=0):
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


# --- solar position ----------------------------------------------------------


def test_daytime_at_local_noon_summer_solstice():
    dt = _utc(2024, 6, 20, LOCAL_NOON_UTC_HOUR, LOCAL_NOON_UTC_MIN)
    pos = cov.solar_position(dt, SAN_JUAN_LAT, SAN_JUAN_LNG)
    assert pos["is_daytime"] is True
    assert pos["solar_elevation_deg"] > 0.0


def test_summer_solstice_long_daylight():
    dt = _utc(2024, 6, 20, LOCAL_NOON_UTC_HOUR, LOCAL_NOON_UTC_MIN)
    times = cov.sun_times(dt, SAN_JUAN_LAT, SAN_JUAN_LNG)
    assert times["daylight_hours"] > 15.0
    assert times["sunrise_utc"] is not None
    assert times["sunset_utc"] is not None


def test_winter_solstice_short_daylight():
    dt = _utc(2024, 12, 21, LOCAL_NOON_UTC_HOUR, LOCAL_NOON_UTC_MIN)
    times = cov.sun_times(dt, SAN_JUAN_LAT, SAN_JUAN_LNG)
    assert times["daylight_hours"] < 9.0


def test_elevation_negative_at_solar_midnight():
    # Local solar midnight is ~12 hours from local solar noon -> ~08:12 UTC.
    dt = _utc(2024, 6, 21, 8, 12)
    pos = cov.solar_position(dt, SAN_JUAN_LAT, SAN_JUAN_LNG)
    assert pos["solar_elevation_deg"] < 0.0
    assert pos["is_daytime"] is False


def test_elevation_near_zero_at_sunrise_and_sunset():
    day = _utc(2024, 9, 22, 12)  # near equinox
    times = cov.sun_times(day, SAN_JUAN_LAT, SAN_JUAN_LNG)

    sunrise = times["sunrise_utc"]
    sunset = times["sunset_utc"]
    assert sunrise is not None and sunset is not None

    rise_elev = cov.solar_position(sunrise, SAN_JUAN_LAT, SAN_JUAN_LNG)[
        "solar_elevation_deg"
    ]
    set_elev = cov.solar_position(sunset, SAN_JUAN_LAT, SAN_JUAN_LNG)[
        "solar_elevation_deg"
    ]
    # At apparent sunrise/sunset the geometric center sits ~ -0.83 deg.
    assert abs(rise_elev + 0.833) < 0.5
    assert abs(set_elev + 0.833) < 0.5


def test_hour_angle_negative_before_noon_positive_after():
    morning = _utc(2024, 6, 21, 16, 0)  # well before 20:12 UTC local noon
    evening = _utc(2024, 6, 22, 0, 0)  # after local noon
    assert cov.solar_position(morning, SAN_JUAN_LAT, SAN_JUAN_LNG)["hour_angle_deg"] < 0
    assert cov.solar_position(evening, SAN_JUAN_LAT, SAN_JUAN_LNG)["hour_angle_deg"] > 0


# --- diel phase --------------------------------------------------------------


def test_diel_phase_half_at_local_solar_noon():
    dt = _utc(2024, 6, 20, LOCAL_NOON_UTC_HOUR, LOCAL_NOON_UTC_MIN)
    phase = cov.diel_phase(dt, SAN_JUAN_LNG)
    assert abs(phase - 0.5) < 0.02


def test_diel_phase_range():
    dt = _utc(2024, 3, 1, 3, 45)
    phase = cov.diel_phase(dt, SAN_JUAN_LNG)
    assert 0.0 <= phase < 1.0


# --- lunar phase -------------------------------------------------------------


def test_full_moon_high_illumination():
    # 2024-06-22 is near a full moon.
    dt = _utc(2024, 6, 22, 1, 0)
    moon = cov.lunar_phase(dt)
    assert moon["illumination_fraction"] > 0.9
    assert abs(moon["phase"] - 0.5) < 0.1


def test_new_moon_low_illumination():
    # 2024-06-06 is near a new moon.
    dt = _utc(2024, 6, 6, 12, 0)
    moon = cov.lunar_phase(dt)
    assert moon["illumination_fraction"] < 0.1
    assert 0.0 <= moon["phase"] < 1.0
    assert 0.0 <= moon["age_days"] < cov._SYNODIC_MONTH


# --- convenience vector ------------------------------------------------------


def test_covariate_vector_keys_and_consistency():
    dt = _utc(2024, 6, 20, LOCAL_NOON_UTC_HOUR, LOCAL_NOON_UTC_MIN)
    vec = cov.covariate_vector(dt, SAN_JUAN_LAT, SAN_JUAN_LNG)
    assert set(vec) == {
        "solar_elevation_deg",
        "is_daytime",
        "daylight_hours",
        "diel_phase",
        "lunar_illumination",
        "lunar_phase",
    }
    assert vec["is_daytime"] is True
    assert vec["daylight_hours"] > 15.0
    assert abs(vec["diel_phase"] - 0.5) < 0.02
    assert 0.0 <= vec["lunar_illumination"] <= 1.0
