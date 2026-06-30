# GP-SCHEMA, the registry schema fork resolved

Wave 0 finding. Lane home `.cca/catalogue/O0/20260630_grounding-post/`. Actor O0.
repo_state_verified_against: orcast `e794dbd`. Dates America/New_York.

## The fork

orcast carries two registry surfaces that both claim to index the wavesets.

1. `docs/devpost/waves.registry.yaml`, the machine registry. Header dated
   `Updated: 2026-06-23`. Despite that header the body is current to
   `2026-06-30`, carrying every recent lane including BSW, BSWR, DPR, the
   CLOSEOUT set, render-host, and the GP grounding-post lane itself. Each wave
   row holds a stable id, family, type, status, optional gate, optional
   `scope_globs`, optional `home`, optional `output`, optional `depends_on`, and
   a free-text note. The file also holds the `gates:` map, the `demo_surfaces`
   block, `next_wave_set`, and the `quarantine` rule.

2. `docs/devpost/WAVES_REGISTRY.md`, the prose index. Its status matrix is
   labelled `baseline 2026-06-23`. It carries the wave-type taxonomy, the
   family-prefix legend, the authoritative demo-surface table, a mermaid
   dependency graph, and per-family narrative tables for the early families
   P, R, AT, I, D, U, H, E, F, G, M, IC, S, A, W, plus DEMO, CAND, BSIDE, MLM,
   MLO, WILDLIFE, SD, P2X, and PP.

The two disagree on coverage. The YAML lists roughly 45 families through
2026-06-30. The prose stops at the 2026-06-23 baseline plus a few hand-added
sections, and never gained the console-journey wavesets, the 3D twin, WATER-FX,
ORCA, CXR, CVP, LGC, the CLOSEOUT set, render-host, V, VX, MP, FA, SC, Q, the
R0 through R5 research channel, DEMO-PROD, DPR, or GP. The prose lags the YAML
by about 37 wave families.

A second contradiction sits inside the YAML header. The first comment line of
`waves.registry.yaml` reads `Canonical prose: WAVES_REGISTRY.md`, which asserts
the prose is canonical. That header comment is itself stale and is contradicted
by the actual coverage, since the prose cannot describe lanes that did not exist
at its baseline.

## Resolution, the authoritative schema

The machine registry `docs/devpost/waves.registry.yaml` is authoritative for
waveset status, scope, dependencies, gates, and home pointers. It is the only
surface that is both complete to the current commit and maintained on every new
lane. The `waves:` list is the source of record for which wavesets exist and
what state each is in.

`docs/devpost/WAVES_REGISTRY.md` is a secondary human narrative. It is
authoritative only for the wave-type taxonomy and the family-prefix legend, and
for the demo-surface table. For waveset status it is stale and must not be read
as current. The `Canonical prose: WAVES_REGISTRY.md` header comment in the YAML
is recorded here as STALE. The reconciliation declares the YAML canonical for
machine truth.

This matches the working note already carried in `CATALOG.md`, which traces
status against the YAML and the git log, not against the prose.

## How catalogued dirs with no registry family are represented

Some dated homes under `.cca/catalogue/O0/` do not appear as their own family in
`waves.registry.yaml`. They are represented by the dated home plus its
`STEP_LOG.md` and its landing commits, and the index lists them under their
program with status read from the home README and STEP_LOG and verified against
the git log. The set is:

- `explore3d-handoff`, a planning home labelled Wave Set EX with no registry
  family. The web app it framed is traced by commit `8e5c6ee`.
- the console-journey wavesets WS-INTENT, WS-SCENIC, WS-BATHY, WS-TRIPS,
  WS-PERF, WS-STREAM. These are catalogued dated homes, not mirrored as families
  in the YAML, and traced by commit, mainly `5415b8c`, `643eef7`, `fd50929`,
  `874f830`, and `fa9da22`.
- the launch-handoff rotation packets, orcast-handoff, integrate-promote,
  os1-launch, signal-modeling-launch, trips-launch, mlops-handoff,
  console-ws-stream-handoff, bsw-dispatch-handoff, sd-deploy-handoff. These are
  O0 rotation packets, not registry families. Nothing lands in the packet dir.
  The code is credited to the program home the packet points to.

## How registry families with no catalogued dir are represented

Some families in `waves.registry.yaml` have no dated home of their own. They are
represented by their registry rows plus their `scope_globs` or `output` paths,
and the index lists them under the registry with status read from the YAML and
verified by commit or by the existence of the named output file. The set is
R0 through R5, S, W, MP, FA, SC, P, Q, U, H, V, VX, the I and D and G and F and
E feature families, and the CLOSEOUT set TLR, CAP, DGM. They live under `docs/`
or in the registry only.

## Representation rule for the index and the post

- A waveset exists if it appears in `waves.registry.yaml` or has a dated home
  under `.cca/catalogue/O0/`. The union of the two is the authoritative waveset
  list, already enumerated in `CATALOG.md`.
- Status is read from the YAML when the family is registered, and from the home
  README and STEP_LOG when the lane is catalogue-only.
- Every status claim that asserts landed work is verified against the orcast git
  log. Anything that cannot be verified is marked UNVERIFIED.

## Note on the closeout DGM family

`DGM-ARCH` is the one registry row still marked `in_progress`. The AWS4 draw.io
architecture diagram is the open item. The canonical TikZ `architecture.png` is
verified current. This is carried into the post as the single in-flight closeout
item, not as a landed outcome.
