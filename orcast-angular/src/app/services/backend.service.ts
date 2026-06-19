import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import {
  OrcaSighting,
  HydrophoneData,
  Detection,
  MapEvent,
  MLPredictionData,
  ProbabilityReportResponse
} from '../models/orca-sighting.model';
import { environment } from '../../environments/environment';
import { inBounds, snapToWater } from './geo-region';

@Injectable({
  providedIn: 'root'
})
export class BackendService {
  private readonly backendUrl = environment.apiBaseUrl.replace(/\/$/, '');

  constructor(private http: HttpClient) {}

  getHealth(): Observable<any> {
    return this.http.get(`${this.backendUrl}/health`).pipe(
      catchError(this.handleError)
    );
  }

  getHistoricalSightings(): Observable<OrcaSighting[]> {
    return this.http.get<any>(`${this.backendUrl}/api/verified-sightings`).pipe(
      map(response => this.convertVerifiedSightings(response)),
      catchError(this.handleError)
    );
  }

  getHydrophoneData(): Observable<HydrophoneData[]> {
    return this.http.get<any>(`${this.backendUrl}/api/live-hydrophones`).pipe(
      map(response => this.convertHydrophones(response)),
      catchError(this.handleError)
    );
  }

  getRecentDetections(): Observable<Detection[]> {
    return this.http.get<any>(`${this.backendUrl}/api/realtime/events`).pipe(
      map(response => this.convertEventsToDetections(response)),
      catchError(this.handleError)
    );
  }

  getMapEvents(): Observable<MapEvent[]> {
    return this.http.get<any>(`${this.backendUrl}/api/realtime/events`).pipe(
      map(response => this.convertEventsToMapEvents(response)),
      catchError(this.handleError)
    );
  }

  generateMLPredictions(hours: number, threshold: number, radiusKm = 12): Observable<MLPredictionData> {
    const payload = {
      lat: 48.5465,
      lng: -123.0307,
      radius_km: radiusKm,
      grid_resolution: 0.04,
      hours
    };

    return this.http.post<any>(`${this.backendUrl}/forecast/spatial`, payload).pipe(
      map(response => this.convertSpatialForecastToPredictions(response, threshold)),
      catchError(this.handleError)
    );
  }

  getEnvironmentalData(): Observable<any> {
    return this.http.get<any>(`${this.backendUrl}/api/environmental`).pipe(
      map(response => response.environmental_data || response),
      catchError(this.handleError)
    );
  }

  generateProbabilityReport(minConfidence = 0): Observable<ProbabilityReportResponse> {
    return this.http.post<any>(`${this.backendUrl}/api/reports/probability`, {
      region: 'san_juan_islands',
      min_confidence: minConfidence,
      report_format: 'json'
    }).pipe(
      map(response => response.report as ProbabilityReportResponse),
      catchError(this.handleError)
    );
  }

