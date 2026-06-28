import type { SubstrateBounds, SubstrateField, SubstratePoint } from "./types";

// Runtime fetch of the modeled CUDEM depth field. The asset is copied verbatim
// to web/public/geo/ (served at /geo/...) rather than imported, so it stays out
// of the JS bundle and can be swapped without a rebuild. See WIRING-substrate.md.
export const SUBSTRATE_URL = "/geo/sample_san_juan_bathymetry_cudem.json";

/** Human-facing honesty label. Attach to any UI string that surfaces substrate values. */
export const SUBSTRATE_LABEL = "modeled, not measured";

interface RawSubstrate {
  source?: unknown;
  dataset?: unknown;
  bounds?: Partial<SubstrateBounds>;
  resolution_deg?: unknown;
  provenance?: unknown;
  points?: unknown;
}

function toNumber(value: unknown, fallback = NaN): number {
  const n = typeof value === "string" ? Number(value) : (value as number);
  return typeof n === "number" && Number.isFinite(n) ? n : fallback;
}

function parsePoints(raw: unknown): SubstratePoint[] {
  if (!Array.isArray(raw)) return [];
  const points: SubstratePoint[] = [];
  for (const item of raw) {
    if (!item || typeof item !== "object") continue;
    const rec = item as Record<string, unknown>;
    const lat = toNumber(rec.lat);
    const lng = toNumber(rec.lng);
    const depth_m = toNumber(rec.depth_m);
    if (Number.isFinite(lat) && Number.isFinite(lng) && Number.isFinite(depth_m)) {
      points.push({ lat, lng, depth_m });
    }
  }
  return points;
}

/**
 * Fetch and parse the modeled CUDEM depth field into a typed `SubstrateField`.
 *
 * MODELED, NOT MEASURED. Mirrors the schema read by `BathymetryAdapter`
 * (src/aws_backend/sources/bathymetry.py): {source, dataset, bounds,
 * resolution_deg, points:[{lat,lng,depth_m}]}. `depth_m` is negative below sea
 * level and positive on land.
 *
 * Rejects if the asset is missing or contains no usable points.
 */
export async function loadSubstrate(url: string = SUBSTRATE_URL): Promise<SubstrateField> {
  const res = await fetch(url, { cache: "force-cache" });
  if (!res.ok) {
    throw new Error(`loadSubstrate: failed to fetch ${url} (${res.status} ${res.statusText})`);
  }
  const data = (await res.json()) as RawSubstrate;

  const points = parsePoints(data.points);
  if (points.length === 0) {
    throw new Error(`loadSubstrate: asset at ${url} contained no usable points`);
  }

  const bounds: SubstrateBounds = {
    min_lat: toNumber(data.bounds?.min_lat),
    max_lat: toNumber(data.bounds?.max_lat),
    min_lng: toNumber(data.bounds?.min_lng),
    max_lng: toNumber(data.bounds?.max_lng),
  };

  let minDepthM = Infinity;
  let maxDepthM = -Infinity;
  for (const p of points) {
    if (p.depth_m < minDepthM) minDepthM = p.depth_m;
    if (p.depth_m > maxDepthM) maxDepthM = p.depth_m;
  }

  return {
    source: typeof data.source === "string" ? data.source : "",
    dataset: typeof data.dataset === "string" ? data.dataset : "",
    bounds,
    resolution_deg: toNumber(data.resolution_deg, 0),
    provenance: typeof data.provenance === "string" ? data.provenance : SUBSTRATE_LABEL,
    modeledNotMeasured: true,
    points,
    minDepthM,
    maxDepthM,
  };
}
