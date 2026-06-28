// Unit assertions for the WS-BATHY honesty label model.
//
// No vitest/jest runner is configured in web/ (only Playwright e2e), so this is
// a self-contained assertion script, matching lib/geo/gazetteer.test.ts. Run it
// offline with:
//
//   cd web && npx tsx lib/scene/bathy/honesty/honesty.test.ts
//
// It exits non-zero on the first failed assertion and also type-checks under
// `npx tsc --noEmit`.

import assert from "node:assert/strict";

import { SUBSTRATE_LABEL } from "../../substrate";
import {
  attachBathyLabel,
  attachModeledLabel,
  BATHY_LABEL_KEY,
  BATHY_MEASURED_COVERAGE_LABEL,
  BATHY_MODELED,
  BATHY_MODELED_LABEL,
  BATHY_MODELED_PROVENANCE,
  BATHY_SCENE_HONESTY_NOTE,
  DEFERRED_MEASURED_OVERLAY,
  measuredCoverageLabel,
  type BathyLabelTarget,
  type MeasuredCoverageProvider,
} from "./index";

let passed = 0;
function check(name: string, fn: () => void): void {
  fn();
  passed += 1;
  console.log(`ok - ${name}`);
}

check("modeled provenance label reads modeled and mirrors SUBSTRATE_LABEL", () => {
  assert.equal(BATHY_MODELED_LABEL, SUBSTRATE_LABEL);
  assert.equal(BATHY_MODELED_LABEL, "modeled, not measured");
  assert.ok(/modeled/i.test(BATHY_MODELED_LABEL));
  assert.equal(BATHY_MODELED_PROVENANCE.modeledNotMeasured, true);
  assert.match(BATHY_MODELED_PROVENANCE.dataset, /CUDEM 1\/9 arc-second/);
  assert.equal(BATHY_MODELED_PROVENANCE.datum, "NAVD88");
  assert.match(BATHY_MODELED_PROVENANCE.method, /interpolated/);
});

check("the modeled label is structurally not measured", () => {
  assert.equal(BATHY_MODELED.kind, "modeled");
  assert.equal(BATHY_MODELED.measured, false);
  assert.equal(BATHY_MODELED.label, BATHY_MODELED_LABEL);
});

check("attachModeledLabel stamps a depth surface as modeled, never measured", () => {
  const surface: BathyLabelTarget = { name: "bathy-seabed-tint" };
  attachModeledLabel(surface);
  const ud = surface.userData ?? {};
  assert.equal(ud.modeledNotMeasured, true);
  assert.equal(ud.measured, false);
  assert.equal(ud.label, BATHY_MODELED_LABEL);
  assert.equal(ud[BATHY_LABEL_KEY], BATHY_MODELED);
  assert.match(String(surface.name), /modeled, not measured/);
  // A modeled surface must never carry a measured-source attribution.
  assert.equal(ud.measuredSource, undefined);
  assert.equal(ud.attribution, undefined);
});

check("a measured-coverage surface carries both the coverage label and its source attribution", () => {
  const label = measuredCoverageLabel("BlueTopo", "MLLW");
  assert.equal(label.kind, "measured-coverage");
  assert.equal(label.measured, true);
  assert.equal(label.label, BATHY_MEASURED_COVERAGE_LABEL);
  assert.equal(label.source, "BlueTopo");
  assert.match(label.attribution, /BlueTopo/);

  const surface: BathyLabelTarget = { name: "bathy-measured-coverage" };
  attachBathyLabel(surface, label);
  const ud = surface.userData ?? {};
  assert.equal(ud.measured, true);
  assert.equal(ud.label, BATHY_MEASURED_COVERAGE_LABEL);
  assert.equal(ud.measuredSource, "BlueTopo");
  assert.match(String(ud.attribution), /BlueTopo/);
});

check("NONNA measured label notes its non-NAVD88 chart datum", () => {
  const label = measuredCoverageLabel("NONNA", "chart datum (CD)");
  assert.equal(label.source, "NONNA");
  assert.match(label.attribution, /NONNA/);
  assert.match(label.attribution, /chart datum/i);
  assert.notEqual(label.datum, "NAVD88");
});

check("the deferred measured overlay is typed and answers modeled everywhere", () => {
  const provider: MeasuredCoverageProvider = DEFERRED_MEASURED_OVERLAY;
  assert.equal(provider.loaded, false);
  assert.equal(provider.sources.length, 0);
  // Haro Strait sample: no measured asset loaded, so it must fall back to modeled.
  assert.equal(provider.coverageAt(48.5583, -123.1735), null);
});

check("the scene honesty note declares modeled and a deferred overlay", () => {
  assert.match(BATHY_SCENE_HONESTY_NOTE, /modeled, not measured/);
  assert.match(BATHY_SCENE_HONESTY_NOTE, /CUDEM/);
  assert.match(BATHY_SCENE_HONESTY_NOTE, /NAVD88/);
  assert.match(BATHY_SCENE_HONESTY_NOTE, /No measured-coverage overlay is loaded/);
});

console.log(`\nOK: ${passed} bathy honesty assertions passed.`);
