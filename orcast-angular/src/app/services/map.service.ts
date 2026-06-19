/// <reference types="google.maps" />

import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { MapMarker, HeatMapPoint, OrcaSighting, HydrophoneData, MLPrediction, ProbabilityHotspot, MapEvent } from '../models/orca-sighting.model';
import { inBounds, isInWater, snapToWater, distanceKm } from './geo-region';
import { GoogleMapsOverlay } from '@deck.gl/google-maps';
import { HeatmapLayer } from '@deck.gl/aggregation-layers';

export interface RealtimeSightingEvent {
  id: string;
  latitude: number;
  longitude: number;
  locationName: string;
  confidence: number;
  timestamp: Date;
}

@Injectable({
  providedIn: 'root'
})
export class MapService {
  private mapSubject = new BehaviorSubject<google.maps.Map | null>(null);
  private markersSubject = new BehaviorSubject<google.maps.Marker[]>([]);
  // Maps JS API v3.65 removed google.maps.visualization.HeatmapLayer, so the
  // probability surface is now drawn as translucent google.maps.Circle cells.
  private heatMapLayersSubject = new BehaviorSubject<google.maps.Circle[]>([]);

  private hydrophoneMarkers: google.maps.Marker[] = [];
  private sightingMarkers: google.maps.Marker[] = [];
  private historicalMarkers: google.maps.Marker[] = [];
  private mlPredictionMarkers: google.maps.Marker[] = [];
  private reportHotspotMarkers: google.maps.Marker[] = [];
  private heatCircles: google.maps.Circle[] = [];
  private heatOverlay: GoogleMapsOverlay | null = null;

  // Wave B: real instrumented-detection layers (independent, clearable).
  private typedSightingMarkers: google.maps.Marker[] = [];
  private feedConnectors: google.maps.Polyline[] = [];

  // Default map center (San Juan Islands)
  private readonly defaultCenter = { lat: 48.5465, lng: -123.0307 };
  private readonly defaultZoom = 11;

  constructor() {}

  // Observable getters
  get map$(): Observable<google.maps.Map | null> {
    return this.mapSubject.asObservable();
  }

  get markers$(): Observable<google.maps.Marker[]> {
    return this.markersSubject.asObservable();
  }

  get heatMapLayers$(): Observable<google.maps.Circle[]> {
    return this.heatMapLayersSubject.asObservable();
  }

  /** Register an existing Map instance from Angular GoogleMap — do not create a second Map on the same div. */
  registerMap(map: google.maps.Map): void {
    this.mapSubject.next(map);
    const triggerResize = () => google.maps.event.trigger(map, 'resize');
    triggerResize();
    setTimeout(triggerResize, 100);
    setTimeout(triggerResize, 400);
  }

  /**
   * @deprecated Use registerMap() with the Map from `<google-map>` instead.
   * Creating a second Map on the same div causes a black map void.
   */
  initializeMap(mapElement: HTMLElement): google.maps.Map {
    console.warn(
      '[MapService] initializeMap() is deprecated. Pass the existing Map from <google-map> to registerMap() instead.'
    );
    const map = new google.maps.Map(mapElement, {
      zoom: this.defaultZoom,
      center: this.defaultCenter,
      mapTypeId: google.maps.MapTypeId.HYBRID,
      styles: [
        {
          featureType: 'poi',
          stylers: [{ visibility: 'off' }]
        },
        {
          featureType: 'transit',
          stylers: [{ visibility: 'off' }]
        }
      ]
    });

    this.registerMap(map);
    return map;
  }

  clearHydrophoneMarkers(): void {
    this.hydrophoneMarkers.forEach(marker => marker.setMap(null));
    this.hydrophoneMarkers = [];
    this.syncMarkersSubject();
  }

  clearSightingMarkers(): void {
    this.sightingMarkers.forEach(marker => marker.setMap(null));
    this.sightingMarkers = [];
    this.syncMarkersSubject();
  }

  clearHistoricalMarkers(): void {
    this.historicalMarkers.forEach(marker => marker.setMap(null));
    this.historicalMarkers = [];
    this.syncMarkersSubject();
  }

