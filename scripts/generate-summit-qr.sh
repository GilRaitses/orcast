#!/usr/bin/env bash
# Generate QR code PNGs for summit booth URLs (requires qrcode: pip install qrcode[pil]).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/docs/field-campaign/qr"
mkdir -p "$OUT"

MANIFEST="$ROOT/infra/aws/state/deployment-manifest.json"
CF_URL="$(python3 -c "import json; print(json.load(open('$MANIFEST'))['cloudfront_url'])")"

python3 - <<PY
from pathlib import Path

try:
    import qrcode
except ImportError:
    print("Install: pip install 'qrcode[pil]'")
    raise SystemExit(1)

urls = {
    "cloudfront-landing": "${CF_URL}/",
    "cloudfront-reports": "${CF_URL}/reports",
    "orcast-org-landing": "https://orcast.org/",
    "orcast-org-partners": "https://orcast.org/partners",
}

out = Path("$OUT")
for name, url in urls.items():
    img = qrcode.make(url)
    path = out / f"{name}.png"
    img.save(path)
    print(f"Wrote {path} -> {url}")
PY

echo "QR codes saved to $OUT"
