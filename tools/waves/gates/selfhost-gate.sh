#!/usr/bin/env bash
# GP Phase B live battery for the self-host cutover (network required).
# Edge reachability + TLS, proxy authz matrix, co-tenant non-interference, and
# SSH-SG world-open check. Read-only; AWS checks SKIP gracefully without creds.
set -uo pipefail
fail=0
note(){ printf "%-6s %s\n" "$1" "$2"; [ "$1" = FAIL ] && fail=1; return 0; }

API_HOST="${ORCAST_API_HOST:-orcast-api.aimez.ai}"
WEB="${ORCAST_WEB_BASE:-https://orcast-h0.vercel.app}"
IP="$(dig +short @1.1.1.1 "$API_HOST" 2>/dev/null | head -1)"
[ -n "$IP" ] && note PASS "DNS $API_HOST -> $IP" || { note FAIL "DNS $API_HOST unresolved"; }

edge(){ curl -s -o /dev/null -w "%{http_code}" --max-time 25 --resolve "$API_HOST:443:$IP" "https://$API_HOST/$1" 2>/dev/null; }
prox(){ curl -s -o /dev/null -w "%{http_code}" --max-time 25 "$WEB/api/be/$1" 2>/dev/null; }

# Edge matrix
[ "$(edge health)" = 200 ] && note PASS "edge /health 200" || note FAIL "edge /health"
[ "$(edge api/gates)" = 200 ] && note PASS "edge /api/gates 200" || note FAIL "edge /api/gates"
[ "$(edge api/evidence/assets)" = 401 ] && note PASS "edge keyed 401" || note FAIL "edge keyed not 401"

# Proxy authz matrix
[ "$(prox health)" = 200 ] && note PASS "proxy /health 200" || note FAIL "proxy /health"
for p in api/evidence/assets api/journal api/decision-records api/review-dossier; do
  [ "$(prox $p)" = 401 ] && note PASS "proxy $p 401" || note FAIL "proxy $p not 401"
done

# Co-tenant: pax untouched
[ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 https://cv.aimez.ai/health)" = 200 ] && note PASS "pax cv 200" || note FAIL "pax cv"
[ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 https://shade.aimez.ai/health)" = 200 ] && note PASS "pax shade 200" || note FAIL "pax shade"

# SSH SG must not be world-open (AWS optional)
if command -v aws >/dev/null 2>&1; then
  world="$(aws ec2 describe-security-groups --region us-east-1 --group-ids sg-08ad4456a152e4b27 --query "SecurityGroups[0].IpPermissions[?FromPort==\`22\`].IpRanges[?CidrIp=='0.0.0.0/0'].CidrIp" --output text 2>/dev/null)"
  [ -z "$world" ] && note PASS "SSH SG not world-open" || note FAIL "SSH SG 0.0.0.0/0 on port 22"
else
  note SKIP "aws cli absent; SSH SG check skipped"
fi

[ "$fail" = 0 ] && { echo "selfhost-gate: PASS"; exit 0; } || { echo "selfhost-gate: FAIL"; exit 1; }
