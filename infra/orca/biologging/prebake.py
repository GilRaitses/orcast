#!/usr/bin/env python3
"""ORCA OG-PREBAKE: offline biologging H5 -> rig-DOF motion artifact baker.

This is the Option B pre-bake tool ratified in
``.cca/catalogue/O0/20260628_orca-biologging-twin/SIGN_OFF.md``. It runs OFFLINE
(never in the web bundle), opens an animaltags / tagtools HDF5 (a NetCDF-4 file is
a valid HDF5 file) biologging deployment, derives the per-sample motion channels,
maps them onto the orca rig DOFs defined in ``docs/orca/SKELETON.md``, and writes:

  * a compact little-endian Float32 ``.bin`` of the per-sample channels, and
  * a JSON manifest (sample rate, channel order, units, datum, duration,
    ``simulated`` flag, provenance) so a plain ``fetch`` in the web loader can read
    it with no HDF5 dependency.

Channel -> DOF mapping and sign conventions are taken verbatim from
``infra/orca/biologging/OG-R_h5_mapping.md`` section 3 and ``docs/orca/SKELETON.md``
sections 3 to 5. The full format spec is in ``OG-PREBAKE_NOTES.md``.

HONESTY (locked, see OG-R_h5_mapping.md section 5): the orca is a modeled animal
driven by simulated or partnership-gated telemetry. This baker propagates the
source ``simulated`` flag into the manifest and never asserts a measured swim of a
named individual unless a real, agreement-covered H5 is loaded.

Dependencies: numpy + h5py only (pinned in requirements.txt). No scipy: the
band-pass and analytic-signal (Hilbert) steps are implemented with numpy FFTs so
the offline tool stays small.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

# --------------------------------------------------------------------------- #
# Format contract (also documented in OG-PREBAKE_NOTES.md).
# The web loader (later OG-BUILD wave) reads exactly this.
# --------------------------------------------------------------------------- #

FORMAT_NAME = "orca-biologging-prebake"
FORMAT_VERSION = 1

# Channel order in the .bin, sample-major (interleaved). For sample i the bytes
# are [c0_i, c1_i, ... c6_i] as float32-LE; the whole bin is a row-major
# (n_samples, n_channels) Float32Array.
#
# Angles are RADIANS at the rig boundary (SKELETON.md section 4). Depth is METRES
# positive-down on the NAVD88-0m datum; the web applies Y = -depth_m *
# worldUnitsPerMeter using the LIVE fit value (never a hard-coded scale).
CHANNELS: List[Dict[str, Any]] = [
    {
        "name": "t_s",
        "unit": "seconds",
        "dof": None,
        "desc": "Sample time on the common time base, t = i / sample_rate_hz.",
    },
    {
        "name": "body_yaw_rad",
        "unit": "radians",
        "dof": "body_yaw",
        "frame": "true heading; NED 0=North, increasing clockwise toward East",
        "sign": (
            "Stored as declination-corrected TRUE heading in radians. Web maps to a "
            "rotation about scene +Y so the rostrum (+X) points along the heading "
            "(SKELETON.md section 5: +Y up, +X forward, +Z port)."
        ),
        "source": "m2h(animal-frame M, A) + magnetic declination",
    },
    {
        "name": "body_pitch_rad",
        "unit": "radians",
        "dof": "body_pitch",
        "frame": "rotation about lateral Z",
        "sign": "positive = nose-up (tagtools a2pr convention, SKELETON.md section 3/5)",
        "source": "a2pr(animal-frame A)",
    },
    {
        "name": "body_roll_rad",
        "unit": "radians",
        "dof": "body_roll",
        "frame": "rotation about longitudinal +X",
        "sign": "positive = dorsal surface banks toward +Z (port/left bank); full +/-pi range",
        "source": "a2pr(animal-frame A)",
    },
    {
        "name": "depth_m",
        "unit": "metres positive-down",
        "dof": "world Y (translation, not a bone)",
        "frame": "NAVD88-0m datum (scene Y 0)",
        "sign": (
            "Web places the root at Y = -depth_m * worldUnitsPerMeter using the LIVE "
            "fit value (DEFAULT_WORLD_UNITS_PER_METER or the per-fit value the scene "
            "attaches), via setDepthPose. Not scaled here."
        ),
        "source": "depth from pressure channel P",
    },
    {
        "name": "fluke_phase_rad",
        "unit": "radians [0, 2*pi)",
        "dof": "caudal[0..5] fluke beat (setFluke phase)",
        "frame": "dorso-ventral, pitch-axis (Z) on the caudal chain",
        "sign": (
            "Instantaneous phase of the band-passed dorso-ventral (heave, Az) "
            "oscillation. Continuous so the beat stays smooth between samples."
        ),
        "source": "Hilbert phase of band-passed animal-frame Az (static/gravity removed)",
    },
    {
        "name": "fluke_amplitude",
        "unit": "normalized 0..1",
        "dof": "caudal[0..5] fluke beat (setFluke amplitude)",
        "frame": "scales the per-joint amplitude profile (0 = no beat, 1 = full nominal stroke)",
        "sign": "Envelope (DBA) of the band-passed Az oscillation, normalized to 0..1.",
        "source": "Hilbert envelope of band-passed animal-frame Az",
    },
]

CHANNEL_NAMES: List[str] = [c["name"] for c in CHANNELS]
N_CHANNELS = len(CHANNELS)

# Orca dominant stroke band (OG-R_h5_mapping.md section 1.5): about 0.3-1.0 Hz,
# cruising near 0.4-0.6 Hz. Used both to band-pass real Az and to seed the dev synth.
STROKE_BAND_HZ: Tuple[float, float] = (0.3, 1.0)

DATUM = {
    "name": "NAVD88-0m",
    "note": (
        "depth_m is positive-down metres. The web applies Y = -depth_m * "
        "worldUnitsPerMeter at the live fit value; vertical placement is NOT baked in."
    ),
}


@dataclass
class MotionTrack:
    """One deployment's per-sample, rig-ready motion on a common time base."""

    sample_rate_hz: float
    t_s: np.ndarray
    body_yaw_rad: np.ndarray
    body_pitch_rad: np.ndarray
    body_roll_rad: np.ndarray
    depth_m: np.ndarray
    fluke_phase_rad: np.ndarray
    fluke_amplitude: np.ndarray
    simulated: bool
    provenance: str
    declination_deg_applied: float = 0.0
    source: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def columns(self) -> List[np.ndarray]:
        return [
            self.t_s,
            self.body_yaw_rad,
            self.body_pitch_rad,
            self.body_roll_rad,
            self.depth_m,
            self.fluke_phase_rad,
            self.fluke_amplitude,
        ]

    @property
    def n_samples(self) -> int:
        return int(self.t_s.shape[0])


