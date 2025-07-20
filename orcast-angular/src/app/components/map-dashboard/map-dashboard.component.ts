import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { BackendService } from '../../services/backend.service';
import { StateService } from '../../services/state.service';

interface MapCard {
  route: string;
  icon: string;
  title: string;
  description: string;
  features: string[];
  status: 'online' | 'beta' | 'development';
}

@Component({
  selector: 'orcast-map-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="dashboard-container">
      <div class="header">
        <h1>ORCAST</h1>
        <p>Multi-Agent Whale Research Platform - Choose Your Map View</p>
      </div>
      
      <div class="map-grid">
        <div 
          *ngFor="let card of mapCards" 
          class="map-card"
          [class.beta]="card.status === 'beta'"
          [class.development]="card.status === 'development'"
          (click)="navigateToMap(card.route)">
          
          <div class="status-indicator" [class]="'status-' + card.status"></div>
          <div class="map-icon">{{ card.icon }}</div>
          <h3 class="map-title">{{ card.title }}</h3>
          <p class="map-description">{{ card.description }}</p>
          
          <ul class="map-features">
            <li *ngFor="let feature of card.features">{{ feature }}</li>
          </ul>
          
          <button class="launch-btn">Launch {{ card.title }} View</button>
        </div>
      </div>
      
      <div class="system-status" *ngIf="systemHealth">
        <h3>🏥 System Health</h3>
        <div class="health-items">
          <div class="health-item" [class.healthy]="systemHealth.backend">
            <span>Backend API:</span>
            <span>{{ systemHealth.backend ? '✅ Online' : '❌ Offline' }}</span>
          </div>
          <div class="health-item" [class.healthy]="systemHealth.redis">
            <span>Redis Cache:</span>
            <span>{{ systemHealth.redis ? '✅ Connected' : '❌ Disconnected' }}</span>
          </div>
          <div class="health-item" [class.healthy]="systemHealth.ml">
            <span>ML Models:</span>
            <span>{{ systemHealth.ml ? '✅ Ready' : '❌ Loading' }}</span>
          </div>
        </div>
      </div>
      
      <div class="footer">
        <a href="https://github.com/GilRaitses/orcast" target="_blank">GitHub Repository</a>
        <a href="/docs/README.md" target="_blank">Documentation</a>
        <a (click)="checkSystemHealth()">🔄 Refresh Health</a>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-container {
      min-height: 100vh;
      background: linear-gradient(135deg, #001e3c 0%, #003366 50%, #001e3c 100%);
      color: white;
      padding: 20px;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .header {
      text-align: center;
      margin-bottom: 40px;
    }
    
    .header h1 {
      font-size: 3rem;
      color: #4fc3f7;
      margin-bottom: 10px;
    }
    
    .header p {
      font-size: 1.2rem;
      opacity: 0.8;
    }
    
    .map-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
      gap: 30px;
      margin-bottom: 40px;
      max-width: 1200px;
      margin-left: auto;
      margin-right: auto;
    }
    
    .map-card {
      background: rgba(0, 30, 60, 0.9);
      border: 2px solid #4fc3f7;
      border-radius: 15px;
      padding: 25px;
      text-align: center;
      transition: all 0.3s ease;
      cursor: pointer;
      position: relative;
      overflow: hidden;
    }
    
    .map-card:hover {
      transform: translateY(-10px);
      box-shadow: 0 20px 40px rgba(79, 195, 247, 0.3);
      border-color: #81d4fa;
    }
    
    .map-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(79, 195, 247, 0.1), transparent);
      transition: left 0.5s;
    }
    
    .map-card:hover::before {
      left: 100%;
    }
    
    .status-indicator {
      position: absolute;
      top: 15px;
      right: 15px;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      animation: pulse 2s infinite;
    }
    
    .status-online {
      background: #4caf50;
    }
    
    .status-beta {
      background: #ff9800;
    }
    
    .status-development {
      background: #f44336;
    }
    
    .map-icon {
      font-size: 4rem;
      margin-bottom: 20px;
      display: block;
    }
    
    .map-title {
      font-size: 1.5rem;
      color: #4fc3f7;
      margin-bottom: 15px;
    }
    
    .map-description {
      font-size: 1rem;
      line-height: 1.6;
      opacity: 0.9;
      margin-bottom: 20px;
    }
    
    .map-features {
      list-style: none;
      text-align: left;
      font-size: 0.9rem;
      opacity: 0.8;
      padding: 0;
    }
    
    .map-features li {
      margin: 8px 0;
      padding-left: 20px;
      position: relative;
    }
    
    .map-features li::before {
      content: '✓';
      position: absolute;
      left: 0;
      color: #4fc3f7;
      font-weight: bold;
    }
    
    .launch-btn {
      background: #4fc3f7;
      color: #001e3c;
      border: none;
      padding: 12px 30px;
      border-radius: 25px;
      font-size: 1rem;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s ease;
      margin-top: 20px;
    }
    
    .launch-btn:hover {
      background: #81d4fa;
      transform: scale(1.05);
    }
    
    .system-status {
      max-width: 600px;
      margin: 40px auto;
      background: rgba(0, 30, 60, 0.9);
      border: 1px solid #4fc3f7;
      border-radius: 10px;
      padding: 20px;
    }
    
    .system-status h3 {
      color: #4fc3f7;
      margin-bottom: 15px;
    }
    
    .health-items {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
    }
    
    .health-item {
      display: flex;
      justify-content: space-between;
      padding: 10px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 5px;
      border: 1px solid #f44336;
    }
    
    .health-item.healthy {
      border-color: #4caf50;
    }
    
    .footer {
      text-align: center;
      margin-top: 40px;
      padding: 20px;
      border-top: 1px solid rgba(79, 195, 247, 0.3);
    }
    
    .footer a {
      color: #4fc3f7;
      text-decoration: none;
      margin: 0 15px;
      cursor: pointer;
    }
    
    .footer a:hover {
      text-decoration: underline;
    }
    
    @keyframes pulse {
      0% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.7; transform: scale(1.1); }
      100% { opacity: 1; transform: scale(1); }
    }
  `]
})
export class MapDashboardComponent implements OnInit {
  mapCards: MapCard[] = [
    {
      route: '/historical',
      icon: '📊',
      title: 'Historical Sightings',
      description: 'Visualize 473 verified orca sightings from 1990-2024 with behavioral patterns and temporal analysis.',
      features: [
        'OBIS database integration',
        'Temporal pattern analysis',
        'Behavioral classification',
        'Seasonal migration routes',
        'Pod identification data'
      ],
      status: 'online'
    },
    {
      route: '/realtime',
      icon: '🎧',
      title: 'Real-time Detection',
      description: 'Live hydrophone data from OrcaHello AI with real-time whale call detection and acoustic analysis.',
      features: [
        'Live hydrophone streams',
        'OrcaHello AI detection',
        'Acoustic pattern analysis',
        'Real-time alerts',
        'Sound classification'
      ],
      status: 'online'
    },
    {
      route: '/ml-predictions',
      icon: '🧠',
      title: 'ML Predictions',
      description: 'Advanced machine learning predictions using PINN physics-informed models and behavioral analysis.',
      features: [
        'PINN physics models',
        'Behavioral ML predictions',
        'Probability heat maps',
        'Temporal forecasting',
        'Uncertainty quantification'
      ],
      status: 'online'
    },
    {
      route: '/agent-demo',
      icon: '🤖',
      title: 'AI Agent Demo',
      description: 'Gemma 3 multi-agent orchestration for personalized San Juan Islands trip planning with orca optimization.',
      features: [
        'Natural language trip planning',
        'Multi-agent workflow coordination',
        'Personalized itinerary generation',
        'User profile & trip history',
        'Intelligent orca timing optimization'
      ],
      status: 'beta'
    }
  ];

  systemHealth: any = null;

  constructor(
    private router: Router,
    private backendService: BackendService,
    private stateService: StateService
  ) {}

  ngOnInit(): void {
    this.stateService.updateCurrentView('dashboard');
    this.checkSystemHealth();
  }

  navigateToMap(route: string): void {
    this.router.navigate([route]);
  }

  checkSystemHealth(): void {
    this.backendService.getHealth().subscribe({
      next: (health) => {
        this.systemHealth = {
          backend: true,
          redis: health.cache_stats?.connected || false,
          ml: health.ml_models?.status === 'ready' || false
        };
      },
      error: () => {
        this.systemHealth = {
          backend: false,
          redis: false,
          ml: false
        };
      }
    });
  }
} 