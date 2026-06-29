# STU-R2 Backend Surface and Storage Model

Read-only research for the STU-Q author. Scope: map the FastAPI backend under `src/aws_backend/` so a net-new DTAG annotations endpoint fits existing patterns. No code was changed.

All file and line references below were read directly from the repo.

## 0. Summary for the STU orchestrator

- Nine env-backed tables exist in `config.py`. Only six are wired into the central `AwsStorage` class in `storage.py` (`sightings`, `hotspots`, `reports`, `ingestion_runs`, `community`, `decision_records`). The other three (`journal`, `partner_keys`, `managed_agents`) have their own store classes with their own boto3 `Table()` handles.
- Storage-backing recommendation (this is an O0 gate, options + recommendation only, NOT decided here): add a tenth table `orcast-dtag-annotations` behind a new `ORCAST_DTAG_ANNOTATIONS_TABLE` setting, following the existing per-domain store pattern. Rejected alternative 1: reuse `community_table` (wrong schema and lifecycle). Rejected alternative 2: the `dtag_cache` file path (a read cache, not a concurrency-safe write store).
- Exact auth pattern for an authenticated write route: route-level `dependencies=[Depends(require_api_key)]` (verifies `X-ORCAST-Key`) plus a parameter `identity: ReviewerIdentity = Depends(require_trusted_reviewer)`. `require_trusted_reviewer` checks `X-ORCAST-Trusted-Proxy == "vercel"` (in production or when an API key is configured) and requires `X-ORCAST-Reviewer-Id`. Reviewer email and role come from `X-ORCAST-Reviewer-Email` and `X-ORCAST-Reviewer-Role`. This is the same pattern used by `POST /api/decision-records` and the community approve/reject routes.
- Recommended router location: a new `src/aws_backend/routers/annotations.py`, mounted in `main.py`. Do not add a write surface to `dtag.py`, which is documented READ-ONLY and partnership-gated.

Findings file path: `/Users/gilraitses/orcast/.cca/catalogue/O0/20260629_bsw-followup-remediation/dispatch/STU/findings/STU-backend-surface.md`

## 1. The nine-table DynamoDB model

Source: `config.py` lines 14 to 22. Defaults shown are the second arg to `os.getenv`.

| Setting attr | Env var | Default name | Stores | Key schema (from usage) | Wired in `AwsStorage`? |
|---|---|---|---|---|---|
| `sightings_table` | `ORCAST_SIGHTINGS_TABLE` | `orcast-sightings` | `NormalizedSighting` rows | `pk = sighting_id` (set in `put_sightings`); read via `scan` | Yes |
| `hotspots_table` | `ORCAST_HOTSPOTS_TABLE` | `orcast-hotspots` | `Hotspot` rows | `pk = hotspot_id`; read via `scan` | Yes |
| `reports_table` | `ORCAST_REPORTS_TABLE` | `orcast-reports` | `ProbabilityReport` metadata (body JSON goes to S3 `reports_bucket`) | `pk = report_id`; `get_item(Key={"pk": ...})` | Yes |
| `ingestion_runs_table` | `ORCAST_INGESTION_RUNS_TABLE` | `orcast-ingestion-runs` | `IngestionRun` records | `pk = run_id`; `put_item` only | Yes |
| `community_table` | `ORCAST_COMMUNITY_TABLE` | `orcast-community-submissions` | `CommunitySubmission` (public sighting moderation queue) | `pk = id`; `put_item` / `get_item` / `scan`; conditional put on `status` | Yes |
| `decision_records_table` | `ORCAST_DECISION_RECORDS_TABLE` | `orcast-decision-records` | `DecisionRecord` (immutable promote/hold/reject audit) | `pk = id`; write-once `put_item` with `attribute_not_exists(pk)`; `get_item` / `scan` | Yes |
| `journal_table` | `ORCAST_JOURNAL_TABLE` | `orcast-user-journal` | `JournalEntry` (per-user private journal) | composite `pk = user_id`, `sk = "entry#{id}"`; `query` by pk, `get_item` by pk+sk | No, own store in `journal/store.py` |
| `partner_keys_table` | `ORCAST_PARTNER_KEYS_TABLE` | `orcast-partner-api-keys` | partner key hashes and per-day usage counters | `pk = "hash#{key_hash}"` and `pk = "usage#{key_id}#{day}"`; `get_item` / `update_item ADD` | No, own store in `partner/keys.py` |
| `managed_agents_table` | `ORCAST_MANAGED_AGENTS_TABLE` | `""` (empty, feature-off by default) | `ManagedAgent` specs | composite `agent_id` (pk) + `version` (sk); `query` / `get_item` / `scan` | No, own store in `casting/registry.py` |

