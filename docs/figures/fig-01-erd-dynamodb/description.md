# fig-01-erd-dynamodb

Nine DynamoDB tables used by the orcast system. Logical application-level references only — DynamoDB enforces pk by convention; no FK constraints are applied by the database.

## Tables

1. **sightings** — normalized sighting records from all sources
2. **community-submissions** — quarantined citizen reports pending moderation
3. **decision-records** — immutable human reviewer decisions (promote/hold/reject)
4. **ingestion-runs** — per-run audit records for the ingest lambda
5. **hotspots** — top cells from the probability surface
6. **reports** — full probability reports; hotspots[] is a denormalized snapshot embed
7. **user-journal** — private per-user field notes (WorkOS-scoped, GSI on user_id)
8. **partner-api-keys** — hashed API keys for the partner gateway
9. **managed-agents** — Central Casting agent configs (policy, skills, model)

## Reference conventions

- Edges attach to the specific field row, not the outer table boundary
- Open circle at the FK (dependent) end; filled arrowhead at the PK (referenced) end
- `FK` label placed outside the table at the dependent endpoint
- Dashed edges for logical-only references (no enforced FK)
- Legend explains the DynamoDB disclaimer
