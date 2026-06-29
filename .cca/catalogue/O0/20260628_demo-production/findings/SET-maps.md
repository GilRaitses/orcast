# SET-maps

Status: READY

Prerequisite: Google Maps usable (key present, tiles load), serving A1, A4, A5.

## Read-examined check

Browser frame on `/ask` (`set_ask_map.png`, viewId adb6a4) after load: the
Google Map paints fully. The San Juan Islands basemap renders with place labels
(Roche Harbor, Lopez Island, Rosario Strait), the Map / Satellite toggle, the
Street View pegman, and the footer "Map data ©2026 Google". A red pin renders at
the pin coordinate.

CDP DOM probe on `/ask`:

```
{"canvasCount":0,"hasGmStyle":true,"mapsImgTiles":12,"bodyHasMapError":false}
```

`hasGmStyle:true` (the `.gm-style` Google Maps root mounted), 12 painted Google
tile images, and no Maps error string ("for development purposes only",
RefererNotAllowed, ApiNotActivated) in the body. Key is present and authorized in
prod (no `NEXT_PUBLIC_MAPS_KEY` fallback message rendered).

## Evidence

- Built surface: `web/app/components/SightingCheckPanel.tsx` (`APIProvider apiKey={key}`),
  `web/app/components/MapHero.tsx` (`APIProvider` / `Map mapId="orcast-forecast"`),
  `web/app/components/ExploreGuidePanel.tsx`.
- The map canvas mounts and tiles paint on the Read-examined `/ask` frame.

## Note (for BLK, not a blocker)

On `/` the primary surface is the custom 3D `SalishScene` (3d-tiles-renderer), not
Google Maps; `MapHero` (Google Maps) is the `SceneHost` fallback. Google Maps tile
painting is proven on `/ask` (A5) and is the surface A4 provenance uses. A1's home
"map" is the 3D scene.

## Ports / pids

None.
