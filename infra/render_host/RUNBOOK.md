# orcast render host — reliable headless rendering of the 3D twin

Local dev servers are unreliable for verifying the Salish Sea twin / orca / water
work. This runbook + `render.sh` give every build subagent a **reliable** way to
render a route and get a real PNG back to look at.

## The channel (why it's reliable)
- **Host:** `aimez-services` EC2 (`i-04a649f91274e9fce`, us-east-1) — x86_64, 4 vCPU,
  node 20, Playwright + chromium-1228 + ffmpeg already installed, Docker present.
- **Control:** AWS **SSM** `send-command` (no SSH key, no port 22). Observed solid
  while SSH port 22 intermittently times out from the operator's network.
- **Artifacts:** **S3** via the host instance role (`aimez-host-role`), which can
  write `s3://198456344617-us-west-2-orcast-aws-backend-reports/render-host/*`.
  aws CLI is not installed natively on the host, so S3 calls run through the
  `amazon/aws-cli` Docker image (the same pattern the 3D-twin pipeline uses).
- **GPU:** the host is **CPU-only** → headless WebGL runs on **SwiftShader**
  (software GL). Good for CORRECTNESS frames (is the water green, is the orca
  countershaded, are there console/page errors). It is **not** a client perf
  measurement — `U` (cost of one full scene render) must be measured on real
  client-tier GPUs, not here. The dedicated `aimez-gpu-capture` (T4) box would be
  ideal but is not currently reachable with the operator's keys.

## Use it
```bash
# sync the working tree (incl. uncommitted edits), render a route, pull the PNG:
infra/render_host/render.sh /orca
infra/render_host/render.sh /water 12000     # heavier route -> longer settle

# render only, code already synced this session:
infra/render_host/render.sh --no-sync /orca
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
