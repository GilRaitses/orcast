"use client";

import Link from "next/link";
import Tooltip from "./Tooltip";

// Anonymous-first action gating (HANDOFF_CHARTER B2): write-actions render as a
// ghosted button. Anonymous users see why and get an inline sign-in/sign-up
// link via the collision-aware Tooltip; surfaces are never hidden.
interface GatedActionProps {
  label: string;
  signedIn: boolean;
  reason?: string;
  onAct?: () => void;
  redirectTo?: string;
}

export default function GatedAction({
  label,
  signedIn,
  reason = "Sign in to do this",
  onAct,
  redirectTo,
}: GatedActionProps) {
  if (signedIn) {
    return (
      <button type="button" className="btn" onClick={onAct}>
        {label}
      </button>
    );
  }

  const loginHref = redirectTo
    ? `/login?returnTo=${encodeURIComponent(redirectTo)}`
    : "/login";
  const signupHref = redirectTo
    ? `/signup?returnTo=${encodeURIComponent(redirectTo)}`
    : "/signup";

  return (
    <Tooltip
      interactive
      content={
        <div className="gated-tip">
          <p className="gated-tip-reason">{reason}</p>
          <div className="gated-tip-links">
            <Link href={loginHref} className="chip">
              Sign in
            </Link>
            <Link href={signupHref} className="chip">
              Create account
            </Link>
          </div>
        </div>
      }
    >
      <button type="button" className="btn ghost gated-button" aria-disabled="true">
        {label}
        <span className="gated-lock" aria-hidden>
          {" "}
          (sign in)
        </span>
      </button>
    </Tooltip>
  );
}
