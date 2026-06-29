// Promoted interpretive ocean-process layer: the operator's "lava lamp in both
// directions". A stylized double-diffusion / salt-fingering volumetric whose
// vertical placement and band sharpness are driven by a REAL-shaped Salish Sea
// stratification profile (see stratification.ts), rendered as a small set of
// additive, transparent, depth-write-off crossed planes.
//
// HONESTY (locked). Double-diffusive convection and salt fingering are real
// oceanography, but the open Salish basin is usually fresher-over-saltier and
// does not routinely show classic thermohaline staircases (BSW-R09). So this is
// an INTERPRETIVE metaphor grounded in real temperature/salinity structure, NOT
// a map of measured microstructure and NEVER measured orca perception. The
// mandatory chip text and the forbidden-claim guard from interpretiveOceanLayer
// are reused here, not weakened. The honesty stamp follows the R09 userData shape.
//
// COMPUTE-NEUTRAL. This adds NO new full render pass: it is one Group of two
// crossed PlaneGeometry meshes drawn in the existing scene render with additive
// blending, depthWrite:false, renderOrder high. There is NO raymarch, NO second
// render(scene,camera), NO EffectComposer, and it never writes depth, so it
// cannot regress the real WFX water. It defaults to disabled and costs 0 when off.

import * as THREE from "three";
import {
  INTERPRETIVE_OCEAN_LABEL,
  INTERPRETIVE_OCEAN_DETAIL,
  assertNoForbiddenClaim,
} from "./interpretiveOceanLayer";
import {
  analyticHaloclineProfile,
  stratificationToTexture,
  type StratificationProfile,
} from "./stratification";

/** Honesty stamp written to object3D.userData, following the R09 shape. */
export interface OceanProcessHonestyLabel {
  kind: "interpretive";
  measured: false;
  modeledNotMeasured: false;
  label: string;
  dataSources: string[];
  speculativeClaim: string;
}

export interface DoubleDiffusionOptions {
  /** Stratification profile that places the halocline and sets band sharpness. */
  profile?: StratificationProfile;
  /** World width of each plane. */
  width?: number;
  /** Vertical extent (depth span) of the column, world units. */
  height?: number;
  /** World Y of the surface (top of the column). Strata descend from here. */
  surfaceY?: number;
  /** Warm/salty descending plume tint. */
  warmColor?: THREE.ColorRepresentation;
  /** Cold/fresh rising plume tint. */
  coolColor?: THREE.ColorRepresentation;
  /** Peak additive opacity. */
  opacity?: number;
  /** Plume drift speed multiplier (visual only). */
  speed?: number;
  /**
   * World-unit band, just below the surface, over which the plume fades to zero
   * so the additive field dies at the waterline instead of showing a hard band.
   * Part of the scalar surface-Y top-clip fed by `surfaceY`. Default 4.
   */
  surfaceFade?: number;
}

