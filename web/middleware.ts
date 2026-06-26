import { authkitMiddleware } from "@workos-inc/authkit-nextjs";

// Lazy mode: refreshes the wos-session cookie so withAuth() works everywhere
// (server components and route handlers, including the api/be proxy). It does
// NOT force authentication globally; pages stay public unless they call
// withAuth() and act on the result.
export default authkitMiddleware();

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
