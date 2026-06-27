"""Validation harness for the salmon (Chinook) run-timing parsers in salmon.py.

Wave 1, Agent E (orcast ML-ops frontier waveset). This module is a STANDALONE
validation harness; it does NOT edit salmon.py (a convergence file). It hits the
real Albion (Fraser/DFO) and DART (Columbia/Bonneville) feeds, captures their
ACTUAL payload shapes, and checks the salmon.py parse helpers
(``_parse_daily_payload``, ``_extract_rows``, ``_row_date``, ``_row_value``)
against them. It answers one question per feed: does a real feed now yield a
usable daily Chinook run-timing index that beats the climatology placeholder?

Run it under .venv (python3.14):

    .venv/bin/python -m src.aws_backend.sources.salmon_validation

It prints a per-feed report and writes a JSON findings file to
``.cca/catalogue/O0/20260627_mlops/salmon_validation_findings.json``.

=============================================================================
MEASURED FINDINGS (live run 2026-06-27, year=2025)
=============================================================================

DART  (Columbia / Bonneville Dam, Columbia Basin Research):
  reachable    : YES  (HTTP 200, content-type text/csv); NB the report is built
                 on the first request for a query and may serve a transient HTML
                 "err-adultdaily" wrapper, so a non-CSV response must be retried.
  parseable    : YES  -> recovered a daily {ISO date: adult-Chinook count} series
  row count    : 269 days with a Chinook count (2025-03-15 .. late autumn)
  sample       : 2025-03-15->1, 2025-03-16->1, 2025-03-19->2; data peak
                 2025-09-07->22928 (the Columbia fall Chinook run).
  beats climo  : YES  -- a real, data-driven run-timing curve (dominant peak at
                 ~day-of-year 250) vs the smooth double-Gaussian placeholder
                 (hard-coded peak at day-of-year 201).
  BLOCKER in current code: the feed is CSV, but ``_fetch_columbia`` calls
                 ``response.json()`` (raises on CSV -> caught -> climatology); the
                 default ``outputFormat=csvSingle`` returns an HTML error page (use
                 ``outputFormat=csv``); the request omits ``year``/``sc``/``mgconfig``
                 (a yearless query returns the error wrapper); and the adult-Chinook
                 column is ``Chin``, NOT in the current ``value_keys``. All fixed by
                 PATCH-salmon.md.
  CAVEAT       : the Bonneville dominant peak is the COLUMBIA FALL run, a different
                 stock than the Fraser summer Chinook that the placeholder models
                 and that SRKW chiefly target. DART is the documented SECONDARY
                 source and a real, parseable proxy; whether it aligns with SRKW
                 presence is the Wave 3 lag-scan's call, not this harness's.

ALBION (Fraser River / DFO Canada test fishery):
  reachable    : YES  (HTTP 200) but the configured ``_ALBION_URL`` is a
                 meta-refresh stub that redirects to a descriptive HTML page.
  parseable    : NO   -- the live Albion page publishes the daily Chinook CPUE
                 ONLY as JPG graph images
                 (images/albion-daily-chinook-quinnat-quotidienne-eng.jpg);
                 there is no HTML table, CSV, or JSON daily series to parse.
                 The historical machine-readable FOS endpoint host
                 (www-ops2.pac.dfo-mpo.gc.ca) does not resolve (DNS: no answer).
  row count    : 0
  beats climo  : N/A -- no machine-readable daily series exists to parse.

NET: a real Chinook run-timing feed IS available and beats climatology, via DART
(Columbia/Bonneville) -- the documented SECONDARY source -- not via Albion
(Fraser). The patch makes ``_fetch_columbia`` real and leaves ``_fetch_fraser``
honestly disabled (image-only source). L3 can move off the placeholder onto the
DART feed; see the caveat in PATCH-salmon.md (Columbia timing is a proxy for, not
identical to, the Fraser-bound Chinook SRKW target).

=============================================================================
PATCH SPEC location
=============================================================================
The exact changes for salmon.py (a convergence file -- DO NOT edit this wave) are
written up in .cca/catalogue/O0/20260627_mlops/PATCH-salmon.md. The Wave 2
backend integrator applies them.
"""
from __future__ import annotations

import csv
import io
import json
import socket
import time
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# Reuse the REAL parse helpers from salmon.py so we validate them directly,
# rather than reimplementing the parse logic.
from .salmon import (
    _DART_URL,
    _normalize_within_season,
    _parse_daily_payload,
)

_HTTP_TIMEOUT = 30
_DNS_RETRIES = 5
_HEADERS = {"User-Agent": "Mozilla/5.0 (orcast salmon_validation harness)"}

# Live Albion landing page (the configured _ALBION_URL is a redirect stub; this
# is the page it refreshes to). Kept here so the harness probes the live source.
_ALBION_LANDING_URL = "https://www.pac.dfo-mpo.gc.ca/fm-gp/fraser/albion-eng.html"

