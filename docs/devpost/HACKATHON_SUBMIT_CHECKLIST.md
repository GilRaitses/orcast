# Hackathon submit checklist (June 29, 2026 5:00 PM)

**Waves registry:** [WAVES_REGISTRY.md](WAVES_REGISTRY.md)

Team ID: `team_dQQph8zC78tTPHDnGnvawdKo`  
Live demo: https://orcast-h0.vercel.app

## Automated gates (run before publish)

```bash
./tools/waves/run-gate.sh H0
./tools/waves/run-gate.sh s-gate    # after S1–S3 complete
./tools/waves/run-gate.sh ic6-gate  # casting regression
```

Or run checks individually:

```bash
python3 tools/testing/agent_smoke.py --dry-run
curl -s https://orcast-h0.vercel.app/api/be/api/sighting-assist/status | jq .narration_backend
```

Both must pass. Bedrock should report `bedrock` or `template` for narration_backend.

## Deploy before partner curl

```bash
# Vercel (from web/)
vercel deploy --prod
# Set ORCAST_PARTNER_DEV_KEY in Vercel env, then:
curl -s -H "X-ORCAST-Partner-Key: $ORCAST_PARTNER_DEV_KEY" \
  https://orcast-h0.vercel.app/api/v1/api/gates | jq .status
```

## You record (H1) — manual

Operator dossier: [submission/H1_MANUAL_SUBMIT.md](submission/H1_MANUAL_SUBMIT.md)

- [x] ~3 minute demo video → `docs/devpost/figures/_demo-run/demo-final-narrated-3min.mp4` (2:53, silence-trimmed from the 3:10 narrated cut; upload to YouTube)
- [x] DynamoDB usage proof → `docs/devpost/figures/dynamodb-console.png` (live `describe-table` for all 9 tables; regenerate with `python3 tools/testing/build_ddb_console_proof.py`)
- [ ] Publish Devpost from [DEVPOST_DRAFT.md](DEVPOST_DRAFT.md)

Partner key is in Vercel env `ORCAST_PARTNER_DEV_KEY` (also seeded in DDB `orcast-aws-backend-partner-api-keys`).

## Already in repo

- [x] Truth table: [workflow-truth-table.md](workflow-truth-table.md) (9 tables, journal, `/ask`, Bedrock, casting)
- [x] S0 charter: [submission/S0_SUBMISSION_SYNC_CHARTER.md](submission/S0_SUBMISSION_SYNC_CHARTER.md)
- [x] Workshop compliance scope: [H0_WORKSHOP_COMPLIANCE.md](H0_WORKSHOP_COMPLIANCE.md)
- [x] Architecture diagram source: [figures/architecture.mmd](figures/architecture.mmd)
- [x] DynamoDB proof doc: [DYNAMODB_PROOF.md](DYNAMODB_PROOF.md)
- [x] Agent smoke + setup: `tools/testing/agent_smoke.py`, `AGENT_USER.md`
- [x] Partner API docs: [API_AGENTS.md](API_AGENTS.md)

## Judge cross-check URLs

| Claim | URL |
|-------|-----|
| Forecast map | `/` |
| Gates | `/gates` |
| Ask (Bedrock) | `/ask` |
| Field journal | `/journal` |
| Moderation | `/moderation` |
| Provenance | `/api/be/api/provenance` (signed in or agent key) |
| Explore planner | `/explore?planner=1` (signed in) |
| Casting plan API | `/api/be/api/interactions/plan` (keyed) |
