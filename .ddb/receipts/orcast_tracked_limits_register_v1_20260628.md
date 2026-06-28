# Receipt: orcast tracked-limits register v1 (WS-CLOSEOUT TLR)

- Decision: `orcast_tracked_limits_register_v1_20260628`
- Kind: `tracked_limits_register`
- Status: active
- Date: 2026-06-28
- Anchor baseline: `orcast_system_state_baseline_v3_20260628`
- Artifact: `.sst/tracked_limits_register_v1.json`

## What was decided

orcast's known limits and residual risks now have a first-class, machine-authoritative
register. Each limit carries a `surmountable` flag, a risk level, a blast radius, a
disposition, a status, a DD reference, an owner, and a future direction. The register
is the canonical limit source; the submission docs and the public web surface draw
from it so the prose cannot drift from the ratified state.

Seeded from: the AX-9 tracked-limits dossier (`.cca/AX_ADVERSARIAL_REGISTER.md`),
baseline v3 `tracked_limits[]`, the whitepaper pilot-scope and known-limits section,
the model-card caveats, the source datasheets, the H0 risk assessment, and the Q/U
gap registers.

## Surmountable vs unsurmountable

- **Unsurmountable for the submission window** (ratified hard limits, mostly scientific
  or scope): TL-01 single-station acoustic, TL-02 unreviewed acoustic, TL-03
  effort-biased sightings, TL-04 honest 0% promoted confidence, TL-05 pilot spatial
  scope, TL-07 twin modeled in sandbox, TL-08 B-side dtag/annotation as direction.
- **Surmountable** (owned fix path, deferred by the window or an operator gate): TL-06
  excluded covariates, TL-09 LGC not shipped, TL-10 SES sandbox, TL-11 no warm
  rollback, TL-12 inert self-host teardown, TL-13 ONC disabled, TL-14 explore3d not
  deployed, TL-15 SSM-only access, TL-16 SDR drift, TL-17 demo narration not
  prose-gated.

## Recently closed (by prior ratified decisions)

- App Runner cold-start user-visible gap (`coldstart_mitigation_v1`, measured gap = 0).
- Self-host + Cloudflare primary path (`hosting_consolidation_v1` / `selfhost_decommission_v1`).
- Explore-session RDS write path (baseline v3, now 200), resolving DD-6.
- P0 authorization bypass on evidence/journal routers (`require_api_key`, `d866e48`).

## Reconciliation gate

Every limit on the AX-9 dossier and baseline v3 `tracked_limits` is either carried
forward here with a surmountable/unsurmountable mark and a future direction, or moved
to `recently_closed` with the decision that closed it. No limit was dropped silently;
no closed limit was re-asserted as open.

## Non-claims

- This register records limits and risks; it does not change any model output, gate
  verdict, or topology.
- An unsurmountable-window limit is a ratified scope or honesty limit, not an
  infrastructure defect.
