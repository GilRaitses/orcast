// Public surface of the depth-driven water module (water2, mini-wave W2.5).
//
// Depth-driven ocean: alpha and color vary with the water-column thickness at
// each fragment (Beer-Lambert), read from the opaque scene depth buffer, so
// shallows and dry land reveal terrain instead of being washed by a flat blue
// plane. See depthWater.ts for the technique and research/R4_ocean_water_rendering.md.

export { makeWater2 } from "./depthWater";
export type { Water2Options, Water2Handle } from "./depthWater";
