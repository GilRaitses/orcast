# API Truth Repair — Lane File Ownership

Wave 0 split routers so parallel lanes do not conflict on `main.py`.

| File | Lane | Wave |
|------|------|------|
| `src/aws_backend/main.py` | coordinator | 0 |
| `src/aws_backend/state.py` | coordinator | 0 |
| `src/aws_backend/routers/read.py` | agent-read-truth | 0 split, 1 truth |
| `src/aws_backend/routers/write.py` | agent-write-auth | 0 split, 1 auth |
| `src/aws_backend/routers/forecast.py` | agent-forecast-ghost | 0 split, 1 forecast |
| `src/aws_backend/routers/reports.py` | coordinator | 0 split |
| `src/aws_backend/routers/deprecated.py` | agent-forecast-ghost | 1 |
| `src/aws_backend/auth.py` | agent-write-auth | 1 |
| `src/aws_backend/config.py` | agent-write-auth | 1 |
| `src/aws_backend/scoring.py` | agent-forecast-ghost | 1 |
| `src/aws_backend/models.py` | agent-forecast-ghost | 1 |
| `infra/aws/template.yaml` | agent-write-auth | 1 |
| `tests/aws_backend/test_read_endpoints.py` | agent-read-truth | 1 |
| `tests/aws_backend/test_auth.py` | agent-write-auth | 1 |
| `tests/aws_backend/test_forecast.py` | agent-forecast-ghost | 1 |
| `orcast-angular/src/app/components/realtime-detection/*` | agent-ui-labels | 2 |
| `orcast-angular/src/app/components/ml-predictions/*` | agent-ui-labels | 2 |
| `orcast-angular/src/app/components/landing/*` | agent-ui-labels | 2 |
| `orcast-angular/src/app/components/shared/nav-header.component.ts` | agent-ui-labels | 2 |
| `orcast-angular/src/app/components/map-dashboard/*` | agent-ui-labels | 2 |
| `orcast-angular/src/app/services/backend.service.ts` | agent-frontend-contract | 2 |
| `orcast-angular/cypress/e2e/aws-backend-smoke.cy.ts` | agent-frontend-contract | 2 |
| `docs/DNS_SETUP.md`, deployment docs | agent-docs-purge | 3 |
| `docs/API.md` | agent-api-catalog | 3 |

Do not edit files outside your lane without coordinator merge.
