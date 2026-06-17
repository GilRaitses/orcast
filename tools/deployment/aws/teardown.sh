#!/usr/bin/env bash
# Safely tear down ORCAST AWS stack: backup state, empty S3, delete CloudFormation.
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-west-2}"
export AWS_REGION
STACK_NAME="${STACK_NAME:-orcast-aws-backend}"
KEEP_ECR="${KEEP_ECR:-false}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$REPO_ROOT"

echo "==> Backing up deployment state before teardown"
bash "$SCRIPT_DIR/backup-state.sh"

if ! aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$STACK_NAME" >/dev/null 2>&1; then
  echo "Stack $STACK_NAME not found in $AWS_REGION — nothing to delete."
  exit 0
fi

echo "==> Emptying S3 buckets"
BUCKETS=$(aws cloudformation describe-stack-resources \
  --region "$AWS_REGION" \
  --stack-name "$STACK_NAME" \
  --query 'StackResources[?ResourceType==`AWS::S3::Bucket`].PhysicalResourceId' \
  --output text)

for bucket in $BUCKETS; do
  echo "  Emptying s3://$bucket"
  aws s3 rm "s3://$bucket" --recursive --region "$AWS_REGION" 2>/dev/null || true
done

echo "==> Deleting CloudFormation stack $STACK_NAME"
aws cloudformation delete-stack --region "$AWS_REGION" --stack-name "$STACK_NAME"
aws cloudformation wait stack-delete-complete --region "$AWS_REGION" --stack-name "$STACK_NAME"
echo "Stack deleted."

if [ "$KEEP_ECR" != "true" ]; then
  ECR_REPO="${ECR_REPO:-orcast-aws-backend}"
  echo "==> Deleting ECR repository $ECR_REPO"
  aws ecr delete-repository --region "$AWS_REGION" --repository-name "$ECR_REPO" --force 2>/dev/null \
    || echo "ECR repo already removed or not found."
fi

cat > infra/aws/state/deployment-manifest.json <<EOF
{
  "stack_name": "$STACK_NAME",
  "region": "$AWS_REGION",
  "status": "teardown_complete",
  "teardown_at": "$(date -u +%Y%m%dT%H%M%SZ)"
}
EOF

echo ""
echo "Teardown complete. Redeploy with:"
echo "  bash tools/deployment/aws/deploy.sh"
