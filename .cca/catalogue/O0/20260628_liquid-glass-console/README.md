# LGC — Liquid-Glass Research Console

Lane home for porting the pax liquid-glass "Friend" console into ORCAST as a
whale-behavior research tool: frosted-glass surfaces over the live map and
probability cloud, single-focus center model, self-hiding chat/dock, edge
panels, consent-gated layout persistence.

## Files
- `WAVESET_CHARTER.md` — authority: locked decisions, grounding, waves W0-W7, gates, escalation, return contract.
- `ORCHESTRATOR_DISPATCH_PROMPT.md` — paste block for the fresh-thread owner + a more-context table.
- `TOKEN_HANDOFF.md` — the cross-lane contract: the Part A glass tokens LGC-W4 lands into `web/app/globals.css :root`, the M3 no-blur rule, and the downstream consumers (TWIN W-LABELS, the demo LGC-styled beats) blocked until they land.
- `LIQUID_GLASS_CONSOLE_MANIFEST.md` (repo root) — the design tokens, contracts, honesty locks, and rubric M1-M10.
- `gate_captures/`, `gate_screenshots/` — created at W5+ for runnable gate evidence and Read-examined frames.

## How to start
Open a new thread and paste the one-liner O0 emitted, or paste the fenced block
in `ORCHESTRATOR_DISPATCH_PROMPT.md`. The new thread hydrates from files, runs W0
(read-only research), and pauses at the target-surface gate for O0.

## Status
chartered, confirmed 2026-06-28 — awaiting fresh-thread dispatch. W0 runs first; the
target-surface confirmation, W3, and W7 are gated to O0. The Part A token handoff
(`TOKEN_HANDOFF.md`) is now the pinned dependency for two downstream lanes: TWIN W-LABELS
and the DEMO-PROD LGC-styled beats both block on LGC-W4 landing the `:root` tokens.

## Key correction vs the manifest
The manifest assumes ORCAST is Angular/vanilla-JS and prescribes a React-to-Angular
rewrite. The live console is `web/` (Next.js/React/TS), the same stack as the pax
reference, so the focus model, GlassSurface, and preload port near-verbatim. Two
other lanes (3D-twin sea-level/camera, console ghost-text/bubbles) are editing the
same `web/` surfaces, so collision control through O0 is required.
