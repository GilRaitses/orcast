import type { CameraDirector } from "@/lib/scene/camera/types";
import {
  runStationPOV,
  type StationGeo,
  type StationPov,
  type StationPovContext,
  type StationPovHandle,
} from "./stationCamera";

// The reusable camera POV-selection object.
//
// This is the durable piece the integrator mounts (not a one-off sandbox
// toggle): a small, framework-agnostic controller that owns the set of named
// points of view and switches between them by driving the shared Camera
// Director ONLY (via `runStationPOV` -> `flyTo`/`orbit`). It never touches
// `camera.position` and never bypasses the director's surface/altitude clamps.
//
// >= 2 named POVs are required by the charter; the two below are the minimum
// set. The list is data, so the UI control (e.g. the sandbox PovChip) renders
// whatever is defined here and a third POV can be added without touching the UI.

export type { StationPov, StationGeo, StationPovContext, StationPovHandle };

/** A named point of view the control can switch to. */
export interface PovDefinition {
  id: StationPov;
  /** Short control label. */
  label: string;
  /** One-line description of what the camera frames. */
  description: string;
}

/** The named POVs the control offers (>= 2). Data-driven; UI renders this. */
export const STATION_POVS: PovDefinition[] = [
  {
    id: "hydrophone",
    label: "Hydrophone POV",
    description: "Eye just above the seabed node, looking up toward the surface.",
  },
  {
    id: "topdown",
    label: "Top-down",
    description: "High station overview, with an optional slow orbit.",
  },
];

/** Per-POV director context, or a function that derives it from the POV. */
export type PovContextResolver =
  | StationPovContext
  | ((pov: StationPov) => StationPovContext);

export interface StationPovControllerOptions {
  /** The shared Camera Director the control drives. */
  director: CameraDirector;
  /** Current station geo (lat/lng/seabedDepthM); read fresh on every switch. */
  getStation: () => StationGeo;
  /** Director context per POV (e.g. top-down orbit on/off). */
  context?: PovContextResolver;
  /** POV to start on. Default the first defined POV ("hydrophone"). */
  initialPov?: StationPov;
}

/**
 * The POV-selection object. `setPov` switches the active POV through the
 * director; `refresh` re-runs the active POV (e.g. after the station changes so
 * the camera re-frames the new node); `stop` ends any motion the active POV
 * started.
 */
export interface StationPovController {
  listPovs(): PovDefinition[];
  getPov(): StationPov;
  setPov(pov: StationPov, contextOverride?: StationPovContext): void;
  /** Re-run the active POV against the current station (call on station change). */
  refresh(contextOverride?: StationPovContext): void;
  stop(): void;
}

function resolveContext(
  resolver: PovContextResolver | undefined,
  pov: StationPov,
  override?: StationPovContext,
): StationPovContext {
  if (override) return override;
  if (typeof resolver === "function") return resolver(pov);
  return resolver ?? {};
}

/**
 * Create a POV-selection controller bound to a director and a station getter.
 * Pure (no React); the live scene and the sandbox both construct one and call
 * `setPov` from their UI.
 */
export function createStationPovController(
  opts: StationPovControllerOptions,
): StationPovController {
  const { director, getStation, context } = opts;
  let current: StationPov = opts.initialPov ?? STATION_POVS[0].id;
  let handle: StationPovHandle | null = null;

  function run(pov: StationPov, override?: StationPovContext): void {
    handle?.stop();
    current = pov;
    handle = runStationPOV(pov, getStation(), director, resolveContext(context, pov, override));
  }

  return {
    listPovs() {
      return STATION_POVS;
    },
    getPov() {
      return current;
    },
    setPov(pov, contextOverride) {
      run(pov, contextOverride);
    },
    refresh(contextOverride) {
      run(current, contextOverride);
    },
    stop() {
      handle?.stop();
      handle = null;
    },
  };
}
