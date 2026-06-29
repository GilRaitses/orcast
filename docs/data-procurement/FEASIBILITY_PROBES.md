# ORCAST Data Procurement Feasibility Probes

## Probe Results

| Source | Probe | Result | Decision |
| --- | --- | --- | --- |
| OrcaHello confirmed detections | `https://aifororcasdetections.azurewebsites.net/api/detections/confirmed?...` | Returned Azure `403` because the web app is currently stopped. Reconnaissance still found public API documentation and alternate v2 deployment. | Needs endpoint fallback/confirmation before adapter hardening. |
| NOAA CO-OPS PUG1702 current predictions | Datagetter query for 2020-01-01 to 2020-01-02 | Success. Returned `current_predictions.cp` rows with `Time`, `Velocity_Major`, `Bin`, `Depth`, `meanFloodDir`, `meanEbbDir`. | `can_get_now` |
| NDBC 46088 standard met | `https://www.ndbc.noaa.gov/data/realtime2/46088.txt` | Success. Large whitespace text file with station meteorological/sea-state rows. | `can_get_now` |
| NOAA CO-OPS Friday Harbor wind | Latest `product=wind` for station `9449880` | Success. Returned metadata and fields `t`, `s`, `d`, `dr`, `g`, `f`. | `can_get_now` |
| OBIS occurrence | `api.obis.org/v3/occurrence?...size=1` | Timed out during this pass. Existing adapter and OBIS docs still support public API use. | Retry during adapter work; likely `can_get_now` |
| iNaturalist observation | `api.inaturalist.org/v1/observations?...per_page=1` | Success, response large but public. | `can_get_now` |
| NOAA PMEL ERDDAP AIS sample | `AIS2024_AIS.csv?...` | Returned 404 for this dataset/query form. Recon found ERDDAP data-access page; dataset ID/query needs correction. | Needs probe correction before adapter implementation. |
| NOAA CUSP shoreline ArcGIS REST | FeatureServer query for one record | Success. Returned fields and sample feature attributes. | `can_get_now` |

## Probe Takeaways

- NOAA currents, NDBC/CO-OPS weather, iNaturalist, and CUSP are immediately feasible.
- OrcaHello public access appears real but endpoint stability is an issue; use the documented v2 Swagger/public endpoint or ask maintainers to confirm the stable endpoint.
- AIS is feasible through NOAA Marine Cadastre bulk downloads even though the ERDDAP query needs correction.
- OBIS should be retried with a smaller or different query during adapter work; it remains a public API source.

## Minimal Next Probes

1. OrcaHello v2:
   - `https://aifororcasdetections2.azurewebsites.net/swagger/index.html`
   - Test `/api/detections/confirmed` equivalent.
2. AIS:
   - Confirm actual ERDDAP dataset ID from the data-access form.
   - If ERDDAP remains awkward, use Marine Cadastre bulk GeoParquet/CSV instead.
3. Albion:
   - Use PSC/DFO report pages to capture current direct download links and column names.
4. SeaStats:
   - Confirm station keys for Orcasound stations and recordingCoverage endpoint.
