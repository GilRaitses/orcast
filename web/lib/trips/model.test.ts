/**
 * Sample-trip validation for the typed trip hierarchy.
 *
 * No test runner is installed in web/, so this is a self-contained assertion
 * script. Run it with: `cd web && npx tsx lib/trips/model.test.ts`.
 * It also type-checks under `npx tsc --noEmit`.
 */

import {
  addActivity,
  addDay,
  addDayTrip,
  addStop,
  addViewingZone,
  createTrip,
  exportTrip,
  findViewingZonesByProbability,
  updateTripMetadata,
  validateTrip,
  type JourneyBranch,
  type Trip,
} from './model';

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) {
    throw new Error(`ASSERT FAILED: ${message}`);
  }
}

// Build a 2-day San Juan Islands trip on the "visiting" branch.
const branch: JourneyBranch = 'visiting';
const trip: Trip = createTrip({
  title: 'San Juan Islands Orca Weekend',
  description: 'Two-day Southern Resident watching trip out of Friday Harbor.',
  duration: 2,
  startDate: '2026-07-10',
  branch,
  groupSize: 4,
  difficulty: 'moderate',
});

// Day 1 -> DayTrip -> Stop -> Activity -> ViewingZone
const day1 = addDay(trip, { theme: 'West-side foraging zones' });
const expedition = addDayTrip(day1, {
  title: "Lime Kiln 'Whale Watch Park' land watch",
  startTime: '09:00',
  endTime: '13:00',
  type: 'land_based',
  cost: 0,
  probabilityScore: 0.62,
  confidence: 0.55,
});
const limeKiln = addStop(expedition, {
  name: 'Lime Kiln Point State Park',
  coordinates: { lat: 48.5160, lng: -123.1520 },
  type: 'viewing_point',
  cost: 10,
  probabilityScore: 0.62,
});
const shoreWatch = addActivity(limeKiln, {
  title: 'Shoreline scanning',
  type: 'viewing',
  duration: 120,
  probabilityScore: 0.6,
});
const haroStrait = addViewingZone(shoreWatch, {
  name: 'Haro Strait foraging line',
  coordinates: { lat: 48.5155, lng: -123.1700 },
  type: 'feeding_zone',
  waterDepth: 180,
  probability: 0.7,
  confidence: 0.6,
});

// Day 2 -> a boat-based day trip with its own stop/activity/zone.
const day2 = addDay(trip, { theme: 'Boundary Pass crossing' });
const boatDay = addDayTrip(day2, {
  title: 'Spieden Channel boat tour',
  startTime: '10:00',
  endTime: '14:30',
  type: 'boat_based',
  cost: 145,
  probabilityScore: 0.5,
  confidence: 0.5,
});
const dockStop = addStop(boatDay, {
  name: 'Friday Harbor dock',
  coordinates: { lat: 48.5350, lng: -123.0140 },
  type: 'facility',
  cost: 0,
});
const boatViewing = addActivity(dockStop, { title: 'On-water viewing', type: 'boat_tour', duration: 240 });
addViewingZone(boatViewing, {
  name: 'Boundary Pass corridor',
  coordinates: { lat: 48.7200, lng: -123.0500 },
  type: 'traveling_corridor',
  probability: 0.45,
  confidence: 0.4,
});

// Rollups are lazy (legacy recomputes on addDay/addDayTrip), so finalize once
// the full tree is built.
updateTripMetadata(trip);

// Assertions.
validateTrip(trip);
assert(trip.id.startsWith('trip_'), 'trip id has trip_ prefix');
assert(trip.branch === 'visiting', 'branch is visiting');
assert(trip.endDate === '2026-07-11', `endDate is inclusive (got ${trip.endDate})`);
assert(trip.days.length === 2, 'trip has 2 days');
assert(day1.dayNumber === 1 && day2.dayNumber === 2, 'day numbers are 1 and 2');
assert(day1.date === '2026-07-10' && day2.date === '2026-07-11', 'day dates increment');
assert(expedition.duration === 240, `lime kiln daytrip duration is 240 min (got ${expedition.duration})`);
assert(haroStrait.activityId === shoreWatch.id, 'zone references its activity');
assert(limeKiln.dayTripId === expedition.id, 'stop references its day trip');
assert(trip.totalCost === 155, `rollup totalCost is 155 (got ${trip.totalCost})`);

const hot = findViewingZonesByProbability(trip, 0.5);
assert(hot.length === 1, `one zone >= 0.5 probability (got ${hot.length})`);
assert(hot[0].name === 'Haro Strait foraging line', 'highest-probability zone is Haro Strait');

// Round-trip serialization.
const reimported = JSON.parse(exportTrip(trip)) as Trip;
assert(reimported.days[0].dayTrips[0].stops[0].activities[0].viewingZones[0].name === 'Haro Strait foraging line', 'serialization preserves the leaf zone');

console.log('OK: sample San Juan Islands trip validates.');
console.log(`  branch=${trip.branch} days=${trip.days.length} totalCost=${trip.totalCost} overallProbability=${trip.overallProbability.toFixed(3)}`);
console.log(`  zones>=0.5: ${hot.map((z) => z.name).join(', ')}`);
