#!/usr/bin/env bash
# Set ORCAST_API_KEY on the live CloudFormation stack (App Runner + Lambda schedulers).
# Stack-only update — no Docker rebuild unless template changes require it.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

AWS_REGION="${AWS_REGION:-us-west-2}"
STACK_NAME="${STACK_NAME:-orcast-aws-backend}"

if [ -z "${ORCAST_API_KEY:-}" ]; then
  ORCAST_API_KEY="$(openssl rand -hex 32)"
  echo "Generated new ORCAST_API_KEY (save this — not printed again after deploy):"
  echo "$ORCAST_API_KEY"
  echo ""
  echo "Store in GitHub: gh secret set ORCAST_API_KEY"
fi

CONTAINER_IMAGE=$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Parameters[?ParameterKey=='ContainerImage'].ParameterValue" \
  --output text)

CORS_ORIGINS=$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Parameters[?ParameterKey=='CorsOrigins'].ParameterValue" \
  --output text)

ENABLE_INAT=$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Parameters[?ParameterKey=='EnableLiveINaturalist'].ParameterValue" \
  --output text)

ENABLE_ORCA=$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Parameters[?ParameterKey=='EnableOrcaHello'].ParameterValue" \
  --output text)

echo "Updating stack $STACK_NAME with ApiKey (App Runner will restart)..."
aws cloudformation deploy \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --template-file infra/aws/template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ServiceName=orcast-aws-backend \
    ContainerImage="$CONTAINER_IMAGE" \
    EnableLiveINaturalist="${ENABLE_INAT:-false}" \
    EnableOrcaHello="${ENABLE_ORCA:-true}" \
    CorsOrigins="$CORS_ORIGINS" \
    ApiKey="$ORCAST_API_KEY"

BACKEND_URL=$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='BackendUrl'].OutputValue" \
  --output text)

echo "ApiKey applied. Backend: https://${BACKEND_URL}"
echo "Verify: POST /api/sightings/ingest without X-ORCAST-Key should return 401."
