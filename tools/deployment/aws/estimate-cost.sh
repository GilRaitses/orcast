#!/usr/bin/env bash
# Print monthly cost estimate for the ORCAST AWS stack (us-west-2 defaults).
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-west-2}"
STACK_NAME="${STACK_NAME:-orcast-aws-backend}"

HOURS_MONTH=730
VCPU=1
MEMORY_GB=2
VCPU_RATE=0.064
MEMORY_RATE=0.007
APPRUNNER_HOURLY=$(python3 -c "print(round($VCPU * $VCPU_RATE + $MEMORY_GB * $MEMORY_RATE, 4))")
APPRUNNER_MONTHLY=$(python3 -c "print(round($APPRUNNER_HOURLY * $HOURS_MONTH, 2))")

STACK_EXISTS=false
if aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$STACK_NAME" >/dev/null 2>&1; then
  STACK_EXISTS=true
  STATUS=$(aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$STACK_NAME" \
    --query 'Stacks[0].StackStatus' --output text)
else
  STATUS="NOT_DEPLOYED"
fi

# Try live cost data from Cost Explorer (last 7 days) if available.
LIVE_COST=""
if aws ce get-cost-and-usage \
  --time-period Start="$(date -u -v-7d +%Y-%m-%d 2>/dev/null || date -u -d '7 days ago' +%Y-%m-%d)",End="$(date -u +%Y-%m-%d)" \
  --granularity MONTHLY \
  --metrics UnblendedCost \
  --filter "{\"Tags\":{\"Key\":\"aws:cloudformation:stack-name\",\"Values\":[\"$STACK_NAME\"]}}" \
  --query 'ResultsByTime[0].Total.UnblendedCost.Amount' \
  --output text 2>/dev/null; then
  LIVE_COST=$(aws ce get-cost-and-usage \
    --time-period Start="$(date -u -v-7d +%Y-%m-%d 2>/dev/null || date -u -d '7 days ago' +%Y-%m-%d)",End="$(date -u +%Y-%m-%d)" \
    --granularity MONTHLY \
    --metrics UnblendedCost \
    --query 'ResultsByTime[-1].Total.UnblendedCost.Amount' \
    --output text 2>/dev/null || echo "")
fi

cat <<EOF
ORCAST AWS monthly cost estimate (region: $AWS_REGION)
Stack: $STACK_NAME — status: $STATUS

FIXED (always-on App Runner: ${VCPU} vCPU, ${MEMORY_GB} GB RAM)
  ~\$${APPRUNNER_HOURLY}/hour  →  ~\$${APPRUNNER_MONTHLY}/month  (largest line item)

VARIABLE (low-traffic demo / dev)
  DynamoDB on-demand (4 tables)     ~\$1–5/month
  S3 (reports + payloads + frontend)  ~\$0.50–2/month
  CloudFront (static frontend)        ~\$1–10/month (traffic-dependent)
  Lambda schedulers (2 functions)     ~\$0.50–2/month
  ECR image storage                   ~\$0.10–1/month
  EventBridge rules                   usually free tier

ESTIMATED TOTAL (idle / low traffic): ~\$$(python3 -c "print(int($APPRUNNER_MONTHLY + 15))")–\$$(python3 -c "print(int($APPRUNNER_MONTHLY + 25))")/month

To reduce cost:
  - Run teardown when not demoing:  bash tools/deployment/aws/teardown.sh
  - Redeploy when needed:           bash tools/deployment/aws/deploy.sh
  - Disable schedulers in template (EventBridge rules) if ingestion can be manual

Actual billing: https://console.aws.amazon.com/cost-management/home
EOF

if [ -n "$LIVE_COST" ] && [ "$LIVE_COST" != "None" ] && [ "$LIVE_COST" != "0" ]; then
  echo ""
  echo "Recent AWS account cost (last period in Cost Explorer): \$${LIVE_COST}"
fi

if [ "$STACK_EXISTS" = true ]; then
  BACKEND=$(aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='BackendUrl'].OutputValue" --output text 2>/dev/null || echo "")
  CLOUDFRONT=$(aws cloudformation describe-stacks --region "$AWS_REGION" --stack-name "$STACK_NAME" \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendDistributionDomainName'].OutputValue" --output text 2>/dev/null || echo "")
  echo ""
  echo "Live endpoints:"
  [ -n "$BACKEND" ] && echo "  Backend:    https://$BACKEND"
  [ -n "$CLOUDFRONT" ] && echo "  CloudFront: https://$CLOUDFRONT"
fi
