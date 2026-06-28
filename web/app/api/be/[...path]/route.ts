import { NextRequest, NextResponse } from "next/server";
import { withAuth } from "@workos-inc/authkit-nextjs";
import { agentUserFromRequest, reviewerProxyHeaders } from "@/lib/agentAuth";

// Server-side proxy to the App Runner backend. Keeps the API key out of the
// browser: keyed endpoints (moderation, promotion, orchestrator) are reachable
// only through this same-origin proxy, which injects X-ORCAST-Key.
//
// Authorization model:
//   - A small allow-list of read-only (GET) endpoints is public.
//   - Everything else (any non-GET method, any non-allow-listed path, and PII
//     reads) requires an authenticated WorkOS user.
// The key is only ever injected after the request passes these checks.

const API_BASE = process.env.ORCAST_API_BASE ?? "";
const API_KEY = process.env.ORCAST_API_KEY ?? "";

export const dynamic = "force-dynamic";

// Public read-only paths. Matched exactly or as a path prefix (entry + "/...").
const PUBLIC_GET_PATHS = [
  "api/gates",
  "api/provenance",
  "api/sighting-assist/status",
  "api/explore/status",
  "api/interactions/status",
  "api/realtime/events",
  "api/status",
  "health",
  "api/hotspots",
  "api/sightings",
  "api/verified-sightings",
  "api/environmental",
  "api/live-hydrophones",
  "api/onc/hydrophone-signal",
  "api/onc/archivefile",
  "forecast",
];

// Paths that expose PII or are explicitly protected even for GET. Listed for
// clarity; they are not in the allow-list, so they already require a session.
const PROTECTED_PATHS = [
  "api/community/submissions",
  "api/decision-records",
  "api/review-dossier",
  "api/journal",
];

function matchesPath(path: string, entries: string[]): boolean {
  return entries.some((entry) => path === entry || path.startsWith(`${entry}/`));
}

function isPublicGet(method: string, path: string): boolean {
  if (method !== "GET") return false;
  if (matchesPath(path, PROTECTED_PATHS)) return false;
  return matchesPath(path, PUBLIC_GET_PATHS);
}

function isPublicRequest(method: string, path: string): boolean {
  if (method === "POST" && path === "api/sighting-assist") return true;
  if (method === "POST" && (path === "api/explore/sessions" || path === "api/explore/turn")) return true;
  if (method === "POST" && path === "api/interactions") return true;
  if (method === "POST" && path === "api/interactions/prepare") return true;
  // Anonymous-first: the adaptive planner/console is usable without sign-in.
  // Keyed T2/T3 skills stay server-side gated, so a public planner simply omits
  // those panels (HANDOFF_CHARTER B2).
  if (method === "POST" && path === "api/interactions/plan") return true;
  // WS6 M1: the panels-first narration JSON path is the guaranteed fallback for
  // the streamed narration. It must be reachable anonymously or the fallback
  // 401s for the primary anonymous audience (defeating the never-hang contract).
  if (method === "POST" && path === "api/interactions/narrate") return true;
  if (method === "POST" && path === "api/interest") return true;
  return isPublicGet(method, path);
}

// --- Best-effort per-IP rate limiting (module-level, in-memory) ---
const RATE_LIMIT = 60; // requests per minute (global public proxy)
const RATE_WINDOW_MS = 60_000;
const EXPLORE_TURN_LIMIT = 10;
const EXPLORE_SESSION_LIMIT = 5;
const rateBuckets = new Map<string, { count: number; resetAt: number }>();

function clientIp(req: NextRequest): string {
  const fwd = req.headers.get("x-forwarded-for");
  if (fwd) return fwd.split(",")[0].trim();
  return req.headers.get("x-real-ip") ?? "unknown";
}

// WS-COLDSTART M4: absorb a brief App Runner instance-handover blip so a deploy or
// instance recycle never surfaces a 404/503 to a user (confirmed root cause: the
// App Runner edge emits a transient 5xx/404 during the ~30s handover before a new
// instance is registered). One bounded retry, double-write-safe.
const RETRY_BACKOFF_MS = 300;
function retryDelayMs(): number {
  return RETRY_BACKOFF_MS + Math.floor(Math.random() * 100);
}
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRateLimited(ip: string, limit: number = RATE_LIMIT, keySuffix = ""): boolean {
  const key = keySuffix ? `${keySuffix}:${ip}` : ip;
  const now = Date.now();
  const bucket = rateBuckets.get(key);
  if (!bucket || now >= bucket.resetAt) {
    rateBuckets.set(key, { count: 1, resetAt: now + RATE_WINDOW_MS });
    return false;
  }
  bucket.count += 1;
  return bucket.count > limit;
}

