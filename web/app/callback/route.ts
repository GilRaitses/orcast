import { handleAuth } from "@workos-inc/authkit-nextjs";

// WorkOS redirects here after a successful hosted sign-in. handleAuth exchanges
// the code for a session and sets the wos-session cookie, then sends the user on.
export const GET = handleAuth({ returnPathname: "/moderation" });
