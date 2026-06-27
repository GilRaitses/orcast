# PATCH spec: `src/aws_backend/sources/salmon.py` (Wave 1, Agent E)

Status: SPEC ONLY. `salmon.py` is a convergence file; **do NOT edit it this wave**.
The Wave 2 backend integrator applies this patch. Validated live 2026-06-27 by
`src/aws_backend/sources/salmon_validation.py` (run:
`PYTHONPATH=. .venv/bin/python -m src.aws_backend.sources.salmon_validation`).
Measured findings are in `salmon_validation_findings.json` and the harness docstring.

## Summary of what changes and why

| Feed | Today | After patch | Why |
|------|-------|-------------|-----|
| DART (Columbia/Bonneville) | falls through to climatology: requests JSON of a CSV feed, with a yearless query and the wrong value key | returns a real daily `{ISO date: adult-Chinook count}` series | the feed is CSV (not JSON), needs `year`+`outputFormat=csv`, and the adult column is `Chin` |
| Albion (Fraser/DFO) | falls through to climatology | stays disabled (`return {}`), documented | the live Albion page publishes daily CPUE only as JPG images; no HTML table / CSV / JSON; the historical FOS data host does not resolve |

Net effect: `fetch_run_index` falls through Fraser (empty, honest) to **DART**, which
now yields a real `source="dart"` series instead of `climatology_fallback`. The
lag-scan (`modeling/studies/salmon_lag.py`) treats `dart` as `real_feed_only=True`,
so L3 can move off the placeholder onto a real feed. **Caveat below.**

## Verified facts (measured, not assumed)

- DART CSV endpoint `https://www.cbr.washington.edu/dart/cs/php/rpt/adult_daily.php`
  with `sc=1, mgconfig=adult, outputFormat=csv, proj=BON, span=no, startdate=1/1,
  enddate=12/31, year=<YYYY>, run=` returns `text/csv`.
  - `outputFormat=csvSingle` (the salmon.py default) returns an **HTML error page**, not CSV.
  - Omitting `year` (or `sc`/`mgconfig`) returns the **HTML `err-adultdaily` wrapper**.
  - The report file is built on first request for a query; a transient `err-` HTML
    wrapper can precede the CSV, so a non-CSV 200 must be **retried**.
  - CSV header: `Project,Date,Chinook Run,Chin,JChin,Stlhd,...`. Date is full ISO
    (`2025-09-07`); adult Chinook is column **`Chin`** (`JChin` is jacks — exclude).
  - 2025: 269 days carry a Chinook count; dominant peak `2025-09-07 = 22928`.
- Albion `_ALBION_URL` (`.../albionchinook-quinnat`) is a meta-refresh stub →
  `https://www.pac.dfo-mpo.gc.ca/fm-gp/fraser/albion-eng.html`, a descriptive page
  with **no `<table>`** and daily CPUE only as
  `images/albion-daily-chinook-quinnat-quotidienne-eng.jpg`. The historical
  machine-readable FOS host `www-ops2.pac.dfo-mpo.gc.ca` does **not resolve** (DNS no answer).
- The existing parse helpers `_parse_daily_payload`, `_extract_rows`, `_row_date`,
  `_row_value` are **correct as written** for a list-of-dict input: `_row_date`
  already parses the full-ISO `Date`, and `_row_value` parses `Chin` once it is in
  `value_keys`. The only gap is that `_extract_rows` does not parse CSV text. The
  harness validates this by calling the real `_parse_daily_payload` on CSV→rows.

## Exact changes

### 1. Add a CSV helper (new module-level function)

Add beside `_extract_rows`:

```python
import csv
import io

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
```

(Optional, equivalent alternative: extend `_extract_rows` to accept a `str` and
delegate to `_csv_text_to_rows`. A dedicated helper keeps `_extract_rows` focused
on the JSON shapes and is preferred.)

### 2. Replace `_fetch_columbia` (DART) — make it real

Today it requests `outputFormat=csvSingle` and calls `response.json()`. Replace the body:

