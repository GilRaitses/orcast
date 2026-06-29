# BSW-R02 - Community annotation corpora

> Read-only research finding (BSW-RESEARCH wave). Repo verified against `240570e`.
> Authored by explore agent 72ed1592; written by the BSW sub-orchestrator.

## Summary

- **No candidate corpus in this set provides an honest, license-clear path to "how many orcas" (source-count) labels.** All are segment-level call detections, ecotype/presence, or moderator yes/no - not multi-source enumeration.
- **DCLDE-2027 (Palmer et al. 2025) is the strongest OPEN corpus** for BAM acoustic training: >225k call-level bounding-box annotations, collated `Annotations.csv` with ecotype (`SRKW`, `NRKW`, `TKW`, etc.), ~1.6 TB audio, CC-BY-4.0 on the NOAA open-data artifact (verified in-repo via OS2/TB4).
- **Orcasound Pod.Cast rounds and OrcaHello moderated data are SRKW-relevant but license-blocked for BAM** under charter rules: Orcasound open-data registry is **CC BY-NC-SA 4.0**; BSW locked decision says NC/ND/unclear -> STOP to O0.
- **Watkins (WHOI) bootstrapped Pod.Cast round 1 only**; recordings are global killer-whale ecotypes (not SRKW-focused), metadata-level signal types (not S1-S40 catalog), and terms are **non-commercial / permission-based** -> STOP.
- **ONC in orcast today is audio/spectrogram relay only** (`src/aws_backend/sources/onc.py`); expert ONC annotations enter via DCLDE (OPEN). The separate **DORI-ONC** amateur label set (CC-BY labels, ~1 TB audio) is pre-release and ecotype-unvalidated -> conditional STOP unless O0 accepts parse cost + label weakness.
- **Existing in-repo label scaffolding is kinematic/detector-QC, not acoustic call-type:** `modeling/fit_kernels.py` ingests `orcahello_reviewed_detector_outcomes` (confirmed/false_positive/unknown/unreviewed); `modeling/acoustic/` does not exist yet.

## In-repo findings (cited)

**Hydrophone catalog (Orcasound stations, no annotation schema):**
- `src/integrations/live_orcasound_feeds.json` - 9 feeds with `node_name`, S3 `bucket`, lat/lng; every feed has `"orcahello_id": null`.
- `src/integrations/orcasound_hydrophones_for_orcast.json` - derived snapshot: 9 hydrophones, 5 active (`visible: true`).

**OrcaHello integration (presence/outcome labels, not call-type catalog):**
- `src/aws_backend/sources/orcahello_history.py` - reviewed-outcome endpoints: `confirmed`, `falsepositives`, `unknowns`, `unreviewed`; normalized fields: `t`, `station`, `confidence`, `reviewed`, `found`, `confirmed`, `audio_uri`, `spectrogram_uri` (no `call_type`, pod, or count).
- `docs/ml/ORCA_ML_INTEGRATION.md` - documents API record shape with ML `annotations[]` (`startTime`, `endTime`, `confidence`) plus moderator `found`/`reviewed`; lists Pod.Cast (~15 hr), Watkins, DCLDE as **training provenance, not runtime feeds**; Orcasound license **CC BY-NC-SA 4.0**.
- `docs/data-procurement/HOSTED_DATA_STATUS.md` - hosted stream `orcahello_reviewed_detector_outcomes`: 334 records, 4 stations, 2020-09-28 -> 2026-06-16; used for detector QC in `modeling/fit_kernels.py`, not acoustic classifier training.
- `data/models/fit_report.json` - `n_reviewed_labels: 420`, `truth_label: live` for level-0 detector QC.

**ONC integration (spectrogram only, not annotations):**
- `src/aws_backend/routers/onc.py` + `src/aws_backend/sources/onc.py` - relays pre-generated PNG spectrograms via `ONC_API_TOKEN`; no annotation ingest.

**Modeling scaffolding (kinematic / forecast, separate from BAM):**
- `modeling/fit_kernels.py:51-53` - streams `acoustic_detections` and `orcahello_reviewed_detector_outcomes` for **temporal kernel fitting**, not call-type classification.
- `modeling/studies/common.py` - `STATION_COORDS` for 4 in-region hydrophones; no acoustic label schema.

