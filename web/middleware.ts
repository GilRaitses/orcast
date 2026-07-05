import { authkitMiddleware } from "@workos-inc/authkit-nextjs";

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

export default authkitMiddleware(
  requireLogin
    ? {
        middlewareAuth: {
          enabled: true,
          unauthenticatedPaths: ["/login", "/sign-in", "/signup", "/callback", "/api/:path*", "/social/:path*"],
        },
      }
    : {},
);

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
