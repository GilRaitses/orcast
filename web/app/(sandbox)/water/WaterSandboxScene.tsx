"use client";

// W2.5 sandbox: proves the depth-driven water2 module against the real
// full-extent CUDEM tileset, with live tuning sliders for the Beer-Lambert
// falloffs and foam. The bar is "land-and-sea": the San Juan Islands and shallow
// shelves must reveal terrain (water clears over them) while deep channels stay
// blue, with a shoreline foam line and a rippling, glittering surface.

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { useTilesLayer } from "@/lib/scene/tiles";
import { makeSun } from "@/app/components/scene/realism/sun";
import { skyColor } from "@/app/components/scene/realism/atmosphere";
import { SCENE_WIDTH, sceneDepth, type HeightmapBounds } from "@/lib/sceneIntent";
import { makeWater2, type Water2Handle } from "@/lib/scene/water2";

const FULL_TILESET_URL =
  "https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/full/tileset.json";

const TILESET_BOUNDS: HeightmapBounds = {
  min_lat: 48.4,
  max_lat: 48.7,
  min_lng: -123.25,
  max_lng: -122.75,
};

const SCENE_DEPTH = sceneDepth(TILESET_BOUNDS);
const SCENE_TIME = new Date("2026-06-27T20:00:00Z");

interface Tuning {
  depthColorScale: number;
  depthAlphaScale: number;
  foamDepth: number;
  amplitude: number;
  maxOpacity: number;
  fresnelStrength: number;
  debug: number;
  debugScale: number;
}

const DEFAULT_TUNING: Tuning = {
  depthColorScale: 0.3,
  depthAlphaScale: 0.3,
  foamDepth: 0.08,
  amplitude: 0.32,
  maxOpacity: 0.96,
  fresnelStrength: 0.5,
  debug: 0,
  debugScale: 1.0,
};

// Imperative depth-driven water rig: builds water2, adds the mesh to the scene,
// runs the opaque depth pre-pass + uniform update each frame BEFORE r3f's
// automatic render (priority 0), and resizes the depth target with the viewport.
function Water2Rig({ tuningRef }: { tuningRef: React.RefObject<Tuning> }) {
  const scene = useThree((s) => s.scene);
  const gl = useThree((s) => s.gl);
  const camera = useThree((s) => s.camera);
  const size = useThree((s) => s.size);
  const handleRef = useRef<Water2Handle | null>(null);

  const sun = useMemo(() => makeSun(SCENE_TIME, 48.5, -123), []);

  useEffect(() => {
    const handle = makeWater2({
      width: SCENE_WIDTH * 1.6,
      depth: SCENE_DEPTH * 1.6,
      level: 0,
      sunDirection: sun.direction,
      skyColor: skyColor(sun.elevationDeg),
    });
    handleRef.current = handle;
    scene.add(handle.mesh);
    return () => {
      scene.remove(handle.mesh);
      handle.dispose();
      handleRef.current = null;
    };
  }, [scene, sun]);

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
    }
    handle.renderDepthPrepass(gl, scene, camera as THREE.PerspectiveCamera);
    handle.update(state.clock.elapsedTime, camera);
  });

  return null;
}

function SandboxContent({ tuningRef }: { tuningRef: React.RefObject<Tuning> }) {
  const [fitRadius, setFitRadius] = useState<number | null>(null);
  const sun = useMemo(() => makeSun(SCENE_TIME, 48.5, -123), []);

  const tiles = useTilesLayer({
    url: FULL_TILESET_URL,
    groupRotationX: -Math.PI / 2,
    fitScaleToWidth: SCENE_WIDTH,
    errorTarget: 16,
    enableShadows: false,
    onFit: (sphere) => setFitRadius(sphere.radius),
  });

  const minDistance = fitRadius ? fitRadius * 0.5 : 30;
  const maxDistance = fitRadius ? fitRadius * 8 : 600;

  return (
    <>
      <ambientLight intensity={sun.ambientIntensity} />
      <directionalLight
        position={sun.direction.clone().multiplyScalar(140).toArray()}
        intensity={sun.intensity}
        color={sun.color.getHex()}
      />
      <hemisphereLight args={["#8fc7ff", "#0a2540", 0.4]} />
      {tiles && <primitive object={tiles.group} />}
      <Water2Rig tuningRef={tuningRef} />
      <OrbitControls
        enablePan
        enableZoom
        maxPolarAngle={Math.PI / 2.05}
        minDistance={minDistance}
        maxDistance={maxDistance}
        target={[0, 0, 0]}
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
    <label style={{ display: "grid", gridTemplateColumns: "120px 1fr 56px", gap: 8, alignItems: "center" }}>
      <span>{label}</span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        defaultValue={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
      />
      <span id={`v-${label}`}>{value.toFixed(3)}</span>
    </label>
  );
}

// Initial tuning can be driven from the URL query string (e.g.
// /water?debug=1&debugScale=1&alphaScale=0.3&colorScale=0.2), so a headless
// browser can set values via navigation without clicking the sliders.
function tuningFromQuery(): Tuning {
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
  return t;
}

export default function WaterSandboxScene() {
  const tuningRef = useRef<Tuning>(tuningFromQuery());
  const [, force] = useState(0);

  function set<K extends keyof Tuning>(key: K, v: number) {
    tuningRef.current = { ...tuningRef.current, [key]: v };
    force((n) => n + 1);
  }

  const t = tuningRef.current;

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Canvas
        camera={{ position: [0, 80, 120], fov: 45, near: 1, far: 800 }}
        style={{ width: "100%", height: "100%", background: "linear-gradient(#0b1f33,#08263d)" }}
        onCreated={({ gl }) => gl.setClearColor("#08263d")}
      >
        <SandboxContent tuningRef={tuningRef} />
      </Canvas>

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
          width: 340,
        }}
      >
        <strong>Depth-driven water (W2.5)</strong> - modeled, not measured.
        <div style={{ display: "grid", gap: 5, marginTop: 8 }}>
          <Slider label="alphaScale" value={t.depthAlphaScale} min={0.02} max={0.6} step={0.005} onChange={(v) => set("depthAlphaScale", v)} />
          <Slider label="colorScale" value={t.depthColorScale} min={0.02} max={0.8} step={0.005} onChange={(v) => set("depthColorScale", v)} />
          <Slider label="foamDepth" value={t.foamDepth} min={0.0} max={0.2} step={0.005} onChange={(v) => set("foamDepth", v)} />
          <Slider label="amplitude" value={t.amplitude} min={0.0} max={0.8} step={0.01} onChange={(v) => set("amplitude", v)} />
          <Slider label="maxOpacity" value={t.maxOpacity} min={0.5} max={1.0} step={0.01} onChange={(v) => set("maxOpacity", v)} />
          <Slider label="fresnel" value={t.fresnelStrength} min={0.0} max={1.0} step={0.02} onChange={(v) => set("fresnelStrength", v)} />
          <Slider label="debugScale" value={t.debugScale} min={0.1} max={3.0} step={0.05} onChange={(v) => set("debugScale", v)} />
          <button
            type="button"
            onClick={() => set("debug", t.debug > 0.5 ? 0 : 1)}
            style={{ marginTop: 4, padding: "4px 8px", cursor: "pointer" }}
          >
            depth debug: {t.debug > 0.5 ? "ON" : "off"}
          </button>
        </div>
      </div>
    </div>
  );
}
