import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

import { environment } from '../../../environments/environment';

@Component({
  selector: 'orcast-partners',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  template: `
    <div class="partners-page">
      <header>
        <a routerLink="/" class="back">← Home</a>
        <h1>Partner with ORCAST</h1>
        <p class="subtitle">Executive summary for research, conservation, and field pilot partners</p>
      </header>

      <section>
        <h2>Executive summary</h2>
        <p>
          ORCAST combines verified marine mammal sightings, environmental data, and acoustic
          context into transparent probability reports for the Salish Sea. We are seeking pilot
          partners for an August 2026 field week in the San Juan archipelago.
        </p>
      </section>

      <section>
        <h2>What we offer</h2>
        <ul>
          <li>Multi-source sighting fusion with cross-validation and source attribution</li>
          <li>Ranked hotspot probability reports with downloadable CSV</li>
          <li>Open pipeline on AWS with documented data sources</li>
          <li>Field pilot support and feedback-driven iteration</li>
          <li>Publication and co-authorship opportunities for validated pilots</li>
        </ul>
      </section>

      <section>
        <h2>What we seek</h2>
        <ul>
          <li>Research groups with verified sighting datasets or DTAG deployments</li>
          <li>Tour operators and naturalists willing to test reports in the field</li>
          <li>Citizen science networks (iNaturalist, Orca Network, Orcasound)</li>
          <li>Technical reviewers for scoring methodology and validation rules</li>
        </ul>
      </section>

      <section>
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

      <section>
        <h2>Technical capabilities (live today)</h2>
        <ul>
          <li>OBIS verified sightings ingestion and cross-validation</li>
          <li>NOAA tides and environmental correlation</li>
          <li>Orcasound hydrophone station integration</li>
          <li>Hotspot probability scoring with confidence and reason codes</li>
          <li>REST API on AWS App Runner with scheduled ingestion</li>
        </ul>
        <p class="note">
          Agent chat and GPU-accelerated PINN demos are research prototypes, not production services.
        </p>
      </section>

      <section class="contact-block" id="partner-contact">
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
          <button type="submit" class="btn" [disabled]="isSubmitting">
            {{ isSubmitting ? 'Sending…' : 'Request a call' }}
          </button>
          <p *ngIf="submitMessage" class="form-note">{{ submitMessage }}</p>
        </form>
        <div *ngIf="!contactFormUrl">
          <a class="btn" [href]="mailtoLink">Email contact&#64;orcast.org</a>
        </div>
      </section>

      <footer>
        <a routerLink="/">Return to home</a>
        ·
        <a routerLink="/reports">Try a live report</a>
      </footer>
    </div>
  `,
  styles: [`
    .partners-page {
      max-width: 760px;
      margin: 0 auto;
      padding: 2rem 1.5rem 3rem;
      background: #001e3c;
      color: #e8f4fc;
      min-height: 100vh;
      font-family: system-ui, -apple-system, sans-serif;
      line-height: 1.6;
    }
    .back {
      color: #4fc3f7;
      text-decoration: none;
      font-size: 0.9rem;
    }
    h1 { color: #4fc3f7; margin-bottom: 0.25rem; }
    .subtitle { color: #a8cce0; margin-top: 0; }
    section { margin-bottom: 2rem; }
    h2 { font-size: 1.15rem; color: #7ec8e8; margin-bottom: 0.5rem; }
    ul { padding-left: 1.2rem; }
    li { margin-bottom: 0.35rem; }
    .partner-list div { margin-bottom: 0.75rem; }
    dt { font-weight: 600; }
    dd { margin: 0.15rem 0 0; color: #a8cce0; }
    .note {
      font-size: 0.9rem;
      color: #8ab4cc;
      border-left: 3px solid #4fc3f7;
      padding-left: 0.75rem;
    }
    .contact-form {
      display: grid;
      gap: 0.75rem;
      max-width: 480px;
    }
    .contact-form label {
      display: grid;
      gap: 0.25rem;
      font-size: 0.9rem;
    }
    .contact-form input,
    .contact-form select,
    .contact-form textarea {
      padding: 0.5rem;
      border-radius: 4px;
      border: 1px solid #2a5a7a;
      background: #001528;
      color: #e8f4fc;
    }
    .btn {
      display: inline-block;
      padding: 0.6rem 1.1rem;
      background: #4fc3f7;
      color: #001e3c;
      border: none;
      border-radius: 6px;
      font-weight: 600;
      cursor: pointer;
      text-decoration: none;
    }
    .btn:disabled { opacity: 0.6; }
    .form-note { font-size: 0.85rem; color: #8ab4cc; }
    footer {
      margin-top: 2rem;
      padding-top: 1rem;
      border-top: 1px solid rgba(79, 195, 247, 0.2);
      font-size: 0.9rem;
    }
    footer a { color: #4fc3f7; }
  `]
})
export class PartnersComponent {
  contactFormUrl = environment.contactFormUrl || '';
  mailtoLink = `mailto:${environment.contactEmail || 'contact@orcast.org'}?subject=ORCAST%20partnership%20inquiry`;
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
      _subject: 'ORCAST partnership inquiry'
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
