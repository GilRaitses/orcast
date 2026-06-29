// Depth-driven ocean water for the Salish Sea twin (water2, mini-wave W2.5),
// rewritten for WATER-FX (WFX) as the single merged R01+R03+R09+R10+R06+R02
// color-path edit. See .cca/catalogue/O0/20260628_water-fx/research/
// SYNTHESIS_water_fx.md section 4 for the merge order and SIGN_OFF.md for the
// ten ratified decisions this honors.
//
// What this module does. A depth pre-pass renders the opaque scene (terrain
// tiles, water hidden) into a render target carrying BOTH a color attachment and
// a DepthTexture. The water fragment shader samples that depth at its own screen
// fragment, reconstructs the seabed WORLD position via the inverse view-
// projection, and computes the vertical water column thickness from the surface
// plane at Y = level. That column drives a per-channel Beer-Lambert body color
// and the alpha; the already-rendered opaque color attachment is reused as the
// refracted seabed color, so the seabed read is nearly free. A GGX specular lobe
// with a Schlick Fresnel toward a reflected-sky gradient replaces the old sub-
// pixel glitter, and a soft shoreline feather plus a phase-coupled foam run-up
// keep the land-never-washed invariant.
//
// HONESTY. Every lever here changes how the water and sky LOOK and asserts no
// measured depth, color, or sea state. The seabed the water reads stays the
// modeled CUDEM topobathy, labeled modeled, not measured. The absorption,
// refraction, specular, foam, and detail ripple are rendering, not soundings.
//
// The merged color path, in SYNTHESIS section 4 order:
//   1. Per-channel Beer-Lambert body color (R09). transmittance =
//      exp(-(uAbsorption / uDepthColorScale) * column). With uAbsorption =
//      vec3(1.0) and uRefractStrength = 0 this reproduces the prior monochrome
//      two-stop frame EXACTLY, for a clean A/B. Coefficients and deep tint from
//      the signed-off green-survives Salish optics (R11): uAbsorption ~ {3,1,3},
//      deep tint turbid green.
//   2. Seabed refraction (R10 Rec A). The discarded opaque color attachment is
//      bound as uSceneColor and read at a normal-offset screen UV with a depth
//      guard, so shallow water reveals the refracted seabed and deep water fades
//      to the deep tint by transmittance. The color attachment uses linear
//      filtering for this read.
//   3. Energy-conserving GGX specular + Schlick Fresnel at F0 0.02 (R01),
//      mixing toward a reflected-sky gradient (uSkyHorizon..uSkyZenith) that the
//      R03 PMREM env sample later swaps into behind the same seam. Roughness
//      grows with screen-space normal variance to kill the sub-pixel sparkle.
//   4. Soft shoreline feather (R10 Rec B) + phase-coupled foam run-up (R06),
//      both reusing `column` and the Gerstner long-wave phase, both zero at the
//      waterline so land is never washed.
//   5. Vertex (R02): the sub-Nyquist Gerstner waves are dropped, amplitude and
//      steepness lowered for a sheltered sea, and a detail normal (a sampled
//      KTX2 tiling map when provided, else a procedural value-noise fallback)
//      carries the fine ripple the 0.55 km mesh quad cannot.
//
// New uniforms are exposed as public Water2Options (uAbsorption, uSceneColor,
// uRefractStrength, uContactSoftness, uRunup, uRoughness, sky-gradient stops).
// The option object is constructed in SalishScene.tsx, so wiring those feeds is
// a later gated convergence-file edit (SYNTHESIS section 6); this module only
// exposes the levers and ships safe defaults.
//
// Built only on `three`. No new dependency. The per-frame pre-pass and resize
// live in the caller (SalishScene.tsx and the /water sandbox), so this module
// stays framework-free.

import * as THREE from "three";

