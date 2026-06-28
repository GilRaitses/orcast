/**
 * Typed Trip hierarchy model for orcast.
 *
 * Port of the legacy js/agentic/trip-hierarchy-model.js into idiomatic
 * TypeScript. Pure types plus minimal constructors and validators. No network,
 * no React, no backend coupling.
 *
 * Hierarchy: Trip -> Day -> DayTrip -> Stop -> Activity -> ViewingZone.
 */

// ---------------------------------------------------------------------------
// Journey branches (W3 console branches)
// ---------------------------------------------------------------------------

/**
 * Top-level console journey branch. Drives which trip-planning experience the
 * orienting answer routes a visitor into.
 *  - "visiting":  compare places / planning a trip to the Salish Sea
 *  - "here-now":  already in the area, local-area planning
 *  - "kayak":     paddle-focused, short-range, water-hugging viewing
 *  - "curious":   sidequests / exploratory, not committed to a trip
 */
export type JourneyBranch = 'visiting' | 'here-now' | 'kayak' | 'curious';

/** All journey branch members, for runtime iteration and validation. */
export const JOURNEY_BRANCHES = ['visiting', 'here-now', 'kayak', 'curious'] as const;

// ---------------------------------------------------------------------------
// Fixed enumerations (legacy `enum:...` fields)
// ---------------------------------------------------------------------------

/** Shared difficulty scale used by Trip, DayTrip and Activity. */
export type Difficulty = 'easy' | 'moderate' | 'challenging';
export const DIFFICULTIES = ['easy', 'moderate', 'challenging'] as const;

/** DayTrip transport/setting type. */
export type DayTripType = 'land_based' | 'boat_based' | 'mixed';
export const DAY_TRIP_TYPES = ['land_based', 'boat_based', 'mixed'] as const;

/** Physical kind of a Stop. */
export type StopType = 'viewing_point' | 'parking' | 'rest_area' | 'facility';
export const STOP_TYPES = ['viewing_point', 'parking', 'rest_area', 'facility'] as const;

/** Kind of Activity performed at a Stop. */
export type ActivityType = 'viewing' | 'photography' | 'education' | 'hiking' | 'boat_tour';
export const ACTIVITY_TYPES = ['viewing', 'photography', 'education', 'hiking', 'boat_tour'] as const;

/** Behavioural classification of a ViewingZone. */
export type ViewingZoneType = 'feeding_zone' | 'traveling_corridor' | 'resting_area' | 'play_zone';
export const VIEWING_ZONE_TYPES = ['feeding_zone', 'traveling_corridor', 'resting_area', 'play_zone'] as const;

// ---------------------------------------------------------------------------
// Shared primitive shapes
// ---------------------------------------------------------------------------

/** ISO date, e.g. "2026-07-01". */
export type ISODateString = string;
/** ISO datetime, e.g. "2026-07-01T09:00:00.000Z". */
export type ISODateTimeString = string;
/** Wall-clock time of day, e.g. "09:00". */
export type TimeString = string;

/** WGS84 point. */
export interface GeoCoordinates {
  lat: number;
  lng: number;
}

/** Group-size envelope for an activity. */
export interface GroupSize {
  min: number;
  max: number;
  optimal: number;
}

/**
 * Loosely-structured metadata bag. The legacy model declared many fields as a
 * bare `object` (weather, tidalConditions, constraints, environmental, etc.).
 * Those shapes are not pinned down by the source, so they are kept as opaque
 * records here rather than inventing a contract.
 */
export type Metadata = Record<string, unknown>;

// ---------------------------------------------------------------------------
// ViewingZone (leaf)
// ---------------------------------------------------------------------------

export interface ViewingZone {
  id: string;
  activityId: string;
  name: string;
  description: string;

  // Precise location
  coordinates: GeoCoordinates;
  bounds?: Metadata;
  area?: number; // square meters

  // Zone characteristics
  type: ViewingZoneType;
  waterDepth?: number; // meters
  substrate?: string;
  currentFlow?: Metadata;

  // Orca data
  probability: number; // 0-1
  confidence: number; // 0-1
  recentSightings?: Metadata[];
  historicalData?: Metadata;

