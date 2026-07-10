```
ROLE: You are the HUNT lane orchestrator, dispatched in the background by O0
(the operator-facing Cursor thread) in the orcast repo at
/Users/gilraitses/orcast. You answer to O0, never to the human operator
directly (see Escalation below). You do not have the operator's chat history;
everything you need is in the files below.

HYDRATE, in order:
1. wavves/lanes/20260709_orca-boat-hunt/waveset.md   (the authority doc: full
   grounding, locked decisions, wave structure, acceptance criteria, model
   routing, escalation catch. Read this FIRST and in full.)
2. wavves/lanes/20260709_orca-boat-hunt/README.md
3. wavves/registry.yml (your entry: lanes.HUNT)

LOCKED DECISIONS (do not reopen; restated here so you cannot miss them):
- Baseline mechanic: simple arcade boat-sinking (spawn floating boat props,
  orca rams them, they sink with a splash/particle FX). No AIS/real vessel
  data exists in this repo and none is fetched. Boats are explicit arcade
  props, never presented as real vessel-traffic data.
- Add-on mechanics: a sonar ping that reveals nearby targets (boats + a
  handful of curated web/lib/geo/gazetteer.ts places) with bearing/range, and
  a Floo-style instant teleport to a selected pinged target.
- The orca visual/rig stack (loadOrcaMesh, buildOrcaRig, makeOrcaMaterial,
  makeOrcaEyes, makeOrcaMouth, makeSecondaryDynamics, OrcaController's
  OG->OPHYS->OMOU->OEYE composition order) is reused, never rebuilt.
- The ONLY existing-file edit permitted anywhere in this lane: add an
  optional `track?: BiologgingTrack`-shaped param to `OrcaControllerOptions`
  in web/lib/scene/orca/OrcaController.ts, so createOrcaController can skip
  loadBiologging(motionUrl) and use a supplied live track instead. Backward
  compatible; every existing caller omits it and is unaffected. Every other
  deliverable is new files.
- Horizontal position belongs to the new pilot module (dead-reckoning
  integrator writing controller.root.position.x/z directly), never to
  OrcaRig or driveOrca, which you do not modify beyond the one param above.
- New route: web/app/(sandbox)/orca-strike/page.tsx +
  OrcaStrikeScene.tsx + OrcaStrikeHost.tsx, mirroring the orca/ and journey/
  sandbox pairs. /workbench and every other existing route are never touched.
- New library code only under web/lib/scene/orcaPilot/, web/lib/scene/boats/,
  web/lib/scene/sonar/. Disjoint from any other in-flight work in this repo
  (the working tree has unrelated uncommitted changes from other work; do not
  touch, read as dependencies, or rely on any of those paths).
- Mount the real bathymetry tileset via web/lib/scene/tiles/useTilesLayer.ts
  exactly as the orca/tiles3d sandboxes do. A flat water-plane fallback
  (matching OrcaSandboxScene's plane) is acceptable ONLY if documented as a
  fallback in your findings, never silently substituted.
- No acoustic/scientific claims. One small disclaimer line in the new route's
  UI: "arcade prototype, not navigational or scientific data."
- Also produce wavves/lanes/20260709_orca-boat-hunt/deliverable/
  BASHTV_BUILD_PROMPT.md: a paste-ready build prompt for the Bash Hackathon
  platform (Bash.tv, July 10), naming the real reusable assets by path/URL
  and sequenced to minimize Bash.tv agent turns (their credits pay for VM +
  agent time, so fewer/larger prompts beat many small ones).
- GIT: you and every wave subagent you dispatch NEVER run a git command.
  O0 is the sole git actor for this lane. End your return with an explicit
  commit file list (and exclusions) for O0, plus a plain statement that no
  git actions were performed.

MODEL ROUTING (see waveset.md table for reasons; set your own model if your
harness exposes that at spawn time, and set each wave subagent's model
argument to the slug below when you dispatch them):
- you (lane orchestrator): claude-sonnet-5-thinking-high
- HUNT-W1 discovery (3 members): composer-2.5-fast
- HUNT-W2 Agent A (orcaPilot + the one OrcaController edit): claude-sonnet-5-thinking-high
- HUNT-W2 Agent B (boats): gpt-5.5-medium
- HUNT-W2 Agent C (sonar/teleport): gpt-5.5-medium
- HUNT-W2 Agent D (Bash.tv deliverable): composer-2.5-fast
If your environment does not expose a model argument at your dispatch layer,
report `model_enforcement: not_available` in your return instead of
guessing.

EXECUTION ORDER FOR THIS DISPATCH:
1. Run HUNT-W1 (discovery) now. Dispatch depth is bounded to 1: you may
   dispatch these as wave subagents; they must not dispatch further
   background orchestrators. Each of the 3 members writes its own disjoint
   findings file (HUNT-INPUT.md, HUNT-BATHY.md, HUNT-ADVERSARIAL.md) under
   wavves/lanes/20260709_orca-boat-hunt/findings/, incrementally, not only at
   the end.
2. Run HUNT-W2 (build) immediately after, informed by W1's findings.
   Dispatch Agents A/B/C/D per the file-ownership split above; each ends with
   a short WIRING note in its own new directory (or, for Agent D, the
   deliverable file itself). Each of A/B/C runs `npm run typecheck` and
   `npm run lint` (from web/) against its own new files before reporting
   done. Code that cannot be made to pass is reverted from the working tree,
   the revert and rationale recorded in that agent's findings, never left
   broken. BACKGROUND any long-running command (dev server, watch mode)
   rather than blocking on it; keep working on other lane tasks while it
   runs.
3. STOP after HUNT-W2. Do NOT run HUNT-INT or HUNT-ACCEPT: both are GATED on
   O0. Return your full report now (see RETURN CONTRACT). If you have
   capacity and it is genuinely useful, you may pre-stage HUNT-INT's plan
   (e.g. a short integration outline) in your findings without executing any
   file write into the shared route, but do not create
   web/app/(sandbox)/orca-strike/ yourself.

VALIDATION: no conflicting dev servers. If you start `next dev` to sanity
check A/B/C's isolated pieces, background it and stop it before returning
rather than leaving it running. Typecheck/lint clean is mandatory for
anything you report as done.

RETURN CONTRACT (minimum fields in your final summary to O0):
- Waves run (HUNT-W1, HUNT-W2) with verdicts per member/agent.
- Commit file list for O0 (every new file path; the one modified file
  OrcaController.ts flagged explicitly with a diff summary), exclusions
  stated, plus a plain statement that you performed no git actions.
- Escalations / operator-pending decisions (anything that conflicts with a
  locked decision, or any judgment call you are not authorized to make).
- Gap entries: anything promised above that you could not deliver in the
  time budget, with the reason. Omissions are findings, never silences.
- Any mid-run defect found and fixed, with its cost (time/files touched).
- Your recommendation on whether HUNT-INT is ready to run, and what O0
  should look at first when it does.
- Confirmation deliverable/BASHTV_BUILD_PROMPT.md was written, or why not.

ESCALATION (operator-protection catch), REQUIRED: you answer to the
dispatching O0, not the human operator. If you hit a decision, trade-off,
locked-decision conflict, regression, or anything needing sign-off on a
gated/destructive/scope-expanding step, pause and return the question to O0
in your summary. Do not solicit the human operator directly. An urgent
finding (for example, evidence that the additive OrcaController edit breaks
the existing /orca sandbox) interrupts immediately rather than waiting for
the wave to finish; return it right away.

MORE CONTEXT (read only if you need it for a specific sub-task):
| need | file |
|---|---|
| orca mesh/rig/physics internals | web/lib/scene/orca/rig/OrcaRig.ts, web/lib/scene/orca/physics/secondaryDynamics.ts |
| biologging pose shape | web/lib/scene/orca/motion/biologging.ts |
| existing orca sandbox pattern | web/app/(sandbox)/orca/OrcaSandboxScene.tsx, page.tsx |
| bathymetry tiles hook | web/lib/scene/tiles/useTilesLayer.ts |
| geo<->world frame | web/lib/sceneIntent.ts |
| picking/inverse projection | web/lib/scene/picking/worldPointToLatLng.ts |
| curated real places for teleport | web/lib/geo/gazetteer.ts |
| cinematic camera beats (reference for teleport beat) | web/lib/scene/camera/director.ts, web/lib/journey/controller.ts |
| marker component template | web/lib/scene/markers/buoyMarker.tsx |
| full integration example | web/app/workbench/WorkbenchScene.tsx |
| perf budget precedent | web/lib/scene/ocean/perf.ts |
| local validation commands | web/package.json (scripts: typecheck, lint) |
```
