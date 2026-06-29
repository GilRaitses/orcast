"use client";

// WFX (WATER-FX) verification rig, built on the W2.5 depth-driven water sandbox.
//
// Originally a bare water+tiles harness; this rig adds the SalishScene-faithful
// composition needed to visually verify the WATER-FX realism levers WITHOUT
// editing the convergence file (SalishScene.tsx):
//   - a Preetham sky dome owning the background (so "white sky" is reproducible
//     and the exposure fix is provable here),
//   - a renderer toneMappingExposure control (proves the ~0.5 exposure lever),
//   - linear / FogExp2 / off fog modes (proves the FogExp2 horizon retune),
//   - sun time-of-day (sunrise / noon / sunset) for the horizon checks,
//   - camera presets (open water, shoreline, horizon, dive/underwater),
//   - a deterministic freeze + a window.__wfx readout so a headless browser can
//     capture matched before/after frames and read the measured U.
//
// Everything is query-driven so a Playwright capture can set state by navigation.
// Honesty: every lever changes how the water/sky LOOK and asserts no measured
// depth, color, or sea state. The seabed read stays the modeled CUDEM topobathy.

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { useTilesLayer } from "@/lib/scene/tiles";
import { makeSun } from "@/app/components/scene/realism/sun";
import { skyColor } from "@/app/components/scene/realism/atmosphere";
import { makeSkyDome } from "@/lib/scene/decor";
import { applyTerrainStyle } from "@/lib/scene/terrain";
import { SCENE_WIDTH, sceneDepth, type HeightmapBounds } from "@/lib/sceneIntent";
import { makeWater2, type Water2Handle, type Water2Options } from "@/lib/scene/water2";

const FULL_TILESET_URL =
  "https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json";

const TILESET_BOUNDS: HeightmapBounds = {
  min_lat: 48.4,
  max_lat: 48.7,
  min_lng: -123.25,
  max_lng: -122.75,
};

const SCENE_DEPTH = sceneDepth(TILESET_BOUNDS);

// Time-of-day instants (UTC) for the horizon checks. Salish Sea ~48.5N -123W.
// Sunrise/sunset are picked near the solar horizon crossing for late June; noon
// is the pinned SalishScene midday. These drive makeSun + the sky dome together.
const TOD_TIMES: Record<string, Date> = {
  sunrise: new Date("2026-06-27T12:40:00Z"), // ~05:40 PDT, sun low in the NE
  noon: new Date("2026-06-27T20:00:00Z"), // ~13:00 PDT, the SalishScene pin
  sunset: new Date("2026-06-28T04:10:00Z"), // ~21:10 PDT, sun low in the NW
};

// Camera presets (position + look-at target), scene units. fitRadius ~60.
type ViewName = "open" | "shore" | "horizon" | "dive";
const VIEWS: Record<ViewName, { pos: [number, number, number]; target: [number, number, number] }> = {
  open: { pos: [0, 70, 95], target: [0, 0, 0] },
  shore: { pos: [18, 16, 34], target: [10, -1, 8] },
  horizon: { pos: [0, 8, 70], target: [0, 6, -120] },
  dive: { pos: [6, -6, 14], target: [0, 2, -30] },
};

interface Tuning {
  // Existing W2.5 levers.
  depthColorScale: number;
  depthAlphaScale: number;
  foamDepth: number;
  amplitude: number;
  maxOpacity: number;
  fresnelStrength: number;
  debug: number;
  debugScale: number;
  // WFX levers (consumed once depthWater.ts is rewritten; harmless before then).
  absorption: [number, number, number];
  refractStrength: number;
  roughness: number;
  runup: number;
  contactSoftness: number;
  colorShallow: string;
  colorDeep: string;
}

const DEFAULT_TUNING: Tuning = {
  depthColorScale: 0.42,
  depthAlphaScale: 0.34,
  foamDepth: 0.06,
  amplitude: 0.3,
  maxOpacity: 0.95,
  fresnelStrength: 0.45,
  debug: 0,
  debugScale: 1.0,
  absorption: [3.0, 1.0, 3.0],
  refractStrength: 0.035,
  roughness: 0.12,
  runup: 0.6,
  contactSoftness: 0.06,
  colorShallow: "#4f8c79",
  colorDeep: "#13302b",
};

interface RigConfig {
  view: ViewName;
  tod: keyof typeof TOD_TIMES;
  exposure: number;
  fog: "linear" | "exp2" | "off";
  fogDensity: number;
  sky: boolean;
  terrain: boolean;
  freeze: number | null;
  perf: boolean;
  capture: boolean;
}

