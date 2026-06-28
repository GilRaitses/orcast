// Perceptually-uniform bathymetric depth ramp for the WS-BATHY seabed tint.
//
// MODELED, NOT MEASURED. This ramp STYLES the modeled CUDEM topobathy seabed.
// It is a colormap, not a survey: it assigns color to a depth value, it does not
// assert that any depth was measured.
//
// Palette: the cmocean `deep` family (Thyng et al. 2016, Oceanography, "True
// Colors of Oceanography"; cmocean https://matplotlib.org/cmocean/). `deep` is a
// sequential, perceptually-uniform, colorblind-safe colormap built for
// bathymetry: light at the shallows (t=0) darkening through teal and blue to a
// dark blue/purple at depth (t=1). It is deliberately NOT jet/rainbow, which
// introduces false gradients and local-maxima bias and is not colorblind-safe.
//
// `t` runs 0 -> 1 where 0 is the SHALLOW endpoint (sea level / least submerged)
// and 1 is the DEEP endpoint (deepest seabed). The caller maps real depth onto
// `t`, so a deeper seabed maps to a darker, bluer-purple color.
//
// The stops below are sampled from the published cmocean `deep` 256-entry table
// at even intervals. The stops are themselves perceptually spaced, so linear
// interpolation between adjacent stops preserves uniformity to display tolerance.
// Values are display-sRGB in [0,1]; convert to the renderer working space with
// THREE.Color.setRGB(r, g, b, THREE.SRGBColorSpace) before writing to a buffer.

export interface RampStop {
  /** Position in [0,1]; 0 = shallow endpoint, 1 = deep endpoint. */
  t: number;
  /** Display-sRGB [r, g, b] in [0,1]. */
  rgb: [number, number, number];
}

/**
 * cmocean `deep` sampled at nine even stops, shallow (t=0) -> deep (t=1).
 * Light cream-green shallows, through green/teal/cyan, to a dark blue/purple
 * deep endpoint.
 */
export const DEEP_RAMP_STOPS: ReadonlyArray<RampStop> = [
  { t: 0.0, rgb: [0.9935, 0.9929, 0.8055] },
  { t: 0.125, rgb: [0.7464, 0.8896, 0.658] },
  { t: 0.25, rgb: [0.4882, 0.8009, 0.6515] },
  { t: 0.375, rgb: [0.3375, 0.7032, 0.6633] },
  { t: 0.5, rgb: [0.2629, 0.601, 0.668] },
  { t: 0.625, rgb: [0.2257, 0.4977, 0.6558] },
  { t: 0.75, rgb: [0.2353, 0.3919, 0.6168] },
  { t: 0.875, rgb: [0.221, 0.2789, 0.5076] },
  { t: 1.0, rgb: [0.1717, 0.1029, 0.2901] },
];

/** The shallow (t=0) endpoint of the deep ramp, display-sRGB [0,1]. */
export const DEEP_RAMP_SHALLOW: [number, number, number] = [...DEEP_RAMP_STOPS[0].rgb];

/** The deep (t=1) endpoint of the deep ramp, display-sRGB [0,1]. */
export const DEEP_RAMP_DEEP: [number, number, number] = [
  ...DEEP_RAMP_STOPS[DEEP_RAMP_STOPS.length - 1].rgb,
];

function toHex([r, g, b]: [number, number, number]): string {
  const c = (v: number) =>
    Math.max(0, Math.min(255, Math.round(v * 255)))
      .toString(16)
      .padStart(2, "0");
  return `#${c(r)}${c(g)}${c(b)}`;
}

/** Shallow endpoint as a `#rrggbb` sRGB hex string. */
export const DEEP_RAMP_SHALLOW_HEX = toHex(DEEP_RAMP_SHALLOW);
/** Deep endpoint as a `#rrggbb` sRGB hex string. */
export const DEEP_RAMP_DEEP_HEX = toHex(DEEP_RAMP_DEEP);

/**
 * Land tint for the above-water portion of the substrate overlay (depth_m > 0).
 * A muted, desaturated tan so the submerged ramp stays the visual subject and
 * land does not compete with the SCENIC land material. This is set dressing for
 * the optional point overlay, not a survey value.
 */
export const LAND_TINT_HEX = "#9c8c6a";

/**
 * Sample the cmocean `deep` ramp at `t` in [0,1] (clamped). Returns display-sRGB
 * [r, g, b] in [0,1]. `t=0` returns the shallow endpoint, `t=1` the deep
 * endpoint. Linear interpolation between the perceptually-spaced stops.
 */
export function sampleDeepRamp(t: number): [number, number, number] {
  const x = Number.isFinite(t) ? Math.max(0, Math.min(1, t)) : 0;
  const stops = DEEP_RAMP_STOPS;
  if (x <= stops[0].t) return [...stops[0].rgb];
  const last = stops[stops.length - 1];
  if (x >= last.t) return [...last.rgb];
  for (let i = 1; i < stops.length; i++) {
    const a = stops[i - 1];
    const b = stops[i];
    if (x <= b.t) {
      const span = b.t - a.t;
      const f = span > 0 ? (x - a.t) / span : 0;
      return [
        a.rgb[0] + (b.rgb[0] - a.rgb[0]) * f,
        a.rgb[1] + (b.rgb[1] - a.rgb[1]) * f,
        a.rgb[2] + (b.rgb[2] - a.rgb[2]) * f,
      ];
    }
  }
  return [...last.rgb];
}

/** Human-facing honesty label for any UI string built from this tint. */
export const BATHY_TINT_LABEL = "modeled, not measured";
