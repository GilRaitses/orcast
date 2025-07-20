import { Component, Input } from '@angular/core';
import { RouterModule } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'orcast-nav-header',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="nav-header">
      <a routerLink="/dashboard" class="nav-btn" [class.active]="currentPage === 'dashboard'">
        ← Dashboard
      </a>
      <a routerLink="/historical" class="nav-btn" [class.active]="currentPage === 'historical'">
        Historical
      </a>
      <a routerLink="/realtime" class="nav-btn" [class.active]="currentPage === 'realtime'">
        Real-time
      </a>
      <a routerLink="/ml-predictions" class="nav-btn" [class.active]="currentPage === 'ml-predictions'">
        ML Predictions
      </a>
    </div>
  `,
  styles: [`
    .nav-header {
      position: absolute;
      top: 10px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 1000;
      display: flex;
      gap: 5px;
    }
    
    .nav-btn {
      background: rgba(0, 30, 60, 0.9);
      border: 1px solid #4fc3f7;
      color: white;
      padding: 8px 15px;
      border-radius: 5px;
      text-decoration: none;
      margin: 0 5px;
      transition: all 0.3s ease;
      font-size: 14px;
    }
    
    .nav-btn:hover, .nav-btn.active {
      background: #4fc3f7;
      color: #001e3c;
    }
  `]
})
export class NavHeaderComponent {
  @Input() currentPage: string = '';
} 