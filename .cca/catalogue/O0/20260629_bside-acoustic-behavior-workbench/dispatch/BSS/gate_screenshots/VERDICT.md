# BSS-ACCEPT verdict, studio + managed-skill console render-path

Verdict: **PASS** for the studio routes (real fixture, truth labels, NC attribution, honest
fallback). Two reported findings on the LIVE paths that need the backend, neither a
dishonest-claim defect: the live console-panel render and the live annotation POST are not
exercisable in the headless host environment because the host dev server has no
`ORCAST_API_BASE`, and the annotation POST path is not allow-listed in the proxy nor implemented
in the backend.

## Capture channel

Real GPU host, but these are DOM/SVG pages, so `canvas: false` is expected and correct.

- Host: `aimez-gpu-capture` EC2 `i-0e66ac03c729ebe02`, us-east-1.
- Driver: `infra/render_host/render.sh` over SSM + S3.
- Renderer string available; `errorCount: 0` on both studio routes.

## Frames (in this folder)

1. `bss_01_studio_landing.png` route `/studio`.
2. `bss_02_annotate_studio.png` route `/studio/annotate`.

## Read-examination findings

1. `/studio` landing renders. CONFIRMED. Title `Processing studio` and three cards: `Annotate`
   (Live now), `Tagtools pipeline` (Served as managed skills. Panels wire in at integration.),
   `Behavior capture` (Served as a managed skill. Panels wire in at integration.). The
   "panels wire in at integration" copy is honest about the console-panel wiring.

2. `/studio/annotate` loads the REAL fixture with truth labels + NC attribution. CONFIRMED.
   - Subtitle: "Real DTAG kinematics from deployment mn09_203a. humpback (Megaptera
     novaeangliae). Contrast and reference only. It never drives an orca." (humpback is
     contrast/reference, never an orca driver, per the locked decision).
   - License line: "License status CC-BY-NC-4.0, non-commercial, authorized per O0 SIGN_OFF
     decision 1".
   - Kinematics timeline plots the real depth (meters down), ODBA, expert-annotation bands, and
     selected dive from `dtag_mn09_203a.json`.
   - Honest no-audio note: "Audio lane is not bound in this sandbox. ... No placeholder audio is
     shipped."
   - "New annotation" form is populated from the fixture (dive `#1 11.2 m 57 s Side rolls`, etc).
   - Below the fold the page also lists the fixture `tagtools_steps` with their `truth_label`.

3. The three managed-skill panels (tagtools_step, poster_viz, behavior_capture). PARTIAL /
   reported. The panel COMPONENTS exist and are wired correctly in
   `web/app/components/ActiveSurfaceHost.tsx`: `TagtoolsStepPanel`, `PosterVizPanel`, and
   `BehaviorCapturePanel` each render a `HonestyBadge` (the `truth_label`) plus an
   `AttributionLine` (`license` + `attribution`) when the console turn supplies their ctx
   (`run_tagtools_step` / `render_poster_viz` / `capture_behavior`). The backing data carries the
   truth label + NC attribution: `studio_artifacts.json` has `truth_label: "baked"`,
   `license: CC-BY-NC-4.0`, and the attribution "Humpback DTAG mn09_203a ... authorized by O0
   SIGN_OFF decision 1.", and `studio_skills.py` forwards `truth_label` + `license` +
   `attribution` for each skill.

   FINDING: I could NOT render these panels LIVE in the console on this host. The panels are
   `sidebar` panels populated by a backend console turn, and the host dev server's same-origin
   proxy returns `500 {"error":"ORCAST_API_BASE not configured"}` for every backend call (probed
   directly, see below), so no turn populates `prepare.context`. With no ctx the panels render
   their honest empty state ("No tagtools step for this turn." etc), not a fabricated panel.
   Rendering them live needs a backend reachable from the renderer, which is not the headless
   host setup. The render path + truth-label/NC-attribution wiring is verified at the code + data
   level.

4. Annotation POST + proxy allowlist. FINDING (honest fallback is in place).
   Direct probe on the host (curl to the dev server proxy at 127.0.0.1:3010):
   - `POST /api/be/api/dtag/annotations` -> `500 {"error":"ORCAST_API_BASE not configured"}`
   - `GET  /api/be/api/dtag/annotations` -> `500`
   - `GET  /api/be/api/live-hydrophones` (allow-listed) -> `500`
   So on the host EVERY backend call 500s because `ORCAST_API_BASE` is unset in the dev server
   env. Beyond the host env, the live POST path is not reachable in production either:
   - the proxy `web/app/api/be/[...path]/route.ts` does NOT list `api/dtag/annotations` as a
     public POST in `isPublicRequest`, so an anonymous POST requires auth -> 401; and
   - the backend `src/aws_backend/routers/dtag.py` has NO `annotations` route, so even an
     authenticated POST would 404.
   The studio handles all of these honestly: `HttpAnnotationStore.create()` throws on the non-OK
   response, `AnnotateStudio.submit()` catches it and falls back to `InMemoryAnnotationStore`, and
   the UI shows the honest label "Backend endpoint unreachable here. Kept locally, round-trip
   verified. Live persist is a batched ACCEPT item." (it never dishonestly claims backend
   persistence). Per the dispatch the in-memory fallback is acceptable; the dishonest claim, which
   is absent, is the only thing that would fail. (The Save button is a click the headless renderer
   cannot perform, so the captured frame shows the pre-submit state; the fallback path is verified
   by the 500 probe plus the catch-to-local code + honest label.)

## Recommended follow-ups for O0 (NOT applied)

- To make the live annotation POST reachable: add a backend `POST /api/dtag/annotations` route and
  allow-list it in the proxy (or keep it auth-gated and document that anonymous demo uses the
  honest local fallback). This is a backend + convergence (proxy) change, O0-gated.
- To capture the live console panels: they need a backend turn; either point the host dev server
  at a real `ORCAST_API_BASE` or add a deterministic console-panel capture fixture. Out of ACCEPT
  scope.

## O0 ruling

O0 ACCEPTED the honest in-memory annotation fallback for v1; the live `POST /api/dtag/annotations`
+ proxy allow-list + `ORCAST_API_BASE` is a flagged backend follow-up, not a v1 blocker.

## Defects

No dishonest-claim defect. No fix applied in the BSS scope.

## Commit gate

Nothing committed or pushed.
