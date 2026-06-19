import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

/**
 * A titled panel section that can collapse its body.
 * Defaults to collapsed on narrow viewports so map controls do not
 * dominate the screen on phones.
 *
 * Usage:
 *   <orcast-collapsible-panel title="Filters">
 *     ...controls...
 *   </orcast-collapsible-panel>
 */
@Component({
  selector: 'orcast-collapsible-panel',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="cp">
      <button
        type="button"
        class="cp__header"
        [attr.aria-expanded]="open"
        (click)="toggle()">
        <span>{{ title }}</span>
        <span class="cp__chevron" [class.cp__chevron--open]="open">›</span>
      </button>
      <div class="cp__body" *ngIf="open">
        <ng-content></ng-content>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }

    .cp__header {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: transparent;
      border: none;
      color: var(--accent);
      font-size: 0.9rem;
      font-weight: 600;
      padding: 8px 0;
      cursor: pointer;
    }

    .cp__chevron {
      transition: transform 0.2s;
      display: inline-block;
      transform: rotate(90deg);
      opacity: 0.8;
    }

    .cp__chevron--open {
      transform: rotate(-90deg);
    }

    .cp__body {
      padding-top: 4px;
    }
  `]
})
export class CollapsiblePanelComponent {
  @Input() title = '';
  @Input() open = true;

  toggle(): void {
    this.open = !this.open;
  }
}
