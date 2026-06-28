// Terrain Stylist for the orcast Salish scene (WS-SCENIC, phase A, producer 1).
//
// Makes the streamed CUDEM tile surface read as living, materially-correct land
// instead of bare tan relief by restyling each tile material with an
// elevation-and-slope biome tint, WITHOUT changing tile geometry, transforms, or
// the tiles hook. Low flat ground reads forest-green near the realism `LAND_LOW`,
// mid elevation drifts to a drier grass-tan near `LAND_HIGH`, steep faces blend to
// a rock gray driven by a `dot(worldNormal, up)` slope term, and a narrow band
// just above sea level (Y == 0) reads as shoreline.
//
// HONESTY. The tint is DERIVED from the rendered CUDEM height and slope. It is
// interpretive color, not a vegetation survey and not draped land cover. The
// geometry is the real CUDEM tileset; this module only restyles materials.
//
// Ownership: web/lib/scene/terrain/ only. The module reads the realism public
// palette (LAND_LOW/LAND_HIGH) through the realism barrel and consumes the
// passed `TilesRenderer` through the public `3d-tiles-renderer` API
// (addEventListener + forEachLoadedModel). It never edits realism/ or tiles/.

import * as THREE from "three";
import { TilesRenderer } from "3d-tiles-renderer";
import { LAND_LOW, LAND_HIGH } from "@/app/components/scene/realism";

export interface TerrainStyleOptions {
  /**
   * Scene units per metre of true elevation. The live tileset is fit so its
   * bounding-sphere diameter equals `SCENE_WIDTH` (120), giving roughly 0.0024
   * units/m with no vertical exaggeration. Elevation thresholds below are given
   * in metres and converted to scene-Y with this factor. Default `0.0024`.
   */
  worldUnitsPerMeter?: number;

  /** Forest-green tint on low flat ground. Default realism `LAND_LOW` (#3f6b3a). */
  lowColor?: THREE.ColorRepresentation;
  /** Drier grass-tan tint at mid elevation. Default realism `LAND_HIGH` (#9aa886). */
  midColor?: THREE.ColorRepresentation;
  /** Rock gray on steep faces. Default `#6e6a63`. */
  rockColor?: THREE.ColorRepresentation;
  /** Shoreline band tint just above sea level. Default `#9a8f73`. */
  shoreColor?: THREE.ColorRepresentation;

  /** Elevation (metres above sea level) where the low->mid blend begins. Default 120. */
  midElevationM?: number;
  /** Elevation (metres) where the tint is fully mid/high grass-tan. Default 500. */
  highElevationM?: number;
  /** Height (metres above Y==0) of the shoreline band. Default 35. */
  shoreBandM?: number;

  /**
   * Slope term `dot(worldNormal, up)` at or below which a face reads as steep
   * rock. 1.0 is flat ground, 0.0 is a vertical wall. Default 0.6 (~53 deg).
   */
  slopeThreshold?: number;
  /** Softness of the steep-rock transition around `slopeThreshold`. Default 0.15. */
  slopeSoftness?: number;

  /** How strongly the shoreline band overrides the biome color, [0,1]. Default 0.7. */
  shoreStrength?: number;
  /** Overall blend of the biome tint over the tile's own color, [0,1]. Default 0.85. */
  tintStrength?: number;

  /** MeshStandardMaterial.roughness applied to restyled tile materials. Default 0.95. */
  roughness?: number;
  /**
   * When set and the tile material carries a normal map, scales it via
   * `material.normalScale`. Omitted by default (the tile normal scale is left
   * untouched).
   */
  normalScale?: number;
}

export interface TerrainStyleHandle {
  /**
   * Remove the `load-model`/`dispose-model` listeners, restore every tile mesh
   * to its original material, and dispose every material this module created.
   */
  dispose(): void;
}

interface ResolvedUniforms {
  uLandLow: { value: THREE.Color };
  uLandMid: { value: THREE.Color };
  uRock: { value: THREE.Color };
  uShore: { value: THREE.Color };
  uMidElevationY: { value: number };
  uHighElevationY: { value: number };
  uShoreBandY: { value: number };
  uSlopeThreshold: { value: number };
  uSlopeSoftness: { value: number };
  uShoreStrength: { value: number };
  uTintStrength: { value: number };
}

