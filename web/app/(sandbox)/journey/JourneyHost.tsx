"use client";

// SSR-safe host, mirroring TilesSandboxHost / WaterSandboxHost: the r3f + WebGL
// scene must never be imported during SSR (window/WebGL are server-unavailable).
// dynamic ssr:false keeps it client-only.

import dynamic from "next/dynamic";

const JourneyScene = dynamic(() => import("./JourneyScene"), {
  ssr: false,
  loading: () => (
    <div style={{ display: "grid", placeItems: "center", width: "100%", height: "100%", color: "#9fb6c8" }}>
      Loading camera journey sandbox…
    </div>
  ),
});

export default function JourneyHost() {
  return (
    <div style={{ width: "100%", height: "100vh" }}>
      <JourneyScene />
    </div>
  );
}
