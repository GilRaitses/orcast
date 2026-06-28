// Depth-driven ocean water for the Salish Sea twin (water2, mini-wave W2.5).
//
// Replaces the agent-A flat translucent plane (realism/water.ts), whose alpha
// was UNIFORM across the whole extent and therefore washed a flat blue over all
// low terrain and bathymetry. Here the water alpha and color are driven by the
// WATER COLUMN THICKNESS at each fragment, read from the opaque scene depth
// buffer (Beer-Lambert). Where terrain sits at or above the water surface the
// water goes (near) transparent and reveals the land or shallow seafloor; where
// the column is deep the water becomes opaque teal/blue. Shoreline foam appears
// where the column is thin, plus Fresnel sky reflection and sun glitter. The
// existing sum-of-Gerstner displacement is kept so the surface still ripples.
//
// Technique (see research/R4_ocean_water_rendering.md):
//   1. A depth pre-pass renders the opaque scene (terrain tiles, with the water
//      mesh hidden) into a WebGLRenderTarget that carries a DepthTexture.
//   2. The water fragment shader samples that depth texture at its own
//      screen-space fragment, reconstructs the seabed WORLD position via the
//      inverse view-projection matrix, and computes the vertical water column
//      thickness relative to the water surface plane at Y = level.
//   3. Beer-Lambert maps that thickness to alpha and to a shallow->deep color
//      ramp; a thin near-shore band gets animated foam.
//
// The water plane stays at scene Y = 0 (the visible waterline that the streamed
// tiles already poke through). Column is measured from that plane, so the datum
// the depth ramp uses is exactly the surface the operator sees.
//
// Built only on `three` (already in web/package.json). No new dependency. The
// react-three-fiber wiring (the per-frame pre-pass and resize) lives in the
// caller (SalishScene.tsx and the /water sandbox), so this module stays
// framework-free, mirroring the agent-A makeWater() factory style.

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
  /** Shallow water tint. Default palette WATER_SHALLOW (#2e6f9e). */
  colorShallow?: THREE.Color;
  /** Deep water tint. Default palette WATER_DEEP (#0a2540). */
  colorDeep?: THREE.Color;
  /** Foam color near the shoreline. Default near-white. */
  colorFoam?: THREE.Color;
  /** Sky/horizon color the Fresnel term reflects toward. Default marine haze. */
  skyColor?: THREE.Color;
  /** Unit vector pointing toward the sun (from makeSun().direction). */
  sunDirection?: THREE.Vector3;
  /** Peak wave amplitude in scene units. Default 0.32. */
  amplitude?: number;
  /** Wave animation speed multiplier. Default 1. */
  speed?: number;
  /**
   * Column thickness (scene units) over which the COLOR ramp goes shallow->deep.
   * Larger = the teal shallow tint persists deeper; smaller = navy sooner.
   * Default 0.3 (tuned in the /water sandbox against the full-extent tileset,
   * where deep channels run about 1.0 scene units below the surface).
   */
  depthColorScale?: number;
  /**
   * Column thickness (scene units) over which ALPHA ramps 0->opaque. Larger =
   * water stays clearer over shallows/moderate depth (revealing the seabed);
   * smaller = opaque sooner. Default 0.3 (sandbox-tuned).
   */
  depthAlphaScale?: number;
  /** Column thickness (scene units) of the near-shore foam band. Default 0.08. */
  foamDepth?: number;
  /** Max water opacity for deep channels in [0,1]. Default 0.96. */
  maxOpacity?: number;
  /** Fresnel sky-reflection strength in [0,1]. Default 0.5. */
  fresnelStrength?: number;
}

