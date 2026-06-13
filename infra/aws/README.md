# ORCAST AWS Backend Deployment

This directory contains the first AWS-native deployment path for ORCAST. The backend runs as a FastAPI container and stores sightings, hotspots, ingestion runs, and probability reports in AWS services.

## Services created

- AWS App Runner service for `src.aws_backend.main:app`
- DynamoDB tables:
  - sightings
  - hotspots
  - reports
  - ingestion runs
- S3 buckets:
  - probability report JSON exports
  - raw source payload snapshots
- IAM roles for App Runner image pull and runtime data access

## Local run

```bash
python3 -m pip install --user fastapi uvicorn boto3 requests
ORCAST_STORAGE_BACKEND=memory ORCAST_ENV=local python3 -m uvicorn src.aws_backend.main:app --host 0.0.0.0 --port 8080
```

Smoke test:

```bash
curl http://localhost:8080/health
curl http://localhost:8080/api/sightings
curl http://localhost:8080/api/hotspots
curl -X POST http://localhost:8080/api/reports/probability -H 'Content-Type: application/json' -d '{"min_confidence":0}'
```

## Build and push image

Set these variables for your AWS account:

```bash
export AWS_REGION=us-west-2
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REPO=orcast-aws-backend
export IMAGE_TAG=$(git rev-parse --short HEAD)
```

Create the ECR repository if needed:

```bash
aws ecr describe-repositories --repository-names "$ECR_REPO" --region "$AWS_REGION" >/dev/null 2>&1 \
  || aws ecr create-repository --repository-name "$ECR_REPO" --region "$AWS_REGION"
```

Build and push:

```bash
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

docker build -f tools/deployment/aws/Dockerfile -t "$ECR_REPO:$IMAGE_TAG" .
docker tag "$ECR_REPO:$IMAGE_TAG" "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG"
docker push "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG"
```

## Deploy CloudFormation

```bash
aws cloudformation deploy \
  --stack-name orcast-aws-backend \
  --template-file infra/aws/template.yaml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ServiceName=orcast-aws-backend \
    ContainerImage="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:$IMAGE_TAG" \
    EnableLiveINaturalist=false \
    EnableOrcaHello=true
```

Get the backend URL:

```bash
aws cloudformation describe-stacks \
  --stack-name orcast-aws-backend \
  --query "Stacks[0].Outputs[?OutputKey=='BackendUrl'].OutputValue" \
  --output text
```

Set `orcast-angular/src/environments/environment.prod.ts` `apiBaseUrl` to the App Runner URL before building the production frontend.

## Runtime configuration

The backend reads these environment variables:

- `ORCAST_STORAGE_BACKEND`: `memory` or `aws`
- `AWS_REGION`
- `ORCAST_SIGHTINGS_TABLE`
- `ORCAST_HOTSPOTS_TABLE`
- `ORCAST_REPORTS_TABLE`
- `ORCAST_INGESTION_RUNS_TABLE`
- `ORCAST_REPORTS_BUCKET`
- `ORCAST_RAW_PAYLOAD_BUCKET`
- `ORCAST_ENABLE_LIVE_INATURALIST`
- `ORCAST_ENABLE_LIVE_NOAA`
- `ORCAST_ENABLE_ORCAHELLO`
- `ORCAST_CORS_ORIGINS`

## Notes

- The local backend starts with the verified OBIS snapshot so it can generate hotspots and reports without AWS credentials.
- The OrcaHello adapter rejects non-JSON responses. This prevents HTML status pages from being treated as sightings.
- The first probability model is deterministic and transparent. It can be replaced by trained model artifacts after the AWS storage path is stable.

