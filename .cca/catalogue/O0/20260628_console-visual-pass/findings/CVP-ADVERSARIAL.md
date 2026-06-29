# CVP-ADVERSARIAL — defect re-verify, collision map, boundary hunt

Owner: W1 Agent A5 (adversarial + collision + defect re-verify). Read-only discovery.
This is the only file this agent wrote. No `web/`, `src/`, registry, or gate file was edited.

Repo state at verification:

```
$ git rev-parse HEAD
a914ad1bdb482cc5a13ba514eba808ba7082b3a6
$ git log --oneline -3
a914ad1 feat(orca): ORCA Wave-0 build gate - mesh, motion pipeline, real orca data
97b6397 chore: working-tree cleanup + submission/infra/tooling tracking
ca5fd6a docs(orchestration): charters, dispatches, and research findings
```

Dispatch pin string is `main 97b6397`. Actual HEAD is `a914ad1`, exactly one commit ahead of the pin.
All three defect re-verifications below ran against the ACTUAL current tree at `a914ad1`.

---

## 0. PIN-vs-HEAD MISMATCH FLAG (read first)

The dispatch pin `97b6397` is STALE. The tree advanced one commit to `a914ad1`
("ORCA Wave-0 build gate"). The defects all persist, so the plan is not broken, but every
artifact that hardcodes the pin is now wrong about HEAD and must be reconciled before W3.

Where the stale `97b6397` string lives:

| Artifact | Line | Field |
| --- | --- | --- |
| `docs/devpost/waves.registry.yaml` | 1602 | CVP-W1 `repo_state_verified_against: 97b6397` |
| `.cca/.../W1_DISPATCH.md` | 12 | "defects at the pin `main 97b6397`" |
| `.cca/.../gate_captures/cvp_preflight.json` | 4-5 | `repo_state_verified_against` and `head` both `97b6397` |
| `tools/waves/gates/cvp-preflight.sh` | 21 | hardcoded `PIN="97b6397"` |

Did the new commit touch the hot files? No. `a914ad1` vs `97b6397` shows an EMPTY diff on all three:

```
$ git diff --stat 97b6397 a914ad1 -- web/app/globals.css web/app/components/AdaptiveExplore.tsx web/app/components/scene/SalishScene.tsx
(no output)
```

`a914ad1` added orca mesh/biologging assets, edited `waves.registry.yaml` (+76 lines), and
ADDED `tools/waves/gates/cvp-preflight.sh` itself (+172 lines). It did not edit any hot file, so
the three defects below are unchanged by the advance.

ESCALATION E1. `gate_captures/cvp_preflight.json` records `head: 97b6397`, yet the gate script
that produced it (`cvp-preflight.sh`) only exists as of `a914ad1`. The capture predates its own
gate landing on HEAD, so it is a stale dry-run. O0 must regenerate the preflight at W3 entry
against `a914ad1` (the script reads `git rev-parse --short HEAD` at run time, so a fresh run
self-corrects the head field). Treating the existing JSON as current would build against a stale capture.

The hot files are clean in the working tree right now (no concurrent hold):

```
$ git status --porcelain -- web/app/globals.css web/app/components/AdaptiveExplore.tsx web/app/components/scene/SalishScene.tsx
(no output)
```

---

## 1. DEFECT RE-VERIFICATION (literal command + literal output + verdict)

### D1 — no `.chip` rule and no base element rules in globals.css

```
$ rg -n "\.chip\s*\{" web/app/globals.css
(no output, exit 1 / zero hits)
```

```
$ rg -n "^\s*(button|textarea|input|label)\s*\{" web/app/globals.css
(no output, exit 1 / zero hits)
```

Confirm `.chip` is USED:

```
$ rg -n 'className="chip"' web/app/components/AdaptiveExplore.tsx
313:                    className="chip"
330:                <button key={p} type="button" className="chip" onClick={() => setMessage(p)}>
```

Confirm no `.chip` rule exists in ANY css file:

```
$ rg -ln '\.chip' web/ --glob '*.css'
(no output, exit 1 / zero hits)
```

VERDICT D1: PRESENT at HEAD `a914ad1`. `web/app/globals.css` defines no `.chip` selector and no
base `button` / `textarea` / `input` / `label` rule, while `.chip` is applied at
`web/app/components/AdaptiveExplore.tsx:313` and `:330`.