export interface Water2Handle {
  /** The renderable water mesh; add it to the scene / r3f tree. */
  mesh: THREE.Mesh;
  /** The shader material (exposed for advanced tweaks / tuning). */
  material: THREE.ShaderMaterial;
  /** The opaque-scene depth target the water samples. */
  depthTarget: THREE.WebGLRenderTarget;
  /**
   * Render the opaque scene depth into the depth target with the water mesh
   * hidden, so the water shader can read the seabed depth beneath each fragment.
   * Call once per frame BEFORE the main render (e.g. in a priority-0 useFrame,
   * which runs ahead of r3f's automatic render).
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
  /** Resize the depth target to match the drawing buffer (CSS size * dpr). */
  setSize(widthCss: number, heightCss: number, pixelRatio: number): void;
  /** Update the sun direction used for glitter / specular. */
  setSunDirection(dir: THREE.Vector3): void;
  /** Free GPU resources. Call on unmount. */
  dispose(): void;
}

const DEFAULT_SHALLOW = new THREE.Color("#2e6f9e");
const DEFAULT_DEEP = new THREE.Color("#0a2540");
const DEFAULT_FOAM = new THREE.Color("#dfeef5");
const DEFAULT_SKY = new THREE.Color("#9fc4e0");

const vertexShader = /* glsl */ `
  uniform float uTime;
  uniform float uAmplitude;
  uniform float uSpeed;

  varying vec3 vWorldPosition;
  varying vec3 vWorldNormal;
  varying vec2 vPlanePos;

  // Gerstner waves: vec4(dirX, dirZ, wavelength, steepness). The first four
  // match the agent-A v1 surface; the last two add higher-frequency crispness.
  const vec4 W0 = vec4( 1.0,  0.35, 18.0, 0.42);
  const vec4 W1 = vec4(-0.6,  1.0,  11.0, 0.34);
  const vec4 W2 = vec4( 0.8, -0.7,  6.5,  0.28);
  const vec4 W3 = vec4(-0.2, -1.0,  3.3,  0.20);
  const vec4 W4 = vec4( 0.5,  0.9,  2.1,  0.16);
  const vec4 W5 = vec4(-0.9,  0.2,  1.3,  0.12);

  vec3 gerstner(vec4 w, vec2 pos, float amp, inout vec3 normal) {
    vec2 dir = normalize(w.xy);
    float wavelength = w.z;
    float steep = w.w;
    float k = 6.2831853 / wavelength;
    float c = sqrt(9.8 / k);
    float a = amp / k;
    float f = k * (dot(dir, pos) - c * uTime * uSpeed);
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
    // Plane authored in XY then rotated to XZ by the mesh; sample in plane space.
    vec2 p = position.xy;
    vPlanePos = p;

    vec3 normal = vec3(0.0, 1.0, 0.0);
    vec3 disp = vec3(0.0);
    disp += gerstner(W0, p, uAmplitude,        normal);
    disp += gerstner(W1, p, uAmplitude * 0.8,  normal);
    disp += gerstner(W2, p, uAmplitude * 0.6,  normal);
    disp += gerstner(W3, p, uAmplitude * 0.4,  normal);
    disp += gerstner(W4, p, uAmplitude * 0.25, normal);
    disp += gerstner(W5, p, uAmplitude * 0.18, normal);

    pos += disp;

    vec4 worldPos = modelMatrix * vec4(pos, 1.0);
    vWorldPosition = worldPos.xyz;
    vWorldNormal = normalize(mat3(modelMatrix) * normalize(normal));

    gl_Position = projectionMatrix * viewMatrix * worldPos;
  }
`;

