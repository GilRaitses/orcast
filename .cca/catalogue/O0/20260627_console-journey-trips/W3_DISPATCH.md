# W3 dispatch: Trips journey

Status: blocked on W2. Discipline unchanged. Convergence file `casting/planner.py` has a single editor
(Trips Planner Branch), phase B, after the phase-A producers land. No new ML promoted.

## Sequencing
- Phase A (parallel): Connections Planner, Corridor Traffic Model, Kayak Branch, Sidequests + Auth Chip.
- Phase B: Trips Planner Branch wires the orienting question + per-branch panels into `planner.py`.

## Agent A — Connections Planner (owns src/aws_backend/casting/trips/connections.py; phase A)
YOUR TASK: "Make your sailing / flight" reasoning. Given an intent (depart X at T, reach islands or
return for a flight), combine WSF schedule + sailing space + WSDOT ETA (realtime now; modeled future
via the corridor model) + flight board. Return a structured plan with per-leg honesty labels and a
freshness stamp.
DELIVERABLES: `src/aws_backend/casting/trips/connections.py`. Exports `plan_connection(intent)`.
VALIDATION: pytest answering "depart SeaTac 3pm Friday, catch the 6:30 Anacortes sailing?" on fixtures,
returning a labeled feasibility + interval.
COLLISION-AVOIDANCE: own ONLY this file; consume the W2 clients + W3 corridor model.
RETURN: diff + pytest output.

## Agent B — Corridor Traffic Model (owns modeling/traffic/corridor.py; phase A)
YOUR TASK: Fit a time-of-day / day-of-week model on the WSDOT travel-time history log for the
SeaTac<->Anacortes corridor; predict a future-departure ETA with a prediction interval. If history is
thin, fall back to a labeled synthetic-bootstrap baseline (clearly flagged, never presented as
measured).
DELIVERABLES: `modeling/traffic/corridor.py`. Exports `predict_eta(depart_dt)` -> {eta, interval, basis}.
VALIDATION: pytest on a recorded history fixture; the model beats a flat-mean baseline on held-out days.
COLLISION-AVOIDANCE: own ONLY `modeling/traffic/`.
RETURN: diff + pytest output + the held-out skill number.

## Agent C — Kayak Branch (owns web/app/components/console/KayakPanel.tsx; phase A)
YOUR TASK: A console panel for the kayak branch: launch points, tide / current windows (reuse the
existing tide/current model surface), short-range viewing zones, safety framing. Camera stays low and
water-hugging (call the Camera Director orbit at small radius).
DELIVERABLES: `web/app/components/console/KayakPanel.tsx`.
VALIDATION: type-check; renders from a sample kayak-branch ui_intent.
COLLISION-AVOIDANCE: do not edit `ActiveSurfaceHost.tsx` (the planner-branch agent registers panels).
RETURN: diff + inspected screenshot.

## Agent D — Sidequests + Auth Chip (owns web/app/components/console/SidequestPanel.tsx; phase A)
YOUR TASK: Curiosity-branch pairing prompts (listen to a hydrophone, replay a recent sighting, explain
a cell score) that each end by inviting the user into the trip platform. Plus a single inline confirm
chip that authorizes a charter / wave from within the chat slot without leaving the scene.
DELIVERABLES: `web/app/components/console/SidequestPanel.tsx` (+ the confirm chip).
VALIDATION: type-check; renders sidequests; the chip emits an auth action on the turn.
COLLISION-AVOIDANCE: do not edit `ActiveSurfaceHost.tsx` or `planner.py`.
RETURN: diff + inspected screenshot.

## Agent E — Trips Planner Branch (owns src/aws_backend/casting/planner.py; phase B; single editor)
YOUR TASK: Add the orienting question (visiting / here-now / kayak / curious) and branch the skill plan
+ panels accordingly: compare-places (broad), local-area (focused), kayak, sidequest. Register the new
panels in `ActiveSurfaceHost`. Wire the Connections Planner into the visiting / here-now branches.
DELIVERABLES: edits to `planner.py` + panel registration in `ActiveSurfaceHost.tsx`.
VALIDATION: a real `/api/interactions/plan` turn for each branch returns a coherent panel set; the
visiting branch returns a connections plan with honesty labels. Read the responses.
COLLISION-AVOIDANCE: you are the ONLY W3 editor of `planner.py` and the panel registry; run after phase A.
RETURN: diff + the four branch responses you inspected.
