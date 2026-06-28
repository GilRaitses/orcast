# Connections research: open transit data for the Trips planner

Source screen for the logistics layer (ferries, road traffic, flights, geocoding). Every source is
labeled measured / modeled / published / heuristic so the planner never overstates a connection.
Verified field-by-field against provider docs (WSF/WSDOT REST help pages, WSDOT Traveler API doxygen,
OpenSky REST 1.4.0, SkyLink v3, AviationStack v1) on 2026-06-27. Recon only — no network/client code
was written here; the W2 clients consume the field lists and adapter signatures below.

## 0. Shared access code (one free WSDOT Traveler API key) — confirmed

WSF and WSDOT Traffic share ONE free access code (register an email at the WSDOT Traveler API). The
casing of the query parameter DIFFERS between the two endpoint families — this is the single most
common integration bug, so it is pinned here:

| Endpoint family | Param name (exact casing) | Placement | Label |
|-----------------|---------------------------|-----------|-------|
| WSF (ferries: vessels / schedule / terminals / fares) | `apiaccesscode` (all lowercase) | URL query string | measured |
| WSDOT Traffic (TravelTimes / TrafficFlow REST .svc) | `AccessCode` (PascalCase) | URL query string | measured |

Both read the same secret from env `WSDOT_ACCESS_CODE`. WSF date fields are WCF/ASP.NET JSON
(`"\/Date(1719500000000-0700)\/"`) — the adapter must parse the epoch-millis + offset, not ISO-8601
(measured; parsing note).

## 1. Ferries (Anacortes <-> San Juan Islands) — WSF REST API

Open and free. JSON (append nothing) or XML (`Accept: text/xml`). Base host
`https://www.wsdot.wa.gov/ferries/api`. Access code param is `apiaccesscode` (lowercase) on every call.

| Need | Endpoint (REST) | Label |
|------|-----------------|-------|
| Real-time vessel positions + ETA | `/vessels/rest/vessellocations?apiaccesscode={CODE}` (or `/vessellocations/{VesselID}`) | measured (~5 s; do not cache long) |
| Schedule by route + date | `/schedule/rest/schedule/{TripDate}/{RouteID}?apiaccesscode={CODE}` or `/schedule/{TripDate}/{DepartingTerminalID}/{ArrivingTerminalID}` | measured/published (TripDate = `YYYY-MM-DD`) |
| Today's remaining departures | `/schedule/rest/scheduletoday/{RouteID}/{OnlyRemainingTimes}?apiaccesscode={CODE}` | measured/published |
| Terminal sailing space (drive-up vs reservation left) | `/terminals/rest/terminalsailingspace?apiaccesscode={CODE}` (or `/terminalsailingspace/{TerminalID}`) | measured (~5 s; do not cache long) |
| Wait times (vehicle + walk-on, free text) | `/terminals/rest/terminalwaittimes?apiaccesscode={CODE}` (or `/terminalwaittimes/{TerminalID}`) | measured (free-text notes; heuristic content) |
| Valid date range / routes / terminals (id resolution) | `/schedule/rest/validdaterange`, `/schedule/rest/routes/{TripDate}`, `/schedule/rest/terminals/{TripDate}` | published (cache via `/cacheflushdate`) |
| Fares | `/fares/rest/...` | published |

ID resolution (do not hard-code blindly — resolve at runtime and cache): Anacortes departing
`TerminalID` is conventionally `1`; San Juan terminals (Friday Harbor, Orcas, Lopez, Shaw) and the
Anacortes/San Juan Islands `RouteID` MUST be resolved via `/schedule/rest/terminals/{TripDate}` and
`/schedule/rest/routes/{TripDate}` then cached (published; verify-at-runtime).

### Exact fields the planner parses

`vessellocations` -> array of `VesselLocationResponse`:
`VesselID`, `VesselName`, `Mmsi`, `DepartingTerminalID`, `DepartingTerminalName`,
`DepartingTerminalAbbrev`, `ArrivingTerminalID`, `ArrivingTerminalName`, `ArrivingTerminalAbbrev`,
`Latitude`, `Longitude`, `Speed`, `Heading`, `InService`, `AtDock`, `LeftDock` (WCF date),
`Eta` (WCF date), `EtaBasis` (string, e.g. position-based vs scheduled — the honesty source for the
ETA), `ScheduledDeparture` (WCF date), `OpRouteAbbrev` (string[]), `VesselPositionNum`, `SortSeq`,
`ManagedBy` (1=WSF, 2=KCM), `TimeStamp` (WCF date), `VesselWatchStatus`, `VesselWatchMsg`. — measured;
key planner fields: `Latitude`/`Longitude`/`Speed`/`Heading` (position), `Eta`+`EtaBasis` (ETA + its
basis), `AtDock`/`InService`.

