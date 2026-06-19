import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

import { NavHeaderComponent } from './nav-header.component';

/**
 * Shell for full-screen map pages (historical, realtime, ml-predictions).
 * Renders the shared nav bar plus a full-viewport map area, and projects
 * overlay panels into named slots so each page only owns its content.
 *
 * Usage:
 *   <orcast-map-shell currentPage="historical">
 *     <div map>
 *       <google-map ...></google-map>
 *     </div>
 *     <aside left class="map-panel map-panel--left">...</aside>
 *     <aside right class="map-panel map-panel--right">...</aside>
 *     <aside bottom-right class="map-panel map-panel--bottom-right">...</aside>
 *   </orcast-map-shell>
 */
@Component({
  selector: 'orcast-map-shell',
  standalone: true,
  imports: [CommonModule, NavHeaderComponent],
  template: `
    <div class="map-shell">
      <orcast-nav-header [currentPage]="currentPage" layout="bar"></orcast-nav-header>

      <div class="map-viewport">
        <ng-content select="[map]"></ng-content>
        <ng-content select="[left]"></ng-content>
        <ng-content select="[right]"></ng-content>
        <ng-content select="[bottom-right]"></ng-content>
        <ng-content></ng-content>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
  `]
})
export class MapShellComponent {
  @Input() currentPage = '';
}
