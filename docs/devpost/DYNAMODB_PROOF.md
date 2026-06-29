# DynamoDB usage proof (H0 submission)

Primary AWS database: **Amazon DynamoDB**. Account `198456344617`, region `us-west-2`.
All **nine** tables are CloudFormation-managed ([infra/aws/template.yaml](../../infra/aws/template.yaml))
and accessed through the `AwsStorage` backend, `JournalStore`, and Central Casting registry ([src/aws_backend/storage.py](../../src/aws_backend/storage.py), [src/aws_backend/journal/store.py](../../src/aws_backend/journal/store.py), [src/aws_backend/casting/registry.py](../../src/aws_backend/casting/registry.py)).

## Live tables (on-demand)

| Table | Role | Key schema | Items (approx) | Status |
|---|---|---|---|---|
| `orcast-aws-backend-sightings` | Normalized orca sightings with source provenance | `pk` | ~131 | ACTIVE |
| `orcast-aws-backend-community-submissions` | Citizen-science moderation queue | `pk` | ~3+ | ACTIVE |
| `orcast-aws-backend-decision-records` | Immutable human promotion-decision audit log | `pk` | 0+ | ACTIVE |
| `orcast-aws-backend-user-journal` | Private field journal (WorkOS user scoped) | `pk` + `sk` | 0+ | ACTIVE |
| `orcast-aws-backend-hotspots` | Computed probability hotspots | `pk` | ~85 | ACTIVE |
| `orcast-aws-backend-reports` | Probability reports | `pk` | ~237 | ACTIVE |
| `orcast-aws-backend-ingestion-runs` | Per-run ingestion audit | `pk` | ~428 | ACTIVE |
| `orcast-aws-backend-partner-api-keys` | Partner OpenAPI gateway keys | `pk` | 1+ | ACTIVE |
| `orcast-aws-backend-managed-agents` | Central Casting managed agent configs | `pk` | 4+ | ACTIVE |

All tables are `BillingMode: PAY_PER_REQUEST` with `KeySchema` `pk (HASH)`. Item counts are
the DynamoDB-reported approximate `ItemCount` (refreshed ~every 6 hours).

S3 is used only as supporting storage (time-series NDJSON + fitted kernel artifacts); the
transactional/operational backbone is DynamoDB.

## How the app uses DynamoDB

- Read paths: `/api/sightings`, `/api/hotspots`, `/api/reports/*`, `/api/community/submissions`,
  `/api/decision-records` (see [src/aws_backend/routers/](../../src/aws_backend/routers)).
- Write paths: source ingestion writes `sightings` + `ingestion-runs`; the public shore form
  writes `community-submissions`; journal publish copies to `community-submissions`;
  moderation updates submission status; the human promotion step writes `decision-records`;
  field journal CRUD writes `user-journal`.
- The demo's human-in-the-loop flow (submit shore sighting -> moderate -> decision record) is
  entirely DynamoDB-backed.

## Reproduce the proof (CLI)

```bash
aws dynamodb list-tables --region us-west-2 \
  --query "TableNames[?contains(@,'orcast')]"

for T in sightings community-submissions decision-records user-journal hotspots reports ingestion-runs partner-api-keys managed-agents; do
  aws dynamodb describe-table --region us-west-2 \
    --table-name "orcast-aws-backend-$T" \
    --query "{name:Table.TableName,key:Table.KeySchema,items:Table.ItemCount,billing:Table.BillingModeSummary.BillingMode}"
done
```

## Console screenshot to attach to the submission

The submission asks for a screenshot proving AWS database usage. Capture either:

1. AWS Console -> DynamoDB -> Tables (region us-west-2), showing the nine `orcast-aws-backend-*`
   tables in the list, OR
2. A single table's "Explore items" view (e.g. `orcast-aws-backend-community-submissions`
   or `orcast-aws-backend-user-journal`) showing real items.

Save it as `docs/devpost/figures/dynamodb-console.png` for the Devpost upload.
