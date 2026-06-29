"use client";

// SSR-safe host (mirrors SliceHost/StationHost). The studio is interactive and
// holds client-only state, so it is loaded with ssr disabled.

import dynamic from "next/dynamic";

const AnnotateStudio = dynamic(() => import("./AnnotateStudio"), {
  ssr: false,
  loading: () => (
    <div style={{ display: "grid", placeItems: "center", width: "100%", minHeight: "100vh", color: "#9fb6c8" }}>
      Loading annotation studio
    </div>
  ),
});

export default function AnnotateHost() {
  return <AnnotateStudio />;
}
