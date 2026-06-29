# BSW-R01 - Orcasound archived audio

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent c2d1c311; written by the BSW sub-orchestrator.

## Summary

- Orcasound hydrophone audio is public on AWS S3 (`us-west-2`), no credentials; in-repo catalogs name `audio-orcasound-net` as the current production bucket per node (`node_name`, `slug`, coords in `live_orcasound_feeds.json`).
- Archived live-stream lossy audio is HLS: `{bucket}/{node}/hls/{unix_session_start}/live.m3u8` plus `live*.ts` segments (~10 s, AAC in MPEG-TS); a proven in-repo pipeline decodes **48 kHz AAC -> PCM** for spectrogram work (`OS1_BUILD_NOTE.md`).
- Lossless FLAC archives live in `archive-orcasound-net` (legacy registry) and are migrating into `audio-orcasound-net`; labeled ML bouts are in `acoustic-sandbox`.
- License is **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)** - contains **NonCommercial (NC)** and **ShareAlike (SA)**. Per BSW hard rules: **STOP-to-O0** before any demo that redistributes audio, trains/ships models on it, or uses it in a commercial context without operator sign-off.
- orcast already serves station metadata + `streamUrl` (live listen page only); `SalishScene.tsx` emits `streamUrl` on hydrophone click but `AdaptiveExplore.tsx` drops it from the panel props - archived S3/HLS is not wired end-to-end yet.
- **Recommended slice:** station **Orcasound Lab** (`rpi_orcasound_lab`), clip **2021-08-25 S10 L-pod SRKW bout**, HLS session **`1629941419`**, highlight window **~19:26:56-19:29:41 Pacific** (~2 min 45 s of measured hydrophone audio with human + OrcaHello SRKW confirmation).

## In-repo findings (cited file:line)

| Finding | Citation |
|--------|----------|
| `OrcasoundHydrophoneAdapter` reads static JSON, maps coords, sets `streamUrl` to live listen page (not S3 archive) | `src/aws_backend/sources/orcasound.py:52` |
| `GET /api/live-hydrophones` returns filtered static catalog; `live_status_check: false` | `src/aws_backend/routers/read.py:186-202` |
| Nine nodes; production bucket `audio-orcasound-net` (dev node uses `dev-streaming-orcasound-net`); Orcasound Lab `id: rpi_orcasound_lab`, `slug: orcasound-lab`, SRKW-focused description | `src/integrations/orcasound_hydrophones_for_orcast.json:113-125` |
| Feeds API snapshot: `node_name`, `slug`, `bucket`, `bucket_region: us-west-2`, GeoJSON coords; self URL `https://live.orcasound.net/api/json/feeds` | `src/integrations/live_orcasound_feeds.json:383-411,490-492` |
| `STATION_COORDS` maps modeling keys to Orcasound Lab / North SJC / Andrews Bay / Haro Strait | `modeling/studies/common.py:24-29` |
| Scene click emits hydrophone `SceneIntent` including `streamUrl` | `web/app/components/scene/SalishScene.tsx:1083-1091` |
| Console panel gets `station/lat/lng` only - **`streamUrl` dropped** | `web/app/components/AdaptiveExplore.tsx:237-244` |
| `SceneIntent` / `HydrophoneNode` types include optional `streamUrl` | `web/lib/sceneIntent.ts:7-14,35-43` |
| S3 path layout used in proven DSP: `s3://audio-orcasound-net/<node>/hls/<session_ts>/live*.ts`; **48 kHz AAC** -> ffmpeg -> Welch PSD | `.cca/catalogue/O0/20260627_open-science-integration/OS1_BUILD_NOTE.md:68-72` |
| ML integration doc: buckets `audio-orcasound-net`, `archive-orcasound-net`, `acoustic-sandbox`; license **CC BY-NC-SA 4.0** | `docs/ml/ORCA_ML_INTEGRATION.md:34` |
| Access walkthrough: public list/read; **confirm bulk redistribution with Orcasound before republishing audio**; station coords safe to display | `docs/data-procurement/ACCESS_WALKTHROUGH.md:13-19` |
| BSW stack locked to **three + WebAudio**; honesty: audio/DTAG = **measured** | `wave_shape.yml:26` |
| BST charter: bind real `streamUrl`/archived audio; no invented stream | `BSW-STATION_CHARTER.md:36-37` |
| BRE reenactment uses **separate** measured DTAG driver (`orca_srkw_oo14_driver.bin`, Tennessen CC-BY-4.0) - kinematics not derived from hydrophone clip | `BSW-REENACTMENT_CHARTER.md:17-18` |
| Orcasound Lab dominates served OrcaHello detections (~1029) in prior ingest work | `.cca/catalogue/O0/20260627_mlops/research/forward/G1_ingest_deploy.md:277` |