Observations relevant to annotations:

- The dominant single-table convention is `pk = <domain>_id` with a top-level string partition key and no sort key (`sightings`, `hotspots`, `reports`, `ingestion_runs`, `community`, `decision_records`).
- Two of the three out-of-`AwsStorage` tables use a composite `pk`/`sk` to scope child rows under a parent (`journal` scopes entries under `user_id`; `managed_agents` scopes versions under `agent_id`). This is the natural shape if annotations should be scoped under a deployment.
- An annotation is a write-once or appendable child of a deployment, with reviewer attribution. It does not match the `CommunitySubmission` moderation lifecycle and it does not match the immutable single-verdict `DecisionRecord`. No existing table is a clean fit.

### Storage-backing options (O0 gate, present, do NOT decide)

Option A (recommended): new tenth table `orcast-dtag-annotations`.
- Add `annotations_table: str = os.getenv("ORCAST_DTAG_ANNOTATIONS_TABLE", "orcast-dtag-annotations")` to `Settings`, matching the nine-table pattern exactly.
- Natural key schema: composite `pk = deployment_id`, `sk = "annotation#{annotation_id}"`, mirroring the journal store. This lets a read return all annotations for one deployment with a single `query`, and keeps annotations against the simulated `cascadia_2010_k33_test` deployment partitioned with it.
- Justification: matches the established per-domain store pattern, keeps the DTAG write path isolated, and gives `query`-by-deployment for free.

Option B (rejected): reuse `community_table`.
- The `CommunitySubmission` schema is a public sighting (place, lat/lon, behavior, observer) with a PENDING/APPROVED/REJECTED moderation lifecycle and a public unauthenticated submit route. Annotations are reviewer-authored telemetry labels against a deployment. Forcing them into the community schema mixes two unrelated lifecycles and pollutes the moderation queue. Rejected.

Option C (rejected): the `dtag_cache` file path (`dtag_cache/deployments/{id}/deployment.json`, see `dtag.py` `_cache_dir`).
- This is an `@lru_cache`d read path over static JSON files on disk. It is not a write store: no concurrency safety, no idempotency primitive, no reviewer attribution, and the cache is memoized for the process lifetime so writes would not be visible without a cache reset. Rejected as a backing store.

## 2. The storage abstraction contract

Selection (`storage.py` lines 351 to 354):

```python
def build_storage(cfg: Settings = settings) -> StorageBackend:
    if cfg.storage_backend.lower() == "aws":
        return AwsStorage(cfg)
    return MemoryStorage()
```

The process-wide instance is created once in `state.py` line 19: `storage: StorageBackend = build_storage(settings)`. Routers import it as `from ..state import storage`.

How a router gets a table handle (`AwsStorage.__init__`, `storage.py` lines 204 to 219):

```python
self.dynamodb = boto3.resource("dynamodb", region_name=cfg.aws_region)
self.s3 = boto3.client("s3", region_name=cfg.aws_region)
self.sightings_table = self.dynamodb.Table(cfg.sightings_table)
...
self.community_table = self.dynamodb.Table(cfg.community_table)
self.decision_records_table = self.dynamodb.Table(cfg.decision_records_table)
```

Routers do NOT call boto3 directly. They call typed methods on the `storage` object. The DynamoDB item shape is produced by two helpers:

```python
def model_to_dict(model: Any) -> Dict[str, Any]:  # model_dump(mode="json") or .dict()
def _decimalize(value: Any) -> Any:                # float -> Decimal, recursive
```

The put/get/query API shape used against a `Table()` handle:
- Put: `table.put_item(Item=item)` where `item = _decimalize(model_to_dict(model))` and `item["pk"] = <id>`.
- Conditional put: `table.put_item(Item=item, ConditionExpression=..., ExpressionAttributeNames=..., ExpressionAttributeValues=...)`.
- Get: `response = table.get_item(Key={"pk": id})`, then `response.get("Item")`.
- Query (journal/managed_agents): `table.query(KeyConditionExpression=Key("pk").eq(...), ScanIndexForward=False, Limit=limit)`.
- Scan: `table.scan(Limit=limit)`.

