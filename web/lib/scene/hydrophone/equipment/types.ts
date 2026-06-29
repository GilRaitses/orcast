import type * as THREE from "three";
import type { HydrophoneNodeClass } from "../catalog";

// Shared shape for a built equipment rig. MODELED, NOT A SCAN. Every variant
// returns a `THREE.Group` whose local origin is the SEABED (local Y=0), so
// `placement.stationSeabedPose` positions the root world Y on the substrate and
// the rig rises by |seabedDepthM| to reach the water plane (world Y=0). The
// root carries an honesty marker in `userData`:
//   userData.honesty = "modeled"
//   userData.label   = "<human label> (modeled)"
//   userData.nodeClass = "cabled" | "mooring"
export interface EquipmentRig {
  root: THREE.Group;
  dispose(): void;
}

/** Options shared by every parametric equipment variant. */
export interface EquipmentVariantOptions {
  /** Modeled seabed depth in metres (negative below sea level). Default -18. */
  seabedDepthM?: number;
  /** World units per metre. Default 1 (sandbox visible scale). */
  worldUnitsPerMeter?: number;
}

export type { HydrophoneNodeClass };