ADVERSARIAL WIDENING (bad assumption in the dispatch). The dispatch and charter say only "Chip is
used at `AdaptiveExplore.tsx:330`". The blast radius is much wider. `.chip` is applied at 15 sites
across 7 components with no rule anywhere:

```
$ rg -n 'className="chip"' web/
web/app/components/ActiveSurfaceHost.tsx:407
web/app/components/ActiveSurfaceHost.tsx:411
web/app/components/AdaptiveExplore.tsx:313
web/app/components/AdaptiveExplore.tsx:330
web/app/components/ui/GatedAction.tsx:46
web/app/components/ui/GatedAction.tsx:49
web/app/components/MapHero.tsx:93
web/app/components/SightingCheckPanel.tsx:348
web/app/components/ProvenanceGraph.tsx:198
web/app/components/InterestForm.tsx:52
web/app/components/InterestForm.tsx:57
web/app/components/InterestForm.tsx:62
web/app/components/ExploreGuidePanel.tsx:287
web/app/components/ExploreGuidePanel.tsx:318
web/app/components/ExploreGuidePanel.tsx:401
```

Consequence for O0. The CVP baseline `.chip` rule is GLOBAL, so it restyles the explore page,
gated-action prompts, the map hero, the sighting-check panel, the provenance graph, and the
interest form in addition to the anonymous home. The charter frames CVP as the "anonymous home
console" pass. Adding a global `.chip` is fine and intended, but the visual-review surface at W4 is
wider than the home alone. Recommend O0 widen the W4 Read-examine set beyond `/` so a baseline
`.chip` change does not silently regress reviewer/explore surfaces.

### D2 — raw composer at AdaptiveExplore.tsx, no `.ask-textarea`, cramped

`web/app/components/AdaptiveExplore.tsx:335-343`:

```335:343:web/app/components/AdaptiveExplore.tsx
            <label>
              Ask about the Salish Sea
              <textarea
                rows={2}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask about a place, a hydrophone, or planning a visit…"
              />
            </label>
```

The composer is a bare `<label>` wrapping a bare `<textarea rows={2}>` with no class, so it falls
through to browser defaults with no width control. It does NOT use `.ask-label` or `.ask-textarea`.

Confirm the `.ask-*` family exists in globals.css but is not used by this composer:

```
$ rg -n "ask-textarea|\.ask-" web/app/globals.css
296:.ask-layout {
303:  .ask-layout { grid-template-columns: 1fr; }
305:.ask-map-card ...
307:.ask-chat-card ...
308:.ask-label { display: flex; flex-direction: column; gap: 0.35rem; font-size: 0.9rem; font-weight: 600; }
309:.ask-textarea, .ask-input { ... }
406:.ask-reply ...
```

The `.ask-*` classes are consumed by `SightingCheckPanel.tsx` and `ExploreGuidePanel.tsx`, and
`AdaptiveExplore.tsx` itself uses `.ask-user` / `.ask-assistant` for the transcript bubbles, but the
HOME composer at `335-343` uses none of them. The assumption "`.ask-*` present but unused on the
home composer" holds for the composer specifically.

VERDICT D2: PRESENT at HEAD `a914ad1`. Raw uncramped composer confirmed at
`AdaptiveExplore.tsx:335-343`, no `.ask-textarea`.

### D3 — cone beacon coneGeometry in #ffcf33

```
$ rg -n "coneGeometry" web/app/components/scene/SalishScene.tsx
355:        <coneGeometry args={[1.6, 5, 6]} />
```

The beacon mesh block and its color origin, `web/app/components/scene/SalishScene.tsx:339` and
`:354-357`:

```339:357:web/app/components/scene/SalishScene.tsx
  const color = online ? "#ffcf33" : "#888";
  ...
      <mesh
        ...
        scale={hovered ? 1.4 : 1}
      >
        <coneGeometry args={[1.6, 5, 6]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={hovered ? 0.9 : 0.4} />
      </mesh>
```

The `#ffcf33` originates at `SalishScene.tsx:339` as `const color = online ? "#ffcf33" : "#888";`
and feeds both the cone `meshStandardMaterial color` and `emissive` at `:356`.

