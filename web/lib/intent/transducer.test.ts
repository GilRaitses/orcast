// Unit assertions for the intent transducer (WS-INTENT Producer A).
//
// No vitest/jest runner is configured in web/ (only Playwright e2e), so this is
// a self-contained assertion script following the repo pattern. Run it with:
//
//   cd web && npx tsx lib/intent/transducer.test.ts
//
// It also type-checks under `npx tsc --noEmit`. It exits non-zero on the first
// failed assertion. The transducer's only runtime state is module-level, so each
// check resets it via setActiveDirector / clearActiveDirector.

import assert from "node:assert/strict";
import type { CameraDirector, CameraState, OrbitHandle } from "../scene/camera/types";
import type { TurnContext } from "../adaptiveConsole";
import {
  SAMPLE_THROTTLE_MS,
  clearActiveDirector,
  enrichTurnContext,
  hasActiveDirector,
  setActiveDirector,
  __setClockForTest,
} from "./transducer";

// A fake director that returns a fixed state and counts getState() reads.
function makeFakeDirector(state: CameraState): {
  director: CameraDirector;
  getCalls: () => number;
} {
  let getStateCalls = 0;
  const orbitHandle: OrbitHandle = { stop: () => {}, isActive: () => false };
  const director: CameraDirector = {
    flyTo: async () => {},
    descendTo: async () => {},
    followPath: async () => {},
    orbit: () => orbitHandle,
    stop: () => {},
    getState: () => {
      getStateCalls += 1;
      return state;
    },
    update: () => {},
    isAnimating: () => false,
  };
  return { director, getCalls: () => getStateCalls };
}

const focusedState: CameraState = {
  target: { lat: 48.69, lng: -122.9 },
  altitude: 4200,
  subject: "East Sound",
  isOrbiting: false,
};

const orbitingState: CameraState = {
  target: { lat: 48.53, lng: -123.02 },
  altitude: 1800,
  subject: "Friday Harbor",
  isOrbiting: true,
};

let passed = 0;
function check(name: string, fn: () => void): void {
  fn();
  passed += 1;
  console.log(`ok - ${name}`);
}

check("unattached transducer returns the base unchanged", () => {
  clearActiveDirector();
  assert.equal(hasActiveDirector(), false);
  const base: TurnContext = { message: "where are the orcas?" };
  const out = enrichTurnContext(base);
  // Same reference back, untouched, when no director is registered.
  assert.equal(out, base);
  assert.equal(out.viewport ?? null, null);
  assert.equal(out.focus ?? null, null);
});

check("a focused state produces enriched focus and viewport", () => {
  const { director } = makeFakeDirector(focusedState);
  setActiveDirector(director);
  const out = enrichTurnContext({ message: "tell me about this place" });
  assert.deepEqual(out.viewport, { lat: 48.69, lng: -122.9 });
  assert.equal(out.focus?.cell, "48.69,-122.9");
  assert.equal(out.cameraSubject, "East Sound");
  assert.equal(out.cameraAltitudeMeters, 4200);
  assert.equal(out.cameraOrbiting, false);
  clearActiveDirector();
});

check("an orbiting state produces enriched focus and viewport", () => {
  const { director } = makeFakeDirector(orbitingState);
  setActiveDirector(director);
  const out = enrichTurnContext({ message: "what is the camera circling?" });
  assert.deepEqual(out.viewport, { lat: 48.53, lng: -123.02 });
  assert.equal(out.focus?.cell, "48.53,-123.02");
  assert.equal(out.cameraSubject, "Friday Harbor");
  assert.equal(out.cameraOrbiting, true);
  clearActiveDirector();
});

check("explicit base viewport/focus are preserved (additive, not overridden)", () => {
  const { director } = makeFakeDirector(focusedState);
  setActiveDirector(director);
  const base: TurnContext = {
    message: "from a scene click",
    viewport: { lat: 47.0, lng: -122.0, zoom: 11 },
    focus: { cell: "47,-122" },
  };
  const out = enrichTurnContext(base);
  // Explicit click intent wins; only metadata is added.
  assert.deepEqual(out.viewport, { lat: 47.0, lng: -122.0, zoom: 11 });
  assert.equal(out.focus?.cell, "47,-122");
  assert.equal(out.cameraSubject, "East Sound");
  clearActiveDirector();
});

check("the sampler throttles: a burst of reads collapses to a few snapshots", () => {
  let t = 1000;
  __setClockForTest(() => t);
  const { director, getCalls } = makeFakeDirector(focusedState);
  setActiveDirector(director); // resets lastSampleAt to 0

  // A tight burst at the same instant: first call samples (leading edge), the
  // rest coalesce into a single pending trailing sample.
  for (let i = 0; i < 500; i += 1) {
    enrichTurnContext({ message: `burst ${i}` });
  }
  assert.equal(getCalls(), 1, "500 reads in one instant collapse to one snapshot");

  // After the throttle window elapses, the next read samples again.
  t = 1000 + SAMPLE_THROTTLE_MS;
  enrichTurnContext({ message: "after the window" });
  assert.equal(getCalls(), 2, "a read past the window takes a fresh snapshot");

  clearActiveDirector(); // cancels any pending trailing timer
  __setClockForTest(null);
});

console.log(`\n${passed} checks passed`);
