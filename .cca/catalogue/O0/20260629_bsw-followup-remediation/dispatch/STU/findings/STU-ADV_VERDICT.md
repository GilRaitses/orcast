# STU-ADV verdict (studio-live-persistence)

Security audit of the wired annotation write path against the STU-R4 risk
register. The path is the net-new authenticated backend route
`src/aws_backend/routers/annotations.py` plus its store
`src/aws_backend/annotations/store.py`, the proxy default-deny on
`api/dtag/annotations`, and the documentation-only `PROTECTED_PATHS` entry.

`repo_state_verified_against`: 61ba1d69ee36cf605f7ba741bdaa1defa8762834

## Verdict

Zero open P0. Zero open P1. The two P0 mitigations and all P1 mitigations from
the R4 register were built into STU-B and are verified by passing offline tests.
Residual items are P2 and P3 and are recorded below with their status.

Evidence run: `pytest tests/aws_backend/test_dtag_annotations.py` is 19 passed.
Related suites `test_dtag.py`, `test_decision_records.py`, `test_community.py`,
`test_auth.py` are 30 passed, so the new router mounts without regressing the
existing surface. `tsc --noEmit` in `web/` is clean.

## Risk register, audited

| id | risk | class | status | mitigation in the wired code | test evidence |
|---|---|---|---|---|---|
| R4-1 | direct-backend header-spoof auth bypass | P0 | CLOSED | router declares `APIRouter(dependencies=[Depends(require_api_key)])`; writes add `require_trusted_reviewer`. A keyless direct caller is rejected before reviewer logic runs. | `test_direct_keyless_call_rejected_when_api_key_configured`, `test_post_without_reviewer_is_rejected`, `test_list_without_reviewer_is_rejected` |
| R4-2 | provenance identity tamper | P0 | CLOSED | `annotator_id` is the verified reviewer id, `annotator_role` the verified role, `source` pinned to `community`. Body identity fields ignored. | `test_provenance_is_server_stamped_not_from_body` |
| R4-3 | dataset / license / tool / h5 spoof | P1 | CLOSED | `dataset` pinned to deployment id, `license_status` pinned from record, `tool` pinned constant, `h5_refs` pinned to the server dive set. | `test_provenance_is_server_stamped_not_from_body` asserts client `evil/ref` dropped |
| R4-4 | honesty mislabel against fake or real deployment | P1 | CLOSED | unknown `deployment_id` rejected with 404; `simulated` copied from the deployment record onto the record and every response. | `test_unknown_deployment_is_rejected`, `test_simulated_label_stamped_from_record` |
| R4-5 | PII leakage of reviewer email | P1 | CLOSED | the opaque reviewer id is stored, the email is never persisted, reads use an explicit field allow-list (`_to_wire`). | `test_reviewer_email_never_returned` |
| R4-6 | idempotency / double-submit | P1 | CLOSED | content-key dedup (`reviewer_id|deployment_id|start|end|behavior`) with `attribute_not_exists(sk)` conditional put; server-generated uuid4 id. | `test_duplicate_post_is_idempotent`, `test_distinct_reviewers_are_not_deduped`, `test_aws_store_create_is_content_key_write_once` |
| R4-7 | stored injection in free-text fields | P1 | CLOSED | enum allow-lists for `target.kind` and `method`; slug pattern with length cap for `behavior` and `state`; `notes` capped at 2000; request provenance string fields length-capped; the studio renders `notes` through React text escaping (no `dangerouslySetInnerHTML`). | `test_invalid_behavior_is_422`, `test_invalid_target_kind_is_422`, `test_notes_over_cap_is_422`, `test_confidence_out_of_range_is_422` |
| R4-8 | resource abuse / DoS | P1 | CLOSED | field length caps bound the body; list route capped with `limit` (default 100, max 500); per-reviewer in-process write rate limit returns 429. | `test_write_rate_limit_per_reviewer` |

## Residuals (P2 / P3)

- DynamoDB expression injection (P3, not applicable as built). The AWS store uses
  a static `ConditionExpression="attribute_not_exists(sk)"` and parameterized
  `Key`/`Attr` conditions. No user input is interpolated into any expression.
- Log injection (P3, not applicable as built). The router does not log request
  fields.
- Agent-key exposure (P2, unchanged by this lane). The `X-ORCAST-Agent-Key` path
  is env-only and gitignored. STU-ACCEPT uses it for the headless round-trip and
  must not write the key to a tracked file.
- Get-by-id scan on the AWS path (P3, scale only). `get` uses a filtered scan;
  the annotation set per simulated deployment is tiny. A GSI on `id` is the noted
  scale path and is a future optimization, not a security issue.

## Loop status

No loop back to STU-B or STU-INT was required. The mitigations were implemented
in STU-B from the start per the O0 hard constraint, so the first adversarial pass
found zero open P0 or P1.
