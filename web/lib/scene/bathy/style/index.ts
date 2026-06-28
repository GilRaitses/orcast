// web/lib/scene/bathy/style
//
// MODELED, NOT MEASURED. The Water and Depth Stylist surface for WS-BATHY: a
// submerged-seabed depth tint over the modeled CUDEM topobathy, on the
// perceptually-uniform cmocean `deep` palette, plus the proposed depth-driven
// water tuning. Pure module: it builds objects and option sets and exposes an
// apply/dispose handle. It mounts nothing; the SalishScene phase-B editor mounts
// it. It edits no water2 or substrate internals (the per-channel absorption
// upgrade is a request, see WATER2_TUNING_REQUEST.md).
//
// See WIRING-bathy-style.md for the integrator-facing contract.

export {
  DEEP_RAMP_STOPS,
  DEEP_RAMP_SHALLOW,
  DEEP_RAMP_DEEP,
  DEEP_RAMP_SHALLOW_HEX,
  DEEP_RAMP_DEEP_HEX,
  LAND_TINT_HEX,
  BATHY_TINT_LABEL,
  sampleDeepRamp,
  type RampStop,
} from "./deepRamp";

export {
  bathyOverlayOptions,
  buildBathyTint,
  type BathyTintOptions,
  type BathyTintHandle,
} from "./bathyTint";

export {
  bathyWater2Options,
  PROPOSED_RGB_EXTINCTION,
  WATER_TUNED_SHALLOW,
  WATER_TUNED_DEEP,
  WATER_TUNED_FOAM,
  WATER_TUNED_SKY,
  type BathyWaterTuningOverrides,
} from "./waterTuning";
