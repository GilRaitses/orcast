# WorkOS AuthKit — email signup demo

ORCAST uses [WorkOS AuthKit](https://workos.com/docs/user-management) for reviewer login
(`/login`, `/signup`, `/callback`). Public forecast/gates stay open without auth.

## Live flow (already wired)

1. User clicks **Create account** on [orcast-h0.vercel.app](https://orcast-h0.vercel.app/signup).
2. Redirect to hosted AuthKit (`*.authkit.app`) with Google, Microsoft, GitHub, Apple, or email.
3. After auth, WorkOS redirects to `https://orcast-h0.vercel.app/callback` and sets the session cookie.
4. Protected proxy routes (moderation, decision records) require that session.

## Two signup paths (different inbox behavior)

| Path | Inbox email? |
|------|----------------|
| **Continue with Google** (Gmail) | No — OAuth only; you land back on ORCAST signed in |
| **Email + password** (your Gmail address) | Yes — WorkOS sends a **verification / magic link** from WorkOS |

For a demo where Gmail receives mail, use **email signup** with your Gmail address, not Google OAuth.

## Dashboard setup (one-time)

In [WorkOS Dashboard](https://dashboard.workos.com):

1. **Redirect URIs** — must include `https://orcast-h0.vercel.app/callback` (and `http://localhost:3000/callback` for local dev).
2. **Authentication → Methods** — enable Email + Password (and/or Magic Auth) plus Google if desired.
3. **Branding** (optional, affects hosted AuthKit UI + how emails *look*, not email body text):
   - Upload logo / set accent color `#4fb8d8`
   - Use the preview page picker to view `sign-up`, `email-verification`, etc.
   - **Copy:** click headings/links *in the auth page preview* to edit signup/sign-in page text (auto-localized)
   - **Email previews** in Branding are **read-only previews** of WorkOS-authored mail (logo/colors applied). There is no subject/body editor there.

**You cannot paste custom verification-email copy in the dashboard** on the default WorkOS mail path. Verification mail is sent by WorkOS from `welcome@workos-mail.com` with WorkOS template text + your branding assets. To fully own email copy you need either [send your own email](https://workos.com/docs/authkit/custom-emails) (listen to WorkOS events) or a [custom email provider](https://workos.com/docs/authkit/custom-email-providers) (deliverability/domain control; content still WorkOS-authored unless you send your own).

## What the verification email looks like (default)

WorkOS sends **email verification** from `welcome@workos-mail.com` when someone signs up with email+password. Subject/body are WorkOS-authored; your logo and colors from Branding may appear in the HTML. For the demo you do **not** need to edit anything in WorkOS beyond redirect URIs + enabling email signup.

Optional: set your **team / environment display name** to **ORCAST** in WorkOS settings so the sender context matches your app (exact menu label varies by dashboard version).

Vercel env vars (already documented in `web/.env.example`):

- `WORKOS_API_KEY`, `WORKOS_CLIENT_ID`, `WORKOS_COOKIE_PASSWORD` (≥32 chars)
- `NEXT_PUBLIC_WORKOS_REDIRECT_URI=https://orcast-h0.vercel.app/callback`

WorkOS delivers auth mail on the default path; no SendGrid/SES required at hackathon scale (AuthKit free tier: first 1M MAUs/month).

## What ORCAST does *not* send yet

- “Your shore report was received / approved” — needs SES or Resend (transactional product email, separate from WorkOS).
- Research copilot export / itinerary email — future wave; see product plan in handoff.

## Demo script (video)

1. Open `/moderation` → redirected or prompted to sign in.
2. **Create account** → AuthKit hosted page.
3. Either **Continue with Google** (fast, no inbox) or **email signup** (show Gmail verification).
4. Return to ORCAST → email shown in top bar → approve a moderation card.

## WorkOS CLI vs REST API

There is **no official WorkOS CLI** for AuthKit configuration. Use the dashboard for redirect URIs, auth methods, and visual branding (not custom verification email body text).

For **programmatic user management** (seeding demo accounts, invitations), use the [User Management REST API](https://workos.com/docs/reference/user-management) with your `WORKOS_API_KEY`:

```bash
export WORKOS_API_KEY="sk_..."

# Create a user (email+password — they still verify via WorkOS email flow)
curl -s https://api.workos.com/user_management/users \
  -u "$WORKOS_API_KEY:" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@gmail.com",
    "password": "YourDemoPassword123!",
    "email_verified": false
  }'

# Send a password reset / magic auth (triggers WorkOS email)
curl -s https://api.workos.com/user_management/password_reset \
  -u "$WORKOS_API_KEY:" \
  -H "Content-Type: application/json" \
  -d '{"email": "you@gmail.com"}'
```

**What the API cannot replace:** OAuth provider setup, redirect URI list, AuthKit page branding. It can create users and trigger password-reset mail, but **not** custom verification email copy on the default WorkOS mail path.

**Recommended next step:** skip email template editing — enable Email + Password, confirm redirect URI, then sign up on ORCAST with **email+password** (not Google OAuth) and confirm the WorkOS verification message in Gmail.