  /** @deprecated Use layer-specific clear methods instead. */
  clearMarkers(): void {
    this.clearHydrophoneMarkers();
    this.clearSightingMarkers();
    this.clearHistoricalMarkers();
    this.clearMLPredictionMarkers();
    this.clearTypedSightings();
    this.clearFeedConnectors();
  }

  private clearMLPredictionMarkers(): void {
    this.mlPredictionMarkers.forEach(marker => marker.setMap(null));
    this.mlPredictionMarkers = [];
    this.syncMarkersSubject();
  }

  clearReportHotspotMarkers(): void {
    this.reportHotspotMarkers.forEach(marker => marker.setMap(null));
    this.reportHotspotMarkers = [];
    this.syncMarkersSubject();
  }

  clearTypedSightings(): void {
    this.typedSightingMarkers.forEach(marker => marker.setMap(null));
    this.typedSightingMarkers = [];
    this.syncMarkersSubject();
  }

  clearFeedConnectors(): void {
    this.feedConnectors.forEach(line => line.setMap(null));
    this.feedConnectors = [];
  }

  private syncMarkersSubject(): void {
    this.markersSubject.next([
      ...this.hydrophoneMarkers,
      ...this.sightingMarkers,
      ...this.historicalMarkers,
      ...this.mlPredictionMarkers,
      ...this.reportHotspotMarkers,
      ...this.typedSightingMarkers
    ]);
  }

  // Clear the probability surface (circle density cells)
  clearHeatMapLayers(): void {
    this.heatCircles.forEach(circle => circle.setMap(null));
    this.heatCircles = [];
    if (this.heatOverlay) {
      this.heatOverlay.setMap(null);
      this.heatOverlay = null;
    }
    this.heatMapLayersSubject.next([]);
  }

  // Add historical sighting markers
  addHistoricalSightings(sightings: OrcaSighting[], filters?: any): void {
    const map = this.mapSubject.value;
    if (!map) return;

    this.clearHistoricalMarkers();

    const filteredSightings = this.filterSightings(sightings, filters);

    filteredSightings.forEach(sighting => {
      if (!inBounds(sighting.latitude, sighting.longitude)) {
        return;
      }
      const water = snapToWater(sighting.latitude, sighting.longitude);

      const marker = new google.maps.Marker({
        position: { lat: water.lat, lng: water.lng },
        map: map,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 8 + (sighting.groupSize / 5),
          fillColor: this.getBehaviorColor(sighting.behavior),
          fillOpacity: 0.8,
          strokeColor: '#ffffff',
          strokeWeight: 2
        },
        title: `${sighting.location} - ${sighting.behavior} (${sighting.year})`
      });

      const infoWindow = new google.maps.InfoWindow({
        content: this.createSightingInfoContent(sighting)
      });

      marker.addListener('click', () => {
        infoWindow.open(map, marker);
      });

      this.historicalMarkers.push(marker);
    });

