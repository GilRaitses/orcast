# CVP globals.css additive boundary versus LGC, TWIN, WFX

W1 Agent A4, console-visual-pass lane. Read-only discovery. This doc is the only file written by this agent.

## Pin reconciliation

Dispatch named `main 97b6397`. Actual `HEAD` in the working tree is `a914ad1` (charter anticipated advancement past the pin). Every cite below is `file:line` against the current tree. Subject file `web/app/globals.css`, 588 lines.

## Grep evidence captured

Command 1, glass and ink token families.

```
$ rg -n -- "--glass-|--text-ink" web/app/globals.css
(no matches)
```

Command 2, the glass-surface and scene-label selectors.

```
$ rg -n -- "\.glass-surface|\.scene-label" web/app/globals.css
(no matches)
```

Command 3, ghost, self-hide, preload.

```
$ rg -ni -- "ghost|self-hide|preload" web/app/globals.css
106:.btn.ghost { background: transparent; color: var(--text); border: 1px solid var(--border); }
319:/* Sleek chat composer: cycling ghost prompt + round send */
347:.chat-ghost {
361:.chat-ghost.visible { opacity: 1; transform: translateY(0); }
```

Command 4, scene-prefixed selectors and any WFX surface.

```
$ rg -ni -- "wfx|water-fx|\.fx-|\.scene-" web/app/globals.css
497:.scene-host, .scene-fallback { width: 100%; height: 100%; }
498:.scene-host { width: 100%; height: 100%; }
499:.scene-loading, .scene-fallback {
508:.scene-fallback-note { font-size: 0.8rem; text-align: center; }
509:.scene-beacon-label {
```

Command 5, presence of the selectors CVP intends to add.

```
$ rg -n -- "\.chip" web/app/globals.css            -> ABSENT
$ rg bare button|textarea|input|label|select       -> ABSENT (no bare element rules)
$ rg -ni get-access|signup|waitlist|field          -> ABSENT
$ rg -n -- ":root" web/app/globals.css              -> 1 block only (line 1)
```

## :root token-family map

A single `:root` block exists at `web/app/globals.css:1` through `:13`. No second `:root` and no media-scoped token overrides.

| Family | Properties | Cite | Status at pin |
| --- | --- | --- | --- |
| Background and surface | `--bg`, `--surface`, `--surface-2` | `globals.css:2`, `:3`, `:4` | present, CVP baseline |
| Border | `--border` | `globals.css:5` | present, CVP baseline |
| Text | `--text`, `--text-muted` | `globals.css:6`, `:7` | present, CVP baseline |
| Accent | `--accent` | `globals.css:8` | present, CVP baseline |
| Status | `--pass`, `--fail`, `--warn` | `globals.css:9`, `:10`, `:11` | present, CVP baseline |
| Radius | `--radius` | `globals.css:12` | present, CVP baseline |
| Glass | `--glass-*` | none | absent at pin, reserved for LGC-W4 |
| Ink | `--text-ink` | none | absent at pin, reserved for LGC-W4 |

Disambiguation. `--text-muted` at `globals.css:7` is the existing muted-text token and is distinct from the LGC `--text-ink` family, which does not exist at the pin. CVP keeps using `--text` and `--text-muted` and does not introduce `--text-ink`.

## glass-surface and scene-label ownership map

| Selector or behavior | Owner lane | Cite | Status at pin |
| --- | --- | --- | --- |
| `.glass-surface` | LGC-W4 | none | absent, reserved for LGC-W4 |
| `--glass-*` token family | LGC-W4 | none | absent, reserved for LGC-W4 |
| `--text-ink` token family | LGC-W4 | none | absent, reserved for LGC-W4 |
| ghost-text `.chat-ghost`, `.chat-ghost.visible` | LGC-W4 identity | `globals.css:347`, `:361` | present at pin, reserved to LGC, CVP does not add or redefine |
| self-hide behavior | LGC-W4 | none | absent, reserved for LGC-W4 |
| preload behavior | LGC-W4 | none | absent, reserved for LGC-W4 |
| `.scene-label` | TWIN-W-LABELS | none | absent, reserved for TWIN-W-LABELS |
| WFX surfaces, any `wfx`, `.fx-`, `water-fx` | WFX-INTEGRATE | none | absent, reserved for WFX-INTEGRATE |

Two clarifications that prevent false collisions.