The contract pattern for a new domain store, if Option A is chosen, is the three-class pattern used by `journal/store.py`, `partner/keys.py`, and `casting/registry.py`: an abstract base, a `Memory*` impl, an `Aws*` impl, and a `build_*` factory that returns the AWS impl only when `cfg.storage_backend.lower() == "aws"`.

### Offline testability (critical for STU-B)

`config.py` line 13: `storage_backend: str = os.getenv("ORCAST_STORAGE_BACKEND", "memory")`. The default is `memory`, so `build_storage` returns `MemoryStorage` with no AWS dependency. `MemoryStorage` (and every `Memory*` store) backs each table with a plain in-process dict and reproduces the same method contract as the AWS impl, including the conditional-update semantics (for example `update_community_submission_status` returns the existing row unchanged when it is no longer PENDING). A new `MemoryAnnotationStore` must mirror its AWS twin so STU-B tests exercise the same code path offline. boto3 is imported lazily inside the `Aws*` `__init__` bodies, so the memory path never imports boto3.

## 3. Auth pattern for a write route

Source: `auth.py`. Three header families, all injected by the trusted Vercel proxy after WorkOS auth:
- `X-ORCAST-Key` (the server-side API key).
- `X-ORCAST-Trusted-Proxy` (literal value `"vercel"`).
- `X-ORCAST-Reviewer-Id`, `X-ORCAST-Reviewer-Email`, `X-ORCAST-Reviewer-Role` (the stamped reviewer identity).

Dependencies (`auth.py`):

```python
def require_api_key(x_orcast_key: str | None = Header(default=None, alias="X-ORCAST-Key")) -> None: ...

def reviewer_identity(
    reviewer_id: str | None = Header(default=None, alias="X-ORCAST-Reviewer-Id"),
    reviewer_email: str | None = Header(default=None, alias="X-ORCAST-Reviewer-Email"),
    reviewer_role: str | None = Header(default=None, alias="X-ORCAST-Reviewer-Role"),
) -> ReviewerIdentity: ...

def require_signed_in(identity: ReviewerIdentity = Depends(reviewer_identity)) -> ReviewerIdentity:
    if not identity.reviewer_id:
        raise HTTPException(status_code=401, detail="Sign in required")
    return identity

def require_trusted_reviewer(
    identity: ReviewerIdentity = Depends(reviewer_identity),
    trusted_proxy: str | None = Header(default=None, alias="X-ORCAST-Trusted-Proxy"),
) -> ReviewerIdentity:
    if _production_mode() or settings.api_key:
        if trusted_proxy != "vercel":
            raise HTTPException(status_code=401, detail="Reviewer actions require trusted proxy")
    if not identity.reviewer_id:
        raise HTTPException(status_code=401, detail="Sign in required")
    return identity
```

How existing authenticated write routes use it:

- `POST /api/decision-records` (`routers/kernel.py` lines 390 to 394): route declares `dependencies=[Depends(require_api_key)]` and the handler takes `identity: ReviewerIdentity = Depends(require_trusted_reviewer)`. The handler stamps reviewer fields from `identity` and stamps gate fields server-side, never from the client body.
- `POST /api/community/submissions/{id}/approve` and `/reject` (`routers/community.py` lines 74 to 123): both `_: None = Depends(require_api_key)` and `identity: ReviewerIdentity = Depends(require_trusted_reviewer)`, then `reviewed_by=identity.reviewer_id or identity.display_name`.
- `POST /api/promotion/apply` (`routers/promotion.py` lines 44 to 48): same `require_api_key` + `require_trusted_reviewer` pair.
- `journal` router (`routers/journal.py` line 23): router-level `APIRouter(dependencies=[Depends(require_api_key)])` plus per-route `require_signed_in`. The inline comment notes `require_api_key` at the router level closes the public-tunnel bypass because `require_signed_in` alone only checks a spoofable reviewer header.

Contrast (do not copy this for annotations): `POST /api/community/sightings` (`routers/community.py` line 38) is intentionally PUBLIC and unauthenticated (it has a honeypot `website` field). The annotations POST must be authenticated, so it follows the decision-records / community-approve pattern, not the public-submit pattern.

