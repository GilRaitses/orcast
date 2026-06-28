// Unit assertions for the Fly-through Controller (WS-INTENT, Producer B).
//
// No vitest/jest runner is configured in web/ (only Playwright e2e), so this
// file is a self-contained assertion script in the same style as
// lib/geo/gazetteer.test.ts. Run it offline with:
//
//   cd web && npx tsx lib/journey/controller.test.ts
//
// It exits non-zero on the first failed assertion. It composes the controller
// against a recording mock director and (for the fog beats) a real THREE.Fog, so
// no scene, no React, and no dev server are involved.

import assert from "node:assert/strict";
import * as THREE from "three";
import {
  approachPath,
  establishAltitudeMeters,
  runPlaceJourney,
  type JourneyAtmosphere,
} from "./controller";
import type {
  CameraDirector,
  CameraState,
  FollowPathOptions,
  LatLng,
  LatLngAlt,
  MoveOptions,
  OrbitHandle,
  OrbitOptions,
} from "@/lib/scene/camera";
import type { Place } from "@/lib/geo/gazetteer";
import type { TweenHandle } from "@/lib/scene/atmosphere/transition";

let passed = 0;
async function check(name: string, fn: () => void | Promise<void>): Promise<void> {
  await fn();
  passed += 1;
  console.log(`ok - ${name}`);
}

// A deferred promise so a mock move can be resolved on demand.
function deferred(): { promise: Promise<void>; resolve: () => void } {
  let resolve!: () => void;
  const promise = new Promise<void>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}

interface DirectorCall {
  method: "flyTo" | "descendTo" | "followPath" | "orbit" | "stop";
  args: unknown[];
}

interface MockDirector {
  director: CameraDirector;
  calls: DirectorCall[];
  orbitHandle: { stopped: boolean; handle: OrbitHandle };
  // When set, flyTo returns this deferred's promise instead of resolving at once.
  flyToGate?: ReturnType<typeof deferred>;
}

// Build a CameraDirector mock that records the order and arguments of every
// move. Moves resolve immediately unless a gate is supplied (used to test that
// cancel supersedes a parked beat).
function makeMockDirector(flyToGate?: ReturnType<typeof deferred>): MockDirector {
  const calls: DirectorCall[] = [];
  const orbitState = { stopped: false } as { stopped: boolean; handle: OrbitHandle };

  const director: CameraDirector = {
    flyTo(target: LatLngAlt, opts?: MoveOptions): Promise<void> {
      calls.push({ method: "flyTo", args: [target, opts] });
      return flyToGate ? flyToGate.promise : Promise.resolve();
    },
    descendTo(altitudeMeters: number, opts?: MoveOptions): Promise<void> {
      calls.push({ method: "descendTo", args: [altitudeMeters, opts] });
      return Promise.resolve();
    },
    followPath(points: LatLngAlt[], opts?: FollowPathOptions): Promise<void> {
      calls.push({ method: "followPath", args: [points, opts] });
      return Promise.resolve();
    },
    orbit(center: LatLng, radius: number, speed: number, opts?: OrbitOptions): OrbitHandle {
      calls.push({ method: "orbit", args: [center, radius, speed, opts] });
      const handle: OrbitHandle = {
        stop: () => {
          orbitState.stopped = true;
        },
        isActive: () => !orbitState.stopped,
      };
      orbitState.handle = handle;
      return handle;
    },
    stop(): void {
      calls.push({ method: "stop", args: [] });
    },
    getState(): CameraState {
      return { target: null, altitude: 0, subject: null, isOrbiting: false };
    },
    update(): void {},
    isAnimating(): boolean {
      return false;
    },
  };

  return { director, calls, orbitHandle: orbitState, flyToGate };
}

// A push sink that records every tween handed to it.
function makeAtmosphere(fog: THREE.Fog | null): {
  atmosphere: JourneyAtmosphere;
  pushed: TweenHandle[];
} {
  const pushed: TweenHandle[] = [];
  return {
    atmosphere: { fog, push: (t) => pushed.push(t) },
    pushed,
  };
}

const EAST_SOUND: Place = {
  id: "east-sound",
  name: "East Sound",
  lat: 48.6935,
  lng: -122.9043,
  bounds: { min_lat: 48.6735, max_lat: 48.7135, min_lng: -122.9293, max_lng: -122.8793 },
  kind: "village",
  region: "san-juans",
};

// A place with no curated corridor, to exercise the derived approach lead-in.
const GENERIC: Place = {
  id: "made-up-cove",
  name: "Made Up Cove",
  lat: 48.5,
  lng: -123.0,
  bounds: { min_lat: 48.49, max_lat: 48.51, min_lng: -123.012, max_lng: -122.988 },
  kind: "harbor",
};

