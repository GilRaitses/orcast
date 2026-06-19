import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { GoogleMapsModule } from '@angular/google-maps';
import { Subject, forkJoin, takeUntil } from 'rxjs';

import { MapShellComponent } from '../shared/map-shell.component';
import { CollapsiblePanelComponent } from '../shared/collapsible-panel.component';
import { MapLegendComponent } from '../shared/map-legend.component';
import { BackendService } from '../../services/backend.service';
import { MapService } from '../../services/map.service';
import { StateService } from '../../services/state.service';
import { HydrophoneData } from '../../models/orca-sighting.model';

interface SightingEvent {
  id: string;
  timestamp: Date;
  source: string;
  locationName: string;
  confidence: number;
  latitude?: number;
  longitude?: number;
}

@Component({
  selector: 'orcast-realtime-detection',
  standalone: true,
  imports: [CommonModule, GoogleMapsModule, MapShellComponent, CollapsiblePanelComponent, MapLegendComponent],
  template: `
    <orcast-map-shell currentPage="realtime">
      <div map>
        <google-map
          #map
          height="100%"
          width="100%"
          [options]="mapOptions"
          (mapInitialized)="onMapInitialized($event)">
        </google-map>
      </div>

      <aside left class="map-panel map-panel--left sightings-panel">
      <h3>Recent sightings</h3>
      <p class="lead">Sightings from our database on a map.</p>

      <button
        (click)="refresh()"
        class="refresh-btn"
        [disabled]="isLoading">
        {{ isLoading ? 'Loading…' : 'Refresh' }}
      </button>

      <div class="sighting-list" *ngIf="sightings.length > 0; else noSightings">
        <div
          *ngFor="let sighting of sightings.slice(0, 15)"
          class="sighting-item"
          (click)="focusSighting(sighting)">
          <div class="sighting-time">{{ sighting.timestamp | date:'medium' }}</div>
          <div class="sighting-source">{{ sighting.locationName || sighting.source }}</div>
          <div class="sighting-confidence">{{ (sighting.confidence * 100) | number:'1.0-0' }}% confidence</div>
        </div>
      </div>

      <ng-template #noSightings>
        <p class="empty">No sightings loaded.</p>
      </ng-template>
      </aside>

      <aside right class="map-panel map-panel--right stations-panel">
      <orcast-collapsible-panel title="Stations" [open]="false">
        <p class="note">Orcasound hydrophones (metadata only).</p>
        <ul class="station-list">
          <li *ngFor="let station of hydrophones" (click)="focusStation(station)">
            {{ station.name }}
          </li>
        </ul>
        <div class="crowd-tag">
          <button type="button" class="crowd-tag-btn" [disabled]="true">
            Tag this clip (coming August)
          </button>
          <p class="crowd-tag-note">Crowd sound tagging arrives with the August pilot.</p>
        </div>
      </orcast-collapsible-panel>
      </aside>

      <orcast-map-legend
        [showHeat]="true"
        [showVisual]="true"
        [showAcoustic]="true"
        [showStation]="true">
      </orcast-map-legend>
    </orcast-map-shell>
  `,
  styles: [`
    :host {
      display: block;
    }

    .lead, .note {
      font-size: 0.85rem;
      color: #a8cce0;
      margin: 0 0 10px;
    }

    .refresh-btn {
      width: 100%;
      padding: 8px;
      background: #4fc3f7;
      color: #001e3c;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      font-weight: bold;
      margin-bottom: 10px;
    }

    .refresh-btn:disabled {
      opacity: 0.6;
    }

    .sighting-list {
      max-height: 360px;
      overflow-y: auto;
    }

    .sighting-item {
      padding: 10px;
      margin: 6px 0;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 5px;
      cursor: pointer;
      font-size: 0.85rem;
    }

    .sighting-time {
      color: #4fc3f7;
      font-weight: 600;
    }

    .sighting-confidence {
      float: right;
      color: #8ab4cc;
    }

    .empty {
      text-align: center;
      color: #8ab4cc;
      padding: 16px 0;
    }

    .stations-panel h4 {
      margin: 0 0 6px;
    }

    .station-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }

    .station-list li {
      padding: 6px 0;
      border-bottom: 1px solid rgba(79, 195, 247, 0.15);
      cursor: pointer;
      font-size: 0.82rem;
    }

    .station-list li:hover {
      color: #4fc3f7;
    }

    .crowd-tag {
      margin-top: 12px;
      padding-top: 10px;
      border-top: 1px solid rgba(79, 195, 247, 0.15);
    }

    .crowd-tag-btn {
      width: 100%;
      padding: 8px;
      background: rgba(255, 255, 255, 0.06);
      color: #8ab4cc;
      border: 1px dashed rgba(138, 180, 204, 0.4);
      border-radius: 5px;
      font-size: 0.82rem;
      cursor: not-allowed;
      opacity: 0.7;
    }

    .crowd-tag-note {
      margin: 6px 0 0;
      font-size: 0.75rem;
      color: #8ab4cc;
    }
  `]
})
export class RealtimeDetectionComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  hydrophones: HydrophoneData[] = [];
  sightings: SightingEvent[] = [];
  isLoading = false;

  mapOptions: google.maps.MapOptions = {
    zoom: 10,
    center: { lat: 48.5465, lng: -123.0307 },
    mapTypeId: google.maps.MapTypeId.HYBRID
  };

  constructor(
    private backendService: BackendService,
    private mapService: MapService,
    private stateService: StateService
  ) {}

  ngOnInit(): void {
    this.stateService.updateCurrentView('realtime');
    this.loadHydrophones();
    this.refresh();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onMapInitialized(map: google.maps.Map): void {
    this.mapService.registerMap(map);
    this.loadInstrumentation();
  }

  refresh(): void {
    this.isLoading = true;
    this.backendService.getRecentDetections()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (detections) => {
          this.sightings = detections.map(d => ({
            id: String(d.id),
            timestamp: d.timestamp,
            source: d.hydrophoneId,
            locationName: d.locationName || d.hydrophone,
            confidence: d.confidence,
            latitude: d.latitude,
            longitude: d.longitude
          }));
          this.isLoading = false;
        },
        error: () => {
          this.stateService.addError('Failed to load sightings');
          this.isLoading = false;
        }
      });
  }

  /**
   * Render the real instrumented detections onto the map: a detection-density
   * heat field (confidence x recency) plus modality-aware markers (visual
   * sighting vs acoustic detection), listening stations, and sighting-to-station
   * connectors. Pulls events + stations together so the layers land in one pass.
   */
  private loadInstrumentation(): void {
    forkJoin({
      events: this.backendService.getMapEvents(),
      stations: this.backendService.getHydrophoneData()
    })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: ({ events, stations }) => {
          const heatPoints = events.map(e => ({
            lat: e.latitude,
            lng: e.longitude,
            weight: Math.max(0.01, e.confidence * this.recencyFactor(e.timestamp))
          }));
          if (heatPoints.length) {
            this.mapService.addDetectionHeat(heatPoints);
          }
          this.mapService.addTypedSightings(events);
          this.mapService.addHydrophones(stations);
          this.mapService.addFeedConnectors(events, stations);
        },
        error: () => {
          this.stateService.addError('Failed to load detection layers');
        }
      });
  }

  /** Recent, confident detections weigh more; old ones fade but never vanish. */
  private recencyFactor(timestamp: Date): number {
    const ageDays = (Date.now() - timestamp.getTime()) / 86_400_000;
    const factor = Math.exp(-ageDays / 540);
    return Math.min(1, Math.max(0.15, factor));
  }

  loadHydrophones(): void {
    this.backendService.getHydrophoneData()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (stations) => {
          this.hydrophones = stations.map(s => ({ ...s, detecting: false }));
          this.mapService.addHydrophones(this.hydrophones);
        },
        error: () => {
          this.stateService.addError('Failed to load station list');
        }
      });
  }

  focusStation(station: HydrophoneData): void {
    this.mapService.centerMap(station.latitude, station.longitude, 12);
  }

  focusSighting(sighting: SightingEvent): void {
    if (sighting.latitude != null && sighting.longitude != null) {
      this.mapService.centerMap(sighting.latitude, sighting.longitude, 13);
    }
  }
}
