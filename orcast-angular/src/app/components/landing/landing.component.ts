import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

import { BackendService } from '../../services/backend.service';
import { environment } from '../../../environments/environment';

interface DemoLink {
  route: string;
  title: string;
  description: string;
  status: 'live' | 'prototype';
}

@Component({
  selector: 'orcast-landing',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule],
  template: `
    <div class="landing">
      <header class="hero">
        <p class="eyebrow">Salish Sea · Southern Resident orcas</p>
        <h1>ORCAST</h1>
        <p class="tagline">
          Sighting fusion and transparent probability reports for whale research,
          tour operators, and citizen science.
        </p>
        <div class="hero-actions">
          <a routerLink="/reports" class="btn primary">Try probability report</a>
          <a routerLink="/partners" class="btn secondary">Partner with us</a>
        </div>
        <p class="backend-status" *ngIf="backendStatus">
          Backend {{ backendStatus }} · {{ sightingsCount }} sightings loaded
        </p>
      </header>

      <section class="panel">
        <h2>What works today</h2>
        <p class="lead">
          ORCAST v1 combines verified research sightings, environmental context, and hydrophone
          feeds into ranked hotspot reports with reason codes and CSV export. Agent chat interfaces
          are research prototypes; the fusion pipeline below runs on AWS.
        </p>
        <ul class="capability-list">
          <li><strong>Verified OBIS backbone</strong> — cross-validated historical sightings</li>
          <li><strong>NOAA environmental data</strong> — tides and ocean conditions</li>
          <li><strong>Orcasound hydrophones</strong> — live hydrophone station metadata</li>
          <li><strong>Hotspot scoring</strong> — probability, confidence, and source counts</li>
          <li><strong>Probability reports</strong> — generate and download CSV from the live API</li>
        </ul>
      </section>

      <section class="panel">
        <h2>Live demos</h2>
        <div class="demo-grid">
          <a *ngFor="let demo of demos" [routerLink]="demo.route" class="demo-card">
            <span class="badge" [class.live]="demo.status === 'live'" [class.prototype]="demo.status === 'prototype'">
              {{ demo.status === 'live' ? 'Live API' : 'Prototype UI' }}
            </span>
            <h3>{{ demo.title }}</h3>
            <p>{{ demo.description }}</p>
          </a>
        </div>
      </section>

      <section class="panel pilot">
        <h2>Field pilot — August 2026</h2>
        <p>
          Last week of August in the San Juan archipelago. We are testing probability reports
          with researchers, tour operators, and observers in the field. Feedback welcome.
        </p>
        <a routerLink="/partners" class="btn secondary">Join the pilot</a>
      </section>

      <section class="panel contact" id="contact">
        <h2>Contact & collaborate</h2>
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
          <button type="submit" class="btn primary" [disabled]="isSubmitting">
            {{ isSubmitting ? 'Sending…' : 'Send message' }}
          </button>
          <p class="form-note" *ngIf="submitMessage">{{ submitMessage }}</p>
        </form>

        <div *ngIf="!contactFormUrl" class="mailto-fallback">
          <p>Email us directly:</p>
          <a class="btn primary" [href]="mailtoLink">contact&#64;orcast.org</a>
          <p class="form-note">
            To enable the web form, set <code>contactFormUrl</code> in your environment
            (see docs/CONTACT_FORM_SETUP.md).
          </p>
        </div>
      </section>

      <footer class="site-footer">
        <p>ORCAST · Open sighting fusion for the Salish Sea</p>
        <nav>
          <a routerLink="/partners">Partners</a>
          <a routerLink="/live-demo">Agent demo (prototype)</a>
          <a href="https://github.com/GilRaitses/orcast" target="_blank" rel="noopener">GitHub</a>
        </nav>
        <p class="footer-docs">
          Field docs: docs/field-campaign/ in the repository
          (FIELD_WEEK_RUNBOOK.md, SUMMIT_DEMO_SCRIPT.md)
        </p>
      </footer>
    </div>
  `,
  styles: [`
    .landing {
      min-height: 100vh;
      background: linear-gradient(160deg, #001e3c 0%, #0a2f52 45%, #001528 100%);
      color: #e8f4fc;
      font-family: system-ui, -apple-system, sans-serif;
      line-height: 1.5;
    }
    .hero {
      max-width: 920px;
      margin: 0 auto;
      padding: 3rem 1.5rem 2rem;
      text-align: center;
    }
    .eyebrow {
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 0.8rem;
      color: #7ec8e8;
      margin-bottom: 0.5rem;
    }
    h1 {
      font-size: 3rem;
      margin: 0 0 0.5rem;
      letter-spacing: 0.04em;
    }
    .tagline {
      font-size: 1.2rem;
      max-width: 640px;
      margin: 0 auto 1.5rem;
      color: #c5dff0;
    }
    .hero-actions {
      display: flex;
      gap: 0.75rem;
      justify-content: center;
      flex-wrap: wrap;
      margin-bottom: 1rem;
    }
    .backend-status {
      font-size: 0.85rem;
      color: #8ab4cc;
    }
    .panel {
      max-width: 920px;
      margin: 0 auto 1.5rem;
      padding: 1.5rem;
      background: rgba(0, 30, 60, 0.55);
      border: 1px solid rgba(79, 195, 247, 0.25);
      border-radius: 10px;
    }
    .panel h2 {
      margin-top: 0;
      color: #4fc3f7;
    }
    .lead { color: #c5dff0; }
    .capability-list {
      padding-left: 1.2rem;
    }
    .capability-list li { margin-bottom: 0.4rem; }
    .demo-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 1rem;
    }
    .demo-card {
      display: block;
      padding: 1rem;
      border-radius: 8px;
      border: 1px solid rgba(79, 195, 247, 0.3);
      background: rgba(0, 20, 40, 0.6);
      color: inherit;
      text-decoration: none;
      transition: border-color 0.2s, transform 0.2s;
    }
    .demo-card:hover {
      border-color: #4fc3f7;
      transform: translateY(-2px);
    }
    .demo-card h3 { margin: 0.5rem 0 0.35rem; font-size: 1rem; }
    .demo-card p { margin: 0; font-size: 0.9rem; color: #a8cce0; }
    .badge {
      display: inline-block;
      font-size: 0.7rem;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .badge.live { background: #1b5e20; color: #c8e6c9; }
    .badge.prototype { background: #4a3f00; color: #fff9c4; }
    .btn {
      display: inline-block;
      padding: 0.65rem 1.2rem;
      border-radius: 6px;
      text-decoration: none;
      font-weight: 600;
      border: none;
      cursor: pointer;
      font-size: 0.95rem;
    }
    .btn.primary {
      background: #4fc3f7;
      color: #001e3c;
    }
    .btn.secondary {
      background: transparent;
      color: #4fc3f7;
      border: 1px solid #4fc3f7;
    }
    .btn:disabled { opacity: 0.6; cursor: not-allowed; }
    .contact-form {
      display: grid;
      gap: 0.75rem;
      max-width: 520px;
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
    .form-note { font-size: 0.85rem; color: #8ab4cc; margin-top: 0.5rem; }
    .mailto-fallback { margin-top: 0.5rem; }
    .site-footer {
      max-width: 920px;
      margin: 0 auto;
      padding: 2rem 1.5rem 3rem;
      text-align: center;
      color: #7a9bb0;
      font-size: 0.85rem;
    }
    .site-footer nav {
      display: flex;
      gap: 1rem;
      justify-content: center;
      flex-wrap: wrap;
      margin: 0.75rem 0;
    }
    .site-footer a { color: #4fc3f7; }
    .footer-docs { max-width: 560px; margin: 0.75rem auto 0; }
    code { font-size: 0.8rem; }
  `]
})
export class LandingComponent implements OnInit {
  backendStatus = '';
  sightingsCount = 0;
  contactFormUrl = environment.contactFormUrl || '';
  contactEmail = environment.contactEmail || 'contact@orcast.org';
  mailtoLink = `mailto:${environment.contactEmail || 'contact@orcast.org'}?subject=ORCAST%20collaboration`;
  isSubmitting = false;
  submitMessage = '';

