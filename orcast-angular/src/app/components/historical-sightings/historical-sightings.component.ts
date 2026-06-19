import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GoogleMapsModule } from '@angular/google-maps';
import { Subject, takeUntil, combineLatest, map } from 'rxjs';

import { MapShellComponent } from '../shared/map-shell.component';
import { CollapsiblePanelComponent } from '../shared/collapsible-panel.component';
import { MapLegendComponent } from '../shared/map-legend.component';
import { BackendService } from '../../services/backend.service';
import { MapService } from '../../services/map.service';
import { StateService } from '../../services/state.service';
import { OrcaSighting, BehaviorType } from '../../models/orca-sighting.model';

interface HistoricalStats {
  totalSightings: number;
  yearSightings: number;
  topBehavior: string;
  topLocation: string;
}

@Component({
  selector: 'orcast-historical-sightings',
  standalone: true,
  imports: [CommonModule, FormsModule, GoogleMapsModule, MapShellComponent, CollapsiblePanelComponent, MapLegendComponent],
  template: `
    <orcast-map-shell currentPage="historical">
      <div map>
        <google-map
          #map
          height="100%"
          width="100%"
          [options]="mapOptions"
          (mapInitialized)="onMapInitialized($event)">
        </google-map>
      </div>

      <aside left class="map-panel map-panel--left historical-controls">
      <h3>Historical sightings</h3>
      <p class="lead">Cross-validated OBIS sightings on a map.</p>
      <p class="count">{{ totalSightings }} verified sightings (1990–2024)</p>
      
      <div class="timeline-control">
        <label>Time Period</label>
        <input 
          type="range" 
          min="1990" 
          max="2024" 
          [value]="selectedYear"
          (input)="updateYear($event)"
          class="timeline-slider">
        <div class="year-display">{{ selectedYear }}</div>
      </div>
      
      <orcast-collapsible-panel title="Behaviors" [open]="true">
        <div class="filter-checkbox" *ngFor="let behavior of behaviors">
          <input 
            type="checkbox" 
            [id]="behavior"
            [checked]="activeBehaviors.includes(behavior)"
            (change)="toggleBehavior(behavior)">
          <label [for]="behavior">{{ getBehaviorLabel(behavior) }}</label>
        </div>
      </orcast-collapsible-panel>
      
      <button 
        (click)="refreshData()" 
        class="refresh-btn"
        [disabled]="isLoading">
        {{ isLoading ? 'Loading…' : 'Refresh data' }}
      </button>

      <div class="inline-stats">
        <div class="stat-item"><span>Total</span><span>{{ stats.totalSightings }}</span></div>
        <div class="stat-item"><span>This year</span><span>{{ stats.yearSightings }}</span></div>
        <div class="stat-item"><span>Top behavior</span><span>{{ stats.topBehavior }}</span></div>
        <div class="stat-item"><span>Top location</span><span>{{ stats.topLocation }}</span></div>
      </div>
      </aside>

      <orcast-map-legend bottom-right
        [showHeat]="false"
        [showVisual]="true"
        [showAcoustic]="false"
        [showStation]="true">
      </orcast-map-legend>

      <aside left class="map-panel map-panel--left sighting-info" *ngIf="selectedSighting" (click)="closeSightingInfo()">
        <h4>Sighting details</h4>
        <p><strong>Date:</strong> {{ selectedSighting.date | date:'mediumDate' }}</p>
        <p><strong>Location:</strong> {{ selectedSighting.location }}</p>
        <p><strong>Behavior:</strong> {{ selectedSighting.behavior }}</p>
        <p><strong>Confidence:</strong> {{ (selectedSighting.confidence * 100) | number:'1.0-0' }}%</p>
      </aside>
    </orcast-map-shell>
  `,
  styles: [`
    :host {
      display: block;
    }

    .count {
      font-size: 0.85rem;
      color: #8ab4cc;
      margin: 0 0 12px;
    }

    .lead {
      font-size: 0.9rem;
      color: #a8cce0;
      margin: 0 0 8px;
    }
    
    .timeline-control {
      margin: 15px 0;
    }
    
    .timeline-slider {
      width: 100%;
      margin: 10px 0;
    }
    
    .year-display {
      text-align: center;
      font-size: 1.2rem;
      color: #4fc3f7;
      font-weight: bold;
    }
    
    .filter-checkbox {
      margin: 5px 0;
      display: flex;
      align-items: center;
    }
    
    .filter-checkbox input {
      margin-right: 8px;
    }

    .refresh-btn {
      width: 100%;
      padding: 10px;
      background: #4fc3f7;
      color: #001e3c;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      font-weight: bold;
    }

    .refresh-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    .inline-stats {
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid rgba(79, 195, 247, 0.2);
      display: grid;
      gap: 6px;
    }

    .stat-item {
      display: flex;
      justify-content: space-between;
      font-size: 0.82rem;
      color: #c5dff0;
    }

    .sighting-info {
      top: auto;
      bottom: 12px;
      max-width: 280px;
      cursor: pointer;
    }

    .sighting-info p {
      margin: 4px 0;
      font-size: 0.85rem;
    }
  `]
})
export class HistoricalSightingsComponent implements OnInit, OnDestroy {
  @ViewChild('map') mapElement!: ElementRef;

