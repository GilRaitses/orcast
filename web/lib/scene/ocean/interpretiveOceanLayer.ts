// Interpretive ocean layer (rank-4 follow-on), OFF by default.
//
// This is an honest, labeled stub: an additive, transparent set of stratified
// vertical planes that read as soft layered mixing, NOT a physical simulation. It
// is NOT a raymarch and adds NO new full render pass; it never writes depth and
// never replaces or regresses the real water. It defaults to disabled and, when
// enabled, the host MUST display the mandatory interpretive chip text below.
//
// Honesty: this layer is interpretive only. The forbidden phrases for the chip and
// any copy around it are asserted out at module load so they can never ship.

import * as THREE from "three";

/** Mandatory on-screen chip text whenever the layer is enabled. */
export const INTERPRETIVE_OCEAN_LABEL = "interpretive · stratified ocean mixing";

// Guardrail: these claims must never appear near this interpretive stub.
const FORBIDDEN = ["measured thermohaline", "biosonar perception"];
for (const phrase of FORBIDDEN) {
  if (INTERPRETIVE_OCEAN_LABEL.toLowerCase().includes(phrase)) {
    throw new Error(`interpretiveOceanLayer: forbidden claim in label: ${phrase}`);
  }
}

export interface InterpretiveOceanOptions {
  /** World width of the layer. */
  width?: number;
  /** Vertical extent (depth span) of the strata. */
  height?: number;
  /** Number of stratified bands. */
  strata?: number;
  /** Top (surface) tint. */
  surfaceColor?: THREE.ColorRepresentation;
  /** Bottom (deep) tint. */
  deepColor?: THREE.ColorRepresentation;
  /** Peak additive opacity per band. */
  opacity?: number;
}

export interface InterpretiveOceanLayer {
  /** Add this to the scene; it is self-contained and starts hidden. */
  object3D: THREE.Object3D;
  /** Default false. */
  enabled: boolean;
  /** The mandatory interpretive chip text. */
  readonly label: string;
  setEnabled(on: boolean): void;
  /** Optional slow drift so the strata are not perfectly static when shown. */
  update(elapsedS: number): void;
  dispose(): void;
}

const VERT = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const FRAG = /* glsl */ `
  precision mediump float;
  varying vec2 vUv;
  uniform vec3 uSurface;
  uniform vec3 uDeep;
  uniform float uStrata;
  uniform float uOpacity;
  uniform float uTime;
  void main() {
    // Vertical gradient from surface (v=1) to deep (v=0).
    vec3 base = mix(uDeep, uSurface, vUv.y);
    // Soft stratified banding with a slow vertical drift.
    float band = sin((vUv.y * uStrata + uTime * 0.05) * 6.2831853);
    float strat = 0.5 + 0.5 * band;
    float a = uOpacity * (0.35 + 0.65 * strat);
    gl_FragColor = vec4(base, a);
  }
`;

/**
 * Build the interpretive ocean layer. Disabled by default; the returned object3D
 * is hidden until setEnabled(true). Keep it minimal and self-contained.
 */
export function createInterpretiveOceanLayer(
  opts: InterpretiveOceanOptions = {},
): InterpretiveOceanLayer {
  const width = opts.width ?? 200;
  const height = opts.height ?? 60;
  const strata = opts.strata ?? 6;
  const opacity = opts.opacity ?? 0.12;
  const surfaceColor = new THREE.Color(opts.surfaceColor ?? "#2e6f9e");
  const deepColor = new THREE.Color(opts.deepColor ?? "#06222b");

  const geometry = new THREE.PlaneGeometry(width, height);
  const material = new THREE.ShaderMaterial({
    vertexShader: VERT,
    fragmentShader: FRAG,
    transparent: true,
    depthWrite: false,
    depthTest: true,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    uniforms: {
      uSurface: { value: surfaceColor },
      uDeep: { value: deepColor },
      uStrata: { value: strata },
      uOpacity: { value: opacity },
      uTime: { value: 0 },
    },
  });

  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.y = -height / 2;
  mesh.renderOrder = 10; // draw additively after opaque scene

  const group = new THREE.Group();
  group.name = "interpretive-ocean-layer";
  group.add(mesh);
  group.visible = false; // default-off

  return {
    object3D: group,
    enabled: false,
    label: INTERPRETIVE_OCEAN_LABEL,
    setEnabled(on: boolean) {
      this.enabled = on;
      group.visible = on;
    },
    update(elapsedS: number) {
      material.uniforms.uTime.value = elapsedS;
    },
    dispose() {
      geometry.dispose();
      material.dispose();
    },
  };
}
