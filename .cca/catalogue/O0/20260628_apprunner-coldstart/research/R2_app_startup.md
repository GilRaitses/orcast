# R2: In-app startup and readiness grounding

**Lane:** WS-COLDSTART CS1-R2 (agent `6ff02d7c-6f9f-4fff-be11-c56f286ceccb`)
**Scope:** `src/aws_backend/` startup, `/health`, explore/interactions paths, Aurora/Bedrock init
**Verdict:** `/health` is liveness-only and never probes Aurora; explore DB and Bedrock are lazy per request with no pool. A fresh instance can pass App Runner health while explore returns 503 (DB unreachable) or 404 (session not found after a failed create). No `/ready` endpoint exists.

## 1. Startup timeline

Import (before uvicorn binds): `config.settings` (env only) → 20 routers → eager `storage = build_storage(settings)` (`state.py:19`, boto3 DynamoDB/S3 client handles, no API calls) → eager store singletons (`interactions.py:27`, `managed_agents.py:15`, `journal.py:24`, `partner.py:14`). Explore + interactions routers mount unconditionally:

```82:84:src/aws_backend/main.py
    app.include_router(explore.router)
    app.include_router(managed_agents.router)
    app.include_router(interactions.router)
```

Lifespan (blocks readiness):

```38:48:src/aws_backend/main.py
@asynccontextmanager
async def lifespan(_: FastAPI):
    if not storage.list_sightings(limit=1):
        run_ingestion(include_live=False)
    try:
        from .exploration.migrate import run_pending_migrations

        run_pending_migrations()
    except Exception:
        pass
    yield
```

- Step A `run_ingestion(include_live=False)` only if DynamoDB has zero sightings (heavy: 5-60s; skipped in steady prod).
- Step B `run_pending_migrations()` opens one psycopg connection per migration file (4 files); first VPC→RDS TCP+TLS can add multi-second latency (`db.py:41,44`, `connect_timeout: 5`).
- Step C bare `except Exception: pass` (`main.py:46-47`) hides DB/migration failure; process still starts, explore fails later.
- Not warmed: Bedrock client, Aurora connectivity probe, connection pool, managed-agent read.

## 2. `/health` is liveness-only

```122:124:src/aws_backend/routers/read.py
@router.get("/health")
def health() -> Dict[str, Any]:
    return _health_payload()
```

`_health_payload()` (`read.py:70-90`) reads in-memory ingestion status + scans up to 10k sightings + 1k hotspots from DynamoDB. It does **not** touch Aurora or Bedrock. App Runner health points at `/health` (`infra/aws/template.yaml:712-718`, interval 10s, healthy threshold 1), so one `/health` 200 marks an instance ready with no explore dependency. Result: `/health` can stay 200 while explore is unreachable. (Per-probe DynamoDB scans are also wasteful at a 10s cadence.)

## 3. Explore + interactions are lazy, no pool

`db.py` opens and closes a new connection per op; no `ConnectionPool`:

```63:70:src/aws_backend/exploration/db.py
@contextmanager
def get_connection() -> Iterator["psycopg.Connection"]:
    if not aurora_configured():
        raise RuntimeError("ORCAST_DATABASE_URL is not configured")
    if psycopg is None:
        raise RuntimeError("psycopg is not installed")
    with psycopg.connect(**_connect_kwargs()) as conn:
        yield conn
```

Explore maps connection failures to 503 (`explore.py:16-30,46-51`); interactions does **not** catch DB-unreachable, so those bubble as 500 (`interactions.py:184+`). App 404 is `"Session not found"` (`explore.py:63-64`, `interactions.py:184-185`) or a managed-agent `LookupError` (`interactions.py:200-201`). Cold-start chain: `POST /api/explore/sessions` 503 (RDS cold) → client reuses an unpersisted session_id → 404 "Session not found".

Bedrock is created per call (`guide.py:172-196`, `_bedrock_guide_stream` `guide.py:217-224`); first narration pays client construction + credential resolution + TLS (latency, not 404).

`/api/explore/status` probes live `SELECT 1` each call with no cache (`db.py:48-60`), returns 200 even when unreachable with `aurora_connected:false`, `exploration_backend:"unreachable"` (`session_store.py:17-31`). Can report a transient false on a cold instance (VPC/RDS cold within the 5s connect timeout).

## 4. Readiness vs liveness

No `/ready` exists. Recommendation: split liveness (`/health`, lightweight) from readiness (`/ready`, returns 200 only when `aurora_configured()` and `aurora_connected()`, optionally managed-agent get + Bedrock client constructed), and point App Runner `HealthCheckConfiguration.Path` at `/ready`. Add a lifespan pre-warm after migrations (open the pool / `aurora_connected()`, construct `boto3.client("bedrock-runtime")`), and replace per-request connects with a lifespan-opened `psycopg_pool.ConnectionPool`. Convergence points: `main.py:38-48` (lifespan), `read.py` (add `/ready`), `infra/aws/template.yaml:712-718` (health path), `exploration/db.py` (pool).

## 5. Five-point summary

1. Lazy items that can 503/404/timeout on a cold instance: Aurora (new connect per call, no pool, 5s timeout) and Bedrock (per-invoke client). Explore maps DB errors to 503; interactions to 500; app 404 is "Session not found" / missing agent, often after a failed create in the 503 window.
2. `/health` should NOT be the readiness gate: it is liveness-only (DynamoDB + in-memory), never probes Aurora (`read.py:70-90`), so instances take traffic before explore is warm.
3. Pre-warm + `/ready` go in `main.py` lifespan (`38-48`) + `read.py`; point App Runner health at `/ready` (`template.yaml:712-718`).
4. Heaviest startup: conditional `run_ingestion` (empty DynamoDB), else 4-connection migrations; per-probe `/health` DynamoDB scans.
5. Highest-leverage app change: add `/ready` gated on `aurora_connected()` + lifespan Aurora pre-warm, and switch the App Runner health path to `/ready` so "healthy" means "explore serveable".

> Note: R4 found the observed 404/503 was generated at the App Runner EDGE during instance handover (not in app logs). The `/ready` work fixes a distinct, real "instance healthy but explore cold" 500/503 path; it does not by itself fix the edge-handover 404 (that needs warm-pool + client retry).
