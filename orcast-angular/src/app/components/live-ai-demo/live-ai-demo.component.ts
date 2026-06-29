import { Component, OnInit, OnDestroy, AfterViewInit, ViewChild, ElementRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription, firstValueFrom } from 'rxjs';
import { RouterModule } from '@angular/router';
import { BackendService } from '../../services/backend.service';

@Component({
  selector: 'orcast-live-ai-demo',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="live-demo-container">
      <div class="header-bar">
        <a routerLink="/" class="home-link">← Home</a>
        <h1>Map demo</h1>
        <span class="badge">Demo only</span>
        <p class="subtitle">Uses the same API as Reports. Scripted UI — not a chatbot.</p>
        <div class="demo-controls">
          <button (click)="startDemo()" [disabled]="isRunning" class="start-btn">Start</button>
          <button (click)="stopDemo()" [disabled]="!isRunning" class="stop-btn">Stop</button>
          <span class="status" [class.running]="isRunning">
            {{ isRunning ? 'Loading data…' : 'Ready' }}
          </span>
        </div>
      </div>

      <div class="main-interface">
        <div class="map-centerpiece">
          <div class="map-header">
            <h3>San Juan Islands</h3>
            <span class="map-mode">Probability map</span>
            </div>
          <div class="map-container" #mapContainer>
            <div id="live-map"></div>
                </div>
              </div>
              
        <div class="data-panel">
          <h3>Live API data</h3>
          <div class="stat" *ngIf="sightingsLoaded >= 0">
            <span class="label">Sightings on map</span>
            <span class="value">{{ sightingsLoaded }}</span>
              </div>
          <div class="stat" *ngIf="gridPoints >= 0">
            <span class="label">Grid points</span>
            <span class="value">{{ gridPoints }}</span>
                </div>
          <div class="stat" *ngIf="maxProbability >= 0">
            <span class="label">Max probability</span>
            <span class="value">{{ (maxProbability * 100) | number:'1.1-1' }}%</span>
              </div>
          <div class="stat" *ngIf="modelVersion">
            <span class="label">Model</span>
            <span class="value mono">{{ modelVersion }}</span>
          </div>
          
          <div class="env-block" *ngIf="environmentalSummary">
            <h4>Conditions</h4>
            <p>{{ environmentalSummary }}</p>
        </div>

          <div class="summary-block">
            <h4>Report summary</h4>
            <input
              type="text"
              [(ngModel)]="summaryPrompt"
              placeholder="Ask for a report summary"
              class="summary-input"
              (keydown.enter)="fetchSummary()">
            <button (click)="fetchSummary()" [disabled]="isFetchingSummary || !summaryPrompt.trim()" class="summary-btn">
              {{ isFetchingSummary ? 'Loading…' : 'Get summary' }}
            </button>
            <p class="summary-text" *ngIf="summaryText">{{ summaryText }}</p>
          </div>
                </div>
      </div>
    </div>
  `,
  styles: [`
    .live-demo-container {
      height: 100vh;
      background: linear-gradient(135deg, #001122 0%, #001f3f 100%);
      color: white;
      font-family: system-ui, -apple-system, sans-serif;
      display: flex;
      flex-direction: column;
    }

    .header-bar {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
      padding: 12px 24px;
      background: rgba(0, 30, 60, 0.9);
      border-bottom: 2px solid #4fc3f7;
    }

    .home-link {
      color: #4fc3f7;
      text-decoration: none;
      font-size: 0.9rem;
    }

    .header-bar h1 {
      color: #4fc3f7;
      font-size: 1.5rem;
      margin: 0;
    }

    .badge {
      background: #4a3f00;
      color: #fff9c4;
      font-size: 0.7rem;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      text-transform: uppercase;
    }

    .subtitle {
      color: #a8cce0;
      font-size: 0.9rem;
      margin: 0;
      flex: 1 1 100%;
    }

    .demo-controls {
      margin-left: auto;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .start-btn, .stop-btn, .summary-btn {
      padding: 8px 16px;
      border-radius: 5px;
      border: none;
      cursor: pointer;
      font-weight: 600;
    }

    .start-btn { background: #4fc3f7; color: #001e3c; }
    .stop-btn { background: #455a64; color: white; }
    .status { font-size: 0.85rem; color: #8ab4cc; }
    .status.running { color: #4fc3f7; }

    .main-interface {
      flex: 1;
      display: grid;
      grid-template-columns: 1fr 320px;
      min-height: 0;
    }

    .map-centerpiece {
      display: flex;
      flex-direction: column;
      min-height: 0;
    }

    .map-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 16px;
      background: rgba(0, 20, 40, 0.8);
    }

    .map-header h3 { margin: 0; color: #4fc3f7; }
    .map-mode { font-size: 0.85rem; color: #a8cce0; }

    .map-container {
      flex: 1;
      min-height: 0;
    }

    #live-map {
      width: 100%;
      height: 100%;
    }

    .data-panel {
      background: rgba(0, 30, 60, 0.95);
      border-left: 1px solid #4fc3f7;
      padding: 16px;
      overflow-y: auto;
    }

    .data-panel h3 {
      margin: 0 0 12px;
      color: #4fc3f7;
      font-size: 1rem;
    }

    .stat {
      display: flex;
      justify-content: space-between;
      margin: 8px 0;
      font-size: 0.9rem;
    }

    .label { color: #a8cce0; }
    .value { font-weight: 600; }
    .mono { font-family: monospace; font-size: 0.75rem; }

    .env-block, .summary-block {
      margin-top: 16px;
      padding-top: 12px;
      border-top: 1px solid rgba(79, 195, 247, 0.3);
    }

    .env-block h4, .summary-block h4 {
      margin: 0 0 8px;
      font-size: 0.9rem;
      color: #7ec8e8;
    }

    .summary-input {
      width: 100%;
      padding: 8px;
      border-radius: 4px;
      border: 1px solid #2a5a7a;
      background: #001528;
      color: white;
      margin-bottom: 8px;
      box-sizing: border-box;
    }

    .summary-text {
      font-size: 0.85rem;
      color: #c5dff0;
      margin-top: 8px;
      white-space: pre-wrap;
    }
  `]
})
export class LiveAIDemoComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('mapContainer', { static: false }) mapContainer!: ElementRef;

  private readonly backendService = inject(BackendService);
  private map: google.maps.Map | null = null;
  private markers: google.maps.Marker[] = [];
  private circles: google.maps.Circle[] = [];
  private subscriptions: Subscription[] = [];

  isRunning = false;
  sightingsLoaded = -1;
  gridPoints = -1;
  maxProbability = -1;
  modelVersion = '';
  environmentalSummary = '';
  summaryPrompt = '';
  summaryText = '';
  isFetchingSummary = false;

  ngOnInit(): void {
    // Map init deferred to AfterViewInit
  }

  ngAfterViewInit(): void {
    setTimeout(() => this.initializeMap(), 500);
  }

  ngOnDestroy(): void {
    this.stopDemo();
  }

  startDemo(): void {
    this.isRunning = true;
    this.clearMapOverlays();
    void this.loadLiveData();
  }

  stopDemo(): void {
    this.isRunning = false;
    this.subscriptions.forEach(sub => sub.unsubscribe());
    this.subscriptions = [];
  }

  fetchSummary(): void {
    const prompt = this.summaryPrompt.trim();
    if (!prompt || this.isFetchingSummary) {
      return;
    }
    this.isFetchingSummary = true;
    this.summaryText = '';
    const sub = this.backendService.queryAgent(prompt).subscribe({
      next: (response) => {
        this.summaryText = typeof response === 'string'
          ? response
          : response?.message || response?.summary || JSON.stringify(response, null, 2);
        this.isFetchingSummary = false;
      },
      error: () => {
        this.summaryText = 'Could not load summary. Try the Reports page for a full CSV.';
        this.isFetchingSummary = false;
      }
    });
    this.subscriptions.push(sub);
  }

  private initializeMap(): void {
    const checkGoogleMaps = () => {
      if (typeof google === 'undefined' || !google.maps || !this.mapContainer) {
        setTimeout(checkGoogleMaps, 500);
        return;
      }
      const mapElement = this.mapContainer.nativeElement.querySelector('#live-map');
      if (!mapElement) {
        return;
      }

      const bounds = new google.maps.LatLngBounds(
        new google.maps.LatLng(48.40, -123.25),
        new google.maps.LatLng(48.70, -122.75)
      );

      this.map = new google.maps.Map(mapElement, {
        center: { lat: 48.5465, lng: -123.0095 },
        zoom: 12,
        minZoom: 11,
        maxZoom: 16,
        restriction: { latLngBounds: bounds, strictBounds: true },
        mapTypeId: google.maps.MapTypeId.HYBRID,
        streetViewControl: false
      });
    };
    checkGoogleMaps();
  }

  private async loadLiveData(): Promise<void> {
    if (!this.map) {
      return;
    }

    try {
      const sightings = await firstValueFrom(this.backendService.getHistoricalSightings());
      this.sightingsLoaded = sightings.length;
      sightings.slice(0, 80).forEach(sighting => {
      const marker = new google.maps.Marker({
        position: { lat: sighting.latitude, lng: sighting.longitude },
        map: this.map,
          title: `${sighting.pod} · ${sighting.date}`,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
            scale: 6,
            fillColor: '#4fc3f7',
          fillOpacity: 0.8,
            strokeColor: '#fff',
            strokeWeight: 1
          }
        });
        this.markers.push(marker);
      });
    } catch {
      this.sightingsLoaded = 0;
    }

    try {
      const grid = await firstValueFrom(this.backendService.generateMLPredictions(24, 0.1, 12));
      this.gridPoints = grid.metadata.totalPredictions;
      this.maxProbability = grid.metadata.maxProbability;
      this.modelVersion = grid.metadata.modelVersion || grid.model;
      grid.predictions.slice(0, 120).forEach(point => {
        const circle = new google.maps.Circle({
        map: this.map,
          center: { lat: point.latitude, lng: point.longitude },
          radius: 400,
          fillColor: '#4fc3f7',
          fillOpacity: Math.min(0.6, point.probability),
          strokeWeight: 0
        });
        this.circles.push(circle);
      });
    } catch {
      this.gridPoints = 0;
    }

    try {
      const env = await firstValueFrom(this.backendService.getEnvironmentalData());
      const parts = [
        env?.tide_height_ft != null ? `Tide ${env.tide_height_ft} ft` : null,
        env?.wind_speed ? `Wind ${env.wind_speed}` : null,
        env?.water_temp_c != null ? `Water ${env.water_temp_c}°C` : null
      ].filter(Boolean);
      this.environmentalSummary = parts.length ? parts.join(' · ') : 'Environmental data loaded.';
    } catch {
      this.environmentalSummary = '';
    }

    this.isRunning = false;
  }

  private clearMapOverlays(): void {
    this.markers.forEach(m => m.setMap(null));
    this.circles.forEach(c => c.setMap(null));
    this.markers = [];
    this.circles = [];
  }
}
