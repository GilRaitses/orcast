import * as THREE from "three";

import { HEIGHT_SCALE, SCENE_WIDTH, projectToScene, sceneDepth } from "../../sceneIntent";
import { SUBSTRATE_LABEL } from "./loadSubstrate";
import type { SubstrateField } from "./types";

export interface SubstrateOverlayOptions {
  /**
   * Map a field point to scene-space [x, y, z]. The integrator should pass the
   * projector that matches the live tile frame so the overlay aligns with the
   * rendered terrain. When omitted, a default layout is used that follows the
   * legacy `sceneIntent` conventions (projectToScene + HEIGHT_SCALE, Y up).
   */
  project?: (lat: number, lng: number, depthM: number) => [number, number, number];
  /** Vertical metres -> scene units, used only by the default layout. Default `HEIGHT_SCALE`. */
  heightScale?: number;
  /** three Points size. Default `0.6`. */
  pointSize?: number;
  /** Material opacity in [0,1]. Default `0.85`. */
  opacity?: number;
  /** Render points relative to camera size. Default `false`. */
  sizeAttenuation?: boolean;
  /**
   * Two-stop depth ramp endpoints as hex colors. `deep` tints the most negative
   * depth, `high` the most positive. Defaults: deep navy -> pale land.
   */
  colorDeep?: THREE.ColorRepresentation;
  colorShore?: THREE.ColorRepresentation;
  colorHigh?: THREE.ColorRepresentation;
}

const DEFAULTS = {
  pointSize: 0.6,
  opacity: 0.85,
  sizeAttenuation: false,
  colorDeep: 0x081d3a,
  colorShore: 0x35c4d6,
  colorHigh: 0xc9b07a,
};

/**
 * Build an OPTIONAL, toggleable data layer for the modeled depth field as a
 * depth-tinted `THREE.Points` cloud. The integrator can `add`/`remove` the
 * returned object freely; it owns no per-frame state.
 *
 * MODELED, NOT MEASURED. The object is tagged `userData.modeledNotMeasured` and
 * `userData.label = "modeled, not measured"`, and `name` carries the same so any
 * UI built from the scene graph can surface the honesty label.
 *
 * Colors interpolate over the field's own depth extent: `colorDeep` at the most
 * negative depth, through `colorShore` at sea level (0 m, when in range), to
 * `colorHigh` at the most positive depth.
 */
export function buildSubstrateOverlay(
  field: SubstrateField,
  opts: SubstrateOverlayOptions = {},
): THREE.Object3D {
  const heightScale = opts.heightScale ?? HEIGHT_SCALE;
  const pointSize = opts.pointSize ?? DEFAULTS.pointSize;
  const opacity = opts.opacity ?? DEFAULTS.opacity;
  const sizeAttenuation = opts.sizeAttenuation ?? DEFAULTS.sizeAttenuation;

  const colorDeep = new THREE.Color(opts.colorDeep ?? DEFAULTS.colorDeep);
  const colorShore = new THREE.Color(opts.colorShore ?? DEFAULTS.colorShore);
  const colorHigh = new THREE.Color(opts.colorHigh ?? DEFAULTS.colorHigh);

  // Default layout mirrors the legacy heightmap frame: lng -> x, lat -> z,
  // depth_m -> y (* heightScale). The integrator should override `project` to
  // match the runtime tile frame instead.
  const depthSpan = sceneDepth(field.bounds);
  const defaultProject = (lat: number, lng: number, depthM: number): [number, number, number] => {
    const [x, z] = projectToScene(lat, lng, field.bounds, depthSpan);
    return [x, depthM * heightScale, z];
  };
  const project = opts.project ?? defaultProject;

  const n = field.points.length;
  const positions = new Float32Array(n * 3);
  const colors = new Float32Array(n * 3);

  const { minDepthM, maxDepthM } = field;
  const range = maxDepthM - minDepthM;
  const tmp = new THREE.Color();

  for (let i = 0; i < n; i++) {
    const p = field.points[i];
    const [x, y, z] = project(p.lat, p.lng, p.depth_m);
    positions[i * 3] = x;
    positions[i * 3 + 1] = y;
    positions[i * 3 + 2] = z;

    // Normalized depth in [0,1] over the field extent.
    const t = range > 0 ? (p.depth_m - minDepthM) / range : 0.5;
    // Sea-level (0 m) split point inside the extent, if 0 is in range.
    const seaT = range > 0 && minDepthM < 0 && maxDepthM > 0 ? -minDepthM / range : 0.5;
    if (t <= seaT && seaT > 0) {
      tmp.copy(colorDeep).lerp(colorShore, t / seaT);
    } else if (seaT < 1) {
      tmp.copy(colorShore).lerp(colorHigh, (t - seaT) / (1 - seaT));
    } else {
      tmp.copy(colorShore);
    }
    colors[i * 3] = tmp.r;
    colors[i * 3 + 1] = tmp.g;
    colors[i * 3 + 2] = tmp.b;
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  geometry.computeBoundingSphere();

  const material = new THREE.PointsMaterial({
    size: pointSize,
    sizeAttenuation,
    vertexColors: true,
    transparent: opacity < 1,
    opacity,
    depthWrite: opacity >= 1,
  });

  const points = new THREE.Points(geometry, material);
  points.name = `substrate-overlay (${SUBSTRATE_LABEL})`;
  points.frustumCulled = true;
  points.userData.modeledNotMeasured = true;
  points.userData.label = SUBSTRATE_LABEL;
  points.userData.source = field.source;
  points.userData.dataset = field.dataset;
  points.userData.minDepthM = minDepthM;
  points.userData.maxDepthM = maxDepthM;
  // Best-effort default scale hint so callers know the layout span.
  points.userData.sceneWidth = SCENE_WIDTH;

  return points;
}
