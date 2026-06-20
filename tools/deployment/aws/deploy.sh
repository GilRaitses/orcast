#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_REGION
ECR_REPO="${ECR_REPO:-orcast-aws-backend}"
STACK_NAME="${STACK_NAME:-orcast-aws-backend}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG"

EXISTING_CF_DOMAIN=""
if aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$STACK_NAME" >/dev/null 2>&1; then
  EXISTING_CF_DOMAIN=$(aws cloudformation describe-stacks \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendDistributionDomainName'].OutputValue" \
    --output text 2>/dev/null || true)
fi
CORS_ORIGINS="https://orca-904de.web.app,https://orcast.org,https://www.orcast.org"
if [ -n "$EXISTING_CF_DOMAIN" ] && [ "$EXISTING_CF_DOMAIN" != "None" ]; then
  CORS_ORIGINS="${CORS_ORIGINS},https://${EXISTING_CF_DOMAIN}"
fi

aws ecr describe-repositories --repository-names "$ECR_REPO" --region "$AWS_REGION" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "$ECR_REPO" --region "$AWS_REGION"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker build --platform linux/amd64 -f tools/deployment/aws/Dockerfile -t "$IMAGE_URI" .
docker push "$IMAGE_URI"

aws cloudformation deploy \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --template-file infra/aws/template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ServiceName=orcast-aws-backend \
    ContainerImage="$IMAGE_URI" \
    EnableLiveINaturalist=true \
    EnableOrcaHello=true \
    CorsOrigins="$CORS_ORIGINS" \
    ApiKey="${ORCAST_API_KEY:-}"

BACKEND_HOST=$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='BackendUrl'].OutputValue" \
  --output text)

BACKEND_URL="https://${BACKEND_HOST}"
FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
  --output text)
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendDistributionId'].OutputValue" \
  --output text)
CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendDistributionDomainName'].OutputValue" \
  --output text)

bash scripts/inject-backend-url.sh "$BACKEND_URL"

cd orcast-angular
npm ci
npm run build -- --configuration=aws
cd ..

aws s3 sync orcast-angular/dist/orcast-angular "s3://$FRONTEND_BUCKET" --delete --region "$AWS_REGION"
aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION_ID" --paths '/*' --region "$AWS_REGION"

if [ -f "$REPO_ROOT/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.venv/bin/activate"
elif [ ! -x "$(command -v requests)" ] 2>/dev/null; then
  python3 -m pip install --quiet --user requests 2>/dev/null || true
fi
python3 tools/testing/test_aws_backend_smoke.py --base-url "$BACKEND_URL"

bash "$SCRIPT_DIR/backup-state.sh"
bash "$SCRIPT_DIR/estimate-cost.sh"

cat <<EOF
Deploy complete.
BACKEND_URL=$BACKEND_URL
CLOUDFRONT_URL=https://$CLOUDFRONT_URL
FRONTEND_BUCKET=$FRONTEND_BUCKET
EOF
