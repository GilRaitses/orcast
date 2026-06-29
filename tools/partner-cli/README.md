# orcast partner CLI

Thin CLI wrapping the `/api/v1` partner gateway. Set:

```bash
export ORCAST_WEB_BASE=https://orcast-h0.vercel.app
export ORCAST_PARTNER_KEY=<your-dev-key>
```

Commands:

- `python3 tools/partner-cli/server.py get_gates`
- `python3 tools/partner-cli/server.py get_provenance`
- `python3 tools/partner-cli/server.py check_sighting --place "Lime Kiln" --observed_at 2026-06-19T12:00:00Z`

This is not an MCP protocol server; it is a copy-paste partner HTTP client.

Full OpenAPI and tool JSON: [API_AGENTS.md](../../docs/devpost/API_AGENTS.md).
