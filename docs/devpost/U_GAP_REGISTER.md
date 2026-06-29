# U — Evidence Uploads Gap Register

Updated: 2026-06-25
Status: Wave Set U in progress

## Severity key
- P0: Breaks user-visible upload or account flow
- P1: Feature gap that degrades the experience
- P2: Minor polish

| ID | Surface | Finding | Severity | Status |
|----|---------|---------|---------|--------|
| U-01 | S3 upload in local mode | In local/memory mode, upload returns `local://` URI; file bytes not persisted. Acceptable for demo; label as known limit. | P2 | known limit |
| U-02 | Cross-user isolation | Evidence DELETE uses prefix `evidence/{owner_id}/` to scope; anonymous and wrong-user deletes return 401/404. Confirmed in u-account gate. | OK | verified |
| U-03 | Account page auth | /account shows "not available" gracefully for evidence list when ORCAST_AGENT_KEY not present in local mode. | P2 | known limit |
| U-04 | arXiv bundle figures | Figures copied by build_arxiv_bundle.py use relative paths; standalone build may need TEXINPUTS adjustment. | P1 | open |