  contact = {
    name: '',
    email: '',
    organization: '',
    interest: 'pilot',
    message: ''
  };

  demos: DemoLink[] = [
    {
      route: '/reports',
      title: 'Probability report',
      description: 'Generate ranked hotspots with reason codes and CSV export.',
      status: 'live'
    },
    {
      route: '/historical',
      title: 'Historical sightings',
      description: 'Verified OBIS backbone and validated observation map.',
      status: 'live'
    },
    {
      route: '/ml-predictions',
      title: 'Spatial forecast grid',
      description: 'Probability surface over the archipelago.',
      status: 'live'
    },
    {
      route: '/realtime',
      title: 'Recent sightings',
      description: 'Historical sighting overlays — not live acoustic detections.',
      status: 'live'
    },
    {
      route: '/agent-spatial-demo',
      title: 'Spatial agent demo',
      description: 'Interactive map with agent-assisted overlays.',
      status: 'prototype'
    },
    {
      route: '/live-demo',
      title: 'Live AI demo',
      description: 'Hackathon agent coordination UI (simulated agents).',
      status: 'prototype'
    }
  ];

  constructor(
    private backendService: BackendService,
    private http: HttpClient
  ) {}

  ngOnInit(): void {
    this.backendService.getHealth().subscribe({
      next: (health) => {
        this.backendStatus = health.status || 'connected';
        this.sightingsCount = health.sightings_loaded ?? 0;
      },
      error: () => {
        this.backendStatus = 'offline (try cached local demo)';
      }
    });
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
      _subject: 'ORCAST collaboration inquiry'
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
