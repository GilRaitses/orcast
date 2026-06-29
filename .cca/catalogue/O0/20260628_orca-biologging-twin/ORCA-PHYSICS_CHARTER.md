# ORCA-PHYSICS charter (OPHYS) - secondary motion physics

- Lane code: **OPHYS** (family ORCA). Type: research-first, then gated build.
- Depends on: **OR** (rig DOFs), **OG** (the telemetry-driven base pose this layers on top of).
- Owns (net-new): `web/lib/scene/orca/physics/`. No existing-file edits in research.

## Intent
"Motion physics of the orca models." The base pose comes from biologging telemetry (OG); OPHYS
adds the **secondary dynamics** that make a data-driven pose look alive in water - body/spine
follow-through, fluke and flipper flex, water drag/resistance, banking lean, momentum - without
fabricating any movement the data did not show.

## Grounding
- OG drives the primary DOFs from real channels (heading/pitch/roll/depth/fluke-beat). A pose set
  directly from samples looks stiff: real bodies have lag, overshoot, and elastic flex.
- Standard real-time approach: spring/critically-damped or Verlet **secondary dynamics** on the
  spine/caudal/flipper chains, plus spine **IK** so the body follows its heading smoothly, plus a
  simple drag/banking model. This is animation polish layered on the data, not new data.

## Locked decisions (honesty is the hard line)
- **OPHYS never fabricates trajectory.** Position, depth, heading, pitch, roll, and the fluke-beat
  rate come from OG (the telemetry). OPHYS only adds **bounded** secondary motion (flex,
  follow-through, damping, drag-induced lean) layered on that base. When a real stream is loaded,
  the visible track still matches the data within tolerance.
- Dynamics are **stable and clamped** (no jitter, no runaway springs); frame-rate independent.
- Banking/lean is derived from the OG turn rate (consistent with roll), not invented.
- Built on `three` math (springs/IK hand-rolled or a small lib as a costed recommendation). No
  full rigid-body engine.
- Honesty label holds: modeled animal; secondary dynamics are clearly polish on telemetry.

## Waves
- **OPHYS-R (research, read-only):** `web/lib/scene/orca/physics/OPHYS-R_dynamics.md` - the
  secondary-dynamics model (which chains get springs, damping coefficients, IK for spine-follow),
  the drag/banking derivation from OG turn rate, the **tolerance bound** proving the polished
  motion still tracks the data, the stability plan (clamps, frame-rate independence), and perf
  cost. Cite OR DOFs + OG mapping.
- **OPHYS-BUILD (gated on O0):** the dynamics layer in the `/orca` sandbox on top of OG; tsc clean;
  verified the orca moves alive (flex/follow-through/lean) while the data track stays within the
  stated tolerance; stable at varying frame rates.

## Acceptance
- OPHYS-R: a bounded secondary-dynamics + IK + drag model with a data-tracking tolerance and perf
  cost; cites OR/OG.
- OPHYS-BUILD (gated): lively motion that provably still follows the OG telemetry within tolerance,
  stable, within budget. No commit without O0.

## Escalation
Any choice that would let polish override the telemetry, dependency choice, stability/perf
trade-off, or a gated step -> pause, return to O0.
