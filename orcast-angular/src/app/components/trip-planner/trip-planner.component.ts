import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { GoogleMapsModule } from '@angular/google-maps';

import { AppShellComponent } from '../shared/app-shell.component';
import { BackendService } from '../../services/backend.service';
import { MapService } from '../../services/map.service';
import { ProbabilityHotspot } from '../../models/orca-sighting.model';

interface IslandOption {
  id: string;
  name: string;
  lat: number;
  lng: number;
}

@Component({
  selector: 'orcast-trip-planner',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, GoogleMapsModule, AppShellComponent],
  template: `
    <orcast-app-shell currentPage="plan">
      <main class="plan-page">
        <div class="plan-split">
          <section class="plan-list">
            <header class="plan-intro">
              <h1>Plan a trip</h1>
              <p class="lead">
                Pick an island and see the top sighting spots nearby, ranked from recent sightings.
              </p>
            </header>

            <div class="controls card">
              <fieldset class="island-picker">
                <legend>Island</legend>
                <label *ngFor="let island of islands" class="island-option">
                  <input
                    type="radio"
                    name="island"
                    [value]="island.id"
                    [(ngModel)]="selectedIslandId">
                  {{ island.name }}
                </label>
              </fieldset>

              <label class="date-field">
                Trip date (optional)
                <input type="date" [(ngModel)]="tripDate">
              </label>

              <div class="actions">
                <button
                  class="btn btn--primary"
                  (click)="findTopSpots()"
                  [disabled]="isLoading"
                  data-cy="find-top-spots">
                  {{ isLoading ? 'Finding spots...' : 'Find top spots' }}
                </button>

                <a class="btn btn--ghost" routerLink="/contribute">
                  Saw orcas? Add a sighting
                </a>
              </div>

              <div *ngIf="errorMessage" class="error">{{ errorMessage }}</div>
            </div>

            <div class="results" *ngIf="hasSearched && !isLoading">
              <div *ngIf="topSpots.length; else emptyState">
                <article
                  class="spot-card card card--hover"
                  *ngFor="let spot of topSpots"
                  [class.selected]="spot === selectedHotspot"
                  (click)="selectSpot(spot)">
                  <h3>{{ spot.name }}</h3>
                  <div class="score-row">
                    <span>Chance of sightings</span>
                    <strong>{{ spot.probability | percent:'1.0-0' }}</strong>
                  </div>
                  <p class="spot-detail">
                    {{ spot.detection_count }} recent sighting(s) near here
                  </p>
                </article>

                <p class="caption">
                  Based on recent sightings, same scoring as the report page.
                </p>
              </div>

              <ng-template #emptyState>
                <p class="empty">
                  No recent hotspots near {{ selectedIslandName }}. Try another island or
                  <a routerLink="/reports">check the full report</a>.
                </p>
              </ng-template>
            </div>
          </section>

          <section class="plan-map">
            <google-map
              height="100%"
              width="100%"
              [options]="mapOptions"
              (mapInitialized)="onMapInitialized($event)">
            </google-map>
          </section>
        </div>
      </main>
    </orcast-app-shell>
  `,
  styles: [`
    :host { display: block; }

    .plan-page {
      padding: 0;
    }

    .plan-split {
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 0;
      min-height: calc(100vh - var(--nav-h));
    }

    .plan-list {
      overflow-y: auto;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .plan-map {
      position: relative;
      min-height: 420px;
      background: var(--bg-panel);
    }

    .plan-intro h1 {
      margin: 0 0 0.25rem;
      font-size: 1.75rem;
    }

    .plan-intro .lead {
      margin: 0;
      color: var(--text-muted);
    }

    .card {
      padding: 16px;
    }

    .island-picker {
      border: none;
      padding: 0;
      margin: 0 0 16px;
    }

    .island-picker legend {
      padding: 0;
      margin-bottom: 8px;
      color: var(--text-muted);
      font-size: 0.9rem;
    }

    .island-option {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 4px 0;
      cursor: pointer;
    }

    .date-field {
      display: block;
      margin-bottom: 16px;
      color: var(--text-muted);
      font-size: 0.9rem;
    }

    .date-field input {
      display: block;
      margin-top: 6px;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .results {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .spot-card {
      cursor: pointer;
      padding: 14px 16px;
      margin-bottom: 12px;
    }

    .spot-card.selected {
      border-color: var(--accent);
      box-shadow: 0 0 0 1px var(--accent);
    }

    .spot-card h3 {
      margin: 0 0 6px;
      font-size: 1.1rem;
    }

    .score-row {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      margin: 4px 0;
    }

    .score-row strong {
      color: var(--accent);
      font-size: 1.15rem;
    }

    .spot-detail {
      color: var(--text-muted);
      font-size: 0.9rem;
      margin: 6px 0 0;
    }

    .caption {
      color: var(--text-faint);
      font-size: 0.85rem;
      margin: 4px 0 0;
    }

    .empty {
      color: var(--text-muted);
    }

    .empty a,
    .caption a {
      color: var(--accent);
    }

    .error {
      color: #ffb3b3;
      margin-top: 12px;
    }

    @media (max-width: 768px) {
      .plan-split {
        grid-template-columns: 1fr;
        grid-template-rows: minmax(420px, 50vh) auto;
        min-height: auto;
      }

      .plan-map {
        grid-row: 1;
      }

      .plan-list {
        grid-row: 2;
        overflow-y: visible;
      }
    }
  `]
})
export class TripPlannerComponent {
  readonly islands: IslandOption[] = [
    { id: 'san-juan', name: 'San Juan', lat: 48.53, lng: -123.08 },
    { id: 'orcas', name: 'Orcas', lat: 48.65, lng: -122.95 },
    { id: 'lopez', name: 'Lopez', lat: 48.47, lng: -122.88 },
    { id: 'shaw', name: 'Shaw', lat: 48.58, lng: -122.93 }
  ];

