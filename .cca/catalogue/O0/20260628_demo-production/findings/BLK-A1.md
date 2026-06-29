# BLK-A1, forecast as the grounding layer (home)

Verdict: BLOCKED (1 moving part). Does not advance to CAM as written.

Prereqs: SET-web READY, SET-maps READY, SET-forecast READY.

## Moving parts

1. Forecast map mounts on `/` — CLEARED. The 3D `SalishScene` paints (land, water,
   forecast marker) in the Read-examined frame `set_home.png`. File:
   `web/app/page.tsx` -> `web/app/components/scene/SceneHost.tsx` / `SalishScene`.
2. Lowercase orcast hero copy correct — CLEARED. Brand `orcast` (lowercase) and hero
   "orcast. Explore the Salish Sea" render. CDP: `brand:"orcast"`.
3. Confidence meter shows the real 0% promoted on `/` — BLOCKED. Defect 1: the home
   `/` surface contains no confidence meter and no "0%"/"promoted" text. CDP probe of
   `document.body.innerText`: `hasConfidenceWord:false` (no "confidence", "0%", or
   "promoted"). The honest 0% promoted renders on `/gates`
   (`web/app/gates/page.tsx`), not on `/` (`web/app/page.tsx`). The home was
   redesigned to the explore/console shell.

## Honesty caption

A1's Honesty caption (the honest 0% promoted, modeled-probability label) is
presentable on `/gates`, but NOT on the `/` surface the beat names. The beat's
Show ("/ map, confidence meter, the honest 0% promoted") and Evidence ("the live
forecast render showing 0% promoted confidence") are not satisfied on `/`.

## Numbered defect (returned to build owner / charter)

1. A1 Show/Evidence target a confidence meter + 0% promoted on `/`, but `/` is the
   explore/console shell with no confidence meter. Fix is a build/charter decision
   (not a First-AD edit): either surface a confidence meter + 0% promoted on `/`, or
   re-point A1's Show/Evidence to `/gates` (where "confidence 0% · promoted" renders
   verbatim). File: `web/app/page.tsx` (no confidence element) vs `web/app/gates/page.tsx`.
