# BSW dispatch handoff — O0 rotation charter

Rotate O0 (the operator-facing orchestrator) to a fresh thread that dispatches background
sub-orchestrators for the six dispatch-ready BSW lanes and reconciles their returns, keeping the human
operator on a single surface.

- Repo: `/Users/gilraitses/orcast`, branch `main`, last commit `1b9772e` (`chore(bsw): make breadth + slice-integrate lanes dispatch-ready`), pushed to `origin/main`.
- Lane family: `BSW` (B-side acoustic + behavior research workbench). Home: `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/`.

## A. Purpose
The new thread resumes as O0 for the BSW breadth + integrate campaign. The five breadth lanes
(BST, BAM, BSH, BRE, BSS) and `SLICE-INTEGRATE` are already authored as launchable packets (each: a
`dispatch/<CODE>/wave_shape.yml` with an agent roster + a fenced `ORCHESTRATOR_DISPATCH_PROMPT.md`).
The new O0 dispatches background sub-orchestrators for these lanes, stays unblocked, and reconciles on
completion notifications, approving gated steps per `dispatch/SEQUENCING.md`. O0 does NOT execute lane
work itself.

## B. Decisions that are LOCKED — do not reopen
1. **The slice already shipped and is committed.** A thin-but-real vertical slice (BST rig + POVs, BSH
   STFT HUD, BAM precomputed real inference, BRE presence-gated reenactment) is built, accepted on the
   T4, lives at `/workbench` (`web/app/workbench/`), and is committed (`b983976`). Breadth lanes
   **extend these modules in place** (`delta_from_slice` in each packet); they do not recreate them.
2. **All six lanes are `gated-on-O0`.** Dispatch runs each lane's ungated BUILD work; INTEGRATE
   (convergence, single editor), ACCEPT (GPU capture), data downloads, model training, and any
   commit/push are gates. A sub-orchestrator pauses at its first gate and returns to O0.
3. **One file, one owner; single editor on convergence files.** BUILD scopes are disjoint across lanes
   (see §E), so the five breadth BUILD waves are safe to run concurrently. Only ONE INTEGRATE wave may
   hold the `SalishScene.tsx` queue at a time, serialized vs LGC/CVP/WFX/ORCA/3D-TWIN. Console-turn
   files (`AdaptiveExplore.tsx`/`ActiveSurfaceHost.tsx`/`uiIntent.ts`/`globals.css`) are a second queue
   shared with LGC/CVP. See `dispatch/SEQUENCING.md`.
4. **Honesty locks (binding, from "no standins").** measured (audio/DTAG) vs modeled (mesh/motion) vs
   interpretive (ocean layer). HUD wording is estimate+confidence, never a count/ID the eval can't
   support; the double-diffusion layer is on-screen-labeled interpretive, never "measured perception";
   orca motion is real SRKW DTAG only (humpback is contrast/reference, never a driver); the mandatory
   representativeness label travels with every spawned orca.
5. **Two ML tracks stay separate.** ACOUSTIC (BAM: sound -> who/what) drives WHICH/HOW-MANY orcas
   spawn; KINEMATIC (BRE/BSS: DTAG -> how it moves) drives motion. Never conflated, never invented.
6. **License/privacy first; heavy assets to the box.** NC authorized by owner (`SIGN_OFF.md` decision 1);
   ND/unclear -> STOP to O0. Corpora, raw audio, weights, large derivatives go to S3 (gitignored); only
   small inference JSON + eval + provenance ship in-repo.
7. **BAM is not greenfield.** The slice already trained a real binary SRKW-presence model (RF F1~0.99,
   but bout-confounded, single station). BAM breadth = the window-level/call-type/single-vs-multiple
   corpora follow-on flagged as `to_strengthen` in `infra/acoustic/eval_report.json`. No overclaim.
8. **BSS route must not clobber the existing `/workbench` route.** The annotation studio is a net-new
   route group `web/app/(workbench)/` or a distinct sub-route, confirmed with O0.
9. **Compute-neutral.** New 3D passes join the existing opaque depth pre-pass; spectrogram is a 2D
   canvas/texture; ocean layer is additive/no-depth/optional. Cost vs 60fps-desktop / 30fps-laptop. A
   new runtime dependency is an O0-costed recommendation with a fallback, never a default.
10. **Verification is real.** ACCEPT runs on `aimez-gpu-capture` (Tesla T4) via
    `infra/render_host/render.sh`; frame-time A/B stays serial on the isolated host.

## C. Registry snapshot
| Lane | Packet | What shipped (slice) | This lane adds | Status |
|---|---|---|---|---|
| SLICE-INTEGRATE | `dispatch/SLICE-INTEGRATE/` | slice at `/workbench` | mount onto `SalishScene.tsx` homepage | gated-on-O0 |
| BST | `dispatch/BST/` | single-station rig + POVs | multi-station player + reusable POV object | gated-on-O0 |
| BAM | `dispatch/BAM/` | binary presence model | window-level/call-type/multi-caller corpora follow-on | gated-on-O0 |
| BSH | `dispatch/BSH/` | STFT HUD + ocean stub | real-stratification interpretive volumetric + HUD polish | gated-on-O0 |
| BRE | `dispatch/BRE/` | presence-only single-orca | multi-orca (nMax 3) + DTAG-segment ethogram | gated-on-O0 (dep BAM+BSH) |
| BSS | `dispatch/BSS/` | nothing (net-new) | annotation studio + tagtools + managed HUD skills | gated-on-O0 |

