# BSS-INTEGRATE wiring note

How the net-new BSS-BUILD output wires into the console turn at the O0-gated
BSS-INTEGRATE step. BUILD touched no convergence files. INTEGRATE is a single
editor on the console turn and serializes against BST, LGC, and CVP.

## Convergence files INTEGRATE will edit

- `web/app/components/AdaptiveExplore.tsx`
- `web/app/components/ActiveSurfaceHost.tsx`
- `web/lib/uiIntent.ts`
- `web/app/globals.css`

`git pull --rebase` first. Serialize against BST, LGC, CVP on these files.

## 1. Activate the managed skills

In `src/aws_backend/casting/skills_manifest.json`, flip these from
`enabled: false` to `true`:

- `run_tagtools_step` (T1, derived)
- `render_poster_viz` (T1, baked)
- `capture_behavior` (T1, measured_behavior_modeled_camera)

After activation the public catalog count rises from 15 to 18 and public-enabled
from 9 to 12. Update `tests/aws_backend/test_casting_policy.py` expected counts in
the same change (that test file is outside the BSS build scope, so the count bump
is an INTEGRATE edit, not a BUILD edit). The dispatch table already merges
`STUDIO_DISPATCH`, so no further `skills.py` change is needed.

## 2. Allowlist the console panels

Add panel ids to the `PANEL_LABELS` map in `web/lib/uiIntent.ts` and render them
in `ActiveSurfaceHost.tsx`:

- `tagtools_step` for `run_tagtools_step`
- `poster_viz` for `render_poster_viz`
- `behavior_capture` for `capture_behavior`
- `annotation_studio` deep link to `/studio/annotate`

The planner seed (`surface-planner-v1`) gains these as allowed panels. Keep them
sidebar-surface unless a map binding is added later.

## 3. Annotation backend binding

`web/lib/annotation/store.ts` ships two stores. The studio uses
`InMemoryAnnotationStore` in the sandbox. INTEGRATE binds `HttpAnnotationStore`
to the backend annotation endpoint through the same-origin proxy
`web/app/api/be/[...path]/route.ts`. Decisions for INTEGRATE:

- Confirm the backend route. Default in code is `api/dtag/annotations`. The dtag
  router exists; a POST and GET annotation endpoint may need adding (backend
  lane, separate owner).
- Add the route to the proxy allow-list if it should be public, or keep it keyed
  and behind the authenticated path. Community write annotations should follow the
  community-submission contract style (server assigns id and status).

## 4. Studio route

`/studio` and `/studio/annotate` are live net-new routes under the `(workbench)`
route group. INTEGRATE adds a console deep link to `/studio/annotate`. No change
to the existing `/workbench` route.

## 5. Deferred follow-up (O0 gate 2, posture 3)

The interactive 3D dive-lattice port to the existing react-three-fiber and
`three` stack is DEFERRED. It is the next interactive step and adds no new
dependency. The baked Plotly HTML serves in the interim through
`render_poster_viz` with `js_port_status: deferred-posture-3-react-three-fiber`.
Do not build the port in this wave.

## Acceptance hooks (BSS-ACCEPT, gated)

- Console invokes `render_poster_viz` and `run_tagtools_step` and renders panels.
- An annotation round-trips with provenance through the bound backend.
- `capture_behavior` produces a capture spec the director runs on a real
  classified DTAG behavior into a 3D capture.
