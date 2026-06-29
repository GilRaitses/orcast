"use client";

// SSR-safe host (mirrors OrcaSandboxHost): the r3f + WebGL + WebAudio scene must
// never be imported during SSR. dynamic ssr:false keeps it client-only.

import dynamic from "next/dynamic";

const StationScene = dynamic(() => import("./StationScene"), {
  ssr: false,
  loading: () => (
    <div style={{ display: "grid", placeItems: "center", width: "100%", height: "100%", color: "#9fb6c8" }}>
      Loading station hydrophone sandbox…
    </div>
  ),
});

export default function StationHost() {
  return (
    <div style={{ width: "100%", height: "100vh" }}>
      <StationScene />
    </div>
  );
}
