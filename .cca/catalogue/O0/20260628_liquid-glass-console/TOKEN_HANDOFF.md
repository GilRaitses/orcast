# LGC token handoff (the cross-lane contract)

This file locks the one dependency other lanes wait on from LGC: the Part A glass design
tokens landed into `web/app/globals.css :root`. Authority for the token values is
`LIQUID_GLASS_CONSOLE_MANIFEST.md` Part A. This handoff is what makes the twin labels and
the demo's LGC-styled beats buildable, so it is pinned and sequenced.

## What LGC must land first (LGC-W4)

LGC-W4 lands the Part A token block into `web/app/globals.css :root` as part of the
GlassSurface build. The token set the downstream consumers read (names per the manifest /
RP3 grounding):

- Fill tints: `--glass-tint-cool` (cool instrument frost, for surfaces over the
  unbounded-luminance canvas), and the neutral frost tint.
- Opacity floor and HUD: `--glass-opacity-floor` (the AA-insurance minimum, ~0.62) and
  `--glass-opacity-hud` (~0.66).
- Scrim: `--glass-scrim` and `--glass-scrim-alpha` (the AA-insurance wash painted under
  text over live frames).
- Ink colors (text is always ink, never fill): `--text-ink` (primary), `--text-muted-ink`
  (secondary), `--accent-ink` (online/selected, deep green), `--warm-ink`
  (offline/warning, deep terracotta).
- Hairline: `--glass-hairline`.

The token values are the manifest's; LGC-W4 owns dropping them in. No downstream lane
invents or duplicates these tokens.

## Hard rule that travels with the tokens (M3)

Any surface placed over the always-repainting r3f canvas (the scene labels, any map HUD
chip) uses `blur=0` with fill plus scrim only and NO `backdrop-filter`. `backdrop-filter`
is reserved for the chat shell and the console dock, which are not over the canvas. This
rule is enforced at the consumer gates (twin W-LABELS, the demo SCR R3/R5).

## Downstream consumers (blocked until the tokens land)

1. **TWIN W-LABELS** (`.cca/catalogue/O0/20260627_terrain-bathymetry-twin/W-LABELS_DISPATCH.md`).
   The `.scene-label` class reads `--glass-tint-cool`, the opacity floor, the scrim, the
   ink colors, and the hairline. W-LABELS holds until these `:root` tokens resolve, then
   builds the geo-anchored, clamped-scale, glass-styled labels. It also tunes
   `LABEL_REF_DIST` against the RP2 resting framing.
2. **Demo LGC-styled beats** (`.cca/catalogue/O0/20260628_demo-production/`). Beat B3 (the
   3D twin) shows the glass-styled scene labels; the demo's HUD chips inherit the same
   token family. The CAM stage cannot capture the LGC-styled look before the tokens land.

## Sequencing (O0 enforces)

```
LGC-W4 Part A tokens into globals.css :root
  -> RP2 resting framing (W-PERFUX-BUILD)            # defines LABEL_REF_DIST
    -> TWIN W-LABELS (clamped scale + .scene-label glass, frame-verified accept)
      -> DEMO CAM capture of the LGC-styled twin beats (B3)
```

## Collision lock

`web/app/globals.css` and `web/app/components/scene/SalishScene.tsx` are convergence files
shared by LGC, the twin camera/labels waves, and W4. Per the LGC charter collision lock,
every edit to them serializes through O0. LGC owns the `:root` token drop and the
`.glass-surface` / chat-shell classes; the twin lane owns the `.scene-label` family and the
scene mount; neither edits the other's region.

## Fresh-thread owner

The LGC lane runs on its own thread per `ORCHESTRATOR_DISPATCH_PROMPT.md`. The owner runs
W0 (read-only research) first and pauses at the target-surface gate for O0. The token drop
is part of LGC-W4 (after the W3 design-acceptance gate). Until then, W-LABELS and the demo
LGC-styled beats are explicitly blocked on this handoff, not on each other.
