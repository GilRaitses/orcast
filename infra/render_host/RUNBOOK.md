# orcast render host — reliable headless rendering of the 3D twin

Local dev servers are unreliable for verifying the Salish Sea twin / orca / water
work. This runbook + `render.sh` give every build subagent a **reliable** way to
render a route and get a real PNG back to look at.

## The channel (why it's reliable)
- **Targets (pick with `ORCAST_RENDER_TARGET`, default `gpu`):**
  - **gpu** — `aimez-gpu-capture` EC2 (`i-0e66ac03c729ebe02`, us-east-1) — **Tesla T4
    (15 GB), 15 GiB RAM**, node 20, Playwright chromium-1228, Docker, libEGL +
    libGLX_nvidia + Xvfb. Real GPU WebGL via ANGLE/EGL. Confirmed renderer string:
    `ANGLE (NVIDIA Corporation, Tesla T4/PCIe/SSE2, OpenGL ES 3.2)`.
  - **cpu** — `aimez-services` EC2 (`i-04a649f91274e9fce`) — 4 vCPU, 7.6 GiB, no GPU
    → **SwiftShader** software GL. Correctness-only fallback.
- **Control:** AWS **SSM** `send-command` (no SSH key, no port 22). Observed solid
  while SSH port 22 intermittently times out from the operator's network for BOTH
  boxes. The GPU box was off + had no instance profile; it was started, given the
  SSM-capable `aimez-host-profile`, and rebooted so its SSM agent registered.
- **Artifacts:** **S3** via the host instance role (`aimez-host-role`), which can
  write `s3://198456344617-us-west-2-orcast-aws-backend-reports/render-host/*`.
  aws CLI is not installed natively on either host, so S3 calls run through the
  `amazon/aws-cli` Docker image (the same pattern the 3D-twin pipeline uses).
- **Renderer confirmation:** every render reports `glRenderer` (the WebGL
  UNMASKED_RENDERER) so you can tell GPU (Tesla T4) from SwiftShader at a glance.
- **Perf caveat:** the T4 gives a REAL-GPU baseline, but it is a server-class GPU,
  not a client laptop tier. Treat `U` numbers from here as an upper-bound sanity
  check, not the binding client-tier budget.

## Use it
```bash
# default = GPU box (Tesla T4). sync working tree (incl. uncommitted), render, pull PNG:
infra/render_host/render.sh /orca
infra/render_host/render.sh /water 12000               # heavier route -> longer settle

# render only, code already synced this session:
infra/render_host/render.sh --no-sync /orca

# force the CPU/SwiftShader fallback box:
ORCAST_RENDER_TARGET=cpu infra/render_host/render.sh /orca
```
The frame lands in `.cca/catalogue/O0/20260628_render-host/proof/<route>_<time>.png`
and the script prints the render JSON: `canvas` present?, and the console/page
**errorCount** (catch runtime bugs the local flake hid — e.g. the `/water`
`reading 'value'` error this surfaced on first run).

## Verify (mandatory)
After rendering, **Read the PNG** and examine it (visual-verification rule).
Do not claim a fix you have not seen in a frame from this host.

## Flow under the hood
1. `tar web/` (minus node_modules/.next/video) → S3 `render-host/code/`.
2. SSM → host pulls + extracts (node_modules preserved), refreshes `render_route.mjs`.
3. SSM → ensure `npm ci` once, ensure `next dev` on :3010, run `render_route.mjs`.
4. host → S3 `render-host/shots/shot.png`; local pulls it into `proof/`.

## Notes
- First `npm ci` and first compile of a route are the slow steps; later renders are fast.
- The host also runs the pax cv/shade co-tenants and pax's own `next dev` on :3000 —
  orcast uses :3010 to stay clear.
- If SSH port 22 is up, `rsync -e "ssh -i ~/.ssh/pax-ec2-key.pem" web/ ubuntu@44.197.243.177:~/orcast/web/`
  is a faster code-sync, but `render.sh` does not depend on it.
