"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas, ThreeEvent } from "@react-three/fiber";
import { OrbitControls, Html } from "@react-three/drei";
import * as THREE from "three";
import { getJSON } from "@/lib/api";
import {
  HEIGHT_SCALE,
  ORCASOUND_FALLBACK,
  SCENE_WIDTH,
  projectToScene,
  sampleDepth,
  sceneDepth,
  unprojectFromScene,
  type Heightmap,
  type HydrophoneNode,
  type SceneIntent,
} from "@/lib/sceneIntent";

interface SalishSceneProps {
  onIntent?: (intent: SceneIntent) => void;
  focus?: { lat: number; lng: number } | null;
}

const WATER_SHALLOW = new THREE.Color("#2e6f9e");
const WATER_DEEP = new THREE.Color("#0a2540");
const LAND_LOW = new THREE.Color("#3f6b3a");
const LAND_HIGH = new THREE.Color("#9aa886");

function depthColor(depth: number, minDepth: number, maxDepth: number): THREE.Color {
  if (depth < 0) {
    const t = Math.min(1, depth / minDepth); // minDepth is negative; t in [0,1] for deep
    return WATER_SHALLOW.clone().lerp(WATER_DEEP, t);
  }
  const t = maxDepth > 0 ? Math.min(1, depth / maxDepth) : 0;
  return LAND_LOW.clone().lerp(LAND_HIGH, t);
}

function TerrainMesh({
  map,
  depth,
  onPick,
}: {
  map: Heightmap;
  depth: number;
  onPick: (lat: number, lng: number, depthM: number) => void;
}) {
  const geometry = useMemo(() => {
    const { rows, cols, depths, min_depth, max_depth } = map;
    const positions: number[] = [];
    const colors: number[] = [];
    for (let r = 0; r < rows; r += 1) {
      for (let c = 0; c < cols; c += 1) {
        const x = (c / (cols - 1) - 0.5) * SCENE_WIDTH;
        const z = -((r / (rows - 1)) - 0.5) * depth;
        const d = depths[r][c];
        positions.push(x, d * HEIGHT_SCALE, z);
        const col = depthColor(d, min_depth, max_depth);
        colors.push(col.r, col.g, col.b);
      }
    }
    const indices: number[] = [];
    for (let r = 0; r < rows - 1; r += 1) {
      for (let c = 0; c < cols - 1; c += 1) {
        const a = r * cols + c;
        const b = r * cols + c + 1;
        const d = (r + 1) * cols + c;
        const e = (r + 1) * cols + c + 1;
        indices.push(a, d, b, b, d, e);
      }
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geo.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    geo.setIndex(indices);
    geo.computeVertexNormals();
    return geo;
  }, [map, depth]);

  function handleClick(e: ThreeEvent<MouseEvent>) {
    e.stopPropagation();
    const { x, z } = e.point;
    const { lat, lng } = unprojectFromScene(x, z, map.bounds, depth);
    onPick(lat, lng, sampleDepth(map, lat, lng));
  }

  return (
    <mesh geometry={geometry} onClick={handleClick} castShadow receiveShadow>
      <meshStandardMaterial vertexColors flatShading roughness={0.95} metalness={0.05} />
    </mesh>
  );
}

function WaterPlane({ depth }: { depth: number }) {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
      <planeGeometry args={[SCENE_WIDTH * 1.6, depth * 1.6]} />
      <meshStandardMaterial
        color="#1b4a6b"
        transparent
        opacity={0.45}
        roughness={0.2}
        metalness={0.4}
      />
    </mesh>
  );
}

function HydrophoneBeacon({
  node,
  position,
  onSelect,
}: {
  node: HydrophoneNode;
  position: [number, number, number];
  onSelect: (node: HydrophoneNode) => void;
}) {
  const [hovered, setHovered] = useState(false);
  const online = (node.status ?? "online") === "online";
  const color = online ? "#ffcf33" : "#888";
  return (
    <group position={position}>
      <mesh
        position={[0, 6, 0]}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(node);
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
        }}
        onPointerOut={() => setHovered(false)}
        scale={hovered ? 1.4 : 1}
      >
        <coneGeometry args={[1.6, 5, 6]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={hovered ? 0.9 : 0.4} />
      </mesh>
      <mesh position={[0, 1.5, 0]}>
        <cylinderGeometry args={[0.18, 0.18, 9, 6]} />
        <meshStandardMaterial color="#ffffff" emissive={color} emissiveIntensity={0.3} />
      </mesh>
      {hovered && (
        <Html center distanceFactor={120} position={[0, 11, 0]} style={{ pointerEvents: "none" }}>
          <div className="scene-beacon-label">{node.name ?? node.location ?? "Hydrophone"}</div>
        </Html>
      )}
    </group>
  );
}