export interface Water2Options {
  /** Plane width in scene units (east-west). Default 192 (SCENE_WIDTH*1.6). */
  width?: number;
  /** Plane depth in scene units (north-south). Default 144. */
  depth?: number;
  /** Subdivisions per axis; higher = smoother waves, more verts. Default 180. */
  segments?: number;
  /** Sea-level (water surface) Y in scene units. Default 0. */
  level?: number;
  /** Shallow water tint. Default Salish shallow green (#4f8c79, R11). */
  colorShallow?: THREE.Color;
  /** Intrinsic deep water tint the transmittance fades toward. Default turbid green (#13302b, R11). */
  colorDeep?: THREE.Color;
  /** Foam color near the shoreline. Default near-white. */
  colorFoam?: THREE.Color;
  /** Legacy single sky color; also the default reflected-sky horizon stop. */
  skyColor?: THREE.Color;
  /** Reflected-sky gradient horizon stop. Default = skyColor. */
  skyHorizon?: THREE.Color;
  /** Reflected-sky gradient zenith stop. Default deeper marine blue. */
  skyZenith?: THREE.Color;
  /** Unit vector pointing toward the sun (from makeSun().direction). */
  sunDirection?: THREE.Vector3;
  /** Peak wave amplitude in scene units. Default 0.26 (sheltered sea). */
  amplitude?: number;
  /** Wave animation speed multiplier. Default 1. */
  speed?: number;
  /**
   * Column thickness (scene units) over which the COLOR ramp goes shallow->deep.
   * Acts as the green e-folding length: divides uAbsorption so the per-channel
   * extinction is uAbsorption/uDepthColorScale. Default 0.42 (sandbox-tuned).
   */
  depthColorScale?: number;
  /**
   * Column thickness (scene units) over which ALPHA ramps 0->opaque. Default 0.34.
   */
  depthAlphaScale?: number;
  /** Column thickness (scene units) of the near-shore foam band. Default 0.06. */
  foamDepth?: number;
  /** Max water opacity for deep channels in [0,1]. Default 0.95. */
  maxOpacity?: number;
  /** Fresnel sky-reflection strength in [0,1]. Default 0.45. */
  fresnelStrength?: number;
  /**
   * Per-channel absorption (inverse, divided by uDepthColorScale). vec3(1.0)
   * reproduces the monochrome two-stop frame. Signed-off green-survives Salish
   * value is ~{3,1,3} (R11): green penetrates deepest, blue dies first.
   * Default vec3(1.0) for a clean A/B until the integrate wave wires {3,1,3}.
   */
  absorption?: THREE.Vector3;
  /**
   * Seabed refraction strength (screen-UV offset scale). 0 disables refraction
   * and reproduces the prior body color exactly. Default 0.035.
   */
  refractStrength?: number;
  /** Base surface roughness for the GGX lobe in [0.02,1]. Default 0.12. */
  roughness?: number;
  /** Phase-coupled foam run-up: how far the outer foam band widens. Default 0.6. */
  runup?: number;
  /** Soft shoreline contact feather width (scene units of column). Default 0.06. */
  contactSoftness?: number;
  /** Optional tiling detail normal map (KTX2/PNG). Procedural fallback if absent. */
  detailNormalMap?: THREE.Texture;
  /** Detail ripple UV tiling scale. Default 0.5. */
  detailScale?: number;
  /** Detail ripple normal strength in [0,1]. Default 0.5. */
  detailStrength?: number;
  /**
   * Render side. Default FrontSide (the surface vanishes from below). Pass
   * DoubleSide for a dive view; the shader renders a turbid-green underside.
   */
  side?: THREE.Side;
}

export interface Water2Handle {
  /** The renderable water mesh; add it to the scene / r3f tree. */
  mesh: THREE.Mesh;
  /** The shader material (exposed for advanced tweaks / tuning). */
  material: THREE.ShaderMaterial;
  /** The opaque-scene render target the water samples (color + depth). */
  depthTarget: THREE.WebGLRenderTarget;
  /**
   * Render the opaque scene (color + depth) into the render target with the
   * water mesh hidden, so the water shader can read both the seabed depth and
   * the seabed color beneath each fragment. Call once per frame BEFORE the main
   * render (e.g. in a priority-0 useFrame, which runs ahead of r3f's render).
   */
  renderDepthPrepass(
    renderer: THREE.WebGLRenderer,
    scene: THREE.Scene,
    camera: THREE.PerspectiveCamera,
  ): void;
  /**
   * Advance the animation and refresh the camera-dependent uniforms (inverse
   * view-projection for depth reconstruction). Pass elapsed seconds and the
   * active camera. Optionally retarget the sun.
   */
  update(elapsedSeconds: number, camera: THREE.Camera, sunDirection?: THREE.Vector3): void;
  /** Resize the render target to match the drawing buffer (CSS size * dpr). */
  setSize(widthCss: number, heightCss: number, pixelRatio: number): void;
  /** Update the sun direction used for specular. */
  setSunDirection(dir: THREE.Vector3): void;
  /**
   * Drive the distance fog from the live scene fog so the far water dissolves
   * into the horizon haze. Pass null to disable. Density matches a FogExp2.
   */
  setFog(fog: { color: THREE.Color; density: number } | null): void;
  /** Free GPU resources. Call on unmount. */
  dispose(): void;
}

