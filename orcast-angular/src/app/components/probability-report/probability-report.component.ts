import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { NavHeaderComponent } from '../shared/nav-header.component';
import { BackendService } from '../../services/backend.service';
import { ProbabilityReportResponse } from '../../models/orca-sighting.model';

@Component({
  selector: 'orcast-probability-report',
  standalone: true,
  imports: [CommonModule, FormsModule, NavHeaderComponent],
  template: `
    <orcast-nav-header currentPage="reports"></orcast-nav-header>

    <main class="report-page">
      <section class="report-card controls">
        <h1>ORCAST Probability Report</h1>
        <p>Generate an AWS backend report from cross-validated sightings and current hotspot probabilities.</p>

        <label>
          Minimum confidence: {{ minConfidence | percent:'1.0-0' }}
          <input type="range" min="0" max="95" step="5" [value]="minConfidence * 100" (input)="setConfidence($event)">
        </label>

        <button (click)="generateReport()" [disabled]="isLoading">
          {{ isLoading ? 'Generating report...' : 'Generate report' }}
        </button>

        <div *ngIf="errorMessage" class="error">{{ errorMessage }}</div>
      </section>

      <section class="report-card" *ngIf="report">
        <h2>{{ report.report_id }}</h2>
        <p class="summary">{{ report.summary }}</p>
        <dl>
          <div>
            <dt>Region</dt>
            <dd>{{ report.region }}</dd>
          </div>
          <div>
            <dt>Generated</dt>
            <dd>{{ report.generated_at | date:'medium' }}</dd>
          </div>
          <div>
            <dt>Model</dt>
            <dd>{{ report.model_version }}</dd>
          </div>
        </dl>
      </section>

      <section class="hotspots" *ngIf="report?.hotspots?.length">
        <article class="hotspot-card" *ngFor="let hotspot of report?.hotspots">
          <h3>{{ hotspot.name }}</h3>
          <div class="score-row">
            <span>Probability</span>
            <strong>{{ hotspot.probability | percent:'1.1-1' }}</strong>
          </div>
          <div class="score-row">
            <span>Confidence</span>
            <strong>{{ hotspot.confidence | percent:'1.1-1' }}</strong>
          </div>
          <p>
            {{ hotspot.detection_count }} sightings,
            {{ hotspot.validated_detection_count }} validated,
            {{ hotspot.source_count }} source(s)
          </p>
          <p class="coordinates">
            {{ hotspot.center_latitude | number:'1.4-4' }},
            {{ hotspot.center_longitude | number:'1.4-4' }}
          </p>
          <ul>
            <li *ngFor="let reason of hotspot.reason_codes">{{ reason }}</li>
          </ul>
        </article>
      </section>
    </main>
  `,
  styles: [`
    :host {
      display: block;
      min-height: 100vh;
      background: linear-gradient(135deg, #001e3c, #003b5c);
      color: white;
    }

    .report-page {
      max-width: 1100px;
      margin: 0 auto;
      padding: 80px 20px 40px;
    }

    .report-card,
    .hotspot-card {
      background: rgba(0, 30, 60, 0.92);
      border: 1px solid #4fc3f7;
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 20px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }

    .controls label {
      display: block;
      margin: 20px 0;
    }

    input[type="range"] {
      display: block;
      width: 100%;
      margin-top: 8px;
    }

    button {
      background: #4fc3f7;
      border: none;
      border-radius: 8px;
      color: #001e3c;
      cursor: pointer;
      font-weight: bold;
      padding: 12px 18px;
    }

    button:disabled {
      opacity: 0.6;
      cursor: wait;
    }

    dl {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
    }

    dt {
      color: #9bdffb;
      font-size: 0.85rem;
    }

    dd {
      margin: 4px 0 0;
      font-weight: bold;
    }

    .summary {
      font-size: 1.1rem;
    }

    .hotspots {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 20px;
    }

    .score-row {
      display: flex;
      justify-content: space-between;
      margin: 8px 0;
    }

    .coordinates {
      color: #9bdffb;
      font-family: monospace;
    }

    .error {
      color: #ffb3b3;
      margin-top: 16px;
    }
  `]
})
export class ProbabilityReportComponent implements OnInit {
  minConfidence = 0;
  report: ProbabilityReportResponse | null = null;
  isLoading = false;
  errorMessage = '';

  constructor(private backendService: BackendService) {}

  ngOnInit(): void {
    this.generateReport();
  }

  setConfidence(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.minConfidence = Number(input.value) / 100;
  }

  generateReport(): void {
    this.isLoading = true;
    this.errorMessage = '';
    this.backendService.generateProbabilityReport(this.minConfidence).subscribe({
      next: report => {
        this.report = report;
        this.isLoading = false;
      },
      error: error => {
        this.errorMessage = error.message || 'Failed to generate report';
        this.isLoading = false;
      }
    });
  }
}