  private destroy$ = new Subject<void>();
  
  // Data
  allSightings: OrcaSighting[] = [];
  filteredSightings: OrcaSighting[] = [];
  selectedSighting: OrcaSighting | null = null;
  totalSightings = 0;
  
  // Filters
  selectedYear = 2024;
  behaviors: BehaviorType[] = ['feeding', 'traveling', 'socializing', 'resting', 'unknown'];
  activeBehaviors: BehaviorType[] = [...this.behaviors];

  // UI State
  isLoading = false;
  stats: HistoricalStats = {
    totalSightings: 0,
    yearSightings: 0,
    topBehavior: '-',
    topLocation: '-'
  };

  // Map
  mapOptions: google.maps.MapOptions = {
    zoom: 11,
    center: { lat: 48.5465, lng: -123.0307 },
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
  };

  constructor(
    private backendService: BackendService,
    private mapService: MapService,
    private stateService: StateService
  ) {}

  ngOnInit(): void {
    this.stateService.updateCurrentView('historical');
    this.loadHistoricalData();
    this.setupStateSubscriptions();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onMapInitialized(map: google.maps.Map): void {
    this.mapService.registerMap(map);
    this.updateMapMarkers();
    this.loadHydrophones();
  }

  private loadHydrophones(): void {
    this.backendService.getHydrophoneData()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (stations) => this.mapService.addHydrophones(stations),
        error: () => this.stateService.addError('Failed to load listening stations')
      });
  }

  private setupStateSubscriptions(): void {
    // Subscribe to state changes
    this.stateService.mapFilters$
      .pipe(takeUntil(this.destroy$))
      .subscribe(filters => {
        this.selectedYear = filters.yearRange.max;
        this.activeBehaviors = [...filters.behaviors];
        this.filterAndUpdateSightings();
      });
  }

  loadHistoricalData(): void {
    this.isLoading = true;
    this.backendService.getHistoricalSightings()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (sightings) => {
          this.allSightings = sightings;
          this.totalSightings = sightings.length;
          this.filterAndUpdateSightings();
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error loading historical data:', error);
          this.stateService.addError('Failed to load historical sightings data');
          this.isLoading = false;
        }
      });
  }

  updateYear(event: Event): void {
    const target = event.target as HTMLInputElement;
    this.selectedYear = parseInt(target.value);
    this.stateService.updateMaxYear(this.selectedYear);
    this.filterAndUpdateSightings();
  }

  toggleBehavior(behavior: BehaviorType): void {
    this.stateService.toggleBehavior(behavior);
  }

  refreshData(): void {
    this.loadHistoricalData();
  }

  closeSightingInfo(): void {
    this.selectedSighting = null;
  }

  private filterAndUpdateSightings(): void {
    const filters = {
      maxYear: this.selectedYear,
      minYear: this.selectedYear - 5, // Show last 5 years
      behaviors: this.activeBehaviors
    };

    this.filteredSightings = this.allSightings.filter(sighting => {
      // Year filter
      if (sighting.year > filters.maxYear) return false;
      if (sighting.year < filters.minYear) return false;

      // Behavior filter
      if (!filters.behaviors.includes(sighting.behavior)) return false;

      return true;
    });

    this.updateMapMarkers();
    this.updateStatistics();
  }

  private updateMapMarkers(): void {
    this.mapService.addHistoricalSightings(this.filteredSightings, {
      maxYear: this.selectedYear,
      behaviors: this.activeBehaviors
    });
  }

  private updateStatistics(): void {
    const filteredByYear = this.allSightings.filter(s => s.year <= this.selectedYear);
    const currentYearSightings = this.allSightings.filter(s => s.year === this.selectedYear);

    // Calculate behavior counts
    const behaviorCounts: Record<string, number> = {};
    const locationCounts: Record<string, number> = {};

    filteredByYear.forEach(sighting => {
      behaviorCounts[sighting.behavior] = (behaviorCounts[sighting.behavior] || 0) + 1;
      locationCounts[sighting.location] = (locationCounts[sighting.location] || 0) + 1;
    });

    // Find top values
    const topBehavior = Object.keys(behaviorCounts).reduce((a, b) =>
      behaviorCounts[a] > behaviorCounts[b] ? a : b, '-');
    const topLocation = Object.keys(locationCounts).reduce((a, b) =>
      locationCounts[a] > locationCounts[b] ? a : b, '-');

    this.stats = {
      totalSightings: filteredByYear.length,
      yearSightings: currentYearSightings.length,
      topBehavior: topBehavior,
      topLocation: topLocation
    };
  }

  getBehaviorLabel(behavior: BehaviorType): string {
    return behavior.charAt(0).toUpperCase() + behavior.slice(1);
  }
} 