"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import MapHero, { EventPoint } from "@/app/components/MapHero";
import type { MapViewport } from "@/lib/viewport";
import type { SceneIntent } from "@/lib/sceneIntent";

// Lazy-load the r3f scene so three/drei (~150KB gz) never blocks first paint and
// is never imported during SSR (WebGL/window unavailable on the server).
const SalishScene = dynamic(() => import("./SalishScene"), {
  ssr: false,
  loading: () => (
    <div className="scene-loading">
      <p className="muted">Loading 3D Salish Sea…</p>
    </div>
  ),
});

function webglAvailable(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const canvas = document.createElement("canvas");
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext("webgl") || canvas.getContext("experimental-webgl"))
    );
  } catch {
    return false;
  }
}

interface SceneHostProps {
  onIntent?: (intent: SceneIntent) => void;
  focus?: { lat: number; lng: number } | null;
  fallbackEvents?: EventPoint[];
  fallbackViewport?: MapViewport | null;
}

export default function SceneHost({
  onIntent,
  focus,
  fallbackEvents = [],
  fallbackViewport = null,
}: SceneHostProps) {
  const [mode, setMode] = useState<"checking" | "scene" | "fallback">("checking");

  useEffect(() => {
    setMode(webglAvailable() ? "scene" : "fallback");
  }, []);

  // SalishScene dispatches this when the terrain asset cannot load.
  useEffect(() => {
    function onError() {
      setMode("fallback");
    }
    window.addEventListener("salish-scene-error", onError);
    return () => window.removeEventListener("salish-scene-error", onError);
  }, []);

  if (mode === "fallback") {
    return (
      <div className="scene-fallback">
        <p className="muted scene-fallback-note">
          3D view unavailable on this device. Showing the Google Maps baseline, a deprecated fallback.
        </p>
        <MapHero events={fallbackEvents} initialViewport={fallbackViewport} />
      </div>
    );
  }

  return (
    <div className="scene-host" data-demo="salish-scene">
      {mode === "scene" ? (
        <SalishScene onIntent={onIntent} focus={focus} />
      ) : (
        <div className="scene-loading">
          <p className="muted">Initializing…</p>
        </div>
      )}
    </div>
  );
}
