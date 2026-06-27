# Albion (Fraser) FOS Chinook feed: provenance + refresh recipe

The L3 `k_salmon` covariate needs the Fraser-summer Chinook stock that SRKW chiefly target. The
real source is the DFO Albion test fishery, published as the FOS "Catch Summary by Date" report.
`src/aws_backend/sources/salmon.py` `_fetch_fraser` reads a per-year cache at
`data/salmon/albion_fos/fosYYYY.csv`; this doc records where that cache comes from and how to
refresh it. DART (Columbia/Bonneville) stays the secondary fallback only.

## Why it is cached, not pulled live in-process

- The DFO FOS report host `www-ops2.pac.dfo-mpo.gc.ca` is DNS-blocked from the dev host and the
  backend region; the report is a POST-driven page that opens a new window in a browser.
- It IS reachable from the `aimez-services` EC2 (`i-04a649f91274e9fce`, x86_64 Ubuntu, account
  198456344617, us-east-1): from there `www-ops2.pac.dfo-mpo.gc.ca` resolves to 205.193.114.62.
- So the real daily series is fetched on the EC2 and cached into the repo. Provenance: DFO Fishery
  Operations System (FOS), Albion test fishery, stat=CPTFM, fsub_id=242 (subsystem), species
  CHINOOK SALMON. Open Government Licence - Canada.

## Working refresh recipe (no Selenium needed)

The form at `rptcsbdparm.cfm` POSTs to `rptCSbD.cfm?stat=CPTFM` with fields:
`lboYears=<YYYY>`, `lboSpecies=124` (CHINOOK SALMON), `lboFsub=242`, `cmdRunReport=Run Report`.
A direct POST returns the report HTML (no JS form-driving required). Run on a DFO-reachable host:

```
ssh -i ~/.ssh/pax-ec2-key.pem ubuntu@44.197.243.177   # aimez-services EC2 (SSM fallback in 198456344617/us-east-1)

# prime a cookie, then POST the report for the target year
curl -sS -c /tmp/fc.txt "https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptcsbdparm.cfm?stat=CPTFM&fsub_id=242" -o /dev/null
curl -sS -b /tmp/fc.txt \
  -e "https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptcsbdparm.cfm?stat=CPTFM&fsub_id=242" \
  --data "lboYears=2026&lboSpecies=124&lboFsub=242&cmdRunReport=Run+Report" \
  "https://www-ops2.pac.dfo-mpo.gc.ca/fos2_Internet/Testfish/rptCSbD.cfm?stat=CPTFM" -o /tmp/fos.html
```

Parse: each data row is a `<tr>` whose stripped text splits into exactly 12 whitespace tokens with
`tokens[0]` a day number and `tokens[1]` a 3-letter month; write them as CSV with header
`day,mon,year,netlen,catch1,sets1,effort1,cpue1,catch2,sets2,effort2,cpue2` (csv-quote the
comma-bearing effort fields). `cpue1` (standard 8-inch gillnet CPUE) is the run-timing index used by
`_load_albion_fos`. Copy the result to `data/salmon/albion_fos/fosYYYY.csv`. Clean up `/tmp` on the
box afterward. Selenium (orcasalmon `scrape_fos`) is a fallback only if the form action changes.

## Coverage notes

- Cached years: 2019-2026. The Albion season runs ~April to October; the current year is partial
  (e.g. 2026 cached 2026-05-01..2026-06-26, before the late-August summer peak). Refresh mid- and
  post-season to extend the current year.
- A year with no cache file falls through to DART (Columbia, a different/fall stock) and is reported
  honestly as not stock-aligned by the L3 lag scan.

## What this changed (2026-06-27)

`_fetch_fraser` now returns real Albion for all detection years 2020-2026 (single source `albion`,
stock-aligned). The L3 lag scan on the complete, correct-stock feed still does not beat the
permutation null (best lag +20 d, r=0.076, p=0.394), so L3 stays WITHHELD honestly: the daily
binary presence vs Albion run-timing signal is not significant on this detection set. The feed is
now correct and complete; this is a data/methodology result, not a wiring gap. No confidence
promotion.
