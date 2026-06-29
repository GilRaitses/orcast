# ORCAST Integrity-Grade Data Procurement Charter

## Purpose

This wave set identifies the missing data needed for integrity-grade ORCAST forecasting. The goal is not to add every possible data source. The goal is to source the data that supports the model's validity conditions:

- input integrity
- effort offset
- kernel identifiability
- prey covariate
- spatial covariate
- detectability/noise
- external validation

## Availability Labels

- `public_api`: can be acquired through a documented public API.
- `public_download`: can be downloaded publicly as files or bulk archives.
- `public_scrape_required`: public page exists but no stable API is confirmed.
- `account_required`: account or API key is needed, but no research approval appears necessary.
- `research_request_required`: access likely requires contacting a project, agency, or research group.
- `vendor_or_restricted`: commercial/restricted source; avoid unless essential.
- `not_found`: no credible source found.

## Decision Labels

- `can_get_now`: agents can fetch or define the adapter from public information.
- `needs_user_account`: the user must create a login/API key.
- `needs_research_request`: the user must request data access from an organization.
- `vendor_or_restricted`: not recommended unless no public substitute exists.
- `not_worth_it`: source is too weak, duplicative, or high-friction for current model needs.

## Priority Labels

- `P0`: required to make current Level 1-2 claims defensible.
- `P1`: needed for Level 3 spatial/prey modeling or stronger validation.
- `P2`: useful but not blocking.

## Agent Output Template

Each source reconnaissance agent must return:

```yaml
source: string
purpose: string
availability: public_api | public_download | public_scrape_required | account_required | research_request_required | vendor_or_restricted | not_found
account_needed: none | free_account | api_key | moderator_access | researcher_request | vendor_contract | unknown
license: string
endpoint_or_access_path: string
fields:
  - name: string
    meaning: string
time_coverage: string
spatial_coverage: string
adapter_contract:
  stream_name: string
  record_shape: object
  cadence: string
integrity_condition: input_integrity | effort_offset | kernel_identifiability | prey_covariate | spatial_covariate | detectability_noise | external_validation
risks:
  - string
next_action: string
decision_label: can_get_now | needs_user_account | needs_research_request | vendor_or_restricted | not_worth_it
priority: P0 | P1 | P2
```

## Non-Goals

- Do not use vendor data if a public or agency source is adequate.
- Do not treat a climatology fallback as a validated ecological covariate.
- Do not ingest bulk data before confirming license and field schema.
- Do not mix observation-effort covariates with ecological covariates without labeling the role.