const ORIGINAL_MATERIAL_KEY = "__terrainStylistOriginalMaterial";

/**
 * Install the elevation-and-slope biome tint onto a `TilesRenderer`.
 *
 * Registers a `load-model` listener that restyles each newly streamed tile, a
 * `dispose-model` listener that restores and frees the materials for an unloaded
 * tile, and calls `forEachLoadedModel` once to restyle tiles already streamed.
 *
 * @param tiles the live `TilesRenderer` instance the integrator passes in
 * @param opts  see `TerrainStyleOptions`
 */
export function applyTerrainStyle(
  tiles: TilesRenderer,
  opts: TerrainStyleOptions = {},
): TerrainStyleHandle {
  const unitsPerMeter = opts.worldUnitsPerMeter ?? 0.0024;

  // Shared uniform objects so every restyled tile reads the same biome tuning.
  const uniforms: ResolvedUniforms = {
    uLandLow: { value: new THREE.Color(opts.lowColor ?? LAND_LOW) },
    uLandMid: { value: new THREE.Color(opts.midColor ?? LAND_HIGH) },
    uRock: { value: new THREE.Color(opts.rockColor ?? "#6e6a63") },
    uShore: { value: new THREE.Color(opts.shoreColor ?? "#9a8f73") },
    uMidElevationY: { value: (opts.midElevationM ?? 120) * unitsPerMeter },
    uHighElevationY: { value: (opts.highElevationM ?? 500) * unitsPerMeter },
    uShoreBandY: { value: (opts.shoreBandM ?? 35) * unitsPerMeter },
    uSlopeThreshold: { value: opts.slopeThreshold ?? 0.6 },
    uSlopeSoftness: { value: Math.max(1e-4, opts.slopeSoftness ?? 0.15) },
    uShoreStrength: { value: clamp01(opts.shoreStrength ?? 0.7) },
    uTintStrength: { value: clamp01(opts.tintStrength ?? 0.85) },
  };

  const roughness = opts.roughness ?? 0.95;
  const normalScale = opts.normalScale;

  // Every material this module creates, so dispose() can free exactly these and
  // never touch a material it did not create.
  const createdMaterials = new Set<THREE.Material>();
  // Meshes this module has restyled, so dispose() can restore originals.
  const styledMeshes = new Set<THREE.Mesh>();

  function patchMaterial(source: THREE.Material): THREE.Material {
    const clone = source.clone();
    clone.onBeforeCompile = (shader) => {
      Object.assign(shader.uniforms, uniforms);
      shader.vertexShader = injectVertex(shader.vertexShader);
      shader.fragmentShader = injectFragment(shader.fragmentShader);
    };
    // Distinguish the program from the unpatched source so three compiles a
    // fresh shader instead of reusing the source program cache key.
    clone.customProgramCacheKey = () => "terrain-stylist";
    if ("roughness" in clone) {
      (clone as THREE.MeshStandardMaterial).roughness = roughness;
    }
    if (
      normalScale !== undefined &&
      "normalScale" in clone &&
      (clone as THREE.MeshStandardMaterial).normalScale
    ) {
      (clone as THREE.MeshStandardMaterial).normalScale.setScalar(normalScale);
    }
    clone.needsUpdate = true;
    createdMaterials.add(clone);
    return clone;
  }

  function styleMesh(mesh: THREE.Mesh): void {
    if (mesh.userData[ORIGINAL_MATERIAL_KEY] !== undefined) return; // already styled
    const original = mesh.material;
    if (Array.isArray(original)) {
      mesh.userData[ORIGINAL_MATERIAL_KEY] = original;
      mesh.material = original.map((m) => patchMaterial(m));
    } else {
      mesh.userData[ORIGINAL_MATERIAL_KEY] = original;
      mesh.material = patchMaterial(original);
    }
    mesh.userData.terrainTint = "derived tint, real CUDEM geometry";
    styledMeshes.add(mesh);
  }

  function restoreMesh(mesh: THREE.Mesh): void {
    const original = mesh.userData[ORIGINAL_MATERIAL_KEY] as
      | THREE.Material
      | THREE.Material[]
      | undefined;
    if (original === undefined) return;
    const current = mesh.material;
    if (Array.isArray(current)) {
      current.forEach((m) => {
        if (createdMaterials.has(m)) {
          m.dispose();
          createdMaterials.delete(m);
        }
      });
    } else if (createdMaterials.has(current)) {
      current.dispose();
      createdMaterials.delete(current);
    }
    mesh.material = original;
    delete mesh.userData[ORIGINAL_MATERIAL_KEY];
    delete mesh.userData.terrainTint;
    styledMeshes.delete(mesh);
  }

  function styleScene(scene: THREE.Object3D): void {
    scene.traverse((o) => {
      if (o instanceof THREE.Mesh) styleMesh(o);
    });
  }

  const onLoadModel = (e: { scene: THREE.Object3D }) => {
    styleScene(e.scene);
  };
  const onDisposeModel = (e: { scene: THREE.Object3D }) => {
    e.scene.traverse((o) => {
      if (o instanceof THREE.Mesh) restoreMesh(o);
    });
  };

  tiles.addEventListener("load-model", onLoadModel);
  tiles.addEventListener("dispose-model", onDisposeModel);

  // Restyle tiles that streamed in before this module mounted.
  tiles.forEachLoadedModel((scene) => styleScene(scene));

  return {
    dispose() {
      tiles.removeEventListener("load-model", onLoadModel);
      tiles.removeEventListener("dispose-model", onDisposeModel);
      // Restore originals and free every material this module created.
      for (const mesh of Array.from(styledMeshes)) restoreMesh(mesh);
      for (const m of Array.from(createdMaterials)) {
        m.dispose();
        createdMaterials.delete(m);
      }
    },
  };
}