export interface DoubleDiffusionLayer {
  /** Add to the scene; self-contained, starts hidden (default off). */
  object3D: THREE.Object3D;
  /** Default false. */
  enabled: boolean;
  /** Mandatory interpretive chip text (identical to the stub's label). */
  readonly label: string;
  /** Full honesty boundary line the host may show beside the chip. */
  readonly detail: string;
  /** Provenance of the driving stratification profile (for HUD attribution). */
  readonly provenance: string;
  setEnabled(on: boolean): void;
  /** Advance the stylized plume drift. */
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

// Fragment: two opposed advected value-noise fields. Warm/salty noise scrolls
// DOWN, cold/fresh noise scrolls UP. The 1-D stratification texture (sampled by
// depth fraction = 1 - vUv.y) supplies salinity (R), temperature (G), and the
// normalized density-gradient (B). The density-gradient channel brightens the
// strongest mixing interface (the halocline) so the bands sit where the real
// profile is sharpest. No raymarch: this is a flat additive field.
const FRAG = /* glsl */ `
  precision mediump float;
  varying vec2 vUv;
  uniform sampler2D uStrata;   // width x 1 RGBA: R salinity, G temp, B |d(rho)/dz|, A depthFrac
  uniform vec3 uWarm;          // warm/salty descending tint
  uniform vec3 uCool;          // cold/fresh rising tint
  uniform float uOpacity;
  uniform float uTime;
  uniform float uSpeed;
  uniform float uSurfaceY;     // world Y of the real water surface (scalar seam)
  uniform float uColumnHeight; // world height of the column; its top maps to uSurfaceY
  uniform float uSurfaceFade;  // world-unit band over which the plume fades to 0 at the surface

  // Cheap hash-based value noise + 3-octave fbm. No texture, no dependency.
  float hash(vec2 p) {
    p = fract(p * vec2(123.34, 345.45));
    p += dot(p, p + 34.345);
    return fract(p.x * p.y);
  }
  float vnoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
  }
  float fbm(vec2 p) {
    float v = 0.0;
    float amp = 0.5;
    for (int i = 0; i < 3; i++) {
      v += amp * vnoise(p);
      p *= 2.02;
      amp *= 0.5;
    }
    return v;
  }

  void main() {
    float depthFrac = 1.0 - vUv.y;            // 0 surface, 1 deep
    vec4 strat = texture2D(uStrata, vec2(depthFrac, 0.5));
    float salinity = strat.r;                 // 0 fresh .. 1 salty
    float bandSharp = strat.b;                // band sharpness at the halocline (GLSL: 'interface' is reserved)

    float t = uTime * uSpeed;
    // Warm/salty fingers descend; cold/fresh plumes rise. Opposed vertical scroll.
    float down = fbm(vec2(vUv.x * 5.0, vUv.y * 7.0 + t * 0.15));
    float up   = fbm(vec2(vUv.x * 5.0 + 11.0, vUv.y * 7.0 - t * 0.12));

    // Salty water below the halocline favors the descending field; fresher water
    // above favors the rising field. bandSharp boosts contrast at the halocline.
    float warmW = salinity;
    float coolW = 1.0 - salinity;
    float warm = down * warmW;
    float cool = up * coolW;

    vec3 col = uWarm * warm + uCool * cool;
    float a = uOpacity * (warm + cool) * (0.55 + 0.9 * bandSharp);

    // Scalar surface-Y top-clip (R09 depth-aware plume against the real water
    // surface). The column top maps to uSurfaceY, fed by the layer's surfaceY.
    // Never emit a fragment above the surface, and fade the plume to zero across
    // uSurfaceFade just below it so the additive field dies at the waterline
    // instead of showing a hard band. This consumes the surface position
    // read-only; it writes nothing back to the water.
    float worldY = uSurfaceY - uColumnHeight * depthFrac;
    if (worldY > uSurfaceY) discard;
    a *= clamp((uSurfaceY - worldY) / max(uSurfaceFade, 1e-4), 0.0, 1.0);

    gl_FragColor = vec4(col, a);
  }
`;

/**
 * Build the interpretive double-diffusion layer. Disabled by default; the
 * returned object3D is hidden until setEnabled(true). Self-contained: it owns a
 * baked 1-D stratification texture and two crossed additive planes.
 */
export function createDoubleDiffusionLayer(
  opts: DoubleDiffusionOptions = {},
): DoubleDiffusionLayer {
  const profile = opts.profile ?? analyticHaloclineProfile();
  // Guard the provenance string the same way the labels are guarded.
  assertNoForbiddenClaim(INTERPRETIVE_OCEAN_LABEL, INTERPRETIVE_OCEAN_DETAIL, profile.provenance);

  const width = opts.width ?? 200;
  const height = opts.height ?? 70;
  const surfaceY = opts.surfaceY ?? 0;
  const opacity = opts.opacity ?? 0.16;
  const speed = opts.speed ?? 1;
  const surfaceFade = opts.surfaceFade ?? 4;
  const warm = new THREE.Color(opts.warmColor ?? "#c8743c"); // amber-rose, warm/salty
  const cool = new THREE.Color(opts.coolColor ?? "#3fa8b6"); // blue-green, cold/fresh

  const strataTex = stratificationToTexture(profile);

  const material = new THREE.ShaderMaterial({
    vertexShader: VERT,
    fragmentShader: FRAG,
    transparent: true,
    depthWrite: false,
    depthTest: true,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    uniforms: {
      uStrata: { value: strataTex },
      uWarm: { value: warm },
      uCool: { value: cool },
      uOpacity: { value: opacity },
      uTime: { value: 0 },
      uSpeed: { value: speed },
      uSurfaceY: { value: surfaceY },
      uColumnHeight: { value: height },
      uSurfaceFade: { value: surfaceFade },
    },
  });

  // Two crossed planes give a hint of volume from oblique angles without a true
  // volumetric pass. Both share the one material.
  const geometry = new THREE.PlaneGeometry(width, height);
  const planeA = new THREE.Mesh(geometry, material);
  const planeB = new THREE.Mesh(geometry, material);
  planeB.rotation.y = Math.PI / 2;

  // Pre-pass exclusion (R4 on-state seabed-tint fix). The WFX Water2 depth
  // pre-pass renders the whole scene into an OFFSCREEN target with the water
  // hidden, to capture the seabed color and depth the water shader samples. This
  // additive interpretive layer must not tint that seabed color. While the
  // renderer draws into any offscreen target, suppress this layer's color writes,
  // and restore them for the on-screen pass. depthWrite is already false, so with
  // colorWrite off the layer contributes nothing to the pre-pass. When the layer
  // is disabled the group is not visible and these callbacks never fire, so the
  // layer-off frame is byte-for-byte untouched. This reads the render state only,
  // mutating no WFX water, scene.environment, scene.fog, or scene.background.
  const suppressOffscreen = (renderer: THREE.WebGLRenderer) => {
    material.colorWrite = renderer.getRenderTarget() === null;
  };
  const restoreColorWrite = () => {
    material.colorWrite = true;
  };
  planeA.onBeforeRender = suppressOffscreen;
  planeB.onBeforeRender = suppressOffscreen;
  planeA.onAfterRender = restoreColorWrite;
  planeB.onAfterRender = restoreColorWrite;

  const group = new THREE.Group();
  group.name = "interpretive-double-diffusion-layer";
  group.add(planeA);
  group.add(planeB);
  // Column hangs from the surface down by `height`.
  group.position.y = surfaceY - height / 2;
  planeA.renderOrder = 11; // additive, after the opaque scene and the basic stub
  planeB.renderOrder = 11;
  group.visible = false; // default off

  const honesty: OceanProcessHonestyLabel = {
    kind: "interpretive",
    measured: false,
    modeledNotMeasured: false,
    label: INTERPRETIVE_OCEAN_LABEL,
    dataSources: [profile.provenance],
    speculativeClaim: "orca biosonar perception, not measured",
  };
  group.userData.oceanProcessHonestyLabel = honesty;

  return {
    object3D: group,
    enabled: false,
    label: INTERPRETIVE_OCEAN_LABEL,
    detail: INTERPRETIVE_OCEAN_DETAIL,
    provenance: profile.provenance,
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
      strataTex.dispose();
    },
  };
}