Recommended for the annotations POST: route-level `dependencies=[Depends(require_api_key)]` and handler param `identity: ReviewerIdentity = Depends(require_trusted_reviewer)`. Stamp `reviewer_id`, `reviewer_email`, `reviewer_role` from `identity`; never trust them from the body.

## 4. Where the annotations router should live

Recommendation: new `src/aws_backend/routers/annotations.py`.

Trade-off:
- `dtag.py` is documented as a READ path. Its module docstring states it is a cache-backed READ path and that DTAG data is partnership-gated. Every route in it is a `@router.get`. Adding a `@router.post` write surface there mixes a read contract with a write contract in one file and dilutes the READ-ONLY guarantee that STU and reviewers rely on.
- A separate `annotations.py` keeps the write surface, its auth dependencies, and its store wiring isolated, and leaves `dtag.py` unchanged. It can import the deployment lookup from `dtag.py` (`_load_deployments`) to validate the target and read its `simulated` flag without taking on `dtag.py`'s read responsibilities.

`main.py` mounting note: `create_app()` (lines 51 to 92) builds the app and calls `app.include_router(...)` once per router (for example `app.include_router(dtag.router)` on line 89). A new router needs (a) an import added to the `from .routers import (...)` block (lines 10 to 31) and (b) one `app.include_router(annotations.router)` line in `create_app`. No prefix is used; each router declares full `/api/...` paths on its own decorators.

## 5. How the simulated label propagates

Source: `dtag.py`.
- The only deployment is the bundled example, hardcoded to `simulated: True`. `_load_deployments` (lines 58 to 91) sets the bundled example entry to `{"results": ..., "simulated": True, "source": "bundled_example"}`. Its `deployment_id` is `cascadia_2010_k33_test` (from `data/dtag_analysis_results.json`).
- Cache deployments are treated as real only when their payload does not flag simulated: `"simulated": bool(payload.get("simulated", False))`.
- Every response carries the flag through. `_deployment_summary` (line 99) sets `"simulated": entry["simulated"]` and `"partnership_gated": True`; `get_dives` and `get_feeding` set `"simulated": entry["simulated"]` on their envelopes.

Requirement for annotations end-to-end:
1. On `POST`, look up the target deployment with `_load_deployments().get(deployment_id)`. If absent, return the same `_not_available` shape `dtag.py` uses (partnership-gated, lists available ids).
2. Copy the deployment's `simulated` value onto the stored annotation record (do not let the client set it) and onto the POST response envelope.
3. On any annotation read route, echo the deployment `simulated` flag the same way the read routes do, so an annotation against `cascadia_2010_k33_test` stays labeled `simulated: true` in storage and in every response. Carry `taxonomy_version` (`TAXONOMY_VERSION = "unratified-0"`) and `partnership_gated: True` on the envelopes for parity with `dtag.py`.

## 6. Idempotency mechanisms in existing write routes

- Write-once conditional put (`decision_records`, `storage.py` lines 329 to 338): `put_item(Item=item, ConditionExpression="attribute_not_exists(pk)")`. An already-written `pk` cannot be silently overwritten. This is the strongest existing idempotency primitive and the natural model for an immutable annotation.
- Conditional state transition (`community`, `storage.py` lines 314 to 326): `put_item(Item=item, ConditionExpression="#st = :pending", ...)`. On `ConditionalCheckFailedException` the handler re-reads and returns the existing row instead of raising, so a double-approve is a no-op. The route layer also guards with a `409` when the row is no longer PENDING (`community.py` lines 86 to 87 and 112 to 113).
- Id assignment: every existing write route generates the id server-side. `CommunitySubmission` and `JournalEntry` use `uuid4().hex`; `DecisionRecord` uses `f"decision_{uuid.uuid4().hex[:12]}"`. No existing write route accepts a client-supplied id or a client dedup key, and gate/version fields on `DecisionRecord` are stamped server-side and explicitly not trusted from the client body (`kernel.py` lines 413 to 415).

Implication for STU-Q: there is no precedent for a client-supplied idempotency key in this backend. The two available primitives are server-generated ids plus a `attribute_not_exists(pk)` write-once put (for immutable annotations) or a conditional put on a status attribute (for mutable lifecycle). If STU-Q wants client-driven dedup, it would be a new pattern and should be flagged as such.