async function main(): Promise<void> {
  await check("drives the director through flyTo -> descendTo -> followPath -> orbit", async () => {
    const mock = makeMockDirector();
    const { atmosphere } = makeAtmosphere(null);
    const handle = runPlaceJourney(EAST_SOUND, mock.director, atmosphere);
    await handle.done;
    const order = mock.calls.map((c) => c.method);
    assert.deepEqual(order, ["flyTo", "descendTo", "followPath", "orbit"], "beat order");
  });

  await check("flyTo establishes at the bounds-derived altitude framing the center", async () => {
    const mock = makeMockDirector();
    const { atmosphere } = makeAtmosphere(null);
    await runPlaceJourney(EAST_SOUND, mock.director, atmosphere).done;
    const fly = mock.calls.find((c) => c.method === "flyTo");
    assert.ok(fly, "flyTo was called");
    const target = fly!.args[0] as LatLngAlt;
    assert.equal(target.lat, EAST_SOUND.lat, "establish frames the center lat");
    assert.equal(target.lng, EAST_SOUND.lng, "establish frames the center lng");
    assert.equal(
      target.altitudeMeters,
      establishAltitudeMeters(EAST_SOUND.bounds),
      "establish altitude is bounds-derived",
    );
  });

  await check("descendTo cruises below the establishing altitude", async () => {
    const mock = makeMockDirector();
    const { atmosphere } = makeAtmosphere(null);
    await runPlaceJourney(EAST_SOUND, mock.director, atmosphere).done;
    const descend = mock.calls.find((c) => c.method === "descendTo");
    const cruise = descend!.args[0] as number;
    assert.ok(cruise < establishAltitudeMeters(EAST_SOUND.bounds), "cruise below establish");
    assert.ok(cruise > 0, "cruise altitude is positive");
  });

  await check("derived approach path ends exactly at the place center", async () => {
    const mock = makeMockDirector();
    const { atmosphere } = makeAtmosphere(null);
    await runPlaceJourney(GENERIC, mock.director, atmosphere).done;
    const follow = mock.calls.find((c) => c.method === "followPath");
    const points = follow!.args[0] as LatLngAlt[];
    assert.ok(points.length >= 2, "approach has at least two points");
    const last = points[points.length - 1];
    assert.equal(last.lat, GENERIC.lat, "ends at center lat");
    assert.equal(last.lng, GENERIC.lng, "ends at center lng");
    // approachPath returns the same geometry the controller fed the director.
    const direct = approachPath(GENERIC);
    assert.deepEqual(points, direct, "controller used approachPath geometry");
  });

  await check("curated corridor approach also ends at the resolved center", () => {
    const path = approachPath(EAST_SOUND);
    const last = path[path.length - 1];
    assert.equal(last.lat, EAST_SOUND.lat, "curated path ends at center lat");
    assert.equal(last.lng, EAST_SOUND.lng, "curated path ends at center lng");
    assert.ok(path.length > 2, "curated corridor has lead-in waypoints");
    // Altitudes ease down from the start band to the end band.
    assert.ok(
      path[0].altitudeMeters! > path[path.length - 1].altitudeMeters!,
      "approach altitudes descend",
    );
  });

  await check("orbit rests on the place center", async () => {
    const mock = makeMockDirector();
    const { atmosphere } = makeAtmosphere(null);
    await runPlaceJourney(EAST_SOUND, mock.director, atmosphere).done;
    const orbit = mock.calls.find((c) => c.method === "orbit");
    const center = orbit!.args[0] as LatLng;
    assert.equal(center.lat, EAST_SOUND.lat, "orbit center lat");
    assert.equal(center.lng, EAST_SOUND.lng, "orbit center lng");
  });

  await check("with fog, pushes a mask-in then a clear-out tween", async () => {
    const mock = makeMockDirector();
    const fog = new THREE.Fog("#9fb8cc", 120, 520);
    const { atmosphere, pushed } = makeAtmosphere(fog);
    await runPlaceJourney(EAST_SOUND, mock.director, atmosphere).done;
    assert.equal(pushed.length, 2, "two fog tweens pushed (mask in, clear out)");
  });

  await check("missing fog: the journey still runs the full beat", async () => {
    const mock = makeMockDirector();
    const { atmosphere, pushed } = makeAtmosphere(null);
    await runPlaceJourney(EAST_SOUND, mock.director, atmosphere).done;
    assert.equal(pushed.length, 0, "no tweens pushed without fog");
    assert.deepEqual(
      mock.calls.map((c) => c.method),
      ["flyTo", "descendTo", "followPath", "orbit"],
      "full beat ran without fog",
    );
  });

  await check("cancel supersedes: stops the director and cancels pushed tweens", async () => {
    const gate = deferred();
    const mock = makeMockDirector(gate);
    const fog = new THREE.Fog("#9fb8cc", 120, 520);
    const { atmosphere, pushed } = makeAtmosphere(fog);
    const handle = runPlaceJourney(EAST_SOUND, mock.director, atmosphere);

    // The beat is parked awaiting the gated flyTo. One fog mask-in was pushed.
    await Promise.resolve();
    assert.equal(pushed.length, 1, "mask-in pushed before parking on flyTo");
    assert.deepEqual(mock.calls.map((c) => c.method), ["flyTo"], "parked at flyTo");

    handle.cancel();
    assert.ok(pushed.every((t) => t.settled), "pushed tweens were cancelled");
    assert.ok(
      mock.calls.some((c) => c.method === "stop"),
      "director.stop() called on cancel",
    );

    // Even if the gated move now resolves, the cancelled guard stops the beat:
    // no descendTo / followPath / orbit follow.
    gate.resolve();
    await handle.done;
    assert.deepEqual(
      mock.calls.filter((c) => c.method !== "stop").map((c) => c.method),
      ["flyTo"],
      "no further beats ran after cancel",
    );
  });

  console.log(`\n${passed} checks passed`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
