import { authkitMiddleware } from "@workos-inc/authkit-nextjs";
import type { NextFetchEvent, NextRequest } from "next/server";
import { NextResponse } from "next/server";

// ORCAST_REQUIRE_LOGIN gates the whole site behind WorkOS AuthKit login. It is set
// only on the product deployment (orcast.aimez.ai); the public hackathon build
// (orcast-h0) leaves it unset. Both run identical code, so the behavior is env-driven
// rather than forked.
//
// Flag set: every page requires a session (unauthenticated visitors are redirected to
// hosted sign-in). The auth routes and the key-authenticated /api surface stay open so
// the backend proxy, agents, and partner API keep working.
//
// Flag unset (lazy mode): the middleware only refreshes the wos-session cookie so
// withAuth() works everywhere; pages stay public unless they call withAuth() themselves.
const requireLogin = process.env.ORCAST_REQUIRE_LOGIN === "1";

const authMiddleware = authkitMiddleware(
  requireLogin
    ? {
        middlewareAuth: {
          enabled: true,
          unauthenticatedPaths: ["/login", "/sign-in", "/signup", "/callback", "/api/:path*", "/social/:path*"],
        },
      }
    : {},
);

// Link-preview crawlers (LinkedIn, Twitter/X, Facebook, Slack, Discord, WhatsApp,
// Telegram) carry no session. When the full-site gate is on, a redirect to
// hosted sign-in is all they ever see, so a shared orcast.aimez.ai link shows no
// title, description, or image. These bots are read-only and never reach an
// authenticated surface, so they skip the gate by user agent instead of by path.
const CRAWLER_UA =
  /facebookexternalhit|Twitterbot|LinkedInBot|Slackbot|Discordbot|WhatsApp|TelegramBot|Pinterest/i;

export default function middleware(request: NextRequest, event: NextFetchEvent) {
  if (requireLogin && CRAWLER_UA.test(request.headers.get("user-agent") ?? "")) {
    return NextResponse.next();
  }
  return authMiddleware(request, event);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