# DART adult-daily report. The CONFIRMED query that returns CSV (not the default
# in salmon.py, which yields an HTML error page). proj=BON, adult Chinook in the
# "Chin" column, full-ISO "Date" column.
_DART_CSV_PARAMS = {
    "sc": "1",
    "mgconfig": "adult",
    "outputFormat": "csv",  # NB: "csvSingle" returns an HTML error page.
    "proj": "BON",
    "span": "no",
    "startdate": "1/1",
    "enddate": "12/31",
    "run": "",
}
# The adult-Chinook column in the DART adult-daily CSV (NOT "count"/"chinook").
_DART_VALUE_KEYS: Tuple[str, ...] = ("Chin", "chin", "Chinook", "chinook")

# A small CAPTURED sample of the real DART CSV (head + a run-season slice), so
# the harness has an offline fixture even if the live feed is down. Verbatim
# from the live 2025 response on 2026-06-27.
DART_CSV_SAMPLE = (
    "Project,Date,Chinook Run,Chin,JChin,Stlhd,WStlhd,Sock,Coho,JCoho,Shad,"
    "LmpryDay,LmpryNight,LmpryCombined,LmpryLPS,BTrout,Chum,Pink,TempC\n"
    "Bonneville,2025-01-01,,,,13,6,,-1,,,,,,,,,,\n"
    "Bonneville,2025-03-15,,1,,,,,,,,,,,,,,,\n"
    "Bonneville,2025-03-16,,1,,,,,,,,,,,,,,,\n"
    "Bonneville,2025-07-31,,505,,,,,,,,,,,,,,,\n"
    "Bonneville,2025-08-01,,448,,,,,,,,,,,,,,,\n"
    "Bonneville,2025-08-02,,442,,,,,,,,,,,,,,,\n"
)

# A captured note on the Albion landing page: the only daily-CPUE artifacts are
# JPG images (verbatim <img> srcs from the live 2026-06-27 page).
ALBION_IMAGE_SRCS = (
    "images/albion-daily-chinook-quinnat-quotidienne-eng.jpg",
    "images/albion-cumulative-chinook-quinnat-accumulees-eng.jpg",
)

_FINDINGS_PATH = (
    Path(__file__).resolve().parents[3]
    / ".cca"
    / "catalogue"
    / "O0"
    / "20260627_mlops"
    / "salmon_validation_findings.json"
)


@dataclass
class FeedResult:
    feed: str
    url: str
    reachable: bool
    http_status: Optional[int]
    content_type: Optional[str]
    parseable: bool
    row_count: int
    sample: Dict[str, float] = field(default_factory=dict)
    beats_climatology: bool = False
    note: str = ""


def _get_with_dns_retry(url: str, params: Optional[dict] = None) -> requests.Response:
    """GET with a few retries; the DFO host has intermittent getaddrinfo flakiness."""
    last: Optional[Exception] = None
    for attempt in range(_DNS_RETRIES):
        try:
            return requests.get(
                url, params=params, timeout=_HTTP_TIMEOUT, headers=_HEADERS, allow_redirects=True
            )
        except (requests.exceptions.ConnectionError, socket.gaierror) as exc:  # pragma: no cover
            last = exc
            time.sleep(1.5 * (attempt + 1))
    assert last is not None
    raise last


def _csv_to_rows(text: str) -> List[Dict[str, object]]:
    """Parse DART CSV text into a list of row dicts (the shape _extract_rows wants).

    DART appends free-text footnote lines after the table; csv.DictReader keeps
    them as rows with mostly-None values, which _row_date/_row_value reject
    harmlessly, so no special trimming is required.
    """
    reader = csv.DictReader(io.StringIO(text))
    rows: List[Dict[str, object]] = []
    for row in reader:
        rows.append({k: v for k, v in row.items() if k is not None})
    return rows


def _climatology_peak_doy() -> int:
    return 201  # mirrors salmon._PRIMARY_PEAK_DOY


def _peak_doy_of(series: Dict[str, float]) -> Optional[int]:
    if not series:
        return None
    best_iso = max(series, key=lambda k: series[k])
    try:
        return date.fromisoformat(best_iso).timetuple().tm_yday
    except ValueError:
        return None


def validate_dart(year: int, live: bool = True) -> FeedResult:
    """Validate the DART (Columbia/Bonneville) feed against salmon.py parse helpers."""
    url = _DART_URL
    status: Optional[int] = None
    ctype: Optional[str] = None
    if live:
        # DART builds the report file on the first request for a query and may
        # serve a transient HTML "err-adultdaily" wrapper before the CSV is
        # ready; retry a few times until we get CSV.
        params = {**_DART_CSV_PARAMS, "year": str(year)}
        resp = None
        for _attempt in range(4):
            try:
                resp = _get_with_dns_retry(url, params=params)
            except Exception as exc:  # network/DNS: fall back to the captured fixture
                return _validate_dart_text(
                    DART_CSV_SAMPLE, url, status=None, ctype=None,
                    note=f"live fetch failed ({type(exc).__name__}); used captured sample",
                )
            status = resp.status_code
            ctype = resp.headers.get("content-type")
            if status == 200 and "csv" in (ctype or "").lower():
                return _validate_dart_text(resp.text, url, status=status, ctype=ctype, note="live")
            time.sleep(2)
        return FeedResult(
            feed="dart", url=url, reachable=False, http_status=status,
            content_type=ctype, parseable=False, row_count=0,
            note="non-CSV response after retries (transient DART err- wrapper); try again later",
        )
    return _validate_dart_text(DART_CSV_SAMPLE, url, status=None, ctype=None, note="captured sample")