**Prior open-corpus screen (DCLDE, ONC, Orcasound):**
- `.cca/catalogue/O0/20260627_open-science-integration/OS2_open_node_screen.md` - measured DCLDE `Annotations.csv`: 207,574 rows, **CC-BY-4.0**, schema includes `Ecotype`, `KW`, `KW_certain`, `Dataset`, `Provider`; Orcasound labels **CC-BY-NC-SA**; DORI-ONC amateur labels Jaccard ~0.7 vs expert, ecotype not compared.

**Grep highlights:** no in-repo references to Watkins, DCLDE, or Pod.Cast outside docs/`.cca` catalogues; `call_type` appears only in legacy BigQuery/ML stubs (`src/data-processing/setup_bigquery_pipeline.py` uses synthetic `foraging_call`/`social_call`, not community labels).

## Corpus-by-corpus table

| name | label schema | size | format | license | URL | OPEN/STOP-to-O0 |
|---|---|---|---|---|---|---|
| **Orcasound Pod.Cast / "podcast rounds"** | Segment-level **binary SRKW call presence** (`start_time_s`, `duration_s`, `location`, `dataset` round); round 1 = Watkins global orca. Pod hints in some rounds in metadata, **not S1-S40 catalog** in TSV. | ~15 hr annotated; combined tar **5.1 GB gzip / ~10 GB** unpacked (8 rounds) | WAV + TSV (`train/train.tsv`, `test/test.tsv`) in S3 `acoustic-sandbox` | **CC BY-NC-SA 4.0** | https://github.com/orcasound/orcadata/wiki/Pod.Cast-data-archive ; https://registry.opendata.aws/orcasound/ | **STOP-to-O0** (NC+SA) |
| **OrcaHello (Microsoft AI4Orcas)** | Live API ML segment boxes + moderator **presence outcome** (`found` Yes/No, outcome buckets). Expert portal adds tags/comments (pod, category inferred from comments - not structured S1-S40). Hosted in orcast: **420 reviewed outcome labels**, not call-type. | ~6,700+ min moderated; ~1,000+ min confirmed orca calls; in-repo store **334** reviewed outcomes | JSON REST API + WAV/PNG URIs; Cosmos-backed archive | **CC BY-NC-SA 4.0** | https://aifororcasdetections.azurewebsites.net/swagger/index.html ; https://ai4orcas.net/orcahello/ | **STOP-to-O0** (NC+SA) |
| **ONC (Ocean Networks Canada)** | In orcast: spectrogram relay only. Expert labels via DCLDE subset (ecotype in collated CSV). DORI-ONC (separate): amateur species/ecotype labels (Jaccard ~0.7 vs expert; ecotype not validated). | Raw: multi-TB; DORI-ONC **~1.03 TB** | ONC Oceans 3.0 API (FLAC/MAT/PNG); DCLDE CSV; DORI CSV + audio | ONC-owned: **CC-BY 4.0**; partner subsets may be CC-BY-NC; DORI labels **CC-BY 4.0** (pre-release) | https://www.oceannetworks.ca/data/data-policy/ ; https://huggingface.co/datasets/DORI-SRKW/DORI-ONC | **OPEN** (expert DCLDE subset); **STOP-to-O0** for DORI-ONC alone |
| **Watkins (WHOI)** | Library metadata: **species**, region, season, **signal-type codes** (clicks, whistles, pulsed calls) - not SRKW S1-S40. Bootstrapped Pod.Cast round 1 (global orca, **not SRKW**). | ~2,000 unique recordings, **>15,000** annotated clips, 60+ species | Online WAV clips + indexed metadata | **Unclear / non-commercial academic-personal** (site under maintenance) | https://doi.org/10.1121/2.0000358 ; https://whoicf2.whoi.edu/science/B/whalesounds/ | **STOP-to-O0** (unclear + not SRKW) |
| **DCLDE-2027 (Palmer et al. 2025)** | Collated `Annotations.csv`: call-level boxes; **`Ecotype`** (SRKW, NRKW, TKW, OKW, SAR); `KW`, `KW_certain`; `Dataset`, `Provider`, `UTC`. Original provider files include stereotyped pulsed call types (SIMRES/HALLO). `Call.Type` = CK / W / BP (category, **not** S1-S40). No source-count field. | **>225,000** annotations; **1.6 TB** audio; 23 locations; 2005-2023; collated CSV **207,574 rows / ~50 MB** | Provider folders + collated CSV; NOAA GCS + NCEI DOI | **CC-BY 4.0** on collated open artifact; Nature *article* is CC-BY-NC-ND (distinct from dataset) | https://doi.org/10.25921/15ey-mh50 ; https://www.nature.com/articles/s41597-025-05281-5 ; gs://noaa-passive-bioacoustic/dclde/2027/ | **OPEN** (collated CC-BY-4.0); flag NC-ND on article text only |

