import type { Metadata } from "next";
import OrcaSandboxHost from "./OrcaSandboxHost";

// Isolated sandbox route at /orca (route group keeps it out of primary nav).
// Proves the data-driven, WFX-lit orca (mesh + rig + materials + eyes + mouth +
// real SRKW biologging motion + bounded secondary physics) before the O0-gated
// integrator mounts it into the live SalishScene underwater view. Sandbox-only.
export const metadata: Metadata = {
  title: "ORCA biologging twin sandbox",
  robots: { index: false, follow: false },
};

export default function OrcaSandboxPage() {
  return <OrcaSandboxHost />;
}