  private readonly maxDistanceKm = 12;

  selectedIslandId = this.islands[0].id;
  tripDate = '';
  topSpots: ProbabilityHotspot[] = [];
  selectedHotspot: ProbabilityHotspot | null = null;
  isLoading = false;
  hasSearched = false;
  errorMessage = '';

  mapOptions: google.maps.MapOptions = {
    zoom: 11,
    center: { lat: 48.5465, lng: -123.0307 },
    mapTypeId: google.maps.MapTypeId.HYBRID,
    styles: [
      { featureType: 'poi', stylers: [{ visibility: 'off' }] },
      { featureType: 'transit', stylers: [{ visibility: 'off' }] }
    ]
  };

  private mapReady = false;

  constructor(
    private backendService: BackendService,
    private mapService: MapService
  ) {}

  get selectedIslandName(): string {
    return this.selectedIsland.name;
  }

  private get selectedIsland(): IslandOption {
    return this.islands.find(island => island.id === this.selectedIslandId) || this.islands[0];
  }

  onMapInitialized(map: google.maps.Map): void {
    this.mapService.registerMap(map);
    this.mapReady = true;
    if (this.topSpots.length) {
      this.plotSpots(this.topSpots);
    }
  }

  findTopSpots(): void {
    const island = this.selectedIsland;
    this.isLoading = true;
    this.errorMessage = '';
    this.selectedHotspot = null;

    this.backendService.generateProbabilityReport(0).subscribe({
      next: report => {
        this.topSpots = this.rankNearbyHotspots(report.hotspots || [], island);
        this.hasSearched = true;
        this.isLoading = false;
        if (this.mapReady) {
          this.plotSpots(this.topSpots);
        }
      },
      error: error => {
        this.errorMessage = error.message || 'Failed to find top spots';
        this.topSpots = [];
        this.hasSearched = true;
        this.isLoading = false;
      }
    });
  }

  selectSpot(spot: ProbabilityHotspot): void {
    this.selectedHotspot = spot;
    this.mapService.centerMap(spot.center_latitude, spot.center_longitude, 13);
  }

  private rankNearbyHotspots(hotspots: ProbabilityHotspot[], island: IslandOption): ProbabilityHotspot[] {
    return hotspots
      .filter(hotspot =>
        this.distanceKm(island.lat, island.lng, hotspot.center_latitude, hotspot.center_longitude)
          <= this.maxDistanceKm
      )
      .sort((a, b) => b.probability - a.probability)
      .slice(0, 3);
  }

  private plotSpots(spots: ProbabilityHotspot[]): void {
    this.mapService.addReportHotspots(spots, hotspot => {
      this.selectedHotspot = hotspot;
    });

    const coords = spots.map(spot => ({
      lat: spot.center_latitude,
      lng: spot.center_longitude
    }));
    if (coords.length) {
      this.mapService.fitBounds(coords);
    } else {
      this.mapService.centerMap(this.selectedIsland.lat, this.selectedIsland.lng, 11);
    }
  }

  /** Equirectangular approximation; accurate enough at this latitude and short range. */
  private distanceKm(lat1: number, lng1: number, lat2: number, lng2: number): number {
    const earthRadiusKm = 6371;
    const toRad = (deg: number) => (deg * Math.PI) / 180;
    const meanLatRad = toRad((lat1 + lat2) / 2);
    const x = toRad(lng2 - lng1) * Math.cos(meanLatRad);
    const y = toRad(lat2 - lat1);
    return Math.sqrt(x * x + y * y) * earthRadiusKm;
  }
}