```python
# DART adult-daily report query that returns CSV (csvSingle returns an HTML
# error page). proj=BON, full-ISO Date, adult Chinook in the "Chin" column.
_DART_PARAMS = {
    "sc": "1", "mgconfig": "adult", "outputFormat": "csv",
    "proj": "BON", "span": "no", "startdate": "1/1", "enddate": "12/31", "run": "",
}
_DART_VALUE_KEYS = ("Chin", "chin", "Chinook", "chinook")

def _fetch_columbia(self, year: int) -> Dict[str, float]:
    """Fetch DART Bonneville daily adult Chinook passage -> {ISO date: count}."""
    params = {**_DART_PARAMS, "year": str(year)}
    # The report is built on first request; retry past the transient err- HTML wrapper.
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
        time.sleep(2)  # add `import time` at module top
    return {}
```

Notes:
- `value_keys` MUST include `Chin` (current keys `count/passage/chinook/adult/value/index`
  never match the real column, so even a parsed CSV would yield `{}`).
- Keep the existing `except Exception` guard in `fetch_run_index` — on any failure
  this still returns `{}` and falls through.

### 3. Disable `_fetch_fraser` (Albion) honestly — document, do not fake

The live Albion source has no machine-readable daily series. Replace the live HTTP
attempt with an honest no-op so the adapter falls through to DART (not climatology),
and record why:

```python
def _fetch_fraser(self, year: int) -> Dict[str, float]:
    """Albion (Fraser) daily Chinook CPUE.

    DISABLED: the live DFO Albion page publishes daily CPUE only as JPG graph
    images (no HTML table / CSV / JSON), and the historical machine-readable FOS
    endpoint host (www-ops2.pac.dfo-mpo.gc.ca) no longer resolves. Returning {}
    lets fetch_run_index fall through to the real DART (Columbia) feed. Re-enable
    if/when a machine-readable Fraser feed is identified. Validated 2026-06-27,
    salmon_validation.py.
    """
    return {}
```

(If you prefer to keep the HTTP probe for monitoring, it must still `return {}` —
do not attempt to parse the image-only page into a series.)

### 4. Module docstring

Update the "UNCONFIRMED" paragraph: DART (Columbia/Bonneville) is CONFIRMED and
parsed (CSV, `Chin` column, validated 2026-06-27); Albion (Fraser) remains
unavailable as a machine-readable feed (image-only). Update `_DART_URL` comment to
note the CSV params; note `_ALBION_URL` is a redirect stub to `albion-eng.html`.

## Honesty / promotion notes (B.1–B.3)

- This patch makes a **real** feed parse; it does **not** promote confidence. L3
  promotion remains a Wave 3 gate + recorded supervisor decision.
- **Biological caveat (record in the L3 verdict):** the DART Bonneville dominant
  peak is the **Columbia fall** Chinook run (~day-of-year 250), a different stock
  than the **Fraser summer** Chinook the climatology placeholder models and that
  SRKW chiefly target. DART is the documented SECONDARY source — a real, parseable
  proxy, not the Fraser primary. Whether it actually aligns with SRKW presence is
  the Wave 3 lag-scan's call (`modeling/studies/salmon_lag.py`), which already
  gates on `real_feed_only` AND a permutation p<0.05. A real-but-non-aligning feed
  still leaves L3 withheld — honest, not promoted.
- If DART is unreachable at fit time, the adapter falls back to climatology and the
  lag-scan reports `withheld` (placeholder feed) — unchanged, honest behavior.

## Risk register

- DART intermittency: the `err-` HTML wrapper on first/cold query. Mitigated by the
  retry-on-non-CSV loop; the harness saw both states on 2026-06-27.
- DFO host DNS flakiness: `www.pac.dfo-mpo.gc.ca` getaddrinfo intermittently fails
  from this host even though `nslookup` resolves it. Does not affect DART. Albion
  stays disabled regardless.
- Stock-relevance caveat above — the main scientific risk; surface it in the L3 verdict.
- DART column/format drift year to year (the docstring's original warning stands);
  the `value_keys` tuple and content-type check make the parse defensive, and the
  harness is the regression check before any future re-enable.
