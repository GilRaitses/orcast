# Lane file ownership

Canonical wave definitions: [docs/devpost/WAVES_REGISTRY.md](../../../docs/devpost/WAVES_REGISTRY.md).

Wave 0 (AT-0) split routers so parallel lanes do not conflict on `main.py`.

## Quarantine rule

`archive/quarantine/**` is **out of scope** for implement and probe lanes unless explicitly assigned. Legacy agent demos and the July 2025 presentation deck live there.

## API truth repair — implement lanes (AT)

| File | Lane | Wave |
|------|------|------|
| `src/aws_backend/main.py` | coordinator | AT-0 |
| `src/aws_backend/state.py` | coordinator | AT-0 |
| `src/aws_backend/routers/read.py` | agent-read-truth | AT-0 split, AT-1 |
| `src/aws_backend/routers/write.py` | agent-write-auth | AT-0 split, AT-1 |
| `src/aws_backend/routers/forecast.py` | agent-forecast-ghost | AT-0 split, AT-1 |
| `src/aws_backend/routers/reports.py` | coordinator | AT-0 |
| `src/aws_backend/routers/deprecated.py` | agent-forecast-ghost | AT-1 |
| `src/aws_backend/auth.py` | agent-write-auth | AT-1 |
| `src/aws_backend/config.py` | agent-write-auth | AT-1 |
| `src/aws_backend/scoring.py` | agent-forecast-ghost | AT-1 |
| `src/aws_backend/models.py` | agent-forecast-ghost | AT-1 |
| `infra/aws/template.yaml` | agent-write-auth | AT-1 |
| `tests/aws_backend/test_read_endpoints.py` | agent-read-truth | AT-1 |
| `tests/aws_backend/test_auth.py` | agent-write-auth | AT-1 |
| `tests/aws_backend/test_forecast.py` | agent-forecast-ghost | AT-1 |
| `orcast-angular/src/app/components/realtime-detection/*` | agent-ui-labels | AT-2 |
| `orcast-angular/src/app/components/ml-predictions/*` | agent-ui-labels | AT-2 |
| `orcast-angular/src/app/components/landing/*` | agent-ui-labels | AT-2 |
| `orcast-angular/src/app/components/shared/nav-header.component.ts` | agent-ui-labels | AT-2 |
| `archive/quarantine/orcast-angular-legacy/components/map-dashboard/*` | (quarantined) | — |
| `orcast-angular/src/app/services/backend.service.ts` | agent-frontend-contract | AT-2 |
| `orcast-angular/cypress/e2e/aws-backend-smoke.cy.ts` | agent-frontend-contract | AT-2 |
| `docs/DNS_SETUP.md`, deployment docs | agent-docs-purge | AT-3 |
| `docs/API.md` | agent-api-catalog | AT-3 |

Do not edit files outside your lane without coordinator merge.

## Remediation channels (R) — aliases

| Canonical | Alias | Scope summary |
|-----------|-------|----------------|
| R-Alpha | Channel Alpha, T0-alpha | `auth.py`, trusted proxy, moderation conditional |
| R-Beta | Channel Beta | `partner.py`, `web/app/api/v1/` |
| R-Gamma | Channel Gamma | `fit_kernels.py`, ASL snapshot wire |
| R-Delta | Channel Delta | `docs/devpost/*` truth labels |
| R-Foxtrot | Channel Foxtrot | `infra/aws/`, Vercel env, partner seed |
| R-Echo | Channel Echo | prod smoke — gate `tools/waves/run-gate.sh R-echo` |

## Adversarial probe lanes (P) — readonly

| Lane | Scope glob | Adversarial question |
|------|------------|----------------------|
| P1-A | `web/app/api/be/`, `web/middleware.ts`, `src/aws_backend/auth.py`, `community.py`, `kernel.py` | Bypass WorkOS / fake reviewer? |
| P1-B | `src/aws_backend/routers/`, `docs/API.md`, `docs/devpost/API_AGENTS.md` | Ghost endpoints or doc lies? |
| P1-C | CloudFront live + `orcast-angular/src/app/` routed pages | Stale copy or fake "live" labels? |
| P1-D | `modeling/`, `kernel_model/serve.py`, `web/app/gates/` | Confidence exceeds earned gates? |
| P1-E | `web/app/api/v1/`, `routers/partner.py` | Partner auth / rate-limit bypass? |
| P1-F | `review_dossier.py`, `promotion/`, `storage.py`, moderation UI | PII leak / double-approve? |

Panel prompts: [docs/devpost/ADVERSARIAL_PROBE_PLAYBOOK.md](../../../docs/devpost/ADVERSARIAL_PROBE_PLAYBOOK.md).

## Wave Set E — exploration guide (implement lanes)

Contract: [docs/devpost/exploration/CONTRACT.md](../../../docs/devpost/exploration/CONTRACT.md).

