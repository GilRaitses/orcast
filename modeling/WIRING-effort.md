# Wiring spec: `modeling/effort.py` -> `build_design` + `_station_intensity_fn`

Audience: the Wave 2 modeling integrator (the single editor of `modeling/fit_kernels.py`
and `modeling/studies/level2_multistation.py`). Agent A does NOT edit any convergence file or
`modeling/design.py`; this doc tells you exactly what to change and why.

`modeling/effort.py` is a pure, side-effect-free module. It is the per-station effort / `log E`
model the conditional intensity should consume. Two wiring points, both small.

## Exported API (stable contract)

```python
from modeling.effort import (
    station_log_effort,      # (uptime, station, grid_times, *, fallback=, detection_times=, min_effort=) -> np.ndarray  (log E_frac at times; 0 when up)
    exposure_for_bins,       # (uptime, station, bin_centers, *, bin_hours=, fallback=, detection_times=) -> np.ndarray   (effort-hours per bin)
    relative_effort,         # (times, uptime, station, *, fallback=, detection_times=) -> np.ndarray                     (E_frac in [min_effort,1])
    resolve_uptime_records,  # (uptime, station) -> list[dict] | None   (cross-namespace station-key binding)
    normalize_station_key,   # (name) -> canonical acoustic key
    uptime_step,             # (records) -> (times_hours, up_fraction) | None
    uptime_binds,            # (uptime, station, detection_times=) -> bool  (exists AND overlaps the window)
    effort_summary,          # (uptime, acoustic_by_station, *, bin_hours=, fallback=) -> dict  (the honest diagnostic)
    FALLBACK_CONTINUOUS, FALLBACK_OBSERVED_WINDOW, FALLBACK_DETECTION_DENSITY,
    DEFAULT_MIN_EFFORT_FRACTION,
)
```

`uptime` accepts either the `{station_key: [records]}` dict that `read_streams` returns for the
`station_uptime` stream, or a single station's record list.

Units (must stay consistent across the two call sites):
- `exposure_for_bins` returns **effort-hours per bin** = `bin_hours * E_frac`. This matches the
  existing `exposure` column whose GLM offset is `log(exposure)`. Use it in `build_design`.
- `station_log_effort` returns **`log E_frac`** (relative, `0` when fully up). Use it in the
  intensity function. It differs from `log(exposure)` only by the constant `log(bin_hours)`, which
  the fitted intercept already absorbs, so do NOT add `log(bin_hours)` inside the intensity.

## Point 1 -- `build_design` in `modeling/design.py`

Today (`design.py` ~L155, ~L167, ~L186):

```python
step = _uptime_step(uptime_by_station.get(station))   # exact-key lookup only
if step is not None:
    effort_assumed = False
...
exposure = _exposure_for_bin(center, bin_hours, step)
...
df.attrs["effort_assumed_continuous"] = effort_assumed
```

The bug: `uptime_by_station.get(station)` looks up by the **acoustic** key (`haro_strait`,
`orcasound_lab`), but `station_uptime` is keyed by node id (`rpi_orcasound_lab`, `rpi_north_sjc`,
`rpi_andrews_bay`; there is no `haro_strait` node). The keys never match, so `effort_assumed` stays
`True` and the offset is flat -- the prime suspect the dispatch names.

Replace with the effort module (vectorised over the bin centres for the station):

```python
from modeling.effort import exposure_for_bins, resolve_uptime_records, uptime_binds, FALLBACK_CONTINUOUS

# inside the per-station loop, after `centers` is computed:
events = events  # the per-station event_times_hours already in scope
exposure = exposure_for_bins(
    uptime_by_station, station, centers,
    bin_hours=bin_hours, fallback=FALLBACK_CONTINUOUS, detection_times=events,
)
if uptime_binds(uptime_by_station, station, detection_times=events):
    effort_assumed = False
# then build rows from `centers`, `counts`, and the `exposure` array element-wise,
# keeping the existing `exposure <= min_exposure` drop.
```

What it replaces: the per-bin `_exposure_for_bin(center, bin_hours, step)` scalar call and the
exact-key `uptime_by_station.get(station)`. `resolve_uptime_records` does the `rpi_*` ->
acoustic-key binding; `uptime_binds` makes `effort_assumed_continuous` honest (it is true only when
a uptime series both exists AND overlaps the detection window, not merely exists).

Keep `fallback=FALLBACK_CONTINUOUS` as the default for any fit that feeds confidence. Do NOT use
`FALLBACK_DETECTION_DENSITY` in a confidence-bearing fit (see "Honesty" below).

## Point 2 -- `_station_intensity_fn` / `_time_rescaling_report` in `modeling/fit_kernels.py`

`_station_intensity_fn` (`fit_kernels.py` ~L483-504) builds the continuous conditional intensity
that `_time_rescaling_report` integrates. It currently returns `exp(b0 + a_station + kernels)` with
**no effort term**. For an observed point process the conditional intensity is
`lambda_obs(t) = exp(b0 + kernels) * E(t)`, so across a verified detector-down interval the hazard
must not accumulate. Add `log E(t)` to the log-rate.

