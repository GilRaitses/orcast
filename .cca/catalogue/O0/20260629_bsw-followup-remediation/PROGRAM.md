# BSWR — BSW follow-up remediation program

Umbrella authority for the remediation round that closes the follow-ups the
landed BSW breadth + integrate campaign explicitly flagged as STOP-to-O0. The
breadth campaign shipped real features on the Salish Sea homepage at
`61ba1d6`; this round remediates the named gaps, each as its own waveset that
runs a full lifecycle until every gate and critique passes.

- Family: `BSWR`
- Home: `.cca/catalogue/O0/20260629_bsw-followup-remediation/`
- `repo_state_verified_against`: `61ba1d69ee36cf605f7ba741bdaa1defa8762834` (origin/main BEFORE this round)
- Central orchestrator: O0. O0 charters, dispatches, reconciles. O0 does not execute lane work or mutate code.
- Predecessor: `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/` (the BSW campaign; its PROGRAM.md, SIGN_OFF.md, and charters remain the standing authority on honesty locks, licensing, and the convergence queue).

## Intent (operator framing, verbatim)

> charter n wavesets (if needed) for all follow ups to be remediated. followed
> by research, discovery, qualification of methodology, implementation,
> adversarial review, implement, adversarial, until pass all gates and critiques.

## The lifecycle every lane runs (the operator's loop)

Each lane runs the same staged lifecycle. The build and adversarial waves repeat
until the lane has zero open P0/P1 critiques and its acceptance metric is met.

```
R (research + discovery, read-only)
  -> Q (qualify methodology: select + justify the method against criteria; GATE on new dep / download / compute / cost)
    -> B (implement: net-new or scoped extend, disjoint scope)
      -> ADV (adversarial review: hunt regressions, overclaim, gate failures)
         ^---- B and ADV repeat until zero open P0/P1 ----v
    -> INT (integrate: single serialized editor on any convergence file; GATED) [lanes that touch convergence only]
      -> ACCEPT (verify on the real target; honest verdict + captured evidence; GATED)
```

Gates are RUN, not asserted. Acceptance evidence is captured under each lane's
`dispatch/<CODE>/gate_captures/` (metrics JSON + log) or `gate_screenshots/`
(Read-examined frames), and the verdict cites measured numbers, never a claim.

## Lanes (one waveset each)

| Code | Label | Remediates | Convergence touch | Hard gates |
|---|---|---|---|---|
| `ACX` | acoustic-heads-strengthen | ecotype TKW weak (f1 0.43/0.28) + call_type diagnostic-only; the eval `to_strengthen` follow-on | none (serves via `classification.json`) | corpora download, new dep (torch), box compute, schema change, commit |
| `STU` | studio-live-persistence | `HttpAnnotationStore` posts to a backend annotations endpoint that does not exist; proxy allow-list + `ORCAST_API_BASE` | `web/app/api/be/[...path]/route.ts` | backend route design, deploy/env config, commit |
| `OCN` | measured-ocean-stratification | analytic halocline -> measured CC0 CTD; R09 depth-aware plume-clipping via the read-only WFX depth seam | `interpretiveOceanLayer.ts` (and slice mount if needed) | CC0 download (license-clear), WFX seam coordination, GPU accept, commit |
| `ENV` | env-handle-consolidation | the slice's second `makeRealWfxEnv` PMREM bake; ORCA exposes its live `WfxEnvHandle` | `SalishScene.tsx` slice block + the orca controller | convergence edit, ORCA coordination, GPU accept, commit |
| `PRF` | client-tier-frametime-verify | T4 captures are vsync-capped server-class upper bounds, not the binding 30fps client-tier number | none | real-hardware/host acquisition, host run, commit |
| `STX` | station-tileset-extent | wider Puget Sound nodes (Port Townsend, Bush Point) need a tileset-extent change owned by 3D-TWIN | `SalishScene.tsx` + tiles layer (3D-TWIN-owned) | OPTIONAL; 3D-TWIN coordination, extent cost, GPU accept, commit |