## Which corpus best supports an HONEST count+type target

| Target | Best corpus | Honest support level |
|---|---|---|
| **Source count ("how many orcas")** | *None* | **Not supported.** All label calls/segments or encounter presence, not number of vocalizing animals. R03 should scope HUD to drop count. |
| **SRKW presence (call detected?)** | DCLDE (OPEN) for offline train/eval; OrcaHello/Pod.Cast for Salish context but **license-blocked** | DCLDE: strong call-level KW flags + `KW_certain`. |
| **Ecotype / pod (coarse "who")** | **DCLDE** (`Ecotype==SRKW` vs TKW/NRKW/OKW) | Collated CSV is ecotype-level, not pod (J/K/L). |
| **Call-type category (CK / W / BP)** | DCLDE originals; Pod.Cast/OrcaHello weakly | `Call.Type` is category, explicitly **not** S1-S40. |
| **SRKW S1-S40 catalog labels** | Partial, expert-only - SIMRES / HALLO subsets inside DCLDE originals | Collated DCLDE CSV excludes matriline/pulsed-call-type fields. Not suitable for honest full S1-S40 classifier without scoped subset + relabel budget. |

**Ranking for BAM honest targets (license-clear only):** 1. DCLDE (OPEN). 2. ONC via DCLDE. 3. Pod.Cast / OrcaHello (best Salish station alignment but **STOP** on license).

## License & privacy verdict per corpus

| Corpus | Verdict | Rationale |
|---|---|---|
| **Pod.Cast** | **STOP-to-O0** | CC BY-NC-SA 4.0; SA + NC fail BSW gate. Community validators named in wiki (public metadata). |
| **OrcaHello** | **STOP-to-O0** | Same CC BY-NC-SA chain; moderator comments may contain free text - treat as **potential PII**; do not export verbatim comments into training manifests. |
| **ONC (expert/DCLDE path)** | **OPEN** | CC-BY 4.0 ONC policy + CC-BY-4.0 DCLDE collated artifact. |
| **ONC (DORI-ONC amateur)** | **STOP-to-O0** | Pre-release labels; ecotype reliability not validated; duplicates DCLDE expert coverage. |
| **Watkins** | **STOP-to-O0** | Non-commercial / permission-based terms; not SRKW; site maintenance obscures TOU. |
| **DCLDE-2027** | **OPEN** (with O0 note) | Collated NOAA artifact CC-BY-4.0. Article NC-ND applies to paper content, not the training CSV. Per-provider audio folders may carry mixed terms - O0 should sign off before mixing all 1.6 TB. |

## Recommendations with cost + standin-free fallback

**Primary (OPEN, standin-free):** BAM-DATA anchors on **DCLDE-2027 collated `Annotations.csv` + matched audio**, filtered to Salish-relevant `Dataset` keys (e.g. `orcasound_lab`, `LimeKiln`, `HaroStrait*`, `StraitofGeorgia`) for domain match. Honest v1 target: binary **killer-whale call detection** + optional **ecotype head (SRKW vs not-SRKW)** on held-out split - not source count, not full S1-S40. Cost: ~50 MB CSV + selective audio pull; training on box; weights on S3/gitignore.

**Station-aligned audio without NC labels:** Use Orcasound archived audio (R01) for inference/demo clip selection only if O0 accepts NC-SA for playback; keep **training labels** on DCLDE OPEN subset to avoid NC-SA label contamination.

