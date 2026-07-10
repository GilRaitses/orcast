```
ROLE: You are ONE of four parallel, disjoint reviewers in the HCHK
adversarial check lane, in the git repo at /Users/gilraitses/orcast. You are
READ-ONLY: you write exactly one findings file and touch nothing else. No
code edits, no commits, no git commands, no implementation plan.

HYDRATE, in order:
1. wavves/lanes/20260709_orca-boat-hunt-check/waveset.md (this check lane's
   authority doc: your lens assignment is in the "Waves" section under your
   wave id).
2. wavves/lanes/20260709_orca-boat-hunt/waveset.md (the HUNT lane's plan you
   are checking, especially the HUNT-INT/HUNT-ACCEPT sections and the
   acceptance criteria).
3. wavves/lanes/20260709_orca-boat-hunt/decisions/HUNT-bathy-fidelity.md and
   HUNT-orbit-coexistence.md (two locks you must NOT reopen, only build on).
4. wavves/lanes/20260709_orca-boat-hunt/findings/HUNT-ORCHESTRATOR-SUMMARY.md
   (what was actually built and self-reported).
5. The actual delivered code: web/lib/scene/orcaPilot/ (input.ts,
   deadReckoning.ts, PilotTrack.ts, chaseCamera.ts, index.ts, WIRING.md),
   web/lib/scene/boats/ (BoatEntity.ts, spawnBoats.ts, collision.ts,
   sinkAnimation.ts, BoatMarker.tsx, index.ts, WIRING.md), web/lib/scene/sonar/
   (radarTargets.ts, ping.ts, teleport.ts, index.ts, WIRING.md), and the diff
   on web/lib/scene/orca/OrcaController.ts (run `git diff
   web/lib/scene/orca/OrcaController.ts` to see it).

YOUR JOB: read your assigned lens in HCHK's waveset.md carefully (grounding /
contradictions / completeness / adversarial - you are told which one you are
in your own dispatch). Write ONLY
wavves/lanes/20260709_orca-boat-hunt-check/findings/HCHK-<your-lens>.md.
Every finding cites an exact file and, where applicable, an exact line range
or function/symbol name. A finding without a cited path is not a finding,
it is a guess, and must not be included. Write incrementally as you find
things, not only at the end.

GROUND RULES:
- You are read-only. You may run read-only shell commands (git diff, git
  status, grep, cat, tsc --noEmit for verification of a specific claim) but
  you never write to any file except your own single findings file, and you
  never run a git command that mutates anything (no add/commit/stash/checkout
  -b, etc; `git diff`/`git status`/`git log` are fine, read-only).
- Do not propose reopening HUNT-bathy-fidelity or HUNT-orbit-coexistence. You
  may flag a NEW risk either lock introduces, but the picks themselves are
  locked.
- Do not write an implementation plan for HUNT-INT. Findings only.
- If you find something that looks like an urgent, active regression (for
  example, a claim that would make HUNT-INT actively break something already
  working), say so explicitly at the top of your findings file, but still
  only write to your own file. There is no human operator to escalate to
  directly in this dispatch; state it clearly in your findings for O0 to
  read at reconciliation.

RETURN: when done, your final message should summarize your own findings
file's top 3-5 items (with citations) so the dispatching context can
reconcile quickly, but the durable artifact is the findings file itself.
```