function clamp01(x: number): number {
  return Math.max(0, Math.min(1, x));
}

// Capture the world-space position and world-space normal of each fragment.
// The tile group is fit with a uniform scale (no shear), so the world normal is
// `mat3(modelMatrix) * objectNormal` normalized.
function injectVertex(src: string): string {
  let out = src;
  out = out.replace(
    "#include <common>",
    "#include <common>\nvarying vec3 vTerrainWorldPos;\nvarying vec3 vTerrainWorldNormal;",
  );
  out = out.replace(
    "#include <beginnormal_vertex>",
    "#include <beginnormal_vertex>\nvTerrainWorldNormal = normalize( mat3( modelMatrix ) * objectNormal );",
  );
  out = out.replace(
    "#include <begin_vertex>",
    "#include <begin_vertex>\nvTerrainWorldPos = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz;",
  );
  return out;
}

function injectFragment(src: string): string {
  const header = `#include <common>
uniform vec3 uLandLow;
uniform vec3 uLandMid;
uniform vec3 uRock;
uniform vec3 uShore;
uniform float uMidElevationY;
uniform float uHighElevationY;
uniform float uShoreBandY;
uniform float uSlopeThreshold;
uniform float uSlopeSoftness;
uniform float uShoreStrength;
uniform float uTintStrength;
varying vec3 vTerrainWorldPos;
varying vec3 vTerrainWorldNormal;`;

  // Elevation + slope biome tint, applied after the tile's own color is resolved.
  const tint = `#include <color_fragment>
{
  float terrainY = vTerrainWorldPos.y;
  vec3 terrainN = normalize( vTerrainWorldNormal );
  float upDot = clamp( dot( terrainN, vec3( 0.0, 1.0, 0.0 ) ), 0.0, 1.0 );

  // Low forest-green to mid grass-tan by elevation.
  float elevT = smoothstep( uMidElevationY, uHighElevationY, terrainY );
  vec3 biome = mix( uLandLow, uLandMid, elevT );

  // Steep faces blend toward rock gray (low up-dot == steep).
  float rockMask = 1.0 - smoothstep(
    uSlopeThreshold - uSlopeSoftness,
    uSlopeThreshold + uSlopeSoftness,
    upDot
  );
  biome = mix( biome, uRock, rockMask );

  // Narrow shoreline band just above sea level (Y == 0), only on flatter ground.
  float shoreMask = ( 1.0 - smoothstep( 0.0, uShoreBandY, abs( terrainY ) ) ) * upDot;
  biome = mix( biome, uShore, shoreMask * uShoreStrength );

  diffuseColor.rgb = mix( diffuseColor.rgb, biome, uTintStrength );
}`;

  let out = src;
  out = out.replace("#include <common>", header);
  out = out.replace("#include <color_fragment>", tint);
  return out;
}
