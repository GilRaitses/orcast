#!/usr/bin/env bash
# Q1c — DynamoDB schema vs. ERD check
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$ROOT"

python3 - <<'EOF'
import boto3, sys

ddb = boto3.client("dynamodb", region_name="us-west-2")
expected_tables = [
    "orcast-aws-backend-sightings",
    "orcast-aws-backend-community-submissions",
    "orcast-aws-backend-decision-records",
    "orcast-aws-backend-user-journal",
    "orcast-aws-backend-hotspots",
    "orcast-aws-backend-reports",
    "orcast-aws-backend-ingestion-runs",
    "orcast-aws-backend-partner-api-keys",
    "orcast-aws-backend-managed-agents",
]

fail = 0
tables = ddb.list_tables()["TableNames"]

for t in expected_tables:
    if t in tables:
        print(f"PASS: {t}")
    else:
        print(f"FAIL: {t} MISSING from DynamoDB")
        fail = 1

# managed-agents: must have 4 cast roles
try:
    r = ddb.scan(TableName="orcast-aws-backend-managed-agents", Select="COUNT")
    count = r["Count"]
    if count >= 4:
        print(f"PASS: managed-agents count={count} (>=4 cast roles)")
    else:
        print(f"FAIL: managed-agents count={count} (expected >=4)")
        fail = 1
except Exception as e:
    print(f"FAIL: managed-agents scan error: {e}")
    fail = 1

# decision-records: must have at least 1
try:
    r = ddb.scan(TableName="orcast-aws-backend-decision-records", Select="COUNT")
    count = r["Count"]
    if count >= 1:
        print(f"PASS: decision-records count={count}")
    else:
        print(f"FAIL: decision-records count=0 (expected >=1)")
        fail = 1
except Exception as e:
    print(f"FAIL: decision-records scan error: {e}")
    fail = 1

# hotspots: must have at least 1
try:
    r = ddb.scan(TableName="orcast-aws-backend-hotspots", Select="COUNT")
    count = r["Count"]
    if count >= 1:
        print(f"PASS: hotspots count={count}")
    else:
        print(f"FAIL: hotspots count=0")
        fail = 1
except Exception as e:
    print(f"FAIL: hotspots scan error: {e}")
    fail = 1

if fail:
    print("Q1c: FAIL")
    sys.exit(1)
print("Q1c: PASS")
EOF