**Grep sweep:** 80+ in-repo `orcasound` references across `src/`, `docs/`, `modeling/`, `.cca/catalogue/` - no in-repo code fetches archived `.ts`/`.m3u8` today; only metadata adapters and research notes.

## External findings (S3/HLS layout, formats, sample rate, license URL)

### Bucket layout (migration-aware)

| Bucket | Role | Region | Access |
|--------|------|--------|--------|
| `audio-orcasound-net` | **Current** raw audio (HLS lossy + growing FLAC) | `us-west-2` | `aws s3 ls --no-sign-request s3://audio-orcasound-net/` |
| `audio-deriv-orcasound-net` | Processed derivatives | `us-west-2` | Quilt: https://open.quiltdata.com/b/audio-deriv-orcasound-net/tree/ |
| `streaming-orcasound-net` | **Legacy** HLS production archive (~2018-2024 migration) | `us-west-2` | Registry + access.md |
| `archive-orcasound-net` | **Legacy** lossless FLAC | `us-west-2` | Registry |
| `dev-streaming-orcasound-net` | Dev/test HLS only | `us-west-2` | In-repo: Andrews Bay test node |
| `acoustic-sandbox` | Labeled bouts, Pod.Cast, ML artifacts | `us-west-2` | Registry |

**HLS object layout** (documented in Orcasound `access.md` and 2021 bout blog):

```
s3://{bucket}/rpi_{node_slug}/hls/{unix_session_start}/live.m3u8
s3://{bucket}/rpi_{node_slug}/hls/{unix_session_start}/live{N}.ts   # ~10 s segments
```

Example manifest URL pattern (orcanode README):
`https://s3-us-west-2.amazonaws.com/dev-streaming-orcasound-net/rpi_seattle/hls/1526661120/live.m3u8`

**Session folders** are 6-hour rolling windows keyed by Unix timestamp when the folder opened.

### Formats and sample rate

| Layer | Format | Sample rate / segment | Source |
|-------|--------|----------------------|--------|
| HLS lossy (primary archive for most nodes) | **AAC-LC in MPEG-TS** (`.ts`), HLS v3 manifest (`.m3u8`) | **48 kHz**, **mono** (typical), **10 s** segments | orcanode `SAMPLE_RATE=48000`, `SEGMENT_DURATION=10` (orcasound/orcanode README); ambient-sound-analysis-api specifies mono 48 kHz PCM after decode |
| Lossless archive | **FLAC** (per-file, not HLS) | Native hydrophone rate (typically 48 kHz) | `archive-orcasound-net` / migrating to `audio-orcasound-net` |
| Labeled ML | WAV/TSV bouts (Pod.Cast), etc. | Varies | `acoustic-sandbox` |

In-repo confirmation of decode target: **48 kHz AAC segment -> ffmpeg decode -> scipy Welch** (`OS1_BUILD_NOTE.md:68-72`).

### License (exact)

- **Name:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
- **URL:** https://creativecommons.org/licenses/by-nc-sa/4.0/
- **Registry:** https://github.com/awslabs/open-data-registry/blob/main/datasets/orcasound.yaml
- **Attribution requested by Orcasound:** `"Orcasound - orcasound.net"`
- **NC clause (legal code 1k):** use must not be *primarily intended for or directed toward commercial advantage or monetary compensation*

## License & privacy verdict (OPEN / STOP-to-O0, with reasoning)

### Verdict: **STOP-to-O0** (not OPEN)

1. **NC present:** CC BY-NC-SA 4.0 explicitly restricts non-commercial use. BSW rules treat NC/ND/unclear -> STOP-to-O0.
2. **SA present:** Adapted material (spectrogram tiles, trained weights, re-hosted clips) must be shared under compatible NC-SA terms - affects model artifact distribution via S3 box.
3. **In-repo caution already recorded:** `ACCESS_WALKTHROUGH.md` says confirm bulk redistribution with Orcasound/AI4Orcas before republishing audio; coords/roster only are safe without negotiation.
4. **OK without STOP (metadata-only):** station names, lat/lng, slug, live listen links, OrcaHello detection timestamps as *candidates* - all already in orcast catalogs.
5. **Privacy:** Hydrophone audio is ambient ocean sound; no PII in the recommended clip.

**Operator action before BSW-BUILD audio playback, spectrogram HUD, or model training on this clip:** confirm orcast's use qualifies as non-commercial research/demo under NC, document attribution string, and decide whether a small cached excerpt in the S3 box is acceptable under SA.

## Recommended station + real clip for the slice (provenance, URL, license, why this clip)

### Station: **Orcasound Lab**