`STX` is optional and 3D-TWIN-dependent; its `Q` wave may return a deferral
decision to O0 rather than proceeding to build.

## Locked decisions (do NOT reopen)

These carry forward from the BSW campaign SIGN_OFF and apply to every lane here.

1. No standins, no overclaim. Every served claim is exactly what a documented
   held-out eval or a measured capture supports, and no more. The HUD/label
   wording never exceeds the evidence. The minGRU 0% attempt and the ecotype TKW
   confound are the standing warnings.
2. `single_vs_multiple` stays BLOCKED. The DCLDE-2027 eval found no source-count
   labels (BSW-R02). No lane revives a caller-count claim without real labels;
   if a lane finds them, that is a return-to-O0 decision, not a self-approval.
3. License-first. Verify license + privacy per asset BEFORE any download. NC is
   authorized for conservation/non-commercial use per the BSW SIGN_OFF; ND or
   unclear terms STOP to O0. NC/SA terms travel into every derivative artifact.
   DCLDE-2027 is CC-BY-SA-4.0; CruiseSalish CTD is CC0.
4. Heavy assets to the box. Corpora, raw audio, weights, raw CTD casts go to S3,
   gitignored; only the small served JSON + eval/provenance ship in-repo with a
   re-fetch pointer.
5. Honesty labels are measured-vs-modeled-vs-interpretive and must be exact. The
   interpretive ocean layer is interpretive even after the measured CTD upgrade
   grounds its profile; the label states what is measured (the cast) and what is
   interpretive (the double-diffusion visualization). Recall the module-load
   forbidden-claim guard that crashed on a negated "biosonar perception" phrase;
   wording is gated by `.cca/CLAIM_BOUNDARIES.md` and the prose gate.
6. Convergence discipline. `SalishScene.tsx`, `globals.css`,
   `web/app/api/be/[...path]/route.ts`, and the orca controller are shared. Any
   edit is a single serialized editor in an `INT` wave, `git pull --rebase`
   first, serialized across LGC / CVP / ORCA / WFX / 3D-TWIN and across the
   sibling BSWR lanes. No two lanes edit the same convergence file concurrently.
7. Validation without a parallel dev server. `tsc --noEmit` and lint for web
   lanes; offline reproducible python for the acoustic/CTD lanes; never run
   `next dev`/`next build` during a parallel build wave.
8. Two ML tracks stay separate. ACX is acoustic (sound to who/what). Kinematic
   behavior is the BRE/BSS track. Do not cross them.

## Gate ledger (O0 holds; human-gated items escalate through O0)

| Gate | Lane(s) | Authority |
|---|---|---|
| corpora / audio / CTD download | ACX, OCN | license + privacy verified per asset; NC ok, ND/unclear STOP; O0 logs, escalates if cost/agreement |
| new runtime dependency (torch / embedding) | ACX | O0-costed; human gate |
| box compute / GPU host time | ACX, OCN, ENV, PRF, STX | human gate (cost) |
| served-JSON / API schema change | ACX, STU | O0 (reversible, in-scope) self-approve; escalate if it widens a claim |
| backend route + deploy/env (`ORCAST_API_BASE`) | STU | human gate (deploy) |
| convergence-file edit (INT) | STU, OCN, ENV, STX | O0 approves the single-editor slot; serialize across lanes |
| real verification capture (ACCEPT) | all | O0 approves capture start; human gate if paid/long shared-host |
| commit / push | all | explicit operator request only |

## Escalation (operator-protection catch)

Every dispatched orchestrator answers to O0, not the human operator. On any
locked-decision conflict, regression, overclaim risk, license/privacy ambiguity,
new-dependency or compute need, or any gated step (download, train, integrate,
deploy, capture, commit), PAUSE and return the question to O0 in the summary. Do
not solicit the human operator directly. Do not block on the human.

## Return contract (every lane, every dispatch)

A dispatched lane returns to O0: the findings/methodology decision with its
justification and rejected alternatives; the file list it produced; the measured
gate evidence (metrics JSON / Read-examined frames) with the pass metric stated
before the run; the exact honest wording of any served claim or label; open
questions and which gate it paused at.
