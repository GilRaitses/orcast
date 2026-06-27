# STEP_LOG, BSIDE whale-tagger build

All times America/New_York.

## 2026-06-27

- Chartered family BSIDE from ORCAST_BSIDE_DESIGN.md section 6.
- B-API (done): added `src/aws_backend/routers/dtag.py`, a cache-backed read path over
  `data/dtag_analysis_results.json` (simulated example) and `dtag_cache/deployments/`.
  Endpoints: `/api/dtag/deployments`, `/api/dtag/deployments/{id}`, `/api/dtag/dives/{id}`,
  `/api/dtag/feeding/{id}`. Registered in `main.py`; updated the deprecated `/api/dtag-data`
  410 hint to point at the new surface. Classifier returns `not_trained` with the
  uniform-probability caveat; deployments flagged `simulated`. Tests in
  `tests/aws_backend/test_dtag.py` (6 passed).
- Registered BSIDE in `docs/devpost/waves.registry.yaml` and `WAVES_REGISTRY.md`.

## Open / awaiting operator

- B-SKILLS..B-MCP are chartered and sequenced; B-INGEST needs a partnership agreement.
- Commit/push only on explicit request.
