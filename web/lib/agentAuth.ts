import { withAuth } from "@workos-inc/authkit-nextjs";

export interface ReviewerIdentity {
  id: string;
  email: string;
}

const AGENT_KEY = process.env.ORCAST_AGENT_KEY ?? "";
const AGENT_REVIEWER_ID = process.env.ORCAST_AGENT_REVIEWER_ID ?? "agent_orcast_automation";
const AGENT_REVIEWER_EMAIL = process.env.ORCAST_AGENT_REVIEWER_EMAIL ?? "agent@orcast.dev";

/** Server-side automation identity (Cursor agent, CI, Playwright demo). Never expose key to browser bundle. */
export function agentUserFromHeaders(headerList: Headers): ReviewerIdentity | null {
  if (!AGENT_KEY) return null;
  const provided =
    headerList.get("x-orcast-agent-key") ?? headerList.get("X-ORCAST-Agent-Key");
  if (!provided || provided !== AGENT_KEY) return null;
  return { id: AGENT_REVIEWER_ID, email: AGENT_REVIEWER_EMAIL };
}

/** Server-side automation identity (Cursor agent, CI, Playwright demo). Never expose key to browser bundle. */
export function agentUserFromRequest(req: Request): ReviewerIdentity | null {
  return agentUserFromHeaders(req.headers);
}

/** WorkOS session or automation agent key — used by keyed proxy routes. */
export async function resolveReviewer(req: Request): Promise<ReviewerIdentity | null> {
  const agent = agentUserFromRequest(req);
  if (agent) return agent;
  const { user } = await withAuth();
  if (!user?.id && !user?.email) return null;
  return {
    id: user.id ?? "",
    email: user.email ?? "",
  };
}

export function reviewerProxyHeaders(reviewer: ReviewerIdentity): Record<string, string> {
  const headers: Record<string, string> = {
    "X-ORCAST-Trusted-Proxy": "vercel",
    "X-ORCAST-Reviewer-Role": "reviewer",
  };
  if (reviewer.id) headers["X-ORCAST-Reviewer-Id"] = reviewer.id;
  if (reviewer.email) headers["X-ORCAST-Reviewer-Email"] = reviewer.email;
  return headers;
}