// Signed-off green-survives Salish optics (R11): shallow reads bright teal-green,
// deep fades to a turbid green rather than navy. These are the bare-module
// defaults; SalishScene supplies its own palette via bathyWater2Options, and the
// deep-tint retarget to #13302b on that path is an O0/WS-BATHY coordination item.
const DEFAULT_SHALLOW = new THREE.Color("#4f8c79");
const DEFAULT_DEEP = new THREE.Color("#13302b");
const DEFAULT_FOAM = new THREE.Color("#dfeef5");
const DEFAULT_SKY = new THREE.Color("#9fc4e0");
const DEFAULT_SKY_ZENITH = new THREE.Color("#5a86a8");

const vertexShader = /* glsl */ `
  uniform float uTime;
  uniform float uAmplitude;
  uniform float uSpeed;

  varying vec3 vWorldPosition;
  varying vec3 vWorldNormal;
  varying vec2 vPlanePos;
  varying float vRunupPhase;
  varying float vViewZ; // R04: view-space depth for the distance fog.

  // Gerstner waves: vec4(dirX, dirZ, wavelength, steepness). R02: the sub-Nyquist
  // short waves (the former W4/W5, and the crispest W3) are dropped because at
  // ~0.55 km per mesh quad they alias rather than read; amplitude and steepness
  // are lowered for the sheltered Salish sea. The fine ripple moves to the detail
  // normal in the fragment shader.
  const vec4 W0 = vec4( 1.0,  0.35, 18.0, 0.30);
  const vec4 W1 = vec4(-0.6,  1.0,  11.0, 0.24);
  const vec4 W2 = vec4( 0.8, -0.7,  6.5,  0.18);

  vec3 gerstner(vec4 w, vec2 pos, float amp, inout vec3 normal, out float phase) {
    vec2 dir = normalize(w.xy);
    float wavelength = w.z;
    float steep = w.w;
    float k = 6.2831853 / wavelength;
    float c = sqrt(9.8 / k);
    float a = amp / k;
    float f = k * (dot(dir, pos) - c * uTime * uSpeed);
    phase = f;
    float cosf = cos(f);
    float sinf = sin(f);

    normal.x -= dir.x * (steep * a * k) * cosf;
    normal.z -= dir.y * (steep * a * k) * cosf;
    normal.y -= steep * (a * k) * sinf;

    return vec3(
      dir.x * (a * cosf) * steep,
      a * sinf,
      dir.y * (a * cosf) * steep
    );
  }

  void main() {
    vec3 pos = position;
    vec2 p = position.xy; // plane authored in XY then rotated to XZ by the mesh.
    vPlanePos = p;

    vec3 normal = vec3(0.0, 1.0, 0.0);
    vec3 disp = vec3(0.0);
    float ph0; float phUnused;
    disp += gerstner(W0, p, uAmplitude,        normal, ph0);
    disp += gerstner(W1, p, uAmplitude * 0.7,  normal, phUnused);
    disp += gerstner(W2, p, uAmplitude * 0.45, normal, phUnused);

    // The long-wave (W0) phase drives the foam run-up so the wet band breathes
    // with the swell instead of sitting at a fixed offset (R06).
    vRunupPhase = ph0;

    pos += disp;

    vec4 worldPos = modelMatrix * vec4(pos, 1.0);
    vWorldPosition = worldPos.xyz;
    vWorldNormal = normalize(mat3(modelMatrix) * normalize(normal));

    vec4 mvPosition = viewMatrix * worldPos;
    vViewZ = -mvPosition.z;
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const fragmentShader = /* glsl */ `
  precision highp float;

  uniform sampler2D uDepthTexture;
  uniform sampler2D uSceneColor;     // the discarded opaque color attachment (R10).
  uniform vec2 uResolution;
  uniform mat4 uInverseViewProjection;

  uniform float uWaterLevel;
  uniform float uDepthColorScale;
  uniform float uDepthAlphaScale;
  uniform float uFoamDepth;
  uniform float uMaxOpacity;
  uniform float uFresnelStrength;
  uniform float uRefractStrength;
  uniform float uRoughness;
  uniform float uRunup;
  uniform float uContactSoftness;
  uniform float uDetailScale;
  uniform float uDetailStrength;
  uniform float uHasDetailMap;
  uniform float uTime;
  // Debug: when > 0.5, output the water-column thickness as grayscale.
  uniform float uDebug;
  uniform float uDebugScale;

  uniform vec3 uColorShallow;
  uniform vec3 uColorDeep;
  uniform vec3 uColorFoam;
  uniform vec3 uAbsorption;
  uniform vec3 uSkyHorizon;
  uniform vec3 uSkyZenith;
  uniform vec3 uSunDirection;

  uniform sampler2D uDetailNormalMap;

  varying vec3 vWorldPosition;
  varying vec3 vWorldNormal;
  varying vec2 vPlanePos;
  varying float vRunupPhase;
  varying float vViewZ;

  // R04: self-contained exponential-squared distance fog so the far water
  // dissolves into the horizon haze instead of ending at a hard plane edge.
  // Fed from the live scene.fog by the caller (uFogEnabled gates it; default
  // off so an un-wired integrate is a no-op).
  uniform float uFogEnabled;
  uniform float uFogDensity;
  uniform vec3 uFogColor;

  const float PI = 3.14159265359;

  float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
  }
  float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(hash(i + vec2(0.0, 0.0)), hash(i + vec2(1.0, 0.0)), u.x),
      mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x),
      u.y
    );
  }

  // Procedural detail normal (R02 fallback): two animated value-noise octaves,
  // central-differenced into a tangent-space-ish perturbation of the up normal.
  vec3 detailNormal(vec2 uv) {
    float e = 0.75;
    float h  = noise(uv) * 0.6 + noise(uv * 2.7 + 11.0) * 0.4;
    float hx = noise(uv + vec2(e, 0.0)) * 0.6 + noise((uv + vec2(e, 0.0)) * 2.7 + 11.0) * 0.4;
    float hz = noise(uv + vec2(0.0, e)) * 0.6 + noise((uv + vec2(0.0, e)) * 2.7 + 11.0) * 0.4;
    return normalize(vec3(-(hx - h), 1.0, -(hz - h)));
  }

  // Column thickness (surface plane down to the seabed) from the depth buffer.
  float waterColumn(vec2 uv) {
    float sceneDepth = texture2D(uDepthTexture, uv).x;
    if (sceneDepth >= 0.9999) return 50.0; // open water / horizon: read as deep.
    vec4 ndc = vec4(uv * 2.0 - 1.0, sceneDepth * 2.0 - 1.0, 1.0);
    vec4 worldH = uInverseViewProjection * ndc;
    vec3 seabed = worldH.xyz / worldH.w;
    return uWaterLevel - seabed.y;
  }

  void main() {
    vec2 uv = gl_FragCoord.xy / uResolution;
    float column = max(waterColumn(uv), 0.0);

    if (uDebug > 0.5) {
      float g = clamp(column / max(uDebugScale, 1e-4), 0.0, 1.0);
      gl_FragColor = vec4(vec3(g), 1.0);
      return;
    }

    // Surface normal: the Gerstner normal, perturbed by the detail ripple (a
    // sampled map when provided, else the procedural fallback). The detail
    // fades out over deep open water so it never adds far-field shimmer.
    vec3 n = normalize(vWorldNormal);
    if (gl_FrontFacing == false) n = -n; // dive view: underside faces the camera.
    vec2 duv = vPlanePos * uDetailScale + vec2(uTime * 0.05, -uTime * 0.04);
    vec3 dN;
    if (uHasDetailMap > 0.5) {
      vec3 t = texture2D(uDetailNormalMap, duv).xyz * 2.0 - 1.0;
      dN = normalize(vec3(t.x, max(t.z, 0.2), t.y));
    } else {
      dN = detailNormal(duv);
    }
    float detailFade = 1.0 - smoothstep(2.0, 12.0, column); // strongest over shallows.
    n = normalize(mix(n, normalize(n + dN * uDetailStrength), 0.6 * detailFade + 0.2));

    vec3 viewDir = normalize(cameraPosition - vWorldPosition);

    // --- Underside (dive view): a turbid-green ceiling brightening toward the
    // Snell window. The full underside material (TIR, particulate) is the W4
    // R12 module; this is the minimal in-shader read so the dive frame is not
    // empty. -------------------------------------------------------------------
    if (gl_FrontFacing == false) {
      float up = clamp(dot(n, viewDir), 0.0, 1.0);
      float snell = pow(up, 1.5);
      vec3 ceiling = mix(uColorDeep, uSkyHorizon, snell * 0.5);
      gl_FragColor = vec4(ceiling, 0.9);
      return;
    }

    // --- 1. Per-channel Beer-Lambert body color (R09) ------------------------
    // transmittance = exp(-(uAbsorption / uDepthColorScale) * column). With
    // uAbsorption = vec3(1.0) every channel collapses to the prior scalar
    // exp(-column/scale), so the body color matches the old two-stop frame.
    vec3 absorb = uAbsorption / max(uDepthColorScale, 1e-4);
    vec3 transmittance = exp(-absorb * column);

    // --- 2. Seabed refraction (R10 Rec A) ------------------------------------
    // The near-surface in-scatter color the transmittance reveals through. When
    // refraction is on, the discarded opaque color attachment is read at a
    // normal-offset screen UV (guarded so a sample that lands on the sky/horizon
    // or in front of the surface falls back to the straight read).
    vec3 seabed = uColorShallow;
    if (uRefractStrength > 0.0) {
      vec2 offset = n.xz * uRefractStrength * clamp(column, 0.0, 1.5);
      vec2 rUv = clamp(uv + offset, vec2(0.001), vec2(0.999));
      float rDepth = texture2D(uDepthTexture, rUv).x;
      vec2 useUv = (rDepth >= 0.9999) ? uv : rUv;
      seabed = texture2D(uSceneColor, useUv).rgb;
    }
    // Beer-Lambert: seabed radiance attenuates through the column, plus the
    // bulk in-scattered deep tint. Shallow -> seabed shows; deep -> deep tint.
    vec3 base = seabed * transmittance + uColorDeep * (1.0 - transmittance);

    // --- 3. GGX specular + reflected-sky Fresnel (R01) -----------------------
    // Roughness grows with screen-space normal variance to kill the old
    // pow(ndh,600) sub-pixel glitter; derivatives are enabled on the material.
    float nvar = length(fwidth(n));
    float rough = clamp(uRoughness + nvar * 6.0, 0.03, 0.7);
    float a = rough * rough;
    float a2 = a * a;

    vec3 sun = normalize(uSunDirection);
    vec3 H = normalize(sun + viewDir);
    float ndl = max(dot(n, sun), 0.0);
    float ndv = max(dot(n, viewDir), 1e-3);
    float ndh = max(dot(n, H), 0.0);
    float vdh = max(dot(viewDir, H), 0.0);

    // GGX normal distribution.
    float d = ndh * ndh * (a2 - 1.0) + 1.0;
    float D = a2 / max(PI * d * d, 1e-6);
    // Height-correlated Smith visibility.
    float gv = ndl * sqrt(ndv * ndv * (1.0 - a2) + a2);
    float gl = ndv * sqrt(ndl * ndl * (1.0 - a2) + a2);
    float V = 0.5 / max(gv + gl, 1e-5);
    // Schlick Fresnel at F0 0.02 for the specular term.
    float F0 = 0.02;
    float specF = F0 + (1.0 - F0) * pow(1.0 - vdh, 5.0);
    float specular = D * V * specF * ndl; // energy-conserving, bounded by NoL.

    // View Fresnel toward the reflected-sky gradient (the R03 PMREM seam).
    float fres = F0 + (1.0 - F0) * pow(1.0 - ndv, 5.0);
    vec3 refl = reflect(-viewDir, n);
    float skyMix = clamp(refl.y * 0.5 + 0.5, 0.0, 1.0);
    vec3 skyRefl = mix(uSkyHorizon, uSkyZenith, pow(skyMix, 1.5));

    // --- 4. Soft shoreline feather + phase-coupled foam run-up (R10/R06) ------
    // Contact feather: a soft dissolve at the waterline (0 at column 0) so the
    // shoreline is not a hard edge. Land is never washed.
    float contact = smoothstep(0.0, max(uContactSoftness, 1e-4), column);

    // Foam: a thin band just offshore whose OUTER edge breathes with the W0
    // swell phase (run-up). The inner edge stays pinned at 0 so the foam never
    // crosses the waterline onto land.
    float runPhase = sin(vRunupPhase) * 0.5 + 0.5;
    float bandOuter = uFoamDepth * (1.0 + uRunup * runPhase);
    float fmid = uFoamDepth * 0.5;
    float foam =
      smoothstep(0.0, fmid, column) * (1.0 - smoothstep(fmid, max(bandOuter, fmid + 1e-3), column));
    float foamNoise =
      noise(vPlanePos * 1.6 + vec2(uTime * 0.6, uTime * 0.35)) * 0.6 +
      noise(vPlanePos * 4.0 - vec2(uTime * 0.4, uTime * 0.5)) * 0.4;
    foam *= 0.45 + 0.55 * foamNoise;

    // --- Compose -------------------------------------------------------------
    vec3 sunColor = vec3(1.0, 0.97, 0.9);
    vec3 color = base * (0.55 + 0.45 * ndl);
    color = mix(color, skyRefl, fres * uFresnelStrength);
    color += sunColor * specular;
    color = mix(color, uColorFoam, clamp(foam, 0.0, 1.0));

    // Alpha: depth-driven core + a little Fresnel rim + the foam line, dissolved
    // softly at the shoreline by the contact feather.
    float depthAlpha = (1.0 - exp(-column / max(uDepthAlphaScale, 1e-4))) * uMaxOpacity;
    float alpha = clamp(depthAlpha + fres * 0.18 + foam * 0.9, 0.0, 1.0) * contact;

    // R04: dissolve the far water into the horizon haze (rgb only; alpha keeps
    // the depth read). Softens the open-water horizon seam.
    float fogFactor = uFogEnabled * (1.0 - exp(-uFogDensity * uFogDensity * vViewZ * vViewZ));
    color = mix(color, uFogColor, clamp(fogFactor, 0.0, 1.0));

    gl_FragColor = vec4(color, alpha);
  }
