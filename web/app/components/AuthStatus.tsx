import Link from "next/link";
import { headers } from "next/headers";
import { withAuth, signOut } from "@workos-inc/authkit-nextjs";
import { agentUserFromHeaders } from "@/lib/agentAuth";

// Server component: WorkOS session, or automation agent when X-ORCAST-Agent-Key matches (Playwright demo).
export default async function AuthStatus() {
  const agent = agentUserFromHeaders(headers());
  if (agent) {
    return (
      <div className="auth-status">
        <span className="muted auth-email">{agent.email}</span>
        <span className="badge auth-automation">Automation</span>
      </div>
    );
  }

  const { user } = await withAuth();

  if (!user) {
    return (
      <div className="auth-status">
        <Link href="/signup" className="btn ghost auth-btn">
          Create account
        </Link>
        <Link href="/login" className="btn auth-btn">
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="auth-status">
      <span className="muted auth-email">{user.email}</span>
      <form
        action={async () => {
          "use server";
          await signOut();
        }}
      >
        <button type="submit" className="btn ghost auth-btn">
          Sign out
        </button>
      </form>
    </div>
  );
}
