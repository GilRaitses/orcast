import * as THREE from "three";

// A representative, low-poly Orcasound-style cabled shore hydrophone rig.
//
// MODELED, NOT A SCAN. The geometry is a faithful-enough stand-in for a cabled
// shore node like Orcasound Lab: a seabed anchor frame, a hydrophone element
// housing, a thin cable rising to the surface, and a small surface float. It is
// built in metres scaled by `worldUnitsPerMeter` so it can sit honestly on the
// modeled seabed at its true depth. The root's local origin is at the seabed
// (Y=0 local); `placement.stationSeabedPose` positions the root world Y on the
// substrate, and the cable rises by |seabedDepthM| so the float reaches the
// water plane (world Y=0).

export interface HydrophoneRigOptions {
  /** Modeled seabed depth in metres (negative below sea level). Default -18. */
  seabedDepthM?: number;
  /** World units per metre. Default 1 (sandbox visible scale). */
  worldUnitsPerMeter?: number;
  /** Seabed anchor frame footprint in metres. Default 2.0. */
  frameSizeM?: number;
  /** Hydrophone element housing height in metres. Default 0.8. */
  housingHeightM?: number;
  /** Surface float radius in metres. Default 0.5. */
  floatRadiusM?: number;
}

export interface HydrophoneRig {
  root: THREE.Group;
  dispose(): void;
}

const FRAME_COLOR = 0x9aa6ad; // galvanised steel frame
const HOUSING_COLOR = 0x202830; // dark sensor housing
const CABLE_COLOR = 0x14181c; // dark cable
const FLOAT_COLOR = 0xf2a93b; // high-visibility surface buoy

/**
 * Build a representative cabled shore hydrophone as a `THREE.Group`.
 *
 * Triangle budget is intentionally low (~150 tris) so many nodes can be placed.
 * The root carries an honesty marker in `userData` so any UI that surfaces it
 * can label it MODELED rather than implying a measured scan.
 */
export function makeHydrophoneRig(opts: HydrophoneRigOptions = {}): HydrophoneRig {
  const wupm = opts.worldUnitsPerMeter && opts.worldUnitsPerMeter > 0 ? opts.worldUnitsPerMeter : 1;
  const depthM = typeof opts.seabedDepthM === "number" ? opts.seabedDepthM : -18;
  const frame = (opts.frameSizeM ?? 2.0) * wupm;
  const housingH = (opts.housingHeightM ?? 0.8) * wupm;
  const floatR = (opts.floatRadiusM ?? 0.5) * wupm;
  // The cable rises from the seabed to the water plane: |depth| in metres.
  const cableLen = Math.max(0.1, Math.abs(depthM)) * wupm;

  const root = new THREE.Group();
  root.name = "hydrophone-rig";
  root.userData.honesty = "modeled";
  root.userData.label = "hydrophone equipment (modeled)";

  const geometries: THREE.BufferGeometry[] = [];
  const materials: THREE.Material[] = [];

  const frameMat = new THREE.MeshStandardMaterial({ color: FRAME_COLOR, roughness: 0.55, metalness: 0.7 });
  const housingMat = new THREE.MeshStandardMaterial({ color: HOUSING_COLOR, roughness: 0.4, metalness: 0.4 });
  const cableMat = new THREE.MeshStandardMaterial({ color: CABLE_COLOR, roughness: 0.85, metalness: 0.1 });
  const floatMat = new THREE.MeshStandardMaterial({ color: FLOAT_COLOR, roughness: 0.5, metalness: 0.05 });
  materials.push(frameMat, housingMat, cableMat, floatMat);

  const track = (g: THREE.BufferGeometry) => {
    geometries.push(g);
    return g;
  };

  // --- seabed anchor frame: a flat base plate + 4 corner legs + a cross brace.
  const legH = 0.5 * wupm;
  const half = frame / 2;
  const legR = 0.06 * wupm;

  const baseGeo = track(new THREE.BoxGeometry(frame, 0.15 * wupm, frame));
  const base = new THREE.Mesh(baseGeo, frameMat);
  base.position.y = legH + 0.075 * wupm;
  root.add(base);

  const legGeo = track(new THREE.BoxGeometry(legR * 2, legH, legR * 2));
  const legOffsets: Array<[number, number]> = [
    [half - legR * 2, half - legR * 2],
    [-(half - legR * 2), half - legR * 2],
    [half - legR * 2, -(half - legR * 2)],
    [-(half - legR * 2), -(half - legR * 2)],
  ];
  for (const [lx, lz] of legOffsets) {
    const leg = new THREE.Mesh(legGeo, frameMat);
    leg.position.set(lx, legH / 2, lz);
    root.add(leg);
  }

  // A single cross brace so the frame reads as a structure, not a slab.
  const braceGeo = track(new THREE.BoxGeometry(frame * 0.9, 0.06 * wupm, legR * 2));
  const brace = new THREE.Mesh(braceGeo, frameMat);
  brace.position.y = legH * 0.5;
  root.add(brace);

  const baseTopY = legH + 0.15 * wupm;

  // --- hydrophone element housing: a short capped cylinder standing on the frame.
  const housingR = 0.12 * wupm;
  const housingGeo = track(new THREE.CylinderGeometry(housingR, housingR, housingH, 8, 1));
  const housing = new THREE.Mesh(housingGeo, housingMat);
  housing.position.y = baseTopY + housingH / 2;
  root.add(housing);

  const capGeo = track(new THREE.ConeGeometry(housingR, 0.18 * wupm, 8));
  const cap = new THREE.Mesh(capGeo, housingMat);
  cap.position.y = baseTopY + housingH + 0.09 * wupm;
  root.add(cap);

  // --- cable rising from the frame to the surface float (open-ended, low tri).
  const cableR = 0.04 * wupm;
  const cableGeo = track(new THREE.CylinderGeometry(cableR, cableR, cableLen, 6, 1, true));
  const cable = new THREE.Mesh(cableGeo, cableMat);
  cable.position.y = baseTopY + cableLen / 2;
  root.add(cable);

  // --- surface float / buoy at the water plane (top of the cable).
  const floatGeo = track(new THREE.IcosahedronGeometry(floatR, 0));
  const buoy = new THREE.Mesh(floatGeo, floatMat);
  buoy.position.y = baseTopY + cableLen;
  root.add(buoy);

  const dispose = () => {
    for (const g of geometries) g.dispose();
    for (const m of materials) m.dispose();
    root.clear();
  };

  return { root, dispose };
}
