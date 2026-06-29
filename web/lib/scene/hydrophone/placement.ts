import { projectToScene, type HeightmapBounds } from "@/lib/sceneIntent";
import { sampleSubstrate, type SubstrateField } from "@/lib/scene/substrate";

// Seabed placement for a station rig.
//
// Horizontal scene XZ reuses `projectToScene` verbatim (never a copy) so the rig
// lines up with the same frame the camera director and terrain use. Vertical Y
// is the modeled seabed:
//   1. If a modeled substrate field is given, sample it (negative metres below
//      sea level) and convert with Y = depth_m * worldUnitsPerMeter.
//   2. Else if a downward-raycast `getSurfaceY(x,z)` probe is given, use it.
//   3. Else fall back to a fixed modeled depth (Orcasound Lab is shallow, ~5-30
//      m per the catalog; default -18 m).
//
// The rig sits ON the seabed, so Y is NEVER clamped to Math.max(y, 0) (that
// would float it at the surface).

const DEFAULT_FALLBACK_DEPTH_M = -18;

export interface StationSeabedOptions {
  /** Modeled CUDEM depth field. Sampled first when present. */
  substrate?: SubstrateField | null;
  /**
   * Optional downward-raycast probe: scene-world X/Z to seabed Y, or null on a
   * miss. Used when no substrate field is available.
   */
  getSurfaceY?: ((x: number, z: number) => number | null) | null;
  /** World units per metre for the vertical mapping. Default 1. */
  worldUnitsPerMeter?: number;
  /** Fixed modeled seabed depth (negative metres) used as the last resort. */
  fallbackDepthM?: number;
}

/**
 * Resolve the modeled seabed depth in metres (negative below sea level) at a
 * lat/lng, following the substrate -> raycast -> fixed-fallback precedence.
 * The raycast branch returns the fallback depth too, since a raycast yields a
 * world Y rather than a metric depth; the pose helper uses the raycast Y
 * directly for the vertical placement.
 */
export function resolveSeabedDepthM(lat: number, lng: number, opts: StationSeabedOptions = {}): number {
  if (opts.substrate) {
    const d = sampleSubstrate(opts.substrate, lat, lng);
    if (Number.isFinite(d)) return d;
  }
  return typeof opts.fallbackDepthM === "number" ? opts.fallbackDepthM : DEFAULT_FALLBACK_DEPTH_M;
}

/**
 * Scene-space `[x, y, z]` for a station rig root sitting on the modeled seabed.
 */
export function stationSeabedPose(
  lat: number,
  lng: number,
  bounds: HeightmapBounds,
  sceneDepth: number,
  opts: StationSeabedOptions = {},
): [number, number, number] {
  const [x, z] = projectToScene(lat, lng, bounds, sceneDepth);
  const wupm = opts.worldUnitsPerMeter && opts.worldUnitsPerMeter > 0 ? opts.worldUnitsPerMeter : 1;

  // 1. Modeled substrate field wins when it has a finite reading here.
  if (opts.substrate) {
    const d = sampleSubstrate(opts.substrate, lat, lng);
    if (Number.isFinite(d)) {
      return [x, d * wupm, z];
    }
  }

  // 2. Downward-raycast probe (e.g. into a seabed mesh) when no substrate.
  if (opts.getSurfaceY) {
    const probed = opts.getSurfaceY(x, z);
    if (typeof probed === "number" && Number.isFinite(probed)) {
      return [x, probed, z];
    }
  }

  // 3. Fixed modeled seabed depth. Negative metres -> below sea level.
  const fallbackDepthM =
    typeof opts.fallbackDepthM === "number" ? opts.fallbackDepthM : DEFAULT_FALLBACK_DEPTH_M;
  return [x, fallbackDepthM * wupm, z];
}