  // Environmental
  environmental?: Metadata;
  prey?: Metadata;
  humanActivity?: Metadata;

  // Behavioral predictions
  expectedBehaviors?: Metadata[];
  optimalConditions?: Metadata;
  timeWindows?: Metadata[];

  // Vector space data
  vectorEmbedding?: number[];
  similarity?: Metadata;
  content?: Metadata;

  // Real-time data
  liveData?: Metadata;
  alerts?: Metadata[];
  lastUpdated?: ISODateTimeString;
}

// ---------------------------------------------------------------------------
// Activity
// ---------------------------------------------------------------------------

export interface Activity {
  id: string;
  stopId: string;
  title: string;
  description: string;

  // Activity details
  type: ActivityType;
  duration: number; // minutes
  cost: number;
  difficulty: Difficulty;

  // Requirements
  equipment?: string[];
  skills?: string[];
  groupSize?: GroupSize;

  // Orca-specific
  expectedBehaviors?: string[];
  probabilityScore: number; // 0-1

  seasonality?: Metadata;

  // Hierarchy
  viewingZones: ViewingZone[];

  // Content and guidance
  instructions?: string[];
  tips?: string[];
  safetyInfo?: string[];
  alternatives?: Metadata[];
}

// ---------------------------------------------------------------------------
// Stop
// ---------------------------------------------------------------------------

export interface Stop {
  id: string;
  dayTripId: string;
  name: string;
  description: string;

  // Location
  coordinates: GeoCoordinates;
  address?: string;
  accessInfo?: string;

  // Timing
  arrivalTime?: TimeString;
  departureTime?: TimeString;
  duration: number; // minutes at this stop

  // Stop characteristics
  type: StopType;
  facilities?: string[];
  accessibility?: Metadata;
  cost: number;

  // Viewing information
  viewingConditions?: Metadata;
  probabilityScore: number; // 0-1
  bestViewingTimes?: Metadata[];

  // Hierarchy
  activities: Activity[];

  // Content
  photos?: Metadata[];
  videos?: Metadata[];
  reviews?: Metadata[];
}

// ---------------------------------------------------------------------------
// DayTrip
// ---------------------------------------------------------------------------

export interface DayTrip {
  id: string;
  dayId: string;
  title: string;
  description: string;

  // Timing
  startTime: TimeString;
  endTime: TimeString;
  duration: number; // minutes

  // Trip characteristics
  type: DayTripType;
  transportationMethod?: string;
  difficulty: Difficulty;
  cost: number;

  // Planning metadata
  probabilityScore: number; // 0-1
  confidence: number; // 0-1
  reasoning?: string;

  // Hierarchy
  stops: Stop[];

  // Logistics
  meetingPoint?: Metadata;
  equipment?: string[];
  tips?: string[];
}

// ---------------------------------------------------------------------------
// Day
// ---------------------------------------------------------------------------

export interface Day {
  id: string;
  tripId: string;
  dayNumber: number; // 1-based
  date: ISODateString;

  // Day-level information
  theme?: string;
  weather?: Metadata;
  tidalConditions?: Metadata;

  // Day statistics
  estimatedCost: number;
  estimatedTravelTime: number; // minutes
  totalViewingTime: number; // minutes
  probabilityScore: number; // 0-1

  // Hierarchy
  dayTrips: DayTrip[];

  // Metadata
  alternatives?: Metadata[];
  contingencyPlans?: Metadata[];
}

// ---------------------------------------------------------------------------
// Trip (root)
// ---------------------------------------------------------------------------

export interface Trip {
  id: string;
  title: string;
  description: string;
  duration: number; // total days
  startDate: ISODateString;
  endDate: ISODateString;

  /**
   * Console journey branch this trip belongs to. Not present in the legacy
   * model; added for the W3 branch routing.
   */
  branch?: JourneyBranch;

  // Trip-level metadata
  constraints?: Metadata; // original user constraints
  totalCost: number;
  groupSize: number; // number of participants
  difficulty: Difficulty;

  // Analytics and confidence
  overallProbability: number; // 0-1
  confidence: number; // 0-1

  // Hierarchy
  days: Day[];