# --------------------------------------------------------------------------- #
# Writer (shared by the real H5 baker AND the dev-track synthesizer so the bin
# format is byte-identical for whatever the web loader reads).
# --------------------------------------------------------------------------- #


def write_track(track: MotionTrack, bin_path: Path, manifest_path: Path) -> Dict[str, Any]:
    """Write the Float32 .bin and the JSON manifest. Returns the manifest dict."""
    cols = track.columns()
    n = track.n_samples
    for name, col in zip(CHANNEL_NAMES, cols):
        if col.shape[0] != n:
            raise ValueError(f"channel {name!r} length {col.shape[0]} != n_samples {n}")

    # Row-major (n_samples, n_channels), little-endian float32, sample-major.
    interleaved = np.empty((n, N_CHANNELS), dtype="<f4")
    for j, col in enumerate(cols):
        interleaved[:, j] = np.asarray(col, dtype="<f4")
    if not np.all(np.isfinite(interleaved)):
        raise ValueError("non-finite value in motion track; refusing to write")

    bin_path.parent.mkdir(parents=True, exist_ok=True)
    bin_path.write_bytes(interleaved.tobytes(order="C"))

    duration_s = float(track.t_s[-1] - track.t_s[0]) if n > 1 else 0.0
    manifest: Dict[str, Any] = {
        "format": FORMAT_NAME,
        "format_version": FORMAT_VERSION,
        "simulated": bool(track.simulated),
        "provenance": track.provenance,
        "source": track.source,
        "bin_file": bin_path.name,
        "layout": "interleaved-sample-major float32 little-endian, shape (n_samples, n_channels)",
        "dtype": "float32-le",
        "byte_order": "little-endian",
        "sample_rate_hz": float(track.sample_rate_hz),
        "n_samples": n,
        "n_channels": N_CHANNELS,
        "duration_s": duration_s,
        "angle_units": "radians",
        "declination_deg_applied": float(track.declination_deg_applied),
        "stroke_band_hz": list(STROKE_BAND_HZ),
        "datum": DATUM,
        "channels": CHANNELS,
        "notes": track.notes,
        "bin_bytes": bin_path.stat().st_size,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


# --------------------------------------------------------------------------- #
# DSP helpers (numpy-only; no scipy dependency).
# --------------------------------------------------------------------------- #


def bandpass_fft(x: np.ndarray, fs: float, f_lo: float, f_hi: float) -> np.ndarray:
    """Zero-phase band-pass via real FFT masking. Mean-removed input."""
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    if n < 4:
        return x - x.mean()
    spec = np.fft.rfft(x - x.mean())
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    mask = (freqs >= f_lo) & (freqs <= f_hi)
    spec[~mask] = 0.0
    return np.fft.irfft(spec, n=n)


def analytic_signal(x: np.ndarray) -> np.ndarray:
    """Analytic signal via FFT (numpy implementation of scipy.signal.hilbert)."""
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    spec = np.fft.fft(x)
    h = np.zeros(n)
    if n % 2 == 0:
        h[0] = h[n // 2] = 1.0
        h[1 : n // 2] = 2.0
    else:
        h[0] = 1.0
        h[1 : (n + 1) // 2] = 2.0
    return np.fft.ifft(spec * h)


def stroke_phase_amplitude(
    az: np.ndarray, fs: float, band: Tuple[float, float] = STROKE_BAND_HZ
) -> Tuple[np.ndarray, np.ndarray]:
    """Extract fluke-beat phase [0, 2*pi) and a 0..1 amplitude envelope from Az.

    Procedure per OG-R_h5_mapping.md section 1.5: remove static/orientation
    (the band-pass low edge does this), keep the orca stroke band, then read the
    instantaneous phase and envelope from the analytic signal.
    """
    osc = bandpass_fft(az, fs, band[0], band[1])
    z = analytic_signal(osc)
    phase = np.mod(np.angle(z), 2.0 * np.pi)
    env = np.abs(z)
    peak = float(np.percentile(env, 99)) if env.size else 0.0
    amp = np.clip(env / peak, 0.0, 1.0) if peak > 0 else np.zeros_like(env)
    return phase.astype(np.float64), amp.astype(np.float64)


# --------------------------------------------------------------------------- #
# tagtools-equivalent orientation derivation (radians).
# --------------------------------------------------------------------------- #


def a2pr(aa: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Pitch and roll (radians) from animal-frame accelerometer, tagtools a2pr.

    aa columns: [x = longitudinal/anterior+, y = lateral, z = dorso-ventral/down+].
    pitch positive = nose-up; roll about the longitudinal axis (SKELETON section 5).
    """
    a = np.asarray(aa, dtype=np.float64)
    norm = np.linalg.norm(a, axis=1)
    norm[norm == 0] = 1.0
    a = a / norm[:, None]
    pitch = np.arctan2(a[:, 0], np.sqrt(a[:, 1] ** 2 + a[:, 2] ** 2))
    roll = np.arctan2(a[:, 1], a[:, 2])
    return pitch, roll


def m2h(ma: np.ndarray, pitch: np.ndarray, roll: np.ndarray) -> np.ndarray:
    """Tilt-compensated magnetic heading (radians) from animal-frame M, tagtools m2h.

    Returns magnetic heading in NED (0 = North, increasing clockwise). The caller
    adds magnetic declination to get true heading.
    """
    m = np.asarray(ma, dtype=np.float64)
    norm = np.linalg.norm(m, axis=1)
    norm[norm == 0] = 1.0
    m = m / norm[:, None]
    mx, my, mz = m[:, 0], m[:, 1], m[:, 2]
    cp, sp = np.cos(pitch), np.sin(pitch)
    cr, sr = np.cos(roll), np.sin(roll)
    xh = mx * cp + my * sr * sp + mz * cr * sp
    yh = my * cr - mz * sr
    return np.arctan2(-yh, xh)


# --------------------------------------------------------------------------- #
# H5 reading.
# --------------------------------------------------------------------------- #


def _resample(t_src: np.ndarray, x_src: np.ndarray, t_dst: np.ndarray) -> np.ndarray:
    """Linear resample a channel onto the common time base."""
    return np.interp(t_dst, t_src, x_src)


def _resample_angle(t_src: np.ndarray, ang_src: np.ndarray, t_dst: np.ndarray) -> np.ndarray:
    """Resample an angle channel via its sin/cos so wrap-around is handled."""
    s = np.interp(t_dst, t_src, np.sin(ang_src))
    c = np.interp(t_dst, t_src, np.cos(ang_src))
    return np.arctan2(s, c)


def _read_sensor(h5: "Any", names: Sequence[str]) -> Optional[Tuple[np.ndarray, float]]:
    """Read the first present sensor struct from a list of candidate names.

    Returns (data, fs). animaltags sensor structs store the array plus an ``fs``
    (sampling rate) attribute; this reads either an HDF5 group with a ``data``
    member and ``sampling_rate``/``fs`` attr, or a plain dataset.
    """
    for name in names:
        if name not in h5:
            continue
        node = h5[name]
        fs = None
        data = None
        # animaltags-style group: members 'data' + attrs.
        if hasattr(node, "keys"):
            if "data" in node:
                data = np.asarray(node["data"][()], dtype=np.float64)
            for key in ("sampling_rate", "fs", "SamplingRate"):
                if key in node.attrs:
                    fs = float(np.ravel(node.attrs[key])[0])
                    break
        else:
            data = np.asarray(node[()], dtype=np.float64)
            for key in ("sampling_rate", "fs", "SamplingRate"):
                if key in node.attrs:
                    fs = float(np.ravel(node.attrs[key])[0])
                    break
        if data is None:
            continue
        if fs is None:
            raise ValueError(
                f"sensor {name!r} has no sampling-rate attribute (fs / sampling_rate); "
                "cannot place it on a time base"
            )
        return data, fs
    return None


def bake_h5(
    input_path: Path,
    out_rate_hz: float = 25.0,
    declination_deg: float = 0.0,
    simulated_override: Optional[bool] = None,
) -> MotionTrack:
    """Read an animaltags/tagtools H5 and derive a rig-ready MotionTrack.

    Expects animal-frame accel/mag (``Aa``/``Aw``, ``Ma``/``Mw``) and pressure
    ``P``. If a derived-angle product already carries ``pitch``/``roll``/``heading``
    (the in-repo BigQuery contract, OG-R_h5_mapping.md section 1.3), those are used
    directly instead of recomputing with a2pr/m2h.
    """
    try:
        import h5py  # imported lazily so the dev synth needs only numpy
    except ImportError as exc:  # pragma: no cover - environment guard
        raise SystemExit(
            "h5py is required to bake a real H5. Install the pinned offline deps: "
            "pip install -r infra/orca/biologging/requirements.txt"
        ) from exc

    with h5py.File(str(input_path), "r") as h5:
        simulated_attr = None
        for key in ("simulated", "is_simulated"):
            if key in h5.attrs:
                simulated_attr = bool(np.ravel(h5.attrs[key])[0])
                break

        pressure = _read_sensor(h5, ("P", "p", "depth", "Depth"))
        if pressure is None:
            raise ValueError("no pressure/depth channel (P) found in H5")
        depth_src, fs_depth = pressure

        # Build the common time base from depth duration, resample everything to it.
        n_depth = depth_src.shape[0]
        duration_s = (n_depth - 1) / fs_depth if n_depth > 1 else 0.0
        n_out = max(int(round(duration_s * out_rate_hz)) + 1, 1)
        t_dst = np.arange(n_out, dtype=np.float64) / out_rate_hz
        t_depth = np.arange(n_depth, dtype=np.float64) / fs_depth
        depth_m = _resample(t_depth, np.ravel(depth_src), t_dst)

        notes: List[str] = []

        # Prefer a derived-angle product if present.
        have_derived = all(k in h5 for k in ("pitch", "roll", "heading"))
        if have_derived:
            pr = _read_sensor(h5, ("pitch",))
            rr = _read_sensor(h5, ("roll",))
            hr = _read_sensor(h5, ("heading",))
            assert pr and rr and hr
            pitch_src, fs_p = pr
            roll_src, fs_r = rr
            head_src, fs_h = hr
            # The in-repo schema stores DEGREES; tagtools stores radians. Detect by
            # range and convert to radians (OG-R_h5_mapping.md section 3).
            def _to_rad(arr: np.ndarray) -> np.ndarray:
                arr = np.ravel(arr)
                if np.nanmax(np.abs(arr)) > 2.0 * np.pi:
                    return np.deg2rad(arr)
                return arr

            pitch = _resample(np.arange(pitch_src.shape[0]) / fs_p, _to_rad(pitch_src), t_dst)
            roll = _resample(np.arange(roll_src.shape[0]) / fs_r, _to_rad(roll_src), t_dst)
            heading_mag = _resample_angle(
                np.arange(head_src.shape[0]) / fs_h, _to_rad(head_src), t_dst
            )
            notes.append("Orientation taken from the derived pitch/roll/heading product.")
        else:
            accel = _read_sensor(h5, ("Aa", "Aw", "A"))
            mag = _read_sensor(h5, ("Ma", "Mw", "M"))
            if accel is None:
                raise ValueError("no animal-frame accelerometer (Aa/Aw/A) found in H5")
            a_src, fs_a = accel
            t_a = np.arange(a_src.shape[0]) / fs_a
            pitch_a, roll_a = a2pr(a_src)
            pitch = _resample_angle(t_a, pitch_a, t_dst)
            roll = _resample_angle(t_a, roll_a, t_dst)
            if mag is not None:
                m_src, fs_m = mag
                t_m = np.arange(m_src.shape[0]) / fs_m
                m_on_a = np.column_stack(
                    [_resample(t_m, m_src[:, k], t_a) for k in range(m_src.shape[1])]
                )
                heading_mag = _resample_angle(t_a, m2h(m_on_a, pitch_a, roll_a), t_dst)
                notes.append("Orientation derived with tagtools a2pr/m2h from animal-frame A/M.")
            else:
                heading_mag = np.zeros_like(t_dst)
                notes.append(
                    "No magnetometer present; heading set to 0. Derived pitch/roll only."
                )

        heading_true = heading_mag + np.deg2rad(declination_deg)

        # Fluke beat from animal-frame dorso-ventral (Az) heave.
        accel = _read_sensor(h5, ("Aa", "Aw", "A"))
        if accel is not None:
            a_src, fs_a = accel
            az = np.ravel(a_src[:, 2]) if a_src.ndim == 2 else np.ravel(a_src)
            phase_a, amp_a = stroke_phase_amplitude(az, fs_a, STROKE_BAND_HZ)
            t_a = np.arange(az.shape[0]) / fs_a
            fluke_phase = _resample_angle(t_a, phase_a, t_dst) % (2.0 * np.pi)
            fluke_amp = np.clip(_resample(t_a, amp_a, t_dst), 0.0, 1.0)
        else:
            fluke_phase = np.zeros_like(t_dst)
            fluke_amp = np.zeros_like(t_dst)
            notes.append("No accelerometer for fluke beat; fluke channels are zero.")

        simulated = simulated_attr if simulated_attr is not None else False
        if simulated_override is not None:
            simulated = simulated_override

        return MotionTrack(
            sample_rate_hz=float(out_rate_hz),
            t_s=t_dst,
            body_yaw_rad=heading_true,
            body_pitch_rad=pitch,
            body_roll_rad=roll,
            depth_m=depth_m,
            fluke_phase_rad=fluke_phase,
            fluke_amplitude=fluke_amp,
            simulated=bool(simulated),
            provenance=(
                f"Baked offline from H5 {input_path.name!r} by prebake.py "
                f"(format {FORMAT_NAME} v{FORMAT_VERSION})."
            ),
            declination_deg_applied=float(declination_deg),
            source={
                "type": "h5",
                "file": input_path.name,
                "out_rate_hz": float(out_rate_hz),
                "simulated_attr": simulated_attr,
            },
            notes=notes,
        )


def _cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bake an animaltags/tagtools H5 biologging file into a rig-DOF "
        "Float32 .bin + JSON manifest (ORCA OG-PREBAKE, Option B)."
    )
    parser.add_argument("input", type=Path, help="path to the animaltags/tagtools .h5 / .nc file")
    parser.add_argument(
        "-o",
        "--out-dir",
        type=Path,
        default=Path("."),
        help="output directory for the .bin and .json (default: current dir)",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="output basename (default: input stem). Writes <name>.bin and <name>.json",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=25.0,
        help="output sample rate in Hz for the common time base (default: 25)",
    )
    parser.add_argument(
        "--declination",
        type=float,
        default=0.0,
        help="magnetic declination in degrees to add to magnetic heading (default: 0)",
    )
    parser.add_argument(
        "--mark-simulated",
        dest="simulated",
        action="store_true",
        default=None,
        help="force simulated:true in the manifest (honesty override)",
    )
    parser.add_argument(
        "--mark-measured",
        dest="simulated",
        action="store_false",
        help="force simulated:false (ONLY for a real, agreement-covered H5)",
    )
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return 2

    track = bake_h5(
        args.input,
        out_rate_hz=args.rate,
        declination_deg=args.declination,
        simulated_override=args.simulated,
    )
    base = args.name or args.input.stem
    bin_path = args.out_dir / f"{base}.bin"
    manifest_path = args.out_dir / f"{base}.json"
    manifest = write_track(track, bin_path, manifest_path)
    print(
        f"wrote {bin_path} ({manifest['bin_bytes']} bytes) and {manifest_path} "
        f"| n_samples={manifest['n_samples']} rate={manifest['sample_rate_hz']}Hz "
        f"simulated={manifest['simulated']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
