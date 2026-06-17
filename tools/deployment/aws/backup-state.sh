#!/usr/bin/env bash
# Save ORCAST AWS deployment state for safe teardown and redeploy.
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-west-2}"
STACK_NAME="${STACK_NAME:-orcast-aws-backend}"
STATE_DIR="${STATE_DIR:-infra/aws/state}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="$STATE_DIR/backups/$TIMESTAMP"

mkdir -p "$BACKUP_DIR" "$STATE_DIR"

if aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$STACK_NAME" >/dev/null 2>&1; then
  aws cloudformation describe-stacks \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    --output json > "$BACKUP_DIR/stack.json"

  aws cloudformation describe-stack-resources \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    --output json > "$BACKUP_DIR/stack-resources.json"

  aws cloudformation get-template \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    --template-stage Processed \
    --output json > "$BACKUP_DIR/processed-template.json" 2>/dev/null \
    || cp infra/aws/template.yaml "$BACKUP_DIR/template.yaml"
else
  echo "Stack $STACK_NAME not found in $AWS_REGION — saving repo template only." >&2
  cp infra/aws/template.yaml "$BACKUP_DIR/template.yaml"
fi

cp infra/aws/template.yaml "$BACKUP_DIR/template.yaml"

# Snapshot Angular environment files if they contain a real backend URL.
for env_file in orcast-angular/src/environments/environment.*.ts; do
  [ -f "$env_file" ] && cp "$env_file" "$BACKUP_DIR/$(basename "$env_file")"
done

[ -f wrangler.toml ] && cp wrangler.toml "$BACKUP_DIR/wrangler.toml"

MANIFEST="$STATE_DIR/deployment-manifest.json"
if aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$STACK_NAME" >/dev/null 2>&1; then
  BACKEND_HOST=$(aws cloudformation describe-stacks \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='BackendUrl'].OutputValue" \
    --output text 2>/dev/null || echo "")
  FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" \
    --output text 2>/dev/null || echo "")
  DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendDistributionId'].OutputValue" \
    --output text 2>/dev/null || echo "")
  CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
    --region "$AWS_REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendDistributionDomainName'].OutputValue" \
    --output text 2>/dev/null || echo "")
  BACKEND_URL=""
  [ -n "$BACKEND_HOST" ] && BACKEND_URL="https://${BACKEND_HOST}"
else
  BACKEND_URL=""
  FRONTEND_BUCKET=""
  DISTRIBUTION_ID=""
  CLOUDFRONT_URL=""
fi

IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo unknown)}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
ECR_REPO="${ECR_REPO:-orcast-aws-backend}"
IMAGE_URI=""
[ -n "$ACCOUNT_ID" ] && IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG"

cat > "$MANIFEST" <<EOF
{
  "stack_name": "$STACK_NAME",
  "region": "$AWS_REGION",
  "backend_url": "$BACKEND_URL",
  "cloudfront_url": "${CLOUDFRONT_URL:+https://$CLOUDFRONT_URL}",
  "frontend_bucket": "$FRONTEND_BUCKET",
  "distribution_id": "$DISTRIBUTION_ID",
  "image_uri": "$IMAGE_URI",
  "image_tag": "$IMAGE_TAG",
  "ecr_repo": "$ECR_REPO",
  "backed_up_at": "$TIMESTAMP",
  "backup_dir": "$BACKUP_DIR"
}
EOF

cp "$MANIFEST" "$BACKUP_DIR/deployment-manifest.json"
echo "Backup saved: $BACKUP_DIR"
echo "Manifest: $MANIFEST"
