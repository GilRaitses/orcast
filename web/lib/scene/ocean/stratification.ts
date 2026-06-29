// Stratification profile that drives the interpretive double-diffusion layer.
//
// HONESTY. The default profile here is an ANALYTIC two-layer Salish halocline,
// not a measured cast. It is grounded in the documented shape of Salish Sea
// stratification (fresher and warmer near the surface, saltier and colder at
// depth, with a sharp halocline) but its numbers are a stylized curve, not data.
// The measured-grounding upgrade is a CC0 CruiseSalish CTD profile baked offline
// (NANOOS CruiseSalish / NCEI Accession 0307188); fetching that dataset is an
// O0-gated download and is intentionally NOT done here. See BSW-R09.
//
// This module produces a small 1-D gradient (a DataTexture, width = samples,
// height = 1) the shader samples by depth fraction to place and sharpen the
// stylized mixing bands. No external fetch, no heavy asset.

import * as THREE from "three";

export type StratificationOrigin = "analytic" | "measured-ctd";

export interface StratificationSample {
  /** Depth below the surface in metres (0 = surface). */
  depthM: number;
  /** Temperature in degrees Celsius. */
  temperatureC: number;
  /** Practical salinity (PSU). */
  salinityPsu: number;
}

export interface StratificationProfile {
  origin: StratificationOrigin;
  /** Human-readable provenance line for the HUD / attribution. */
  provenance: string;
  /** Max depth the profile spans in metres. */
  maxDepthM: number;
  /** Samples ordered surface -> deep. */
  samples: StratificationSample[];
}

/**
 * Analytic Salish-shaped halocline. Surface ~28 PSU / 13 C, deep ~31 PSU / 9 C,
 * with the halocline centred near `haloclineM`. Stylized, not measured.
 */
export function analyticHaloclineProfile(opts: {
  maxDepthM?: number;
  samples?: number;
  haloclineM?: number;
} = {}): StratificationProfile {
  const maxDepthM = opts.maxDepthM ?? 80;
  const count = Math.max(4, opts.samples ?? 64);
  const haloclineM = opts.haloclineM ?? 14;
  const sharpness = 6 / Math.max(1, haloclineM); // tanh slope of the transition

  const samples: StratificationSample[] = [];
  for (let i = 0; i < count; i++) {
    const depthM = (i / (count - 1)) * maxDepthM;
    // Smooth two-layer transition through the halocline.
    const k = Math.tanh((depthM - haloclineM) * sharpness); // -1 surface .. +1 deep
    const mix = 0.5 + 0.5 * k;
    const salinityPsu = 28.0 + (31.2 - 28.0) * mix;
    const temperatureC = 13.0 + (9.0 - 13.0) * mix;
    samples.push({ depthM, temperatureC, salinityPsu });
  }

  return {
    origin: "analytic",
    provenance:
      "analytic Salish halocline (stylized, not a measured cast). Measured grounding available from NANOOS CruiseSalish CTD (CC0), gated.",
    maxDepthM,
    samples,
  };
}

function range(values: number[]): { min: number; max: number } {
  let min = Infinity;
  let max = -Infinity;
  for (const v of values) {
    if (v < min) min = v;
    if (v > max) max = v;
  }
  if (!Number.isFinite(min) || !Number.isFinite(max) || max === min) {
    return { min: 0, max: 1 };
  }
  return { min, max };
}

/**
 * Bake the profile into a width x 1 RGBA8 DataTexture the shader samples by depth
 * fraction (u = depthFrac, surface at u=0):
 *   R = normalized salinity       (0 fresh .. 1 salty)
 *   G = normalized temperature    (0 cold  .. 1 warm)
 *   B = normalized |d(density)/dz| (stratification strength -> band sharpness)
 *   A = depth fraction            (0 surface .. 1 deepest)
 * Density uses a linear equation-of-state proxy (saltier and colder -> denser),
 * which is enough to locate the strongest mixing interface for a stylized layer.
 */
export function stratificationToTexture(profile: StratificationProfile): THREE.DataTexture {
  const n = profile.samples.length;
  const sal = profile.samples.map((s) => s.salinityPsu);
  const tmp = profile.samples.map((s) => s.temperatureC);
  const salR = range(sal);
  const tmpR = range(tmp);

  // Density proxy (relative): rho ~ b*S - a*T. Constants are illustrative scales.
  const rho = profile.samples.map((s) => 0.78 * s.salinityPsu - 0.2 * s.temperatureC);
  const dRho: number[] = new Array(n);
  for (let i = 0; i < n; i++) {
    const a = rho[Math.max(0, i - 1)];
    const b = rho[Math.min(n - 1, i + 1)];
    dRho[i] = Math.abs(b - a);
  }
  const dRhoR = range(dRho);

  const data = new Uint8Array(n * 4);
  for (let i = 0; i < n; i++) {
    const sNorm = (sal[i] - salR.min) / (salR.max - salR.min);
    const tNorm = (tmp[i] - tmpR.min) / (tmpR.max - tmpR.min);
    const gNorm = (dRho[i] - dRhoR.min) / (dRhoR.max - dRhoR.min);
    const depthFrac = i / (n - 1);
    data[i * 4] = Math.round(sNorm * 255);
    data[i * 4 + 1] = Math.round(tNorm * 255);
    data[i * 4 + 2] = Math.round(gNorm * 255);
    data[i * 4 + 3] = Math.round(depthFrac * 255);
  }

  const tex = new THREE.DataTexture(data, n, 1, THREE.RGBAFormat, THREE.UnsignedByteType);
  tex.minFilter = THREE.LinearFilter;
  tex.magFilter = THREE.LinearFilter;
  tex.wrapS = THREE.ClampToEdgeWrapping;
  tex.wrapT = THREE.ClampToEdgeWrapping;
  tex.needsUpdate = true;
  return tex;
}
