"use client";

// SSR-safe host, mirroring web/app/components/scene/SceneHost.tsx: the r3f +
// WebGL scene (three/drei/3d-tiles-renderer) must never be imported during SSR
// because window/WebGL are unavailable on the server. dynamic(..., { ssr: false })
// keeps it client-only, exactly as SalishScene is loaded.

import dynamic from "next/dynamic";

const TilesSandboxScene = dynamic(() => import("./TilesSandboxScene"), {
  ssr: false,
  loading: () => (
    <div style={{ display: "grid", placeItems: "center", width: "100%", height: "100%", color: "#9fb6c8" }}>
      Loading 3D Tiles sandbox…
    </div>
  ),
});

export default function TilesSandboxHost() {
  return (
    <div style={{ width: "100%", height: "100vh" }}>
      <TilesSandboxScene />
    </div>
  );
}
