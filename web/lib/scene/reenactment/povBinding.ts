// Camera POV binding for the reenactment. This REUSES BST's POV-selection object
// (runStationPOV from web/lib/scene/hydrophone) which itself drives only the
// shared Camera Director (web/lib/scene/camera/director.ts). BRE never touches
// camera.position directly and never bypasses the director's surface/altitude
// clamps; it only chooses a POV and hands the station geometry through.
//
// Two points of view, identical to the station lane:
//   - "hydrophone": eye just above the seabed node, looking up the water column.
//   - "topdown": a high station overview, optional slow orbit.

import type { CameraDirector } from "@/lib/scene/camera/types";
import {
  runStationPOV,
  type StationGeo,
  type StationPov,
  type StationPovContext,
  type StationPovHandle,
} from "@/lib/scene/hydrophone";

export type ReenactmentPov = StationPov;

/** Human-readable labels for a POV chip. */
export const REENACTMENT_POV_LABELS: Record<ReenactmentPov, string> = {
  hydrophone: "Hydrophone POV",
  topdown: "Top-down",
};

/**
 * Drive the shared Camera Director to a reenactment POV via BST's selector.
 * Returns BST's handle whose `stop()` ends any orbit it began.
 */
export function bindReenactmentPov(
  director: CameraDirector,
  station: StationGeo,
  pov: ReenactmentPov,
  ctx: StationPovContext = {},
): StationPovHandle {
  return runStationPOV(pov, station, director, ctx);
}

export type { StationGeo, StationPov, StationPovContext, StationPovHandle };
