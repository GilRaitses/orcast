# Grounding index

The consolidated grounding surface. orcast and every one of its wavesets, then
the related projects as roadmap entries. repo_state_verified_against: orcast
`e794dbd`. Dates America/New_York.

## orcast

- Grounding post: [orcast_grounding_post.md](./orcast_grounding_post.md), the nine
  perspectives for orcast.
- Catalog: [CATALOG.md](../../../.cca/catalogue/O0/20260630_grounding-post/dispatch/CATALOG/CATALOG.md),
  the waveset-to-code-to-outcome matrix.
- Ledger: [LEDGER.md](./LEDGER.md), the decision ledger, the dated timeline, and
  the dependency and supersession graph.
- Machine registry: [waves.registry.yaml](../waves.registry.yaml), authoritative
  for waveset status, scope, gates, and dependencies.
- Prose registry: [WAVES_REGISTRY.md](../WAVES_REGISTRY.md), authoritative for the
  wave-type taxonomy and the family-prefix legend only, and stale for status.

Live surface: https://orcast-h0.vercel.app

### orcast wavesets

The authoritative waveset universe is the union of the registry families and the
catalogued program directories. The registry lists roughly 45 families. The
working tree holds 39 catalogued program directories. Seven wavesets are
catalogue-only and traced by commit rather than mirrored as families, the six
console-journey wavesets and explore3d-handoff.

Forecasting, modeling, backend:

- forecast-candidates, CAND, done, 200 candidates, 166 tier-A.
- mlops, MLM levels and MLO platform, L0 and L1 done, L2 and L3 frontier, MLO
  chartered.
- wildlife-sources, WILDLIFE, done as research, 34 sources ranked, nothing
  promoted.
- open-science-integration, OS, measured no-go, physics banked.
- backend families R-Alpha through R-Gamma, AT, E, M, IC and J, A1, Q1, shipped.

Frontend, console, twin, water:

- explore3d-handoff, the founding twin handoff, executed downstream.
- 3d-twin, the reusable template.
- console-journey-trips and its wavesets WS-INTENT, WS-SCENIC, WS-BATHY,
  WS-TRIPS, WS-PERF, WS-STREAM, shipped, with WS-PERF run as a benchmark split.
- console-copy-redaction, CXR, shipped.
- console-visual-pass, CVP, shipped.
- liquid-glass-console, LGC, partial, only the glass tokens landed.
- terrain-bathymetry-twin, 3D-TWIN, shipped for the datum and perf waves.
- water-fx, WFX, shipped.
- orca-biologging-twin, ORCA, shipped, a modeled orca with simulated motion.

B-side workbench and infra:

- bside-build, BSIDE, B-API shipped, six breadth waves planned.
- bside-acoustic-behavior-workbench, BSW, slice and breadth shipped.
- bsw-followup-remediation, BSWR, five lanes remediated, STX deferred.
- orcast-selfhost-cutover, SELFHOST, shipped then superseded.
- apprunner-coldstart, WS-COLDSTART, done, measured gap 0.
- hosting-consolidation-followups, WS-HOSTFOLLOWUP, done, self-host
  decommissioned.
- render-host, the Tesla T4 GPU capture host, shipped.
- R-Foxtrot, the registry deploy family, done.

Demo, media, docs, governance:

- demo-waveset, DEMO, story lock shipped, render superseded.
- demo-production, DEMO-PROD, framework shipped, render chartered.
- demo-production-recut, DPR, research on disk, nothing committed.
- V per-beat video and VX voice clone, done.
- A agent demo, done.
- S submission sync, W whitepaper, MP multi-panel, FA figure audit, R0 through
  R5 research sync, SC search cycle, all done, W1 build still flagged in_progress.
- P probes, Q scrutiny, U uploads charter, H hackathon submit, the governance
  families.
- CLOSEOUT TLR and CAP done, DGM-ARCH the one in-progress item, the AWS4 diagram.
- grounding-post, GP, this lane.

Rotation and dispatch packets, no code lands in the packet directory:
orcast-handoff, integrate-promote-launch-handoff, os1-launch-handoff,
signal-modeling-launch-handoff, trips-launch-handoff, mlops-handoff,
console-ws-stream-handoff, bsw-dispatch-handoff, sd-deploy-handoff.

## Related projects, roadmap entries

These projects are referenced from the orcast repo. Their status here is read
from those references only and is not a catalog of their own work. Each is a
roadmap entry for a future grounding post in its own repo.

- pax. The reference product the orcast patterns are generalized from, including
  the NYC 3D viewer that seeded the orcast twin and the liquid-glass console.
  Its cv and shade services co-tenant the shared aimez-services EC2 host with
  orcast in the self-host era. A pax grounding post is the roadmap entry.
- aimez. The shared infrastructure surface at aimez.ai, the aimez-services EC2
  host, the cloudflared tunnel, and the orcast section on the aimez site. An
  aimez grounding post is the roadmap entry.
- IST675. A human-centered machine learning course. Its reading responses were
  mined for verified human-AI interaction sources that anchor the second orcast
  whitepaper. An IST675 grounding post is the roadmap entry.
- PHY600. A physics course. The orcast actor log records a module-4 whitepaper
  committed and pushed at `95791c2`. That commit does not resolve in the orcast
  git log, so it lives in a separate repository and is marked UNVERIFIED from
  here. A PHY600 grounding post is the roadmap entry.

The details of pax, aimez, IST675, and PHY600 beyond these orcast references are
UNVERIFIED from this repo and are deferred to each project's own grounding post.
