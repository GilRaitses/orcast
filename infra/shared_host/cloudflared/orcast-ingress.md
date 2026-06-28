# orcast tunnel ingress (W-REACH) — shared aimez-services tunnel

> **RETIRED AS PRIMARY (DD-10, 2026-06-28).** `orcast-api.aimez.ai` is no longer in
> the production path; App Runner serves all backend traffic. This ingress is the
> **decommission target** of the FW2 wave in
> `.cca/catalogue/O0/20260628_hosting-consolidation-followups/`: an operator
> removes the orcast ingress rule + the `api.orcast` CNAME (read-modify-write; the
> pax `cv`/`shade` routes are preserved verbatim). The procedure below also serves
> as the teardown reference — invert it to remove the rule and the CNAME.

The shared host runs a **remotely-managed** cloudflared tunnel (token-based; no
local `/etc/cloudflared/config.yml`). Ingress is configured through the Cloudflare
API, NOT a file on the host.

- Account: `0b620d7c4ea9b39dcd8d04b853bd8c2f`
- Tunnel `aimez-services`: `e1ce3073-0588-4125-9f6a-cff5fb2a7d3d`
- Zone `aimez.ai`: `5200b6a14fd92f5ef1fc9127b28168d9`
- Hostname: `orcast-api.aimez.ai` -> `http://127.0.0.1:8090`

Use a FIRST-LEVEL subdomain (`orcast-api.aimez.ai`), like pax's `cv.`/`shade.`.
The Universal SSL cert covers `*.aimez.ai` but NOT a third-level name such as
`orcast-api.aimez.ai`, which fails the TLS handshake (`sslv3 alert handshake
failure`). A multi-level name would need Advanced Certificate Manager.

The orcast ingress is APPENDED to the existing pax ingress (`cv.aimez.ai` 8077,
`shade.aimez.ai` 8078) before the `http_status:404` catch-all. The pax routes are
preserved verbatim — read-modify-write, never replace.

## 1. Add the public hostname to the tunnel config

GET the current config, insert the orcast rule before the catch-all, PUT it back:

```bash
set -a; . ~/.pax_cutover.env; set +a
ACCT="$CLOUDFLARE_ACCOUNT_ID"; TUN="e1ce3073-0588-4125-9f6a-cff5fb2a7d3d"
curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCT/cfd_tunnel/$TUN/configurations" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" > /tmp/tun.json
# append {hostname: orcast-api.aimez.ai, service: http://127.0.0.1:8090} before the 404,
# then PUT {"config": {...}} back to the same endpoint.
```

## 2. Create the proxied DNS CNAME

```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/5200b6a14fd92f5ef1fc9127b28168d9/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"api.orcast","content":"e1ce3073-0588-4125-9f6a-cff5fb2a7d3d.cfargotunnel.com","proxied":true}'
```

## 3. Auth model

No new tunnel service key. The orcast backend keeps its own `ORCAST_API_KEY`
auth: keyed endpoints require the `X-ORCAST-Key` header that the Vercel proxy
injects. Public read-only GETs and the anonymous-first POSTs are open by design
(identical posture to the public App Runner URL).

## 4. Verify

```bash
curl -fsS https://orcast-api.aimez.ai/health           # 200
curl -fsS https://orcast-api.aimez.ai/api/gates        # 200 (public)
curl -s -o /dev/null -w '%{http_code}\n' https://orcast-api.aimez.ai/api/evidence/assets  # 401 (keyed)
```