export default function SalishScene({ onIntent, focus }: SalishSceneProps) {
  const [map, setMap] = useState<Heightmap | null>(null);
  const [nodes, setNodes] = useState<HydrophoneNode[]>([]);
  const [assetError, setAssetError] = useState(false);
  const onIntentRef = useRef(onIntent);
  onIntentRef.current = onIntent;

  useEffect(() => {
    fetch("/geo/salish_heightmap.json", { cache: "force-cache" })
      .then((r) => {
        if (!r.ok) throw new Error(`heightmap ${r.status}`);
        return r.json();
      })
      .then((m: Heightmap) => setMap(m))
      .catch(() => setAssetError(true));
  }, []);

  useEffect(() => {
    getJSON<{ data?: HydrophoneNode[]; hydrophones?: HydrophoneNode[] }>("/api/live-hydrophones")
      .then((res) => {
        const list = res.hydrophones ?? res.data ?? [];
        setNodes(list.length ? list : ORCASOUND_FALLBACK);
      })
      .catch(() => setNodes(ORCASOUND_FALLBACK));
  }, []);

  // Bubble asset failure to the host so it can fall back to Maps.
  useEffect(() => {
    if (assetError) {
      const evt = new CustomEvent("salish-scene-error");
      window.dispatchEvent(evt);
    }
  }, [assetError]);

  const depth = useMemo(() => (map ? sceneDepth(map.bounds) : 90), [map]);

  if (assetError) {
    return null;
  }

  if (!map) {
    return (
      <div className="scene-loading">
        <p className="muted">Loading 3D Salish Sea…</p>
      </div>
    );
  }

  const inBoundsNodes = nodes.filter(
    (n) =>
      n.latitude >= map.bounds.min_lat &&
      n.latitude <= map.bounds.max_lat &&
      n.longitude >= map.bounds.min_lng &&
      n.longitude <= map.bounds.max_lng,
  );
  const beacons = inBoundsNodes.length ? inBoundsNodes : nodes.slice(0, 1);

  return (
    <Canvas
      shadows
      camera={{ position: [0, 70, 95], fov: 45, near: 0.1, far: 2000 }}
      style={{ width: "100%", height: "100%", background: "linear-gradient(#0b1f33,#08263d)" }}
      onCreated={({ gl }) => gl.setClearColor("#08263d")}
    >
      <ambientLight intensity={0.6} />
      <directionalLight position={[60, 90, 40]} intensity={1.1} castShadow />
      <hemisphereLight args={["#8fc7ff", "#0a2540", 0.4]} />
      <TerrainMesh
        map={map}
        depth={depth}
        onPick={(lat, lng, depthM) => onIntentRef.current?.({ type: "cell", lat, lng, depth_m: depthM })}
      />
      <WaterPlane depth={depth} />
      {beacons.map((node, i) => {
        const [x, z] = projectToScene(node.latitude, node.longitude, map.bounds, depth);
        const y = sampleDepth(map, node.latitude, node.longitude) * HEIGHT_SCALE;
        return (
          <HydrophoneBeacon
            key={`${node.id ?? node.name ?? i}`}
            node={node}
            position={[x, Math.max(y, 0), z]}
            onSelect={(n) =>
              onIntentRef.current?.({
                type: "hydrophone",
                id: n.id ?? null,
                name: n.name,
                lat: n.latitude,
                lng: n.longitude,
                streamUrl: n.streamUrl,
              })
            }
          />
        );
      })}
      {focus && (
        <FocusMarker lat={focus.lat} lng={focus.lng} map={map} depth={depth} />
      )}
      <OrbitControls
        enablePan
        enableZoom
        maxPolarAngle={Math.PI / 2.05}
        minDistance={20}
        maxDistance={400}
        target={[0, 0, 0]}
      />
    </Canvas>
  );
}

function FocusMarker({
  lat,
  lng,
  map,
  depth,
}: {
  lat: number;
  lng: number;
  map: Heightmap;
  depth: number;
}) {
  const [x, z] = projectToScene(lat, lng, map.bounds, depth);
  const y = sampleDepth(map, lat, lng) * HEIGHT_SCALE;
  return (
    <mesh position={[x, Math.max(y, 0) + 4, z]}>
      <sphereGeometry args={[1.6, 16, 16]} />
      <meshStandardMaterial color="#ff5a5a" emissive="#ff5a5a" emissiveIntensity={0.7} />
    </mesh>
  );
}