const fragmentShader = /* glsl */ `
  precision highp float;

  uniform sampler2D uDepthTexture;
  uniform vec2 uResolution;
  uniform mat4 uInverseViewProjection;

  uniform float uWaterLevel;
  uniform float uDepthColorScale;
  uniform float uDepthAlphaScale;
  uniform float uFoamDepth;
  uniform float uMaxOpacity;
  uniform float uFresnelStrength;
  uniform float uTime;
  // Debug: when > 0.5, output the water-column thickness as grayscale (white =
  // uDebugScale scene units or deeper). Used in the sandbox to read the actual
  // depth distribution while tuning; off (0) in the live scene.
  uniform float uDebug;
  uniform float uDebugScale;

  uniform vec3 uColorShallow;
  uniform vec3 uColorDeep;
  uniform vec3 uColorFoam;
  uniform vec3 uSkyColor;
  uniform vec3 uSunDirection;

  varying vec3 vWorldPosition;
  varying vec3 vWorldNormal;
  varying vec2 vPlanePos;

  // Cheap value noise for foam / glitter break-up.
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

  void main() {
    // Screen-space UV of this fragment, matching the depth target resolution.
    vec2 uv = gl_FragCoord.xy / uResolution;

    // Reconstruct the seabed WORLD position from the opaque-scene depth buffer.
    float sceneDepth = texture2D(uDepthTexture, uv).x; // window-space [0,1]
    float column;
    if (sceneDepth >= 0.9999) {
      // No opaque geometry behind this fragment (open water / horizon): treat as
      // deep so it reads as solid blue rather than clearing to nothing.
      column = 50.0;
    } else {
      vec4 ndc = vec4(uv * 2.0 - 1.0, sceneDepth * 2.0 - 1.0, 1.0);
      vec4 worldH = uInverseViewProjection * ndc;
      vec3 seabed = worldH.xyz / worldH.w;
      // Vertical water column from the surface plane down to the seabed. Terrain
      // at/above the surface yields <= 0 -> the water clears and land shows.
      column = uWaterLevel - seabed.y;
    }
    column = max(column, 0.0);

    if (uDebug > 0.5) {
      float g = clamp(column / max(uDebugScale, 1e-4), 0.0, 1.0);
      gl_FragColor = vec4(vec3(g), 1.0);
      return;
    }

    vec3 n = normalize(vWorldNormal);
    vec3 viewDir = normalize(cameraPosition - vWorldPosition);

    // Beer-Lambert: color and alpha grow with column thickness.
    float colorT = 1.0 - exp(-column / max(uDepthColorScale, 1e-4));
    float depthAlpha = 1.0 - exp(-column / max(uDepthAlphaScale, 1e-4));
    depthAlpha *= uMaxOpacity;

    vec3 base = mix(uColorShallow, uColorDeep, colorT);

    // Shoreline foam: a thin band just offshore. Zero exactly at the waterline
    // (so land never gets a foam wash) and zero again past the band.
    float fmid = uFoamDepth * 0.5;
    float foam =
      smoothstep(0.0, fmid, column) * (1.0 - smoothstep(fmid, uFoamDepth, column));
    float foamNoise =
      noise(vPlanePos * 1.6 + vec2(uTime * 0.6, uTime * 0.35)) * 0.6 +
      noise(vPlanePos * 4.0 - vec2(uTime * 0.4, uTime * 0.5)) * 0.4;
    foam *= 0.45 + 0.55 * foamNoise;

    // Fresnel sky reflection: grazing angles brighten toward the sky color.
    float fres = pow(1.0 - max(dot(n, viewDir), 0.0), 5.0);

    // Sun specular + sharper glitter, broken up by surface noise.
    vec3 sun = normalize(uSunDirection);
    vec3 halfVec = normalize(sun + viewDir);
    float ndh = max(dot(n, halfVec), 0.0);
    float spec = pow(ndh, 90.0);
    float glitter = pow(ndh, 600.0) *
      step(0.55, noise(vPlanePos * 7.0 + vec2(uTime * 0.9, -uTime * 0.7)));
    float diff = clamp(dot(n, sun), 0.0, 1.0);

    vec3 color = base * (0.6 + 0.4 * diff);
    color = mix(color, uSkyColor, fres * uFresnelStrength);
    color += vec3(1.0, 0.97, 0.9) * (spec * 0.8 + glitter * 1.4);
    color = mix(color, uColorFoam, clamp(foam, 0.0, 1.0));

    // Alpha: depth-driven core + a little Fresnel rim + the foam line. Clamped so
    // the thinnest water still approaches fully transparent and reveals land.
    float alpha = clamp(depthAlpha + fres * 0.18 + foam * 0.9, 0.0, 1.0);

    gl_FragColor = vec4(color, alpha);
  }
`;

