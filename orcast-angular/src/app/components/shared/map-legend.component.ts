import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

/**
 * Shared map legend for the instrumentation encoding (visual sighting vs
 * acoustic detection vs listening station vs detection-density heat).
 * Toggle individual rows so each page only shows the layers it renders.
 */
@Component({
  selector: 'orcast-map-legend',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="map-legend card">
      <span class="legend-row" *ngIf="showVisual"><i class="dot visual"></i> Visual sighting</span>
      <span class="legend-row" *ngIf="showAcoustic"><i class="dot acoustic"></i> Acoustic detection (hydrophone)</span>
      <span class="legend-row" *ngIf="showStation"><i class="dot station"></i> Listening station</span>
      <span class="legend-row" *ngIf="showHeat"><i class="swatch heat"></i> Recent detection density</span>
    </div>
  `,
  styles: [`
    .map-legend {
      position: absolute;
      right: 12px;
      bottom: 12px;
      z-index: 1000;
      display: grid;
      gap: 4px;
      padding: 8px 12px;
      font-size: 0.78rem;
      color: var(--text-muted);
      max-width: 240px;
      background: var(--bg-panel);
      border: 1px solid var(--border-strong);
      border-radius: var(--radius);
    }
    .legend-row {
      display: flex;
      align-items: center;
      gap: 8px;
      white-space: nowrap;
    }
    .dot {
      width: 11px;
      height: 11px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .dot.visual { background: #ffb300; border: 1px solid #fff; }
    .dot.acoustic { background: transparent; border: 2px solid #4fc3f7; }
    .dot.station { background: #00e5ff; border: 1px solid #fff; border-radius: 2px; }
    .swatch.heat {
      width: 16px;
      height: 11px;
      border-radius: 2px;
      flex-shrink: 0;
      background: linear-gradient(90deg, #0078c8, #28dcaa, #ffcd00, #ff6e00);
    }
    @media (max-width: 768px) {
      .map-legend { display: none; }
    }
  `]
})
export class MapLegendComponent {
  @Input() showVisual = true;
  @Input() showAcoustic = true;
  @Input() showStation = true;
  @Input() showHeat = true;
}
