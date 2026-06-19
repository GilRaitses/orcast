import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GoogleMapsModule } from '@angular/google-maps';
import { Subject, takeUntil } from 'rxjs';

import { MapShellComponent } from '../shared/map-shell.component';
import { MapLegendComponent } from '../shared/map-legend.component';
import { BackendService } from '../../services/backend.service';
import { MapService } from '../../services/map.service';
import { StateService } from '../../services/state.service';
import { MLPredictionData, MapEvent } from '../../models/orca-sighting.model';

@Component({
  selector: 'orcast-ml-predictions',
  standalone: true,
  imports: [CommonModule, FormsModule, GoogleMapsModule, MapShellComponent, MapLegendComponent],
  template: `
    <orcast-map-shell currentPage="ml-predictions">
      <div map>
        <google-map
          #map
          height="100%"
          width="100%"
          [options]="mapOptions"
          (mapInitialized)="onMapInitialized($event)">
        </google-map>
      </div>

      <aside left class="map-panel map-panel--left grid-controls">
      <h3>Probability map</h3>
      <p class="lead">Map of sighting probability for a region you choose. Same scoring as the report page.</p>

      <div class="prediction-params">
        <label>Hours: <span>{{ predictionHours }}</span></label>
        <input
          type="range"
          min="1"
          max="72"
          [(ngModel)]="predictionHours"
          (input)="onParameterChange()"
          class="param-slider">

        <label>Radius (km): <span>{{ radiusKm }}</span></label>
        <input
          type="range"
          min="5"
          max="30"
          [(ngModel)]="radiusKm"
          (input)="onParameterChange()"
          class="param-slider">

        <label>Min probability: <span>{{ (probabilityThreshold * 100) | number:'1.0-0' }}%</span></label>
        <input
          type="range"
          min="0"
          max="90"
          [ngModel]="probabilityThreshold * 100"
          (ngModelChange)="probabilityThreshold = $event / 100; onParameterChange()"
          class="param-slider">
      </div>

      <button
        (click)="generateGrid()"
        class="generate-btn"
        [disabled]="isGenerating">
        {{ isGenerating ? 'Loading…' : 'Load probability map' }}
      </button>
      </aside>

      <aside right class="map-panel map-panel--right results-panel" *ngIf="predictionResults">
      <h4>Results</h4>
      <p *ngIf="predictionResults.metadata.totalPredictions === 0" class="empty-state">
        No grid points above the minimum probability. Try lowering the threshold.
      </p>
      <ng-container *ngIf="predictionResults.metadata.totalPredictions > 0">
        <p><strong>Grid points:</strong> {{ predictionResults.metadata.totalPredictions }}</p>
        <p><strong>Max probability:</strong> {{ (predictionResults.metadata.maxProbability * 100) | number:'1.1-1' }}%</p>
      </ng-container>
      </aside>

      <orcast-map-legend
        [showHeat]="true"
        [showVisual]="true"
        [showAcoustic]="true"
        [showStation]="false">
      </orcast-map-legend>
    </orcast-map-shell>
  `,
  styles: [`
    :host {
      display: block;
    }

    .lead {
      font-size: 0.9rem;
      color: #a8cce0;
      margin: 0 0 12px;
    }

    .prediction-params {
      margin: 12px 0;
      padding: 12px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 5px;
    }

    .prediction-params label {
      display: block;
      margin: 12px 0 4px;
      font-size: 0.9rem;
    }

    .param-slider {
      width: 100%;
      margin: 6px 0;
    }

    .generate-btn {
      width: 100%;
      padding: 12px;
      background: #4fc3f7;
      color: #001e3c;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      font-weight: bold;
    }

    .generate-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .results-panel p {
      margin: 4px 0;
      font-size: 0.85rem;
    }

    .empty-state {
      color: #a8cce0;
      font-size: 0.85rem;
    }
  `]
})
export class MLPredictionsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  predictionHours = 24;
  radiusKm = 12;
  probabilityThreshold = 0.05;
  isGenerating = false;
  predictionResults: MLPredictionData | null = null;

  mapOptions: google.maps.MapOptions = {
    zoom: 11,
    center: { lat: 48.5465, lng: -123.0307 },
    mapTypeId: google.maps.MapTypeId.HYBRID
  };

  constructor(
    private backendService: BackendService,
    private mapService: MapService,
    private stateService: StateService
  ) {}

  ngOnInit(): void {
    this.stateService.updateCurrentView('ml-predictions');
    this.generateGrid();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onMapInitialized(map: google.maps.Map): void {
    this.mapService.registerMap(map);
    if (this.predictionResults?.predictions?.length) {
      this.updateMapWithPredictions(this.predictionResults);
    }
    this.loadReferenceSightings();
  }

  /**
   * Overlay real visual/acoustic detections as reference against the modeled
   * probability surface. Reference-only, so failures must never block the grid.
   */
  private loadReferenceSightings(): void {
    this.backendService.getMapEvents()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (events: MapEvent[]) => this.mapService.addTypedSightings(events),
        error: (error) => console.warn('Reference sightings failed to load:', error)
      });
  }

  onParameterChange(): void {
    setTimeout(() => this.generateGrid(), 300);
  }

  generateGrid(): void {
    this.isGenerating = true;
    this.predictionResults = null;

    this.backendService.generateMLPredictions(
      this.predictionHours,
      this.probabilityThreshold,
      this.radiusKm
    )
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.predictionResults = data;
          // Reset the button before rendering so a render error can never
          // leave it stuck on "Loading…".
          this.isGenerating = false;
          try {
            this.updateMapWithPredictions(data);
          } catch (renderError) {
            console.error('Error rendering probability map:', renderError);
            this.stateService.addError('Failed to render probability map');
          }
        },
        error: (error) => {
          console.error('Error loading probability map:', error);
          this.stateService.addError('Failed to load probability map');
          this.isGenerating = false;
        }
      });
  }

  private updateMapWithPredictions(data: MLPredictionData): void {
    if (data.predictions?.length) {
      this.mapService.addMLPredictionHeatMap(data.predictions, data.model);
    }
  }
}
