import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GoogleMapsModule } from '@angular/google-maps';
import { Subject, takeUntil, combineLatest, map } from 'rxjs';

import { NavHeaderComponent } from '../shared/nav-header.component';
import { BackendService } from '../../services/backend.service';
import { MapService } from '../../services/map.service';
import { StateService } from '../../services/state.service';
import { OrcaSighting, BehaviorType, PodType } from '../../models/orca-sighting.model';

interface HistoricalStats {
  totalSightings: number;
  yearSightings: number;
  activePod: string;
  topBehavior: string;
  topLocation: string;
}

@Component({
  selector: 'orcast-historical-sightings',
  standalone: true,
  imports: [CommonModule, FormsModule, GoogleMapsModule, NavHeaderComponent],
  template: `
    <orcast-nav-header currentPage="historical"></orcast-nav-header>

    <!-- Historical Controls Panel -->
    <div class="historical-controls">
      <h3>📊 Historical Sightings</h3>
      <p>{{ totalSightings }} verified orca sightings (1990-2024)</p>
      
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
      
      <div class="filter-group">
        <h4>Pod Types</h4>
        <div class="filter-checkbox" *ngFor="let podType of podTypes">
          <input 
            type="checkbox" 
            [id]="podType"
            [checked]="activePodTypes.includes(podType)"
            (change)="togglePodType(podType)">
          <label [for]="podType">{{ getPodTypeLabel(podType) }}</label>
        </div>
      </div>
      
      <div class="filter-group">
        <h4>Behaviors</h4>
        <div class="filter-checkbox" *ngFor="let behavior of behaviors">
          <input 
            type="checkbox" 
            [id]="behavior"
            [checked]="activeBehaviors.includes(behavior)"
            (change)="toggleBehavior(behavior)">
          <label [for]="behavior">{{ getBehaviorLabel(behavior) }}</label>
        </div>
      </div>
      
      <button 
        (click)="refreshData()" 
        class="refresh-btn"
        [disabled]="isLoading">
        {{ isLoading ? '🔄 Loading...' : '🔄 Refresh Data' }}
      </button>
    </div>

    <!-- Statistics Panel -->
    <div class="stats-panel">
      <h4>📈 Current Statistics</h4>
      <div class="stat-item">
        <span>Total Sightings:</span>
        <span>{{ stats.totalSightings }}</span>
      </div>
      <div class="stat-item">
        <span>This Year:</span>
        <span>{{ stats.yearSightings }}</span>
      </div>
      <div class="stat-item">
        <span>Most Active Pod:</span>
        <span>{{ stats.activePod }}</span>
      </div>
      <div class="stat-item">
        <span>Top Behavior:</span>
        <span>{{ stats.topBehavior }}</span>
      </div>
      <div class="stat-item">
        <span>Best Location:</span>
        <span>{{ stats.topLocation }}</span>
      </div>
    </div>

    <!-- Map Container -->
    <google-map 
      #map
      [options]="mapOptions"
      (mapInitialized)="onMapInitialized($event)">
    </google-map>

    <!-- Legend -->
    <div class="legend">
      <h4>🗺️ Legend</h4>
      <div class="legend-item" *ngFor="let item of legendItems">
        <div class="legend-color" [style.background]="item.color"></div>
        <span>{{ item.label }}</span>
      </div>
    </div>

    <!-- Sighting Information Panel -->
    <div class="sighting-info" *ngIf="selectedSighting" (click)="closeSightingInfo()">
      <h4>📍 Sighting Details</h4>
      <div>
        <p><strong>Date:</strong> {{ selectedSighting.date | date:'fullDate' }}</p>
        <p><strong>Location:</strong> {{ selectedSighting.location }}</p>
        <p><strong>Pod:</strong> {{ selectedSighting.pod }}</p>
        <p><strong>Behavior:</strong> {{ selectedSighting.behavior }}</p>
        <p><strong>Group Size:</strong> {{ selectedSighting.groupSize }} individuals</p>
        <p><strong>Confidence:</strong> {{ (selectedSighting.confidence * 100) | number:'1.0-0' }}%</p>
        <p><strong>Coordinates:</strong> {{ selectedSighting.latitude | number:'1.4-4' }}, {{ selectedSighting.longitude | number:'1.4-4' }}</p>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      height: 100vh;
      width: 100%;
      position: relative;
    }

    google-map {
      height: 100vh;
      width: 100%;
    }

    .historical-controls {
      position: absolute;
      top: 20px;
      left: 20px;
      background: rgba(0, 30, 60, 0.95);
      padding: 20px;
      border-radius: 10px;
      border: 1px solid #4fc3f7;
      color: white;
      z-index: 1000;
      width: 300px;
      max-height: 80vh;
      overflow-y: auto;
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
    
    .filter-group {
      margin: 15px 0;
      padding: 10px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 5px;
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
    
    .stats-panel {
      position: absolute;
      top: 20px;
      right: 20px;
      background: rgba(0, 30, 60, 0.95);
      padding: 15px;
      border-radius: 8px;
      border: 1px solid #4fc3f7;
      color: white;
      z-index: 1000;
      width: 250px;
    }
    
    .stat-item {
      display: flex;
      justify-content: space-between;
      margin: 8px 0;
      padding: 5px 0;
      border-bottom: 1px solid rgba(79, 195, 247, 0.2);
    }
    
    .legend {
      position: absolute;
      bottom: 20px;
      right: 20px;
      background: rgba(0, 30, 60, 0.95);
      padding: 15px;
      border-radius: 8px;
      border: 1px solid #4fc3f7;
      color: white;
      z-index: 1000;
    }
    
    .legend-item {
      display: flex;
      align-items: center;
      margin: 5px 0;
    }
    
    .legend-color {
      width: 15px;
      height: 15px;
      border-radius: 50%;
      margin-right: 10px;
    }
    
    .sighting-info {
      position: absolute;
      bottom: 20px;
      left: 20px;
      background: rgba(0, 30, 60, 0.95);
      padding: 15px;
      border-radius: 8px;
      border: 1px solid #4fc3f7;
      color: white;
      z-index: 1000;
      max-width: 400px;
      cursor: pointer;
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
  podTypes: PodType[] = ['resident', 'transient', 'offshore'];
  activeBehaviors: BehaviorType[] = [...this.behaviors];
  activePodTypes: PodType[] = [...this.podTypes];

  // UI State
  isLoading = false;
  stats: HistoricalStats = {
    totalSightings: 0,
    yearSightings: 0,
    activePod: '-',
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

  legendItems = [
    { color: '#ff4444', label: 'Feeding Behavior' },
    { color: '#44ff44', label: 'Traveling' },
    { color: '#4444ff', label: 'Socializing' },
    { color: '#ffff44', label: 'Resting' },
    { color: '#ff44ff', label: 'Unknown' }
  ];

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
    this.mapService.initializeMap(map.getDiv()!);
    this.updateMapMarkers();
  }

  private setupStateSubscriptions(): void {
    // Subscribe to state changes
    this.stateService.mapFilters$
      .pipe(takeUntil(this.destroy$))
      .subscribe(filters => {
        this.selectedYear = filters.yearRange.max;
        this.activeBehaviors = [...filters.behaviors];
        this.activePodTypes = [...filters.podTypes];
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

  togglePodType(podType: PodType): void {
    this.stateService.togglePodType(podType);
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
      behaviors: this.activeBehaviors,
      podTypes: this.activePodTypes
    };

    this.filteredSightings = this.allSightings.filter(sighting => {
      // Year filter
      if (sighting.year > filters.maxYear) return false;
      if (sighting.year < filters.minYear) return false;

      // Behavior filter
      if (!filters.behaviors.includes(sighting.behavior)) return false;

      // Pod type filter
      const podType = this.getPodTypeFromName(sighting.pod);
      if (!filters.podTypes.includes(podType)) return false;

      return true;
    });

    this.updateMapMarkers();
    this.updateStatistics();
  }

  private updateMapMarkers(): void {
    this.mapService.addHistoricalSightings(this.filteredSightings, {
      maxYear: this.selectedYear,
      behaviors: this.activeBehaviors,
      podTypes: this.activePodTypes
    });
  }

  private updateStatistics(): void {
    const filteredByYear = this.allSightings.filter(s => s.year <= this.selectedYear);
    const currentYearSightings = this.allSightings.filter(s => s.year === this.selectedYear);

    // Calculate behavior counts
    const behaviorCounts: Record<string, number> = {};
    const podCounts: Record<string, number> = {};
    const locationCounts: Record<string, number> = {};

    filteredByYear.forEach(sighting => {
      behaviorCounts[sighting.behavior] = (behaviorCounts[sighting.behavior] || 0) + 1;
      podCounts[sighting.pod] = (podCounts[sighting.pod] || 0) + 1;
      locationCounts[sighting.location] = (locationCounts[sighting.location] || 0) + 1;
    });

    // Find top values
    const topBehavior = Object.keys(behaviorCounts).reduce((a, b) =>
      behaviorCounts[a] > behaviorCounts[b] ? a : b, '-');
    const topPod = Object.keys(podCounts).reduce((a, b) =>
      podCounts[a] > podCounts[b] ? a : b, '-');
    const topLocation = Object.keys(locationCounts).reduce((a, b) =>
      locationCounts[a] > locationCounts[b] ? a : b, '-');

    this.stats = {
      totalSightings: filteredByYear.length,
      yearSightings: currentYearSightings.length,
      activePod: topPod,
      topBehavior: topBehavior,
      topLocation: topLocation
    };
  }

  private getPodTypeFromName(podName: string): PodType {
    if (podName.includes('J-') || podName.includes('K-') || podName.includes('L-')) {
      return 'resident';
    } else if (podName.includes('T-')) {
      return 'transient';
    } else {
      return 'offshore';
    }
  }

  getBehaviorLabel(behavior: BehaviorType): string {
    return behavior.charAt(0).toUpperCase() + behavior.slice(1);
  }

  getPodTypeLabel(podType: PodType): string {
    const labels: Record<PodType, string> = {
      resident: 'Resident Pods (J, K, L)',
      transient: 'Transient (T-pods)',
      offshore: 'Offshore Pods'
    };
    return labels[podType];
  }
} 