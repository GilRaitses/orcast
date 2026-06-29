#!/usr/bin/env node
// Bake the San Juan bathymetry point cloud into a regular grid heightmap the
// r3f terrain mesh consumes at runtime. Source is the existing ETOPO-derived
// grid (data/geo/san_juan_bathymetry.json); no network or account required.
//
// Output: web/public/geo/salish_heightmap.json
//   { bounds, cols, rows, step_deg, depths[row][col], min_depth, max_depth }
// depth_m sign convention follows the source: negative = below sea level
// (water), positive = land elevation.

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "..", "..");
const SRC = resolve(repoRoot, "data/geo/san_juan_bathymetry.json");
const OUT = resolve(repoRoot, "web/public/geo/salish_heightmap.json");

function nearestIndex(value, min, step) {
  return Math.round((value - min) / step);
}

function main() {
  const raw = JSON.parse(readFileSync(SRC, "utf8"));
  const { bounds, resolution_deg: step, points } = raw;
  if (!Array.isArray(points) || points.length === 0) {
    throw new Error("bathymetry source has no points");
  }

  const cols = Math.round((bounds.max_lng - bounds.min_lng) / step) + 1;
  const rows = Math.round((bounds.max_lat - bounds.min_lat) / step) + 1;

  // Initialise grid with null so we can detect gaps, then fill.
  const depths = Array.from({ length: rows }, () => new Array(cols).fill(null));
  let minDepth = Infinity;
  let maxDepth = -Infinity;

  for (const p of points) {
    const c = nearestIndex(p.lng, bounds.min_lng, step);
    const r = nearestIndex(p.lat, bounds.min_lat, step);
    if (r < 0 || r >= rows || c < 0 || c >= cols) continue;
    depths[r][c] = p.depth_m;
    if (p.depth_m < minDepth) minDepth = p.depth_m;
    if (p.depth_m > maxDepth) maxDepth = p.depth_m;
  }

  // Fill any gaps by nearest-neighbour row average so the mesh has no holes.
  let filled = 0;
  for (let r = 0; r < rows; r += 1) {
    for (let c = 0; c < cols; c += 1) {
      if (depths[r][c] === null) {
        const neighbours = [
          depths[r][c - 1],
          depths[r][c + 1],
          r > 0 ? depths[r - 1][c] : null,
          r < rows - 1 ? depths[r + 1][c] : null,
        ].filter((v) => typeof v === "number");
        depths[r][c] = neighbours.length
          ? neighbours.reduce((a, b) => a + b, 0) / neighbours.length
          : 0;
        filled += 1;
      }
    }
  }

  const out = {
    source: raw.source,
    dataset: raw.dataset,
    bounds,
    step_deg: step,
    cols,
    rows,
    min_depth: minDepth,
    max_depth: maxDepth,
    depths,
  };

  mkdirSync(dirname(OUT), { recursive: true });
  writeFileSync(OUT, JSON.stringify(out));
  console.log(
    `baked ${rows}x${cols} grid (${points.length} src points, ${filled} gaps filled) -> ${OUT}`
  );
  console.log(`depth range: ${minDepth}m .. ${maxDepth}m`);
}

main();
