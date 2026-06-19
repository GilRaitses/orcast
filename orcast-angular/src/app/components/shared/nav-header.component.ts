import { Component, Input } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'orcast-nav-header',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <header class="nav-header" [class.nav-header--bar]="layout === 'bar'">
      <a routerLink="/" class="nav-brand" *ngIf="layout === 'bar'">orcast</a>
      <nav class="nav-links">
        <a routerLink="/" class="nav-btn" [class.active]="currentPage === 'home'" title="Home">
          Home
        </a>
        <a routerLink="/reports" class="nav-btn nav-btn-primary" [class.active]="currentPage === 'reports'" title="Probability report">
          Reports
        </a>
        <a routerLink="/historical" class="nav-btn" [class.active]="currentPage === 'historical'" title="Historical sightings">
          Historical
        </a>
        <a routerLink="/realtime" class="nav-btn" [class.active]="currentPage === 'realtime'" title="Recent sightings">
          Recent
        </a>
        <a routerLink="/ml-predictions" class="nav-btn" [class.active]="currentPage === 'ml-predictions'" title="Probability map">
          Score grid
        </a>
        <a routerLink="/plan" class="nav-btn" [class.active]="currentPage === 'plan'" title="Trip planner">
          Plan
        </a>
      </nav>
    </header>
  `,
  styles: [`
    .nav-header {
      position: absolute;
      top: 10px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 1100;
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
      justify-content: center;
      max-width: 95vw;
    }

    .nav-header--bar {
      position: relative;
      top: auto;
      left: auto;
      transform: none;
      flex-shrink: 0;
      width: 100%;
      max-width: none;
      flex-wrap: nowrap;
      align-items: center;
      gap: 0;
      padding: 0 12px;
      min-height: var(--nav-h, 48px);
      background: rgba(0, 16, 32, 0.96);
      border-bottom: 1px solid var(--border, rgba(79, 195, 247, 0.3));
      overflow-x: auto;
    }

    .nav-brand {
      color: var(--accent, #4fc3f7);
      font-weight: 700;
      font-size: 0.95rem;
      text-decoration: none;
      letter-spacing: 0.04em;
      margin-right: 12px;
      white-space: nowrap;
      flex-shrink: 0;
    }

    .nav-links {
      display: flex;
      gap: 4px;
      align-items: center;
      flex: 1;
      min-width: 0;
    }

    .nav-btn {
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted, #c5dff0);
      padding: 8px 12px;
      border-radius: var(--radius-sm, 6px);
      text-decoration: none;
      transition: background 0.15s, color 0.15s, border-color 0.15s;
      font-size: 0.85rem;
      white-space: nowrap;
      flex-shrink: 0;
    }

    .nav-btn-primary {
      font-weight: 600;
    }

    .nav-btn:hover {
      background: rgba(79, 195, 247, 0.15);
      color: #fff;
    }

    .nav-btn.active {
      background: var(--accent, #4fc3f7);
      color: var(--accent-ink, #001e3c);
      border-color: var(--accent, #4fc3f7);
    }

    .nav-header--bar .nav-btn {
      padding: 6px 10px;
      font-size: 0.8rem;
    }
  `]
})
export class NavHeaderComponent {
  @Input() currentPage = '';
  @Input() layout: 'overlay' | 'bar' = 'bar';
}