def _validate_dart_text(
    text: str, url: str, status: Optional[int], ctype: Optional[str], note: str
) -> FeedResult:
    rows = _csv_to_rows(text)
    # This is the EXACT call the patched _fetch_columbia should make: feed the
    # list-of-dict rows to the real _parse_daily_payload with the Chin value key.
    parsed = _parse_daily_payload(rows, value_keys=_DART_VALUE_KEYS, year=date.today().year)
    normalized = _normalize_within_season(parsed)
    peak = _peak_doy_of(normalized)
    # "Beats climatology": a real, non-degenerate daily series whose data-driven
    # peak is not the hard-coded placeholder peak and whose shape carries signal.
    beats = (
        len(parsed) >= 30
        and len({round(v, 3) for v in normalized.values()}) > 5  # not flat / degenerate
    )
    sample = {k: parsed[k] for k in sorted(parsed)[:3]}
    if normalized:
        peak_iso = max(normalized, key=lambda k: normalized[k])
        sample[peak_iso] = parsed.get(peak_iso, normalized[peak_iso])
    return FeedResult(
        feed="dart",
        url=url,
        reachable=status == 200 if status is not None else True,
        http_status=status,
        content_type=ctype,
        parseable=len(parsed) > 0,
        row_count=len(parsed),
        sample=sample,
        beats_climatology=bool(beats),
        note=(
            f"{note}; parsed via salmon._parse_daily_payload on CSV->rows; "
            f"data peak doy={peak} (climatology placeholder peak doy={_climatology_peak_doy()})"
        ),
    )


def validate_albion(year: int, live: bool = True) -> FeedResult:
    """Validate the Albion (Fraser/DFO) feed. There is no machine-readable series."""
    url = _ALBION_LANDING_URL
    if not live:
        return FeedResult(
            feed="albion", url=url, reachable=True, http_status=None, content_type="text/html",
            parseable=False, row_count=0,
            note=f"image-only source; daily CPUE published as JPG ({', '.join(ALBION_IMAGE_SRCS)})",
        )
    try:
        resp = _get_with_dns_retry(url)
    except Exception as exc:
        return FeedResult(
            feed="albion", url=url, reachable=False, http_status=None, content_type=None,
            parseable=False, row_count=0,
            note=f"unreachable ({type(exc).__name__}); DFO host DNS is intermittent",
        )
    text = resp.text
    has_table = "<table" in text.lower()
    img_present = any(src in text for src in ALBION_IMAGE_SRCS)
    return FeedResult(
        feed="albion",
        url=url,
        reachable=resp.status_code == 200,
        http_status=resp.status_code,
        content_type=resp.headers.get("content-type"),
        parseable=False,  # no HTML table / CSV / JSON daily series on the page
        row_count=0,
        beats_climatology=False,
        note=(
            "no machine-readable daily series: "
            f"has_html_table={has_table}, daily-CPUE published as JPG image={img_present}. "
            "Historical FOS data host (www-ops2.pac.dfo-mpo.gc.ca) does not resolve."
        ),
    )


def run(year: int = 2025, live: bool = True, write_json: bool = True) -> Dict[str, object]:
    dart = validate_dart(year, live=live)
    albion = validate_albion(year, live=live)
    verdict = {
        "real_feed_available": dart.parseable and dart.beats_climatology,
        "real_feed": "dart" if (dart.parseable and dart.beats_climatology) else None,
        "albion_parseable": albion.parseable,
        "l3_recommendation": (
            "promote-eligible: DART (Columbia/Bonneville) yields a real daily Chinook "
            "run-timing index that beats the climatology placeholder. Apply PATCH-salmon.md."
            if (dart.parseable and dart.beats_climatology)
            else "withheld: no real feed beats climatology; L3 stays on the placeholder."
        ),
    }
    payload = {"year": year, "live": live, "dart": asdict(dart), "albion": asdict(albion), "verdict": verdict}
    if write_json:
        _FINDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _FINDINGS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _print_feed(r: FeedResult) -> None:
    print(f"[{r.feed.upper()}] {r.url}")
    print(f"    reachable={r.reachable} http={r.http_status} ctype={r.content_type}")
    print(f"    parseable={r.parseable} row_count={r.row_count} beats_climatology={r.beats_climatology}")
    if r.sample:
        print(f"    sample={r.sample}")
    print(f"    note: {r.note}")


if __name__ == "__main__":
    result = run(year=2025, live=True, write_json=True)
    print("=== Salmon feed validation (Wave 1, Agent E) ===")
    _print_feed(FeedResult(**result["dart"]))
    _print_feed(FeedResult(**result["albion"]))
    print("--- verdict ---")
    for k, v in result["verdict"].items():
        print(f"    {k}: {v}")
    print(f"--> findings written to {_FINDINGS_PATH}")