Thread `uptime` (and the station's event times) into the function and add the offset:

```python
from modeling.effort import station_log_effort, FALLBACK_CONTINUOUS

def _station_intensity_fn(model, station, lat, lng, tide, uptime=None,
                          detection_times=None, effort_fallback=FALLBACK_CONTINUOUS):
    base = model.intercept + model.station_effects.get(station, 0.0)

    def intensity(t_hours):
        t_hours = np.atleast_1d(np.asarray(t_hours, dtype=float))
        log_rate = np.full(t_hours.shape, base)
        # ... existing kernel phase accumulation, unchanged ...
        log_rate = log_rate + station_log_effort(
            uptime, station, t_hours,
            fallback=effort_fallback, detection_times=detection_times,
        )
        return np.exp(log_rate)

    return intensity
```

Then in `_time_rescaling_report` (`fit_kernels.py` ~L882-898) pass the new args through. The
function already has `acoustic` and builds `events`; thread `uptime` from `run_fit` into it:

```python
def _time_rescaling_report(model, acoustic, tide, bin_hours, uptime=None):
    ...
    for station, records in acoustic.items():
        events = event_times_hours(records)
        ...
        intensity = _station_intensity_fn(
            model, station, lat, lng, tide,
            uptime=uptime, detection_times=events,
        )
        res = run_time_rescaling(events, intensity=intensity, grid_step=bin_hours, min_ieis=20)
```

And at the call site in `run_fit` (`fit_kernels.py` ~L722):

```python
tr = _time_rescaling_report(model, acoustic, tide, bin_hours, uptime=uptime)
```

`uptime` is already read in `run_fit` (`read_streams` returns `acoustic, uptime, currents`), so it
is in scope; just pass it.

What it replaces: nothing is removed -- this ADDS the missing `log E(t)` multiplier to the existing
kernel intensity. With `fallback=continuous` and fully-up effort it adds `0.0`, so it is a strict
no-op there and cannot change a passing result; it only suppresses intensity across verified
downtime.

## Validation result this wiring is based on (measured, S3 store)

Run: multi-station memory store (production `haro_strait` from S3 + cached OrcaHello index for
`orcasound_lab`/`north_san_juan_channel`/`andrews_bay`) + `station_uptime` from S3, upload disabled,
no fit written. Measured by `modeling.effort.effort_summary`:

- Station-key binding now works: `orcasound_lab -> rpi_orcasound_lab`, `north_san_juan_channel ->
  rpi_north_sjc`, `andrews_bay -> rpi_andrews_bay` all resolve (346/346/347 samples).
  `haro_strait` resolves to no uptime (there is no Haro Strait node -- honest, not an error).
- BUT no station's uptime **binds the detection window**: the `station_uptime` stream covers
  2026-06-20 -> 2026-06-27 only, while the detections are 2020-2021 (haro_strait) and the cached
  windows; overlap is 0. Each per-station series is also constant within its own window
  (`uptime_constant_in_window: true`; up-fraction 1.0 for orcasound_lab/north_sjc, 0.0 for
  andrews_bay). So `effort_assumed_continuous` is correctly `true` for every station and the real
  per-station `log E` is flat (`log_effort_std = 0`).
- On SYNTHETIC transitioning uptime (up -> down -> up inside the window) the same API yields a
  non-degenerate series: `log E` std `3.26`, values `{0.0, -6.908}`, exposure `{1.0 h, 0.001 h}`.
  The module is correct; today's *data* is degenerate.

## Honesty / expectations (charter B.2, B.3)

- Wiring this in is necessary plumbing and fixes the station-key mismatch, but on the **current**
  S3 data it does not change time-rescaling: the uptime is temporally disjoint and constant, so
  `log E(t) = 0` everywhere and `lambda_obs = lambda`. Do not expect the pooled KS to move from this
  change alone. The dominant time-rescaling failure is the burst/refractory structure of the
  detections (median IEI ~0.02 h with 80% of IEIs < 0.5 h, vs 7% of gaps > 24 h and a 356 h max
  gap), which a smooth cyclic intensity cannot reproduce -- that is Agent B's diagnostic and is not
  an effort artefact.
- `FALLBACK_DETECTION_DENSITY` exists but is OFF by default and is CIRCULAR (it conditions effort on
  the very detections the kernels model). Never use it in a confidence-bearing fit; it is for
  sensitivity analysis only. `FALLBACK_OBSERVED_WINDOW` only bounds exposure to the deployment span
  and is a no-op inside the span (so a no-op for the event-spanning time-rescaling grid).
- The module fabricates no uptime. When uptime is absent or non-binding it reports
  `effort_assumed_continuous: true` and a flat offset, exactly as the honesty gate requires.
- This change earns no confidence by itself and must be a recorded integration, not a promotion
  (B.1, B.5): keep `_maybe_write_s3` disabled and `write_outputs=False` for any refit that exercises
  it.
