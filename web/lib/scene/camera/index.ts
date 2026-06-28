// Camera Director barrel (W1 Agent A). Public surface for the cinematic camera
// program. The scene (W2) imports `createCameraDirector` and the handle/types.

export { createCameraDirector } from "./director";
export { EASINGS, resolveEasing } from "./easing";
export type {
  CameraDirector,
  CameraDirectorHandle,
  CameraState,
  ControlsLike,
  EasingFn,
  EasingName,
  FollowPathOptions,
  LatLng,
  LatLngAlt,
  MoveOptions,
  OrbitHandle,
  OrbitOptions,
} from "./types";
