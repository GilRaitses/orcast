import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import {
  OrcaSighting,
  HydrophoneData,
  Detection,
  MLPredictionData,
  ProbabilityReportResponse
} from '../models/orca-sighting.model';
import { environment } from '../../environments/environment';

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

  generateMLPredictions(model: string, hours: number, threshold: number): Observable<MLPredictionData> {
    const payload = {
      lat: 48.5465,
      lng: -123.0307,
      radius_km: 12,
      grid_resolution: 0.04,
      hours
    };

    return this.http.post<any>(`${this.backendUrl}/forecast/spatial`, payload).pipe(
      map(response => this.convertSpatialForecastToPredictions(response, model, threshold)),
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
    return sightings.map((item: any, index: number) => {
      const timestamp = item.observation_timestamp || item.timestamp || new Date().toISOString();
      const date = new Date(timestamp);
      return {
        id: item.sighting_id || item.id || `sighting-${index}`,
        date,
        latitude: Number(item.latitude),
        longitude: Number(item.longitude),
        behavior: this.normalizeBehavior(item.behavior_primary || item.behavior),
        pod: item.pod || this.inferPod(item),
        location: item.location_name || item.location || item.source || 'San Juan Islands',
        groupSize: Number(item.pod_size || item.count || 1),
        confidence: Number(item.data_quality_score || item.confidence || 0.5),
        year: date.getFullYear()
      } as OrcaSighting;
    });
  }

  private convertHydrophones(response: any): HydrophoneData[] {
    const hydrophones = response.hydrophones || response.data || [];
    return hydrophones.map((item: any) => ({
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
    return events.map((event: any, index: number) => ({
      id: event.id || `detection-${index}`,
      timestamp: new Date(event.timestamp),
      hydrophone: event.location_name || event.source || 'Sighting',
      hydrophoneId: event.source || event.id || 'sighting',
      confidence: Number(event.confidence || 0.75),
      frequency: Number(event.frequency || 0),
      duration: Number(event.duration || 0),
      callType: 'unknown'
    }));
  }

  private convertSpatialForecastToPredictions(response: any, model: string, threshold: number): MLPredictionData {
    const gridPoints = response.grid_points || [];
    const predictions: Array<{ latitude: number; longitude: number; probability: number; hour: number }> = gridPoints
      .filter((point: any) => Number(point.probability || 0) >= threshold)
      .map((point: any, index: number) => ({
        latitude: Number(point.lat),
        longitude: Number(point.lng),
        probability: Number(point.probability || 0),
        hour: index
      }));

    const probabilities: number[] = predictions.map((point: { probability: number }) => point.probability);
    return {
      model,
      predictions,
      metadata: {
        totalPredictions: predictions.length,
        averageProbability: probabilities.length ? probabilities.reduce((sum: number, value: number) => sum + value, 0) / probabilities.length : 0,
        maxProbability: probabilities.length ? Math.max(...probabilities) : 0
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

  private inferPod(item: any): string {
    if (item.ecotype === 'transient') return 'T-Pod';
    if (item.ecotype === 'offshore') return 'Offshore';
    return 'J-Pod';
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    console.error('Backend service error:', error);
    return throwError(() => new Error(error.message || 'Backend service error'));
  }
}

