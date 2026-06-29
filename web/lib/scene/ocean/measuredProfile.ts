// Measured CTD stratification profile, baked offline from one CC0 CruiseSalish
// cast (NCEI Accession 0307188) into a small JSON by
// infra/ocean/bake_ctd_profile.py. See infra/ocean/PROVENANCE.md.
//
// HONESTY. The cast supplies depth, temperature, and salinity only, and it is a
// nearby-analog cast from the eastern Strait of Juan de Fuca, not an on-site San
// Juan Channel station. The render layer that consumes this profile is
// interpretive, not a map of measured microstructure and not a depiction of how
// an animal senses its surroundings. This module performs NO bake of its own: it
// returns a plain StratificationProfile and lets createDoubleDiffusionLayer call
// the shared stratificationToTexture so the per-profile normalization stays
// identical to the analytic path. The provenance string is guarded by
// assertNoForbiddenClaim inside createDoubleDiffusionLayer, the same path the
// analytic profile travels.

import type { StratificationProfile, StratificationOrigin } from "./stratification";
import baked from "./measured_cruisesalish_profile.json";

/**
 * Return the baked measured CTD profile, typed exactly like
 * analyticHaloclineProfile's return so it drops into
 * createDoubleDiffusionLayer({ profile }) with no other change.
 */
export function measuredHaloclineProfile(): StratificationProfile {
  return {
    origin: baked.origin as StratificationOrigin,
    provenance: baked.provenance,
    maxDepthM: baked.maxDepthM,
    samples: baked.samples.map((s) => ({
      depthM: s.depthM,
      temperatureC: s.temperatureC,
      salinityPsu: s.salinityPsu,
    })),
  };
}
