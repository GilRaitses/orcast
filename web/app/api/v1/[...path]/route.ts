import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.ORCAST_API_BASE ?? "";
const API_KEY = process.env.ORCAST_API_KEY ?? "";
const PARTNER_DEV_KEY = process.env.ORCAST_PARTNER_DEV_KEY ?? "";

const PUBLIC_PATHS = new Set([
  "api/gates",
  "api/provenance",
  "api/sighting-assist/status",
  "health",
  "forecast/quick",
  "forecast/spatial",
  "forecast/current",
]);

const SIGHTING_PATH = "api/sighting-assist";

const RATE_LIMIT = 60;
const RATE_WINDOW_MS = 60_000;
const ipBuckets = new Map<string, { count: number; resetAt: number }>();
const keyBuckets = new Map<string, { count: number; resetAt: number; day: string }>();

const TIER_DAILY: Record<string, number> = {
  free: 100,
  builder: 1000,
  pro: 10000,
};

export const dynamic = "force-dynamic";

function tierAllowsSighting(tier: string): boolean {
  return tier === "builder" || tier === "pro";
}

function clientIp(req: NextRequest): string {
  const fwd = req.headers.get("x-forwarded-for");
  if (fwd) return fwd.split(",")[0].trim();
  return req.headers.get("x-real-ip") ?? "unknown";
}

function isIpLimited(ip: string): boolean {
  const now = Date.now();
  const bucket = ipBuckets.get(ip);
  if (!bucket || now >= bucket.resetAt) {
    ipBuckets.set(ip, { count: 1, resetAt: now + RATE_WINDOW_MS });
    return false;
  }
  bucket.count += 1;
  return bucket.count > RATE_LIMIT;
}

function isKeyOverDailyLimit(keyId: string, tier: string): boolean {
  const day = new Date().toISOString().slice(0, 10);
  const bucket = keyBuckets.get(keyId);
  if (!bucket || bucket.day !== day) {
    keyBuckets.set(keyId, { count: 1, resetAt: 0, day });
    return false;
  }
  bucket.count += 1;
  return bucket.count > (TIER_DAILY[tier] ?? TIER_DAILY.free);
}

async function resolvePartner(raw: string): Promise<{ tier: string; keyId: string } | null> {
  if (!raw) return null;
  if (PARTNER_DEV_KEY && raw === PARTNER_DEV_KEY) {
    return { tier: "builder", keyId: "partner_dev" };
  }
  if (!API_BASE || !API_KEY) return null;
  const resp = await fetch(`${API_BASE.replace(/\/$/, "")}/api/partner/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-ORCAST-Key": API_KEY },
    body: JSON.stringify({ key: raw }),
    cache: "no-store",
  });
  if (!resp.ok) return null;
  const body = await resp.json();
  return { tier: body.tier, keyId: body.key_id };
}

async function forward(req: NextRequest, path: string[], tier: string) {
  if (!API_BASE) {
    return NextResponse.json({ error: "ORCAST_API_BASE not configured" }, { status: 500 });
  }
  const joined = path.join("/");
  if (joined === SIGHTING_PATH && req.method === "POST" && !tierAllowsSighting(tier)) {
    return NextResponse.json(
      { error: "Sighting assist requires builder or pro tier" },
      { status: 402 },
    );
  }
  if (!PUBLIC_PATHS.has(joined) && joined !== SIGHTING_PATH) {
    return NextResponse.json({ error: "Path not enabled for partner tier" }, { status: 403 });
  }

  const target = new URL(`${API_BASE.replace(/\/$/, "")}/${joined}`);
  req.nextUrl.searchParams.forEach((v, k) => target.searchParams.set(k, v));
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (API_KEY) headers["X-ORCAST-Key"] = API_KEY;
  headers["X-ORCAST-Partner-Tier"] = tier;

  const init: RequestInit = { method: req.method, headers, cache: "no-store" };
  if (req.method !== "GET" && req.method !== "HEAD") {
    init.body = await req.text();
  }
  const resp = await fetch(target.toString(), init);
  const body = await resp.text();
  return new NextResponse(body, {
    status: resp.status,
    headers: {
      "Content-Type": resp.headers.get("Content-Type") ?? "application/json",
      "X-ORCAST-Partner-Tier": tier,
    },
  });
}

export async function GET(req: NextRequest, ctx: { params: { path: string[] } }) {
  return handle(req, ctx.params.path);
}

export async function POST(req: NextRequest, ctx: { params: { path: string[] } }) {
  return handle(req, ctx.params.path);
}

async function handle(req: NextRequest, path: string[]) {
  if (isIpLimited(clientIp(req))) {
    return NextResponse.json({ error: "Rate limit exceeded" }, { status: 429 });
  }
  const raw = req.headers.get("x-orcast-partner-key") ?? "";
  const partner = await resolvePartner(raw);
  if (!partner) {
    return NextResponse.json({ error: "Invalid or missing X-ORCAST-Partner-Key" }, { status: 401 });
  }
  if (isKeyOverDailyLimit(partner.keyId, partner.tier)) {
    return NextResponse.json({ error: "Daily partner quota exceeded" }, { status: 429 });
  }
  return forward(req, path, partner.tier);
}
