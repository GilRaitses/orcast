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

FIT_ECR_REPO="${FIT_ECR_REPO:-orcast-aws-fit}"

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG"
FIT_IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$FIT_ECR_REPO:$IMAGE_TAG"

apprunner_service_arn() {
  aws apprunner list-services --region "$AWS_REGION" \
    --query "ServiceSummaryList[?ServiceName=='$STACK_NAME'].ServiceArn | [0]" --output text
}

# ECR push triggers App Runner auto-deploy; CFN UPDATE_SERVICE races and fails unless idle.
wait_for_apprunner_idle() {
  local arn="$1"
  local max_wait="${2:-900}"
  local elapsed=0
  while [ "$elapsed" -lt "$max_wait" ]; do
    local status op_status
    status=$(aws apprunner list-services --region "$AWS_REGION" \
      --query "ServiceSummaryList[?ServiceArn=='$arn'].Status | [0]" --output text)
    op_status=$(aws apprunner list-operations --service-arn "$arn" --region "$AWS_REGION" \
      --query 'OperationSummaryList[0].Status' --output text 2>/dev/null || echo "SUCCEEDED")
    if [ "$status" = "RUNNING" ] && [[ "$op_status" != "IN_PROGRESS" && "$op_status" != "PENDING" && "$op_status" != "ROLLBACK_IN_PROGRESS" ]]; then
      return 0
    fi
    echo "Waiting for App Runner idle (service=$status, latest_op=$op_status)..."
    sleep 20
    elapsed=$((elapsed + 20))
  done
  echo "Timed out waiting for App Runner to become idle" >&2
  return 1
}

EXISTING_CF_DOMAIN=""
if aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$STACK_NAME" >/dev/null 2>&1; then
  EXISTING_CF_DOMAIN=$(aws cloudformation describe-stacks \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendDistributionDomainName'].OutputValue" \
    --output text 2>/dev/null || true)
fi
CORS_ORIGINS="https://orca-904de.web.app,https://orcast.org,https://www.orcast.org,https://orcast-h0.vercel.app"
if [ -n "$EXISTING_CF_DOMAIN" ] && [ "$EXISTING_CF_DOMAIN" != "None" ]; then
  CORS_ORIGINS="${CORS_ORIGINS},https://${EXISTING_CF_DOMAIN}"
fi

aws ecr describe-repositories --repository-names "$ECR_REPO" --region "$AWS_REGION" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "$ECR_REPO" --region "$AWS_REGION"
aws ecr describe-repositories --repository-names "$FIT_ECR_REPO" --region "$AWS_REGION" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "$FIT_ECR_REPO" --region "$AWS_REGION"

aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker build --platform linux/amd64 -f tools/deployment/aws/Dockerfile -t "$IMAGE_URI" .
docker push "$IMAGE_URI"

# Fit-stage container-image Lambda (carries scipy/statsmodels).
# Lambda rejects OCI attestation manifests; disable BuildKit attestations.
BUILDX_NO_DEFAULT_ATTESTATIONS=1 docker build --platform linux/amd64 -f tools/deployment/aws/Dockerfile.fit -t "$FIT_IMAGE_URI" .
docker push "$FIT_IMAGE_URI"

SERVICE_ARN="$(apprunner_service_arn)"
if [ -n "$SERVICE_ARN" ] && [ "$SERVICE_ARN" != "None" ]; then
  wait_for_apprunner_idle "$SERVICE_ARN"
fi

aws cloudformation deploy \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --template-file infra/aws/template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ServiceName=orcast-aws-backend \
    ContainerImage="$IMAGE_URI" \
    FitImage="$FIT_IMAGE_URI" \
    EnableLiveINaturalist=true \
    EnableOrcaHello=true \
    EnableBedrock="${ORCAST_ENABLE_BEDROCK:-true}" \
    EnableExplorationDatabase="${ORCAST_ENABLE_EXPLORATION_DATABASE:-false}" \
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

EXPLORATION_DB_HOST=$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='ExplorationDatabaseEndpoint'].OutputValue" \
  --output text 2>/dev/null || true)

if [ -n "$EXPLORATION_DB_HOST" ] && [ "$EXPLORATION_DB_HOST" != "None" ]; then
  echo "Exploration database endpoint: $EXPLORATION_DB_HOST"
  bash "$SCRIPT_DIR/sync-apprunner-explore-env.sh" || true
  SECRET_ARN=$(aws cloudformation describe-stacks \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='ExplorationDatabaseSecretArn'].OutputValue" \
    --output text 2>/dev/null || true)
  if [ -n "$SECRET_ARN" ] && [ "$SECRET_ARN" != "None" ]; then
    DB_PASS=$(aws secretsmanager get-secret-value --secret-id "$SECRET_ARN" --region "$AWS_REGION" \
      --query SecretString --output text | python3 -c "import json,sys; print(json.load(sys.stdin)['password'])")
    export PGPASSWORD="$DB_PASS"
    export EXPLORATION_DB_HOST
    export DB_PASS
    if command -v psql >/dev/null 2>&1; then
      if psql -h "$EXPLORATION_DB_HOST" -U orcast -d orcast_explore -c 'SELECT 1' >/dev/null 2>&1; then
        psql -h "$EXPLORATION_DB_HOST" -U orcast -d orcast_explore -f src/aws_backend/exploration/migrations/001_initial.sql
        psql -h "$EXPLORATION_DB_HOST" -U orcast -d orcast_explore -f src/aws_backend/exploration/migrations/002_retention.sql
        psql -h "$EXPLORATION_DB_HOST" -U orcast -d orcast_explore -f src/aws_backend/exploration/migrations/003_interaction_trace.sql
        psql -h "$EXPLORATION_DB_HOST" -U orcast -d orcast_explore -f src/aws_backend/exploration/migrations/004_interaction_steps.sql
      else
        echo "Skipping external migrations (RDS not reachable from deploy host; App Runner applies on startup)"
      fi
    else
      python3 - <<PY || echo "Skipping external migrations (Python fallback failed; App Runner applies on startup)"
import os, psycopg
host = os.environ["EXPLORATION_DB_HOST"]
password = os.environ["DB_PASS"]
for path in (
    "src/aws_backend/exploration/migrations/001_initial.sql",
    "src/aws_backend/exploration/migrations/002_retention.sql",
    "src/aws_backend/exploration/migrations/003_interaction_trace.sql",
    "src/aws_backend/exploration/migrations/004_interaction_steps.sql",
):
    sql = open(path).read()
    with psycopg.connect(
        host=host,
        port=5432,
        dbname="orcast_explore",
        user="orcast",
        password=password,
        connect_timeout=10,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
    print("Applied", path)
PY
    fi
  fi
fi

MANAGED_AGENTS_TABLE=$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='ManagedAgentsTableName'].OutputValue" \
  --output text 2>/dev/null || true)
if [ -n "$MANAGED_AGENTS_TABLE" ] && [ "$MANAGED_AGENTS_TABLE" != "None" ]; then
  echo "Seeding Central Casting agent in $MANAGED_AGENTS_TABLE"
  ORCAST_MANAGED_AGENTS_TABLE="$MANAGED_AGENTS_TABLE" PYTHONPATH="$REPO_ROOT" \
    python3 "$SCRIPT_DIR/seed_managed_agent.py" --table "$MANAGED_AGENTS_TABLE" --all || true
fi

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