| Field | Value |
|-------|--------|
| Display name | Orcasound Lab |
| Node id | `rpi_orcasound_lab` |
| Slug | `orcasound-lab` |
| Coords | 48.5583362, -123.1735774 (Haro Strait, west San Juan Island) |
| Bucket (catalog) | `audio-orcasound-net` |
| Live listen (in-repo `streamUrl`) | `https://live.orcasound.net/listen/orcasound-lab` |
| Modeling key | `orcasound_lab` in `STATION_COORDS` |

**Why this station:** SRKW core summer habitat (catalog description); highest OrcaHello detection density in served ingest (~1029 detections); OS1 DSP pipeline already proven on this node; aligns with BRE DTAG SRKW driver (separate kinematic asset) and Salish scene beacon placement.

### Clip: **2021-08-25 L-pod SRKW bout (S10 calls)**

| Field | Value |
|-------|--------|
| Event | Southern Resident killer whales (L pod); diverse calls + clicks ~40 min bout |
| Human + machine confirmation | OrcaHello + live listeners; Center for Whale Research / L54 matriline context |
| HLS session start (Unix) | **`1629941419`** (= Wed 2021-08-25 18:30:19 Pacific, 6-hour folder) |
| Bout label (Orcasound) | `210825_1922-2007_OS_SRKW_L` |
| OrcaHello first detection | **19:25:07** Pacific |
| **Recommended demo window** | **~19:26:56-19:29:41** Pacific (~2 min 45 s highlight with strong S10 calls, low vessel noise) |
| Offset within session | ~56:37-59:22 into concatenated session audio (per blog) |

