import { headers } from "next/headers";
import { withAuth } from "@workos-inc/authkit-nextjs";
import { agentUserFromHeaders } from "@/lib/agentAuth";
import AdaptiveExplore from "./components/AdaptiveExplore";

// Explore-first landing (HANDOFF_CHARTER A): the 3D Salish Sea + adaptive
// orchestrator console is the home surface. Auth is resolved server-side only to
// toggle write-action gating; every surface stays visible to anonymous users.
export default async function HomePage() {
  const agent = agentUserFromHeaders(headers());
  let signedIn = !!agent;
  if (!signedIn) {
    try {
      const { user } = await withAuth();
      signedIn = !!user;
    } catch {
      signedIn = false;
    }
  }
  return <AdaptiveExplore signedIn={signedIn} />;
}
