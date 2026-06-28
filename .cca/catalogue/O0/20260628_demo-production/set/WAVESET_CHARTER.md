# Stage 0, SET (stage readiness), waveset charter

Family DSET. Parent program: `../PROGRAM.md`. Beat set: `../BEAT_SET.md`.

## Intent

Stand up and verify every environment prerequisite the live beats need, so the downstream
beats clear instead of block. This is the set and stage crew before the camera rolls. No
capture, no evaluation, no approval here.

## Unit of parallelism

One First AD per prerequisite. Each stands the prerequisite up and verifies it with a
Read-examined runtime check (a real health body, a real authenticated session, a real
rendered pane). READY is never asserted from a launch command alone. Long-lived processes
(dev server, any detector service) are started and their ports and pids recorded.

## Prerequisites (one First AD each)

| id | Prerequisite | Serves beats | Read-examined check |
|---|---|---|---|
| SET-web | Capture target reachable: either the local `web/` dev server (`npm run dev`, port + pid recorded) or the prod alias `https://orcast-h0.vercel.app` | all | GET `/` 200 and the forecast hero rendered in the returned HTML |
| SET-maps | Google Maps usable on `/`, `/ask` (key present, tiles load) | A1, A4, A5 | the map canvas mounts and tiles paint on a Read-examined frame |
| SET-session | Reviewer/agent session: a working `X-ORCAST-Agent-Key` or WorkOS sign-in for journal, moderation, planner, reviewer console | A6, B1, B2 | an authenticated request returns 200 and a reviewer-only pane renders |
| SET-forecast | Live forecast + gates respond with the honest 0% promoted and integrity conditions | A1, A4 | `/gates` renders the integrity-conditions list and the real 0% value |
| SET-twin | Twin sandbox build state: W2.6 datum + W-PERFUX-BUILD framing present; the sandbox twin route renders land at the waterline | B3 | the twin scene renders and a Read-examined frame shows land meeting the waterline |

## Output

- `findings/SET-<prereq>.md` per prerequisite: READY / NOT READY, the exact runtime check
  Read-examined, ports/pids for long-lived processes, and for NOT READY the exact gap and
  operator-actionable fix.
- `READINESS.md` manifest: the full prerequisite table with status, the recorded
  ports/pids, and the capture target the director locked (local dev vs prod).

## Advance gate

The director confirms the manifest. A beat may enter BLK only when its prerequisites are
READY. A NOT READY prerequisite is an operator-actionable blocker with the gap and fix, not
a silent pass.

## Escalation

First AD to Director; Director resolves or escalates to O0. Operator gates (paid resource
start, prod credential) reach the human only through O0.
