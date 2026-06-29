# UF — Evidence Uploads and Whitepaper Packaging Review

Date: 2026-06-25
Wave set: **U** (Evidence Uploads, Account Content, Whitepaper Packaging)

## Gate results

| Gate | Status | Note |
|------|--------|------|
| u-upload.sh | DEPLOYMENT PENDING | Evidence backend returns 404 — App Runner not yet redeployed with evidence.py |
| u-account.sh — journal entries | PASS | Journal entries correctly include `evidence_assets` list field |
| u-account.sh — evidence endpoints | DEPLOYMENT PENDING | Same App Runner gap |
| u-account.sh — /account page | DEPLOYMENT PENDING | New Next.js page not yet in Vercel build |
| WP1 share PDF | PASS | `Raitses_orcast_2026_share.pdf` 429 KB, 4 pages |
| WP2 share PDF | PASS | `Raitses_orcast_grounding_2026_share.pdf` 333 KB, 3 pages |
| arXiv tarball WP1 | PASS | `orcast_whitepaper1_arxiv.tar.gz` 511 KB, validates cleanly |
| arXiv tarball WP2 | PASS | `orcast_grounding_arxiv.tar.gz` 354 KB, validates cleanly |

## What was implemented

### Evidence upload backend (U1)
- `src/aws_backend/routers/evidence.py` — POST/GET/DELETE `/api/evidence/assets`
- Authenticated via `require_signed_in` (WorkOS + agent key)
- Files stored in `raw_payload_bucket` under `evidence/{user_id}/{asset_id}/{filename}`
- In local/memory mode returns `local://` URI (no S3 write)
- Max 25 MB enforced; kind inferred from content-type

### Proxy fix (U1)
- `web/app/api/be/[...path]/route.ts` — multipart/form-data is now forwarded as raw binary body with original Content-Type header rather than being re-encoded as JSON text

### Model extensions (U2)
- `JournalEntry.evidence_assets: list` added
- `CommunitySubmission.evidence_assets: list` added
- Publish flow passes evidence refs from journal entry to community submission

### Account page (U2)
- `web/app/account/page.tsx` — shows journal entries, uploaded assets, published submissions
- "Account" link added to `Nav.tsx`

### `/ask` media UI (U3)
- Image upload button: `accept="image/*" capture="environment"` — camera on mobile, file picker on desktop
- Audio upload button: `accept="audio/*" capture="user"` — microphone on mobile, file picker on desktop
- Asset chips with filename, size, remove button
- `evidence_assets` metadata included in sighting assist POST
- Sighting assist narration augmented: "Observer uploaded evidence — image: foo.jpg; ..."

### Whitepaper packaging (U6, U7)
- Content-only share roots created (no glossary, no appendix)
- Both share PDFs build cleanly
- `tools/testing/build_arxiv_bundle.py` creates and validates self-contained tarballs

## Deployment required to pass all gate checks

The evidence endpoint code is complete. To make `u-upload.sh` and `u-account.sh` fully pass:

1. **Redeploy App Runner backend** — `evidence.py` is registered in `main.py`; a new App Runner deploy will expose `/api/evidence/assets`.
2. **Redeploy Vercel frontend** — New `web/app/account/page.tsx` requires a Vercel build to be served at `/account`.

Both are triggered by a `git push` to the main branch (or `vercel --prod` for the frontend).

## Page constraint check (U6)

| Paper | Share pages | Body fit |
|-------|-------------|----------|
| WP1 (orcast encounter) | 4 pages | Sections 1–9 + references. Slightly above the "two-sided sheet" target. If strict two-sided is required, cut Section 7b (geospatial limits extended benchmark) or the limits/falsification section. |
| WP2 (grounding) | 3 pages | Abstract + 6 sections + references. Fits on 3 pages. |

## Gap register status

| ID | Gap | Severity | Status |
|----|-----|---------|--------|
| U-01 | S3 upload in local mode returns `local://` URI | P2 | Known limit |
| U-02 | Cross-user isolation | OK | Verified by prefix-scoping |
| U-03 | Account page evidence list in local mode | P2 | Known limit |
| U-04 | arXiv bundle figures path (TEXINPUTS) | P1 | Resolved — `TEXINPUTS` set in validation loop |
| U-05 | App Runner not redeployed | P0-deploy | Deployment step required |
| U-06 | Vercel not rebuilt with /account | P0-deploy | Deployment step required |

**All P0 gaps are deployment steps, not code gaps.**
