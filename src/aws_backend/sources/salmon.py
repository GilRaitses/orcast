from __future__ import annotations

import csv
import io
import math
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from ..models import NormalizedSighting
from .base import SourceAdapter, SourceFetchResult

# Daily Chinook run-timing INDEX adapter (the k_salmon prey covariate in
# docs/methodology/FORECAST_KERNELS.md). It produces a normalized 0-1 daily
# series for the Salish Sea, preferring the Fraser River signal (most relevant
# to Southern Resident Killer Whales) with a secondary Columbia/Bonneville
# signal.
#
# Source-pluggable + robust by design:
#   1. Primary live source: Albion Chinook test fishery (Fraser River, DFO
#      Canada) - daily CPUE (catch-per-unit-effort) during the run season.
#      UNAVAILABLE as a machine-readable feed (see _fetch_fraser).
#   2. Secondary live source: Columbia River DART Bonneville Dam Chinook
#      passage counts (Columbia Basin Research). CONFIRMED + parsed (CSV).
#   3. Documented climatology FALLBACK (see _climatology_series): if every live
#      source is unavailable, return a smooth seasonal Chinook run-timing curve
#      so the covariate is ALWAYS available while real feeds are being wired.
#
# Feed status (validated 2026-06-27 by sources/salmon_validation.py):
#   - DART (Columbia/Bonneville) is CONFIRMED and parsed: the feed is CSV (not
#     JSON), requires year + outputFormat=csv (csvSingle returns an HTML error
#     page), and the adult-Chinook column is "Chin". 269 daily rows for 2025,
#     dominant peak 2025-09-07. _fetch_columbia parses it.
#   - Albion (Fraser/DFO) is WIRED from a cached real FOS export: the live page
#     serves CPUE only as JPG images and the FOS report host is DNS-blocked from
#     this host, so the real daily FOS Chinook CPUE is cached per year under
#     data/salmon/albion_fos/fosYYYY.csv and read by _fetch_fraser. This is the
#     stock-aligned Fraser-summer Chinook signal (years not cached fall to DART).
#
# BIOLOGICAL CAVEAT: DART's dominant peak is the Columbia FALL Chinook run, a
# different stock than the Fraser SUMMER Chinook that SRKW chiefly target. DART
# is a real, parseable proxy/SECONDARY source, not the Fraser primary; whether
# it aligns with SRKW presence is the L3 lag-scan's call (salmon_lag.py).

# Albion test fishery (Fraser River, DFO). The live daily CPUE is served only as
# JPG graph images on the descriptive page; the machine-readable daily series is
# the DFO FOS "Catch Summary by Date" report (stat=CPTFM, fsub_id=242), a
# Selenium-driven JS form whose host (www-ops2.pac.dfo-mpo.gc.ca) is DNS-blocked
# from this host / CI. We therefore cache the real Albion FOS Chinook CPUE per
# year under data/salmon/albion_fos/fosYYYY.csv and read it here; refresh the
# cache from a DFO-reachable host with the FOS report (see WIRING-salmon-albion).
_ALBION_URL = "https://www.pac.dfo-mpo.gc.ca/fm-gp/fraser/docs/commercial/albionchinook-quinnat"