/**
 * Build the depth-driven ocean surface. Pure factory: it allocates Three.js
 * objects (mesh, material, depth render target) but mutates no scene. The caller
 * adds `handle.mesh`, runs `handle.renderDepthPrepass(...)` then `handle.update(...)`
 * each frame, and `handle.setSize(...)` on viewport change.
 */
export function makeWater2(opts: Water2Options = {}): Water2Handle {
  const width = opts.width ?? 192;
  const depth = opts.depth ?? 144;
  const segments = opts.segments ?? 180;
  const level = opts.level ?? 0;

  const geometry = new THREE.PlaneGeometry(width, depth, segments, segments);

  // Depth target: a small color attachment (unused) plus a DepthTexture the
  // water shader samples. Sized 1x1 until setSize() runs from the caller.
  const depthTexture = new THREE.DepthTexture(1, 1);
  depthTexture.type = THREE.UnsignedIntType;
  depthTexture.format = THREE.DepthFormat;
  depthTexture.minFilter = THREE.NearestFilter;
  depthTexture.magFilter = THREE.NearestFilter;

  const depthTarget = new THREE.WebGLRenderTarget(1, 1, {
    minFilter: THREE.NearestFilter,
    magFilter: THREE.NearestFilter,
    depthTexture,
    depthBuffer: true,
    stencilBuffer: false,
  });

  const material = new THREE.ShaderMaterial({
    vertexShader,
    fragmentShader,
    transparent: true,
    depthWrite: false,
    side: THREE.FrontSide,
    uniforms: {
      uTime: { value: 0 },
      uAmplitude: { value: opts.amplitude ?? 0.32 },
      uSpeed: { value: opts.speed ?? 1 },
      uDepthTexture: { value: depthTexture },
      uResolution: { value: new THREE.Vector2(1, 1) },
      uInverseViewProjection: { value: new THREE.Matrix4() },
      uWaterLevel: { value: level },
      uDepthColorScale: { value: opts.depthColorScale ?? 0.3 },
      uDepthAlphaScale: { value: opts.depthAlphaScale ?? 0.3 },
      uFoamDepth: { value: opts.foamDepth ?? 0.08 },
      uMaxOpacity: { value: opts.maxOpacity ?? 0.96 },
      uFresnelStrength: { value: opts.fresnelStrength ?? 0.5 },
      uDebug: { value: 0 },
      uDebugScale: { value: 1.0 },
      uColorShallow: { value: (opts.colorShallow ?? DEFAULT_SHALLOW).clone() },
      uColorDeep: { value: (opts.colorDeep ?? DEFAULT_DEEP).clone() },
      uColorFoam: { value: (opts.colorFoam ?? DEFAULT_FOAM).clone() },
      uSkyColor: { value: (opts.skyColor ?? DEFAULT_SKY).clone() },
      uSunDirection: {
        value: (opts.sunDirection ?? new THREE.Vector3(0.4, 0.8, 0.4)).clone().normalize(),
      },
    },
  });

  const mesh = new THREE.Mesh(geometry, material);
  // Author plane in XY, rotate to XZ horizontal (same orientation as agent-A v1).
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.y = level;
  mesh.renderOrder = 1;
  mesh.name = "water2-depth-driven";
  // The depth pre-pass excludes the water by frustum-independent geometry hiding;
  // never let it be culled out of the main render.
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
    dispose() {
      geometry.dispose();
      material.dispose();
      depthTexture.dispose();
      depthTarget.dispose();
    },
  };
}
