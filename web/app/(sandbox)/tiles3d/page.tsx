import type { Metadata } from "next";
import TilesSandboxHost from "./TilesSandboxHost";

// Isolated sandbox route at /tiles3d. The (sandbox) route group keeps it out of
// the app's primary navigation; it exists only to de-risk the Wave 2 mount of
// `3d-tiles-renderer` inside the live react-three-fiber scene.
export const metadata: Metadata = {
  title: "3D Tiles sandbox — Wave 1 de-risk",
  robots: { index: false, follow: false },
};

export default function Tiles3DSandboxPage() {
  return <TilesSandboxHost />;
}
