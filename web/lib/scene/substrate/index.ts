// web/lib/scene/substrate
//
// MODELED, NOT MEASURED. Makes agent F's modeled CUDEM depth field
// (NOAA NCEI CUDEM 1/9 arc-second topobathy) sampleable in the live scene.
// `depth_m` is negative below sea level and positive on land, mirroring the
// Python BathymetryAdapter (src/aws_backend/sources/bathymetry.py).
//
// See WIRING-substrate.md for the integrator-facing contract.

export type {
  SubstrateBounds,
  SubstrateField,
  SubstratePoint,
} from "./types";

export {
  loadSubstrate,
  SUBSTRATE_URL,
  SUBSTRATE_LABEL,
} from "./loadSubstrate";

export { sampleSubstrate } from "./sampleSubstrate";

export {
  buildSubstrateOverlay,
  type SubstrateOverlayOptions,
} from "./buildSubstrateOverlay";
