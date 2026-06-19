from src.aws_backend import geo_region as geo
from src.aws_backend.geo_region import SAN_JUAN_BOUNDS


def test_mask_loaded():
    # The real coastline mask should be present and parsed into rings.
    assert len(geo._LAND_RINGS) > 0


def test_in_bounds_inside_and_outside():
    assert geo.in_bounds(48.55, -123.20) is True
    # South of the region (Tacoma latitude) and far east/north.
    assert geo.in_bounds(47.35, -122.32) is False
    assert geo.in_bounds(48.80, -123.0) is False
    assert geo.in_bounds(48.5, -123.40) is False


def test_in_bounds_rejects_non_finite():
    assert geo.in_bounds(float("nan"), -123.0) is False
    assert geo.in_bounds(None, None) is False


def test_is_on_land_island_interior_true():
    # Deep in the interior of San Juan Island.
    assert geo.is_on_land(48.53, -123.08) is True
    # Orcas Island interior.
    assert geo.is_on_land(48.65, -122.93) is True


def test_is_in_water_haro_strait_true():
    # Haro Strait, west of San Juan Island, is open water.
    assert geo.is_in_water(48.55, -123.20) is True
    # An island interior point is not water.
    assert geo.is_in_water(48.53, -123.08) is False


def test_snap_to_water_moves_land_point_to_water():
    # A shoreline land point near Lime Kiln Point.
    land_lat, land_lng = 48.516, -123.15
    assert geo.is_on_land(land_lat, land_lng) is True

    snapped_lat, snapped_lng = geo.snap_to_water(land_lat, land_lng)
    assert geo.is_in_water(snapped_lat, snapped_lng) is True
    # The snap should not have moved the point out of the region.
    assert geo.in_bounds(snapped_lat, snapped_lng) is True


def test_snap_to_water_leaves_water_point_unchanged():
    lat, lng = 48.55, -123.20
    assert geo.snap_to_water(lat, lng) == (lat, lng)


def test_filter_and_snap_drops_out_of_bounds():
    assert geo.filter_and_snap(47.35, -122.32) is None


def test_filter_and_snap_returns_water_for_in_region_land():
    result = geo.filter_and_snap(48.516, -123.15)
    assert result is not None
    assert geo.is_in_water(*result) is True


def test_bounds_constant_shape():
    assert SAN_JUAN_BOUNDS.min_lat == 48.40
    assert SAN_JUAN_BOUNDS.max_lat == 48.70
    assert SAN_JUAN_BOUNDS.min_lng == -123.25
    assert SAN_JUAN_BOUNDS.max_lng == -122.75
