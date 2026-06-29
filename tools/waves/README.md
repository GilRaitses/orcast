# Wave gates

Executable verification between probe and implement waves. Canonical definitions: [docs/devpost/WAVES_REGISTRY.md](../../docs/devpost/WAVES_REGISTRY.md).

## Usage

From repo root:

```bash
chmod +x tools/waves/run-gate.sh tools/waves/gates/*.sh
./tools/waves/run-gate.sh H0
./tools/waves/run-gate.sh P1-gate
./tools/waves/run-gate.sh I-suite
./tools/waves/run-gate.sh AT-4
./tools/waves/run-gate.sh R-echo
```

## Script mapping

| Wave ID | Scripts | What it checks |
|---------|---------|----------------|
| `H0` | `gates/h0-hackathon.sh` | `agent_smoke --dry-run`, sighting-assist, health, public gates, optional partner 200 |
| `P1-gate` | `p1-doc-grep.sh`, `p1-prod-curl.sh` | Stale copy / ghost endpoints; prod HTTP smoke |
| `I-suite` | `i-suite.sh` | `pytest tests/aws_backend/` + `modeling/tests/` |
| `AT-1` | `at-1.sh` | Read/auth/forecast endpoint tests |
| `AT-4` | `at-smoke.sh`, `angular-build.sh` | App Runner smoke + `ng build --configuration=aws` |
| `R-echo` | `r-echo.sh` | I-suite + H0 + P1 prod curl |
| `m` | `m-local.sh`, `m-doc-grep.sh` | Casting pytest + doc grep |
| `m-gate` | `m-prod-smoke.sh` | Prod interactions by agent_id + explore regression |
| `a-gate` | `a-gate.sh` | Full stack: docs + maps + agent_smoke + screenshots + webm |
| `a-maps` | `a-maps-smoke.sh` | Google Maps render on `/`, `/explore`, `/ask` |
| `a-video-gate` | `a-video-gate.sh` | Records `demo-walkthrough.webm` (≥120s) |
| `a-grounding` | `a-grounding.sh` | Grounding benchmark: orcast uncited rate < Maps 85% baseline. GEMINI_API_KEY optional (skips Maps refresh if absent); ORCAST_AGENT_KEY required. |

## Environment

| Variable | Default |
|----------|---------|
| `ORCAST_WEB_BASE` | `https://orcast-h0.vercel.app` |
| `ORCAST_BACKEND_URL` | `https://pjrftm3bkv.us-west-2.awsapprunner.com` |
| `ORCAST_CLOUDFRONT_URL` | `https://d2gslju5drx74c.cloudfront.net` |
| `ORCAST_PARTNER_DEV_KEY` | unset — partner 200 checks skipped if empty |

`agent_smoke` may read `.agent-credentials.env` at repo root for `ORCAST_AGENT_KEY`.

## Parent agent rule

Subagents run probes; **only the parent** runs `run-gate.sh` between waves.
