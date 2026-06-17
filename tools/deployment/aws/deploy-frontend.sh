#!/usr/bin/env bash
# Sync Angular build to S3 + invalidate CloudFront (no backend redeploy).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

MANIFEST="$ROOT/infra/aws/state/deployment-manifest.json"
if [ ! -f "$MANIFEST" ]; then
  echo "Missing $MANIFEST — run full deploy first."
  exit 1
fi

AWS_REGION="$(python3 -c "import json; print(json.load(open('$MANIFEST'))['region'])")"
FRONTEND_BUCKET="$(python3 -c "import json; print(json.load(open('$MANIFEST'))['frontend_bucket'])")"
DISTRIBUTION_ID="$(python3 -c "import json; print(json.load(open('$MANIFEST'))['distribution_id'])")"
CLOUDFRONT_URL="$(python3 -c "import json; print(json.load(open('$MANIFEST'))['cloudfront_url'])")"

bash scripts/inject-backend-url.sh

cd orcast-angular
npm ci
npm run build -- --configuration=aws
cd "$ROOT"

aws s3 sync orcast-angular/dist/orcast-angular "s3://$FRONTEND_BUCKET" --delete --region "$AWS_REGION"
aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths '/*' --region "$AWS_REGION" >/dev/null

echo "Frontend deployed to $CLOUDFRONT_URL"
