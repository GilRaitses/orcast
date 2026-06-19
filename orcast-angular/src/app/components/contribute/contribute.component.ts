import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GoogleMapsModule } from '@angular/google-maps';

import { AppShellComponent } from '../shared/app-shell.component';
import { BackendService } from '../../services/backend.service';
import { PilotSubmissionService, PilotSighting } from '../../services/pilot-submission.service';

interface SightingForm {
  place: string;
  observedAt: string;
  behavior: string;
  groupSize: number | null;
  notes: string;
  observerName: string;
}

@Component({
  selector: 'orcast-contribute',
  standalone: true,
  imports: [CommonModule, FormsModule, GoogleMapsModule, AppShellComponent],
  template: `
    <orcast-app-shell currentPage="contribute">
      <header class="page-head">
        <h1>Add a sighting</h1>
        <p class="lead">
          Log an orca sighting from the shore or your kayak on San Juan, Orcas,
          Lopez, or Shaw. Tap the map to mark where you saw them.
        </p>
      </header>

      <p class="prototype-note">
        Community sightings are reviewed before they appear on the map. We also
        keep a copy on this device in the list below.
      </p>

      <section class="card form-card">
        <form (ngSubmit)="submit()" #sightingForm="ngForm" novalidate>
          <div class="field">
            <label for="place">Place <span class="req">required</span></label>
            <input
              id="place"
              name="place"
              type="text"
              [(ngModel)]="form.place"
              required
              placeholder="e.g. Lime Kiln Point" />
          </div>

          <div class="field">
            <label for="observedAt">Date &amp; time observed <span class="req">required</span></label>
            <input
              id="observedAt"
              name="observedAt"
              type="datetime-local"
              [(ngModel)]="form.observedAt"
              required />
          </div>

          <div class="field">
            <label for="behavior">Behavior</label>
            <select id="behavior" name="behavior" [(ngModel)]="form.behavior">
              <option value="feeding">Feeding</option>
              <option value="traveling">Traveling</option>
              <option value="socializing">Socializing</option>
              <option value="resting">Resting</option>
              <option value="unknown">Unknown</option>
            </select>
          </div>

          <div class="field">
            <label for="groupSize">Group size</label>
            <input
              id="groupSize"
              name="groupSize"
              type="number"
              min="0"
              [(ngModel)]="form.groupSize"
              placeholder="Optional" />
          </div>

          <div class="field">
            <label for="observerName">Your name</label>
            <input
              id="observerName"
              name="observerName"
              type="text"
              [(ngModel)]="form.observerName"
              placeholder="Optional" />
          </div>

          <div class="field">
            <label for="notes">Notes</label>
            <textarea
              id="notes"
              name="notes"
              rows="3"
              [(ngModel)]="form.notes"
              placeholder="Optional"></textarea>
          </div>

          <div class="field">
            <label>Location <span class="req">optional</span></label>
            <p class="map-hint">
              Tap the map to drop a pin where you saw the orcas.
            </p>
            <div class="map-wrap">
              <google-map
                height="320px"
                width="100%"
              [options]="mapOptions"
              (mapClick)="onMapClick($event)">
                <map-marker *ngIf="hasPin" [position]="markerPosition"></map-marker>
              </google-map>
            </div>
            <p class="coords" *ngIf="hasPin">
              Pinned at {{ latitude | number: '1.4-4' }}, {{ longitude | number: '1.4-4' }}
              <button type="button" class="link-btn" (click)="clearPin()">Clear pin</button>
            </p>
            <p class="coords coords--empty" *ngIf="!hasPin">
              No pin set — you can submit without one.
            </p>
          </div>

          <p class="form-error" *ngIf="error">{{ error }}</p>
          <p class="form-success" *ngIf="success">{{ success }}</p>

          <button type="submit" class="btn btn--primary" [disabled]="isSubmitting">
            {{ isSubmitting ? 'Sending...' : 'Add sighting' }}
          </button>
        </form>
      </section>

      <section class="card list-card">
        <div class="list-head">
          <h2>Your submissions</h2>
          <button
            type="button"
            class="btn btn--ghost"
            *ngIf="sightings.length"
            (click)="clearAll()">
            Clear all
          </button>
        </div>

        <p class="empty" *ngIf="!sightings.length">
          No submissions yet. Add one above.
        </p>

        <ul class="sighting-list" *ngIf="sightings.length">
          <li *ngFor="let s of sightings" class="sighting-item">
            <div class="sighting-place">{{ s.place }}</div>
            <div class="sighting-meta">
              <span>{{ s.observedAt | date: 'medium' }}</span>
              <span class="sep">·</span>
              <span>{{ s.behavior }}</span>
              <ng-container *ngIf="s.groupSize != null">
                <span class="sep">·</span>
                <span>group of {{ s.groupSize }}</span>
              </ng-container>
            </div>
          </li>
        </ul>
      </section>
    </orcast-app-shell>
  `,
  styles: [`
    :host { display: block; }

    .page-head {
      max-width: 760px;
      margin: 0 auto;
      padding: 2rem 1.5rem 0.5rem;
    }

    .page-head h1 {
      margin: 0 0 0.5rem;
    }

    .lead {
      color: var(--text-muted);
      margin: 0;
    }

    .prototype-note {
      max-width: 760px;
      margin: 1rem auto 0;
      padding: 0.6rem 0.9rem;
      border-left: 3px solid var(--accent);
      background: var(--bg-panel);
      border-radius: var(--radius-sm);
      color: var(--text-muted);
      font-size: 0.9rem;
    }

    .form-card,
    .list-card {
      max-width: 760px;
      margin: 1.25rem auto 0;
    }

    .field {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      margin-bottom: 1rem;
    }

    .field label {
      font-weight: 600;
      font-size: 0.92rem;
    }

    .req {
      font-weight: 400;
      font-size: 0.78rem;
      color: var(--text-muted);
    }

    .field input,
    .field select,
    .field textarea {
      padding: 0.55rem 0.7rem;
      border-radius: var(--radius-sm);
      border: 1px solid rgba(255, 255, 255, 0.15);
      background: var(--bg-panel);
      color: inherit;
      font: inherit;
    }

    .map-hint {
      margin: 0;
      color: var(--text-muted);
      font-size: 0.85rem;
    }

    .map-wrap {
      border-radius: var(--radius-sm);
      overflow: hidden;
      border: 1px solid rgba(255, 255, 255, 0.15);
    }

    .coords {
      margin: 0;
      font-size: 0.85rem;
      color: var(--accent);
    }

    .coords--empty {
      color: var(--text-muted);
    }

    .link-btn {
      background: none;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      font: inherit;
      text-decoration: underline;
      padding: 0 0 0 0.5rem;
    }

    .form-error {
      color: #ff8a80;
      margin: 0 0 0.75rem;
    }

    .form-success {
      color: var(--accent);
      margin: 0 0 0.75rem;
    }

    .list-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 0.75rem;
    }

    .list-head h2 {
      margin: 0;
    }

    .empty {
      color: var(--text-muted);
      margin: 0;
    }

    .sighting-list {
      list-style: none;
      margin: 0;
      padding: 0;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .sighting-item {
      padding: 0.75rem 0.9rem;
      border-radius: var(--radius-sm);
      background: var(--bg-panel);
    }

    .sighting-place {
      font-weight: 600;
    }

    .sighting-meta {
      color: var(--text-muted);
      font-size: 0.88rem;
      margin-top: 0.2rem;
    }

    .sighting-meta .sep {
      margin: 0 0.35rem;
    }
  `]
})
export class ContributeComponent implements OnInit {
  form: SightingForm = this.emptyForm();
  sightings: PilotSighting[] = [];
  error = '';
  success = '';
  isSubmitting = false;