1. `.btn.ghost` at `globals.css:106` is a transparent button variant, not ghost-text. It stays CVP baseline and is unrelated to the LGC ghost-text behavior.
2. The `.scene-*` selectors that exist at `globals.css:497` through `:517`, namely `.scene-host`, `.scene-fallback`, `.scene-loading`, `.scene-fallback-note`, and `.scene-beacon-label`, are existing explore-shell baseline owned outside CVP-LGC glass. None of them is `.scene-label`. TWIN owns only the exact `.scene-label` selector, which is absent. CVP adds no `.scene-*` selector at all.

## CVP baseline versus LGC identity, split by selector

CVP baseline already present at the pin. CVP owns these and may refine them in place. None redefines a deny-list family. Examples with cites: `.topbar` `globals.css:28`, `.nav` `:52`, `.card` `:71`, `.badge` `:81`, `.btn` `:97`, the chat composer container and controls `.chat-composer` `:320`, `.chat-input` `:335`, `.chat-send` `:362`, `.chat-footer` `:379`, the adaptive console panels `.console-card` `:520`, `.console-panel-label` `:527`, and the existing media breakpoints at `:47`, `:64`, `:115`, `:122`, `:302`, `:483`.

CVP net-new additions, absent at the pin, confirmed by grep command 5. These are the genuine baseline additions this lane introduces:

| CVP add | Namespace | Collision check | Family check |
| --- | --- | --- | --- |
| `.chip` and states such as `.chip.active`, `.chip:hover`, `.chip:disabled` | component class | no existing `.chip`, absent at pin | adds no `--glass-*` or `--text-ink`, uses existing `--surface-2`, `--border`, `--accent` |
| base `button`, `textarea`, `input`, `label`, `select` element styles | bare element | no bare element rules exist at pin | reuses existing tokens only |
| Get-access form field selectors such as `.access-field`, `.access-label`, `.access-input` | component class, access namespace | absent at pin | reuses existing tokens only |
| composer layout refinement on existing non-ghost composer selectors | existing CVP baseline | refine in place, no rename | does not touch `.chat-ghost*` |
| panel hierarchy and mobile breakpoint refinements | existing CVP baseline | refine in place, no rename | reuses existing tokens only |

LGC identity, off limits to CVP. `--glass-*`, `--text-ink`, `.glass-surface`, the ghost-text selectors `.chat-ghost` and `.chat-ghost.visible`, self-hide, and preload. CVP layers underneath LGC, so LGC adds glass identity on top of CVP later.

## Additive boundary

### Allow-list, selectors CVP may add or own

1. `.chip` and its state variants `.chip.active`, `.chip:hover`, `.chip:disabled`.
2. Base element rules for `button`, `textarea`, `input`, `label`, `select`.
3. Get-access form field selectors in an access component namespace, for example `.access-field`, `.access-label`, `.access-input`, `.access-error`.
4. CVP composer layout, panel hierarchy, and mobile breakpoint rules, added as new selectors or refined in place on the existing CVP baseline selectors listed above.
5. All existing non-glass, non-ghost, non-scene-label, non-WFX selectors already in `globals.css`, which CVP continues to own.

### Deny-list, selectors and families CVP must never add or redefine

1. `--glass-*` token family. Owner LGC-W4.
2. `--text-ink` token family. Owner LGC-W4.
3. `.glass-surface`. Owner LGC-W4.
4. ghost-text behavior including `.chat-ghost`, `.chat-ghost.visible`, and any new ghost-text rule. Owner LGC-W4.
5. self-hide behavior. Owner LGC-W4.
6. preload behavior. Owner LGC-W4.
7. `.scene-label`. Owner TWIN-W-LABELS.
8. WFX surfaces, any `wfx`, `.fx-`, or `water-fx` selector. Owner WFX-INTEGRATE.

### Additivity proof

The `:root` block holds exactly the eight present families at `globals.css:1` through `:13`, and none of them is `--glass-*` or `--text-ink`. Grep command 1 returns no matches for the glass or ink families, so CVP cannot redefine what does not exist, and CVP adds none of them. Grep command 2 returns no matches for `.glass-surface` or `.scene-label`, so CVP adds neither. Grep command 3 shows ghost-text lives only in the pre-existing `.chat-ghost` selectors at `globals.css:347` and `:361`, which CVP leaves untouched and adds no new ghost-text rule, while `.btn.ghost` at `:106` is a button variant outside the ghost-text family. Grep command 4 shows no WFX surface and confirms `.scene-label` is absent while the present `.scene-*` selectors are existing baseline, not the TWIN label. Grep command 5 confirms `.chip`, the bare element rules, and the access form selectors are all absent, so every CVP net-new selector introduces a brand new name that collides with nothing and reuses only the present token families. CVP therefore introduces only new selectors and redefines none of the deny-list, which proves the boundary is additive.
