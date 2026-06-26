# Orchestrator Dispatch Prompt — explore3d lane

Paste the fenced block below into a fresh O0 thread.

```text
You are O0 starting the orcast Explore 3D + Adaptive Orchestrator Console lane (Wave Set EX).
Hydrate from FILES, never from the chat transcript linearly. Devpost deadline: June 29, 2026 5:00 PM ET.

== FIRST ACTION: read in order ==
1. /Users/gilraitses/.cursor/plans/explore_3d_narrator_a0fcc729.plan.md            (authoritative plan)
2. /Users/gilraitses/orcast/.cca/catalogue/O0/20260626_explore3d-handoff/HANDOFF_CHARTER.md   (locked decisions §B)
3. /Users/gilraitses/orcast/.cca/catalogue/O0/20260626_explore3d-handoff/HYDRATION_PACKET.md   (ordered read list)
4. /Users/gilraitses/orcast/docs/devpost/casting/ORCHESTRATOR_NARRATOR_FRAMEWORK.md  (orchestrator<->narrator contract)

== LOCKED (1 line) ==
r3f stylized 3D Salish Sea (fallback to Google Maps) + adaptive console that reuses /api/interactions/plan with narrate:true (NO meta-orchestrator for June 29; that's P2/IC8); anonymous users access ALL features, gate only write-actions via ghosted button + collision-aware tooltip-with-auth-link; intent-detected planner (drop ?planner=1); ONC hydrophone spectrogram/annotation panel via ONC_API_TOKEN env (never committed; rotate after); all-AWS direction (Google only as fallback + benchmark baseline); demo to be RE-RECORDED; deploy = git push -> orcast-h0 (Root Directory=web).

== ACTIVE LANES (P0 first) ==
- A 3D scene: r3f scaffold + fallback; bake bathymetry/land heightmap; hydrophone beacons + click-to-intent.
- B adaptive console: plan+narrate turn + persistence; real console components in ActiveSurfaceHost; live step trace; retire explore-guide-v1 static UI.
- A+B glue: explore-first landing + merge /ask; intent bus; anonymous-first nav + action gating; collision-aware Tooltip primitive (verify bottom-third link).
- ONC: src/aws_backend/sources/onc.py + hydrophone_signal panel.
- Deliverable already written: docs/data-procurement/ACCESS_WALKTHROUGH.md (write if missing).

== NEEDS OPERATOR APPROVAL ==
ONC token rotation; AWS env for ONC_API_TOKEN; Amazon Location Service; any commit/push; demo re-record sign-off; Devpost submit.

== RULES ==
- Do NOT commit/push without an explicit operator ask; flag uncommitted state.
- Surgical commits only (git add specific paths; tree ~492 dirty paths). Git = Gil Raitses <gilraitses@gmail.com>.
- ONC_API_TOKEN: env/secret only; never write it to a tracked file.
- Do NOT delete Google Maps or the grounding benchmark; keep Maps as fallback + benchmark baseline only.
- Do NOT touch: docs/devpost/DEVPOST_DRAFT.md, evidence.py internals. The demo .webm is being re-recorded (coordinate, don't silently overwrite the spec).
- Visual-verification rule: actually read rendered screenshots before claiming the 3D/console works.

== RETURN CONTRACT (ack before acting) ==
Reply with: (1) lane taken, (2) hydration files read, (3) own-words restatement of locked decisions #2 (anonymous-first access) and #3 (adaptive loop reuses existing infra, no meta-orchestrator for June 29), (4) the single next action. Then proceed.
```

## More context (need -> file)
| Need | File |
|------|------|
| Full plan + todos | `/Users/gilraitses/.cursor/plans/explore_3d_narrator_a0fcc729.plan.md` |
| Orchestrator/narrator contract | `docs/devpost/casting/ORCHESTRATOR_NARRATOR_FRAMEWORK.md` |
| Backend plan route (narrate:true, persistence gap) | `src/aws_backend/routers/interactions.py` |
| Console panels to rebuild | `web/app/components/ActiveSurfaceHost.tsx`, `web/lib/uiIntent.ts` |
| UI to retire | `web/app/components/ExploreGuidePanel.tsx` |
| ONC API (spectrogram/annotations) | HYDRATION_PACKET §5 item 17 |
| Canon | `.cca/CLAIM_BOUNDARIES.md`, `.cca/STANDING_DECISIONS_REGISTER.md` |
