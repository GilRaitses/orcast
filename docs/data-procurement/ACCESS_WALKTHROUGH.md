# Data Access Walkthrough

Step-by-step access for each upstream data source: signup URLs, token handling,
request-email templates, and license caveats. This complements
[ACCOUNT_REQUESTS.md](ACCOUNT_REQUESTS.md) and [SOURCE_DECISIONS.md](SOURCE_DECISIONS.md).

Secrets rule: tokens live ONLY in env/secret stores (App Runner secret + local
`.env.local`). Never commit a token value to any tracked file. Rotate any token
that was ever shared in plaintext.

---

## 1. Orcasound (public, no account)

- Audio buckets: `aws s3 ls --no-sign-request s3://audio-orcasound-net/`
- Labeled data: `s3://acoustic-sandbox` (annotated bouts, broadband/PSD).
- Station roster (already wired): `https://live.orcasound.net/api/json/feeds`.
- License: confirm bulk-redistribution terms with Orcasound / AI4Orcas before
  republishing audio. Station coordinates and roster are safe to display.

## 2. OrcaHello / AI4Orcas (public read; partly wired)

- Detections API host: `https://aifororcasdetections.azurewebsites.net`.
- Endpoints: detections, confirmed, false-positive. Confidence is 0-100 (we
  rescale to 0-1). Treat unreviewed detections as candidates, not confirmed orca
  positions.
- Caveat: the Azure backend intermittently returns 403/stops; treat as optional.

## 3. Ocean Networks Canada — Oceans 3.0 (token provided; actionable now)

Token handling:
- Store as `ONC_API_TOKEN` (App Runner secret + local `.env.local`). Set
  `ORCAST_ENABLE_ONC=true` to activate the adapter. The value is never written to
  a tracked file and is never returned to the browser; spectrogram bytes are
  proxied through `/api/onc/archivefile`.
- Operator action: rotate the token after the hackathon (it was shared in
  plaintext).

Steps:
1. Validate discovery:
   `GET https://data.oceannetworks.ca/api/locations?deviceCategoryCode=HYDROPHONE&token=...`
   to list Salish Sea hydrophone locations + `locationCode`s.
2. List recent spectrogram PNGs:
   `GET https://data.oceannetworks.ca/api/archivefile/location?locationCode=...&deviceCategoryCode=HYDROPHONE&dateFrom=...&dateTo=...&extension=png&token=...`
3. Download a file (server-side only):
   `GET https://data.oceannetworks.ca/api/archivefile/download?filename=...&token=...`
   (MAT/FFT spectrograms: `dataProductCode=HSD`, product 146.)
4. Annotations: SeaTube annotation export (data product 126) / Annotation File
   (89), WoRMS taxonomy. Annotation submission in-app is auth-gated.

Adapter: [`src/aws_backend/sources/onc.py`](../../src/aws_backend/sources/onc.py),
route [`src/aws_backend/routers/onc.py`](../../src/aws_backend/routers/onc.py).
Without the token the panel degrades to station metadata only.

## 4. SanctSound / NCEI (public)

- Immediate: GCS bucket `noaa-passive-bioacoustic`.
- Async: "Request Data from NCEI" form (name / org / email).
- Caveat: mostly non-Salish sites — context/benchmark only.

## 5. Request-only sources (email/account)

Each needs a contact step before data flows; quote the templates in
[ACCOUNT_REQUESTS.md](ACCOUNT_REQUESTS.md):

| Source | Access path | Caveat |
|--------|-------------|--------|
| Happywhale | Account + research/export request | Reuse terms per request |
| Acartia / The Whale Museum | Request API token + docs | Token in env only |
| Orca Network | Email research request for structured export | Confirm reuse terms |
| Center for Whale Research | Research request | No public API |
| SeaStats / Orcanode | Confirm station-key mapping + uptime API | Station mapping |

## 6. Not an API (partnership only)

DTAG / Cascadia / NWFSC and Oceans Initiative require a data-sharing agreement;
there is no programmatic endpoint. Track under partnerships, not ingestion.