VERDICT D3: PRESENT at HEAD `a914ad1`. Cone beacon `coneGeometry args={[1.6, 5, 6]}` in `#ffcf33`
confirmed.

LINE-DRIFT NOTE (bad assumption in the dispatch). The dispatch cites the cone at "354-357". The
literal `coneGeometry` line is `355`. The 354-357 range is the enclosing mesh block, so the defect
is intact, but anyone grepping a fixed line number rather than the token will miss it. The
preflight already greps the literal token string (`coneGeometry args={[1.6, 5, 6]}`,
`cvp-preflight.sh:110`), which is drift-proof. Keep matching by token, not by line.

### Defect summary

| Defect | Site | Verdict at a914ad1 | Preflight check |
| --- | --- | --- | --- |
| D1 no `.chip` / no base controls | `globals.css` (absent), used `AdaptiveExplore.tsx:313,330` + 13 more | PRESENT | PF-3.chip |
| D2 raw composer | `AdaptiveExplore.tsx:335-343` | PRESENT | PF-3.composer |
| D3 cone beacon | `SalishScene.tsx:355` color from `:339` | PRESENT | PF-3.beacon |

No defect is absent or changed. No defect-level escalation. The only escalations are the stale-pin
and stale-capture items (E1 above, E2-E3 below).

---

## 2. COLLISION MAP (cross-referenced to docs/devpost/waves.registry.yaml)

Status legend from the registry. `dispatched` = in-flight, the real serialization risk.
`chartered` / `gated` = not yet building.

### globals.css — `web/app/globals.css`

| Holding wave | Registry lines | Status | What it edits here |
| --- | --- | --- | --- |
| LGC-W4 | 1241-1250 (glob 1247) | chartered | `--glass-*` / `--text-ink` tokens, `.glass-surface`, focus model, self-hide, edge panels, consent preload |
| TWIN-W-LABELS | 1453-1464 (glob 1463) | chartered | `.scene-label` glass label (blur 0 over canvas) |
| WFX-INTEGRATE | 1482-1491 (glob 1490) | gated | water / atmosphere stack landing in live styles |
| CVP-W3 | 1617-1627 (glob 1625) | chartered | baseline component classes (`.chip`, base controls), composer layout, Get-access form, breakpoints |

In-flight risk on globals.css: NONE right now. All four holders are chartered or gated, none dispatched.

### AdaptiveExplore.tsx — `web/app/components/AdaptiveExplore.tsx`

| Holding wave | Registry lines | Status | What it edits here |
| --- | --- | --- | --- |
| CXR-1 | 1307-1319 (glob 1314) | dispatched, commit gated to O0 (1312) | redact internal/reviewer copy on the anonymous home (promotion, effective confidence, raw agent IDs, skill manifest) |
| CVP-W3 | 1617-1627 (glob 1626) | chartered | restyle composer markup at 335-343, apply baseline control classes |

In-flight risk on AdaptiveExplore.tsx: HIGH. CXR-1 is dispatched and edits the same file. CXR owns
copy, CVP owns style, so the concerns are disjoint, but they share line ranges around the composer
335-343, so a textual rebase conflict is likely if CVP does not land second.

### SalishScene.tsx — `web/app/components/scene/SalishScene.tsx`

| Holding wave | Registry lines | Status | What it edits here |
| --- | --- | --- | --- |
| TWIN-W2.6 | 1270-1283 (glob 1277) | dispatched, commit gated to O0 | datum-frame fix, water plane Y0, tint, scale |
| TWIN-W-PERFUX-BUILD | 1297-1305 (glob 1304) | dispatched, commit gated to O0 | resting framing, camera, errorTarget, maxDepth cap |
| TWIN-W-CAM-REG | 1445-1451 (no glob, note names SalishScene) | chartered | camera choreography, resting orbit, focus journeys, tour |
| TWIN-W-LABELS | 1453-1464 (glob 1462) | chartered | geo-anchored place labels |
| WFX-INTEGRATE | 1482-1491 (glob 1489) | gated | water / atmosphere in the live scene |
| ORCA-OINT | 1587-1595 (glob 1594) | gated | mount the driven orca into the underwater view |
| CVP-W3 | 1617-1627 (glob 1627) | chartered | beacon geometry / scale / material ONLY (mount net-new buoy module) |

