"use client";

// Wave 1 de-risk sandbox scene. Proves the imperative `3d-tiles-renderer`
// TilesRenderer coexists with: r3f's render loop (useFrame), drei OrbitControls,
// shadow-mapped lighting, and a raycast pick — all WITHOUT touching the live
// SalishScene.tsx. Visual confirmation that geometry actually renders is a Wave 2
// task (no dev server is run during a parallel wave); this file is type-checked
// only.

import { useEffect, useRef, useState } from "react";
import { Canvas, ThreeEvent, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import { useTilesRenderer } from "./useTilesRenderer";

// STAND-IN tileset: a public OGC 3D Tiles 1.1 sample (implicit quadtree, glb
// content) from CesiumGS/3d-tiles-samples, served with CORS `*`. Kept for
// reference / fallback; it is NOT orcast geometry.
export const STANDIN_TILESET_URL =
  "https://raw.githubusercontent.com/CesiumGS/3d-tiles-samples/main/1.1/SparseImplicitQuadtree/tileset.json";

// orcast pilot tileset: the baked integrated CUDEM (wash_bellingham) land+seafloor
// surface for the San Juan bbox, NAVD88 m, EPSG:32610 local UTM frame, served
// over CloudFront (OAC) with CORS. This is the gate-closing geometry.
export const ORCAST_PILOT_TILESET_URL =
  "https://d8kxxpcnj3ub5.cloudfront.net/3dtwin/pilot/tileset.json";

// Active tileset for the sandbox. Point at the orcast pilot to close the Wave 1
// gate (pilot validates AND sandbox renders it).
const ACTIVE_TILESET_URL = ORCAST_PILOT_TILESET_URL;

type ControlsRef = React.ElementRef<typeof OrbitControls>;

function TilesLayer({
  url,
  controlsRef,
  onPick,
}: {
  url: string;
  controlsRef: React.RefObject<ControlsRef>;
  onPick: (point: THREE.Vector3) => void;
}) {
  const camera = useThree((s) => s.camera);
  const tiles = useTilesRenderer({ url, errorTarget: 8 });

  // Frame the camera on the tileset once the root loads. Works regardless of the
  // tileset's local extent/orientation, so it also fits the Wave 2 orcast pilot
  // (whose bbox is only known after the bake) with no hard-coded numbers.
  useEffect(() => {
    if (!tiles) return;
    const fit = () => {
      const sphere = new THREE.Sphere();
      if (!tiles.getBoundingSphere(sphere) || sphere.radius <= 0) return;
      const { center, radius } = sphere;
      const dir = new THREE.Vector3(1, 0.8, 1).normalize();
      camera.position.copy(center).addScaledVector(dir, radius * 2.5);
      if (camera instanceof THREE.PerspectiveCamera) {
        camera.near = Math.max(radius / 1000, 0.001);
        camera.far = radius * 100;
        camera.updateProjectionMatrix();
      }
      const controls = controlsRef.current;
      if (controls) {
        controls.target.copy(center);
        controls.update();
      }
    };
    tiles.addEventListener("load-tileset", fit);
    return () => tiles.removeEventListener("load-tileset", fit);
  }, [tiles, camera, controlsRef]);

  if (!tiles) return null;

  // The TilesRenderer streams tile meshes into `tiles.group` at runtime. r3f
  // raycasts the primitive recursively, so onClick resolves hits on the
  // dynamically-added tile meshes. `e.point` is the world-space hit; Wave 2 maps
  // it to a lat/lng SceneIntent (see WIRING-renderer.md).
  return (
    <primitive
      object={tiles.group}
      onClick={(e: ThreeEvent<MouseEvent>) => {
        e.stopPropagation();
        onPick(e.point.clone());
      }}
    />
  );
}

export default function TilesSandboxScene() {
  const controlsRef = useRef<ControlsRef>(null);
  const [pick, setPick] = useState<THREE.Vector3 | null>(null);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <Canvas
        shadows
        camera={{ position: [3, 3, 3], fov: 50, near: 0.01, far: 1000 }}
        style={{ width: "100%", height: "100%", background: "linear-gradient(#0b1f33,#08263d)" }}
        onCreated={({ gl }) => gl.setClearColor("#08263d")}
      >
        <ambientLight intensity={0.6} />
        <directionalLight
          position={[5, 10, 4]}
          intensity={1.2}
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
        />
        <hemisphereLight args={["#8fc7ff", "#0a2540", 0.4]} />

        <TilesLayer url={ACTIVE_TILESET_URL} controlsRef={controlsRef} onPick={setPick} />

        {/* Shadow catcher proves the imperative tiles cast into the r3f shadow map. */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.001, 0]} receiveShadow>
          <planeGeometry args={[1000, 1000]} />
          <shadowMaterial opacity={0.3} />
        </mesh>

        <OrbitControls
          ref={controlsRef}
          makeDefault
          enablePan
          enableZoom
          maxPolarAngle={Math.PI / 2.02}
        />
      </Canvas>

      <div
        style={{
          position: "absolute",
          left: 12,
          bottom: 12,
          padding: "8px 12px",
          borderRadius: 8,
          font: "12px/1.4 ui-monospace, monospace",
          color: "#cfe6ff",
          background: "rgba(8,38,61,0.78)",
          pointerEvents: "none",
        }}
      >
        <strong>3D Tiles sandbox</strong> — orcast CUDEM pilot (modeled, not measured).
        {pick ? (
          <span>
            {" "}
            picked world point: x={pick.x.toFixed(2)} y={pick.y.toFixed(2)} z={pick.z.toFixed(2)}
          </span>
        ) : (
          <span> click the geometry to pick a point.</span>
        )}
      </div>
    </div>
  );
}