function explorePathLimit(path: string): { limit: number; suffix: string } | null {
  if (path === "api/explore/turn") return { limit: EXPLORE_TURN_LIMIT, suffix: "explore-turn" };
  if (path === "api/interactions") return { limit: EXPLORE_TURN_LIMIT, suffix: "interactions" };
  if (path === "api/interactions/prepare") return { limit: EXPLORE_TURN_LIMIT, suffix: "interactions-prepare" };
  if (path === "api/interactions/plan") return { limit: EXPLORE_TURN_LIMIT, suffix: "interactions-plan" };
  if (path === "api/interactions/narrate") return { limit: EXPLORE_TURN_LIMIT, suffix: "interactions-narrate" };
  if (path === "api/explore/sessions") return { limit: EXPLORE_SESSION_LIMIT, suffix: "explore-session" };
  return null;
}

async function forward(req: NextRequest, path: string[]) {
  if (!API_BASE) {
    return NextResponse.json({ error: "ORCAST_API_BASE not configured" }, { status: 500 });
  }

  const joined = path.join("/");
  const ip = clientIp(req);
  const exploreLimit = explorePathLimit(joined);
  if (exploreLimit && isRateLimited(ip, exploreLimit.limit, exploreLimit.suffix)) {
    return NextResponse.json(
      { error: "Explore rate limit exceeded", path: joined },
      { status: 429 },
    );
  }

  if (isRateLimited(ip)) {
    return NextResponse.json({ error: "Rate limit exceeded" }, { status: 429 });
  }

  let authenticatedUser: unknown = null;
  const agentUser = agentUserFromRequest(req);

  if (!isPublicRequest(req.method, joined)) {
    if (agentUser) {
      authenticatedUser = { id: agentUser.id, email: agentUser.email };
    } else {
      const { user } = await withAuth();
      if (!user) {
        return NextResponse.json({ error: "Authentication required" }, { status: 401 });
      }
      authenticatedUser = user;
    }
  }

  const target = new URL(`${API_BASE.replace(/\/$/, "")}/${joined}`);
  req.nextUrl.searchParams.forEach((v, k) => target.searchParams.set(k, v));

  const incomingContentType = req.headers.get("content-type") ?? "";
  const isMultipart = incomingContentType.toLowerCase().startsWith("multipart/form-data");

  const headers: Record<string, string> = {};
  // For multipart, let the browser-set Content-Type (with boundary) pass through;
  // for everything else default to JSON so existing callers are unchanged.
  if (!isMultipart) {
    headers["Content-Type"] = "application/json";
  }
  if (incomingContentType && isMultipart) {
    headers["Content-Type"] = incomingContentType;
  }

  if (API_KEY) headers["X-ORCAST-Key"] = API_KEY;
  if (authenticatedUser || agentUser) {
    headers["X-ORCAST-Trusted-Proxy"] = "vercel";
  }
  if (authenticatedUser) {
    const user = authenticatedUser as { id?: string; email?: string };
    Object.assign(headers, reviewerProxyHeaders({ id: user.id ?? "", email: user.email ?? "" }));
  }

  const init: RequestInit = { method: req.method, headers, cache: "no-store" };
  if (req.method !== "GET" && req.method !== "HEAD") {
    if (isMultipart) {
      // Forward the raw binary body; do NOT call req.text() which corrupts binary data.
      init.body = await req.arrayBuffer();
    } else {
      init.body = await req.text();
    }
  }

  // A 503 from the App Runner edge means no healthy instance received the request,
  // so it had no side effect and is safe to retry for any method. 502/504/404 are
  // ambiguous for mutations, so they are only retried for idempotent GETs. The
  // request body is fully buffered in `init.body`, so a retry replays cleanly.
  const idempotent = req.method === "GET";
  const maxAttempts = 2;
  let resp: Response | undefined;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    try {
      resp = await fetch(target.toString(), init);
    } catch {
      if (attempt < maxAttempts) {
        await sleep(retryDelayMs());
        continue;
      }
      return NextResponse.json({ error: "upstream_unreachable" }, { status: 502 });
    }
    const status = resp.status;
    const retryable = status === 503 || (idempotent && (status === 502 || status === 504 || status === 404));
    if (retryable && attempt < maxAttempts) {
      try {
        await resp.body?.cancel();
      } catch {
        // ignore: best-effort drain before retry
      }
      await sleep(retryDelayMs());
      continue;
    }
    break;
  }

  const settled = resp as Response;
  const body = await settled.text();
  return new NextResponse(body, {
    status: settled.status,
    headers: { "Content-Type": settled.headers.get("Content-Type") ?? "application/json" },
  });
}

export async function GET(req: NextRequest, ctx: { params: { path: string[] } }) {
  return forward(req, ctx.params.path);
}

export async function POST(req: NextRequest, ctx: { params: { path: string[] } }) {
  return forward(req, ctx.params.path);
}

export async function PUT(req: NextRequest, ctx: { params: { path: string[] } }) {
  return forward(req, ctx.params.path);
}

export async function PATCH(req: NextRequest, ctx: { params: { path: string[] } }) {
  return forward(req, ctx.params.path);
}

export async function DELETE(req: NextRequest, ctx: { params: { path: string[] } }) {
  return forward(req, ctx.params.path);
}
