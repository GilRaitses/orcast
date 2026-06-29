import { makeHydrophoneRig } from "../makeHydrophoneRig";
import { makeMooringHydrophone } from "./makeMooringHydrophone";
import type { EquipmentRig, EquipmentVariantOptions, HydrophoneNodeClass } from "./types";

// Pick and build the right MODELED equipment variant for a node class.
//
//   - "cabled":  the cabled shore hydrophone (element + housing on a seabed
//                frame, cable rising to a surface float) -> makeHydrophoneRig.
//   - "mooring": the subsurface mooring (anchor, riser, subsurface buoyancy,
//                mid-water element, tether to a surface marker) -> makeMooringHydrophone.
//
// Both variants share the seabed-origin convention and an `userData` honesty
// marker, so placement and labeling are identical. The variant choice is a
// MODELED/representative presentation decision (see catalog.classifyNodeClass),
// not a claim about the exact hardware in the water.

/**
 * Build the equipment rig for a node class. Returns the same `{ root, dispose }`
 * shape regardless of variant; the root's `userData.nodeClass` records which
 * variant was built.
 */
export function makeStationEquipment(
  nodeClass: HydrophoneNodeClass,
  opts: EquipmentVariantOptions = {},
): EquipmentRig {
  if (nodeClass === "mooring") {
    return makeMooringHydrophone(opts);
  }
  // Cabled shore hydrophone (the slice's canonical rig). Tag the node class on
  // the root so a UI can read it the same way as the mooring variant.
  const rig = makeHydrophoneRig(opts);
  rig.root.userData.nodeClass = "cabled";
  return rig;
}
