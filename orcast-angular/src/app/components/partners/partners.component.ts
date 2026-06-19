import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

import { AppShellComponent } from '../shared/app-shell.component';
import { environment } from '../../../environments/environment';

@Component({
  selector: 'orcast-partners',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, AppShellComponent],
  template: `
    <orcast-app-shell currentPage="partners" [showFooter]="true">
      <header class="page-head">
        <h1>Partner with orcast</h1>
        <p class="subtitle">Pilot study on forecast durability, San Juan islands</p>
      </header>

      <section class="card">
        <h2>Executive summary</h2>
        <p>
          orcast is a pilot study on forecast durability for orca sighting probabilities
          on the San Juan islands (San Juan, Orcas, Lopez, and Shaw). Backend decision
          infrastructure integrates sighting catalogs (OBIS, iNaturalist, OrcaHello),
          NOAA tides and conditions, Orcasound hydrophone stations, and crowd sound tags.
          Maps and planning tools sit on top for people watching from the shore or going
          out kayaking. Forecasting runs in the backend; the app is the field and social
          layer. Not for commercial whale-watching boats.
        </p>
      </section>

      <div class="two-col">
        <section class="card">
          <h2>What we offer</h2>
          <ul>
            <li>Maps and planning tools for shore visitors and kayakers on San Juan, Orcas, Lopez, and Shaw</li>
            <li>Probability reports you can download for a trip</li>
            <li>Field pilot support and feedback-driven iteration</li>
            <li>Cross-validated sightings with source attribution</li>
            <li>Publication and co-authorship opportunities for validated pilots</li>
          </ul>
        </section>

        <section class="card">
          <h2>What we seek</h2>
          <ul>
            <li>Shore visitors and kayakers willing to test maps and planning in the field</li>
            <li>Research groups with verified sighting datasets or DTAG deployments</li>
            <li>Citizen science networks (iNaturalist, Orca Network, Orcasound)</li>
            <li>Technical reviewers for scoring methodology and validation rules</li>
          </ul>
        </section>
      </div>

      <section class="card">
        <h2>Target partners</h2>
        <dl class="partner-list">
          <div>
            <dt>Cascadia Research Collective</dt>
            <dd>Southern Resident behavioral datasets · Dr. Robin Baird</dd>
          </div>
          <div>
            <dt>NOAA Northwest Fisheries Science Center</dt>
            <dd>Federal research collaboration · Dr. Brad Hanson</dd>
          </div>
          <div>
            <dt>Orca Network / Whale Museum / local naturalists</dt>
            <dd>Field pilot feedback and observer networks</dd>
          </div>
        </dl>
      </section>

      <section class="card">
        <h2>Technical capabilities (live today)</h2>
        <ul>
          <li>OBIS verified sightings ingestion and cross-validation</li>
          <li>NOAA tides and environmental correlation</li>
          <li>Orcasound hydrophone station integration</li>
          <li>Sighting probability scoring with confidence and reason codes</li>
          <li>Downloadable probability reports and CSV export</li>
          <li>REST API on AWS App Runner with scheduled ingestion</li>
        </ul>
        <p class="note">
          The chat-style map demos are scripted. The report page and CSV export call the live API on AWS.
        </p>
      </section>

      <section class="card cta-card">
        <h2>See it live</h2>
        <p>Open a probability report for this week before you reach out.</p>
        <div class="cta-actions">
          <a routerLink="/reports" class="btn btn--primary">Try a live report</a>
          <a class="btn btn--ghost" [href]="mailtoLink">contact&#64;orcast.org</a>
        </div>
      </section>

      <section class="card contact-block" id="partner-contact">
        <h2>Get in touch</h2>
        <form *ngIf="contactFormUrl" (ngSubmit)="submitContact()" class="contact-form">
          <label>
            Name
            <input type="text" [(ngModel)]="contact.name" name="name" required>
          </label>
          <label>
            Email
            <input type="email" [(ngModel)]="contact.email" name="email" required>
          </label>
          <label>
            Organization
            <input type="text" [(ngModel)]="contact.organization" name="organization">
          </label>
          <label>
            Interest
            <select [(ngModel)]="contact.interest" name="interest">
              <option value="pilot">Field pilot partner</option>
              <option value="research">Research collaboration</option>
              <option value="data">Data sharing</option>
              <option value="technical">Technical review</option>
            </select>
          </label>
          <label>
            Message
            <textarea [(ngModel)]="contact.message" name="message" rows="4" required></textarea>
          </label>
          <button type="submit" class="btn btn--primary" [disabled]="isSubmitting">
            {{ isSubmitting ? 'Sending…' : 'Request a call' }}
          </button>
          <p *ngIf="submitMessage" class="form-note">{{ submitMessage }}</p>
        </form>
        <div *ngIf="!contactFormUrl" class="mailto-fallback">
          <a class="btn btn--primary" [href]="mailtoLink">Email contact&#64;orcast.org</a>
        </div>
      </section>
    </orcast-app-shell>
  `,
  styles: [`
    .page-head {
      margin-bottom: var(--s5);
    }
    h1 { color: var(--accent); margin: 0 0 var(--s1); }
    .subtitle { color: var(--text-muted); margin: 0; }
    .card { margin-bottom: var(--s5); }
    h2 { font-size: 1.15rem; color: var(--accent); margin: 0 0 var(--s3); }
    ul { padding-left: 1.2rem; margin: 0; }
    li { margin-bottom: var(--s1); }
    .two-col {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: var(--s4);
    }
    .partner-list div { margin-bottom: var(--s3); }
    dt { font-weight: 600; }
    dd { margin: var(--s1) 0 0; color: var(--text-muted); }
    .note {
      font-size: 0.9rem;
      color: var(--text-faint);
      border-left: 3px solid var(--accent);
      padding-left: var(--s3);
      margin-top: var(--s4);
    }
    .cta-actions {
      display: flex;
      gap: var(--s3);
      flex-wrap: wrap;
      margin-top: var(--s3);
    }
    .contact-form {
      display: grid;
      gap: var(--s3);
      max-width: 480px;
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
    .form-note { font-size: 0.85rem; color: var(--text-faint); }
    .mailto-fallback { margin-top: var(--s2); }
  `]
})
export class PartnersComponent {
  contactFormUrl = environment.contactFormUrl || '';
  mailtoLink = `mailto:${environment.contactEmail || 'contact@orcast.org'}?subject=orcast%20partnership%20inquiry`;
  isSubmitting = false;
  submitMessage = '';

  contact = {
    name: '',
    email: '',
    organization: '',
    interest: 'pilot',
    message: ''
  };

  constructor(private http: HttpClient) {}

  submitContact(): void {
    if (!this.contactFormUrl) {
      return;
    }
    this.isSubmitting = true;
    const payload = {
      ...this.contact,
      _subject: 'orcast partnership inquiry'
    };
    this.http.post(this.contactFormUrl, payload, { responseType: 'text' }).subscribe({
      next: () => {
        this.submitMessage = 'Thank you — we will follow up within a few days.';
        this.isSubmitting = false;
      },
      error: () => {
        this.submitMessage = 'Send failed. Please email contact@orcast.org.';
        this.isSubmitting = false;
      }
    });
  }
}