`terminalsailingspace` -> array of terminal objects, each:
`TerminalID`, `TerminalSubjectID`, `RegionID`, `TerminalName`, `TerminalAbbrev`, `SortSeq`,
`IsNoFareCollected`, `NoFareCollectedMsg`, and `DepartingSpaces[]` where each `SailingSpaceDeparture`
has: `Departure` (WCF date), `IsCancelled`, `VesselID`, `VesselName`, `MaxSpaceCount`, and
`SpaceForArrivalTerminals[]` where each `SailingSpaceArrival` has: `TerminalID`, `TerminalName`,
`VesselID`, `VesselName`, `DisplayReservableSpace` (bool), `ReservableSpaceCount` (int),
`ReservableSpaceHexColor`, `DisplayDriveUpSpace` (bool), `DriveUpSpaceCount` (int),
`DriveUpSpaceHexColor`, `MaxSpaceCount`, `ArrivalTerminalIDs` (int[]). — measured. **The key trip
signal is `DriveUpSpaceCount` (0 = drive-up lane full) and `ReservableSpaceCount` per
`Departure`+arrival terminal** ("will the 6:30 to Friday Harbor have drive-up room"). Honor
`DisplayDriveUpSpace`/`DisplayReservableSpace` — when false, the count is not meaningful for that
sailing (suppress, do not show 0).

`schedule/{TripDate}/{RouteID}` -> `SchedResponse`:
`ScheduleID`, `ScheduleName`, `ScheduleSeason` (enum Spring/Summer/Fall/Winter), `SchedulePDFUrl`,
`ScheduleStart`, `ScheduleEnd`, `AllRoutes` (int[]), `TerminalCombos[]` where each `SchedTerminalCombo`
has `DepartingTerminalID`, `DepartingTerminalName`, `ArrivingTerminalID`, `ArrivingTerminalName`,
`SailingNotes`, `Annotations` (string[]), `AnnotationsIVR` (string[]), and `Times[]` where each
`SchedTime` has `DepartingTime` (WCF date), `ArrivingTime` (WCF date, nullable), `LoadingRule`
(enum 1=Passenger, 2=Vehicle, 3=Both), `VesselID`, `VesselName`, `VesselHandicapAccessible`,
`VesselPositionNum`, `Routes` (int[]), `AnnotationIndexes` (int[] -> index into `Annotations`). —
published/measured; planner reads `DepartingTime`/`ArrivingTime` per `TerminalCombo` and resolves
`AnnotationIndexes` against `Annotations` for "reservations required / tidal cancellation" notes.

`terminalwaittimes` -> array of `TerminalWaitTimeResponse`:
`TerminalID`, `TerminalSubjectID`, `RegionID`, `TerminalName`, `TerminalAbbrev`, `SortSeq`, and
`WaitTimes[]` where each `WaitTime` has `RouteID` (nullable), `RouteName`, `WaitTimeNotes` (free text),
`WaitTimeLastUpdated` (WCF date), `WaitTimeIVRNotes`. — measured timestamp, but `WaitTimeNotes` is
human-authored free text -> surface as heuristic/advisory, never parse into a number.

## 2. Road traffic (SeaTac <-> Anacortes corridor) — WSDOT Traveler API

Same free code, param `AccessCode` (PascalCase). REST `.svc` JSON endpoints:

| Need | Endpoint | Label |
|------|----------|-------|
| Current travel times (all covered routes) | `/Traffic/api/TravelTimes/TravelTimesREST.svc/GetTravelTimesAsJson?AccessCode={CODE}` | measured (realtime, refreshed ~every 2 min) |
| Single travel time by id | `/Traffic/api/TravelTimes/TravelTimesREST.svc/GetTravelTimeAsJson?AccessCode={CODE}&TravelTimeID={ID}` | measured |
| Traffic flow (congestion enum per station, ~90 s) | `/Traffic/api/TrafficFlow/TrafficFlowREST.svc/GetTrafficFlowsAsJson?AccessCode={CODE}` | measured (realtime) |

