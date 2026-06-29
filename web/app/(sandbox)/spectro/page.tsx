import type { Metadata } from "next";
import SpectroSandboxHost from "./SpectroSandboxHost";

// Isolated sandbox route at /spectro (route group keeps it out of primary nav).
// Bakes a Web Worker STFT spectrogram of the REAL Orcasound Lab slice clip and
// proves the scrubbable HUD + SpectroTimelineAuthority before the O0-gated
// integrator wires it into the live scene. Sandbox-only.
export const metadata: Metadata = {
  title: "SPECTRO timeline authority sandbox",
  robots: { index: false, follow: false },
};

export default function SpectroSandboxPage() {
  return <SpectroSandboxHost />;
}