  downloadReportCsv(reportId: string): Observable<Blob> {
    return this.http.get(`${this.backendUrl}/api/reports/${reportId}.csv`, {
      responseType: 'blob'
    }).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * Submit a community shore/kayak sighting for moderation review.
   * Coordinates are optional; the honeypot `website` field is always sent empty.
   */
  submitCommunitySighting(payload: {
    place: string;
    latitude?: number;
    longitude?: number;
    observed_at: string;
    behavior: string;
    count?: number;
    notes?: string;
    observer_name?: string;
  }): Observable<{ id: string; status: string }> {
    return this.http.post<{ id: string; status: string }>(
      `${this.backendUrl}/api/community/sightings`,
      { ...payload, website: '' }
    ).pipe(
      catchError(this.handleError)
    );
  }

  /**
   * Report summary (not LLM): formats the latest probability report as a natural-language answer.
   */
  queryAgent(prompt: string): Observable<any> {
    return this.generateProbabilityReport(0).pipe(
      map(report => ({ answer: this.formatAgentResponse(prompt, report) })),
      catchError(this.handleError)
    );
  }

  private convertVerifiedSightings(response: any): OrcaSighting[] {
    const sightings = response.sightings || response.data || [];
    return sightings.reduce((kept: OrcaSighting[], item: any, index: number) => {
      const lat = Number(item.latitude);
      const lng = Number(item.longitude);
      if (!inBounds(lat, lng)) {
        return kept;
      }

      const timestamp = item.observation_timestamp || item.timestamp || new Date().toISOString();
      const date = new Date(timestamp);
      const water = snapToWater(lat, lng);
      kept.push({
        id: item.sighting_id || item.id || `sighting-${index}`,
        date,
        latitude: water.lat,
        longitude: water.lng,
        behavior: this.normalizeBehavior(item.behavior_primary || item.behavior),
        // Only surface a pod label the source actually provided; never inferred.
        pod: item.pod || undefined,
        location: item.location_name || item.location || item.source || 'San Juan Islands',
        groupSize: Number(item.pod_size || item.count || 1),
        confidence: Number(item.data_quality_score || item.confidence || 0.5),
        year: date.getFullYear()
      } as OrcaSighting);
      return kept;
    }, [] as OrcaSighting[]);
  }

  private convertHydrophones(response: any): HydrophoneData[] {
    const hydrophones = response.hydrophones || response.data || [];
    return hydrophones
      .filter((item: any) => inBounds(Number(item.latitude), Number(item.longitude)))
      .map((item: any) => ({
        id: item.id,
        name: item.name,
        location: item.location || item.name,
        latitude: Number(item.latitude),
        longitude: Number(item.longitude),
        status: item.status === 'offline' ? 'offline' : 'online',
        detecting: Boolean(item.detecting),
        lastDetection: item.lastDetection ? new Date(item.lastDetection) : null,
        streamUrl: item.streamUrl || null
      }));
  }

  private convertEventsToDetections(response: any): Detection[] {
    const events = response.events || [];
    return events.reduce((kept: Detection[], event: any, index: number) => {
      const hasCoords = event.location?.lat != null && event.location?.lng != null;
      let latitude: number | undefined;
      let longitude: number | undefined;

      if (hasCoords) {
        const lat = Number(event.location.lat);
        const lng = Number(event.location.lng);
        if (!inBounds(lat, lng)) {
          return kept;
        }
        const water = snapToWater(lat, lng);
        latitude = water.lat;
        longitude = water.lng;
      }

      kept.push({
        id: event.id || `detection-${index}`,
        timestamp: new Date(event.timestamp),
        hydrophone: event.location_name || event.source || 'Sighting',
        hydrophoneId: event.source || event.id || 'sighting',
        confidence: Number(event.confidence || 0.75),
        frequency: Number(event.frequency || 0),
        duration: Number(event.duration || 0),
        callType: 'unknown',
        latitude,
        longitude,
        locationName: event.location_name
      });
      return kept;
    }, [] as Detection[]);
  }

  private convertEventsToMapEvents(response: any): MapEvent[] {
    const events = response.events || [];
    return events.reduce((kept: MapEvent[], event: any, index: number) => {
      const latitude = Number(event.location?.lat);
      const longitude = Number(event.location?.lng);
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        return kept;
      }

      const confidence = Number(event.confidence);
      kept.push({
        id: event.id || `event-${index}`,
        kind: event.source === 'orcahello' ? 'acoustic' : 'visual',
        source: event.source,
        latitude,
        longitude,
        locationName: event.location_name || event.source,
        confidence: Number.isFinite(confidence) ? confidence : 0.5,
        timestamp: new Date(event.timestamp)
      });
      return kept;
    }, [] as MapEvent[]);
  }

  private convertSpatialForecastToPredictions(response: any, threshold: number): MLPredictionData {
    const gridPoints = response.grid_points || [];
    const allProbabilities = gridPoints.map((point: any) => Number(point.probability || 0));
    const unfilteredMaxProbability = allProbabilities.length ? Math.max(...allProbabilities) : 0;

    let thresholdApplied = threshold;
    let thresholdAutoAdjusted = false;
    if (unfilteredMaxProbability < threshold) {
      thresholdApplied = Math.floor(unfilteredMaxProbability * 100) / 100;
      thresholdAutoAdjusted = true;
    }

    const predictions: Array<{ latitude: number; longitude: number; probability: number; hour: number }> = gridPoints
      .filter((point: any) => Number(point.probability || 0) >= thresholdApplied)
      .map((point: any, index: number) => ({
        latitude: Number(point.lat),
        longitude: Number(point.lng),
        probability: Number(point.probability || 0),
        hour: index
      }));

    const probabilities: number[] = predictions.map((point: { probability: number }) => point.probability);
    const modelId = response.model || response.model_version || 'aws-deterministic-hotspot-v1';
    return {
      model: modelId,
      predictions,
      metadata: {
        totalPredictions: predictions.length,
        averageProbability: probabilities.length ? probabilities.reduce((sum: number, value: number) => sum + value, 0) / probabilities.length : 0,
        maxProbability: probabilities.length ? Math.max(...probabilities) : 0,
        modelVersion: modelId,
        unfilteredMaxProbability,
        thresholdAutoAdjusted,
        thresholdApplied
      }
    };
  }

  private formatAgentResponse(prompt: string, report: ProbabilityReportResponse): string {
    const topHotspot = report.hotspots?.[0];
    if (!topHotspot) {
      return `Report ${report.report_id} found no active hotspots for "${prompt}".`;
    }
    return `Report ${report.report_id}: ${topHotspot.name} is the top hotspot with ${(topHotspot.probability * 100).toFixed(1)}% probability and ${(topHotspot.confidence * 100).toFixed(1)}% confidence.`;
  }

  private normalizeBehavior(value: string | undefined): OrcaSighting['behavior'] {
    const normalized = (value || 'unknown').toLowerCase();
    if (normalized === 'foraging') return 'feeding';
    if (['feeding', 'traveling', 'socializing', 'resting', 'unknown'].includes(normalized)) {
      return normalized as OrcaSighting['behavior'];
    }
    return 'unknown';
  }

  private normalizeCallType(value: string | undefined): Detection['callType'] {
    if (value === 'resident' || value === 'transient') {
      return value;
    }
    return 'unknown';
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    console.error('Backend service error:', error);
    return throwError(() => new Error(error.message || 'Backend service error'));
  }
}

