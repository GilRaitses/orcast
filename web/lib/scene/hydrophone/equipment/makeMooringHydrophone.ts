import * as THREE from "three";
import type { EquipmentRig, EquipmentVariantOptions } from "./types";

// A representative, low-poly subsurface MOORING hydrophone rig.
//
// MODELED, NOT A SCAN. This is a faithful-enough stand-in for an offshore
// moored PAM deployment (the kind described for North San Juan Channel: a CRT
// element on a longer cable, deployed deeper and away from the intertidal): a
// seabed anchor weight, a taut riser line, a subsurface buoyancy float that
// holds the line up, the hydrophone element in mid-water just below that
// buoyancy, and a thin tether continuing to a small surface marker. The root's
// local origin is the SEABED (local Y=0), matching makeHydrophoneRig, so the
// same `placement.stationSeabedPose` positions it on the modeled seabed and the
// surface marker reaches the water plane (world Y=0).
//
// Triangle budget is intentionally low (~200 tris). The root carries an honesty
// marker in `userData` so any UI that surfaces it labels it MODELED.

export interface MooringHydrophoneOptions extends EquipmentVariantOptions {
  /** Anchor weight footprint in metres. Default 1.4. */
  anchorSizeM?: number;
  /** Subsurface buoyancy float radius in metres. Default 0.7. */
  buoyancyRadiusM?: number;
  /** Hydrophone element housing height in metres. Default 0.6. */
  housingHeightM?: number;
  /** Surface marker float radius in metres. Default 0.35. */
  markerRadiusM?: number;
  /** Fraction of the depth at which the subsurface buoyancy sits. Default 0.6. */
  buoyancyDepthFraction?: number;
}

const ANCHOR_COLOR = 0x4a4f55; // dark concrete/iron clump weight
const LINE_COLOR = 0x9aa6ad; // galvanised riser line
const BUOYANCY_COLOR = 0xf2d23b; // yellow syntactic-foam buoyancy
const HOUSING_COLOR = 0x202830; // dark sensor housing
const TETHER_COLOR = 0x14181c; // dark tether
const MARKER_COLOR = 0xf2a93b; // high-visibility surface marker

/**
 * Build a representative subsurface mooring hydrophone as a `THREE.Group`.
 */
export function makeMooringHydrophone(opts: MooringHydrophoneOptions = {}): EquipmentRig {
  const wupm = opts.worldUnitsPerMeter && opts.worldUnitsPerMeter > 0 ? opts.worldUnitsPerMeter : 1;
  const depthM = typeof opts.seabedDepthM === "number" ? opts.seabedDepthM : -18;
  const fullLen = Math.max(0.1, Math.abs(depthM)) * wupm;
  const anchor = (opts.anchorSizeM ?? 1.4) * wupm;
  const buoyR = (opts.buoyancyRadiusM ?? 0.7) * wupm;
  const housingH = (opts.housingHeightM ?? 0.6) * wupm;
  const markerR = (opts.markerRadiusM ?? 0.35) * wupm;
  const frac = Math.min(0.9, Math.max(0.2, opts.buoyancyDepthFraction ?? 0.6));
  const buoyancyY = fullLen * frac; // local Y of the subsurface buoyancy

  const root = new THREE.Group();
  root.name = "hydrophone-mooring";
  root.userData.honesty = "modeled";
  root.userData.label = "hydrophone mooring (modeled)";
  root.userData.nodeClass = "mooring";

  const geometries: THREE.BufferGeometry[] = [];
  const materials: THREE.Material[] = [];
  const track = (g: THREE.BufferGeometry) => {
    geometries.push(g);
    return g;
  };

  const anchorMat = new THREE.MeshStandardMaterial({ color: ANCHOR_COLOR, roughness: 0.9, metalness: 0.2 });
  const lineMat = new THREE.MeshStandardMaterial({ color: LINE_COLOR, roughness: 0.6, metalness: 0.5 });
  const buoyancyMat = new THREE.MeshStandardMaterial({ color: BUOYANCY_COLOR, roughness: 0.6, metalness: 0.05 });
  const housingMat = new THREE.MeshStandardMaterial({ color: HOUSING_COLOR, roughness: 0.4, metalness: 0.4 });
  const tetherMat = new THREE.MeshStandardMaterial({ color: TETHER_COLOR, roughness: 0.85, metalness: 0.1 });
  const markerMat = new THREE.MeshStandardMaterial({ color: MARKER_COLOR, roughness: 0.5, metalness: 0.05 });
  materials.push(anchorMat, lineMat, buoyancyMat, housingMat, tetherMat, markerMat);

  // --- seabed anchor weight: a squat trapezoidal clump on the bottom.
  const anchorH = 0.5 * wupm;
  const anchorGeo = track(new THREE.CylinderGeometry(anchor * 0.45, anchor * 0.6, anchorH, 6, 1));
  const anchorMesh = new THREE.Mesh(anchorGeo, anchorMat);
  anchorMesh.position.y = anchorH / 2;
  root.add(anchorMesh);
  const anchorTopY = anchorH;

  // --- taut riser line from the anchor up to the subsurface buoyancy.
  const riserLen = Math.max(0.1, buoyancyY - anchorTopY);
  const riserR = 0.045 * wupm;
  const riserGeo = track(new THREE.CylinderGeometry(riserR, riserR, riserLen, 6, 1, true));
  const riser = new THREE.Mesh(riserGeo, lineMat);
  riser.position.y = anchorTopY + riserLen / 2;
  root.add(riser);

  // --- hydrophone element housing in mid-water, just below the buoyancy.
  const housingR = 0.11 * wupm;
  const housingGeo = track(new THREE.CylinderGeometry(housingR, housingR, housingH, 8, 1));
  const housing = new THREE.Mesh(housingGeo, housingMat);
  const housingY = buoyancyY - buoyR - housingH / 2 - 0.1 * wupm;
  housing.position.y = housingY;
  root.add(housing);

  const capGeo = track(new THREE.ConeGeometry(housingR, 0.16 * wupm, 8));
  const cap = new THREE.Mesh(capGeo, housingMat);
  cap.position.y = housingY - housingH / 2 - 0.08 * wupm;
  cap.rotation.x = Math.PI; // point the element down into the water column
  root.add(cap);

  // --- subsurface buoyancy float that tensions the line.
  const buoyancyGeo = track(new THREE.IcosahedronGeometry(buoyR, 0));
  const buoyancy = new THREE.Mesh(buoyancyGeo, buoyancyMat);
  buoyancy.position.y = buoyancyY;
  root.add(buoyancy);

  // --- thin tether continuing from the buoyancy to the surface marker.
  const tetherLen = Math.max(0.1, fullLen - buoyancyY);
  const tetherR = 0.03 * wupm;
  const tetherGeo = track(new THREE.CylinderGeometry(tetherR, tetherR, tetherLen, 6, 1, true));
  const tether = new THREE.Mesh(tetherGeo, tetherMat);
  tether.position.y = buoyancyY + tetherLen / 2;
  root.add(tether);

  // --- small surface marker float at the water plane (top of the tether).
  const markerGeo = track(new THREE.IcosahedronGeometry(markerR, 0));
  const marker = new THREE.Mesh(markerGeo, markerMat);
  marker.position.y = fullLen;
  root.add(marker);

  const dispose = () => {
    for (const g of geometries) g.dispose();
    for (const m of materials) m.dispose();
    root.clear();
  };

  return { root, dispose };
}
