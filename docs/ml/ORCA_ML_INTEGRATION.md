# orca ML tools and datasets: integration catalog

Research deliverable for orcast. Catalogs orca-focused ML systems, models, and datasets, and proposes concrete integration candidates against the existing source-adapter pipeline. Docs only; no app or backend code is changed here.

Scope and honesty are tied together throughout: orcast is a pilot study on forecast durability for orca sighting probabilities on the San Juan islands. We integrate external catalogs and feeds; we do not claim to run live ML we do not actually run. See [MAP_DATA_TRUTH.md](../ux/MAP_DATA_TRUTH.md) and [UI_COPY.md](../UI_COPY.md).

Related code:

- Adapter pattern: [`sources/base.py`](../../src/aws_backend/sources/base.py)
- Existing adapters: [`orcahello.py`](../../src/aws_backend/sources/orcahello.py), [`orcasound.py`](../../src/aws_backend/sources/orcasound.py), [`inaturalist.py`](../../src/aws_backend/sources/inaturalist.py), [`noaa.py`](../../src/aws_backend/sources/noaa.py), [`local_obis.py`](../../src/aws_backend/sources/local_obis.py)
- Pipeline and enable flags: [`state.py`](../../src/aws_backend/state.py), [`config.py`](../../src/aws_backend/config.py)

## Executive summary

What is realistically integrable now:

1. **OrcaHello detections REST API (fix in place).** Our adapter currently fails with "non-JSON content" because it points at the Blazor web UI host and a path that does not exist. The live JSON API is at a different host (`aifororcasdetections.azurewebsites.net`) and a different path (`/api/detections`). It returned 15,554 records when tested on 2026-06-19. This is a small, well-scoped fix and the highest-value near-term item. Detections must be labeled as unreviewed acoustic candidates at a hydrophone, not confirmed orca positions.
2. **Orcasound open data on AWS (no-credential S3).** Hydrophone audio and labeled datasets are public, free egress, `--no-sign-request`. Useful for an offline/batch path and for a "where you could listen" feed layer; not a live-sightings feed by itself.
3. **Orcasound live human-detection API.** `live.orcasound.net` exposes a JSON/GraphQL detections API for human reports, distinct from OrcaHello's ML detections. A clean candidate for a second acoustic-report adapter.

What is aspirational (real but heavier, or license-restricted for our use):

- **Self-running the OrcaHello SRKW detector** (Hugging Face model) on Orcasound audio. Technically feasible (PyTorch, `from_pretrained`), but it means we operate an inference service, accept GPU/compute and latency cost, and take on the OrcaHello-RAIL license obligations. Large effort and a change in what orcast claims to do.
- **Perch 2.0 embeddings + linear probe** for ecotype/call classification. Strong research direction; meaningful build and validation effort; not something to surface to users as a product claim in the pilot window.
- **Palmer et al. 2025 (DCLDE 2026) dataset** as training/eval data for any self-run classifier. Research input, not a runtime feed.
- **DTAG / biologging.** No open real-time feed; integration would require a data-sharing agreement with a research group. Keep as a partnership line, not a build item.

## Candidate table