Note: `TWIN-W-CAM` (1284-1290, chartered) is the wave_shape sibling of the registry-mirror
`TWIN-W-CAM-REG`. Both name SalishScene edits and instruct serializing against W4 and W-LABELS.

In-flight risk on SalishScene.tsx: HIGHEST. Two dispatched lanes (TWIN-W2.6 datum and
TWIN-W-PERFUX-BUILD framing) are actively editing this file. CVP only touches the beacon, but it
rebases onto whatever those two land.

---

## 3. RECOMMENDED SERIALIZE ORDER (per hot file, for O0 to request)

Anchored to the locked decision in the charter that CVP baseline lands BEFORE LGC identity, and to
CVP-W3 operator_gate (`waves.registry.yaml:1622`) requiring `git pull --rebase` first and serialize
vs LGC / CXR / 3D-TWIN / WFX / ORCA.

### globals.css

```
CVP-W3 (baseline)  ->  LGC-W4 (token drop, .glass-surface)  ->  TWIN-W-LABELS (.scene-label, sequence_after LGC-W4 per 1458)  ->  WFX-INTEGRATE (water/atmosphere)
```

CVP-W3 is safe to go first here because no globals.css holder is dispatched. Going first also
satisfies the locked baseline-before-LGC ordering. The only requirement is that CVP add NEW
selectors and never the `--glass-*` / `--text-ink` family so LGC-W4 can drop tokens on top cleanly.

### AdaptiveExplore.tsx

```
CXR-1 (already dispatched, copy redaction, commit-gated O0)  ->  CVP-W3 (style, rebases onto CXR-1)
```

CXR-1 is in-flight, so it lands first. CVP-W3 must `git pull --rebase` (PF-4.rebase,
`cvp-preflight.sh:117`) before touching the composer, then restyle the post-redaction markup. CVP
must not alter any copy string CXR redacted.

### SalishScene.tsx

```
TWIN-W2.6 (datum, dispatched)  ->  TWIN-W-PERFUX-BUILD (framing, dispatched)  ->  CVP-W3 (beacon module mount)  ->  TWIN-W-CAM-REG (camera)  ->  TWIN-W-LABELS (labels)  ->  WFX-INTEGRATE (water)  ->  ORCA-OINT (orca mount)
```

CVP-W3 must serialize AFTER the two dispatched TWIN waves so it does not rebase onto a moving datum
and framing. CVP touches only the beacon mount seam, so it slots cleanly between the framing work
and the later camera / label / water / orca lanes.

---

## 4. BOUNDARY-VIOLATION HUNT (risk -> guardrail)

### (a) Accidentally introducing an LGC token family or LGC behavior

| Risk | Guardrail |
| --- | --- |
| CVP baseline CSS references or defines `--glass-*` or `--text-ink` | PF-5.tokens greps added diff lines for `--glass-|--text-ink` and FAILs, `cvp-preflight.sh:132-136` |
| CVP adds ghost-text, self-hide, or consent preload behavior | PF-5.lgc greps added lines for `ghost-text|ghostText|self-hide|selfHide|consent.*preload` and FAILs, `cvp-preflight.sh:137-141` |

Clarification to prevent a false guardrail trip. The home already uses baseline tokens
`var(--accent, #5aa9e6)`, `var(--text-muted)`, and `var(--border)` at
`AdaptiveExplore.tsx:318,305` and across globals.css. These are EXISTING baseline custom properties,
not the LGC identity family. CVP may reuse `--accent` / `--text-muted` / `--border`. Only
`--glass-*` and `--text-ink` are off limits. The PF-5 grep is scoped exactly to those two stems, so
reusing the existing tokens will not trip it.

### (b) Accidentally changing an anonymous-path copy string (CXR's lane)

| Risk | Guardrail |
| --- | --- |
| CVP edits the composer label "Ask about the Salish Sea" or the placeholder while restyling 335-343 | CXR-2 deny-term grep `tools/waves/gates/console-deny-terms.sh` (gate `cxr-deny-terms`, registry 1750-1753) plus the prose gate, surfaced as PF-6.prose (`cvp-preflight.sh:146`). PF-5.copy marks CVP style-only (`:142`) |

Recommendation. CVP keeps every visible string byte-identical and changes only markup and class
names. Copy is CXR-1's lane. There is no automated grep that asserts CVP left the strings untouched,
so add a Read-review of the AdaptiveExplore diff at W3 (see E2).

