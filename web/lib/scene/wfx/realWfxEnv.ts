// WFX environment producer for the LIVE twin (W4 integrate).
//
// The orca sandbox used `makeSandboxWfxEnv`, a stand-in that PMREMs a procedural
// sky AND supplies SANDBOX-METRIC underwater absorption (vec3(0.12,0.06,0.035),
// per-metre because the sandbox runs 1 unit == 1 m). At integrate the twin runs
// the synthetic SCENE_WIDTH=120 frame where ~0.0024 units == 1 m, so the same
// metric vector would barely tint the animal. This module is the REAL producer:
// it owns the unit conversion. It PMREMs the actual scene sky (the decor
// Preetham dome) for the orca's above-water IBL, and it derives the underwater
// Beer-Lambert absorption in TWIN units from the owner-signed
// `PROPOSED_RGB_EXTINCTION` {3,1,3} (green-survives, WFX SIGN_OFF #2 / R11). The
// SAME handle is fed to BOTH the Water2Rig and the OrcaRig, so neither over- nor
// under-extinguishes: the water divides this absorption by its own
// `depthColorScale` color ramp, the orca applies it raw against its scene-unit
// submersion depth, and both read the one green-survives optic.
//
// HONESTY. The sky is a modeled atmosphere, the absorption is a rendering optic,
// not measured water clarity. The shared handle keeps the modeled animal lit by
// the same modeled atmosphere as the modeled water.

import * as THREE from "three";
import { makeSkyDome } from "@/lib/scene/decor";
import {
  PROPOSED_RGB_EXTINCTION,
  WATER_TUNED_DEEP,
  WATER_TUNED_SHALLOW,
} from "@/lib/scene/bathy/style/waterTuning";
import type { WfxEnvHandle } from "@/lib/scene/orca";

export interface RealWfxEnvOptions {
  /** Live renderer, for the PMREM pass. */
  renderer: THREE.WebGLRenderer;
  /** Unit vector toward the sun (realism makeSun().direction). */
  sunDirection: THREE.Vector3;
  /** Sun color (realism makeSun().color). */
  sunColor: THREE.Color;
  /** Sun intensity (realism makeSun().intensity). */
  sunIntensity: number;
  /** Scene Y of the water surface (SEA_LEVEL_Y). Default 0. */
  waterLevelY?: number;
  /** Useful underwater sight distance in scene units. Default 1.5. */
  visibility?: number;
}

/**
 * Build the real WFX environment handle for the live twin. PMREMs the decor
 * Preetham sky dome (the same sky SkyRig renders for the background) so the
 * orca's PBR IBL comes from the scene's own sky, and supplies the twin-unit
 * underwater optic. Call `dispose()` on unmount to free the PMREM target.
 */
export function makeRealWfxEnv(opts: RealWfxEnvOptions): WfxEnvHandle {
  // --- PMREM of the scene sky (orca above-water IBL, R03 env seam) ---
  const pmrem = new THREE.PMREMGenerator(opts.renderer);
  const dome = makeSkyDome({ sunDirection: opts.sunDirection });
  const skyScene = new THREE.Scene();
  skyScene.add(dome.object3D);
  // The Sky dome forces fragments to the far plane, so near/far only need to be
  // valid; the captured radiance is the full sky regardless of dome scale.
  const target = pmrem.fromScene(skyScene, 0, 0.1, 1000);
  skyScene.remove(dome.object3D);
  dome.dispose();

  // --- Twin-unit underwater optic (owns the unit conversion) ---
  // PROPOSED_RGB_EXTINCTION is the owner-signed green-survives extinction in
  // INVERSE SCENE UNITS for the twin (NOT the sandbox per-metre stand-in). The
  // orca material applies exp(-absorption * depthBelow) with depthBelow in scene
  // units, so this is the value to hand it directly. The water consumes the same
  // numbers through bathyWater2Options/E4 and divides by its own depthColorScale.
  const absorption = new THREE.Vector3(
    PROPOSED_RGB_EXTINCTION.r,
    PROPOSED_RGB_EXTINCTION.g,
    PROPOSED_RGB_EXTINCTION.b,
  );

  // In-scatter glow the orca silhouette picks up underwater: a turbid Salish
  // green midway between the signed deep and shallow tints (green-survives).
  const inScatterColor = new THREE.Color(WATER_TUNED_DEEP).lerp(
    new THREE.Color(WATER_TUNED_SHALLOW),
    0.5,
  );

  return {
    pmremEnvironment: target.texture,
    sunDirection: opts.sunDirection.clone().normalize(),
    sunColor: opts.sunColor.clone(),
    sunIntensity: opts.sunIntensity,
    underwater: {
      absorption,
      inScatterColor,
      waterLevelY: opts.waterLevelY ?? 0,
      visibility: opts.visibility ?? 1.5,
    },
    dispose() {
      target.dispose();
      pmrem.dispose();
    },
  };
}
