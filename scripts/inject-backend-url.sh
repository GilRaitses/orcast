#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MANIFEST="$ROOT/infra/aws/state/deployment-manifest.json"

if [ -n "${1:-}" ]; then
  BACKEND_URL="${1%/}"
elif [ -f "$MANIFEST" ]; then
  BACKEND_URL="$(python3 -c "import json; print(json.load(open('$MANIFEST'))['backend_url'].rstrip('/'))")"
else
  echo "Usage: $0 [backend-url]"
  echo "  With no argument, reads backend_url from $MANIFEST"
  exit 1
fi

inject_apprunner() {
  local file="$1"
  sed -i.bak "s|https://BACKEND_URL_PLACEHOLDER|${BACKEND_URL}|g" "$file"
  sed -i.bak -E "s|https://[a-z0-9]+\.us-west-2\.awsapprunner\.com|${BACKEND_URL}|g" "$file"
  rm -f "${file}.bak"
}

inject_local() {
  local file="$1"
  sed -i.bak "s|apiBaseUrl: '[^']*'|apiBaseUrl: '${BACKEND_URL}'|g" "$file"
  rm -f "${file}.bak"
}

if [[ "$BACKEND_URL" == http://127.0.0.1:* ]] || [[ "$BACKEND_URL" == http://localhost:* ]]; then
  inject_local orcast-angular/src/environments/environment.ts
  echo "Injected local BACKEND_URL=${BACKEND_URL} into environment.ts only"
  exit 0
fi

for file in orcast-angular/src/environments/environment.aws.ts \
            orcast-angular/src/environments/environment.firebase.ts \
            orcast-angular/src/environments/environment.prod.ts; do
  inject_apprunner "$file"
done

inject_apprunner wrangler.toml

echo "Injected BACKEND_URL=${BACKEND_URL} into production environment files and wrangler.toml"

if [ -f "$MANIFEST" ]; then
  python3 <<'PY'
import json
from pathlib import Path

root = Path(".")
manifest = json.loads((root / "infra/aws/state/deployment-manifest.json").read_text())
handoff = root / "HANDOFF_STATUS.md"
text = handoff.read_text()
lines = [
    "# ORCAST AWS Handoff — Coordination Status",
    "",
    f"**Last updated:** {manifest.get('backed_up_at', 'auto')}",
    "",
    "## Live URLs",
    "",
    "```",
    f"BACKEND_URL={manifest['backend_url']}",
    f"CLOUDFRONT_URL={manifest['cloudfront_url']}",
    f"FRONTEND_BUCKET={manifest['frontend_bucket']}",
    f"DISTRIBUTION_ID={manifest.get('distribution_id', '')}",
    f"AWS_REGION={manifest['region']}",
    "```",
    "",
    "Run `bash scripts/inject-backend-url.sh` before any production build.",
]
if "## Stream status" in text:
    lines.append("")
    lines.append(text[text.index("## Stream status"):])
else:
    lines.extend([
        "",
        "## Verification",
        "",
        "- `python3 tools/testing/test_aws_backend_smoke.py --base-url <BACKEND_URL>`",
        "- CloudFront `/reports` generates a probability report",
    ])
handoff.write_text("\n".join(lines) + "\n")
print("Updated HANDOFF_STATUS.md from deployment manifest")
PY
fi