**Provenance chain (verifiable, no stand-in):**
1. Measured hydrophone recording -> S3 HLS segments (not synthesized).
2. Published analysis: "Exciting (S10) L pod calls as the sun sets over Orcasound Lab" (https://www.orcasound.net/2021/08/25/exciting-s10-l-pod-calls-as-the-sun-sets-over-orcasound-lab/) - documents Unix folder, bout times, OrcaHello detections, and download recipe (`ts2mp3.sh orcasound_lab 1629941419`).
3. Cross-check: OrcaHello "true positive" detection list linked from that post (first 19:25:07, last 20:04:28).

**URLs (try new bucket first, then legacy):**

| Resource | URL |
|----------|-----|
| HLS manifest (new bucket) | `https://s3-us-west-2.amazonaws.com/audio-orcasound-net/rpi_orcasound_lab/hls/1629941419/live.m3u8` |
| HLS prefix (CLI) | `s3://audio-orcasound-net/rpi_orcasound_lab/hls/1629941419/` |
| HLS prefix (legacy, 2021-era docs) | `s3://streaming-orcasound-net/rpi_orcasound_lab/hls/1629941419/` |
| Quilt browser | https://open.quiltdata.com/b/audio-orcasound-net/tree/ |
| Blog / bout narrative | https://www.orcasound.net/2021/08/25/exciting-s10-l-pod-calls-as-the-sun-sets-over-orcasound-lab/ |
| License | CC BY-NC-SA 4.0 - https://creativecommons.org/licenses/by-nc-sa/4.0/ |

**Honesty flags:**
- **Measured:** HLS `.ts` audio from Orcasound Lab hydrophone.
- **Not measured from this clip:** DTAG orca swim kinematics (`oo14` driver) - separate Tennessen deployment; BRE must label as measured DTAG, not inferred from this audio.
- **Cannot be faked:** Classifier outputs on this slice must come from a real model run on decoded PCM; do not script detections to match blog labels. OrcaHello timestamps are independent reference, not orcast ground truth unless ingested via `OrcaHelloAdapter`.
- **Timing caveat:** Blog notes possible ~10 min HLS segment-boundary clock drift vs OrcaHello absolute times - align demo playhead to **audio content** (S10 calls in spectrogram), not wall-clock alone.

**Secondary candidate (if 2021 bucket empty after migration):** L90 + calf, 2024-09-17 (https://www.orcasound.net/2024/09/17/l90-and-her-new-calf-vocalize-echolocate-alone/) - rarer isolated SRKW vocalization; session timestamp must be resolved from live archive. Prefer 2021 bout for pre-published Unix key + OrcaHello crosswalk.

## Recommendations with cost + standin-free fallback

| # | Recommendation | Cost | Standin-free fallback |
|---|----------------|------|------------------------|
| 1 | **Wire archived playback:** resolve `bucket` + `node_name` from `live_orcasound_feeds.json`, construct `{bucket}/{node}/hls/{session}/live.m3u8`, fetch/decode via **WebAudio** | **S** eng; **$0** AWS egress (sponsored open data); client CPU for FFT/decode | If NC blocks: show station pin + bout metadata + listen link only - **no synthetic waveform** |
| 2 | **Demo clip window:** decode segments covering **19:26:56-19:29:41** Pacific from session `1629941419` (~17-20 `.ts` files ~3-4 MB egress) | minutes dev time; negligible bandwidth | If manifest 404: list `audio-orcasound-net` then `streaming-orcasound-net` prefix; browse Quilt; use blog-hosted `.ogg` excerpt only as **last-resort** (still real audio) |
| 3 | **Pass `streamUrl` through intent -> panel -> player** (`AdaptiveExplore.tsx` props) | **S** | Fallback: hardcode listen URL for Orcasound Lab from catalog |
| 4 | **Spectrogram (BSH):** WebAudio/AudioWorklet FFT on decoded PCM from same clip | **M**; no new server dep | ONC PNG spectrogram proxy is **not** a fallback - requires `ONC_API_TOKEN`, different source |
| 5 | **Classifier (BAM):** train/eval on Pod.Cast + this clip holdout; report honest SRKW-call presence / call-type only | **L**; box storage for weights | No canned detections; if NC blocks training: run **OrcaHello API** confirmed detections as read-only reference overlay (candidate labels, not orcast model output) |
| 6 | **Reenactment (BRE):** scrub-sync `track.sample(t)` on existing **oo14** DTAG driver; spawn count from BAM | **M** integrate | Never drive orca mesh from spectrogram alone; if BAM blocked, single orca with measured DTAG path only |
| 7 | **Attribution UI:** persistent "Audio: Orcasound (CC BY-NC-SA 4.0)" + link to bout blog | **S** | Required for license compliance regardless of playback |
| 8 | **Cache clip in S3 box** after operator NC sign-off | ~5 MB box storage; one-time egress | Re-fetch from public S3 via documented prefix - no git binary |

## Open questions for O0

1. **NC scope:** Does the orcast.org demo / hackathon / research posture qualify as non-commercial under CC BY-NC-SA for embedded playback, cached box excerpt, and a shipped small classifier artifact?
2. **Bucket authority for session `1629941419`:** Has this 2021 folder been copied to `audio-orcasound-net`, or must the slice read from legacy `streaming-orcasound-net`? (Needs one `aws s3 ls` check at build time.)
3. **`streamUrl` semantics:** Should BST player use live HLS from current session, fixed archived session URL, or operator-picked bout ID - and who owns session discovery UX?
4. **Classifier ground truth:** Is OrcaHello human-confirmed label on this bout sufficient reference, or must Pod.Cast/community TSV labels be the training source?
5. **ShareAlike on model weights:** If acoustic model weights are derived from NC-SA audio, must published box artifacts carry SA-compatible licensing text?
6. **Orcasound Lab live status:** Catalog `visible: true` but 2024-2025 outages noted; is live listen required for demo, or archive-only slice?
7. **Commercial downstream:** Any plan to monetize orcast features that play this audio triggers hard STOP until Orcasound grants alternate terms.

## Sources

### In-repo (verified at `/Users/gilraitses/orcast`, commit `240570e`)
- `src/aws_backend/sources/orcasound.py`, `src/aws_backend/routers/read.py`, `src/aws_backend/state.py`
- `src/integrations/orcasound_hydrophones_for_orcast.json`, `src/integrations/live_orcasound_feeds.json`
- `web/app/components/scene/SalishScene.tsx`, `web/app/components/AdaptiveExplore.tsx`, `web/lib/sceneIntent.ts`
- `modeling/studies/common.py`, `docs/ml/ORCA_ML_INTEGRATION.md`, `docs/data-procurement/ACCESS_WALKTHROUGH.md`
- `.cca/catalogue/O0/20260627_open-science-integration/OS1_BUILD_NOTE.md`
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/{wave_shape.yml,BSW-STATION_CHARTER.md,BSW-ACOUSTIC-ML_CHARTER.md,BSW-REENACTMENT_CHARTER.md}`

### External

| Source | URL | License / terms |
|--------|-----|-----------------|
| AWS Open Data Registry | https://registry.opendata.aws/orcasound/ | CC BY-NC-SA 4.0 |
| Registry YAML | https://github.com/awslabs/open-data-registry/blob/main/datasets/orcasound.yaml | CC BY-NC-SA 4.0 |
| Orcasound data access | https://github.com/orcasound/orcadata/blob/master/access.md | CC BY-NC-SA 4.0 |
| CC BY-NC-SA 4.0 Legal Code | https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode | NC + SA + BY |
| orcanode (48 kHz / 10 s HLS) | https://github.com/orcasound/orcanode/blob/master/README.md | OSS (check repo license for software, not audio) |
| 2021 SRKW bout blog | https://www.orcasound.net/2021/08/25/exciting-s10-l-pod-calls-as-the-sun-sets-over-orcasound-lab/ | Audio CC BY-NC-SA; attribution Orcasound |
| Quilt `audio-orcasound-net` | https://open.quiltdata.com/b/audio-orcasound-net/tree/ | Same dataset license |
| OrcaHello / AI4Orcas | https://ai4orcas.net/orcahello/ | Detections API separate; training data NC-SA |
