# O0 Handoff Charter — Explore 3D + Adaptive Orchestrator Console lane

**Lane:** explore3d (Wave Set EX)
**Date:** 2026-06-26 (America/New_York)
**Repo:** `/Users/gilraitses/orcast` — branch `main` (deploy: Git push -> Vercel project `orcast-h0`, Root Directory=`web`, verified green)
**Deadline context:** Devpost submission June 29, 2026 5:00 PM ET.

## A. Purpose
A freshly rotated O0 executes the `explore_3d_narrator` plan: make Explore the landing surface as a react-three-fiber 3D Salish Sea (bathymetry + land + hydrophones, scripted fly-throughs, click-to-intent), driven by an adaptive orchestrator-mediated console that replaces the stale `explore-guide-v1` static UI. Every turn runs orchestrator(plan) -> managed agents/skills -> orchestrator(narrate) -> dynamic console rendering, with the live step-log shown as the orchestrator-in-the-loop trace. Anonymous users access ALL features; only write-actions are gated. Plan from FILES (see HYDRATION_PACKET), not the chat transcript.

## B. Decisions that are LOCKED — do not reopen
1. **3D engine = react-three-fiber** (three + @react-three/fiber + @react-three/drei), stylized Salish Sea; lazy-loaded; graceful fallback to the existing Google Maps `MapHero` if WebGL/asset fails.
2. **Anonymous-first access:** every surface/feature is visible and usable by anonymous users, including the adaptive planner/console. Gate ONLY write-actions (submit annotation, promote/hold/reject, publish journal) with a ghosted button + collision-aware tooltip carrying a sign-in/sign-up link. Do NOT hide nav/surfaces by permission. `/api/interactions/plan` is exposed publicly through the proxy; keyed T2/T3 skills stay server-side gated (planner omits those panels for anon).
3. **Adaptive loop reuses existing infra:** drive turns through `/api/interactions/plan` with `narrate:true`; add turn persistence to the plan route; render `ui_intent.panels` as real console components and `steps[]` as the live trace. Do NOT build the deferred LLM/multi-agent meta-orchestrator for June 29 (that is P2, per IC8).
4. **Intent-detected planner:** drop `?planner=1`; classify intent per turn; ambiguous intent -> narrator asks one clarifying question (see ORCHESTRATOR_NARRATOR_FRAMEWORK.md).
5. **ONC integration:** token held ONLY as env `ONC_API_TOKEN` (App Runner secret + local `.env.local`); NEVER written to any tracked file. Relay pre-generated spectrograms (`archivefile` PNG / `dataProductCode=HSD`) + station metadata; new `hydrophone_signal` console panel; annotation affordance is auth-gated. Operator must ROTATE the ONC token after the hackathon (it was shared in plaintext).
6. **All-AWS direction:** stop adding Google deps in the product. Geocoding -> Amazon Location Service (or self-hosted). Google Maps stays ONLY (a) as the flagged-deprecated June-29 fallback and (b) as the WP2 grounding-benchmark baseline (`tools/testing/grounding_parallel_rag.py`) — that usage is the thesis and is NOT product infra. Multiphysics layers over the 3D substrate are P2.
7. **Tooltip-with-link is a real bug to fix:** one collision-aware Tooltip primitive (flip by viewport space; hover safe-bridge so the link stays clickable; focus/escape dismiss). Must be verified specifically with a link in the bottom third of the screen.
8. **Demo video = RE-RECORD** against the new UI before submit; re-run the video gate after P0. The frozen Maps `.webm`/spec is superseded for this submission.
9. **Deploy:** Git push to `main` auto-deploys `orcast-h0` (Root Directory=`web`). Surgical commits only (tree ~492 dirty paths); git identity Gil Raitses <gilraitses@gmail.com>; do NOT commit/push without an explicit operator ask.

## C. Registry snapshot
| Slice | What shipped | Status |
|-------|--------------|--------|
| Planning + framework | plan + ORCHESTRATOR_NARRATOR_FRAMEWORK.md written | done |
| SD-H deploy + SDR | prod green; STANDING_DECISIONS_REGISTER.md live | done (prior lane) |
| EX P0 (3D + console) | scoped, not started | pending execution |
| ONC adapter | spec'd; token provided | pending |

## D. Active lanes (P0 first)
- Workstream A (3D scene): r3f scaffold + fallback; bathymetry/land heightmap asset; hydrophone beacons + click-to-intent.
- Workstream B (adaptive console): plan+narrate turn + persistence; real console components in `ActiveSurfaceHost`; live orchestrator trace; retire `explore-guide-v1` static UI.
- A+B glue: explore-first shell + merge `/ask`; intent bus from scene; anonymous-first nav + action gating; tooltip primitive.
- ONC: adapter + `hydrophone_signal` panel.

## E. Needs operator approval
ONC token rotation; any commit/push; Amazon Location Service enablement; AWS/App Runner env for `ONC_API_TOKEN`; demo re-record sign-off; Devpost submit.

## F. Open gate / metric state
- Deploy: `orcast-h0` green via Git (verified 2026-06-26, commit `8e5c6ee` / `gfgdba0t5`).
- `./tools/waves/run-gate.sh s-doc-grep`: RED on two pre-existing stale assertions (SDR O-2) unrelated to EX — drawio path + `next_wave_set` (decision pending).
- Video gate must be re-run after the demo re-record.

## G. Return contract (ack before acting)
Reply with: (1) lane taken; (2) hydration files read; (3) own-words restatement of locked decisions #2 (anonymous-first access) and #3 (adaptive loop reuses existing infra, no meta-orchestrator for June 29); (4) the single next action. When a lane completes: deliverables (exact paths), gate state, any P0/P1 gap + resolution, any claim emitted not in CLAIM_BOUNDARIES.md, next operator action.

## H. Provenance pointer
Planning thread STEP_LOG: this folder's `STEP_LOG.md`. Authoritative plan: `/Users/gilraitses/.cursor/plans/explore_3d_narrator_a0fcc729.plan.md`.