### Exact fields the planner parses

`GetTravelTimesAsJson` -> array of `TravelTimeRoute`:
`TravelTimeID` (int, the stable route id to pin), `Name` (string, friendly e.g. "SeaTac-Seattle"),
`Description` (string), `TimeUpdated` (WCF date), `Distance` (decimal miles), `AverageTime` (int min,
typical), `CurrentTime` (int min, live), `StartPoint` and `EndPoint` (each a `RoadwayLocation`:
`Description`, `RoadName`, `Direction` ["Northbound"/"Southbound"], `MilePost` decimal, `Latitude`,
`Longitude`). — measured; planner reads `CurrentTime` (live) vs `AverageTime` (baseline) and
`TimeUpdated` for freshness; `StartPoint`/`EndPoint` mileposts + `Direction` let the planner stitch
contiguous segments into the corridor.

`GetTrafficFlowsAsJson` -> array of `FlowData`:
`FlowDataID` (int station id), `Time` (WCF date), `StationName` (string), `Region` (string),
`FlowStationLocation` (`RoadwayLocation`: same six fields as above), `FlowReadingValue` (int enum:
**0=Unknown, 1=WideOpen, 2=Moderate, 3=Heavy, 4=StopAndGo, 5=NoData**). — measured; the congestion
enum + station milepost let the planner color the corridor where no travel-time route exists.

### SeaTac <-> Anacortes corridor — candidate TravelTime route ids (named, by `Name`)

`TravelTimeID` integers are NOT static across the feed, so the W2 client resolves them at startup by
matching on `Name` and `StartPoint`/`EndPoint` `RoadName`+`MilePost`. Confirmed against the live public
travel-time list (data.wsdot.wa.gov NW feed, 2026-06-27), the northbound I-5 chain that covers the
SOUTHERN part of the corridor uses these route Names (measured):

- `SeaTac-Seattle` (I-5, ~13.0 mi) — leg 1, SeaTac airport area north into Seattle.
- `Seattle-Everett` (I-5, ~26.9 mi; also `Seattle-Everett HOV`, `Seattle-Everett EL`/`EL HOV` express-lane variants) — leg 2.
- `Seattle-Lynnwood` (I-5, ~15.7 mi) — optional finer-grained sub-leg of leg 2.
- `Everett-Marysville` (I-5, ~7.9 mi) — leg 3, north through Everett/Marysville.
- `Everett-Arlington` (I-5, ~13.1 mi) — leg 4, north to Arlington (~MP 208).

**HONEST COVERAGE GAP (measured absence):** WSDOT TravelTimes coverage on I-5 ENDS near Arlington
(~MP 208). There is NO TravelTimes route for the NORTHERN leg — Arlington -> Mount Vernon -> Burlington
(~MP 230) and SR 20 west to Anacortes. That ~40-mile final leg has no realtime travel-time product, so
its ETA is **modeled** (corridor history + free-flow), never measured. `TrafficFlow` stations may exist
a bit farther north than the travel-time routes and can color congestion where available, but do not
assume flow coverage all the way to Anacortes — treat any northern-leg congestion as best-effort
(heuristic) and the leg duration as modeled.

### Future-departure prediction (no API history)

The Traffic API serves realtime only; it has NO historical endpoint (history requires a separate WSDOT
data agreement). So future-departure prediction ("leave SeaTac 3 pm Friday, make the 6:30") is MODELED,
two open paths:

- Self-collect (default): `append_history(record)` writes each travel-time / flow reading to a
  gitignored corridor log; W3's `modeling/traffic/corridor.py` fits a time-of-day / day-of-week model
  that returns an ETA + prediction interval. Open and project-consistent; needs lead time to accrue
  history (modeled; labeled basis).
- Commercial fallback (OPTIONAL, not default, per locked constraint): Google Directions
  (`departure_time`, `traffic_model`), HERE, or TomTom give turnkey predictive ETAs. Pure-open routers
  (OSRM / Valhalla / OpenRouteService) give free-flow time only, no live traffic (modeled/published).

## 3. Flights (SeaTac + seaplane)