    this.syncMarkersSubject();
  }

  addRealtimeSightings(events: RealtimeSightingEvent[]): void {
    const map = this.mapSubject.value;
    if (!map) return;

    this.clearSightingMarkers();

    events.forEach(event => {
      if (!this.isValidCoordinate(event.latitude, event.longitude)) {
        return;
      }
      if (!inBounds(event.latitude, event.longitude)) {
        return;
      }
      const water = snapToWater(event.latitude, event.longitude);

      const marker = new google.maps.Marker({
        position: { lat: water.lat, lng: water.lng },
        map: map,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 12,
          fillColor: '#ff9800',
          fillOpacity: 0.9,
          strokeColor: '#ffffff',
          strokeWeight: 2
        },
        title: `${event.locationName} - ${(event.confidence * 100).toFixed(0)}%`
      });

      const infoWindow = new google.maps.InfoWindow({
        content: this.createRealtimeSightingInfoContent(event)
      });

      marker.addListener('click', () => {
        infoWindow.open(map, marker);
      });

      this.sightingMarkers.push(marker);
    });

    this.syncMarkersSubject();
  }

  // Add hydrophone markers
  addHydrophones(hydrophones: HydrophoneData[]): void {
    const map = this.mapSubject.value;
    if (!map) return;

    this.clearHydrophoneMarkers();

    hydrophones.forEach(hydrophone => {
      const online = hydrophone.status === 'online';
      // Online stations read as bright, filled, white-outlined; offline stations
      // are dimmed and grey with a soft outline so they recede on the base map.
      const marker = new google.maps.Marker({
        position: { lat: hydrophone.latitude, lng: hydrophone.longitude },
        map: map,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: hydrophone.detecting ? 20 : 15,
          fillColor: online ? (hydrophone.detecting ? '#ff4444' : '#00bcd4') : '#7a8a99',
          fillOpacity: online ? 0.85 : 0.35,
          strokeColor: online ? '#ffffff' : '#b0bec5',
          strokeWeight: online ? 2 : 1,
          strokeOpacity: online ? 1 : 0.6
        },
        title: `${hydrophone.name} - ${hydrophone.status}`,
        opacity: online ? 1 : 0.6,
        zIndex: online ? 2 : 1
      });

      if (hydrophone.detecting) {
        this.createDetectionWave(marker.getPosition()!, map);
      }

      const infoWindow = new google.maps.InfoWindow({
        content: this.createHydrophoneInfoContent(hydrophone)
      });

      marker.addListener('click', () => {
        infoWindow.open(map, marker);
      });

      this.hydrophoneMarkers.push(marker);
    });

    this.syncMarkersSubject();
  }

  /**
   * Render the ML probability surface as a smooth heat field.
   *
   * Maps JS API v3.65 removed google.maps.visualization.HeatmapLayer, so the
   * surface is drawn with deck.gl's GoogleMapsOverlay + HeatmapLayer (a GPU
   * gaussian heat field that reads well even with sparse, low-variance data).
   * Input is masked to in-water cells so the bloom originates on water.
   * Signature is unchanged so landing and ml-predictions callers stay the same.
   */
  addMLPredictionHeatMap(predictions: MLPrediction[], model: string): void {
    const map = this.mapSubject.value;
    if (!map) return;

    this.clearHeatMapLayers();
    this.clearMLPredictionMarkers();

    const inWaterPredictions = predictions.filter(pred => isInWater(pred.latitude, pred.longitude));
    if (!inWaterPredictions.length) {
      this.heatMapLayersSubject.next([]);
      return;
    }

    const data = inWaterPredictions.map(pred => ({
      position: [pred.longitude, pred.latitude] as [number, number],
      weight: Math.max(pred.probability, 0.01)
    }));

    // Cool -> warm ramp tuned for a dark satellite base.
    const colorRange: [number, number, number][] = [
      [0, 120, 200],
      [0, 180, 220],
      [40, 220, 170],
      [170, 230, 90],
      [255, 205, 0],
      [255, 110, 0]
    ];

    const heatLayer = new HeatmapLayer({
      id: 'orca-probability-heat',
      data,
      getPosition: (d: { position: [number, number] }) => d.position,
      getWeight: (d: { weight: number }) => d.weight,
      radiusPixels: 110,
      intensity: 0.4,
      threshold: 0.03,
      opacity: 0.5,
      colorRange,
      aggregation: 'SUM'
    });

    this.heatOverlay = new GoogleMapsOverlay({ layers: [heatLayer] });
    this.heatOverlay.setMap(map);

    this.heatMapLayersSubject.next([]);
    this.syncMarkersSubject();
  }

  /**
   * Generic real-detection heat field for the hero map.
   *
   * Mirrors addMLPredictionHeatMap but takes raw weighted points instead of
   * MLPrediction objects. Points are masked to in-water cells, then drawn with
   * the same deck.gl GoogleMapsOverlay + HeatmapLayer and cool -> warm ramp.
   * Reuses this.heatOverlay so it tears down via clearHeatMapLayers().
   */
  addDetectionHeat(points: Array<{ lat: number; lng: number; weight: number }>): void {
    const map = this.mapSubject.value;
    if (!map) return;

    this.clearHeatMapLayers();

    const inWaterPoints = points.filter(p => isInWater(p.lat, p.lng));
    if (!inWaterPoints.length) {
      this.heatMapLayersSubject.next([]);
      return;
    }

    const data = inWaterPoints.map(p => ({
      position: [p.lng, p.lat] as [number, number],
      weight: Math.max(p.weight, 0.01)
    }));

    // Same cool -> warm ramp as the ML surface, tuned for a dark satellite base.
    const colorRange: [number, number, number][] = [
      [0, 120, 200],
      [0, 180, 220],
      [40, 220, 170],
      [170, 230, 90],
      [255, 205, 0],
      [255, 110, 0]
    ];

    const heatLayer = new HeatmapLayer({
      id: 'orca-detection-heat',
      data,
      getPosition: (d: { position: [number, number] }) => d.position,
      getWeight: (d: { weight: number }) => d.weight,
      radiusPixels: 110,
      intensity: 0.4,
      threshold: 0.03,
      opacity: 0.5,
      colorRange,
      aggregation: 'SUM'
    });

    this.heatOverlay = new GoogleMapsOverlay({ layers: [heatLayer] });
    this.heatOverlay.setMap(map);

    this.heatMapLayersSubject.next([]);
  }

  /**
   * Plot instrumented detections with modality-aware glyphs.
   *
   * Visual sightings are filled circles colored/scaled by confidence; acoustic
   * detections are a distinct hollow ring (the marker is the hydrophone, not the
   * orca). InfoWindows state the modality honestly. Owns its own clearable layer.
   */
  addTypedSightings(events: MapEvent[]): void {
    const map = this.mapSubject.value;
    if (!map) return;

    this.clearTypedSightings();

    events.forEach(event => {
      if (!this.isValidCoordinate(event.latitude, event.longitude)) {
        return;
      }
      if (!inBounds(event.latitude, event.longitude)) {
        return;
      }
      const water = snapToWater(event.latitude, event.longitude);
      if (!isInWater(water.lat, water.lng)) {
        return;
      }

      const confidence = Math.max(0, Math.min(1, event.confidence));
      const icon: google.maps.Symbol =
        event.kind === 'acoustic'
          ? {
              // Hollow, bold ring so it reads as "sound from a station",
              // visibly different from the filled visual dot.
              path: google.maps.SymbolPath.CIRCLE,
              scale: 13,
              fillColor: '#26c6da',
              fillOpacity: 0.12,
              strokeColor: '#26c6da',
              strokeWeight: 3,
              strokeOpacity: 0.95
            }
          : {
              path: google.maps.SymbolPath.CIRCLE,
              scale: 9 + confidence * 4,
              fillColor: this.getConfidenceColor(confidence),
              fillOpacity: 0.9,
              strokeColor: '#ffffff',
              strokeWeight: 2
            };

      const title =
        event.kind === 'acoustic'
          ? `Heard at ${event.locationName}`
          : `${event.locationName} sighting`;

      const marker = new google.maps.Marker({
        position: { lat: water.lat, lng: water.lng },
        map,
        icon,
        title,
        zIndex: event.kind === 'acoustic' ? 3 : 4
      });

      const infoWindow = new google.maps.InfoWindow({
        content: this.createTypedSightingInfoContent(event)
      });

      marker.addListener('click', () => {
        infoWindow.open(map, marker);
      });

      this.typedSightingMarkers.push(marker);
    });

    this.syncMarkersSubject();
  }

  /**
   * Draw faint connectors from each visual sighting to its nearest in-region
   * hydrophone, hinting at which station could corroborate the detection.
   * Owns its own clearable polyline layer; no-ops when no stations are given.
   */
  addFeedConnectors(events: MapEvent[], stations: HydrophoneData[]): void {
    const map = this.mapSubject.value;
    if (!map) return;

    this.clearFeedConnectors();

    const inRegionStations = stations.filter(s =>
      this.isValidCoordinate(s.latitude, s.longitude) && inBounds(s.latitude, s.longitude)
    );
    if (!inRegionStations.length) {
      return;
    }

    events
      .filter(event => event.kind === 'visual')
      .forEach(event => {
        if (!this.isValidCoordinate(event.latitude, event.longitude)) {
          return;
        }
        if (!inBounds(event.latitude, event.longitude)) {
          return;
        }
        const water = snapToWater(event.latitude, event.longitude);

        let nearest: HydrophoneData | null = null;
        let nearestDist = Infinity;
        for (const station of inRegionStations) {
          const dist = distanceKm(
            { lat: water.lat, lng: water.lng },
            { lat: station.latitude, lng: station.longitude }
          );
          if (dist < nearestDist) {
            nearestDist = dist;
            nearest = station;
          }
        }
        if (!nearest) {
          return;
        }

        const line = new google.maps.Polyline({
          path: [
            { lat: water.lat, lng: water.lng },
            { lat: nearest.latitude, lng: nearest.longitude }
          ],
          map,
          strokeColor: '#80deea',
          strokeOpacity: 0.35,
          strokeWeight: 1.5,
          zIndex: 0
        });

        this.feedConnectors.push(line);
      });
  }

  // Center map on coordinates
  centerMap(lat: number, lng: number, zoom?: number): void {
    const map = this.mapSubject.value;
    if (!map) return;

    map.setCenter({ lat, lng });
    if (zoom) {
      map.setZoom(zoom);
    }
  }

  /**
   * Plot probability report hotspots as circle markers.
   * Markers are scaled and colored by probability (higher = warmer and larger).
   * Owns its own layer; clears only that layer before plotting.
   * @param hotspots Hotspots from a probability report.
   * @param onSelect Optional callback fired with the hotspot when its marker is clicked.
   */
  addReportHotspots(
    hotspots: ProbabilityHotspot[],
    onSelect?: (hotspot: ProbabilityHotspot) => void
  ): void {
    const map = this.mapSubject.value;
    if (!map) return;

    this.clearReportHotspotMarkers();

    hotspots.forEach(hotspot => {
      const lat = hotspot.center_latitude;
      const lng = hotspot.center_longitude;
      if (!this.isValidCoordinate(lat, lng)) {
        return;
      }
      if (!inBounds(lat, lng)) {
        return;
      }
      const water = snapToWater(lat, lng);

      const probability = Number.isFinite(hotspot.probability) ? hotspot.probability : 0;
      const chance = Math.round(probability * 100);

      const marker = new google.maps.Marker({
        position: { lat: water.lat, lng: water.lng },
        map,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: this.getHotspotScale(probability),
          fillColor: this.getHotspotColor(probability),
          fillOpacity: 0.85,
          strokeColor: '#ffffff',
          strokeWeight: 2
        },
        title: `${hotspot.name} — ${chance}%`
      });

      const infoWindow = new google.maps.InfoWindow({
        content: this.createReportHotspotInfoContent(hotspot)
      });

      marker.addListener('click', () => {
        infoWindow.open(map, marker);
        if (onSelect) {
          onSelect(hotspot);
        }
      });

      this.reportHotspotMarkers.push(marker);
    });

    this.syncMarkersSubject();
  }

  /** Fit the map viewport to a set of coordinates. Falls back to centerMap for a single point. */
  fitBounds(coords: { lat: number; lng: number }[]): void {
    const map = this.mapSubject.value;
    if (!map) return;

    const valid = coords.filter(c => this.isValidCoordinate(c.lat, c.lng));
    if (valid.length === 0) return;

    if (valid.length === 1) {
      this.centerMap(valid[0].lat, valid[0].lng, 12);
      return;
    }

    const bounds = new google.maps.LatLngBounds();
    valid.forEach(c => bounds.extend(new google.maps.LatLng(c.lat, c.lng)));
    map.fitBounds(bounds, 64);
  }

  private getHotspotColor(probability: number): string {
    if (probability >= 0.7) return '#ff4444';
    if (probability >= 0.5) return '#ff9800';
    if (probability >= 0.3) return '#ffd54f';
    return '#4fc3f7';
  }

  private getHotspotScale(probability: number): number {
    const clamped = Math.max(0, Math.min(1, probability));
    return 9 + clamped * 13;
  }

  private createReportHotspotInfoContent(hotspot: ProbabilityHotspot): string {
    const chance = Math.round((Number.isFinite(hotspot.probability) ? hotspot.probability : 0) * 100);
    return `
      <div style="color: #001e3c; min-width: 200px;">
        <h3 style="margin: 0 0 6px;">${hotspot.name}</h3>
        <p style="margin: 4px 0;"><strong>Chance of sightings:</strong> ${chance}%</p>
        <p style="margin: 4px 0;">${hotspot.detection_count} recent sighting(s) near this area</p>
      </div>
    `;
  }

  private isValidCoordinate(latitude: number, longitude: number): boolean {
    return (
      Number.isFinite(latitude) &&
      Number.isFinite(longitude) &&
      latitude >= -90 &&
      latitude <= 90 &&
      longitude >= -180 &&
      longitude <= 180
    );
  }

  /** Confidence [0..1] -> cool -> warm accent for visual sighting dots. */
  private getConfidenceColor(confidence: number): string {
    if (confidence >= 0.75) return '#ff6e00';
    if (confidence >= 0.5) return '#ffcd00';
    if (confidence >= 0.25) return '#28dcaa';
    return '#00b4dc';
  }

  private createTypedSightingInfoContent(event: MapEvent): string {
    const chance = `${(Math.max(0, Math.min(1, event.confidence)) * 100).toFixed(0)}%`;
    const date = event.timestamp.toLocaleString();
    const body =
      event.kind === 'acoustic'
        ? `Acoustic detection — heard at ${event.locationName}; marker is the hydrophone, not the orca.`
        : `Visual sighting — ${event.source}`;
    const heading = event.kind === 'acoustic' ? `Heard at ${event.locationName}` : event.locationName;
    return `
      <div style="color: #001e3c; min-width: 220px;">
        <h3 style="margin: 0 0 6px;">${heading}</h3>
        <p style="margin: 4px 0;">${body}</p>
        <p style="margin: 4px 0;"><strong>Confidence:</strong> ${chance}</p>
        <p style="margin: 4px 0;"><strong>Date:</strong> ${date}</p>
      </div>
    `;
  }

  private createRealtimeSightingInfoContent(event: RealtimeSightingEvent): string {
    return `
      <div style="color: #001e3c; min-width: 200px;">
        <h3>${event.locationName}</h3>
        <p><strong>Time:</strong> ${event.timestamp.toLocaleString()}</p>
        <p><strong>Confidence:</strong> ${(event.confidence * 100).toFixed(0)}%</p>
      </div>
    `;
  }

  // Private helper methods
  private filterSightings(sightings: OrcaSighting[], filters?: any): OrcaSighting[] {
    if (!filters) return sightings;

    return sightings.filter(sighting => {
      if (filters.maxYear && sighting.year > filters.maxYear) return false;
      if (filters.minYear && sighting.year < filters.minYear) return false;

      if (filters.behaviors && filters.behaviors.length > 0) {
        if (!filters.behaviors.includes(sighting.behavior)) return false;
      }

      if (filters.podTypes && filters.podTypes.length > 0 && sighting.pod) {
        const podType = this.getPodType(sighting.pod);
        if (!filters.podTypes.includes(podType)) return false;
      }

      return true;
    });
  }

  private getBehaviorColor(behavior: string): string {
    switch (behavior) {
      case 'feeding': return '#ff4444';
      case 'traveling': return '#44ff44';
      case 'socializing': return '#4444ff';
      case 'resting': return '#ffff44';
      default: return '#ff44ff';
    }
  }

  private getPodType(podName: string): string {
    if (podName.includes('J-') || podName.includes('K-') || podName.includes('L-')) {
      return 'resident';
    } else if (podName.includes('T-')) {
      return 'transient';
    } else {
      return 'offshore';
    }
  }

  /**
   * Map a probability [0..1] to a circle fill color along a cool -> warm ramp.
   * Color stops are taken from the per-model gradient so model coloring intent
   * is preserved now that the heatmap layer is gone.
   */
  private getHeatColor(probability: number, model: string): string {
    const stops = this.getModelGradient(model)
      .map(stop => this.parseRgba(stop))
      .filter(rgb => rgb !== null) as Array<{ r: number; g: number; b: number; a: number }>;

    // Drop fully transparent anchor stops; they only exist to fade the old heatmap.
    const opaqueStops = stops.filter(s => s.a > 0);
    const ramp = opaqueStops.length >= 2 ? opaqueStops : stops;
    if (ramp.length === 0) {
      return '#4fc3f7';
    }
    if (ramp.length === 1) {
      const { r, g, b } = ramp[0];
      return this.toHex(r, g, b);
    }

    const t = Math.max(0, Math.min(1, probability));
    const scaled = t * (ramp.length - 1);
    const lower = Math.floor(scaled);
    const upper = Math.min(ramp.length - 1, lower + 1);
    const frac = scaled - lower;

    const a = ramp[lower];
    const b = ramp[upper];
    const r = Math.round(a.r + (b.r - a.r) * frac);
    const g = Math.round(a.g + (b.g - a.g) * frac);
    const bl = Math.round(a.b + (b.b - a.b) * frac);
    return this.toHex(r, g, bl);
  }

  private parseRgba(value: string): { r: number; g: number; b: number; a: number } | null {
    const match = value.match(/rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)/i);
    if (!match) {
      return null;
    }
    return {
      r: Number(match[1]),
      g: Number(match[2]),
      b: Number(match[3]),
      a: match[4] !== undefined ? Number(match[4]) : 1
    };
  }

  private toHex(r: number, g: number, b: number): string {
    const channel = (n: number) => Math.max(0, Math.min(255, n)).toString(16).padStart(2, '0');
    return `#${channel(r)}${channel(g)}${channel(b)}`;
  }

  private getModelGradient(modelType: string): string[] {
    const gradients: { [key: string]: string[] } = {
      pinn: [
        'rgba(0, 255, 255, 0)',
        'rgba(0, 255, 255, 1)',
        'rgba(0, 127, 255, 1)',
        'rgba(127, 0, 255, 1)',
        'rgba(255, 0, 255, 1)'
      ],
      behavioral: [
        'rgba(0, 255, 0, 0)',
        'rgba(0, 255, 0, 1)',
        'rgba(127, 255, 0, 1)',
        'rgba(255, 255, 0, 1)',
        'rgba(255, 127, 0, 1)',
        'rgba(255, 0, 0, 1)'
      ],
      ensemble: [
        'rgba(255, 255, 0, 0)',
        'rgba(255, 255, 0, 1)',
        'rgba(255, 192, 0, 1)',
        'rgba(255, 128, 0, 1)',
        'rgba(255, 64, 0, 1)',
        'rgba(255, 0, 0, 1)'
      ]
    };

    return gradients[modelType] || gradients['ensemble'];
  }

  private createDetectionWave(position: google.maps.LatLng, map: google.maps.Map): void {
    const wave = new google.maps.Circle({
      center: position,
      radius: 100,
      strokeColor: '#ff4444',
      strokeOpacity: 0.8,
      strokeWeight: 2,
      fillOpacity: 0,
      map: map
    });

    let radius = 100;
    const animation = setInterval(() => {
      radius += 50;
      wave.setRadius(radius);

      if (radius > 1000) {
        wave.setMap(null);
        clearInterval(animation);
      }
    }, 100);
  }

  private createSightingInfoContent(sighting: OrcaSighting): string {
    return `
      <div style="color: #001e3c; min-width: 200px;">
        <h3>${sighting.location}</h3>
        <p><strong>Date:</strong> ${sighting.date.toLocaleDateString()}</p>
        <p><strong>Behavior:</strong> ${sighting.behavior}</p>
        <p><strong>Pod size:</strong> ${sighting.groupSize} individuals</p>
        <p><strong>Confidence:</strong> ${(sighting.confidence * 100).toFixed(0)}%</p>
      </div>
    `;
  }

  private createHydrophoneInfoContent(hydrophone: HydrophoneData): string {
    return `
      <div style="color: #001e3c; min-width: 200px;">
        <h3>${hydrophone.name}</h3>
        <p><strong>Location:</strong> ${hydrophone.location}</p>
        <p><strong>Status:</strong> ${hydrophone.status}</p>
        <p><strong>Detecting:</strong> ${hydrophone.detecting ? 'YES' : 'No'}</p>
        ${hydrophone.lastDetection ?
          `<p><strong>Last Detection:</strong> ${this.getTimeAgo(hydrophone.lastDetection)}</p>` : ''}
        ${hydrophone.streamUrl ?
          `<button onclick="window.open('${hydrophone.streamUrl}', '_blank')"
                   style="background: #4fc3f7; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">
              🔊 Listen Live
          </button>` : ''}
      </div>
    `;
  }

  private getTimeAgo(date: Date): string {
    const minutes = Math.floor((Date.now() - date.getTime()) / (1000 * 60));
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }
}
