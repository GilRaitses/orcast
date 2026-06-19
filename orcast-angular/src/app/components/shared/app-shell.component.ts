import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { NavHeaderComponent } from './nav-header.component';

/**
 * Shell for content pages (landing, reports, partners).
 * Provides the shared top nav bar and site footer around projected content.
 *
 * Usage:
 *   <orcast-app-shell currentPage="reports">
 *     <main>...</main>
 *   </orcast-app-shell>
 */
@Component({
  selector: 'orcast-app-shell',
  standalone: true,
  imports: [CommonModule, RouterModule, NavHeaderComponent],
  template: `
    <div class="app-page">
      <orcast-nav-header [currentPage]="currentPage" layout="bar"></orcast-nav-header>

      <div class="app-page__main">
        <ng-content></ng-content>
      </div>

      <footer class="site-footer" *ngIf="showFooter">
        <p>orcast · San Juan islands pilot</p>
        <nav>
          <a routerLink="/partners">Partners</a>
          <a routerLink="/live-demo">Map demo</a>
          <a href="https://github.com/GilRaitses/orcast" target="_blank" rel="noopener">GitHub</a>
        </nav>
      </footer>
    </div>
  `,
  styles: [`
    :host { display: block; }

    .site-footer {
      max-width: 1100px;
      margin: 0 auto;
      padding: 2rem 1.5rem 3rem;
      text-align: center;
      color: var(--text-faint);
      font-size: 0.85rem;
    }

    .site-footer nav {
      display: flex;
      gap: 1rem;
      justify-content: center;
      flex-wrap: wrap;
      margin-top: 0.75rem;
    }

    .site-footer a {
      color: var(--accent);
      text-decoration: none;
    }

    .site-footer a:hover {
      text-decoration: underline;
    }
  `]
})
export class AppShellComponent {
  @Input() currentPage = '';
  @Input() showFooter = true;
}