  latitude: number | null = null;
  longitude: number | null = null;

  mapOptions: google.maps.MapOptions = {
    zoom: 10,
    center: { lat: 48.5465, lng: -123.0307 },
    mapTypeId: google.maps.MapTypeId.HYBRID,
    styles: [
      { featureType: 'poi', stylers: [{ visibility: 'off' }] },
      { featureType: 'transit', stylers: [{ visibility: 'off' }] }
    ]
  };

  constructor(
    private backendService: BackendService,
    private pilotSubmissionService: PilotSubmissionService
  ) {}

  ngOnInit(): void {
    this.refresh();
  }

  get hasPin(): boolean {
    return this.latitude != null && this.longitude != null;
  }

  get markerPosition(): google.maps.LatLngLiteral {
    return { lat: this.latitude ?? 0, lng: this.longitude ?? 0 };
  }

  onMapClick(event: google.maps.MapMouseEvent): void {
    if (!event.latLng) {
      return;
    }
    this.latitude = event.latLng.lat();
    this.longitude = event.latLng.lng();
  }

  clearPin(): void {
    this.latitude = null;
    this.longitude = null;
  }

  submit(): void {
    this.error = '';
    this.success = '';

    const place = this.form.place?.trim();
    const observedAt = this.form.observedAt?.trim();

    if (!place || !observedAt) {
      this.error = 'Place and date & time observed are required.';
      return;
    }

    const observedIso = this.toIso(observedAt);
    const count = this.form.groupSize != null ? Number(this.form.groupSize) : undefined;
    const notes = this.form.notes?.trim() || undefined;
    const observerName = this.form.observerName?.trim() || undefined;

    const payload: {
      place: string;
      latitude?: number;
      longitude?: number;
      observed_at: string;
      behavior: string;
      count?: number;
      notes?: string;
      observer_name?: string;
    } = {
      place,
      observed_at: observedIso,
      behavior: this.form.behavior
    };

    if (this.latitude != null && this.longitude != null) {
      payload.latitude = this.latitude;
      payload.longitude = this.longitude;
    }
    if (count != null && !Number.isNaN(count)) {
      payload.count = count;
    }
    if (notes) {
      payload.notes = notes;
    }
    if (observerName) {
      payload.observer_name = observerName;
    }

    this.isSubmitting = true;

    this.backendService.submitCommunitySighting(payload).subscribe({
      next: () => {
        this.cacheLocally(place, observedAt);
        this.success = 'Submitted for review';
        this.isSubmitting = false;
        this.resetForm();
      },
      error: () => {
        this.cacheLocally(place, observedAt);
        this.success = `Saved on this device — we'll sync it when you're back online.`;
        this.isSubmitting = false;
        this.resetForm();
      }
    });
  }

  clearAll(): void {
    this.pilotSubmissionService.clear();
    this.refresh();
  }

  private cacheLocally(place: string, observedAt: string): void {
    this.pilotSubmissionService.save({
      place,
      observedAt,
      behavior: this.form.behavior,
      groupSize: this.form.groupSize,
      notes: this.form.notes?.trim() ?? ''
    });
  }

  private resetForm(): void {
    this.form = this.emptyForm();
    this.clearPin();
    this.refresh();
  }

  private refresh(): void {
    this.sightings = this.pilotSubmissionService.list();
  }

  /** Convert a datetime-local value to an ISO string; pass through if already parseable. */
  private toIso(value: string): string {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? value : parsed.toISOString();
  }

  private emptyForm(): SightingForm {
    return {
      place: '',
      observedAt: '',
      behavior: 'unknown',
      groupSize: null,
      notes: '',
      observerName: ''
    };
  }
}
