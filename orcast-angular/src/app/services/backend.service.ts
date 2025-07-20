import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, of, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { 
  OrcaSighting, 
  HydrophoneData, 
  Detection, 
  MLPredictionData, 
  BackendResponse 
} from '../models/orca-sighting.model';

@Injectable({
  providedIn: 'root'
})
export class BackendService {
  private readonly backendUrl = 'https://orcast-production-backend-2cvqukvhga-uw.a.run.app';

  constructor(private http: HttpClient) {}

  // Health check
  getHealth(): Observable<any> {
    return this.http.get(`${this.backendUrl}/health`).pipe(
      catchError(this.handleError)
    );
  }

  // Historical sightings
  getHistoricalSightings(): Observable<OrcaSighting[]> {
    return this.http.get<BackendResponse<OrcaSighting[]>>(`${this.backendUrl}/api/verified-sightings`).pipe(
      map(response => response.data || []),
      catchError(() => of(this.generateMockSightings()))
    );
  }

  // Live hydrophone data  
  getHydrophoneData(): Observable<HydrophoneData[]> {
    return this.http.get<BackendResponse<HydrophoneData[]>>(`${this.backendUrl}/api/live-hydrophones`).pipe(
      map(response => response.data || []),
      catchError(() => of(this.generateMockHydrophones()))
    );
  }

  // Recent detections
  getRecentDetections(): Observable<Detection[]> {
    return this.http.get<BackendResponse<Detection[]>>(`${this.backendUrl}/api/recent-detections`).pipe(
      map(response => response.data || []),
      catchError(() => of([]))
    );
  }

  // ML Predictions
  generateMLPredictions(model: string, hours: number, threshold: number): Observable<MLPredictionData> {
    const payload = {
      model,
      hours,
      threshold,
      latitude: 48.5465,
      longitude: -123.0307
    };

    return this.http.post<BackendResponse<MLPredictionData>>(`${this.backendUrl}/api/ml/predict`, payload).pipe(
      map(response => response.data),
      catchError(() => of(this.generateMockPredictions(model, hours, threshold)))
    );
  }

  // Environmental data
  getEnvironmentalData(): Observable<any> {
    return this.http.get<BackendResponse<any>>(`${this.backendUrl}/api/environmental`).pipe(
      map(response => response.data),
      catchError(this.handleError)
    );
  }

  // Agent API
  queryAgent(prompt: string): Observable<any> {
    return this.http.post<BackendResponse<any>>(`${this.backendUrl}/api/agent/query`, { prompt }).pipe(
      map(response => response.data),
      catchError(this.handleError)
    );
  }

  // Private helper methods
  private handleError(error: HttpErrorResponse): Observable<never> {
    console.error('Backend service error:', error);
    return throwError(() => new Error(error.message || 'Backend service error'));
  }

  private generateMockSightings(): OrcaSighting[] {
    const sightings: OrcaSighting[] = [];
    const behaviors: Array<'feeding' | 'traveling' | 'socializing' | 'resting' | 'unknown'> = 
      ['feeding', 'traveling', 'socializing', 'resting', 'unknown'];
    const pods = ['J-Pod', 'K-Pod', 'L-Pod', 'T-001', 'T-002', 'T-123', 'Offshore-1'];
    const locations = [
      { name: 'Lime Kiln Point', lat: 48.5165, lng: -123.1524 },
      { name: 'False Bay', lat: 48.4865, lng: -123.0924 },
      { name: 'Cattle Point', lat: 48.4515, lng: -122.9624 },
      { name: 'West Side San Juan', lat: 48.5365, lng: -123.1724 },
      { name: 'Haro Strait', lat: 48.5865, lng: -123.1124 },
      { name: 'Boundary Pass', lat: 48.7265, lng: -123.0524 }
    ];

    for (let year = 1990; year <= 2024; year++) {
      const yearSightings = Math.floor(Math.random() * 30) + 10;
      
      for (let i = 0; i < yearSightings; i++) {
        const location = locations[Math.floor(Math.random() * locations.length)];
        const behavior = behaviors[Math.floor(Math.random() * behaviors.length)];
        const pod = pods[Math.floor(Math.random() * pods.length)];
        
        sightings.push({
          id: `${year}-${i}`,
          year: year,
          date: new Date(year, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28)),
          latitude: location.lat + (Math.random() - 0.5) * 0.02,
          longitude: location.lng + (Math.random() - 0.5) * 0.02,
          behavior: behavior,
          pod: pod,
          location: location.name,
          groupSize: Math.floor(Math.random() * 20) + 1,
          confidence: Math.random() * 0.3 + 0.7
        });
      }
    }

    return sightings;
  }

  private generateMockHydrophones(): HydrophoneData[] {
    return [
      {
        id: 'orcasound_lab',
        name: 'Orcasound Lab',
        location: 'University of Washington',
        latitude: 47.6579,
        longitude: -122.3182,
        status: 'online',
        detecting: false,
        lastDetection: null,
        streamUrl: 'https://live.orcasound.net/orcasound-lab'
      },
      {
        id: 'bush_point',
        name: 'Bush Point',
        location: 'Whidbey Island',
        latitude: 47.9076,
        longitude: -122.6084,
        status: 'online',
        detecting: false,
        lastDetection: new Date(Date.now() - 1000 * 60 * 45),
        streamUrl: 'https://live.orcasound.net/bush-point'
      },
      {
        id: 'port_townsend',
        name: 'Port Townsend',
        location: 'Olympic Peninsula',
        latitude: 48.1173,
        longitude: -122.7859,
        status: 'online',
        detecting: true,
        lastDetection: new Date(Date.now() - 1000 * 60 * 2),
        streamUrl: 'https://live.orcasound.net/port-townsend'
      },
      {
        id: 'sunset_bay',
        name: 'Sunset Bay',
        location: 'San Juan Island',
        latitude: 48.4935,
        longitude: -123.1424,
        status: 'online',
        detecting: false,
        lastDetection: new Date(Date.now() - 1000 * 60 * 15),
        streamUrl: 'https://live.orcasound.net/sunset-bay'
      }
    ];
  }

  private generateMockPredictions(model: string, hours: number, threshold: number): MLPredictionData {
    const predictions = [];
    const centerLat = 48.5465;
    const centerLng = -123.0307;
    const gridSize = 0.01;

    for (let latOffset = -0.3; latOffset <= 0.3; latOffset += gridSize) {
      for (let lngOffset = -0.4; lngOffset <= 0.4; lngOffset += gridSize) {
        const lat = centerLat + latOffset;
        const lng = centerLng + lngOffset;
        
        const distance = Math.sqrt(latOffset * latOffset + lngOffset * lngOffset);
        let probability = 0.4 * Math.exp(-distance * 5);
        
        if (model === 'behavioral') {
          const feedingFactor = Math.exp(-((lat - 48.52) ** 2 + (lng + 123.15) ** 2) * 100) * 0.3;
          probability += feedingFactor;
        }
        
        probability += (Math.random() - 0.5) * 0.3;
        probability = Math.max(0, Math.min(1, probability));

        if (probability > threshold) {
          predictions.push({
            latitude: lat,
            longitude: lng,
            probability: probability,
            hour: 0
          });
        }
      }
    }

    return {
      model,
      predictions,
      metadata: {
        totalPredictions: predictions.length,
        averageProbability: predictions.reduce((sum, p) => sum + p.probability, 0) / predictions.length,
        maxProbability: Math.max(...predictions.map(p => p.probability))
      }
    };
  }
} 