  // Metadata
  createdAt: ISODateTimeString;
  updatedAt: ISODateTimeString;
  createdBy: string; // agent or user
  version: string;
}

// ---------------------------------------------------------------------------
// Constructor input shapes (all fields optional; defaults applied)
// ---------------------------------------------------------------------------

export interface TripInput {
  title?: string;
  description?: string;
  duration?: number;
  startDate?: ISODateString;
  branch?: JourneyBranch;
  constraints?: Metadata;
  groupSize?: number;
  difficulty?: Difficulty;
  createdBy?: string;
  version?: string;
}

export interface DayInput {
  theme?: string;
  weather?: Metadata;
  tidalConditions?: Metadata;
}

export interface DayTripInput {
  title?: string;
  description?: string;
  startTime?: TimeString;
  endTime?: TimeString;
  type?: DayTripType;
  transportationMethod?: string;
  difficulty?: Difficulty;
  cost?: number;
  probabilityScore?: number;
  confidence?: number;
  reasoning?: string;
  meetingPoint?: Metadata;
  equipment?: string[];
  tips?: string[];
}

export interface StopInput {
  name?: string;
  description?: string;
  coordinates?: GeoCoordinates;
  address?: string;
  accessInfo?: string;
  arrivalTime?: TimeString;
  departureTime?: TimeString;
  duration?: number;
  type?: StopType;
  facilities?: string[];
  accessibility?: Metadata;
  cost?: number;
  viewingConditions?: Metadata;
  probabilityScore?: number;
  bestViewingTimes?: Metadata[];
  photos?: Metadata[];
  videos?: Metadata[];
  reviews?: Metadata[];
}

export interface ActivityInput {
  title?: string;
  description?: string;
  type?: ActivityType;
  duration?: number;
  cost?: number;
  difficulty?: Difficulty;
  equipment?: string[];
  skills?: string[];
  groupSize?: GroupSize;
  expectedBehaviors?: string[];
  probabilityScore?: number;
  seasonality?: Metadata;
  instructions?: string[];
  tips?: string[];
  safetyInfo?: string[];
  alternatives?: Metadata[];
}

export interface ViewingZoneInput {
  name?: string;
  description?: string;
  coordinates?: GeoCoordinates;
  bounds?: Metadata;
  area?: number;
  type?: ViewingZoneType;
  waterDepth?: number;
  substrate?: string;
  currentFlow?: Metadata;
  probability?: number;
  confidence?: number;
  recentSightings?: Metadata[];
  historicalData?: Metadata;
  environmental?: Metadata;
  prey?: Metadata;
  humanActivity?: Metadata;
  expectedBehaviors?: Metadata[];
  optimalConditions?: Metadata;
  timeWindows?: Metadata[];
  vectorEmbedding?: number[];
  similarity?: Metadata;
  content?: Metadata;
  liveData?: Metadata;
  alerts?: Metadata[];
}

// ---------------------------------------------------------------------------
// ID + date/time helpers
// ---------------------------------------------------------------------------

const ID_PREFIX = {
  trip: 'trip',
  day: 'day',
  dayTrip: 'daytrip',
  stop: 'stop',
  activity: 'activity',
  zone: 'zone',
} as const;

export type IdKind = keyof typeof ID_PREFIX;

/** Generate a reasonably-unique id, e.g. "trip_1719537600000_a1b2c3d4e". */
export function generateId(kind: IdKind): string {
  const rand = Math.random().toString(36).slice(2, 11);
  return `${ID_PREFIX[kind]}_${Date.now()}_${rand}`;
}

/** Inclusive end date: start + (duration - 1) days. */
export function calculateEndDate(startDate: ISODateString, duration: number): ISODateString {
  const d = new Date(startDate);
  d.setDate(d.getDate() + duration - 1);
  return d.toISOString().split('T')[0];
}

/** Date for the n-th day of a trip (0-based offset). */
export function calculateDayDate(tripStartDate: ISODateString, dayIndex: number): ISODateString {
  const d = new Date(tripStartDate);
  d.setDate(d.getDate() + dayIndex);
  return d.toISOString().split('T')[0];
}

