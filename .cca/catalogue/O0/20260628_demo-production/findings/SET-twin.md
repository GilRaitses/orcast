# SET-twin

Status: READY (sandbox twin route renders land at the waterline)

Prerequisite: twin sandbox build state present, the sandbox twin route renders land
at the waterline, serving B3.

## Read-examined check

The B3 twin with the choreographed pan maps to the `/journey` sandbox route (East
Sound camera choreography, `web/app/(sandbox)/journey/`).

GET `/journey` -> 200. Browser-rendered frame (`set_journey.png`, viewId adb6a4)
after ~5s tile streaming: a 3D terrain twin paints, dark land masses meeting a
lighter water surface with visible shoreline foam where land transitions to water
(land at the waterline). Overlay HUD reads:

```
Camera Director (W1) East Sound journey.
subject: Anacortes to Orcas ferry
altitude: 276 m
target: 48.5634, -122.8861
orbiting: no
```

CDP canvas probe: `{"canvasCount":1,"dims":["641x564"]}` (the WebGL scene canvas is
mounted and sized). The choreography HUD confirms a non-random, scripted camera
director (not a free orbit).

## Evidence

- Built surface: `web/app/(sandbox)/journey/page.tsx`, `JourneyHost`,
  `web/app/(sandbox)/journey/JourneyScene.tsx`, camera `web/lib/scene/camera/director.ts`,
  water/waterline `web/lib/scene/water2/depthWater.ts` (W2.6 datum).
- Land-at-waterline observed in the rendered `/journey` frame; W1 Camera Director
  HUD observed.

## Note (for BLK, not a SET blocker)

Per `../BEAT_SET.md` B3, the full Show carries needs-build parts that are direction:
the choreographed pan across *labeled* places (post W-CAM labels) and a *deployed*
(non-sandbox) twin route. SET only asserts the sandbox twin route renders land at
the waterline, which is observed. Label/deploy completeness is a BLK determination.

## Ports / pids

None.
