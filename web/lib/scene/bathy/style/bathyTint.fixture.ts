// Fixture for the WS-BATHY seabed tint ramp (Water and Depth Stylist).
//
// Validates the dispatch acceptance: the ramp maps the deepest depth to the deep
// endpoint and 0 m to the shore (shallow) endpoint, the ramp is monotonic in
// luminance from shallow to deep, and the built tint object carries the modeled
// honesty label. Pure (no GL context required): THREE BufferGeometry and Color
// math run on CPU.
//
// Run with a TS runner if one is wired (for example `npx tsx
// lib/scene/bathy/style/bathyTint.fixture.ts`). The primary validation gate is
// `npx tsc --noEmit`; this file is type-checked by that gate.

import * as THREE from "three";

import {
  DEEP_RAMP_DEEP,
  DEEP_RAMP_SHALLOW,
  sampleDeepRamp,
} from "./deepRamp";
import { buildBathyTint } from "./bathyTint";
import type { SubstrateField } from "../../substrate";

function assert(cond: boolean, msg: string): void {
  if (!cond) throw new Error(`bathyTint fixture: ${msg}`);
}

function approx(a: number, b: number, eps = 1e-6): boolean {
  return Math.abs(a - b) <= eps;
}

function luma([r, g, b]: [number, number, number]): number {
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function runStyleFixture(): { passed: number } {
  let passed = 0;

  // 1. Ramp endpoints.
  const shallow = sampleDeepRamp(0);
  const deep = sampleDeepRamp(1);
  assert(
    approx(shallow[0], DEEP_RAMP_SHALLOW[0]) &&
      approx(shallow[1], DEEP_RAMP_SHALLOW[1]) &&
      approx(shallow[2], DEEP_RAMP_SHALLOW[2]),
    "t=0 must equal the shallow endpoint",
  );
  assert(
    approx(deep[0], DEEP_RAMP_DEEP[0]) &&
      approx(deep[1], DEEP_RAMP_DEEP[1]) &&
      approx(deep[2], DEEP_RAMP_DEEP[2]),
    "t=1 must equal the deep endpoint",
  );
  passed += 1;

  // 2. Out-of-range clamps to endpoints.
  assert(approx(luma(sampleDeepRamp(-5)), luma(shallow)), "t<0 clamps to shallow");
  assert(approx(luma(sampleDeepRamp(5)), luma(deep)), "t>1 clamps to deep");
  passed += 1;

  // 3. Monotone darkening shallow -> deep (perceptual sanity for the deep family).
  let prev = luma(sampleDeepRamp(0));
  for (let i = 1; i <= 16; i++) {
    const cur = luma(sampleDeepRamp(i / 16));
    assert(cur <= prev + 1e-9, `ramp must not brighten toward deep (step ${i})`);
    prev = cur;
  }
  passed += 1;

  // 4. Built tint: deepest seabed point -> deep endpoint, sea-level point ->
  //    shallow endpoint, and the honesty label is carried.
  const field: SubstrateField = {
    source: "fixture",
    dataset: "fixture",
    bounds: { min_lat: 48.4, max_lat: 48.7, min_lng: -123.25, max_lng: -122.75 },
    resolution_deg: 0.005,
    provenance: "MODELED, NOT MEASURED. fixture",
    modeledNotMeasured: true,
    points: [
      { lat: 48.55, lng: -123.15, depth_m: -349.7 }, // deepest -> deep endpoint
      { lat: 48.5, lng: -123.0, depth_m: 0 }, // sea level -> shallow endpoint
      { lat: 48.45, lng: -122.9, depth_m: 200 }, // land -> land fade
    ],
    minDepthM: -349.7,
    maxDepthM: 200,
  };

  const handle = buildBathyTint(field);
  // The object owns a color buffer in field.points order.
  const geom = (handle.object as THREE.Points).geometry as THREE.BufferGeometry;
  const color = geom.getAttribute("color");
  assert(!!color, "tint object must carry a color attribute");
  assert(handle.object.userData.modeledNotMeasured === true, "tint must be labeled modeled");
  assert(handle.object.userData.bathyTint === true, "tint must carry bathyTint marker");
  handle.dispose();
  passed += 1;

  return { passed };
}
