import type { SubstrateField } from "./types";

/**
 * Nearest-neighbour depth (metres) at a lat/lng.
 *
 * MODELED, NOT MEASURED. Faithful mirror of `BathymetryAdapter.depth_at`
 * (src/aws_backend/sources/bathymetry.py): nearest grid point by simple
 * equirectangular distance, with longitude scaled by cos(lat). Accurate at this
 * latitude and extent. Returns the depth of the nearest point in `field.points`
 * (negative below sea level, positive on land).
 *
 * Returns `NaN` if the field has no points or the query is non-finite, so the
 * caller can distinguish "no data" from a real 0 m (sea-level) reading.
 */
export function sampleSubstrate(field: SubstrateField, lat: number, lng: number): number {
  const points = field.points;
  if (!points || points.length === 0) return NaN;
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return NaN;

  const cosLat = Math.cos((lat * Math.PI) / 180);
  let bestDepth = NaN;
  let bestDist = Infinity;
  for (let i = 0; i < points.length; i++) {
    const p = points[i];
    const dLat = p.lat - lat;
    const dLng = (p.lng - lng) * cosLat;
    const dist = dLat * dLat + dLng * dLng;
    if (dist < bestDist) {
      bestDist = dist;
      bestDepth = p.depth_m;
    }
  }
  return bestDepth;
}
