# BSS-BUILD adversarial audit (B4)

Adversarial review of the BSS-BUILD output. Mandate: hunt overclaims, privacy
and license violations, honesty-tier breaks, scripted fakes, and convergence
collisions. Verdict is honest with no reassurance bias.

Audited at HEAD on branch main, after gates 1 and 2 resolved (route `/studio/*`,
dependency posture 2). Net-new files only, no convergence edits, no commit.

## 1. Privacy

| check | finding | status |
|---|---|---|
| Human PII in source | The annotation log carries `whaleID`, `whaleName`, `sampleHz`, sample indices, `state`, `event`. No human names, emails, locations, or device ids. | PASS |
| PII in shipped fixture | `bake.py` drops `whaleName` and keeps only `whaleID` for provenance. The web fixture has no human PII. | PASS |
| Annotator identity | Annotations carry `annotator_id` and `annotator_role`. In the studio these are free-text and default to a non-identifying value. Real community identities are an INTEGRATE concern and must not store PII without consent. | PASS with note |

Note for INTEGRATE: if community annotations bind to real user identities, route
identity through the existing authenticated proxy and store an opaque id, not an
email or name.

## 2. License

| check | finding | status |
|---|---|---|
| Source DTAG license | O0 ruled the humpback DTAG mn09_203a is CC-BY-NC, covered by the SIGN_OFF NC authorization (decision 1). Cleared for ship under non-commercial terms. | CLEARED |
| License label on artifacts | The fixture, the box manifest, the tagtools provenance, the poster-viz descriptors, and the managed-skill outputs all carry `CC-BY-NC-4.0` plus attribution and a source pointer. No UNVERIFIED labels remain. | PASS |
| Attribution | Attribution reads "humpback DTAG mn09_203a, whale-behavior-analysis dataset" with the source `dive_analysis.h5` pointer on every artifact. | PASS |
| Non-commercial scope | NC is honored: the data is contrast and reference only and never drives a commercial output. | PASS |
| Shipping posture | Nothing is committed. The web fixture is an untracked working-tree file. Heavy arrays are gitignored under `infra/tagtools/out/`. | PASS |

License ruling resolved by O0: CC-BY-NC, non-commercial, authorized per SIGN_OFF
decision 1. Commit remains a separate operator gate, so nothing is committed in
this step.

## 3. Honesty tiers

| check | finding | status |
|---|---|---|
| New skill tiers | `run_tagtools_step`, `render_poster_viz`, `capture_behavior` are all T1 and public. No T2 or T3 public exposure. | PASS |
| Catalog activation | The three skills are `enabled: false` in the manifest, so the public catalog count is unchanged. Activation is the O0-gated INTEGRATE. | PASS |
| Truth labels | Labels are honest: `derived` for recomputed tagtools, `baked` for offline poster renders, `measured_behavior_modeled_camera` for capture. | PASS |
| Existing tests | `tests/aws_backend/test_casting_policy.py` passes 8/8. Public-enabled stays 9, catalog stays 15, keyed stays 6. | PASS |

## 4. No scripted fakes

| check | finding | status |
|---|---|---|
| Tagtools steps run on real data | All 5 stages run on the real 99,925-sample sensor CSV. Orientation reproduces the provided pitch and roll to ~3e-10 rad, confirming a correct re-implementation, not a canned output. | PASS |
| Behavior capture pulls a real example | `capture_behavior` selects a real classified dive (for example Kick feeding on dive 15) whose behavior comes from the expert annotation overlap on a real dive window. No invented behavior. | PASS |
| Annotation round-trip | The round-trip harness creates a provenance-tagged annotation on a real classified dive, persists it, and reads it back with provenance intact. | PASS |
| Poster viz | Served as baked descriptors with box pointers. No claim that R runs live. The 3D lattice JS port is explicitly deferred, not faked. | PASS |

## 5. Overclaim hunt

| claim risk | finding | resolution |
|---|---|---|
| Dive detection matches the reference | The recompute finds 215 dives vs the reference 128. | Reported honestly in the step summary and README with the parameters used. Not tuned to match. No claim of equivalence. |
| Stroke and glide match the reference | Recompute finds far more peaks than the reference. | Reported honestly with a method note. No claim of equivalence. |
| Audio annotation | The studio is titled for audio and kinematics, but only kinematics are real here. | The UI states audio is not bound in the sandbox and ships no placeholder audio. Audio binds via the station and spectro lanes at integrate. |
| Units | Accelerometer values are in g, not m/s2 as the schema attribute states. | Step summaries relabeled to g; the calibration check confirms static magnitude near 1.0 g. |
| Console invocation | The skills are registered but not active. | The build proves direct handler runs. Console invocation is the ACCEPT criterion, gated. No claim it runs in the live console yet. |

## 6. Convergence collisions

| check | finding | status |
|---|---|---|
| Route collision | The studio lives under the `(workbench)` route group serving `/studio/*`. The existing `/workbench` slice route is untouched. | PASS |
| Console convergence files | `AdaptiveExplore.tsx`, `ActiveSurfaceHost.tsx`, `uiIntent.ts`, `globals.css` are not edited. | PASS |
| Scope discipline | Edits are confined to `web/app/(workbench)/**`, `web/lib/annotation/**`, `infra/tagtools/**`, `src/aws_backend/casting/**`, `docs/devpost/casting/**`, and this dispatch folder. | PASS |
| skills.py edit | A two-line additive merge of `STUDIO_DISPATCH` into `_DISPATCH`. In scope, no behavior change for existing skills, tests green. | PASS |

## Verdict

BSS-BUILD is clean on privacy, license, honesty tiers, scripted fakes, and
convergence. The build is sandbox-verified and tsc-clean. The license is
resolved: O0 ruled CC-BY-NC, non-commercial, authorized per SIGN_OFF decision 1,
and every artifact carries the CC-BY-NC label with attribution and a source
pointer. The recomputed dive count (215 vs reference 128) and stroke and glide
counts remain divergent by design, reported honestly with parameters and not
tuned to match. Commit stays a separate operator gate, so nothing is committed.
