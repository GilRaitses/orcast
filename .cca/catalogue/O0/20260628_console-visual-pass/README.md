# CVP lane (console-visual-pass)

The full explore-console visual pass as the baseline design layer for `web/` (Next.js + plain CSS).
Started because the home console renders native unstyled OS controls (no `.chip` rule, no base
`button` / `textarea` / `input` / `label`), a cramped raw composer, and a yellow cone hydrophone
beacon that dominates the frame. CVP fixes baseline correctness and adds a component design system;
LGC layers its glass identity on top later.

Lane: O0 (web home console). Status: CHARTERED, pending operator GO. Pin: `main 97b6397`.

## File set

| File | Role |
|------|------|
| `WAVESET_CHARTER.md` | Authority doc: grounding, the three defects, locked decisions, waves W1-W4, gates, escalation |
| `wave_shape.yml` | Machine-readable shape mirroring the charter (waves, agents, gates, locked decisions) |
| `ORCHESTRATOR_DISPATCH_PROMPT.md` | The paste block for the background sub-orchestrator |
| `DECISION_RECORD.md` | Decisions to confirm before launch (separate lane, full console pass, collision serialize) |
| `W1_DISPATCH.md` | Wave 1 shared context + 5 read-only discovery agent prompts + the W1 exit gate |
| `CVP_PREFLIGHT.md` | The PF-1..PF-6 verdict table skeleton + how to run the harness |
| `STEP_LOG.md` | Orchestrator synthesis trace (newest last) |
| `findings/` | The 5 discovery findings docs + `SYNTHESIS_cvp.md` (created by the wave) |
| `gate_captures/` | Preflight JSON (`cvp_preflight.json`) and gate evidence |

## How to start

Dispatch the sub-orchestrator with `ORCHESTRATOR_DISPATCH_PROMPT.md`. It runs the 5-agent read-only
W1 discovery wave, writes the synthesis, and returns to O0. W2 build, W3 integrate, and W4 accept are
O0-gated. The preflight (`tools/waves/gates/cvp-preflight.sh`) runs at W3 entry and writes
`gate_captures/cvp_preflight.json`.

The three hot convergence files (`globals.css`, `AdaptiveExplore.tsx`, `SalishScene.tsx`) are shared
with LGC / CXR / 3D-TWIN / WFX / ORCA. W3 is a single serialized editor gated on O0 confirming the
serialize order. No commit / push / deploy without explicit operator request.
