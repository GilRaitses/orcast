/**
 * San Juan archipelago geo helpers: region bounding, land/water testing,
 * and snap-to-water. Pure functions, no Angular DI, tree-shakable.
 *
 * Keeps orca markers on water and inside the pilot region. See
 * docs/ux/MAP_DATA_TRUTH.md for the rules these implement.
 */

import { LatLng, LAND_POLYGONS, SAN_JUAN_BOUNDS } from './geo-region.data';

export { SAN_JUAN_BOUNDS } from './geo-region.data';
export type { LatLng } from './geo-region.data';

/** True when a point is inside the archipelago bounding box. */
export function inBounds(lat: number, lng: number): boolean {
  return (
    Number.isFinite(lat) &&
    Number.isFinite(lng) &&
    lat >= SAN_JUAN_BOUNDS.minLat &&
    lat <= SAN_JUAN_BOUNDS.maxLat &&
    lng >= SAN_JUAN_BOUNDS.minLng &&
    lng <= SAN_JUAN_BOUNDS.maxLng
  );
}

/** Ray-casting point-in-polygon over a single [lng,lat] ring. */
function pointInRing(lat: number, lng: number, ring: number[][]): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][0];
    const yi = ring[i][1];
    const xj = ring[j][0];
    const yj = ring[j][1];
    const intersects =
      yi > lat !== yj > lat &&
      lng < ((xj - xi) * (lat - yi)) / (yj - yi || Number.EPSILON) + xi;
    if (intersects) {
      inside = !inside;
    }
  }
  return inside;
}

/** True when a point falls on one of the approximate island landmasses. */
export function isOnLand(lat: number, lng: number): boolean {
  for (const ring of Object.values(LAND_POLYGONS)) {
    if (pointInRing(lat, lng, ring)) {
      return true;
    }
  }
  return false;
}

/** True when a point is in the region and not on land. */
export function isInWater(lat: number, lng: number): boolean {
  return inBounds(lat, lng) && !isOnLand(lat, lng);
}

/**
 * If the point is on water, return it unchanged. If it is on land (a shoreline
 * sighting coordinate), nudge to the nearest in-water point by sampling
 * expanding rings. Falls back to the original point if nothing is found.
 */
export function snapToWater(lat: number, lng: number): LatLng {
  if (isInWater(lat, lng)) {
    return { lat, lng };
  }

  const stepDeg = 0.005; // ~0.5 km
  const maxRings = 12; // up to ~6 km out
  const directions = 16;

  for (let ring = 1; ring <= maxRings; ring++) {
    const radius = stepDeg * ring;
    let best: { point: LatLng; dist: number } | null = null;
    for (let d = 0; d < directions; d++) {
      const angle = (2 * Math.PI * d) / directions;
      const candLat = lat + radius * Math.cos(angle);
      const candLng = lng + (radius * Math.sin(angle)) / Math.cos((lat * Math.PI) / 180);
      if (isInWater(candLat, candLng)) {
        const dist = distanceKm({ lat, lng }, { lat: candLat, lng: candLng });
        if (!best || dist < best.dist) {
          best = { point: { lat: candLat, lng: candLng }, dist };
        }
      }
    }
    if (best) {
      return best.point;
    }
  }

  return { lat, lng };
}

/** Great-circle distance in kilometers. */
export function distanceKm(a: LatLng, b: LatLng): number {
  const R = 6371;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLng = ((b.lng - a.lng) * Math.PI) / 180;
  const lat1 = (a.lat * Math.PI) / 180;
  const lat2 = (b.lat * Math.PI) / 180;
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}
