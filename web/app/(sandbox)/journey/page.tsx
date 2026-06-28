import type { Metadata } from "next";
import JourneyHost from "./JourneyHost";

// Isolated sandbox route at /journey (the (sandbox) route group keeps it out of
// the primary navigation). It exercises the W1 Camera Director against the real
// full-extent CUDEM tileset by running the East Sound choreography end to end:
// descend toward the water, follow the Anacortes -> Orcas ferry route, then
// settle into a continuous orbit of East Sound. The orchestrator runs the visual
// gate verification here; the director itself is type-checked and framework-free.
export const metadata: Metadata = {
  title: "Camera journey sandbox — W1 East Sound",
  robots: { index: false, follow: false },
};

export default function JourneySandboxPage() {
  return <JourneyHost />;
}