const DEFAULT_CONFIG: RigConfig = {
  view: "open",
  tod: "noon",
  exposure: 1.0,
  fog: "linear",
  fogDensity: 0.012,
  sky: true,
  terrain: true,
  freeze: null,
  perf: false,
  capture: false,
};

function readConfig(): RigConfig {
  const c = { ...DEFAULT_CONFIG };
  if (typeof window === "undefined") return c;
  const q = new URLSearchParams(window.location.search);
  const num = (k: string, cur: number) => {
    const v = q.get(k);
    const n = v == null ? NaN : parseFloat(v);
    return Number.isFinite(n) ? n : cur;
  };
  const view = q.get("view");
  if (view && view in VIEWS) c.view = view as ViewName;
  const tod = q.get("tod");
  if (tod && tod in TOD_TIMES) c.tod = tod as keyof typeof TOD_TIMES;
  c.exposure = num("exposure", c.exposure);
  const fog = q.get("fog");
  if (fog === "linear" || fog === "exp2" || fog === "off") c.fog = fog;
  c.fogDensity = num("fogDensity", c.fogDensity);
  if (q.get("sky") != null) c.sky = q.get("sky") !== "0";
  if (q.get("terrain") != null) c.terrain = q.get("terrain") !== "0";
  if (q.get("freeze") != null) c.freeze = num("freeze", 8);
  c.perf = q.get("perf") === "1";
  c.capture = q.get("capture") === "1";
  return c;
}

