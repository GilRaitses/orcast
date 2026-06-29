#!/usr/bin/env bash
# Sync App Runner VPC egress + discrete DB env vars after CFN (ECR auto-deploy can leave stale config).
set -euo pipefail

REGION="${AWS_REGION:-us-west-2}"
STACK="${STACK_NAME:-orcast-aws-backend}"
SERVICE="${SERVICE_NAME:-orcast-aws-backend}"

python3 <<PY
import json, subprocess, sys

region = "${REGION}"
stack = "${STACK}"
service_name = "${SERVICE}"

def sh(*args):
    return subprocess.check_output(list(args), text=True).strip()

def cf_output(key):
    return sh(
        "aws", "cloudformation", "describe-stacks",
        "--stack-name", stack, "--region", region,
        "--query", f"Stacks[0].Outputs[?OutputKey=='{key}'].OutputValue | [0]",
        "--output", "text",
    )

host = cf_output("ExplorationDatabaseEndpoint")
if not host or host == "None":
    print("Exploration DB not enabled; skip App Runner sync")
    sys.exit(0)

secret_arn = cf_output("ExplorationDatabaseSecretArn")
secret_raw = sh(
    "aws", "secretsmanager", "get-secret-value",
    "--secret-id", secret_arn, "--region", region,
    "--query", "SecretString", "--output", "text",
)
db_pass = json.loads(secret_raw)["password"]
svc_arn = sh(
    "aws", "apprunner", "list-services", "--region", region,
    "--query", f"ServiceSummaryList[?ServiceName=='{service_name}'].ServiceArn | [0]",
    "--output", "text",
)
vpc_arn = sh(
    "aws", "apprunner", "list-vpc-connectors", "--region", region,
    "--query", "VpcConnectors[0].VpcConnectorArn", "--output", "text",
)
raw = sh("aws", "apprunner", "describe-service", "--service-arn", svc_arn, "--region", region, "--output", "json")
svc = json.loads(raw)["Service"]
env = dict(svc["SourceConfiguration"]["ImageRepository"]["ImageConfiguration"]["RuntimeEnvironmentVariables"])
env.pop("ORCAST_DATABASE_URL", None)
env["ORCAST_DB_HOST"] = host
env["ORCAST_DB_USER"] = "orcast"
env["ORCAST_DB_NAME"] = "orcast_explore"
env["ORCAST_DB_PASSWORD"] = db_pass
image = svc["SourceConfiguration"]["ImageRepository"]["ImageIdentifier"]
payload = {
    "ServiceArn": svc_arn,
    "NetworkConfiguration": {
        "EgressConfiguration": {
            "EgressType": "VPC",
            "VpcConnectorArn": vpc_arn,
        }
    },
    "SourceConfiguration": {
        "ImageRepository": {
            "ImageIdentifier": image,
            "ImageRepositoryType": "ECR",
            "ImageConfiguration": {
                "Port": "8080",
                "RuntimeEnvironmentVariables": env,
            },
        },
        "AutoDeploymentsEnabled": True,
        "AuthenticationConfiguration": svc["SourceConfiguration"]["AuthenticationConfiguration"],
    },
}
with open("/tmp/apprunner-explore-sync.json", "w") as f:
    json.dump(payload, f)
subprocess.check_call([
    "aws", "apprunner", "update-service",
    "--region", region, "--cli-input-json", "file:///tmp/apprunner-explore-sync.json",
])
print("App Runner explore sync submitted")
PY
