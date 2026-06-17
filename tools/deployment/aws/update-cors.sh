#!/usr/bin/env bash
# Update App Runner CORS to include CloudFront origin (browser calls API directly).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

MANIFEST="$ROOT/infra/aws/state/deployment-manifest.json"
AWS_REGION="$(python3 -c "import json; print(json.load(open('$MANIFEST'))['region'])")"
STACK_NAME="$(python3 -c "import json; print(json.load(open('$MANIFEST'))['stack_name'])")"
CLOUDFRONT_URL="$(python3 -c "import json; print(json.load(open('$MANIFEST'))['cloudfront_url'])")"
IMAGE_URI="$(python3 -c "import json; print(json.load(open('$MANIFEST'))['image_uri'])")"

CF_ORIGIN="${CLOUDFRONT_URL}"
CORS_ORIGINS="https://orca-904de.web.app,https://orcast.org,https://www.orcast.org,${CF_ORIGIN}"

aws cloudformation deploy \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --template-file infra/aws/template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ServiceName=orcast-aws-backend \
    ContainerImage="$IMAGE_URI" \
    EnableLiveINaturalist=false \
    EnableOrcaHello=true \
    CorsOrigins="$CORS_ORIGINS"

echo "CORS updated to include $CF_ORIGIN"
