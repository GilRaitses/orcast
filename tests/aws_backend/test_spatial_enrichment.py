from src.aws_backend.geo_region import nearest_shore_m
from src.aws_backend.spatial_enrichment import build_grid_cells, cell_id_for, lookup_cell


def test_build_grid_cells_include_depth_and_shoreline():
    cells = build_grid_cells(step_degrees=0.1)
    assert cells
    sample = cells[0]
    assert sample["cell_id"] == cell_id_for(sample["lat"], sample["lng"])
    assert sample["inside_land"] is False
    assert sample.get("depth_m") is not None or sample.get("depth_m") is None
    assert sample.get("nearest_shore_m") is not None


def test_lookup_cell_matches_grid_id():
    cells = build_grid_cells(step_degrees=0.1)
    target = cells[0]
    found = lookup_cell(target["lat"], target["lng"], cells=cells)
    assert found["cell_id"] == target["cell_id"]


def test_nearest_shore_m_zero_on_land():
    assert nearest_shore_m(48.53, -123.08) == 0.0
