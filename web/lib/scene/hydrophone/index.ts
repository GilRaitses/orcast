// web/lib/scene/hydrophone
//
// Parametric hydrophone-equipment rig (MODELED), modeled-seabed placement, a
// WebAudio player bound to the one real archived clip (MEASURED), and a camera
// POV selector that drives the existing Camera Director. Built on `three` +
// WebAudio only. See WIRING.md for the integrator contract.

export {
  makeHydrophoneRig,
  type HydrophoneRig,
  type HydrophoneRigOptions,
} from "./makeHydrophoneRig";

export {
  stationSeabedPose,
  resolveSeabedDepthM,
  type StationSeabedOptions,
} from "./placement";

export {
  StationPlayer,
  type StationPlayerOptions,
  type StationPlayerStatus,
} from "./StationPlayer";

export {
  runStationPOV,
  type StationPov,
  type StationGeo,
  type StationPovContext,
  type StationPovHandle,
} from "./stationCamera";
