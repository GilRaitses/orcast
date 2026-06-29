// web/lib/scene/hydrophone/equipment
//
// MODELED, low-poly equipment variants per node class (cabled shore hydrophone
// vs subsurface mooring). All parametric `three` geometry built in-repo; no
// external mesh, no new runtime dependency. Each variant returns
// `{ root, dispose }` with the root's local origin at the seabed and an
// honesty marker in `userData`.

export { makeStationEquipment } from "./makeStationEquipment";
export {
  makeMooringHydrophone,
  type MooringHydrophoneOptions,
} from "./makeMooringHydrophone";
export type {
  EquipmentRig,
  EquipmentVariantOptions,
  HydrophoneNodeClass,
} from "./types";
