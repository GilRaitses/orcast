// CI guard for the measured CTD stratification profile (OCN lane).
//
// O0 gate: catch a forbidden-claim provenance BEFORE scene mount. At mount,
// createDoubleDiffusionLayer runs
//   assertNoForbiddenClaim(INTERPRETIVE_OCEAN_LABEL, INTERPRETIVE_OCEAN_DETAIL, profile.provenance)
// and a bad provenance throws, which takes down the whole scene. This test makes
// that exact guard call against the SHIPPED baked profile, so a bad string fails
// CI instead of the scene at runtime.
//
// The test reads the baked JSON from disk rather than importing measuredProfile.ts,
// because the loader uses an extensionless ESM JSON import that the web bundler
// resolves but the node test runner does not. Reading the shipped artifact and
// running the real guard is the faithful, runner-safe gate. interpretiveOceanLayer.ts
// imports only three, so it loads cleanly under `node --test`.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import {
  assertNoForbiddenClaim,
  INTERPRETIVE_OCEAN_LABEL,
  INTERPRETIVE_OCEAN_DETAIL,
} from "./interpretiveOceanLayer.ts";

function loadBaked(): {
  origin: string;
  provenance: string;
  maxDepthM: number;
  samples: { depthM: number; temperatureC: number; salinityPsu: number }[];
} {
  const here = dirname(fileURLToPath(import.meta.url));
  const path = resolve(here, "measured_cruisesalish_profile.json");
  return JSON.parse(readFileSync(path, "utf-8"));
}

test("measured profile provenance passes the mount-time forbidden-claim guard", () => {
  const profile = loadBaked();
  // Identical to the call inside createDoubleDiffusionLayer at scene mount.
  assert.doesNotThrow(() =>
    assertNoForbiddenClaim(INTERPRETIVE_OCEAN_LABEL, INTERPRETIVE_OCEAN_DETAIL, profile.provenance),
  );
});

test("the forbidden-claim guard is live (a known-bad string still throws)", () => {
  // Proves the guard catches a negated forbidden phrase too (plain includes()).
  assert.throws(() => assertNoForbiddenClaim("this is not measured thermohaline structure"));
});

test("measured profile has the measured-ctd origin and honest CC0 provenance", () => {
  const profile = loadBaked();
  assert.equal(profile.origin, "measured-ctd");
  const p = profile.provenance.toLowerCase();
  assert.ok(p.includes("cc0"), "provenance carries the CC0 attribution");
  assert.ok(p.includes("0307188"), "provenance carries the NCEI accession");
  assert.ok(p.includes("analog"), "provenance labels the cast a nearby analog, not on-site");
  assert.ok(p.includes("interpret"), "provenance keeps the visualization interpretive");
});

test("measured profile samples are well-formed surface to deep", () => {
  const profile = loadBaked();
  assert.equal(profile.samples.length, 64, "64 samples, matching the analytic texture width");
  for (const s of profile.samples) {
    assert.ok(Number.isFinite(s.depthM) && Number.isFinite(s.temperatureC) && Number.isFinite(s.salinityPsu));
  }
  for (let i = 1; i < profile.samples.length; i++) {
    assert.ok(profile.samples[i].depthM >= profile.samples[i - 1].depthM, "depth is non-decreasing");
  }
  assert.ok(profile.maxDepthM > 0 && Number.isFinite(profile.maxDepthM));
});
