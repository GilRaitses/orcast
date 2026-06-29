# orcast external agent API

> **Deploy gate:** `/api/v1` is live only after Vercel deploy with `ORCAST_PARTNER_DEV_KEY` set.
> Prefix-based keys (`orcast_builder_*`) are **not** accepted; use a provisioned dev key or DDB-hashed key.

Partner-facing surface for Claude, OpenAI, and HTTP clients. Authenticate with
`X-ORCAST-Partner-Key` on the Vercel gateway (`/api/v1/...`).

## Base URLs

| Environment | Base |
|-------------|------|
| Production gateway | `https://orcast-h0.vercel.app/api/v1` (after deploy) |
| Backend verify (internal) | `POST /api/partner/verify` on App Runner |

## Authentication

```http
X-ORCAST-Partner-Key: <ORCAST_PARTNER_DEV_KEY>
```

Response headers:

```http
X-ORCAST-Partner-Tier: builder
```

| Tier | Source | Daily limit | Sighting assist |
|------|--------|-------------|-----------------|
| free | DDB hashed key | 100 | no |
| builder | dev key or DDB | 1,000 | yes |
| pro | DDB hashed key | 10,000 | yes |

Invalid keys return `401`. Sighting assist on free tier returns `402`.
Per-IP and per-key daily limits return `429` when exceeded (gateway-enforced).

## OpenAPI subset

### `GET /api/gates`

```bash
curl -s -H "X-ORCAST-Partner-Key: $ORCAST_PARTNER_DEV_KEY" \
  "https://orcast-h0.vercel.app/api/v1/api/gates" | jq .
```

### `GET /api/provenance`

```bash
curl -s -H "X-ORCAST-Partner-Key: $ORCAST_PARTNER_DEV_KEY" \
  "https://orcast-h0.vercel.app/api/v1/api/provenance" | jq .
```

### `POST /api/sighting-assist`

Builder+ only.

```bash
curl -s -X POST -H "Content-Type: application/json" \
  -H "X-ORCAST-Partner-Key: $ORCAST_PARTNER_DEV_KEY" \
  "https://orcast-h0.vercel.app/api/v1/api/sighting-assist" \
  -d '{"place":"Lime Kiln","observed_at":"2026-06-19T12:00:00Z","behavior":"feeding"}' | jq .
```

### `GET /api/sighting-assist/status`

```bash
curl -s -H "X-ORCAST-Partner-Key: $ORCAST_PARTNER_DEV_KEY" \
  "https://orcast-h0.vercel.app/api/v1/api/sighting-assist/status" | jq .narration_backend
```

## Partner CLI

See `tools/partner-cli/README.md` (HTTP client, not MCP protocol).

## Billing

Partner keys are stored hashed in DynamoDB (`orcast-partner-api-keys`).
Stripe provisioning is stubbed in `src/aws_backend/billing/`; tier catalog at `GET /api/partner/tiers` (keyed).

## Internal automation

CI uses `X-ORCAST-Agent-Key` on `/api/be/...`. Do not expose that key to external LLM vendors.