/** Minutes between two "HH:MM" times. */
export function calculateDuration(startTime: TimeString, endTime: TimeString): number {
  const [sh, sm] = startTime.split(':').map(Number);
  const [eh, em] = endTime.split(':').map(Number);
  return eh * 60 + em - (sh * 60 + sm);
}

// ---------------------------------------------------------------------------
// Constructors (mirror legacy create/add* with defaults)
// ---------------------------------------------------------------------------

function today(): ISODateString {
  return new Date().toISOString().split('T')[0];
}

export function createTrip(input: TripInput = {}): Trip {
  const startDate = input.startDate ?? today();
  const duration = input.duration ?? 3;
  const now = new Date().toISOString();

  const trip: Trip = {
    id: generateId('trip'),
    title: input.title ?? 'ORCAST Orca Watching Adventure',
    description: input.description ?? '',
    duration,
    startDate,
    endDate: calculateEndDate(startDate, duration),

    branch: input.branch,

    constraints: input.constraints ?? {},
    totalCost: 0,
    groupSize: input.groupSize ?? 1,
    difficulty: input.difficulty ?? 'easy',

    overallProbability: 0,
    confidence: 0,

    days: [],

    createdAt: now,
    updatedAt: now,
    createdBy: input.createdBy ?? 'multi-agent-orchestrator',
    version: input.version ?? '1.0',
  };

  validateTrip(trip);
  return trip;
}

export function addDay(trip: Trip, input: DayInput = {}): Day {
  const dayNumber = trip.days.length + 1;
  const day: Day = {
    id: generateId('day'),
    tripId: trip.id,
    dayNumber,
    date: calculateDayDate(trip.startDate, trip.days.length),

    theme: input.theme ?? `Day ${dayNumber} Adventure`,
    weather: input.weather ?? {},
    tidalConditions: input.tidalConditions ?? {},

    estimatedCost: 0,
    estimatedTravelTime: 0,
    totalViewingTime: 0,
    probabilityScore: 0,

    dayTrips: [],

    alternatives: [],
    contingencyPlans: [],
  };

  trip.days.push(day);
  updateTripMetadata(trip);
  validateDay(day);
  return day;
}

export function addDayTrip(day: Day, input: DayTripInput = {}): DayTrip {
  const startTime = input.startTime ?? '09:00';
  const endTime = input.endTime ?? '15:00';
  const dayTrip: DayTrip = {
    id: generateId('dayTrip'),
    dayId: day.id,
    title: input.title ?? 'Orca Viewing Expedition',
    description: input.description ?? '',

    startTime,
    endTime,
    duration: calculateDuration(startTime, endTime),

    type: input.type ?? 'land_based',
    transportationMethod: input.transportationMethod ?? 'car',
    difficulty: input.difficulty ?? 'easy',
    cost: input.cost ?? 0,

    probabilityScore: input.probabilityScore ?? 0,
    confidence: input.confidence ?? 0,
    reasoning: input.reasoning ?? '',

    stops: [],

    meetingPoint: input.meetingPoint ?? {},
    equipment: input.equipment ?? [],
    tips: input.tips ?? [],
  };

  day.dayTrips.push(dayTrip);
  updateDayMetadata(day);
  validateDayTrip(dayTrip);
  return dayTrip;
}

export function addStop(dayTrip: DayTrip, input: StopInput = {}): Stop {
  const stop: Stop = {
    id: generateId('stop'),
    dayTripId: dayTrip.id,
    name: input.name ?? 'Viewing Location',
    description: input.description ?? '',

    coordinates: input.coordinates ?? { lat: 0, lng: 0 },
    address: input.address ?? '',
    accessInfo: input.accessInfo ?? '',

    arrivalTime: input.arrivalTime ?? '',
    departureTime: input.departureTime ?? '',
    duration: input.duration ?? 60,

    type: input.type ?? 'viewing_point',
    facilities: input.facilities ?? [],
    accessibility: input.accessibility ?? {},
    cost: input.cost ?? 0,

    viewingConditions: input.viewingConditions ?? {},
    probabilityScore: input.probabilityScore ?? 0,
    bestViewingTimes: input.bestViewingTimes ?? [],

    activities: [],

    photos: input.photos ?? [],
    videos: input.videos ?? [],
    reviews: input.reviews ?? [],
  };

  dayTrip.stops.push(stop);
  validateStop(stop);
  return stop;
}

