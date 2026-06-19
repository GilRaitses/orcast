import { Component, OnInit, OnDestroy, NgZone } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';
import { GoogleMapsModule } from '@angular/google-maps';
import { Subject, forkJoin, takeUntil } from 'rxjs';

import { AppShellComponent } from '../shared/app-shell.component';
import { BackendService } from '../../services/backend.service';
import { MapService } from '../../services/map.service';
import { MapEvent } from '../../models/orca-sighting.model';
import { SAN_JUAN_BOUNDS, isInWater } from '../../services/geo-region';
import { environment } from '../../../environments/environment';

interface PathStep {
  route: string;
  title: string;
  description: string;
}

interface PeekState {
  visible: boolean;
  lat: number;
  lng: number;
}

@Component({
  selector: 'orcast-landing',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, GoogleMapsModule, AppShellComponent],
  template: `
    <orcast-app-shell currentPage="home" [showFooter]="true">
      <section class="map-hero">
        <google-map
          height="100%"
          width="100%"
          [options]="mapOptions"
          (mapInitialized)="onMapInitialized($event)">
        </google-map>

        <div class="hero-overlay card">
          <p class="eyebrow">Salish Sea · Southern Resident orcas</p>
          <h1>orcast</h1>
          <p class="tagline">
            orcast is a pilot study on forecast durability for orca sighting probabilities
            on the San Juan islands (San Juan, Orcas, Lopez, and Shaw). It supports maps
            and planning tools by integrating sighting catalogs, hydrophone and crowd sound tags.
          </p>
          <span class="pilot-banner">Pilot dataset · few points so far · San Juan islands</span>
        </div>

        <div class="map-legend card">
          <span class="legend-row"><i class="dot visual"></i> Visual sighting</span>
          <span class="legend-row"><i class="dot acoustic"></i> Acoustic detection (hydrophone)</span>
          <span class="legend-row"><i class="dot station"></i> Listening station</span>
          <span class="legend-row"><i class="swatch heat"></i> Recent detection density</span>
        </div>

        <div class="peek-card card" *ngIf="peek.visible">
          <button type="button" class="peek-close" (click)="closePeek()" aria-label="Close">×</button>
          <h3>Elevated chance of sightings near here</h3>
          <p class="peek-coords">{{ peek.lat | number:'1.3-3' }}, {{ peek.lng | number:'1.3-3' }}</p>
          <div class="peek-actions">
            <a routerLink="/reports" class="btn btn--primary">See this week's report</a>
            <a routerLink="/plan" class="btn btn--ghost">Plan a trip here</a>
          </div>
        </div>
      </section>

      <div class="hero-actions">
        <a routerLink="/reports" class="btn btn--ghost">See this week's map</a>
        <a routerLink="/partners" class="btn btn--ghost">Partner with us</a>
      </div>

      <section class="panel card">
        <h2>Start here</h2>
        <p class="lead">
          Maps and planning tools for people watching from the shore or going out kayaking
          on the San Juan islands. Follow the three steps below.
        </p>

        <ol class="steps">
          <li *ngFor="let step of steps; let i = index">
            <a [routerLink]="step.route" class="card card--hover step-card">
              <span class="step-num">{{ i + 1 }}</span>
              <span class="badge badge--live">Live API</span>
              <h3>{{ step.title }}</h3>
              <p>{{ step.description }}</p>
            </a>
          </li>
        </ol>

        <a [routerLink]="extra.route" class="card card--hover extra-card">
          <span class="badge badge--live">Live API</span>
          <h3>{{ extra.title }}</h3>
          <p>{{ extra.description }}</p>
        </a>

        <p class="demo-disclaimer">
          The chat-style map demos are scripted. The report page and CSV export call the live API on AWS.
        </p>
      </section>

      <section class="panel card field-tools">
        <h2>Field tools (preview)</h2>
        <div class="field-tools-grid">
          <a routerLink="/plan" class="card card--hover field-tool-card">
            <span class="badge badge--demo">Preview</span>
            <h3>Plan a trip</h3>
            <p>Pick an island and see where orcas have been showing up.</p>
          </a>
          <a routerLink="/contribute" class="card card--hover field-tool-card">
            <span class="badge badge--demo">Prototype</span>
            <h3>Add a sighting</h3>
            <p>Log a shore or kayak sighting for the August pilot.</p>
          </a>
        </div>
      </section>

      <section class="panel card contact" id="contact">
        <h2>Contact &amp; collaborate</h2>
        <p>Tell us about your organization and how you would like to collaborate.</p>

        <form *ngIf="contactFormUrl" (ngSubmit)="submitContact()" class="contact-form">
          <label>
            Name
            <input type="text" name="name" [(ngModel)]="contact.name" required>
          </label>
          <label>
            Email
            <input type="email" name="email" [(ngModel)]="contact.email" required>
          </label>
          <label>
            Organization
            <input type="text" name="organization" [(ngModel)]="contact.organization">
          </label>
          <label>
            Interest
            <select name="interest" [(ngModel)]="contact.interest">
              <option value="pilot">Field pilot partner</option>
              <option value="research">Research collaboration</option>
              <option value="technical">Technical integration</option>
              <option value="other">Other</option>
            </select>
          </label>
          <label>
            Message
            <textarea name="message" rows="4" [(ngModel)]="contact.message" required></textarea>
          </label>
          <button type="submit" class="btn btn--primary" [disabled]="isSubmitting">
            {{ isSubmitting ? 'Sending…' : 'Send message' }}
          </button>
          <p class="form-note" *ngIf="submitMessage">{{ submitMessage }}</p>
        </form>

        <div *ngIf="!contactFormUrl" class="mailto-fallback">
          <p>Email us directly:</p>
          <a class="btn btn--primary" [href]="mailtoLink">contact&#64;orcast.org</a>
        </div>
      </section>
    </orcast-app-shell>
  `,
  styles: [`
    /* Full-bleed coastline heatmap hero. Breaks out of the centered
       .app-page__main column and sits directly under the nav bar. */
    .map-hero {
      position: relative;
      width: 100vw;
      margin-left: calc(50% - 50vw);
      margin-top: calc(var(--s5) * -1);
      margin-bottom: var(--s4);
      height: 60vh;
      min-height: 360px;
      overflow: hidden;
      background: var(--bg-deep);
    }
    .map-hero google-map,
    .map-hero .map-container {
      display: block;
      height: 100% !important;
      width: 100% !important;
    }
    .hero-overlay {
      position: absolute;
      top: var(--s4);
      left: var(--s4);
      z-index: 2;
      max-width: min(420px, calc(100vw - 2 * var(--s4)));
      padding: var(--s4);
    }
    .eyebrow {
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 0.8rem;
      color: var(--accent);
      margin: 0 0 var(--s2);
    }
    h1 {
      font-size: 2.6rem;
      margin: 0 0 var(--s2);
      letter-spacing: 0.04em;
    }
    .tagline {
      font-size: 1rem;
      margin: 0 0 var(--s3);
      color: var(--text-muted);
    }
    .map-legend {
      position: absolute;
      right: var(--s3);
      bottom: var(--s3);
      z-index: 1000;
      display: grid;
      gap: 4px;
      padding: var(--s2) var(--s3);
      font-size: 0.78rem;
      color: var(--text-muted);
      max-width: 240px;
    }
    .legend-row {
      display: flex;
      align-items: center;
      gap: var(--s2);
      white-space: nowrap;
    }
    .map-legend .dot {
      width: 11px;
      height: 11px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .map-legend .dot.visual { background: #ffb300; border: 1px solid #fff; }
    .map-legend .dot.acoustic { background: transparent; border: 2px solid #4fc3f7; }
    .map-legend .dot.station { background: #00e5ff; border: 1px solid #fff; border-radius: 2px; }
    .map-legend .swatch.heat {
      width: 16px;
      height: 11px;
      border-radius: 2px;
      flex-shrink: 0;
      background: linear-gradient(90deg, #0078c8, #28dcaa, #ffcd00, #ff6e00);
    }
    @media (max-width: 768px) {
      .map-legend { display: none; }
    }
    .peek-card {
      position: absolute;
      left: 50%;
      bottom: var(--s4);
      transform: translateX(-50%);
      z-index: 3;
      width: min(420px, calc(100vw - 2 * var(--s4)));
      padding: var(--s4);
      animation: peek-slide-up 0.18s ease-out;
    }
    @keyframes peek-slide-up {
      from { opacity: 0; transform: translate(-50%, 12px); }
      to { opacity: 1; transform: translate(-50%, 0); }
    }
    .peek-card h3 {
      margin: 0 var(--s4) var(--s1) 0;
      font-size: 1.05rem;
      color: var(--accent);
    }
    .peek-coords {
      margin: 0 0 var(--s3);
      font-size: 0.8rem;
      color: var(--text-faint);
    }
    .peek-actions {
      display: flex;
      gap: var(--s3);
      flex-wrap: wrap;
    }
    .peek-close {
      position: absolute;
      top: var(--s2);
      right: var(--s2);
      width: 1.75rem;
      height: 1.75rem;
      border: none;
      border-radius: 999px;
      background: transparent;
      color: var(--text-muted);
      font-size: 1.2rem;
      line-height: 1;
      cursor: pointer;
    }
    .peek-close:hover { color: var(--text); }
    .hero-actions {
      display: flex;
      gap: var(--s3);
      justify-content: center;
      flex-wrap: wrap;
      margin-bottom: var(--s5);
    }
    @media (max-width: 768px) {
      .hero-overlay {
        top: var(--s3);
        left: var(--s3);
        right: var(--s3);
        max-width: none;
        padding: var(--s3);
      }
      .tagline { display: none; }
      h1 { font-size: 2rem; }
      .peek-card { width: calc(100vw - 2 * var(--s3)); }
    }
    .panel {
      margin: 0 auto var(--s5);
    }
    .panel h2 {
      margin-top: 0;
      color: var(--accent);
    }
    .lead {
      color: var(--text-muted);
      margin-bottom: var(--s4);
    }
    .steps {
      list-style: none;
      padding: 0;
      margin: 0 0 var(--s4);
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: var(--s4);
    }
    .step-card,
    .extra-card {
      display: block;
      position: relative;
      color: inherit;
      text-decoration: none;
    }
    .extra-card {
      margin-bottom: var(--s4);
    }
    .step-num {
      position: absolute;
      top: var(--s3);
      right: var(--s3);
      width: 1.75rem;
      height: 1.75rem;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      background: var(--accent);
      color: var(--accent-ink);
      font-weight: 700;
      font-size: 0.85rem;
    }
    .step-card h3,
    .extra-card h3 {
      margin: var(--s2) 0 var(--s1);
      font-size: 1rem;
    }
    .step-card p,
    .extra-card p {
      margin: 0;
      font-size: 0.9rem;
      color: var(--text-muted);
    }
    .demo-disclaimer {
      margin: 0;
      font-size: 0.9rem;
      color: var(--text-faint);
    }
    .field-tools-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: var(--s4);
    }
    .field-tool-card {
      display: block;
      position: relative;
      color: inherit;
      text-decoration: none;
    }
    .field-tool-card h3 {
      margin: var(--s2) 0 var(--s1);
      font-size: 1rem;
    }
    .field-tool-card p {
      margin: 0;
      font-size: 0.9rem;
      color: var(--text-muted);
    }
    .contact-form {
      display: grid;
      gap: var(--s3);
      max-width: 520px;
    }
    .contact-form label {
      display: grid;
      gap: var(--s1);
      font-size: 0.9rem;
    }
    .contact-form input,
    .contact-form select,
    .contact-form textarea {
      padding: var(--s2);
      border-radius: var(--radius-sm);
      border: 1px solid #2a5a7a;
      background: var(--bg-deep);
      color: var(--text);
    }
    .form-note { font-size: 0.85rem; color: var(--text-faint); margin-top: var(--s2); }
    .mailto-fallback { margin-top: var(--s2); }
  `]
})
export class LandingComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  // Archipelago center + zoom; fitBounds on init frames the whole pilot area.
  mapOptions: google.maps.MapOptions = {
    zoom: 10,
    center: { lat: 48.55, lng: -123.0 },
    mapTypeId: 'hybrid',
    disableDefaultUI: true,
    zoomControl: true,
    gestureHandling: 'cooperative',
    clickableIcons: false
  };

  peek: PeekState = { visible: false, lat: 0, lng: 0 };

  contactFormUrl = environment.contactFormUrl || '';
  contactEmail = environment.contactEmail || 'contact@orcast.org';
  mailtoLink = `mailto:${environment.contactEmail || 'contact@orcast.org'}?subject=orcast%20collaboration`;
  isSubmitting = false;
  submitMessage = '';

  contact = {
    name: '',
    email: '',
    organization: '',
    interest: 'pilot',
    message: ''
  };

  steps: PathStep[] = [
    {
      route: '/reports',
      title: 'Probability report',
      description: 'See where sightings cluster this week. Download a report for your trip.'
    },
    {
      route: '/historical',
      title: 'Historical sightings',
      description: 'Cross-validated OBIS sightings on a map.'
    },
    {
      route: '/ml-predictions',
      title: 'Probability map',
      description: 'Map of sighting probability for a region you choose. Same scoring as the report page.'
    }
  ];

  extra: PathStep = {
    route: '/realtime',
    title: 'Recent sightings',
    description: 'Sightings from our database on a map.'
  };

  constructor(
    private http: HttpClient,
    private backendService: BackendService,
    private mapService: MapService,
    private zone: NgZone
  ) {}

  ngOnInit(): void {}

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onMapInitialized(map: google.maps.Map): void {
    this.mapService.registerMap(map);
    this.frameArchipelago();
    this.loadInstrumentation();

    map.addListener('click', (event: google.maps.MapMouseEvent) => {
      const latLng = event.latLng;
      if (!latLng) {
        return;
      }
      const lat = latLng.lat();
      const lng = latLng.lng();
      this.zone.run(() => this.onMapClick(lat, lng));
    });
  }

  closePeek(): void {
    this.peek = { ...this.peek, visible: false };
  }

  private onMapClick(lat: number, lng: number): void {
    // Tap-water peek: only react to clicks on water inside the region.
    if (!isInWater(lat, lng)) {
      this.peek = { ...this.peek, visible: false };
      return;
    }
    this.peek = { visible: true, lat, lng };
  }

  private frameArchipelago(): void {
    this.mapService.fitBounds([
      { lat: SAN_JUAN_BOUNDS.minLat, lng: SAN_JUAN_BOUNDS.minLng },
      { lat: SAN_JUAN_BOUNDS.maxLat, lng: SAN_JUAN_BOUNDS.maxLng }
    ]);
  }

  /**
   * Synthesize the real instrumented data into the hero: a detection-density
   * heat (confidence x recency) plus typed markers (visual sighting vs acoustic
   * detection), listening stations, and sighting-to-station connectors.
   * Replaces the synthetic forecast grid that previously rendered here.
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
          this.mapService.addHydrophones(stations);
          this.mapService.addTypedSightings(events);
          this.mapService.addFeedConnectors(events, stations);
        },
        error: (error) => console.error('Landing instrumentation failed to load:', error)
      });
  }

  /** Recent, confident detections weigh more; old ones fade but never vanish. */
  private recencyFactor(timestamp: Date): number {
    const ageDays = (Date.now() - timestamp.getTime()) / 86_400_000;
    const factor = Math.exp(-ageDays / 540);
    return Math.min(1, Math.max(0.15, factor));
  }

  submitContact(): void {
    if (!this.contactFormUrl) {
      return;
    }
    this.isSubmitting = true;
    this.submitMessage = '';
    const payload = {
      name: this.contact.name,
      email: this.contact.email,
      organization: this.contact.organization,
      interest: this.contact.interest,
      message: this.contact.message,
      _subject: 'orcast collaboration inquiry'
    };
    this.http.post(this.contactFormUrl, payload, { responseType: 'text' }).subscribe({
      next: () => {
        this.submitMessage = 'Thank you — we will be in touch soon.';
        this.contact = { name: '', email: '', organization: '', interest: 'pilot', message: '' };
        this.isSubmitting = false;
      },
      error: () => {
        this.submitMessage = 'Could not send. Please email contact@orcast.org directly.';
        this.isSubmitting = false;
      }
    });
  }
}
