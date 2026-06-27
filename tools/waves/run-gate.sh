#!/usr/bin/env bash
# Wave gate dispatcher — see tools/waves/README.md and docs/devpost/WAVES_REGISTRY.md
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
GATES="$ROOT/tools/waves/gates"

usage() {
  cat <<EOF
Usage: $0 <wave-id>

Wave IDs:
  H0          Hackathon automated (agent_smoke, sighting-assist, health, gates)
  P1-gate     Post-probe: doc grep + prod curls
  I-suite     pytest aws_backend + modeling
  AT-1        API truth wave 1 backend tests
  AT-4        Backend smoke + Angular aws build
  R-echo      Remediation prod verification (I-suite + H0 + P1 curl)
  e2          Exploration local gate (pytest + tsc)
  e-gate      Exploration prod smoke
  e-doc-grep  Exploration doc consistency
  f           F local gate (limits + explore tests)
  f-gate      F prod smoke + network check
  f-network   RDS public port check only
  g           G local gate (AI Gateway + auth tests)
  g-gate      G prod smoke + f-gate regression
  m           M local gate (Central Casting registry + interactions)
  m-gate      M prod smoke (interactions by agent_id)
  ic          IC local gate (interaction steps + manifest skills)
  ic-doc-grep IC doc consistency (IC0 synthesis + pattern + catalog)
  ic-gate     IC prod smoke (steps + annotations on App Runner)
  ic4         IC4 local gate (G5 remediation + ic regression)
  ic4-doc-grep IC4 doc consistency (API.md + gates UI)
  ic6         IC6 local gate (surface planner + panel registry)
  ic6-doc-grep IC6 doc consistency (UI intent schema + plan route)
  ic6-gate    IC6 prod smoke (keyed plan + ic-gate regression)
  s-doc-grep  Submission doc consistency
  s-gate      Submission gate (S4)
  a-doc-grep  Agent demo doc consistency
  a-maps      Google Maps smoke on H0 (/, /explore, /ask)
  a-video-gate  Record demo-walkthrough.webm (~3 min)
  a-gate      Agent demo automation + video-complete gate (A5)
  a-grounding Grounding benchmark: orcast uncited rate < Maps 85% baseline
  u-upload    Evidence upload adversarial tests (U5)
  u-account   Account content management tests (U5)
  v-beat      Verify all per-beat webms exist + duration check
  v-stitch    Concatenate beat webms → demo-final.webm via ffmpeg
  h1-demo     Agent-automation demo screenshots (needs .agent-credentials.env)
  selfhost-preflight  GP Phase A static preflight (secret scan + syntax + .ddb verify)
  selfhost-gate       GP Phase B live battery (edge/proxy authz + co-tenant + SSH SG)
  copy-gate           Prose gate: hard-fail em/en dash + arrows, report semicolons/colons/voice (.cca/PROSE_GATE_RULES.md)

Environment (optional):
  ORCAST_WEB_BASE, ORCAST_BACKEND_URL, ORCAST_CLOUDFRONT_URL
  ORCAST_PARTNER_DEV_KEY — enables partner 200 checks
EOF
}

if [ $# -lt 1 ]; then
  usage
  exit 1
fi

WAVE="$(echo "$1" | tr '[:upper:]' '[:lower:]')"

run() {
  local script="$1"
  if [ ! -x "$script" ]; then
    chmod +x "$script"
  fi
  bash "$script"
}

case "$WAVE" in
  h0)
    run "$GATES/h0-hackathon.sh"
    ;;
  p1-gate|p1)
    run "$GATES/p1-doc-grep.sh"
    run "$GATES/p1-prod-curl.sh"
    ;;
  i-suite|i)
    run "$GATES/i-suite.sh"
    ;;
  at-1)
    run "$GATES/at-1.sh"
    ;;
  at-4)
    run "$GATES/at-smoke.sh"
    run "$GATES/angular-build.sh"
    ;;
  r-echo|recho)
    run "$GATES/r-echo.sh"
    ;;
  e2)
    run "$GATES/e2-local.sh"
    ;;
  e-gate|egate)
    run "$GATES/e-prod-smoke.sh"
    ;;
  e-doc-grep|edoc)
    run "$GATES/e-doc-grep.sh"
    ;;
  f)
    run "$GATES/f-local.sh"
    ;;
  f-gate|fgate)
    run "$GATES/f-prod-smoke.sh"
    ;;
  f-network|fnetwork)
    run "$GATES/f-network-check.sh"
    ;;
  g)
    run "$GATES/g-local.sh"
    ;;
  g-gate|ggate)
    run "$GATES/g-prod-smoke.sh"
    ;;
  m)
    run "$GATES/m-local.sh"
    ;;
  m-gate|mgate)
    run "$GATES/m-prod-smoke.sh"
    ;;
  ic)
    run "$GATES/ic-local.sh"
    ;;
  ic-doc-grep|icdoc)
    run "$GATES/ic-doc-grep.sh"
    ;;
  ic-gate|icgate)
    run "$GATES/ic-prod-smoke.sh"
    ;;
  ic4|ic4-local)
    run "$GATES/ic4-local.sh"
    ;;
  ic4-doc-grep|ic4doc)
    run "$GATES/ic4-doc-grep.sh"
    ;;
  ic6|ic6-local)
    run "$GATES/ic6-local.sh"
    ;;
  ic6-doc-grep|ic6doc)
    run "$GATES/ic6-doc-grep.sh"
    ;;
  ic6-gate|ic6gate)
    run "$GATES/ic6-prod-smoke.sh"
    ;;
  s-doc-grep|sdoc)
    run "$GATES/s-doc-grep.sh"
    ;;
  s-gate|sgate)
    run "$GATES/s-doc-grep.sh"
    ;;
  a-doc-grep|adoc)
    run "$GATES/a-doc-grep.sh"
    ;;
  a-gate|agate)
    run "$GATES/a-gate.sh"
    ;;
  a-maps|amaps)
    run "$GATES/a-maps-smoke.sh"
    ;;
  a-video-gate|avideo)
    run "$GATES/a-video-gate.sh"
    ;;
  a-grounding|agrounding)
    run "$GATES/a-grounding.sh"
    ;;
  u-upload|uupload)
    run "$GATES/u-upload.sh"
    ;;
  u-account|uaccount)
    run "$GATES/u-account.sh"
    ;;
  v-beat|vbeat)
    run "$GATES/v-beat-check.sh"
    ;;
  v-stitch|vstitch)
    run "$GATES/v-stitch.sh"
    ;;
  h1-demo|h1demo)
    run "$GATES/h1-demo-walkthrough.sh"
    ;;
  selfhost-preflight|shpre)
    run "$GATES/selfhost-preflight.sh"
    ;;
  selfhost-gate|shgate)
    run "$GATES/selfhost-gate.sh"
    ;;
  copy-gate|prose-gate|copygate)
    run "$GATES/copy-gate.sh"
    ;;
  *)
    echo "Unknown wave id: $1"
    usage
    exit 1
    ;;
esac

echo ""
echo "Gate $1: ALL PASS"
