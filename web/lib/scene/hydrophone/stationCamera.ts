import type { CameraDirector, OrbitHandle } from "@/lib/scene/camera/types";

// Station POV selection driven entirely through the Camera Director API.
//
// This NEVER touches `camera.position` directly: it only calls `flyTo`,
// `descendTo`, and `orbit` on the director the scene owns and advances each
// frame. Two points of view:
//   - "hydrophone": eye just above the seabed node, looking up toward the
//     surface (altitude = seabedDepthM + 1.5 m).
//   - "topdown": a high station overview at 180 m, with an optional slow orbit.

export type StationPov = "hydrophone" | "topdown";

export interface StationGeo {
  lat: number;
  lng: number;
  /** Modeled seabed depth in metres (negative below sea level). */
  seabedDepthM: number;
}

export interface StationPovContext {
  /** Start a slow top-down orbit after the fly-in. Default false. */
  orbit?: boolean;
  /** Top-down orbit radius in scene units. Default 60. */
  orbitRadius?: number;
  /** Top-down orbit angular speed (rad/s). Default 0.03. */
  orbitSpeed?: number;
  /** Override the fly-in duration in ms. */
  durationMs?: number;
}

export interface StationPovHandle {
  pov: StationPov;
  /** Stop any orbit and pending motion this POV started. */
  stop(): void;
}

const HYDROPHONE_EYE_ABOVE_NODE_M = 1.5;
const TOPDOWN_ALTITUDE_M = 180;
const TOPDOWN_ORBIT_RADIUS = 60;
const TOPDOWN_ORBIT_SPEED = 0.03;

/**
 * Drive the director to a station POV. Returns a small handle whose `stop()`
 * ends any orbit it began.
 */
export function runStationPOV(
  pov: StationPov,
  station: StationGeo,
  director: CameraDirector,
  ctx: StationPovContext = {},
): StationPovHandle {
  director.stop();

  if (pov === "hydrophone") {
    void director.flyTo(
      {
        lat: station.lat,
        lng: station.lng,
        altitudeMeters: station.seabedDepthM + HYDROPHONE_EYE_ABOVE_NODE_M,
      },
      { durationMs: ctx.durationMs ?? 2500, subject: "hydrophone node" },
    );
    return {
      pov,
      stop() {
        director.stop();
      },
    };
  }

  // top-down: fly up to the overview altitude, then optionally orbit slowly.
  let orbitHandle: OrbitHandle | null = null;
  const flyDone = director.flyTo(
    { lat: station.lat, lng: station.lng, altitudeMeters: TOPDOWN_ALTITUDE_M },
    { durationMs: ctx.durationMs ?? 2500, subject: "station top-down" },
  );
  if (ctx.orbit) {
    void flyDone.then(() => {
      orbitHandle = director.orbit(
        { lat: station.lat, lng: station.lng },
        ctx.orbitRadius ?? TOPDOWN_ORBIT_RADIUS,
        ctx.orbitSpeed ?? TOPDOWN_ORBIT_SPEED,
        { altitudeMeters: TOPDOWN_ALTITUDE_M, subject: "station top-down" },
      );
    });
  }

  return {
    pov,
    stop() {
      orbitHandle?.stop();
      director.stop();
    },
  };
}
