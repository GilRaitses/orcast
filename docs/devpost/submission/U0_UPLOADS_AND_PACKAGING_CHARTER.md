# U0 — Evidence Uploads, Account Content, and Whitepaper Packaging

Date: 2026-06-25
Wave set: **U**
Predecessor: Wave Sets F, Q, SC complete

## Scope

Three separate but related gaps closed in a single wave set:

1. **Evidence uploads on `/ask`** — users can attach an image (camera on mobile, file on desktop) and an audio clip (recording on mobile, file on desktop) alongside a text note. Files go to S3; refs are passed to sighting assist and optionally linked to journal entries.

2. **Account content management** — a new `/account` page shows a user's journal entries, uploaded evidence assets, and published submissions in one place. Users can unlink assets.

3. **Whitepaper packaging** — content-only share PDFs (no glossary/appendix) and arXiv-compatible self-contained tarballs for both whitepapers.

## Gates

All U waves pass when:
- `POST /api/evidence/assets` accepts image, audio, and generic files, rejects anonymous callers and files over 25 MB.
- Asset chips appear on `/ask` after file selection; sighting assist response acknowledges uploaded evidence.
- `/account` lists journal entries, uploaded assets, and submission status.
- Content-only PDFs build cleanly for both whitepapers.
- Both arXiv tarballs build successfully in a clean temp directory.
- Final adversarial review in UF_UPLOADS_PACKAGING_REVIEW.md signed off.

## Execution order

U0 → U1 → U2 → U3 → U4 → U5 → U6 → U7 → UF