`;

/**
 * Build the depth-driven ocean surface. Pure factory: it allocates Three.js
 * objects (mesh, material, render target) but mutates no scene. The caller adds
 * `handle.mesh`, runs `handle.renderDepthPrepass(...)` then `handle.update(...)`
 * each frame, and `handle.setSize(...)` on viewport change.
 */
export function makeWater2(opts: Water2Options = {}): Water2Handle {
  const width = opts.width ?? 192;
  const depth = opts.depth ?? 144;
  const segments = opts.segments ?? 180;
  const level = opts.level ?? 0;

  const geometry = new THREE.PlaneGeometry(width, depth, segments, segments);

  // Render target: a LINEAR-filtered color attachment (R10: reused as the
  // refracted seabed color) plus a DepthTexture the water shader samples for the
  // column. The depth texture stays nearest; only the color read is linear.
  const depthTexture = new THREE.DepthTexture(1, 1);
  depthTexture.type = THREE.UnsignedIntType;
  depthTexture.format = THREE.DepthFormat;
  depthTexture.minFilter = THREE.NearestFilter;
  depthTexture.magFilter = THREE.NearestFilter;

  const depthTarget = new THREE.WebGLRenderTarget(1, 1, {
    minFilter: THREE.LinearFilter,
    magFilter: THREE.LinearFilter,
    depthTexture,
    depthBuffer: true,
    stencilBuffer: false,
  });

  const skyHorizon = (opts.skyHorizon ?? opts.skyColor ?? DEFAULT_SKY).clone();
  const skyZenith = (opts.skyZenith ?? DEFAULT_SKY_ZENITH).clone();
  const detailMap = opts.detailNormalMap ?? null;
  if (detailMap) {
    detailMap.wrapS = THREE.RepeatWrapping;
    detailMap.wrapT = THREE.RepeatWrapping;
  }

  const material = new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    transparent: true,
    depthWrite: false,
    side: opts.side ?? THREE.FrontSide,
    // R01: fwidth() in the roughness term needs the derivatives extension under
    // GLSL ES 1.0 (no-op on WebGL2, where derivatives are core).
    extensions: { derivatives: true } as THREE.ShaderMaterialParameters["extensions"],
    uniforms: {
      uTime: { value: 0 },
      uAmplitude: { value: opts.amplitude ?? 0.26 },
      uSpeed: { value: opts.speed ?? 1 },
      uDepthTexture: { value: depthTexture },
      uSceneColor: { value: depthTarget.texture },
      uResolution: { value: new THREE.Vector2(1, 1) },
      uInverseViewProjection: { value: new THREE.Matrix4() },
      uWaterLevel: { value: level },
      uDepthColorScale: { value: opts.depthColorScale ?? 0.42 },
      uDepthAlphaScale: { value: opts.depthAlphaScale ?? 0.34 },
      uFoamDepth: { value: opts.foamDepth ?? 0.06 },
      uMaxOpacity: { value: opts.maxOpacity ?? 0.95 },
      uFresnelStrength: { value: opts.fresnelStrength ?? 0.45 },
      uRefractStrength: { value: opts.refractStrength ?? 0.035 },
      uRoughness: { value: opts.roughness ?? 0.12 },
      uRunup: { value: opts.runup ?? 0.6 },
      uContactSoftness: { value: opts.contactSoftness ?? 0.06 },
      uDetailScale: { value: opts.detailScale ?? 0.5 },
      uDetailStrength: { value: opts.detailStrength ?? 0.5 },
      uHasDetailMap: { value: detailMap ? 1 : 0 },
      uDetailNormalMap: { value: detailMap },
      uDebug: { value: 0 },
      uDebugScale: { value: 1.0 },
      uFogEnabled: { value: 0 },
      uFogDensity: { value: 0.012 },
      uFogColor: { value: new THREE.Color("#9fb8cc") },
      uColorShallow: { value: (opts.colorShallow ?? DEFAULT_SHALLOW).clone() },
      uColorDeep: { value: (opts.colorDeep ?? DEFAULT_DEEP).clone() },
      uColorFoam: { value: (opts.colorFoam ?? DEFAULT_FOAM).clone() },
      uAbsorption: { value: (opts.absorption ?? new THREE.Vector3(1, 1, 1)).clone() },
      uSkyHorizon: { value: skyHorizon },
      uSkyZenith: { value: skyZenith },
      uSunDirection: {
        value: (opts.sunDirection ?? new THREE.Vector3(0.4, 0.8, 0.4)).clone().normalize(),
      },
    },
  });

  const mesh = new THREE.Mesh(geometry, material);
  mesh.rotation.x = -Math.PI / 2; // author plane in XY, rotate to XZ horizontal.
  mesh.position.y = level;
  mesh.renderOrder = 1;
  mesh.name = "water2-depth-driven";
  mesh.frustumCulled = false;

  const invViewProj = material.uniforms.uInverseViewProjection.value as THREE.Matrix4;
  const resolution = material.uniforms.uResolution.value as THREE.Vector2;

  return {
    mesh,
    material,
    depthTarget,
    renderDepthPrepass(renderer, scene, camera) {
      const prevTarget = renderer.getRenderTarget();
      const wasVisible = mesh.visible;
      mesh.visible = false;
      renderer.setRenderTarget(depthTarget);
      renderer.render(scene, camera);
      renderer.setRenderTarget(prevTarget);
      mesh.visible = wasVisible;
    },
    update(elapsedSeconds, camera, sunDirection) {
      material.uniforms.uTime.value = elapsedSeconds;
      camera.updateMatrixWorld();
      // inverse(P * V) = inverse(V) * inverse(P) = matrixWorld * projInverse.
      camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();
      invViewProj.multiplyMatrices(camera.matrixWorld, camera.projectionMatrixInverse);
      if (sunDirection) {
        (material.uniforms.uSunDirection.value as THREE.Vector3).copy(sunDirection).normalize();
      }
    },
    setSize(widthCss, heightCss, pixelRatio) {
      const w = Math.max(1, Math.round(widthCss * pixelRatio));
      const h = Math.max(1, Math.round(heightCss * pixelRatio));
      depthTarget.setSize(w, h);
      resolution.set(w, h);
    },
    setSunDirection(dir) {
      (material.uniforms.uSunDirection.value as THREE.Vector3).copy(dir).normalize();
    },
    setFog(fog) {
      material.uniforms.uFogEnabled.value = fog ? 1 : 0;
      if (fog) {
        material.uniforms.uFogDensity.value = fog.density;
        (material.uniforms.uFogColor.value as THREE.Color).copy(fog.color);
      }
    },
    dispose() {
      geometry.dispose();
      material.dispose();
      depthTexture.dispose();
      depthTarget.dispose();
    },
  };
}