| Lane | Agent | Owns | Must not touch |
|------|-------|------|----------------|
| E1-A | agent-e-infra | `infra/aws/template.yaml` (Aurora, VPC connector, secret, outputs) | `src/aws_backend/*`, `web/*` |
| E1-B | agent-e-store | `src/aws_backend/exploration/db.py`, `models.py`, `session_store.py`, `migrations/`, `tests/aws_backend/test_exploration_store.py`, `requirements.txt` (psycopg only) | `routers/`, `main.py`, `infra/` |
| E1-B-config | agent-e-store | `src/aws_backend/config.py` (`database_url` field only) | other config fields |
| E1-C | agent-e-api | `src/aws_backend/exploration/tools.py`, `guide.py`, `routers/explore.py`, `tests/aws_backend/test_explore_router.py` | `main.py`, `web/*`, `template.yaml` |
| E1-D | agent-e-ui | `web/app/explore/`, `web/app/components/ExploreGuidePanel.tsx`, `web/app/components/Nav.tsx` (link only) | `web/app/api/be/` |
| E1-E | agent-e-test | `tools/waves/gates/e2-local.sh`, `e-prod-smoke.sh`, `e-doc-grep.sh`, `run-gate.sh` (e2/e-gate entries) | deploy scripts until E4 |
| E2 | integrator | `main.py`, `web/app/api/be/[...path]/route.ts`, `web/lib/explore.ts` | — |
| E2-F | agent-e-gateway | `web/app/api/explore/route.ts`, `web/package.json` (AI SDK) | backend explore router |
| E3-A | agent-e-docs | `docs/devpost/figures/architecture.mmd`, PNG export, `H0_WORKSHOP_COMPLIANCE.md`, `SUBMISSION.md` | — |
| E3-B | agent-e-registry | `WAVES_REGISTRY.md`, `waves.registry.yaml`, `HANDOFF_STATUS.md` | — |
| E5-A…F | probe (readonly) | see CONTRACT + ADVERSARIAL_PROBE_PLAYBOOK | no writes |

## Wave Set F — caveat mediation

Charter: [docs/devpost/exploration/F0_CAVEAT_CHARTER.md](../../../docs/devpost/exploration/F0_CAVEAT_CHARTER.md).

| Lane | Agent | Owns |
|------|-------|------|
| F1-A | agent-f-network | `infra/aws/template.yaml` (VPC connector, private RDS, endpoints, NAT) |
| F1-B | agent-f-rate | `web/app/api/be/[...path]/route.ts`, `routers/explore.py`, `session_store.py` limits |
| F1-C | agent-f-retention | `exploration/migrations/002_*`, purge helper, tests |
| F1-D | agent-f-docs | CONTRACT, architecture.mmd/png, H0_WORKSHOP_COMPLIANCE, HANDOFF |
| F1-E | agent-f-test | `tools/waves/gates/f-*.sh`, `run-gate.sh` |

## Wave Set M — Central Casting (user-facing Wave Set H)

Contract: [docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md](../../../docs/devpost/casting/MANAGED_AGENTS_CONTRACT.md).

| Lane | Agent | Owns | Must not touch |
|------|-------|------|----------------|
| M1-A | agent-m-infra | `infra/aws/template.yaml` (ManagedAgentsTable), `config.py` (`managed_agents_table` only) | `casting/`, `routers/`, `web/*` |
| M1-B | agent-m-registry | `casting/models.py`, `registry.py`, `seeds/`, `routers/managed_agents.py`, `test_managed_agents_registry.py` | `concierge.py`, `interactions.py`, `main.py` |
| M1-C | agent-m-runtime | `casting/concierge.py`, `routers/interactions.py`, `migrations/003_*`, `session_store.py` trace columns, `test_interactions_router.py` | `template.yaml`, `skills.py`, `managed_agents.py` |
| M1-D | agent-m-skills | `casting/skills.py`, `policy.py`, `exploration/guide.py` (optional params), `test_casting_policy.py` | routers, DDB |
| M1-E | agent-m-test | `tools/waves/gates/m-*.sh`, `run-gate.sh` (m/m-gate) | production routers until M2 |
| M2 | integrator | `main.py`, `web/app/api/be/[...path]/route.ts`, `WAVES_REGISTRY.md`, `waves.registry.yaml` | — |
| M3 | deploy | `deploy.sh`, `seed_managed_agent.py`, `sync-apprunner-explore-env.sh` | — |

## Wave Set IC — Interactions Casting (user-facing Wave Set I)

Pattern: [docs/devpost/casting/INTERACTIONS_GROUNDING_PATTERN.md](../../../docs/devpost/casting/INTERACTIONS_GROUNDING_PATTERN.md).

| Lane | Agent | Owns | Must not touch |
|------|-------|------|----------------|
| IC2-A | agent-ic-manifest | `casting/skills_manifest.json`, `manifest.py`, `SKILL_CATALOG.md`, `policy.py` validation | `concierge.py`, UI |
| IC2-B | agent-ic-adapters | `exploration/tools.py` fetch wrappers, reserved stubs | manifest, migrations |
| IC2-C | agent-ic-schema | `migrations/004_*`, `session_store.py` `interaction_steps`, `models.py` | skills dispatch |
| IC2-D | agent-ic-test | `tools/waves/gates/ic-*.sh`, `test_casting_policy.py`, `test_interactions_router.py` | production deploy |
| IC2 integrator | integrator | `concierge.py`, `interactions.py`, `MANAGED_AGENTS_CONTRACT.md`, registry | — |
