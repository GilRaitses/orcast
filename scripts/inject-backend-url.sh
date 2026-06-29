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
import re
from datetime import datetime, timezone
from pathlib import Path

root = Path(".")
manifest = json.loads((root / "infra/aws/state/deployment-manifest.json").read_text())
handoff = root / "HANDOFF_STATUS.md"

url_lines = {
    "BACKEND_URL": manifest["backend_url"],
    "CLOUDFRONT_URL": manifest["cloudfront_url"],
    "FRONTEND_BUCKET": manifest["frontend_bucket"],
    "DISTRIBUTION_ID": manifest.get("distribution_id", ""),
    "AWS_REGION": manifest["region"],
}

stamp = manifest.get("backed_up_at") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

if not handoff.exists():
    body = (
        "# orcast AWS handoff — coordination status\n\n"
        f"**Last updated:** {stamp}\n\n"
        "## Live URLs\n\n```\n"
        + "\n".join(f"{k}={v}" for k, v in url_lines.items())
        + "\n```\n\n"
        "Run `bash scripts/inject-backend-url.sh` before any production Angular build.\n"
    )
    handoff.write_text(body)
    print("Created HANDOFF_STATUS.md with Live URLs block")
else:
    text = handoff.read_text()
    if "**Last updated:**" in text:
        text = re.sub(r"\*\*Last updated:\*\* [^\n]+", f"**Last updated:** {stamp}", text, count=1)
    else:
        text = re.sub(r"(# [^\n]+\n)", rf"\1\n**Last updated:** {stamp}\n", text, count=1)

    if "## Live URLs" in text and "```" in text:
        def replace_url_block(match: re.Match[str]) -> str:
            block = match.group(0)
            for key, value in url_lines.items():
                if re.search(rf"^{key}=", block, flags=re.M):
                    block = re.sub(rf"^{key}=.*$", f"{key}={value}", block, flags=re.M)
                else:
                    block = block.rstrip("`").rstrip("\n") + f"\n{key}={value}\n```"
            return block

        text = re.sub(r"## Live URLs\n\n```[\s\S]*?```", replace_url_block, text, count=1)
    else:
        insert = (
            "\n## Live URLs\n\n```\n"
            + "\n".join(f"{k}={v}" for k, v in url_lines.items())
            + "\n```\n"
        )
        text = text.rstrip() + insert

    handoff.write_text(text if text.endswith("\n") else text + "\n")
    print("Patched Live URLs in HANDOFF_STATUS.md (preserved other sections)")
PY
fi