**STOP corpora (no shipped weights without O0):** Pod.Cast, OrcaHello training exports, Watkins, DORI-ONC amateur labels.

**Standin-free fallback if DCLDE Salish subset is sparse:** Train **presence-only** detector on OPEN DCLDE SRKW rows; report precision/recall on held-out datasets; HUD wording: "model-detected SRKW-class call (not pod, not count)." Do **not** fall back to synthetic `call_type` fields or mock OrcaHello categories.

**OrcaHello in orcast (already wired):** retain for **live candidate detections / reviewed-outcome QC** on the kinematic forecast track; **do not conflate** with BAM acoustic classifier training labels unless license cleared.

## Open questions for O0

1. **NC-SA override?** Will O0 allow CC BY-NC-SA Pod.Cast/OrcaHello/Orcasound labeled data for a non-commercial research demo, or is DCLDE-only mandatory for BAM weights?
2. **DCLDE scope:** Salish-only subset vs full NE Pacific (domain shift vs volume)?
3. **Per-provider DCLDE audio licenses:** Is collated CSV + CC-BY-4.0 GCS path sufficient, or must each provider folder be legal-reviewed before train?
4. **Call-type ambition:** Pursue HALLO/SIMRES original annotations for stereotyped call types, or cap v1 at ecotype + CK/W/BP?
5. **OrcaHello maintainer ask:** bulk export of reviewed segments with stable license for ML reuse?
6. **ONC token + DORI-ONC:** Invest ~1 TB parse for incremental labels, or rely on DCLDE expert ONC rows only?
7. **Demo clip provenance:** Which OPEN-licensed recording matches the chosen orcast hydrophone station for BAM-ACCEPT?

## Sources

**In-repo (commit 240570e):**
- `src/integrations/live_orcasound_feeds.json`, `src/integrations/orcasound_hydrophones_for_orcast.json`
- `src/aws_backend/sources/orcahello_history.py`, `src/aws_backend/sources/onc.py`, `src/aws_backend/routers/onc.py`
- `modeling/fit_kernels.py`, `modeling/studies/common.py`
- `docs/ml/ORCA_ML_INTEGRATION.md`, `docs/data-procurement/HOSTED_DATA_STATUS.md`, `docs/data-procurement/ACCOUNT_REQUESTS.md`
- `.cca/catalogue/O0/20260629_bside-acoustic-behavior-workbench/BSW-ACOUSTIC-ML_CHARTER.md`
- `.cca/catalogue/O0/20260627_open-science-integration/OS2_open_node_screen.md`

**External:**

| Resource | URL | License / terms |
|---|---|---|
| Orcasound AWS Open Data | https://registry.opendata.aws/orcasound/ | **CC BY-NC-SA 4.0** |
| Pod.Cast data archive wiki | https://github.com/orcasound/orcadata/wiki/Pod.Cast-data-archive | Audio NC-SA; round 1 Watkins separate |
| AI4Orcas OrcaHello | https://ai4orcas.net/orcahello/ | Data via Orcasound NC-SA |
| OrcaHello API v1.2 | https://aifororcasdetections.azurewebsites.net/swagger/index.html | Public read; NC-SA data chain |
| ONC data policy | https://www.oceannetworks.ca/data/data-policy/ | **CC-BY 4.0** (ONC-owned); partners may be NC |
| DORI-ONC (HF) | https://huggingface.co/datasets/DORI-SRKW/DORI-ONC | Labels **CC-BY**; pre-release |
| Watkins (Sayigh et al. 2020) | https://doi.org/10.1121/2.0000358 | Non-commercial use cited downstream |
| DCLDE NCEI dataset | https://doi.org/10.25921/15ey-mh50 | Collated artifact **CC-BY-4.0** |
| Palmer et al. 2025 (Sci Data) | https://www.nature.com/articles/s41597-025-05281-5 | Article **CC-BY-NC-ND 4.0**; dataset schemas |
| DCLDE collation code | https://doi.org/10.5281/zenodo.15743033 | Zenodo (R scripts) |
