# SET-web

Status: READY

Prerequisite: capture target reachable. Locked target is the prod alias
`https://orcast-h0.vercel.app` (no local dev server started, so no ports/pids).

## Read-examined check

GET `/`:

```
HTTP_STATUS:200
SIZE:8717
URL_EFFECTIVE:https://orcast-h0.vercel.app/
```

Returned HTML carries the rendered forecast hero marker:

- `<title>orcast</title>`
- `<h1 class="hero-title">orcast. Explore the Salish Sea</h1>`
- hero subtitle "A 3D map of the Salish Sea with a live encounter forecast."
- the explore console (`data-demo="explore-console"`) and scene host (`data-demo="salish-scene"`).

Browser-rendered frame (`set_home.png`, viewId adb6a4): the 3D Salish Sea
terrain/bathymetry scene paints (land masses, water, a forecast marker pin). The
hero, nav, and console all render.

## Evidence

- Built surface: `web/app/page.tsx`, `web/app/components/scene/SceneHost.tsx`
  (`SalishScene`), nav from `web/app/layout.tsx`.
- HTTP 200 + hero `h1.hero-title` text observed in the returned HTML and in the
  rendered frame.

## Ports / pids

None. Capture target is the prod alias; no long-lived local process started.
