# A0 — Agent demo automation charter

Date: 2026-06-23  
Wave set: **A** (Agent demo automation)  
Predecessor: Wave Set **S** complete (S4 `s-gate` PASS)  
Capstone: **H1** manual Devpost submit (depends on **A5** `a-gate` PASS + `demo-walkthrough.webm`)

## Purpose

Record the same 8-beat demo narrative as [DEMO_STORYBOARD.md](../DEMO_STORYBOARD.md) on https://orcast-h0.vercel.app **without WorkOS sign-in friction**, using the existing `ORCAST_AGENT_KEY` automation identity and Playwright header injection.

Manual alternative: sign in with WorkOS before recording ([DEMO_STORYBOARD.md](../DEMO_STORYBOARD.md) Option B).

## Prerequisite

```bash
export VERCEL_TOKEN=...
bash tools/testing/setup_agent_user.sh   # writes .agent-credentials.env
bash tools/testing/setup_demo_maps.sh    # NEXT_PUBLIC_MAPS_KEY on Vercel + GCP referrer checklist
cd web && npx vercel deploy --prod
```

See [tools/testing/AGENT_USER.md](../../../tools/testing/AGENT_USER.md).

## Exit bar (zero open caveats)

Wave Set **A** closes only when every row is closed.

| ID | Caveat | Lane | Closed when |
|----|--------|------|-------------|
| A-C1 | `/api/interactions/plan` rejects automation | A1 | `curl` with `X-ORCAST-Agent-Key` → HTTP 200 + `ui_intent.panels` |
| A-C2 | Planner UI sends wrong `agent_id` → 400 | A3 | `ExploreGuidePanel` uses `surface-planner-v1` in planner mode |
| A-C3 | Journal / moderation 401 without WorkOS cookie | A1 | `agent_smoke.py` journal + moderation + plan PASS |
| A-C4 | Nav shows **Sign in** during headed demo | A3 | `AuthStatus` shows automation identity when valid agent key header on request |
| A-C5 | No reproducible wave gate | A4/A5 | `./tools/waves/run-gate.sh a-gate` PASS |
| A-C6 | Operator path undocumented | A0/A5 | AGENT_USER, DEMO_NO_CRED, H1_MANUAL list `a-gate` prerequisite |
| A-C7 | Not in waves registry | A0 | A0–A5 in `waves.registry.yaml` + WAVES_REGISTRY.md |
| A-C8 | Google Maps error on map beats | A5 | `./tools/waves/run-gate.sh a-maps` PASS on prod |
| A-C9 | No recordable video artifact | A5 | `docs/devpost/figures/_demo-run/demo-walkthrough.webm` (≥120s) from `a-video-gate` |

### Deferred (not A caveats)

| Track | Notes |
|-------|-------|
| Beat 7 live AWS Console | Static slide by design — [DEMO_NO_CRED_STORYBOARD.md](../DEMO_NO_CRED_STORYBOARD.md) |
| WorkOS manual sign-in | Option B in DEMO_STORYBOARD — not required for `a-gate` |

## Wave breakdown

### A1 — Proxy auth unify

**Scope:** `web/lib/agentAuth.ts`; `/api/be` and `/api/interactions/plan` proxies accept `X-ORCAST-Agent-Key` or WorkOS session.

**Acceptance:** `python3 tools/testing/agent_smoke.py` — plan panels line prints.

### A2 — Playwright harness

**Scope:** `web/playwright.config.ts`, `web/e2e/*`, npm demo scripts, [DEMO_NO_CRED_STORYBOARD.md](../DEMO_NO_CRED_STORYBOARD.md).

**Acceptance:** `npm run demo:screenshots` PASS on prod with `.agent-credentials.env`.

### A3 — Demo UX truth

**Scope:** `AuthStatus` automation chip via request headers; `ExploreGuidePanel` planner agent id.

**Acceptance:** Headed walkthrough nav shows `agent@orcast.dev · Automation`, not Sign in.

### A4 — Auth/API gate

**Scope:** `a-doc-grep.sh`, `agent_smoke.py`, screenshot walkthrough.

### A5 — Video-complete gate

**Scope:** Maps infra (`setup_demo_maps.sh`), content waits in spec, same-origin slides, `a-video-gate.sh`.

**Acceptance:** `./tools/waves/run-gate.sh a-gate` produces [`demo-walkthrough.webm`](../figures/_demo-run/demo-walkthrough.webm).

## Execution order

1. A0 (charter) — **done**
2. A1 proxy auth — **done**
3. A2 Playwright harness — **done**
4. A3 AuthStatus chip — **done**
5. A4 auth/API gate — **done**
6. A5 video-complete — **done** (`demo-walkthrough.webm` ~134s)
7. **H1** manual submit — [H1_MANUAL_SUBMIT.md](H1_MANUAL_SUBMIT.md)

## Operator workflow (post-A5)

```bash
./tools/waves/run-gate.sh a-gate

# Artifact for Devpost (or re-narrate live over headed browser):
open docs/devpost/figures/_demo-run/demo-walkthrough.webm

source .agent-credentials.env
cd web
PW_SLOW_MO=500 npm run demo:walkthrough
```
