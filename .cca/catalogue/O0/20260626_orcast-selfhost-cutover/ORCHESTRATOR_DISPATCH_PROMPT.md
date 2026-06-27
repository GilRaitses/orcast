You are resuming the **orcast self-host cutover** lane (O0).

## First action

Read, in order, the files in:
`.cca/catalogue/O0/20260626_orcast-selfhost-cutover/HYDRATION_PACKET.md`

It gives the read order, the locked decisions, what shipped, and the open
follow-ups. Hydrate from files, not from the chat transcript.

## State (2026-06-26)

The cutover is EXECUTED and verified GREEN. orcast production
(`orcast-h0.vercel.app`) now proxies to the self-hosted backend
`https://orcast-api.aimez.ai` (co-tenant `orcast-api.service` on the
`aimez-services` EC2). App Runner `orcast-aws-backend` stays RUNNING as rollback.
The `orcast/.ddb` ledger exists with the first system-state baseline registered.

## Do not

- Do not scale down / pause App Runner before the June 29 submission (DD-3).
- Do not replace the cloudflared tunnel ingress; it is additive (pax cv/shade must stay).
- Do not `git add -A`; surgical commits only (SD-024).
- Do not push the uncommitted local explore3d backend to the host without intent (DD-4).

## Open follow-ups (pick one and state it)

- Commit the new surfaces to `main` (surgical): `infra/shared_host/`, `.ddb/`, `.sst/`, `.cca/DEPLOY_DEMO_DECISIONS.md`, this handoff home.
- Post-submission: pause App Runner (DD-3).
- Backend P2: fix `AwsStorage.raw_payload_bucket` (DD-5), then `git -C /opt/orcast pull --ff-only && sudo systemctl restart orcast-api`.
- OX operator gates: DynamoDB screenshot, Devpost, arXiv.
