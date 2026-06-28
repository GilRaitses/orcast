# Console program: waveset structure, lifecycle, and execution topology

This charter expands the Console Journey + Trips program into a multi-waveset program where every
waveset runs a fixed six-wave lifecycle, adds the visual roles the operator called for (terrain
stylist and scenic decorator under the Director, plus bathymetry special teams), and fixes the
execution topology. It supersedes the flat W1/W2/W3 plan for all REMAINING work. W1 (foundation
primitives) and the W2 backend clients (WSF, WSDOT) are already DONE and feed the wavesets below.

## 1. The six-wave lifecycle (every waveset runs this in order)

Each waveset is not a single build pass. It is six waves with entry and exit gates. A wave does not
start until the prior wave's exit gate passes.

1. Research. Gather external knowledge: techniques, prior art, data sources, provider docs, reference
   imagery. Read-only, doc-producing. Output: a research synthesis with cited options and a
   recommendation. Gate: the synthesis names concrete techniques/sources the implementation can use.
2. Discovery. Ground the research in THIS codebase: what already exists and is reusable, the exact
   files and seams, the one-file-one-owner map, the convergence file, constraints, and honesty labels.
   Read-only, doc-producing. Gate: a discovery map that lists every file to be created or edited, its
   owner, and the integration seam, with no unowned convergence-file edits.
3. Implementation. Build it. Parallel one-file-one-owner producers in phase A, then a single
   convergence editor in phase B. Validate with type-check / fixture tests, no dev server during the
   parallel phase. Gate: every module type-checks/tests green and the convergence wiring lands.
4. Adversarial. Red-team the implementation. A reviewer that did not build it hunts visual,
   behavioral, honesty, performance, and edge-case defects and audits every claim. Produces a defect
   register with severities. Read-mostly. Gate: the register is complete and triaged.
5. Remediation. Fix the defects the adversarial wave filed, by owner, highest severity first. Touches
   implementation files, so it is serialized on convergence files. Gate: every blocking and major
   defect is closed or explicitly deferred with operator sign-off.
6. Acceptance. Verify against the waveset's acceptance criteria, including real visual verification
   (read the rendered output, never claim a fix unseen). The orchestrator, not the builder, signs off.
   Gate: acceptance criteria met and recorded in the waveset STEP_LOG.

## 2. The wavesets (four remaining)

Convergence files have a single editor in their implementation phase B and are serialized ACROSS
wavesets by the program orchestrator (section 4). Honesty labels travel with every served surface.

### WS-INTENT, the console intent loop (the spine, locked decision B.2)
Make the dead `map_viewport` ui_intent and the search affordance drive the live camera. Components:
intent transducer (`web/lib/intent/transducer.ts` + additive `adaptiveConsole.ts` turn builder),
fly-through controller (`web/lib/journey/controller.ts`), Viewport Bridge (convergence
`web/app/components/scene/SalishScene.tsx`, phase B), search-affordance wiring. Depends on: W1 (done).
Acceptance: searching a gazetteer place flies the live console camera through the beat; a planner turn
returning `map_viewport` moves the camera.

### WS-SCENIC, scene realism and decoration (Director + new roles, above the water)
Make the world look right above sea level. The island looks barren and the horizon has no surrounding
geometry. Teams report to the Director.
- Terrain Stylist. Land materials, landcover and vegetation treatment, terrain texturing and shading
  so islands read as living land, not bare tan relief. Owns a new landcover/material module; reads
  realism public surface, does not own it.
- Scenic Decorator. Horizon surrounding geometry (distant land and mountain silhouettes BEYOND the
  served CUDEM extent so the horizon is not empty water), atmospheric depth, and sky/fog/haze
  refinement as set dressing. Owns a new horizon/atmosphere-decor module.
Convergence: the scene visual mount (`SalishScene.tsx` rig section, phase B, serialized with INTENT
and BATHY). Acceptance: the live scene and the journey beats show vegetated, materially-correct land
and a framed horizon with surrounding geometry and coherent sky/haze; honesty note holds (real CUDEM,
fog labeled atmosphere, any added distant geometry labeled decorative not surveyed).

### WS-BATHY, bathymetry layout (special teams, below the water)
Make the seafloor and the water-over-terrain read correctly.
- Bathy Data Engineer. Source and curate seafloor bathymetric data for the Salish extent; label
  measured vs modeled provenance.
- Bathy Terrain Builder. Represent the underwater terrain (the field/mesh the depth-driven water
  reads), reconciled with the CUDEM substrate.
- Water and Depth Stylist. Tune the depth-driven water (`web/lib/scene/water2/`) and substrate
  (`web/lib/scene/substrate/`) so shoals, channels, and depth read truthfully.
- Honesty Labeler. Ensure measured vs modeled bathymetry is labeled on every surface; no invented
  depths presented as measured.