function readTuning(): Tuning {
  const t: Tuning = { ...DEFAULT_TUNING };
  if (typeof window === "undefined") return t;
  const q = new URLSearchParams(window.location.search);
  const num = (k: string, cur: number) => {
    const v = q.get(k);
    const n = v == null ? NaN : parseFloat(v);
    return Number.isFinite(n) ? n : cur;
  };
  t.depthAlphaScale = num("alphaScale", t.depthAlphaScale);
  t.depthColorScale = num("colorScale", t.depthColorScale);
  t.foamDepth = num("foamDepth", t.foamDepth);
  t.amplitude = num("amplitude", t.amplitude);
  t.maxOpacity = num("maxOpacity", t.maxOpacity);
  t.fresnelStrength = num("fresnel", t.fresnelStrength);
  t.debugScale = num("debugScale", t.debugScale);
  t.debug = q.get("debug") === "1" ? 1 : 0;
  t.refractStrength = num("refract", t.refractStrength);
  t.roughness = num("roughness", t.roughness);
  t.runup = num("runup", t.runup);
  t.contactSoftness = num("contact", t.contactSoftness);
  t.absorption = [
    num("absR", t.absorption[0]),
    num("absG", t.absorption[1]),
    num("absB", t.absorption[2]),
  ];
  if (q.get("shallow")) t.colorShallow = "#" + q.get("shallow")!.replace(/^#/, "");
  if (q.get("deep")) t.colorDeep = "#" + q.get("deep")!.replace(/^#/, "");
  return t;
}

// Build a Water2Options set. Fields the rewritten shader does not yet know are
// optional on Water2Options, so passing them before the rewrite is type-safe.
function tuningToOptions(
  t: Tuning,
  sun: ReturnType<typeof makeSun>,
  dive: boolean,
): Water2Options {
  const opts: Water2Options & Record<string, unknown> = {
    width: SCENE_WIDTH * 1.6,
    depth: SCENE_DEPTH * 1.6,
    level: 0,
    side: dive ? THREE.DoubleSide : THREE.FrontSide,
    sunDirection: sun.direction,
    skyColor: skyColor(sun.elevationDeg),
    colorShallow: new THREE.Color(t.colorShallow),
    colorDeep: new THREE.Color(t.colorDeep),
    depthColorScale: t.depthColorScale,
    depthAlphaScale: t.depthAlphaScale,
    foamDepth: t.foamDepth,
    amplitude: t.amplitude,
    maxOpacity: t.maxOpacity,
    fresnelStrength: t.fresnelStrength,
  };
  // WFX levers: only set if the rewritten Water2Options declares them.
  opts.absorption = new THREE.Vector3(...t.absorption);
  opts.refractStrength = t.refractStrength;
  opts.roughness = t.roughness;
  opts.runup = t.runup;
  opts.contactSoftness = t.contactSoftness;
  return opts as Water2Options;
}

// Imperative water rig: builds water2, runs the opaque depth pre-pass + update
// each frame BEFORE r3f's auto-render (priority 0), resizes with the viewport.
function Water2Rig({
  tuningRef,
  sun,
  freeze,
  dive,
}: {
  tuningRef: React.RefObject<Tuning>;
  sun: ReturnType<typeof makeSun>;
  freeze: number | null;
  dive: boolean;
}) {
  const scene = useThree((s) => s.scene);
  const gl = useThree((s) => s.gl);
  const camera = useThree((s) => s.camera);
  const size = useThree((s) => s.size);
  const handleRef = useRef<Water2Handle | null>(null);

  useEffect(() => {
    const handle = makeWater2(tuningToOptions(tuningRef.current ?? DEFAULT_TUNING, sun, dive));
    handleRef.current = handle;
    scene.add(handle.mesh);
    return () => {
      scene.remove(handle.mesh);
      handle.dispose();
      handleRef.current = null;
    };
    // Rebuild only when the sun (tod) changes; live levers update via uniforms.
  }, [scene, sun, dive]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    handleRef.current?.setSize(size.width, size.height, gl.getPixelRatio());
  }, [size, gl]);

  useFrame((state) => {
    const handle = handleRef.current;
    if (!handle) return;
    const t = tuningRef.current;
    if (t) {
      const u = handle.material.uniforms;
      u.uDepthColorScale.value = t.depthColorScale;
      u.uDepthAlphaScale.value = t.depthAlphaScale;
      u.uFoamDepth.value = t.foamDepth;
      u.uAmplitude.value = t.amplitude;
      u.uMaxOpacity.value = t.maxOpacity;
      u.uFresnelStrength.value = t.fresnelStrength;
      u.uDebug.value = t.debug;
      u.uDebugScale.value = t.debugScale;
      // WFX uniforms (present only after the rewrite); set defensively.
      if (u.uAbsorption) (u.uAbsorption.value as THREE.Vector3).set(...t.absorption);
      if (u.uRefractStrength) u.uRefractStrength.value = t.refractStrength;
      if (u.uRoughness) u.uRoughness.value = t.roughness;
      if (u.uRunup) u.uRunup.value = t.runup;
      if (u.uContactSoftness) u.uContactSoftness.value = t.contactSoftness;
    }
    // Feed the live scene fog into the water so the far surface dissolves into
    // the horizon haze (FogExp2) / the underwater turbid-green volume (dive).
    const f = scene.fog;
    if (f instanceof THREE.FogExp2) handle.setFog({ color: f.color, density: f.density });
    else if (f instanceof THREE.Fog)
      handle.setFog({ color: f.color, density: 2.0 / Math.max(f.far - f.near, 1) });
    else handle.setFog(null);
    const elapsed = freeze != null ? freeze : state.clock.elapsedTime;
    handle.renderDepthPrepass(gl, scene, camera as THREE.PerspectiveCamera);
    handle.update(elapsed, camera);
  });

  return null;
}

// Sky dome owning the background, driven by the same sun as the light + water.
function SkyRig({ sun }: { sun: ReturnType<typeof makeSun> }) {
  const handle = useMemo(() => makeSkyDome({ sunDirection: sun.direction }), [sun]);
  useEffect(() => {
    handle.setSun(sun.direction);
    return () => handle.dispose();
  }, [handle, sun]);
  return <primitive object={handle.object3D} />;
}

// Fog rig: installs the requested fog mode on the live scene. FogExp2 proves the
// horizon retune; linear at the legacy near/far is the before-state baseline.
function FogRig({
  mode,
  density,
  sun,
  dive,
}: {
  mode: RigConfig["fog"];
  density: number;
  sun: ReturnType<typeof makeSun>;
  dive: boolean;
}) {
  const scene = useThree((s) => s.scene);
  useEffect(() => {
    const sky = skyColor(sun.elevationDeg);
    const haze = sky.clone().lerp(new THREE.Color("#1b4a6b"), 0.35);
    const prev = scene.fog;
    if (dive) {
      // R08 underwater volume: a turbid-green FogExp2 with short visibility, so
      // the submerged read is Salish-green (fog color from R11 #356f5d).
      scene.fog = new THREE.FogExp2(new THREE.Color("#356f5d"), 0.06);
    } else if (mode === "linear") scene.fog = new THREE.Fog(haze, 120, 520);
    else if (mode === "exp2") scene.fog = new THREE.FogExp2(haze, density);
    else scene.fog = null;
    return () => {
      scene.fog = prev;
    };
  }, [scene, mode, density, sun, dive]);
  return null;
}

// Terrain stylist: tints the streamed CUDEM tiles so the refracted seabed read
// is a living coast, mirroring the live scene. Optional via ?terrain=0.
function TerrainRig({ tiles }: { tiles: ReturnType<typeof useTilesLayer> }) {
  useEffect(() => {
    if (!tiles) return;
    const handle = applyTerrainStyle(tiles);
    return () => handle.dispose();
  }, [tiles]);
  return null;
}

// Applies camera preset, exposure, and the U-measurement harness. Exposes a
// window.__wfx readout (ready flag + measured U + frame-time A/B) for capture.
function RigController({ config, sun }: { config: RigConfig; sun: ReturnType<typeof makeSun> }) {
  const gl = useThree((s) => s.gl);
  const camera = useThree((s) => s.camera);
  const scene = useThree((s) => s.scene);
  const framesRef = useRef(0);

  useEffect(() => {
    gl.toneMappingExposure = config.exposure;
  }, [gl, config.exposure]);

  useEffect(() => {
    const v = VIEWS[config.view];
    camera.position.set(...v.pos);
    camera.lookAt(...v.target);
    camera.updateProjectionMatrix();
  }, [camera, config.view]);

  useFrame(() => {
    framesRef.current += 1;
    // After a warmup, mark ready so a headless capture can settle then shoot.
    if (framesRef.current === 90 && typeof window !== "undefined") {
      const w = window as unknown as { __wfx?: Record<string, unknown> };
      w.__wfx = { ...(w.__wfx ?? {}), ready: true };
    }
    // Perf harness: measure U (one full opaque scene render of the streamed
    // tileset) and a water-on vs water-off frame-time A/B, GPU-flushed via
    // gl.finish(). Runs once, ~3s after first paint so the tileset has streamed.
    if (config.perf && framesRef.current === 180 && typeof window !== "undefined") {
      const r = gl as unknown as THREE.WebGLRenderer;
      const cam = camera as THREE.PerspectiveCamera;
      const N = 30;
      // Hide water for the U + water-off measurements.
      const water = scene.getObjectByName("water2-depth-driven");
      const waterWasVisible = water?.visible ?? false;

      const time = (fn: () => void): number => {
        fn(); // warm
        r.getContext().finish();
        const t0 = performance.now();
        for (let i = 0; i < N; i++) fn();
        r.getContext().finish();
        return (performance.now() - t0) / N;
      };

      // U: one full opaque scene render (water hidden), to screen.
      if (water) water.visible = false;
      const u = time(() => r.render(scene, cam));

      // Water-off baseline already == U here. Water-on full frame:
      if (water) water.visible = true;
      const frameOn = time(() => r.render(scene, cam));

      if (water) water.visible = waterWasVisible;

      const w = window as unknown as { __wfx?: Record<string, unknown> };
      w.__wfx = {
        ...(w.__wfx ?? {}),
        ready: true,
        perf: {
          samples: N,
          dpr: r.getPixelRatio(),
          drawingBuffer: [r.domElement.width, r.domElement.height],
          U_ms: Number(u.toFixed(3)),
          frameWaterOn_ms: Number(frameOn.toFixed(3)),
          waterAdd_ms: Number((frameOn - u).toFixed(3)),
          note:
            "U = one full opaque scene render (water hidden) of the streamed CUDEM tileset, to screen, gl.finish()-flushed, mean of " +
            N +
            " renders. The depth pre-pass is a second render of the same opaque scene, so the running baseline is ~2U. waterAdd = full water-on frame minus U.",
        },
      };
    }
  });
  return null;
}

function SandboxContent({
  tuningRef,
  config,
  sun,
}: {
  tuningRef: React.RefObject<Tuning>;
  config: RigConfig;
  sun: ReturnType<typeof makeSun>;
}) {
  const tiles = useTilesLayer({
    url: FULL_TILESET_URL,
    groupRotationX: -Math.PI / 2,
    fitScaleToWidth: SCENE_WIDTH,
    errorTarget: 16,
    enableShadows: false,
  });

  return (
    <>
      <ambientLight intensity={sun.ambientIntensity} />
      <directionalLight
        position={sun.direction.clone().multiplyScalar(140).toArray()}
        intensity={sun.intensity}
        color={sun.color.getHex()}
      />
      <hemisphereLight args={["#8fc7ff", "#0a2540", 0.4]} />
      {config.sky && config.view !== "dive" && <SkyRig sun={sun} />}
      <FogRig mode={config.fog} density={config.fogDensity} sun={sun} dive={config.view === "dive"} />
      {tiles && config.terrain && <TerrainRig tiles={tiles} />}
      {tiles && <primitive object={tiles.group} />}
      <Water2Rig tuningRef={tuningRef} sun={sun} freeze={config.freeze} dive={config.view === "dive"} />
      <RigController config={config} sun={sun} />
      <OrbitControls
        enablePan
        enableZoom
        maxPolarAngle={Math.PI / 1.05}
        target={VIEWS[config.view].target}
      />
    </>
  );
}

function Slider({
  label,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (v: number) => void;
}) {
  return (
    <label style={{ display: "grid", gridTemplateColumns: "108px 1fr 52px", gap: 8, alignItems: "center" }}>
      <span>{label}</span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        defaultValue={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
      />
      <span>{value.toFixed(3)}</span>
    </label>
  );
}

export default function WaterSandboxScene() {
  const tuningRef = useRef<Tuning>(readTuning());
  const config = useMemo(() => readConfig(), []);
  const sun = useMemo(() => makeSun(TOD_TIMES[config.tod], 48.5, -123), [config.tod]);
  const [, force] = useState(0);

  function set<K extends keyof Tuning>(key: K, v: Tuning[K]) {
    tuningRef.current = { ...tuningRef.current, [key]: v };
    force((n) => n + 1);
  }

  const t = tuningRef.current;
  const view = VIEWS[config.view];

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Canvas
        camera={{ position: view.pos, fov: 45, near: 0.5, far: 4000 }}
        style={{ width: "100%", height: "100%", background: "#08263d" }}
        gl={{ antialias: true, preserveDrawingBuffer: true }}
        onCreated={({ gl }) => {
          gl.setClearColor(config.view === "dive" ? "#1c4a40" : "#08263d");
          gl.toneMapping = THREE.ACESFilmicToneMapping;
          gl.toneMappingExposure = config.exposure;
        }}
      >
        <SandboxContent tuningRef={tuningRef} config={config} sun={sun} />
      </Canvas>

      {!config.capture && (
        <div
          style={{
            position: "absolute",
            right: 12,
            bottom: 12,
            padding: "12px 14px",
            borderRadius: 8,
            font: "11px/1.4 ui-monospace, monospace",
            color: "#cfe6ff",
            background: "rgba(8,38,61,0.82)",
            width: 320,
          }}
        >
          <strong>WFX water rig</strong> - modeled, not measured.
          <div style={{ opacity: 0.8, marginTop: 2 }}>
            view={config.view} tod={config.tod} exp={config.exposure} fog={config.fog}
          </div>
          <div style={{ display: "grid", gap: 5, marginTop: 8 }}>
            <Slider label="alphaScale" value={t.depthAlphaScale} min={0.02} max={0.6} step={0.005} onChange={(v) => set("depthAlphaScale", v)} />
            <Slider label="colorScale" value={t.depthColorScale} min={0.02} max={0.8} step={0.005} onChange={(v) => set("depthColorScale", v)} />
            <Slider label="refract" value={t.refractStrength} min={0.0} max={0.12} step={0.002} onChange={(v) => set("refractStrength", v)} />
            <Slider label="roughness" value={t.roughness} min={0.02} max={0.6} step={0.005} onChange={(v) => set("roughness", v)} />
            <Slider label="runup" value={t.runup} min={0.0} max={2.0} step={0.02} onChange={(v) => set("runup", v)} />
            <Slider label="contact" value={t.contactSoftness} min={0.0} max={0.3} step={0.005} onChange={(v) => set("contactSoftness", v)} />
            <Slider label="foamDepth" value={t.foamDepth} min={0.0} max={0.2} step={0.005} onChange={(v) => set("foamDepth", v)} />
            <Slider label="fresnel" value={t.fresnelStrength} min={0.0} max={1.0} step={0.02} onChange={(v) => set("fresnelStrength", v)} />
            <button
              type="button"
              onClick={() => set("debug", t.debug > 0.5 ? 0 : 1)}
              style={{ marginTop: 4, padding: "4px 8px", cursor: "pointer" }}
            >
              depth debug: {t.debug > 0.5 ? "ON" : "off"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