## D. PRIMER — open items (operator's verbatim framing)
> "this would be a good time to rotate the O0 orchestration to a new thread, and have it dispatch
> background suborchestrators for the remaining 6 lanes"

So: the new O0's first action is to dispatch background sub-orchestrators for the six lanes (hydrating
each from its packet's `ORCHESTRATOR_DISPATCH_PROMPT.md`), then stay available and reconcile.

## E. Dispatch table
| Lane | Sub-orch hydrates from | BUILD scope (disjoint) | Run now | First gate it pauses at |
|---|---|---|---|---|
| BST | `dispatch/BST/ORCHESTRATOR_DISPATCH_PROMPT.md` | `web/lib/scene/hydrophone/**`, `web/public/hydrophone/**`, `web/app/(sandbox)/station/**` | BST-BUILD (net-new) | external mesh download (if any), then INTEGRATE |
| BAM | `dispatch/BAM/ORCHESTRATOR_DISPATCH_PROMPT.md` | `infra/acoustic/**`, `modeling/acoustic/**` | pipeline scaffolding | BAM-DATA corpora download (web, O0 go) |
| BSH | `dispatch/BSH/ORCHESTRATOR_DISPATCH_PROMPT.md` | `web/lib/scene/hud/spectro/**`, `web/lib/scene/ocean/**`, `web/public/ocean/**` | BSH-BUILD (net-new) | stratification-data download, then INTEGRATE (WFX) |
| BRE | `dispatch/BRE/ORCHESTRATOR_DISPATCH_PROMPT.md` | `web/lib/scene/reenactment/**`, `web/lib/scene/orca/motion/clips/**` | BRE-BUILD vs current contracts | INTEGRATE (ORCA); needs BAM+BSH for richer fields |
| BSS | `dispatch/BSS/ORCHESTRATOR_DISPATCH_PROMPT.md` | `web/app/(workbench)/**`, `infra/tagtools/**`, `src/aws_backend/casting/**`, `docs/devpost/casting/**` | BSS-BUILD (net-new) | route-path confirm + R/tagtools dep choice |
| SLICE-INTEGRATE | `dispatch/SLICE-INTEGRATE/ORCHESTRATOR_DISPATCH_PROMPT.md` | none (integrate-only) | prepare the single-editor mount | INTEGRATE onto `SalishScene.tsx` (O0 go) |

Exit bar (per lane): BUILD = `tsc`/lint clean, sandbox-verified, WIRING written, no convergence edit,
no commit; pause + return to O0 with the lane's return contract.

## F. Open gate / authority state
- **O0 may self-approve** (reasonable, reversible, in-scope): BUILD-wave decisions, sandbox structure,
  parametric-vs-licensed-mesh choices when license-clear, naming, frame-budget trade-offs that hold.
- **O0 must bring to the HUMAN operator** before approving: any external download whose license/privacy
  isn't already cleared, model training / GPU compute spend, adopting a new runtime dependency (R
  runtime, torch, etc.), integrating onto the live `SalishScene.tsx` homepage (`SLICE-INTEGRATE` and
  every breadth INTEGRATE), and any commit/push. NC is already authorized (`SIGN_OFF.md`); DCLDE-2027
  is CC-BY-4.0.
- **Sequencing:** BAM + BSH BUILD can run in parallel; BRE-BUILD prefers BAM+BSH landed (else builds
  against current contracts and flags the gap); INTEGRATE order on `SalishScene.tsx` is
  SLICE-INTEGRATE -> BST -> BSH -> BRE, one at a time; BSS-INTEGRATE is the console queue (serialize vs
  BST on `AdaptiveExplore.tsx`/`globals.css`).

## G. Pending uncommitted local state
None. The handoff packet itself (this folder, `.cca/catalogue/O0/20260629_bsw-dispatch-handoff/`) is
uncommitted until the operator asks to commit it; the BSW packets + slice are already committed/pushed
(`b983976`, `1b9772e`). Same-machine rotation: the new thread reads these files directly. Cross-actor:
commit this folder first.

## H. Return contract (the ack the new thread must produce)
Before acting, the new O0 posts a short ack:
1. "Rotated as O0 for the BSW dispatch campaign at `main` `1b9772e`."
2. The six lanes + their `gated-on-O0` status (one line each), and the planned dispatch order/parallelism per §E and `SEQUENCING.md`.
3. The gate-authority split it will honor (§F): which gates it self-approves vs escalates to the human.
4. Confirmation it will dispatch background sub-orchestrators (not execute lane work itself) and will not commit/push without an explicit operator ask.
Then it dispatches.

## I. Transcript / provenance pointer
Session transcript:
`/Users/gilraitses/.cursor/projects/Users-gilraitses-orcast/agent-transcripts/f99daa85-44d1-4b94-ae59-f5d7f89f93f2/f99daa85-44d1-4b94-ae59-f5d7f89f93f2.jsonl`
Search by keyword (lane code, filename, "delta_from_slice", "SEQUENCING"); do NOT read it linearly.
