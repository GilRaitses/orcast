// Depth-driven water tuning for the WS-BATHY seabed read (Water and Depth
// Stylist). Produces the proposed `Water2Options` set that the phase-B editor
// applies to the existing `Water2Rig` construction so the water color and alpha
// read truthfully over the modeled CUDEM seabed: shoals light and translucent,
// channels dark and opaque, the deep Haro Strait channel deepest.
//
// HONESTY. The water is physics and atmosphere over a MODELED seabed, not a
// survey. Foam, Fresnel sky reflection, and sun glitter are rendering, not
// soundings. The color/alpha attenuation reads the seabed depth that the tiles
// already carry; it asserts no measured depth.
//
// SCOPE. This module only PROPOSES option values. It does not edit water2
// internals (`depthWater.ts`). The single-scalar -> per-channel RGB absorption
// upgrade, which would shift deep water toward blue/purple by physics rather
// than by a two-stop lerp, is a REQUEST to the water2 owner; see
// WATER2_TUNING_REQUEST.md and PROPOSED_RGB_EXTINCTION below.

import * as THREE from "three";

import type { Water2Options } from "../../water2";

/**
 * Tuned shallow water tint: a believable bright teal-green for shoals, lighter
 * than the water2 default (#2e6f9e) so thin water over shallows reads as living
 * coastal water rather than washed navy. Pairs with the cmocean `deep` seabed
 * shallow endpoint.
 */
export const WATER_TUNED_SHALLOW = "#2f8fa6";

/**
 * Tuned deep water tint: a navy leaning slightly cool/violet toward the cmocean
 * `deep` deep endpoint, so the deepest channels read dark blue-purple under the
 * two-stop lerp until the per-channel absorption upgrade lands.
 */
export const WATER_TUNED_DEEP = "#0b2140";

/** Foam color near the shoreline; near-white marine spray. */
export const WATER_TUNED_FOAM = "#dfeef5";

/** Sky/horizon color the Fresnel term reflects toward; marine haze. */
export const WATER_TUNED_SKY = "#9fc4e0";

/**
 * Proposed per-channel RGB extinction coefficients for the requested water2
 * absorption upgrade, in inverse scene units (column thickness). Red is absorbed
 * fastest, blue slowest, so transmitted color shifts blue-green -> navy with
 * depth by physics. These are a starting point for the water2 owner to tune in
 * the /water sandbox against the full-extent tileset; they are NOT applied here.
 *
 * Mapping note: the deep Haro Strait channel runs about 1.0 scene units below
 * the surface in the live tile frame (water2 default-tuning comment), so a
 * coefficient near 3.0 takes the red channel to ~95% extinction over that
 * column while blue retains ~70%, producing the deep navy/violet read.
 */
export const PROPOSED_RGB_EXTINCTION: { r: number; g: number; b: number } = {
  r: 3.0,
  g: 1.6,
  b: 0.9,
};

export interface BathyWaterTuningOverrides {
  /** Optional sun direction from the realism rig (makeSun().direction). */
  sunDirection?: THREE.Vector3;
  /** Override the plane width (scene units) the editor computes. */
  width?: number;
  /** Override the plane depth (scene units) the editor computes. */
  depth?: number;
}

/**
 * The proposed `Water2Options` tuning set for the bathymetric depth read. The
 * editor merges these into its existing `makeWater2` construction, then passes
 * its own `width`/`depth`/`level`/`sunDirection` from the scene. Anything the
 * editor already computes (plane size, sun) is left to the override argument so
 * this set never overrides the live frame by accident.
 *
 * Scale rationale (live tile frame, deepest channel ~1.0 scene units below
 * surface, water2 default-tuning comment):
 *  - depthColorScale 0.42: shoals (~0.1 units) read light teal (colorT ~0.21);
 *    the deep channel (~1.0 units) reaches the deep tint (colorT ~0.91).
 *  - depthAlphaScale 0.34: thin water over shoals stays clear enough to reveal
 *    the seabed tint; the deep channel goes near-opaque.
 *  - maxOpacity 0.95: the deepest channel stays just shy of fully opaque so the
 *    seabed tint still hints through and the surface is not a flat black.
 *  - foamDepth 0.06: a thin shoreline band, no broad foam wash.
 *  - fresnelStrength 0.45: a touch under the default so the depth read is not
 *    overwhelmed by sky reflection at grazing angles.
 */
export function bathyWater2Options(overrides: BathyWaterTuningOverrides = {}): Water2Options {
  return {
    colorShallow: new THREE.Color(WATER_TUNED_SHALLOW),
    colorDeep: new THREE.Color(WATER_TUNED_DEEP),
    colorFoam: new THREE.Color(WATER_TUNED_FOAM),
    skyColor: new THREE.Color(WATER_TUNED_SKY),
    depthColorScale: 0.42,
    depthAlphaScale: 0.34,
    foamDepth: 0.06,
    maxOpacity: 0.95,
    fresnelStrength: 0.45,
    amplitude: 0.3,
    speed: 1,
    ...(overrides.sunDirection ? { sunDirection: overrides.sunDirection } : {}),
    ...(overrides.width !== undefined ? { width: overrides.width } : {}),
    ...(overrides.depth !== undefined ? { depth: overrides.depth } : {}),
  };
}