| # | Candidate | What it is | Access method | License | Maturity | Concrete integration proposal | Effort | Honesty fit |
|---|-----------|------------|---------------|---------|----------|-------------------------------|--------|-------------|
| 1 | OrcaHello live inference + detections REST API | Real-time ML system on Orcasound audio; binary SRKW call classifier; moderator portal; public detections API | REST GET `https://aifororcasdetections.azurewebsites.net/api/detections` (v1.2, returns JSON array) | API content via Orcasound/ai4orcas; data CC BY-NC-SA 4.0 (see Orcasound registry) | Production; v1 stable, v2 portal/API in progress | Fix existing `OrcaHelloAdapter`: correct host, path, params, and parse a top-level array. Optionally pull only moderator-confirmed via `/api/detections/confirmed`. Surface as "unreviewed acoustic candidate at <hydrophone>" | S | Good, if labeled as candidate detection at a hydrophone, not a confirmed orca location |
| 2 | OrcaHello SRKW Detector V1 | ResNet50 on mel-spectrogram (1x256x312), binary orca-call classifier; PyTorch, `from_pretrained` | Hugging Face `orcasound/orcahello-srkw-detector-v1` | OrcaHello-RAIL ("other"); Be Whale Wise, no captive-industry use, no MMPA violation | Released; ported FastAI -> PyTorch (early 2026); v1 weights | Self-run inference on Orcasound S3 audio in a batch worker; write detections to our store as a source. Only if we decide to operate ML. Accept RAIL terms | L | Acceptable only if we are explicit that orcast runs this model; otherwise do not imply it |
| 3 | Orcasound open data on AWS | Live-streamed + archived hydrophone audio (HLS/FLAC) and labeled ML data | Public S3, `aws s3 ls --no-sign-request s3://audio-orcasound-net/` (also `archive-orcasound-net`, `acoustic-sandbox`) | CC BY-NC-SA 4.0 | Production; Amazon-sponsored open data | Use station/stream metadata to power a feeds layer ("listen here"); use archive/labeled buckets for any offline classifier work. Not a sightings feed on its own | S (metadata) / M (audio pipeline) | Good; it is infrastructure/audio, not a sighting claim |
| 4 | Pod.Cast annotated dataset + Watkins DB | Pod.Cast: ~15 hrs crowd-validated SRKW call annotations (TSV + WAV). Watkins (WHOI): global marine mammal recordings used to bootstrap Pod.Cast | Pod.Cast via `acoustic-sandbox` S3 (`--no-sign-request`); Watkins via WHOI website | Pod.Cast: Orcasound CC BY-NC-SA 4.0; Watkins: separate WHOI terms, non-SRKW | Stable archives | Training/eval data for a self-run classifier (candidate #2). Not a runtime feed | M (as training input) | N/A for runtime; cite as data provenance only |
| 5 | Palmer et al. 2025 (Nature) + Perch 2.0 | Palmer: DCLDE 2026 killer-whale dataset, 200k+ annotations, 3 ecotypes, AK/BC/WA. Perch 2.0: DeepMind bioacoustics foundation model; strong few-shot transfer to whale tasks | Palmer: Nature `s41597-025-05281-5` (data via DCLDE). Perch 2.0: Google/Kaggle/TF Hub model + Colab | Palmer: per-dataset (academic). Perch 2.0: per Google model terms | Research, current (2025) | Future R&D: embed Orcasound audio with Perch 2.0, linear-probe for ecotype/call type using Palmer labels. Pilot-stage research, not a user feature | L | Research only; do not present as a live orcast capability |
| 6 | OBIS, iNaturalist, NOAA | Sighting catalogs + environmental conditions | OBIS local seed JSON (active); iNaturalist REST (built, flag off); NOAA CO-OPS REST (active) | OBIS/iNat: open (CC varies by record); NOAA: public | Integrated | Already in pipeline. Near-term: enable iNaturalist live flag after a quota/quality check; keep OBIS seed as verified baseline | S | Already aligned; keep quality grades visible |
| 7 | DTAG / biologging | Animal-borne tags (movement, depth, acoustics) | No open real-time feed; by research agreement | Per provider; typically restricted/embargoed | Mature science, closed data | Keep as a partnership line on the partners page. Real integration needs a data-sharing agreement and a bespoke ingest; not a pilot build item | L (blocked on partnership) | Do not imply any current DTAG data in orcast |

## Recommended near-term integrations (ranked)

1. **Fix the OrcaHello adapter (effort S).** Re-point to the live JSON API and parse the array response. Highest value for least work; restores a source the project already advertises. Honesty: label records as unreviewed acoustic candidates at the named hydrophone, with a link to the OrcaHello audio/spectrogram. Do not present them as confirmed orca positions, and prefer the confirmed-only endpoint for any "detected" wording. See triage below.
2. **Orcasound feeds layer from open data + station metadata (effort S, metadata only).** We already ship `orcasound_hydrophones_for_orcast.json` and an `OrcasoundHydrophoneAdapter`. Tie a "listen here" feed to in-region stations only, per the region rules in MAP_DATA_TRUTH.md. No sighting claim attached.
3. **Add an Orcasound human-detection adapter (effort S/M).** `live.orcasound.net/api/json/detections` (and a GraphQL endpoint) provide human-reported detections, complementary to OrcaHello's ML detections. A second small adapter following the same pattern, clearly labeled as community/human acoustic reports.
4. **Enable the existing iNaturalist live adapter (effort S).** Code exists; the `ORCAST_ENABLE_LIVE_INATURALIST` flag is off. Turn on after verifying response quality and rate limits; keep `quality_grade` reliability weighting that is already implemented.
5. **(Aspirational, effort L) self-run OrcaHello SRKW detector on Orcasound audio.** Only if the project decides to actually operate ML inference. Requires a batch/stream worker, GPU or acceptable CPU latency, RAIL compliance, and a clear public statement that orcast runs this model. Until then, do not imply it.

## OrcaHello triage and proposed fix

### Symptom

`/health` reports: `OrcaHello returned non-JSON content; source skipped`. This is the guard in [`orcahello.py`](../../src/aws_backend/sources/orcahello.py) lines 40-47 firing because the response content-type is not JSON.

### Root cause

The adapter targets the wrong host and a non-existent path:

```19:30:src/aws_backend/sources/orcahello.py
        self.base_url = "https://aifororcas.azurewebsites.net/api"
...
            response = requests.get(f"{self.base_url}/detections/bytag/whale", params=params, timeout=12)
```

- `aifororcas.azurewebsites.net` is the Blazor **web UI** (moderator/public portal). It serves HTML, so the content-type guard correctly skips it.
- The path `/detections/bytag/whale` does not exist on the API.
- The params (`fromDate`, `toDate`, `page`, `pageSize`) and the expected response shape (`{"detections": [...]}`) do not match the real API.

The live JSON API is a separate host. Verified on 2026-06-19:

```
GET https://aifororcasdetections.azurewebsites.net/api/detections?Page=1&SortBy=timestamp&SortOrder=desc&Timeframe=all&RecordsPerPage=2
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
totalNumberRecords: 15554
totalAmountPages: 7777
```

### Corrected request

Base URL: `https://aifororcasdetections.azurewebsites.net`
Endpoint: `GET /api/detections` (Swagger title "AI For Orcas API", v1.2)

Query parameters (from the live Swagger):

| Param | Type | Notes |
|-------|------|-------|
| `Page` | int | page number (1-based) |
| `SortBy` | string | `timestamp` or `confidence` |
| `SortOrder` | string | `asc` or `desc` |
| `Timeframe` | string | `30m`, `3h`, `6h`, `24h`, `1w`, `1m`, `range`, `all` |
| `DateFrom` | string | `mm/dd/yyyy` (used when `Timeframe=range`) |
| `DateTo` | string | `mm/dd/yyyy` (used when `Timeframe=range`) |
| `Location` | string | hydrophone location name, or `all` (e.g. `Orcasound Lab`, `Port Townsend`) |
| `HydrophoneId` | string | e.g. `rpi_orcasound_lab`, or `all` |
| `RecordsPerPage` | int | page size |

Sample request that returns JSON detections:

```bash
curl -s "https://aifororcasdetections.azurewebsites.net/api/detections?Page=1&SortBy=timestamp&SortOrder=desc&Timeframe=24h&RecordsPerPage=25"
```

For a "detected orca" claim, prefer moderator-confirmed records only:

```bash
curl -s "https://aifororcasdetections.azurewebsites.net/api/detections/confirmed?Page=1&SortBy=timestamp&SortOrder=desc&Timeframe=1w&RecordsPerPage=25"
```

Related paths on the same host: `/api/detections/{id}`, `/api/detections/unreviewed`, `/api/detections/confirmed`, `/api/detections/falsepositives`, `/api/detections/unknowns`, `/api/metrics/system`, `/api/tags`.

### Response shape (the other bug)

The API returns a **top-level JSON array**, not an object with a `detections` key. Total counts are in the response **headers** (`totalNumberRecords`, `totalAmountPages`), not the body. So both the content guard and the `"detections" not in payload` check in the current adapter are wrong for this API.

A single record (real example, trimmed):

```json
{
  "id": "9bb69d69-bbd7-4079-bbd7-6593cbb47943",
  "audioUri": "https://livemlaudiospecstorage.blob.core.windows.net/audiowavs/rpi-port-townsend_2026_06_19_10_46_52_PDT.wav",
  "spectrogramUri": "https://livemlaudiospecstorage.blob.core.windows.net/spectrogramspng/rpi-port-townsend_2026_06_19_10_46_52_PDT.png",
  "location": { "name": "Port Townsend", "longitude": -122.760614, "latitude": 48.135743 },
  "timestamp": "2026-06-19T17:46:52Z",
  "annotations": [
    { "id": 1, "startTime": 14, "endTime": 17, "confidence": 0.895 },
    { "id": 2, "startTime": 26, "endTime": 29, "confidence": 0.640 }
  ],
  "reviewed": false,
  "found": "No",
  "comments": null,
  "confidence": 76.77,
  "moderator": null,
  "moderated": "0001-01-01T00:00:00",
  "tags": null
}
```

Field mapping notes for the follow-up code change (do not change code here):

- Iterate the response body directly as a list; there is no `detections` wrapper.
- Confidence is the top-level `confidence` field on a 0-100 scale (the current adapter reads `whaleFoundConfidence`, which does not exist). The existing `_normalize_confidence` divide-by-100 logic already handles the 0-100 case.
- Location is `location.latitude` / `location.longitude` and `location.name` (current adapter reads `locationName`, which does not exist). Note: this is the hydrophone position, not the orca's position.
- Review status is `reviewed` (bool) and `found` ("Yes"/"No"/unknown); there is no `state` field. Use these for labeling and for choosing the confirmed endpoint.
- `audioUri` and `spectrogramUri` are good evidence URLs.

### Headline fix recommendation

Change the OrcaHello adapter base URL from `https://aifororcas.azurewebsites.net/api` to `https://aifororcasdetections.azurewebsites.net`, call `GET /api/detections` (with `Page`, `SortBy=timestamp`, `SortOrder=desc`, `Timeframe=24h`, `RecordsPerPage`), parse the response as a top-level JSON array, and map `location.{latitude,longitude,name}`, `timestamp`, `confidence` (0-100), and `audioUri`/`spectrogramUri`. Label every record as an unreviewed acoustic candidate at the named hydrophone (or use `/api/detections/confirmed` for any "detected" wording), never as a confirmed orca position.

### v2 note

A v2 deployment exists at `https://aifororcasdetections2.azurewebsites.net`. Its `/api/detections` uses a different contract (requires `state` and `sortBy` params; returns RFC 9110 problem+json on validation errors). Target v1 for the near-term fix; revisit v2 only when its API is documented as stable.

## Honesty guardrails (what we must NOT claim)

- Do not claim orcast runs live ML detection. We consume OrcaHello's API output; we do not run the model (unless and until candidate #2 is actually built and stated plainly).
- OrcaHello detections are candidate detections at a hydrophone. Historically the unreviewed stream is dominated by false positives; most records are unreviewed. Present them as "unreviewed acoustic candidate" and prefer moderator-confirmed records for any "detected" language.
- A detection's coordinates are the hydrophone location, not the animal's location. Do not plot it as an orca position or imply a precise whale fix.
- No pod or ecotype identity unless a source field actually provides it (consistent with MAP_DATA_TRUTH.md section 4).
- Do not present Perch 2.0, Palmer 2025, Pod.Cast, or Watkins as orcast capabilities. They are external research and data; cite them as provenance only.
- Respect licenses: OrcaHello-RAIL for the model (Be Whale Wise, no captive-industry use, no MMPA violation); CC BY-NC-SA 4.0 for Orcasound open data (non-commercial, share-alike, attribution). orcast is not for commercial whale-watching fleets, which fits the non-commercial terms.
- Keep brand voice: lowercase orcast, no hype, and avoid the banned words in UI_COPY.md.

## Sources

- OrcaHello / AI For Orcas detections API (v1 Swagger): https://aifororcasdetections.azurewebsites.net/swagger/index.html
- OrcaHello v2 API: https://aifororcasdetections2.azurewebsites.net/swagger/index.html
- OrcaHello moderator/public portal: https://aifororcas.azurewebsites.net/
- OrcaHello project page: https://ai4orcas.net/orcahello/
- orcasound/orcahello repo (README): https://github.com/orcasound/orcahello
- orcasound/aifororcas-livesystem: https://github.com/orcasound/aifororcas-livesystem
- Orcasite "report detections" API issue: https://github.com/orcasound/orcasite/issues/846
- Orcasite detections API (human reports): https://live.orcasound.net/api/json/swaggerui
- Hugging Face SRKW detector v1: https://huggingface.co/orcasound/orcahello-srkw-detector-v1
- OrcaHello-RAIL license: https://github.com/orcasound/aifororcas-livesystem/blob/main/InferenceSystem/model/LICENSE
- Orcasound open data on AWS: https://registry.opendata.aws/orcasound/
- Open data registry YAML (buckets + CC BY-NC-SA 4.0): https://github.com/awslabs/open-data-registry/blob/main/datasets/orcasound.yaml
- Orcasound data access (AWS CLI, bucket migration): https://github.com/orcasound/orcadata/blob/master/access.md
- Pod.Cast data archive: https://github.com/orcasound/orcadata/wiki/Pod.Cast-data-archive
- Orca training data wiki: https://github.com/orcasound/orcadata/wiki/Orca-training-data
- Watkins Marine Mammal Sound Database (WHOI): https://whoicf2.whoi.edu/science/B/whalesounds/
- Palmer et al. 2025 (Nature Scientific Data): https://www.nature.com/articles/s41597-025-05281-5
- Perch 2.0 transfers 'whale' to underwater tasks (arXiv): https://arxiv.org/abs/2512.03219
- Perch 2.0 (Google Research blog): https://research.google/blog/how-ai-trained-on-birds-is-surfacing-underwater-mysteries/