| Need | Provider / endpoint | Open | Label |
|------|---------------------|------|-------|
| Live aircraft positions over a bbox | OpenSky `GET https://opensky-network.org/api/states/all?lamin&lomin&lamax&lomax` | yes (OAuth2) | measured; positions only, NO schedules; **may block AWS IPs -> fetch via off-AWS proxy** |
| Live status by aircraft (historical batch) | OpenSky `/flights/arrival` `/flights/departure` (airport=ICAO, begin/end Unix, <=2 days) | yes (OAuth2) | measured; batched nightly, NOT realtime boards |
| Scheduled SeaTac departure/arrival boards | SkyLink (RapidAPI) `GET /v3/schedules/departures` / `/v3/schedules/arrivals` (`?iata=SEA`) | freemium (1000 req/mo) | published/measured |
| Single flight status | SkyLink `GET /v3/flight_status/{flight_number}` | freemium | published/measured |
| Scheduled boards alt | AviationStack `GET /v1/flights` (realtime) / `/v1/flight_schedules` (future) | freemium (~100/mo) | published |
| Kenmore Air seaplane times | Kenmore Air published timetable (no open API) | no API | published static table |

### Fields the planner parses

OpenSky `states/all` -> `{ time, states[] }`. Each state is a positional ARRAY (parse by index, not
key): `[0] icao24`, `[1] callsign`, `[2] origin_country`, `[3] time_position`, `[4] last_contact`,
`[5] longitude`, `[6] latitude`, `[7] baro_altitude` (m), `[8] on_ground` (bool), `[9] velocity`
(m/s), `[10] true_track` (deg), `[11] vertical_rate` (m/s), `[12] sensors`, `[13] geo_altitude` (m),
`[14] squawk`, `[15] spi`, `[16] position_source` (0=ADS-B,1=ASTERIX,2=MLAT,3=FLARM),
`[17] category`. — measured (live position); use `[5]/[6]` lon/lat, `[8]` on_ground, `[9]` velocity,
`[10]` true_track for the live "a plane is on final into SEA" cue. NO scheduled/gate data here.
Auth: OAuth2 client-credentials (token from `auth.opensky-network.org`, Bearer, 30-min expiry — basic
auth is discontinued). Anonymous quota 400 credits/day, bbox <=25 sq° costs 1 credit.

SkyLink `/v3/schedules/{departures|arrivals}` -> per-flight status object exposing (published/measured):
flight number (IATA/ICAO), airline, departure + arrival airport, `scheduled` / `estimated` / `actual`
times, `gate`, `terminal`, `delay` minutes, and `status`. 12-hour schedule window per query
(yesterday -> tomorrow, both directions). Auth header `X-RapidAPI-Key`; base
`https://skylink-api.p.rapidapi.com`. Rate limit: free tier 1000 req/mo (overage $0.007/req).

AviationStack `/v1/flights?access_key={KEY}&dep_iata=SEA` (or `arr_iata`, `flight_status`) -> response
with `pagination` + `data[]`; each item has top-level `flight_date`, `flight_status`
(scheduled|active|landed|cancelled|incident|diverted), and nested objects `departure` and `arrival`
each with `{ airport, iata, icao, terminal, gate, scheduled, estimated, actual, delay }`, plus
`airline { name, iata, icao }`, `flight { number, iata, icao }`, and (realtime only) `live
{ latitude, longitude, altitude, speed_horizontal }`. — published; free tier ~100 req/mo, HTTPS may
require a paid plan.

Kenmore Air seaplane -> NO open API. Ship a curated static table (published columns):
`route` (e.g. Lake Union <-> Friday Harbor), `departure_time`, `arrival_time`, `days_of_operation`,
`season`/effective date range, `terminal`/`dock`. Labeled published (not live), with the source date
stamped; the adapter never claims realtime status for seaplanes.

Approach: static seaplane table + SkyLink for the SeaTac board + OpenSky for live position cues. The
planner labels flight times published, not guaranteed.

## 4. Geocoding (place -> camera target)

| Option | Open | Role | Label |
|--------|------|------|-------|
| Curated Salish gazetteer | yes (offline) | core resolver; deterministic, demo-proof; ~40 places w/ bounds | published/heuristic |
| Photon (Komoot, Apache-2.0, OSM) | yes (self-host) | search-as-you-type, typo tolerance, bbox + location bias | published |
| Nominatim (OSM) | yes (self-host) | structured + reverse geocoding (heavier) | published |
| Pelias (MIT, Elasticsearch) | yes (self-host) | multi-source global autocomplete | published |