export function addActivity(stop: Stop, input: ActivityInput = {}): Activity {
  const activity: Activity = {
    id: generateId('activity'),
    stopId: stop.id,
    title: input.title ?? 'Orca Watching',
    description: input.description ?? '',

    type: input.type ?? 'viewing',
    duration: input.duration ?? 30,
    cost: input.cost ?? 0,
    difficulty: input.difficulty ?? 'easy',

    equipment: input.equipment ?? [],
    skills: input.skills ?? [],
    groupSize: input.groupSize ?? { min: 1, max: 10, optimal: 4 },

    expectedBehaviors: input.expectedBehaviors ?? [],
    probabilityScore: input.probabilityScore ?? 0,
    seasonality: input.seasonality ?? {},

    viewingZones: [],

    instructions: input.instructions ?? [],
    tips: input.tips ?? [],
    safetyInfo: input.safetyInfo ?? [],
    alternatives: input.alternatives ?? [],
  };

  stop.activities.push(activity);
  validateActivity(activity);
  return activity;
}

export function addViewingZone(activity: Activity, input: ViewingZoneInput = {}): ViewingZone {
  const zone: ViewingZone = {
    id: generateId('zone'),
    activityId: activity.id,
    name: input.name ?? 'Viewing Zone',
    description: input.description ?? '',

    coordinates: input.coordinates ?? { lat: 0, lng: 0 },
    bounds: input.bounds ?? {},
    area: input.area ?? 0,

    type: input.type ?? 'feeding_zone',
    waterDepth: input.waterDepth ?? 0,
    substrate: input.substrate ?? '',
    currentFlow: input.currentFlow ?? {},

    probability: input.probability ?? 0,
    confidence: input.confidence ?? 0,
    recentSightings: input.recentSightings ?? [],
    historicalData: input.historicalData ?? {},

    environmental: input.environmental ?? {},
    prey: input.prey ?? {},
    humanActivity: input.humanActivity ?? {},

    expectedBehaviors: input.expectedBehaviors ?? [],
    optimalConditions: input.optimalConditions ?? {},
    timeWindows: input.timeWindows ?? [],

    vectorEmbedding: input.vectorEmbedding ?? new Array<number>(128).fill(0),
    similarity: input.similarity ?? {},
    content: input.content ?? {},

    liveData: input.liveData ?? {},
    alerts: input.alerts ?? [],
    lastUpdated: new Date().toISOString(),
  };

  activity.viewingZones.push(zone);
  return zone;
}

// ---------------------------------------------------------------------------
// Metadata roll-ups (cost + probability + confidence)
// ---------------------------------------------------------------------------

export function updateTripMetadata(trip: Trip): void {
  trip.totalCost = trip.days.reduce(
    (sum, day) =>
      sum +
      day.dayTrips.reduce(
        (daySum, dt) =>
          daySum +
          dt.cost +
          dt.stops.reduce(
            (stopSum, stop) =>
              stopSum + stop.cost + stop.activities.reduce((actSum, act) => actSum + act.cost, 0),
            0,
          ),
        0,
      ),
    0,
  );

  trip.overallProbability = calculateOverallProbability(trip);
  trip.confidence = calculateOverallConfidence(trip);
  trip.updatedAt = new Date().toISOString();
}

export function updateDayMetadata(day: Day): void {
  day.estimatedCost = day.dayTrips.reduce((sum, dt) => sum + dt.cost, 0);
  day.probabilityScore = calculateDayProbability(day);
}

export function calculateOverallProbability(trip: Trip): number {
  let total = 0;
  let count = 0;
  for (const day of trip.days) {
    for (const dayTrip of day.dayTrips) {
      for (const stop of dayTrip.stops) {
        for (const activity of stop.activities) {
          for (const zone of activity.viewingZones) {
            total += zone.probability * zone.confidence;
            count++;
          }
        }
      }
    }
  }
  return count > 0 ? total / count : 0;
}