### (c) Accidentally altering camera / framing / datum / re-bake (TWIN's lane)

| Risk | Guardrail |
| --- | --- |
| CVP beacon edit perturbs camera position, water plane Y0, `useTilesLayer`, errorTarget, or maxDepth | CVP-W3 scope is beacon geometry / scale / material only (registry 1627 + W1_DISPATCH A3 TWIN boundary, lines 60-62). PF-4.worktree confirms no concurrent hold (`cvp-preflight.sh:118-123`) |

ESCALATION E2. The preflight has NO grep that asserts CVP left camera / datum / framing untouched on
SalishScene. PF-3.beacon only confirms the OLD cone still matched before the edit, and after CVP
swaps the geometry that check will FLIP to FAIL by design. There is no positive assertion that the
camera, the water-plane Y, `useTilesLayer`, `errorTarget`, or `maxDepth` were not moved. Recommend
O0 require a Read-examined diff of `SalishScene.tsx` at W3 that touches only the beacon mount, or add
a PF check that the camera / datum / tiles lines are byte-identical to the pin.

### (d) Accidentally altering water (WFX's lane)

| Risk | Guardrail |
| --- | --- |
| CVP touches the water material or seabed shader while near the beacon | scope discipline only; WFX-INTEGRATE owns water (registry 1482-1491). No preflight grep covers it |

ESCALATION E3. Same gap as E2 for the water surface. The seabed `meshStandardMaterial` at
`SalishScene.tsx:885` and the water plane are WFX / TWIN territory and the beacon group sits in the
same file. There is no automated assertion CVP left them alone. Fold this into the Read-examined
SalishScene diff review at W3.

---

## 5. BAD-ASSUMPTION LEDGER (consolidated)

| # | Assumption in charter / dispatch | Reality at a914ad1 | Impact |
| --- | --- | --- | --- |
| 1 | Pin is `97b6397` | HEAD is `a914ad1`, one commit ahead | Stale pin string everywhere; defects still present (E1) |
| 2 | cvp_preflight.json reflects HEAD | Capture head `97b6397` predates the gate script landing on HEAD | Regenerate at W3 (E1) |
| 3 | "Chip used at AdaptiveExplore.tsx:330" | `.chip` used at 15 sites across 7 components, no rule anywhere | Baseline `.chip` is global, widens W4 review surface |
| 4 | Cone at "354-357" | `coneGeometry` literal is line 355 | Match by token not line; preflight already does |
| 5 | `.ask-*` at "globals.css:308-318" | `.ask-label` at 308, `.ask-textarea` at 309, family spans 296-458 | Minor cite drift; family present, home composer uses none of it |
| 6 | `.ask-*` unused on the home | Home composer 335-343 uses none; `.ask-user`/`.ask-assistant` used for transcript only | Assumption holds for the composer |
| 7 | SalishScene serialization is the headline risk | Two dispatched TWIN waves are in-flight on it now; CXR-1 dispatched on AdaptiveExplore | CVP must rebase after them; globals.css has no in-flight holder |

---

## 6. ESCALATIONS FOR O0

- E1. Stale pin and stale capture. Pin `97b6397` is one commit behind HEAD `a914ad1`. Defects
  persist (no plan break), but reconcile the pin string in the four artifacts in section 0 and
  regenerate `gate_captures/cvp_preflight.json` against `a914ad1` before W3.
- E2. No positive camera / datum / framing guardrail. PF-3.beacon flips to FAIL by design once the
  cone is replaced, and nothing asserts the camera / `useTilesLayer` / `errorTarget` / `maxDepth`
  lines are unchanged. Require a Read-examined SalishScene diff at W3 or add a PF byte-identical check.
- E3. No water-surface guardrail. The seabed material and water plane share SalishScene with the
  beacon group and have no automated CVP-left-it-alone assertion. Fold into the W3 diff review.
- Awareness, not a blocker. Global `.chip` blast radius spans 7 components. Widen the W4
  Read-examine set beyond `/` so the baseline does not regress reviewer / explore surfaces.

No code, registry, or gate file was changed by this agent. The only file written is this one,
`.cca/catalogue/O0/20260628_console-visual-pass/findings/CVP-ADVERSARIAL.md`.
