// Typed view of agent F's modeled CUDEM depth field.
//
// MODELED, NOT MEASURED. The depth field is rasterized from the NOAA NCEI
// CUDEM 1/9 arc-second topobathy surface (the same geometry that feeds the 3D
// render tiles), aggregated to a regular lat/lng grid. `depth_m` is NEGATIVE
// below sea level and POSITIVE on land, matching the Python BathymetryAdapter
// (src/aws_backend/sources/bathymetry.py) sign convention.

export interface SubstrateBounds {
  min_lat: number;
  max_lat: number;
  min_lng: number;
  max_lng: number;
}

export interface SubstratePoint {
  lat: number;
  lng: number;
  /** Metres. Negative below sea level (water), positive on land. */
  depth_m: number;
}

export interface SubstrateField {
  source: string;
  dataset: string;
  bounds: SubstrateBounds;
  resolution_deg: number;
  /** Full provenance string from the source asset. */
  provenance: string;
  /** Always true: this field is derived/modeled, not an in-situ measurement. */
  modeledNotMeasured: true;
  points: SubstratePoint[];
  /** Derived extents over `points`, computed once at load time. */
  minDepthM: number;
  maxDepthM: number;
}