Default: gazetteer-first (W1 Agent C `web/lib/geo/gazetteer.ts`), Photon behind a flag (`PHOTON_URL`)
for unknown queries. No proprietary geocoder. (Not a Python backend client — listed for completeness;
no `sources/` adapter required.)

## 5. Adapter contracts (signatures only — W2/W3 consume; NO implementation here)

WSF client — `src/aws_backend/sources/wsf.py` (W2 Agent C). Access code from env `WSDOT_ACCESS_CODE`;
graceful failure (return empty/None) when absent; WCF dates parsed to aware datetimes:

```python
def vessel_locations(vessel_id: int | None = None) -> list[dict]: ...
def schedule(route_id: int, date: datetime.date) -> dict: ...
def sailing_space(terminal_id: int | None = None) -> list[dict]: ...
def wait_times(terminal_id: int | None = None) -> list[dict]: ...
# helpers (resolution, cached via /cacheflushdate):
def routes(trip_date: datetime.date) -> list[dict]: ...
def terminals(trip_date: datetime.date) -> list[dict]: ...
```

WSDOT Traffic client — `src/aws_backend/sources/wsdot_traffic.py` (W2 Agent D). Param `AccessCode`;
`append_history` writes to a gitignored data path for the W3 corridor model:

```python
def travel_times() -> list[dict]: ...                 # all TravelTimeRoute, measured
def traffic_flows() -> list[dict]: ...                # all FlowData, measured
def append_history(record: dict) -> None: ...         # persist a corridor reading (TravelTimeID, CurrentTime, TimeUpdated, ...)
# corridor resolution helper:
def corridor_route_ids() -> list[int]: ...            # resolve SeaTac->Anacortes TravelTimeIDs by Name/milepost
```

Flight adapters — `src/aws_backend/sources/flights.py` (consumed by W3 Agent A connections planner).
OpenSky fetched through an off-AWS proxy (env `OPENSKY_PROXY_URL`) because OpenSky may block AWS IPs;
OAuth2 creds from env (`OPENSKY_CLIENT_ID`/`OPENSKY_CLIENT_SECRET`):

```python
def opensky_states(bbox: tuple[float, float, float, float]) -> list[dict]: ...   # measured live positions
def skylink_board(airport_iata: str, direction: str = "departures") -> list[dict]: ...  # published/measured
def aviationstack_flights(dep_iata: str | None = None, arr_iata: str | None = None) -> list[dict]: ...  # published
def flight_status(flight_number: str) -> dict: ...   # SkyLink single-flight status
```

Seaplane adapter — `src/aws_backend/sources/seaplane.py` (published static table, no network):

```python
def seaplane_schedule(route: str | None = None, day: datetime.date | None = None) -> list[dict]: ...
```

## 6. AWS-IP / rate-limit notes (pinned)

- **OpenSky may block AWS IP ranges.** Mitigation: route OpenSky calls through an off-AWS proxy
  (`OPENSKY_PROXY_URL`); never call OpenSky directly from a Lambda/ECS task in AWS. Quota: anonymous
  400 credits/day (bbox <=25 sq° = 1 credit), authenticated 4000/day. (measured constraint)
- **SkyLink (RapidAPI):** 1000 req/mo free; overage $0.007/req. Cache the SeaTac board; do not poll
  per-turn. (published constraint)
- **AviationStack:** ~100 req/mo free; HTTPS may need a paid tier. Use as fallback only. (published)
- **WSF / WSDOT Traffic:** free, no published hard cap, but `vessellocations` and
  `terminalsailingspace` change ~every 5 s — fetch on demand with a short TTL, never tight-poll.
  (measured)

## 7. What the planner can honestly promise

- "The 6:30 Anacortes -> Friday Harbor sailing currently shows N drive-up spaces" — measured
  (`DriveUpSpaceCount`), with a freshness stamp from `terminalsailingspace`.
- "A vessel is ~12 min out per live position" — measured (`Eta` + `EtaBasis`, `Latitude`/`Longitude`).
- "Leaving SeaTac at 3 pm Friday, the corridor model expects 2 h 05 m +/- 30 m to Anacortes" — modeled,
  interval shown; the southern legs lean on measured `CurrentTime`, the Arlington->Anacortes leg is
  modeled (no TravelTimes coverage).
- "Kenmore seaplane departs Lake Union 5:15 pm (published schedule)" — published, not live.
- Whale forecast on the map stays the hotspot heuristic with its existing `effective_confidence` gate.
