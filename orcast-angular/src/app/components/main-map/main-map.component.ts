import { Component, OnInit, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'orcast-main-map',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="main-container">
      <!-- Left Sidebar -->
      <div class="sidebar">
        <div class="logo-section">
          <h1>ORCAST</h1>
          <p>Orca Behavioral Analysis</p>
        </div>
        
        <div class="time-controls">
          <h3>TIME UNIT</h3>
          <div class="time-buttons">
            <button class="time-btn" [class.active]="timeUnit === 'weeks'" (click)="setTimeUnit('weeks')">Weeks</button>
            <button class="time-btn" [class.active]="timeUnit === 'months'" (click)="setTimeUnit('months')">Months</button>
            <button class="time-btn" [class.active]="timeUnit === 'years'" (click)="setTimeUnit('years')">Years</button>
          </div>
          <div class="time-slider">
            <input type="range" min="0" max="100" [value]="currentMonth" (input)="updateTime($event)">
            <p>Current Month</p>
          </div>
        </div>
        
        <div class="navigation-controls">
          <h3>QUICK NAVIGATE</h3>
          <div class="nav-buttons">
            <button class="nav-btn">-3</button>
            <button class="nav-btn">-1</button>
            <button class="nav-btn">+1</button>
          </div>
        </div>
        
        <div class="probability-controls">
          <h3>PROBABILITY THRESHOLD: MEDIUM</h3>
          <div class="threshold-slider">
            <input type="range" min="0" max="100" [value]="probabilityThreshold" (input)="updateThreshold($event)">
            <div class="threshold-labels">
              <span>Low</span>
              <span>High</span>
            </div>
          </div>
        </div>
        
        <div class="forecast-controls">
          <h3>🌊 Forecast Layers</h3>
          <div class="forecast-options">
            <label><input type="checkbox" [checked]="layers.highTemporal" (change)="toggleLayer('highTemporal')"> High Temporal Resolution</label>
            <label><input type="checkbox" [checked]="layers.highSpatial" (change)="toggleLayer('highSpatial')"> High Spatial Resolution</label>
            <label><input type="checkbox" [checked]="layers.overview" (change)="toggleLayer('overview')"> 📊 Overview Forecast</label>
            <label><input type="checkbox" [checked]="layers.aiAssistant" (change)="toggleLayer('aiAssistant')"> 🤖 AI Assistant</label>
          </div>
        </div>
      </div>
      
      <!-- Main Map Area -->
      <div class="map-container">
        <div id="map" #mapElement></div>
        <div class="map-loading" *ngIf="isMapLoading">
          <p>Map Loading Error</p>
          <p>Unable to load Google Maps</p>
          <p>Please refresh the page</p>
        </div>
      </div>
      
      <!-- AI Agent Panel -->
      <div class="agent-panel" [class.open]="agentPanelOpen">
        <div class="panel-header">
          <h3>🤖 AI Agent Assistant</h3>
          <button class="close-btn" (click)="toggleAgentPanel()">×</button>
        </div>
        
        <div class="heat-map-controls">
          <h4>🔥 Heat Map Layers</h4>
          <div class="layer-buttons">
            <button class="layer-btn active">ML Predictions</button>
            <button class="layer-btn">PINN Forecast</button>
          </div>
          <div class="prediction-types">
            <button class="pred-btn">Environmental</button>
            <button class="pred-btn">Behavioral</button>
          </div>
        </div>
        
        <div class="agent-status">
          <p>🤖 ORCAST Agent Ready</p>
          <p>Ask me to identify hotspots, generate focused forecasts, or analyze patterns!</p>
        </div>
        
        <div class="agent-input">
          <input type="text" placeholder="Find best whale watching spots for tomorrow" [value]="agentQuery" (input)="updateQuery($event)">
          <div class="quick-actions">
            <button class="action-btn">❤️ Find Hotspots</button>
            <button class="action-btn">📊 Focused Forecast</button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .main-container {
      display: flex;
      height: 100vh;
      background: #000;
      color: white;
      font-family: 'Arial', sans-serif;
    }
    
    .sidebar {
      width: 280px;
      background: rgba(0, 30, 60, 0.95);
      padding: 20px;
      overflow-y: auto;
      border-right: 1px solid #4fc3f7;
    }
    
    .logo-section h1 {
      color: #4fc3f7;
      font-size: 2rem;
      margin: 0 0 5px 0;
    }
    
    .logo-section p {
      color: #ccc;
      margin: 0 0 30px 0;
      font-size: 0.9rem;
    }
    
    .time-controls, .navigation-controls, .probability-controls, .forecast-controls {
      margin-bottom: 30px;
    }
    
    .time-controls h3, .navigation-controls h3, .probability-controls h3, .forecast-controls h3 {
      color: #4fc3f7;
      font-size: 0.8rem;
      margin-bottom: 15px;
      font-weight: bold;
    }
    
    .time-buttons {
      display: flex;
      gap: 5px;
      margin-bottom: 15px;
    }
    
    .time-btn {
      flex: 1;
      padding: 8px;
      background: rgba(79, 195, 247, 0.2);
      border: 1px solid #4fc3f7;
      color: white;
      border-radius: 4px;
      cursor: pointer;
    }
    
    .time-btn.active {
      background: #4fc3f7;
      color: #000;
    }
    
    .nav-buttons {
      display: flex;
      gap: 10px;
    }
    
    .nav-btn {
      padding: 8px 15px;
      background: rgba(79, 195, 247, 0.2);
      border: 1px solid #4fc3f7;
      color: white;
      border-radius: 4px;
      cursor: pointer;
    }
    
    .time-slider input, .threshold-slider input {
      width: 100%;
      margin-bottom: 10px;
    }
    
    .threshold-labels {
      display: flex;
      justify-content: space-between;
      font-size: 0.8rem;
      color: #ccc;
    }
    
    .forecast-options {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    
    .forecast-options label {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      font-size: 0.9rem;
    }
    
    .map-container {
      flex: 1;
      position: relative;
      background: #001122;
    }
    
    #map {
      width: 100%;
      height: 100%;
    }
    
    .map-loading {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      text-align: center;
      color: #ff4444;
    }
    
    .agent-panel {
      position: fixed;
      top: 20px;
      right: 20px;
      width: 350px;
      background: rgba(0, 30, 60, 0.95);
      border: 1px solid #4fc3f7;
      border-radius: 8px;
      padding: 15px;
      z-index: 1000;
      max-height: calc(100vh - 40px);
      overflow-y: auto;
    }
    
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
    }
    
    .panel-header h3 {
      margin: 0;
      color: #4fc3f7;
    }
    
    .close-btn {
      background: none;
      border: none;
      color: white;
      font-size: 1.5rem;
      cursor: pointer;
    }
    
    .layer-buttons, .prediction-types {
      display: flex;
      gap: 5px;
      margin-bottom: 10px;
    }
    
    .layer-btn, .pred-btn {
      padding: 6px 12px;
      background: rgba(79, 195, 247, 0.2);
      border: 1px solid #4fc3f7;
      color: white;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.8rem;
    }
    
    .layer-btn.active {
      background: #4fc3f7;
      color: #000;
    }
    
    .agent-status {
      background: rgba(0, 0, 0, 0.3);
      padding: 10px;
      border-radius: 5px;
      margin: 15px 0;
      font-size: 0.9rem;
    }
    
    .agent-input input {
      width: 100%;
      padding: 8px;
      background: rgba(0, 0, 0, 0.5);
      border: 1px solid #4fc3f7;
      color: white;
      border-radius: 4px;
      margin-bottom: 10px;
    }
    
    .quick-actions {
      display: flex;
      gap: 5px;
    }
    
    .action-btn {
      flex: 1;
      padding: 6px;
      background: rgba(79, 195, 247, 0.2);
      border: 1px solid #4fc3f7;
      color: white;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.8rem;
    }
  `]
})
export class MainMapComponent implements OnInit, AfterViewInit {
  timeUnit = 'months';
  currentMonth = 50;
  probabilityThreshold = 50;
  agentPanelOpen = true;
  isMapLoading = false;
  agentQuery = '';
  
  layers = {
    highTemporal: true,
    highSpatial: true,
    overview: true,
    aiAssistant: true
  };

  ngOnInit() {
    // Initialize component
  }

  ngAfterViewInit() {
    this.initializeMap();
  }

  initializeMap() {
    // Check if Google Maps API is available
    if (typeof google !== 'undefined' && google.maps) {
      const map = new google.maps.Map(document.getElementById('map')!, {
        center: { lat: 48.5465, lng: -123.0095 }, // San Juan Islands
        zoom: 10,
        styles: [
          {
            "elementType": "geometry",
            "stylers": [{"color": "#242f3e"}]
          },
          {
            "elementType": "labels.text.stroke",
            "stylers": [{"color": "#242f3e"}]
          },
          {
            "elementType": "labels.text.fill",
            "stylers": [{"color": "#746855"}]
          }
        ]
      });
    } else {
      this.isMapLoading = true;
      // Try to load Google Maps
      this.loadGoogleMaps();
    }
  }

  loadGoogleMaps() {
    const script = document.createElement('script');
    script.src = 'https://maps.googleapis.com/maps/api/js?key=AIzaSyD9aM6oj1wpVG-VungMtIpyNWeHp3Q7XjU&callback=initMap';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);
    
    // Set global callback
    (window as any).initMap = () => {
      this.isMapLoading = false;
      this.initializeMap();
    };
  }

  setTimeUnit(unit: string) {
    this.timeUnit = unit;
  }

  updateTime(event: any) {
    this.currentMonth = event.target.value;
  }

  updateThreshold(event: any) {
    this.probabilityThreshold = event.target.value;
  }

  toggleLayer(layer: string) {
    this.layers = { ...this.layers, [layer]: !this.layers[layer as keyof typeof this.layers] };
  }

  toggleAgentPanel() {
    this.agentPanelOpen = !this.agentPanelOpen;
  }

  updateQuery(event: any) {
    this.agentQuery = event.target.value;
  }
} 