export function calculateOverallConfidence(trip: Trip): number {
  let total = 0;
  let count = 0;
  for (const day of trip.days) {
    for (const dayTrip of day.dayTrips) {
      for (const stop of dayTrip.stops) {
        for (const activity of stop.activities) {
          for (const zone of activity.viewingZones) {
            total += zone.confidence;
            count++;
          }
        }
      }
    }
  }
  return count > 0 ? total / count : 0;
}

/** Legacy used a fixed placeholder of 0.75; preserved for parity. */
export function calculateDayProbability(_day: Day): number {
  return 0.75;
}

// ---------------------------------------------------------------------------
// Validators (mirror legacy required-field checks)
// ---------------------------------------------------------------------------

export function validateTrip(trip: Trip): true {
  if (!trip.id || !trip.title || !trip.duration) {
    throw new Error('Trip validation failed: missing required fields (id, title, duration)');
  }
  if (trip.branch !== undefined && !JOURNEY_BRANCHES.includes(trip.branch)) {
    throw new Error(`Trip validation failed: invalid branch "${trip.branch}"`);
  }
  return true;
}

export function validateDay(day: Day): true {
  if (!day.id || !day.tripId || !day.dayNumber) {
    throw new Error('Day validation failed: missing required fields (id, tripId, dayNumber)');
  }
  return true;
}

export function validateDayTrip(dayTrip: DayTrip): true {
  if (!dayTrip.id || !dayTrip.dayId || !dayTrip.title) {
    throw new Error('DayTrip validation failed: missing required fields (id, dayId, title)');
  }
  return true;
}

export function validateStop(stop: Stop): true {
  if (!stop.id || !stop.dayTripId || !stop.name) {
    throw new Error('Stop validation failed: missing required fields (id, dayTripId, name)');
  }
  return true;
}

export function validateActivity(activity: Activity): true {
  if (!activity.id || !activity.stopId || !activity.title) {
    throw new Error('Activity validation failed: missing required fields (id, stopId, title)');
  }
  return true;
}

export function validateViewingZone(zone: ViewingZone): true {
  if (!zone.id || !zone.activityId || !zone.name) {
    throw new Error('ViewingZone validation failed: missing required fields (id, activityId, name)');
  }
  return true;
}

// ---------------------------------------------------------------------------
// Serialization helpers
// ---------------------------------------------------------------------------

export function exportTrip(trip: Trip): string {
  return JSON.stringify(trip, null, 2);
}

export function importTrip(tripJson: string): Trip {
  const trip = JSON.parse(tripJson) as Trip;
  validateTrip(trip);
  return trip;
}

// ---------------------------------------------------------------------------
// Query helpers (typed ports of legacy search methods)
// ---------------------------------------------------------------------------

export interface ZonePath {
  day: number;
  dayTrip: string;
  stop: string;
  activity: string;
}

export type ViewingZoneWithPath = ViewingZone & { path: ZonePath };

export function findViewingZonesByProbability(trip: Trip, minProbability = 0.5): ViewingZoneWithPath[] {
  const zones: ViewingZoneWithPath[] = [];
  for (const day of trip.days) {
    for (const dayTrip of day.dayTrips) {
      for (const stop of dayTrip.stops) {
        for (const activity of stop.activities) {
          for (const zone of activity.viewingZones) {
            if (zone.probability >= minProbability) {
              zones.push({
                ...zone,
                path: { day: day.dayNumber, dayTrip: dayTrip.title, stop: stop.name, activity: activity.title },
              });
            }
          }
        }
      }
    }
  }
  return zones.sort((a, b) => b.probability - a.probability);
}

export interface ActivityPath {
  day: number;
  dayTrip: string;
  stop: string;
}

export type ActivityWithPath = Activity & { path: ActivityPath };

export function findActivitiesByType(trip: Trip, activityType: ActivityType): ActivityWithPath[] {
  const activities: ActivityWithPath[] = [];
  for (const day of trip.days) {
    for (const dayTrip of day.dayTrips) {
      for (const stop of dayTrip.stops) {
        for (const activity of stop.activities) {
          if (activity.type === activityType) {
            activities.push({
              ...activity,
              path: { day: day.dayNumber, dayTrip: dayTrip.title, stop: stop.name },
            });
          }
        }
      }
    }
  }
  return activities;
}
