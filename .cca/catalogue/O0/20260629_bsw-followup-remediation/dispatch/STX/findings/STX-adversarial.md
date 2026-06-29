# STX-R4 adversarial, framing regression, load blowup, the deferral case

Lane STX. Wave STX-R, member R4. Read-only. Reports to O0 via the STX
sub-orchestrator. repo_state_verified_against:
`61ba1d69ee36cf605f7ba741bdaa1defa8762834`.
Role: argue against the widen, hunt the regressions a proceed would cause, and
state the deferral case. Grounded in R1, R2, R3 and the source files they cite.

## 1. Framing regression (the strongest argument against)

The fit scales the whole baked bounding-sphere DIAMETER to `SCENE_WIDTH = 120`
(`useTilesLayer.ts:191-211`), and every camera distance is derived from the
resulting `fitRadius` (R2 section 2). The geo half-diagonal sets the scale:

- Current half-diagonal `geoRadiusMeters(TILESET_BOUNDS)` is about 24,815 m.
- Union bbox half-diagonal is `0.5 * hypot(77.7 km, 51.5 km)` about 46,600 m,
  about 1.88x larger.

So a union widen makes `worldUnitsPerMeter` about 1.88x smaller and the San Juan
core, which is where ALL current content lives (the three stations, the orca rig,
the slice rig, the bathy tint, the reenactment), renders about half its current
on-screen size at the same camera pose. This directly reverses the W-PERFUX RP2
tightening that just fixed the operator's verbatim "do not show the view so far
back" complaint (`W-PERFUX_RESEARCH_DISPATCH.md`, `RP2_view_scope.md`). Two ways
to react, both bad:

- Keep the RP2 orbit factor `fitRadius*0.4`: it now frames a fraction of a 1.88x
  bigger sphere, so the core shrinks and the frame again shows "so far back".
- Re-tighten the orbit to the core: then the two new Admiralty nodes sit about 45
  to 55 km south-east, off-frame at rest. The user only ever sees them by
  triggering a journey 45+ km away, where the surrounding terrain is the
  low-value water-and-land gap. The nodes you widened for are not in the picture
  the widen produced.

This is the core adversarial point: the value of the homepage twin IS the tight
San Juan core framing, and widening the extent is in tension with it by
construction. You cannot both keep the core tight and show Admiralty nodes in the
same resting frame.

## 2. Load-cost blowup (R3, restated as a regression)

A union tileset is about a 3.3x load regression: first paint about 19 to about
60 MiB, engaged about 76 to about 248 MiB (R3 section 3a). The W-PERFUX startup
caps scale up with it rather than rescuing it. The `Water2Rig` per-frame depth
pre-pass and meshopt decode both scale with the streamed leaf set (R3 section 4),
so frame-time during the stream degrades too. There is no approved load or
frame-time budget, and the binding client-tier frame-time number is unmeasured
(it is the sibling PRF lane's deliverable). STX cannot certify "within budget"
against a budget that does not exist for a number nobody has measured. Under the
charter locked decision 3 (no load-cost regression beyond an O0-approved budget),
that alone blocks a proceed today.

## 3. Honesty and data-value regression

The two nodes have real catalog positions (R1), so rendering them is not
dishonest about location. But the marginal VALUE is thin:

- Their served acoustic backing does not exist yet. The PT/BP region expansion
  is operator-gated (TB1 decision D1, not approved) and the acoustic ingest is
  not run, so beyond station metadata there is nothing to show at those nodes.
  Only Orcasound Lab has a license-clear archived clip in-repo anyway; PT and BP
  would be live-listen-only beacons, exactly like North San Juan Channel and
  Andrews Bay already are.
- TB1 measured that PT and BP add 25 net-new region presence-days but 0 in
  summer, the binding regime. So the data story is off-season coverage, not a
  headline feature. Spending a 3.3x load regression and a host re-bake to place
  two off-season, live-listen-only beacons 45+ km off-frame is a poor trade.

## 4. Hidden integration cost the optimistic case ignores

- The substrate field is bounded to the same `48.40..48.70 / -123.25..-122.75`
  and must be re-baked too, or the new nodes have no seabed to seat on and the
  beacon raycast misses, floating the marker at `Y = 0` on the water plane (R1
  section 4, R2 section 5).
- The CUDEM `wash_bellingham` source may not extend to Admiralty Inlet (lat 48.0
  to 48.2), so the re-fetch may need an additional CUDEM collection, more host
  work, not a free clip (R2 section 5).
- The edit lands on `SalishScene.tsx` / `useTilesLayer.ts`, the shared
  convergence files, so it serializes behind a single-editor INT slot against
  3D-TWIN, WFX, ORCA, OCN, ENV and the sibling BSWR lanes (`PROGRAM.md` locked
  decision 6). The host re-bake and the GPU ACCEPT capture are both human-gated
  compute (`PROGRAM.md` gate ledger).

## 5. The deferral case (recommended)

Defer. The lane is explicitly OPTIONAL and deferrable, and the cost is stated.

1. Cost: a single union widen is about a 3.3x load regression (about +41 MiB
   first paint, about +172 MiB engaged) plus a host re-bake and a substrate
   re-bake, possibly an extra CUDEM source.
2. Framing: it reverses the just-landed RP2 tightening; the core halves on screen
   or the new nodes are off-frame. There is no framing in which the widen both
   keeps the core tight and shows the nodes at rest.
3. Budget: no approved load or frame-time budget exists, and the binding
   client-tier frame-time number is unmeasured (PRF lane). The charter forbids a
   regression beyond an approved budget, so a proceed is blocked on a number that
   is not yet available.
4. Value: the two nodes are off-season, live-listen-only, and their region
   expansion is itself gated and uningested. The marginal feature value is two
   off-frame beacons.

Deferral preserves every honesty and quality lock and changes nothing on the
shared convergence files, which is the safest outcome for a lane the program
already flags as 3D-TWIN-dependent and optional.

## 6. The narrow case FOR a future proceed (so the deferral is honest)

For completeness, the conditions under which a widen would be worth revisiting,
all of which must hold:

- PT/BP region expansion (TB1 D1) is approved AND the acoustic ingest is landed,
  so the nodes carry real served data, not just positions.
- A real client-tier frame-time budget exists (PRF lane) and O0 approves a load
  budget that a re-bake can meet.
- The product decision is to offer an Admiralty Inlet VIEW (its own framing),
  not to widen the single core frame. That argues for the two-box separate
  tileset with its own projection frame (R2 seam B), explicitly scoped as a new
  view, sequenced behind 3D-TWIN, not as a quiet extent edit.

Absent all three, defer.

## 7. R4 conclusion

Recommend defer, cost stated. The widen reverses the operator-driven framing fix,
triples the load with no approved budget and no measured frame-time number,
re-bakes terrain and substrate to place two off-season live-listen-only beacons
that end up off-frame, and its data backing is itself gated and uningested. None
of the three conditions for a worthwhile proceed currently holds.