Convergence: water2/substrate integration into the scene (serialized with SCENIC and INTENT).
Acceptance: the water-over-terrain reads truthfully across depths with provenance labels; no fabricated
bathymetry presented as measured.

### WS-TRIPS, the trips journey and connections (locked decisions B.3/B.4)
The real multi-step planner on the live console. Components: trips planner branch (convergence
`src/aws_backend/casting/planner.py`, phase B) + panel registration in `ActiveSurfaceHost.tsx`,
connections planner (`casting/trips/connections.py`), corridor traffic model (`modeling/traffic/
corridor.py`, fit on the now-collecting history), kayak panel, sidequests + auth chip. Depends on:
WS-INTENT (needs the live surface) and the W2 clients (done) + corridor history (accruing). Acceptance:
each branch returns a coherent panel set from a real turn; the connections planner answers a concrete
sailing/flight question with a labeled confidence; no ML promoted.

## 3. Execution topology (decided)

One program orchestrator (this O0 thread) running the wavesets in the background through one
suborchestrator per waveset. NOT separate human-operated threads.

Why one orchestrator with background suborchestrators, not separate threads:
- The wavesets share the scene and its convergence files (`SalishScene.tsx`, the realism and water2
  rigs, `ActiveSurfaceHost.tsx`). A single orchestrator must arbitrate convergence-file ownership and
  serialize edits. Separate threads cannot see each other's file locks, so they would collide.
- Research and Discovery waves are read-only and doc-producing, so they parallelize safely across all
  four wavesets at once. The suborchestrators run these cheaply in parallel.
- Implementation and Remediation waves are serialized on shared files by the program orchestrator via
  the convergence calendar below.

Each waveset suborchestrator (a background subagent) owns its six-wave lifecycle, dispatches its
producer subagents, and reports a wave summary up. The program orchestrator gates each wave, keeps the
single DECISION_RECORD and STEP_LOG, and commits nothing without operator ask.

## 4. Collision governance (convergence calendar)

- `SalishScene.tsx` is touched by WS-INTENT (Viewport Bridge), WS-SCENIC (rig mount), WS-BATHY
  (water/bathy mount). Only ONE waveset edits it at a time, in this order: INTENT -> SCENIC -> BATHY,
  each as a single phase-B editor. The others stage their scene changes as pure modules the next
  editor mounts.
- `web/app/components/AdaptiveExplore.tsx` (the shell `focus` pipeline): WS-INTENT only, phase B,
  additive (read `mapViewportFromIntent(resp)` into `focus` to close the planner-initiated camera
  loop). Granted by the program orchestrator 2026-06-27 after WS-INTENT discovery flagged it as
  unnamed. No other waveset edits it.
- `planner.py` and `ActiveSurfaceHost.tsx` panel registry: WS-TRIPS only.
- `realism/` and `water2/` and `substrate/` internals stay owned by their existing modules; SCENIC and
  BATHY add NEW sibling modules and read the existing public surface, they do not edit internals.
- Producers commit/deploy/promote nothing; operator commits. Secrets stay in `.env`. Never `git add -A`.

## 5. Dependency and schedule graph

- Now: WS-SCENIC, WS-BATHY, WS-INTENT, WS-TRIPS can all run Research + Discovery in parallel
  (read-only).
- Implementation order driven by the convergence calendar and dependencies:
  - WS-INTENT implementation first (it owns the SalishScene bridge and is the spine).
  - WS-SCENIC and WS-BATHY implementation next, serialized on the SalishScene mount (SCENIC then
    BATHY), but their pure modules build in parallel before the mount.
  - WS-TRIPS implementation after WS-INTENT (needs the live surface); its backend (connections,
    corridor model) builds in parallel earlier.
- Adversarial -> Remediation -> Acceptance run per waveset after its implementation.
- Capture (demo beats) stays the existing demo-waveset handoff, after the visual and trips wavesets.

## 6. New roles summary

- Director (exists). Owns journey cinematography and the visual deficiency register; SCENIC and BATHY
  visual leads report visual coherence to the Director.
- Terrain Stylist (new, WS-SCENIC). Land materials, landcover, vegetation, terrain shading.
- Scenic Decorator (new, WS-SCENIC). Horizon surrounding geometry, atmospheric depth, sky/fog/haze.
- Bathy special teams (new, WS-BATHY). Data engineer, terrain builder, water/depth stylist, honesty
  labeler.

## 7. Operator decisions to confirm before fan-out

1. Four wavesets (INTENT, SCENIC, BATHY, TRIPS) at this granularity, or split/merge.
2. Topology: one orchestrator + background suborchestrators (recommended) vs separate threads.
3. Start all four Research + Discovery waves now in parallel (read-only), holding implementation for
   the gate.
