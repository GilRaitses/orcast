// Submerged-seabed bathymetric depth tint (WS-BATHY, Water and Depth Stylist).
//
// MODELED, NOT MEASURED. This tint STYLES the modeled CUDEM topobathy seabed
// that the tiles already render and the substrate field already rasterizes. It
// authors no geometry and reads no measured source. The honesty label travels
// with the produced object (userData + name), mirroring SUBSTRATE_LABEL.
//
// Reuse, not re-implementation: the tint is built ON TOP of substrate's public
// `buildSubstrateOverlay`, which owns the point positions, the projector seam,
// the material, and the base honesty tags. This module retunes that overlay to
// the perceptually-uniform cmocean `deep` palette by overwriting the per-vertex
// color buffer of the object RETURNED to it. It does not touch substrate or
// water2 internals.
//
// Why overwrite colors rather than only pass colorDeep/colorShore/colorHigh:
// buildSubstrateOverlay interpolates LINEARLY between two endpoints per segment,
// which would skip the green/teal/cyan midtones that make cmocean `deep`
// perceptually uniform and would read as a muddy gray midtone. Sampling the full
// ramp per point keeps the submerged half perceptually uniform while still
// reusing the overlay for everything else.
//
// Pure module: `buildBathyTint` allocates an object and returns an apply/dispose
// handle. It mutates no scene until `apply(parent)` is called. The SalishScene
// phase-B editor owns the mount; this module owns only the object's lifecycle.

import * as THREE from "three";

import {
  buildSubstrateOverlay,
  SUBSTRATE_LABEL,
  type SubstrateField,
  type SubstrateOverlayOptions,
} from "../../substrate";
import {
  DEEP_RAMP_DEEP_HEX,
  DEEP_RAMP_SHALLOW_HEX,
  LAND_TINT_HEX,
  sampleDeepRamp,
} from "./deepRamp";

export interface BathyTintOptions {
  /**
   * Map a field point into the live tile frame. Pass the WS-BATHY `field`
   * projector (producer A2) so the tint aligns with the rendered terrain. When
   * omitted the overlay's default `sceneIntent` layout is used, which will NOT
   * line up with the runtime tile group (see WIRING-substrate.md).
   */
  project?: (lat: number, lng: number, depthM: number) => [number, number, number];
  /** Point size passed through to the overlay. Default 0.6. */
  pointSize?: number;
  /** Material opacity in [0,1]. Default 0.85. */
  opacity?: number;
  /** Size relative to camera distance. Default false. */
  sizeAttenuation?: boolean;
  /**
   * Override the depth extent the ramp is mapped over. Defaults to the field's
   * own `minDepthM` (deepest seabed -> deep endpoint) and `maxDepthM` (highest
   * land -> land tint). Sea level (0 m) is always the shallow endpoint.
   */
  minDepthM?: number;
  maxDepthM?: number;
}

export interface BathyTintHandle {
  /** The renderable depth-tinted point object. Honesty-tagged via userData. */
  object: THREE.Object3D;
  /** Add the object to `parent`. Idempotent re-parent if already applied. */
  apply(parent: THREE.Object3D): void;
  /** Remove from its parent and free GPU resources. Safe to call repeatedly. */
  dispose(): void;
}

const DEFAULTS = {
  pointSize: 0.6,
  opacity: 0.85,
  sizeAttenuation: false,
};

/**
 * The tuned `SubstrateOverlayOptions` set for the cmocean `deep` bathymetric
 * tint, addressed to `buildSubstrateOverlay`. The endpoints are the deep-ramp
 * shallow/deep colors plus a muted land tint; `buildBathyTint` additionally
 * overwrites the midtones with the full perceptual ramp. Returned standalone so
 * the phase-B editor (or a fixture) can read the ramp choice without building an
 * object.
 */
