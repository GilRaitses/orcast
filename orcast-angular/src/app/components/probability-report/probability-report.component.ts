import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GoogleMapsModule } from '@angular/google-maps';

import { AppShellComponent } from '../shared/app-shell.component';
import { BackendService } from '../../services/backend.service';
import { MapService } from '../../services/map.service';
import { ProbabilityReportResponse, ProbabilityHotspot } from '../../models/orca-sighting.model';

@Component({
  selector: 'orcast-probability-report',
  standalone: true,
  imports: [CommonModule, FormsModule, GoogleMapsModule, AppShellComponent],
  template: `
    <orcast-app-shell currentPage="reports">
      <main class="report-page">
        <div class="report-split">
          <section class="report-list">
            <header class="report-intro">
              <h1>Probability report</h1>
              <p class="lead">Where to watch this week. Tap a hotspot to see it on the map.</p>
            </header>

            <div class="controls card">
              <label class="confidence">
                Minimum confidence: {{ minConfidence | percent:'1.0-0' }}
                <input
                  type="range"
                  min="0"
                  max="95"
                  step="5"
                  [value]="minConfidence * 100"
                  (input)="setConfidence($event)">
              </label>

              <div class="actions">
                <button
                  class="btn btn--primary"
                  (click)="generateReport()"
                  [disabled]="isLoading"
                  data-cy="generate-report">
                  {{ isLoading ? 'Generating report...' : 'Generate report' }}
                </button>

                <button
                  *ngIf="report"
                  class="btn btn--ghost"
                  (click)="downloadCsv()"
                  [disabled]="isDownloading"
                  data-cy="download-csv">
                  {{ isDownloading ? 'Downloading...' : 'Download CSV' }}
                </button>
              </div>

              <div *ngIf="errorMessage" class="error">{{ errorMessage }}</div>
            </div>

            <p class="summary" *ngIf="report?.summary">{{ report?.summary }}</p>

            <div class="hotspots" *ngIf="report?.hotspots?.length; else emptyState">
              <article
                class="hotspot-card card card--hover"
                *ngFor="let hotspot of report?.hotspots"
                [class.selected]="hotspot === selectedHotspot"
                (click)="selectHotspot(hotspot)">
                <h3>{{ hotspot.name }}</h3>
                <div class="score-row">
                  <span>Chance of sightings</span>
                  <strong>{{ hotspot.probability | percent:'1.0-0' }}</strong>
                </div>
                <p class="hotspot-detail">
                  {{ hotspot.detection_count }} recent sighting(s) near this area
                </p>
              </article>
            </div>

            <ng-template #emptyState>
              <p class="empty" *ngIf="!isLoading && !errorMessage">
                No hotspots above this confidence yet. Lower the slider or generate again.
              </p>
            </ng-template>

            <details class="report-details" *ngIf="report">
              <summary>Report details</summary>
              <dl>
                <div>
                  <dt>Generated</dt>
                  <dd>{{ report?.generated_at | date:'medium' }}</dd>
                </div>
                <div>
                  <dt>Report ID</dt>
                  <dd>{{ report?.report_id }}</dd>
                </div>
                <div>
                  <dt>model_version</dt>
                  <dd>{{ report?.model_version }}</dd>
                </div>
              </dl>
            </details>
          </section>

          <section class="report-map">
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

    .report-page {
      padding: 0;
    }

    .report-split {
      display: grid;
      grid-template-columns: 380px 1fr;
      gap: 0;
      height: calc(100vh - var(--nav-h));
    }

    .report-list {
      overflow-y: auto;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .report-map {
      position: relative;
      min-height: 300px;
      background: var(--bg-panel);
    }

    .report-intro h1 {
      margin: 0 0 0.25rem;
      font-size: 1.75rem;
    }

    .report-intro .lead {
      margin: 0;
      color: var(--text-muted);
    }

    .card {
      padding: 16px;
    }

    .controls .confidence {
      display: block;
      margin-bottom: 16px;
    }

    .controls input[type="range"] {
      display: block;
      width: 100%;
      margin-top: 8px;
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .summary {
      font-size: 1.05rem;
      color: var(--text-muted);
      margin: 0;
    }

    .hotspots {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .hotspot-card {
      cursor: pointer;
      padding: 14px 16px;
    }

    .hotspot-card.selected {
      border-color: var(--accent);
      box-shadow: 0 0 0 1px var(--accent);
    }

    .hotspot-card h3 {
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

    .hotspot-detail {
      color: var(--text-muted);
      font-size: 0.9rem;
      margin: 6px 0 0;
    }

    .empty {
      color: var(--text-muted);
    }

    .error {
      color: #ffb3b3;
      margin-top: 12px;
    }

    .report-details {
      margin-top: auto;
      color: var(--text-faint);
      font-size: 0.85rem;
    }

    .report-details summary {
      cursor: pointer;
      color: var(--text-muted);
    }

    .report-details dl {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
      gap: 12px;
      margin: 12px 0 0;
    }

    .report-details dt {
      color: var(--text-faint);
      font-size: 0.8rem;
    }

    .report-details dd {
      margin: 2px 0 0;
      font-family: monospace;
      word-break: break-all;
    }

    @media (max-width: 768px) {
      .report-split {
        grid-template-columns: 1fr;
        grid-template-rows: minmax(300px, 40vh) auto;
        height: auto;
      }

      .report-list {
        overflow-y: visible;
      }
    }
  `]
})
export class ProbabilityReportComponent implements OnInit {
  minConfidence = 0;
  report: ProbabilityReportResponse | null = null;
  selectedHotspot: ProbabilityHotspot | null = null;
  isLoading = false;
  isDownloading = false;
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

  ngOnInit(): void {
    this.generateReport();
  }

  onMapInitialized(map: google.maps.Map): void {
    this.mapService.registerMap(map);
    this.mapReady = true;
    if (this.report?.hotspots?.length) {
      this.plotHotspots(this.report.hotspots);
    }
  }

  setConfidence(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.minConfidence = Number(input.value) / 100;
  }

  generateReport(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.selectedHotspot = null;
    this.backendService.generateProbabilityReport(this.minConfidence).subscribe({
      next: report => {
        this.report = report;
        this.isLoading = false;
        if (this.mapReady) {
          this.plotHotspots(report.hotspots);
        }
      },
      error: error => {
        this.errorMessage = error.message || 'Failed to generate report';
        this.isLoading = false;
      }
    });
  }

  selectHotspot(hotspot: ProbabilityHotspot): void {
    this.selectedHotspot = hotspot;
    this.mapService.centerMap(hotspot.center_latitude, hotspot.center_longitude, 13);
  }

  downloadCsv(): void {
    if (!this.report?.report_id) {
      return;
    }
    this.isDownloading = true;
    this.backendService.downloadReportCsv(this.report.report_id).subscribe({
      next: blob => {
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = `${this.report!.report_id}.csv`;
        anchor.click();
        URL.revokeObjectURL(url);
        this.isDownloading = false;
      },
      error: error => {
        this.errorMessage = error.message || 'Failed to download CSV';
        this.isDownloading = false;
      }
    });
  }

  private plotHotspots(hotspots: ProbabilityHotspot[]): void {
    this.mapService.addReportHotspots(hotspots, hotspot => {
      this.selectedHotspot = hotspot;
    });

    const coords = (hotspots || [])
      .map(h => ({ lat: h.center_latitude, lng: h.center_longitude }));
    if (coords.length) {
      this.mapService.fitBounds(coords);
    }
  }
}