# Real Albion FOS Chinook CPUE cache (provenance: DFO FOS report stat=CPTFM,
# fsub_id=242, "CHINOOK SALMON"; columns day,mon,year,netlen,catch1,sets1,
# effort1,cpue1,catch2,sets2,effort2,cpue2). cpue1 is the standard 8-inch gillnet
# CPUE used as the Fraser run-timing index. This is REAL data (the Fraser-summer
# Chinook stock SRKW target), not climatology.
_ALBION_FOS_CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "salmon" / "albion_fos"
_ALBION_FOS_VALUE_KEY = "cpue1"
_MONTH_ABBR = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Columbia River DART Bonneville Dam adult Chinook passage (Columbia Basin
# Research). Returns CSV with year + outputFormat=csv; adult Chinook = "Chin"
# column, full-ISO "Date" column. Validated 2026-06-27.
_DART_URL = "https://www.cbr.washington.edu/dart/cs/php/rpt/adult_daily.php"

# DART adult-daily report query that returns CSV. outputFormat=csvSingle returns
# an HTML error page; a yearless query returns the err-adultdaily HTML wrapper.
_DART_PARAMS = {
    "sc": "1",
    "mgconfig": "adult",
    "outputFormat": "csv",
    "proj": "BON",
    "span": "no",
    "startdate": "1/1",
    "enddate": "12/31",
    "run": "",
}
# Adult-Chinook column in the DART CSV (NOT count/passage/chinook); JChin = jacks.
_DART_VALUE_KEYS = ("Chin", "chin", "Chinook", "chinook")

_HTTP_TIMEOUT = 10

# Climatology run-timing shape (day-of-year). The Fraser summer/early-summer
# Chinook run peaks roughly mid-July to early-August; a smaller fall component
# trails into September. Values are a relative abundance shape, min-max
# normalized to 0-1 before being returned.
_PRIMARY_PEAK_DOY = 201  # ~July 20
_PRIMARY_WIDTH = 24.0
_SECONDARY_PEAK_DOY = 248  # ~Sept 5 (fall run)
_SECONDARY_WIDTH = 18.0
_SECONDARY_WEIGHT = 0.35

# Season window the daily series spans (day-of-year). Wide enough to capture
# the full run shoulder-to-shoulder.
_SEASON_START_DOY = 60   # ~Mar 1
_SEASON_END_DOY = 320    # ~Nov 16


class SalmonRunAdapter(SourceAdapter):
    """Daily Chinook run-timing index for the Salish Sea (k_salmon covariate).

    fetch_run_index(year) is the primary entrypoint. It attempts the live
    Fraser (Albion) feed first, then the Columbia (DART) feed, and finally
    falls back to a documented climatology curve so the covariate is always
    available.
    """

    source_name = "salmon_run"
    reliability = 0.6

    def __init__(self, albion_url: str = _ALBION_URL, dart_url: str = _DART_URL) -> None:
        self.albion_url = albion_url
        self.dart_url = dart_url

    # -- SourceAdapter interface ------------------------------------------------
    def fetch(self) -> SourceFetchResult:
        """Adapter-style fetch for the current year's run index."""
        year = date.today().year
        series = self.fetch_run_index(year)
        source = series[0]["source"] if series else "climatology_fallback"
        return SourceFetchResult(
            source=self.source_name,
            available=source != "climatology_fallback",
            raw=series,
        )

    def normalize(self, result: SourceFetchResult) -> List[NormalizedSighting]:
        # This adapter produces a temporal covariate series, not point
        # sightings, so there is nothing to normalize into NormalizedSighting.
        return []

    # -- Run-timing index -------------------------------------------------------
    def fetch_run_index(self, year: int) -> List[Dict[str, object]]:
        """Return a daily Chinook run-timing series for ``year``.

        Each record: {'t': ISO date, 'fraser_index': float|None,
        'columbia_index': float|None, 'run_index': float, 'source': str}.

        ``run_index`` is a normalized 0-1 composite preferring the Fraser
        signal and falling back to Columbia. Always returns a non-empty
        series; on any live-fetch failure it returns the climatology fallback.
        """
        # 1. Primary: Fraser / Albion.
        try:
            fraser = self._fetch_fraser(year)
        except Exception:
            fraser = {}
        if fraser:
            return self._build_series(year, fraser_raw=fraser, columbia_raw={}, source="albion")

        # 2. Secondary: Columbia / DART.
        try:
            columbia = self._fetch_columbia(year)
        except Exception:
            columbia = {}
        if columbia:
            return self._build_series(year, fraser_raw={}, columbia_raw=columbia, source="dart")

        # 3. Documented climatology fallback (always available).
        return self._climatology_series(year)

    # -- Live fetchers ----------------------------------------------------------
    def _fetch_fraser(self, year: int) -> Dict[str, float]:
        """Albion (Fraser) daily Chinook CPUE -> {ISO date: cpue1}.

        REAL stock-aligned Fraser-summer Chinook signal. The live DFO Albion page
        serves CPUE only as JPG images, and the machine-readable FOS report
        (stat=CPTFM, fsub_id=242) is a Selenium-driven JS form whose host is
        DNS-blocked from this host / CI, so we read the cached real FOS CSV at
        data/salmon/albion_fos/fosYYYY.csv (provenance in the module header).
        Returns {} when the year is not cached, so fetch_run_index falls through
        to DART. Refresh the cache from a DFO-reachable host.
        """
        return _load_albion_fos(year, self.albion_url)

    def _fetch_columbia(self, year: int) -> Dict[str, float]:
        """Fetch DART Bonneville daily adult Chinook passage -> {ISO date: count}.

        The DART adult-daily report is CSV (csvSingle returns an HTML error page)
        and is built on the first request for a query, so a transient err- HTML
        wrapper can precede the CSV; retry past it. Adult Chinook is the "Chin"
        column. Validated 2026-06-27, sources/salmon_validation.py.
        """
        params = {**_DART_PARAMS, "year": str(year)}
        for _attempt in range(4):
            response = requests.get(self.dart_url, params=params, timeout=_HTTP_TIMEOUT)
            if getattr(response, "status_code", None) != 200:
                return {}
            ctype = (response.headers.get("content-type") or "").lower()
            if "csv" in ctype:
                return _parse_daily_payload(
                    _csv_text_to_rows(response.text),
                    value_keys=_DART_VALUE_KEYS,
                    year=year,
                )
            time.sleep(2)  # transient DART err- HTML wrapper; retry until CSV
        return {}

    # -- Series assembly --------------------------------------------------------
    def _build_series(
        self,
        year: int,
        fraser_raw: Dict[str, float],
        columbia_raw: Dict[str, float],
        source: str,
    ) -> List[Dict[str, object]]:
        fraser_norm = _normalize_within_season(fraser_raw)
        columbia_norm = _normalize_within_season(columbia_raw)

        dates = sorted(set(fraser_norm) | set(columbia_norm))
        series: List[Dict[str, object]] = []
        for iso in dates:
            fraser_index = fraser_norm.get(iso)
            columbia_index = columbia_norm.get(iso)
            # Prefer Fraser; fall back to Columbia.
            run_index = fraser_index if fraser_index is not None else columbia_index
            if run_index is None:
                run_index = 0.0
            run_index = _clamp01(run_index)
            series.append(
                {
                    "t": iso,
                    "fraser_index": fraser_index,
                    "columbia_index": columbia_index,
                    "run_index": run_index,
                    "source": source,
                    "source_url": _source_url_for(source),
                }
            )
        return series

    def _climatology_series(self, year: int) -> List[Dict[str, object]]:
        """Documented PLACEHOLDER seasonal run-timing curve for the Salish Sea.

        A double-Gaussian over day-of-year (a dominant Fraser summer/early
        Chinook peak ~mid-July to early-August plus a smaller fall component),
        min-max normalized to 0-1. Used whenever live feeds are unavailable so
        k_salmon is always defined. Replace with confirmed live feeds when wired.
        """
        raw: Dict[str, float] = {}
        for doy in range(_SEASON_START_DOY, _SEASON_END_DOY + 1):
            d = _date_from_doy(year, doy)
            raw[d.isoformat()] = _climatology_shape(doy)

        normalized = _normalize_within_season(raw)
        series: List[Dict[str, object]] = []
        for iso in sorted(normalized):
            run_index = _clamp01(normalized[iso])
            series.append(
                {
                    "t": iso,
                    "fraser_index": run_index,
                    "columbia_index": None,
                    "run_index": run_index,
                    "source": "climatology_fallback",
                    "source_url": _source_url_for("climatology_fallback"),
                }
            )
        return series


# -- Module helpers -------------------------------------------------------------
def _load_albion_fos(year: int, albion_url: str = _ALBION_URL) -> Dict[str, float]:
    """Read cached real Albion FOS Chinook CPUE for ``year`` -> {ISO date: cpue1}.

    Parses data/salmon/albion_fos/fosYYYY.csv (DFO FOS report export). Each row
    is day,mon(3-letter),year,...,cpue1,...; cpue1 is the standard 8-inch gillnet
    CPUE. Returns {} if the cache file is missing or unparseable so the caller can
    fall through. REAL data, not climatology.
    """
    path = _ALBION_FOS_CACHE_DIR / f"fos{year}.csv"
    if not path.exists():
        return {}
    out: Dict[str, float] = {}
    try:
        reader = csv.DictReader(io.StringIO(path.read_text(encoding="utf-8")))
        for row in reader:
            mon = str(row.get("mon", "")).strip().lower()[:3]
            month = _MONTH_ABBR.get(mon)
            try:
                day = int(str(row.get("day", "")).strip())
                row_year = int(str(row.get("year", year)).strip())
            except (TypeError, ValueError):
                continue
            if month is None:
                continue
            value = row.get(_ALBION_FOS_VALUE_KEY)
            if value is None or str(value).strip() == "":
                continue
            try:
                cpue = float(str(value).replace(",", "").strip())
            except (TypeError, ValueError):
                continue
            try:
                iso = date(row_year, month, day).isoformat()
            except ValueError:
                continue
            out[iso] = cpue
    except OSError:
        return {}
    return out


def _climatology_shape(doy: int) -> float:
    primary = _gaussian(doy, _PRIMARY_PEAK_DOY, _PRIMARY_WIDTH)
    secondary = _SECONDARY_WEIGHT * _gaussian(doy, _SECONDARY_PEAK_DOY, _SECONDARY_WIDTH)
    return primary + secondary


def _gaussian(x: float, mu: float, sigma: float) -> float:
    return math.exp(-0.5 * ((x - mu) / sigma) ** 2)


def _date_from_doy(year: int, doy: int) -> date:
    return date(year, 1, 1) + timedelta(days=doy - 1)


def _normalize_within_season(raw: Dict[str, float]) -> Dict[str, float]:
    """Min-max normalize a {date: value} mapping to 0-1 within the season."""
    if not raw:
        return {}
    values = list(raw.values())
    lo = min(values)
    hi = max(values)
    span = hi - lo
    if span <= 0:
        # Flat series: nothing to normalize against; treat all as peak.
        return {k: 1.0 for k in raw}
    return {k: (v - lo) / span for k, v in raw.items()}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _parse_daily_payload(
    payload: object,
    value_keys: Tuple[str, ...],
    year: int,
) -> Dict[str, float]:
    """Best-effort parse of a daily {date: value} mapping from varied payloads.

    Accepts a list of row dicts, or a dict wrapping such a list under common
    keys ('data', 'rows', 'results'). Each row must expose a date-like field
    and one of ``value_keys``. Returns {} on anything unparseable so callers
    fall back gracefully. UNCONFIRMED against live feeds - see module docstring.
    """
    rows = _extract_rows(payload)
    parsed: Dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        iso = _row_date(row, year)
        value = _row_value(row, value_keys)
        if iso is None or value is None:
            continue
        parsed[iso] = value
    return parsed


def _extract_rows(payload: object) -> List[object]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "rows", "results", "records"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []


def _csv_text_to_rows(text: str) -> List[Dict[str, object]]:
    """Parse DART-style CSV text into a list of row dicts.

    DART appends free-text footnote lines after the table; csv.DictReader keeps
    them as rows with mostly-empty values, which _row_date/_row_value reject
    harmlessly. Returns [] on empty/garbage input.
    """
    if not isinstance(text, str) or not text.strip():
        return []
    reader = csv.DictReader(io.StringIO(text))
    rows: List[Dict[str, object]] = []
    for row in reader:
        rows.append({k: v for k, v in row.items() if k is not None})
    return rows


_DATE_KEYS = ("t", "date", "Date", "day", "Day", "obs_date", "mm-dd")


def _row_date(row: Dict[str, object], year: int) -> Optional[str]:
    for key in _DATE_KEYS:
        if key not in row:
            continue
        value = row[key]
        if not isinstance(value, (str, int)):
            continue
        text = str(value).strip()
        # Full ISO date.
        try:
            return date.fromisoformat(text).isoformat()
        except ValueError:
            pass
        # MM-DD or MM/DD within the requested year.
        for sep in ("-", "/"):
            parts = text.split(sep)
            if len(parts) == 2:
                try:
                    month, dom = int(parts[0]), int(parts[1])
                    return date(year, month, dom).isoformat()
                except ValueError:
                    break
    return None


def _row_value(row: Dict[str, object], value_keys: Tuple[str, ...]) -> Optional[float]:
    for key in value_keys:
        if key in row and row[key] is not None:
            try:
                return float(row[key])
            except (TypeError, ValueError):
                continue
    return None


def _source_url_for(source: str) -> str:
    if source == "albion":
        return _ALBION_URL
    if source == "dart":
        return _DART_URL
    return "orcast://salmon/climatology_fallback"