export function bathyOverlayOptions(opts: BathyTintOptions = {}): SubstrateOverlayOptions {
  return {
    project: opts.project,
    pointSize: opts.pointSize ?? DEFAULTS.pointSize,
    opacity: opts.opacity ?? DEFAULTS.opacity,
    sizeAttenuation: opts.sizeAttenuation ?? DEFAULTS.sizeAttenuation,
    colorDeep: DEEP_RAMP_DEEP_HEX,
    colorShore: DEEP_RAMP_SHALLOW_HEX,
    colorHigh: LAND_TINT_HEX,
  };
}

/**
 * Build the submerged-seabed depth tint over the modeled substrate field.
 *
 * Color mapping (depth_m is negative below sea level, positive on land):
 *  - submerged (depth_m < 0): the cmocean `deep` ramp over [0, |minDepthM|], so
 *    0 m -> shallow endpoint and the deepest seabed -> deep endpoint.
 *  - above water (depth_m > 0): a fade from the shallow endpoint to the muted
 *    land tint over [0, maxDepthM], set dressing for the optional point layer.
 *
 * The relief lighting is supplied by the live scene's sun (RealismRig) acting on
 * the already-shaded tile mesh beneath the points; this tint reads as the
 * translucent depth wash filling the lows over that relief.
 */
export function buildBathyTint(
  field: SubstrateField,
  opts: BathyTintOptions = {},
): BathyTintHandle {
  const object = buildSubstrateOverlay(field, bathyOverlayOptions(opts));

  // Re-tint the per-vertex colors with the full perceptual ramp. Indices match
  // field.points order (buildSubstrateOverlay iterates the same array).
  const points = object as THREE.Points;
  const geometry = points.geometry as THREE.BufferGeometry;
  const colorAttr = geometry.getAttribute("color") as THREE.BufferAttribute | undefined;

  const minD = opts.minDepthM ?? field.minDepthM;
  const maxD = opts.maxDepthM ?? field.maxDepthM;
  if (colorAttr && colorAttr.count === field.points.length) {
    const c = new THREE.Color();
    const landShallow = new THREE.Color(DEEP_RAMP_SHALLOW_HEX);
    const landHigh = new THREE.Color(LAND_TINT_HEX);
    for (let i = 0; i < field.points.length; i++) {
      const d = field.points[i].depth_m;
      if (d < 0 && minD < 0) {
        // 0 at sea level, 1 at the deepest modeled seabed.
        const sub = Math.max(0, Math.min(1, d / minD));
        const [r, g, b] = sampleDeepRamp(sub);
        c.setRGB(r, g, b, THREE.SRGBColorSpace);
      } else if (d > 0 && maxD > 0) {
        const tl = Math.max(0, Math.min(1, d / maxD));
        c.copy(landShallow).lerp(landHigh, tl);
      } else {
        c.copy(landShallow);
      }
      colorAttr.setXYZ(i, c.r, c.g, c.b);
    }
    colorAttr.needsUpdate = true;
  }

  // Carry the honesty label and the ramp provenance. Keep the substrate honesty
  // tags intact; add the bathy-tint markers on top.
  object.name = `bathy-tint (${SUBSTRATE_LABEL})`;
  object.userData.modeledNotMeasured = true;
  object.userData.label = SUBSTRATE_LABEL;
  object.userData.bathyTint = true;
  object.userData.ramp = "cmocean deep (perceptually uniform)";
  object.userData.minDepthM = minD;
  object.userData.maxDepthM = maxD;

  let mounted: THREE.Object3D | null = null;
  let disposed = false;

  return {
    object,
    apply(parent: THREE.Object3D) {
      if (disposed) return;
      if (mounted && mounted !== parent) {
        mounted.remove(object);
      }
      parent.add(object);
      mounted = parent;
    },
    dispose() {
      if (disposed) return;
      disposed = true;
      if (mounted) {
        mounted.remove(object);
        mounted = null;
      }
      geometry.dispose();
      const material = points.material;
      if (Array.isArray(material)) {
        for (const m of material) m.dispose();
      } else {
        material.dispose();
      }
    },
  };
}
