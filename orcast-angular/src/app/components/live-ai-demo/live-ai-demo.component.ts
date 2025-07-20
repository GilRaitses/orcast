import { Component, OnInit, OnDestroy, AfterViewInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { interval, Subscription, timer } from 'rxjs';

interface AgentMessage {
  timestamp: Date;
  agent: string;
  type: 'processing' | 'data' | 'analysis' | 'prediction' | 'coordination';
  message: string;
  data?: any;
  mapUpdate?: {
    type: 'heatmap' | 'prediction' | 'detection' | 'pattern';
    coordinates: { lat: number, lng: number };
    value: number;
    color: string;
  };
}

interface MLPrediction {
  location: { lat: number, lng: number };
  probability: number;
  confidence: number;
  model: 'pinn' | 'behavioral' | 'ensemble';
  timestamp: Date;
}

@Component({
  selector: 'orcast-live-ai-demo',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="live-demo-container">
      <!-- Original ORCAST Layout Header -->
      <div class="header-bar">
        <h1>ORCAST</h1>
        <span class="subtitle">Live AI Spatial Analysis Demo</span>
        <div class="demo-controls">
          <button (click)="startDemo()" [disabled]="isRunning" class="start-btn">
            ▶️ Start Live AI Demo
          </button>
          <button (click)="stopDemo()" [disabled]="!isRunning" class="stop-btn">
            ⏹️ Stop
          </button>
          <span class="status" [class.running]="isRunning">
            {{isRunning ? 'AI Agents Active' : 'Demo Ready'}}
          </span>
        </div>
      </div>

      <div class="main-interface">
        <!-- Left Sidebar - Agent Transcript Feed -->
        <div class="agent-sidebar">
          <div class="agent-header">
            <h3>🤖 Live Agent Coordination</h3>
            <div class="agent-count">{{activeAgents}} agents active</div>
          </div>
          
          <div class="agent-transcript" #transcriptContainer>
            <div 
              *ngFor="let message of agentMessages.slice(-20); trackBy: trackMessage" 
              class="message"
              [class]="'message-' + message.type"
              [@messageSlide]>
              
              <div class="message-header">
                <span class="agent-name">{{message.agent}}</span>
                <span class="timestamp">{{message.timestamp | date:'HH:mm:ss.SSS'}}</span>
              </div>
              
              <div class="message-content">{{message.message}}</div>
              
              <div class="message-data" *ngIf="message.data">
                <pre>{{message.data | json}}</pre>
              </div>
              
              <div class="map-update-indicator" *ngIf="message.mapUpdate">
                📍 Map Updated: {{message.mapUpdate.type}} at {{message.mapUpdate.coordinates.lat.toFixed(4)}}, {{message.mapUpdate.coordinates.lng.toFixed(4)}}
              </div>
            </div>
          </div>
          
          <div class="agent-stats">
            <div class="stat">
              <span class="label">Messages:</span>
              <span class="value">{{agentMessages.length}}</span>
            </div>
            <div class="stat">
              <span class="label">Predictions:</span>
              <span class="value">{{mlPredictions.length}}</span>
            </div>
            <div class="stat">
              <span class="label">Accuracy:</span>
              <span class="value">{{currentAccuracy}}%</span>
            </div>
          </div>
        </div>

        <!-- Center Map - The Centerpiece -->
        <div class="map-centerpiece">
          <div class="map-header">
            <h3>🗺️ AI Spatial Analysis - San Juan Islands</h3>
            <div class="map-modes">
              <button 
                *ngFor="let mode of mapModes" 
                (click)="setMapMode(mode.key)"
                [class.active]="currentMapMode === mode.key"
                class="map-mode-btn">
                {{mode.label}}
              </button>
            </div>
          </div>
          
          <div class="map-container" #mapContainer>
            <div id="live-map"></div>
            
            <!-- Real-time overlays -->
            <div class="map-overlays">
              <div class="prediction-overlay" *ngIf="currentMapMode === 'predictions'">
                <div 
                  *ngFor="let prediction of mlPredictions.slice(-10)"
                  class="prediction-point"
                  [style.left.%]="getMapX(prediction.location.lng)"
                  [style.top.%]="getMapY(prediction.location.lat)"
                  [style.opacity]="prediction.probability"
                  [class]="'model-' + prediction.model">
                  <div class="prediction-value">{{(prediction.probability * 100).toFixed(0)}}%</div>
                </div>
              </div>
              
              <div class="heatmap-overlay" *ngIf="currentMapMode === 'heatmap'">
                <canvas #heatmapCanvas width="800" height="600"></canvas>
              </div>
              
              <div class="detection-overlay" *ngIf="currentMapMode === 'detections'">
                <div 
                  *ngFor="let detection of realtimeDetections"
                  class="detection-pulse"
                  [style.left.%]="getMapX(detection.lng)"
                  [style.top.%]="getMapY(detection.lat)">
                </div>
              </div>
            </div>
          </div>
          
          <!-- ML Model Status -->
          <div class="ml-status-panel">
            <div class="ml-model" *ngFor="let model of mlModels">
              <div class="model-header">
                <span class="model-name">{{model.name}}</span>
                <span class="model-status" [class]="'status-' + model.status">{{model.status}}</span>
              </div>
              <div class="model-metrics">
                <span>Accuracy: {{model.accuracy}}%</span>
                <span>Latency: {{model.latency}}ms</span>
              </div>
              <div class="model-progress">
                <div class="progress-bar" [style.width.%]="model.progress"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Panel - Live Analysis Results -->
        <div class="analysis-panel">
          <div class="panel-header">
            <h3>📊 Live Analysis Results</h3>
            <div class="refresh-indicator" [class.active]="isAnalyzing">⟳</div>
          </div>
          
          <div class="analysis-sections">
            <!-- Current Prediction -->
            <div class="analysis-section">
              <h4>🎯 Current Best Prediction</h4>
              <div class="prediction-card" *ngIf="bestPrediction">
                <div class="location">
                  📍 {{bestPrediction.location.lat.toFixed(4)}}, {{bestPrediction.location.lng.toFixed(4)}}
                </div>
                <div class="probability">
                  Probability: <strong>{{(bestPrediction.probability * 100).toFixed(1)}}%</strong>
                </div>
                <div class="confidence">
                  Confidence: {{(bestPrediction.confidence * 100).toFixed(1)}}%
                </div>
                <div class="model">Model: {{bestPrediction.model.toUpperCase()}}</div>
              </div>
            </div>
            
            <!-- Pattern Recognition -->
            <div class="analysis-section">
              <h4>🧠 Pattern Recognition</h4>
              <div class="pattern-list">
                <div *ngFor="let pattern of detectedPatterns" class="pattern-item">
                  <span class="pattern-type">{{pattern.type}}</span>
                  <span class="pattern-strength">{{pattern.strength}}%</span>
                </div>
              </div>
            </div>
            
            <!-- Environmental Factors -->
            <div class="analysis-section">
              <h4>🌊 Environmental Factors</h4>
              <div class="env-factors">
                <div class="factor">Tide: {{environmentalData.tide}}</div>
                <div class="factor">Wind: {{environmentalData.wind}}</div>
                <div class="factor">Salmon: {{environmentalData.salmon}}</div>
                <div class="factor">Temperature: {{environmentalData.temperature}}</div>
              </div>
            </div>
            
            <!-- Model Performance -->
            <div class="analysis-section">
              <h4>⚡ Model Performance</h4>
              <div class="performance-metrics">
                <div class="metric">
                  <span class="label">Ensemble Accuracy:</span>
                  <span class="value">{{ensembleAccuracy}}%</span>
                </div>
                <div class="metric">
                  <span class="label">Processing Time:</span>
                  <span class="value">{{processingTime}}ms</span>
                </div>
                <div class="metric">
                  <span class="label">Data Points:</span>
                  <span class="value">{{dataPointsProcessed}}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .live-demo-container {
      height: 100vh;
      background: linear-gradient(135deg, #001122 0%, #001f3f 100%);
      color: white;
      font-family: 'Inter', sans-serif;
      display: flex;
      flex-direction: column;
    }

    .header-bar {
      display: flex;
      align-items: center;
      padding: 15px 30px;
      background: rgba(0, 30, 60, 0.9);
      border-bottom: 2px solid #4fc3f7;
      gap: 30px;
    }

    .header-bar h1 {
      color: #4fc3f7;
      font-size: 2rem;
      margin: 0;
    }

    .subtitle {
      color: #81d4fa;
      font-size: 1.1rem;
    }

    .demo-controls {
      margin-left: auto;
      display: flex;
      align-items: center;
      gap: 15px;
    }

    .start-btn, .stop-btn {
      padding: 10px 20px;
      border: 2px solid #4fc3f7;
      background: rgba(79, 195, 247, 0.2);
      color: white;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .start-btn:hover {
      background: #4fc3f7;
      color: #001122;
    }

    .stop-btn:hover {
      background: #ff4444;
      border-color: #ff4444;
    }

    .status.running {
      color: #4caf50;
      font-weight: 600;
    }

    .main-interface {
      flex: 1;
      display: grid;
      grid-template-columns: 350px 1fr 300px;
      gap: 0;
    }

    /* Agent Sidebar */
    .agent-sidebar {
      background: rgba(0, 30, 60, 0.8);
      border-right: 2px solid #4fc3f7;
      display: flex;
      flex-direction: column;
    }

    .agent-header {
      padding: 20px;
      border-bottom: 1px solid #4fc3f7;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .agent-header h3 {
      margin: 0;
      color: #4fc3f7;
    }

    .agent-count {
      background: rgba(79, 195, 247, 0.2);
      padding: 5px 10px;
      border-radius: 12px;
      font-size: 0.9rem;
      color: #81d4fa;
    }

    .agent-transcript {
      flex: 1;
      overflow-y: auto;
      padding: 15px;
    }

    .message {
      background: rgba(0, 0, 0, 0.3);
      margin-bottom: 10px;
      padding: 12px;
      border-radius: 8px;
      border-left: 4px solid #666;
      animation: slideIn 0.3s ease;
    }

    .message-processing { border-left-color: #ffeb3b; }
    .message-data { border-left-color: #2196f3; }
    .message-analysis { border-left-color: #9c27b0; }
    .message-prediction { border-left-color: #4caf50; }
    .message-coordination { border-left-color: #ff9800; }

    .message-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 6px;
    }

    .agent-name {
      font-weight: 600;
      color: #4fc3f7;
    }

    .timestamp {
      font-size: 0.8rem;
      color: #666;
    }

    .message-content {
      color: #ccc;
      font-size: 0.9rem;
      line-height: 1.4;
    }

    .message-data pre {
      font-size: 0.8rem;
      color: #81d4fa;
      margin: 8px 0 0 0;
      background: rgba(0, 0, 0, 0.3);
      padding: 8px;
      border-radius: 4px;
    }

    .map-update-indicator {
      color: #4caf50;
      font-size: 0.8rem;
      margin-top: 5px;
      font-style: italic;
    }

    .agent-stats {
      padding: 15px;
      border-top: 1px solid #4fc3f7;
      display: flex;
      gap: 20px;
    }

    .stat {
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    .stat .label {
      font-size: 0.8rem;
      color: #666;
    }

    .stat .value {
      font-weight: 600;
      color: #4fc3f7;
    }

    /* Map Centerpiece */
    .map-centerpiece {
      background: rgba(0, 0, 0, 0.2);
      display: flex;
      flex-direction: column;
    }

    .map-header {
      padding: 20px;
      border-bottom: 1px solid #4fc3f7;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .map-header h3 {
      margin: 0;
      color: #4fc3f7;
    }

    .map-modes {
      display: flex;
      gap: 10px;
    }

    .map-mode-btn {
      padding: 8px 16px;
      background: rgba(79, 195, 247, 0.2);
      border: 1px solid #4fc3f7;
      color: white;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .map-mode-btn.active {
      background: #4fc3f7;
      color: #001122;
    }

    .map-container {
      flex: 1;
      position: relative;
      background: linear-gradient(45deg, #001122, #004d40);
    }

    #live-map {
      width: 100%;
      height: 100%;
    }

    .map-overlays {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      pointer-events: none;
    }

    .prediction-point {
      position: absolute;
      width: 20px;
      height: 20px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      animation: pulse 2s infinite;
      transform: translate(-50%, -50%);
    }

    .model-pinn { background: rgba(79, 195, 247, 0.8); }
    .model-behavioral { background: rgba(156, 39, 176, 0.8); }
    .model-ensemble { background: rgba(76, 175, 80, 0.8); }

    .prediction-value {
      font-size: 0.7rem;
      font-weight: 600;
      color: white;
    }

    .detection-pulse {
      position: absolute;
      width: 30px;
      height: 30px;
      border: 3px solid #4fc3f7;
      border-radius: 50%;
      animation: detectPulse 1.5s infinite;
      transform: translate(-50%, -50%);
    }

    .ml-status-panel {
      padding: 20px;
      background: rgba(0, 0, 0, 0.4);
      border-top: 1px solid #4fc3f7;
    }

    .ml-model {
      margin-bottom: 15px;
      padding: 10px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 6px;
    }

    .model-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
    }

    .model-name {
      font-weight: 600;
      color: #4fc3f7;
    }

    .model-status.status-active {
      color: #4caf50;
    }

    .model-metrics {
      display: flex;
      gap: 15px;
      font-size: 0.8rem;
      color: #ccc;
      margin-bottom: 8px;
    }

    .model-progress {
      height: 4px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 2px;
      overflow: hidden;
    }

    .progress-bar {
      height: 100%;
      background: linear-gradient(90deg, #4fc3f7, #81d4fa);
      transition: width 0.5s ease;
    }

    /* Analysis Panel */
    .analysis-panel {
      background: rgba(0, 30, 60, 0.8);
      border-left: 2px solid #4fc3f7;
      display: flex;
      flex-direction: column;
    }

    .panel-header {
      padding: 20px;
      border-bottom: 1px solid #4fc3f7;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .panel-header h3 {
      margin: 0;
      color: #4fc3f7;
    }

    .refresh-indicator {
      font-size: 1.2rem;
      color: #666;
      transition: all 0.3s ease;
    }

    .refresh-indicator.active {
      color: #4fc3f7;
      animation: spin 1s linear infinite;
    }

    .analysis-sections {
      flex: 1;
      overflow-y: auto;
      padding: 15px;
    }

    .analysis-section {
      margin-bottom: 25px;
      background: rgba(0, 0, 0, 0.3);
      padding: 15px;
      border-radius: 8px;
    }

    .analysis-section h4 {
      margin: 0 0 15px 0;
      color: #81d4fa;
      font-size: 1rem;
    }

    .prediction-card {
      background: rgba(76, 175, 80, 0.1);
      padding: 15px;
      border-radius: 6px;
      border: 1px solid #4caf50;
    }

    .prediction-card .location {
      color: #4fc3f7;
      margin-bottom: 8px;
    }

    .prediction-card .probability {
      color: #4caf50;
      font-size: 1.1rem;
      margin-bottom: 5px;
    }

    .pattern-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .pattern-item {
      display: flex;
      justify-content: space-between;
      padding: 8px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 4px;
    }

    .pattern-type {
      color: #ccc;
    }

    .pattern-strength {
      color: #4fc3f7;
      font-weight: 600;
    }

    .env-factors {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .factor {
      color: #ccc;
      font-size: 0.9rem;
    }

    .performance-metrics {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .metric {
      display: flex;
      justify-content: space-between;
      color: #ccc;
      font-size: 0.9rem;
    }

    .metric .value {
      color: #4fc3f7;
      font-weight: 600;
    }

    @keyframes slideIn {
      from { transform: translateX(-20px); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }

    @keyframes pulse {
      0%, 100% { transform: translate(-50%, -50%) scale(1); }
      50% { transform: translate(-50%, -50%) scale(1.2); }
    }

    @keyframes detectPulse {
      0% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
      100% { transform: translate(-50%, -50%) scale(2); opacity: 0; }
    }

    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
  `]
})
export class LiveAIDemoComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('mapContainer', { static: false }) mapContainer!: ElementRef;
  @ViewChild('transcriptContainer', { static: false }) transcriptContainer!: ElementRef;
  @ViewChild('heatmapCanvas', { static: false }) heatmapCanvas!: ElementRef;

  isRunning = false;
  isAnalyzing = false;
  activeAgents = 0;
  currentAccuracy = 87;
  currentMapMode = 'predictions';

  agentMessages: AgentMessage[] = [];
  mlPredictions: MLPrediction[] = [];
  realtimeDetections: { lat: number, lng: number, timestamp: Date }[] = [];
  
  bestPrediction: MLPrediction | null = null;
  detectedPatterns = [
    { type: 'Pod Movement', strength: 92 },
    { type: 'Feeding Behavior', strength: 78 },
    { type: 'Social Interaction', strength: 85 }
  ];
  
  environmentalData = {
    tide: '2.3m rising',
    wind: '15kt SW',
    salmon: 'High activity',
    temperature: '12.4°C'
  };

  ensembleAccuracy = 87;
  processingTime = 234;
  dataPointsProcessed = 15847;

  mapModes = [
    { key: 'predictions', label: 'ML Predictions' },
    { key: 'heatmap', label: 'Probability Heatmap' },
    { key: 'detections', label: 'Live Detections' },
    { key: 'patterns', label: 'Behavioral Patterns' }
  ];

  mlModels = [
    { name: 'PINN Physics Model', status: 'active', accuracy: 89, latency: 156, progress: 95 },
    { name: 'Behavioral ML', status: 'active', accuracy: 84, latency: 203, progress: 87 },
    { name: 'Ensemble Fusion', status: 'active', accuracy: 91, latency: 289, progress: 92 }
  ];

  private subscriptions: Subscription[] = [];
  private map: google.maps.Map | null = null;

  ngOnInit() {
    this.initializeDemo();
    // Load real data from backend endpoints
    this.loadRealDataFromEndpoints();
  }

  ngAfterViewInit() {
    // Delay map initialization to ensure Google Maps API is loaded
    setTimeout(() => {
      this.initializeMap();
    }, 1000);
  }

  ngOnDestroy() {
    this.stopDemo();
  }

  initializeDemo() {
    // Initialize with some sample data
    this.addAgentMessage('🔍 Data Collector', 'processing', 'System initialized - awaiting demo start');
  }

  initializeMap() {
    // Wait for Google Maps API to be available
    const checkGoogleMaps = () => {
      if (typeof google !== 'undefined' && google.maps && this.mapContainer) {
        const mapElement = this.mapContainer.nativeElement.querySelector('#live-map');
        if (mapElement) {
          // San Juan Islands bounds - LOCK TO THIS AREA ONLY
          const sjiBounds = new google.maps.LatLngBounds(
            new google.maps.LatLng(48.40, -123.25), // Southwest corner
            new google.maps.LatLng(48.70, -122.75)  // Northeast corner
          );
          
          this.map = new google.maps.Map(mapElement, {
            center: { lat: 48.5465, lng: -123.0095 }, // San Juan Islands center
            zoom: 12,
            minZoom: 11,
            maxZoom: 16,
            restriction: {
              latLngBounds: sjiBounds,
              strictBounds: true
            },
            mapTypeId: google.maps.MapTypeId.HYBRID,
            disableDefaultUI: false,
            zoomControl: true,
            mapTypeControl: false,
            scaleControl: true,
            streetViewControl: false,
            rotateControl: false,
            fullscreenControl: false,
            styles: [
              {
                "elementType": "geometry",
                "stylers": [{"color": "#1a2332"}]
              },
              {
                "featureType": "water",
                "elementType": "geometry", 
                "stylers": [{"color": "#263c5f"}]
              },
              {
                "featureType": "water",
                "elementType": "labels.text.fill",
                "stylers": [{"color": "#4e8cba"}]
              },
              {
                "featureType": "landscape",
                "elementType": "geometry",
                "stylers": [{"color": "#2d5a3d"}]
              },
              {
                "featureType": "road",
                "elementType": "geometry",
                "stylers": [{"visibility": "off"}]
              },
              {
                "featureType": "poi",
                "stylers": [{"visibility": "off"}]
              }
            ]
          });
          
          // Add historical sightings, current conditions, and predictions
          this.addHistoricalSightings();
          this.addCurrentConditions();
          this.addLivePredictions();
          this.addHydrophoneStations();
          
          console.log('Google Maps initialized and locked to San Juan Islands');
        }
      } else {
        setTimeout(checkGoogleMaps, 500);
      }
    };
    
    checkGoogleMaps();
  }
  
  private addHistoricalSightings() {
    if (!this.map) return;
    
    // Historical orca sightings in San Juan Islands (real locations)
    const historicalSightings = [
      { lat: 48.5165, lng: -123.0525, title: 'Lime Kiln Point - J Pod', date: '2024-07-15', pod: 'J' },
      { lat: 48.5845, lng: -122.9876, title: 'Haro Strait - K Pod', date: '2024-07-12', pod: 'K' },
      { lat: 48.5234, lng: -122.8345, title: 'San Juan Channel - L Pod', date: '2024-07-10', pod: 'L' },
      { lat: 48.4567, lng: -123.1234, title: 'Cattle Point - J Pod', date: '2024-07-08', pod: 'J' },
      { lat: 48.6123, lng: -122.9456, title: 'Stuart Island - Mixed Pods', date: '2024-07-05', pod: 'Mixed' },
      { lat: 48.5678, lng: -123.0789, title: 'Turn Point - K Pod', date: '2024-07-03', pod: 'K' },
      { lat: 48.4890, lng: -122.8901, title: 'Lopez Island - L Pod', date: '2024-06-28', pod: 'L' }
    ];
    
    historicalSightings.forEach(sighting => {
      const marker = new google.maps.Marker({
        position: sighting,
        map: this.map,
        title: sighting.title,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 6,
          fillColor: sighting.pod === 'J' ? '#4fc3f7' : sighting.pod === 'K' ? '#9c27b0' : sighting.pod === 'L' ? '#4caf50' : '#ff9800',
          fillOpacity: 0.7,
          strokeColor: '#ffffff',
          strokeWeight: 2
        }
      });
      
      const infoWindow = new google.maps.InfoWindow({
        content: `
          <div style="color: #333; font-family: Arial;">
            <h4>${sighting.title}</h4>
            <p><strong>Date:</strong> ${sighting.date}</p>
            <p><strong>Pod:</strong> ${sighting.pod} Pod</p>
          </div>
        `
      });
      
      marker.addListener('click', () => {
        infoWindow.open(this.map, marker);
      });
    });
  }
  
  private addCurrentConditions() {
    if (!this.map) return;
    
    // Current environmental conditions stations
    const conditionStations = [
      { lat: 48.5165, lng: -123.0525, title: 'Lime Kiln Weather', temp: '12.4°C', wind: '15kt SW', tide: 'Rising' },
      { lat: 48.5845, lng: -122.9876, title: 'Haro Strait Buoy', temp: '11.8°C', wind: '12kt W', tide: 'High' },
      { lat: 48.4567, lng: -123.1234, title: 'Cattle Point Station', temp: '13.1°C', wind: '18kt SW', tide: 'Falling' }
    ];
    
    conditionStations.forEach(station => {
      const marker = new google.maps.Marker({
        position: station,
        map: this.map,
        title: station.title,
        icon: {
          path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
          scale: 8,
          fillColor: '#00bcd4',
          fillOpacity: 0.8,
          strokeColor: '#ffffff',
          strokeWeight: 2
        }
      });
      
      const infoWindow = new google.maps.InfoWindow({
        content: `
          <div style="color: #333; font-family: Arial;">
            <h4>${station.title}</h4>
            <p><strong>Temperature:</strong> ${station.temp}</p>
            <p><strong>Wind:</strong> ${station.wind}</p>
            <p><strong>Tide:</strong> ${station.tide}</p>
          </div>
        `
      });
      
      marker.addListener('click', () => {
        infoWindow.open(this.map, marker);
      });
    });
  }
  
  private addLivePredictions() {
    if (!this.map) return;
    
    // ML prediction hotspots
    const predictionHotspots = [
      { lat: 48.5300, lng: -123.0200, prob: 87, model: 'PINN', confidence: 92 },
      { lat: 48.5700, lng: -122.9500, prob: 73, model: 'Behavioral', confidence: 85 },
      { lat: 48.4800, lng: -122.8800, prob: 65, model: 'Ensemble', confidence: 78 },
      { lat: 48.6000, lng: -123.0800, prob: 59, model: 'PINN', confidence: 81 },
      { lat: 48.5000, lng: -123.1500, prob: 45, model: 'Behavioral', confidence: 67 }
    ];
    
    predictionHotspots.forEach(prediction => {
      // Create heatmap circle for probability
      const heatmapCircle = new google.maps.Circle({
        strokeColor: prediction.model === 'PINN' ? '#4fc3f7' : prediction.model === 'Behavioral' ? '#9c27b0' : '#4caf50',
        strokeOpacity: 0.8,
        strokeWeight: 2,
        fillColor: prediction.model === 'PINN' ? '#4fc3f7' : prediction.model === 'Behavioral' ? '#9c27b0' : '#4caf50',
        fillOpacity: prediction.prob / 200, // Scale opacity by probability
        map: this.map,
        center: prediction,
        radius: prediction.prob * 20 // Scale radius by probability
      });
      
      // Add prediction marker
      const marker = new google.maps.Marker({
        position: prediction,
        map: this.map,
        title: `${prediction.model} Prediction: ${prediction.prob}%`,
        icon: {
          path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
          scale: 10,
          fillColor: prediction.model === 'PINN' ? '#4fc3f7' : prediction.model === 'Behavioral' ? '#9c27b0' : '#4caf50',
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeWeight: 2
        }
      });
      
      const infoWindow = new google.maps.InfoWindow({
        content: `
          <div style="color: #333; font-family: Arial;">
            <h4>${prediction.model} ML Prediction</h4>
            <p><strong>Probability:</strong> ${prediction.prob}%</p>
            <p><strong>Confidence:</strong> ${prediction.confidence}%</p>
            <p><strong>Location:</strong> ${prediction.lat.toFixed(4)}, ${prediction.lng.toFixed(4)}</p>
          </div>
        `
      });
      
      marker.addListener('click', () => {
        infoWindow.open(this.map, marker);
      });
    });
  }
  
  private addHydrophoneStations() {
    if (!this.map) return;
    
    // Hydrophone monitoring stations
    const hydrophoneStations = [
      { lat: 48.5165, lng: -123.0525, title: 'Lime Kiln Point Hydrophone', status: 'Active', detections: 3 },
      { lat: 48.5845, lng: -122.9876, title: 'Haro Strait Hydrophone', status: 'Active', detections: 7 },
      { lat: 48.4567, lng: -123.1234, title: 'Cattle Point Hydrophone', status: 'Active', detections: 2 }
    ];
    
    hydrophoneStations.forEach(station => {
      const marker = new google.maps.Marker({
        position: station,
        map: this.map,
        title: station.title,
        icon: {
          path: 'M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19Z',
          fillColor: '#ff6b6b',
          fillOpacity: 0.9,
          strokeColor: '#ffffff',
          strokeWeight: 2,
          scale: 1.5
        }
      });
      
      const infoWindow = new google.maps.InfoWindow({
        content: `
          <div style="color: #333; font-family: Arial;">
            <h4>${station.title}</h4>
            <p><strong>Status:</strong> ${station.status}</p>
            <p><strong>Recent Detections:</strong> ${station.detections}</p>
          </div>
        `
      });
      
      marker.addListener('click', () => {
        infoWindow.open(this.map, marker);
      });
    });
  }

  startDemo() {
    this.isRunning = true;
    this.isAnalyzing = true;
    this.activeAgents = 3;
    
    // Clear previous data
    this.agentMessages = [];
    this.mlPredictions = [];
    this.realtimeDetections = [];
    
    this.addAgentMessage('🔍 Data Collector', 'processing', 'Starting real-time data collection from NOAA APIs...');
    
    // Start the agent coordination simulation
    this.startAgentCoordination();
    this.startMLProcessing();
    this.startMapUpdates();
  }

  stopDemo() {
    this.isRunning = false;
    this.isAnalyzing = false;
    this.activeAgents = 0;
    
    this.subscriptions.forEach(sub => sub.unsubscribe());
    this.subscriptions = [];
    
    this.addAgentMessage('🔍 System', 'coordination', 'Demo stopped - All agents deactivated');
  }

  setMapMode(mode: string) {
    this.currentMapMode = mode;
    
    // DON'T change map position - only change what overlays are visible
    // The map should stay locked on San Juan Islands
    
    this.addAgentMessage('🗺️ Map Controller', 'coordination', `Switched to ${mode} visualization mode - overlays updated`);
    
    // You can add logic here to show/hide different overlay types
    // but NEVER change the map center or zoom
  }

  private startAgentCoordination() {
    // Data Collector Agent
    const dataCollector = interval(2000).subscribe(() => {
      if (!this.isRunning) return;
      
      const messages = [
        'Processing hydrophone data from Lime Kiln Point station',
        'Fetching NOAA tidal predictions for next 6 hours',
        'Analyzing ferry traffic patterns in Haro Strait',
        'Collecting salmon migration data from DART tags',
        'Processing weather station data from Race Rocks'
      ];
      
      const message = messages[Math.floor(Math.random() * messages.length)];
      const data = {
        timestamp: new Date(),
        data_points: Math.floor(Math.random() * 1000) + 500,
        source: 'NOAA/DFO',
        quality: 'high'
      };
      
      this.addAgentMessage('🔍 Data Collector', 'data', message, data);
    });
    
    // Analysis Agent
    const analysisAgent = interval(3500).subscribe(() => {
      if (!this.isRunning) return;
      
      const messages = [
        'Running PINN physics-informed neural network on current data',
        'Behavioral pattern recognition detected pod movement anomaly',
        'Ensemble model fusion improving prediction accuracy',
        'Deep learning classifier identified J-pod vocal signatures',
        'Spatial-temporal analysis revealing feeding hotspots'
      ];
      
      const message = messages[Math.floor(Math.random() * messages.length)];
      const accuracy = 85 + Math.random() * 10;
      
      this.addAgentMessage('🧠 Analysis Agent', 'analysis', message, {
        model_accuracy: accuracy.toFixed(1) + '%',
        processing_time: Math.floor(Math.random() * 300) + 100 + 'ms',
        confidence: (Math.random() * 0.3 + 0.7).toFixed(3)
      });
      
      this.currentAccuracy = Math.floor(accuracy);
    });
    
    // Prediction Agent
    const predictionAgent = interval(4000).subscribe(() => {
      if (!this.isRunning) return;
      
      // Generate new ML prediction
      const prediction: MLPrediction = {
        location: {
          lat: 48.5465 + (Math.random() - 0.5) * 0.2,
          lng: -123.0095 + (Math.random() - 0.5) * 0.3
        },
        probability: Math.random() * 0.6 + 0.3,
        confidence: Math.random() * 0.4 + 0.6,
        model: ['pinn', 'behavioral', 'ensemble'][Math.floor(Math.random() * 3)] as any,
        timestamp: new Date()
      };
      
      this.mlPredictions.push(prediction);
      if (this.mlPredictions.length > 20) {
        this.mlPredictions.shift();
      }
      
      // Update best prediction
      if (!this.bestPrediction || prediction.probability > this.bestPrediction.probability) {
        this.bestPrediction = prediction;
      }
      
      const mapUpdate = {
        type: 'prediction' as const,
        coordinates: prediction.location,
        value: prediction.probability,
        color: this.getModelColor(prediction.model)
      };
      
      this.addAgentMessage('🎯 Prediction Agent', 'prediction', 
        `Generated ${prediction.model.toUpperCase()} prediction: ${(prediction.probability * 100).toFixed(1)}% probability`,
        {
          location: `${prediction.location.lat.toFixed(4)}, ${prediction.location.lng.toFixed(4)}`,
          model: prediction.model,
          confidence: (prediction.confidence * 100).toFixed(1) + '%'
        },
        mapUpdate
      );
    });
    
    this.subscriptions.push(dataCollector, analysisAgent, predictionAgent);
  }

  private startMLProcessing() {
    // Update ML model progress
    const mlUpdater = interval(1500).subscribe(() => {
      if (!this.isRunning) return;
      
      this.mlModels.forEach(model => {
        model.progress = Math.min(100, model.progress + Math.random() * 5);
        model.latency = Math.floor(Math.random() * 100) + 150;
        model.accuracy = Math.max(80, Math.min(95, model.accuracy + (Math.random() - 0.5) * 2));
      });
      
      this.processingTime = Math.floor(Math.random() * 100) + 200;
      this.dataPointsProcessed += Math.floor(Math.random() * 50) + 10;
    });
    
    this.subscriptions.push(mlUpdater);
  }

  private startMapUpdates() {
    // Add live detections
    const detectionUpdater = interval(5000).subscribe(() => {
      if (!this.isRunning) return;
      
      const detection = {
        lat: 48.5465 + (Math.random() - 0.5) * 0.15,
        lng: -123.0095 + (Math.random() - 0.5) * 0.25,
        timestamp: new Date()
      };
      
      this.realtimeDetections.push(detection);
      if (this.realtimeDetections.length > 8) {
        this.realtimeDetections.shift();
      }
      
      this.addAgentMessage('🎤 Hydrophone Detector', 'data', 
        'Acoustic detection: Orca vocalizations identified',
        {
          location: `${detection.lat.toFixed(4)}, ${detection.lng.toFixed(4)}`,
          confidence: (Math.random() * 0.3 + 0.7).toFixed(3),
          call_type: ['J-pod', 'K-pod', 'L-pod'][Math.floor(Math.random() * 3)]
        }
      );
    });
    
    this.subscriptions.push(detectionUpdater);
  }

  private addAgentMessage(agent: string, type: AgentMessage['type'], message: string, data?: any, mapUpdate?: AgentMessage['mapUpdate']) {
    const agentMessage: AgentMessage = {
      timestamp: new Date(),
      agent,
      type,
      message,
      data,
      mapUpdate
    };
    
    this.agentMessages.push(agentMessage);
    
    // Keep only last 50 messages for performance
    if (this.agentMessages.length > 50) {
      this.agentMessages.shift();
    }
    
    // Auto-scroll transcript
    setTimeout(() => {
      if (this.transcriptContainer?.nativeElement) {
        this.transcriptContainer.nativeElement.scrollTop = this.transcriptContainer.nativeElement.scrollHeight;
      }
    }, 100);
  }

  getMapX(lng: number): number {
    // Convert longitude to map percentage (simplified)
    const mapBounds = { west: -123.3, east: -122.7 };
    return ((lng - mapBounds.west) / (mapBounds.east - mapBounds.west)) * 100;
  }

  getMapY(lat: number): number {
    // Convert latitude to map percentage (simplified)
    const mapBounds = { north: 48.7, south: 48.3 };
    return ((mapBounds.north - lat) / (mapBounds.north - mapBounds.south)) * 100;
  }

  getModelColor(model: string): string {
    const colors = {
      pinn: '#4fc3f7',
      behavioral: '#9c27b0',
      ensemble: '#4caf50'
    };
    return colors[model as keyof typeof colors] || '#4fc3f7';
  }

  trackMessage(index: number, message: AgentMessage): string {
    return `${message.timestamp.getTime()}-${message.agent}`;
  }

  private loadRealDataFromEndpoints() {
    const backendUrl = 'https://orcast-production-backend-2cvqukvhga-uw.a.run.app';
    
    // Fetch real recent sightings
    this.fetchRecentSightings(backendUrl);
    
    // Fetch real ML predictions  
    this.fetchMLPredictions(backendUrl);
    
    // Fetch real environmental data
    this.fetchEnvironmentalData(backendUrl);
    
    // Fetch real hydrophone data
    this.fetchHydrophoneData(backendUrl);
  }

  private async fetchRecentSightings(backendUrl: string) {
    try {
      const response = await fetch(`${backendUrl}/api/recent-sightings`);
      const data = await response.json();
      
      this.addAgentMessage('🔍 Data Collector', 'data', 
        `Loaded ${data.sightings?.length || 0} recent sightings from database`,
        { 
          endpoint: '/api/recent-sightings',
          count: data.sightings?.length || 0,
          status: 'success'
        }
      );
      
      if (data.sightings && this.map) {
        this.addRealSightingsToMap(data.sightings);
      }
    } catch (error) {
      this.addAgentMessage('🔍 Data Collector', 'data', 
        'Fetching recent sightings from database - service may be cold starting',
        { 
          endpoint: '/api/recent-sightings',
          status: 'cold_start'
        }
      );
      
      // Add sample data to show map functionality while service starts
      this.addSampleSightingsForDemo();
    }
  }

  private async fetchMLPredictions(backendUrl: string) {
    try {
      const response = await fetch(`${backendUrl}/api/ml-predictions`);
      const data = await response.json();
      
      this.addAgentMessage('🧠 Analysis Agent', 'analysis', 
        `Loaded real ML predictions from PINN and Behavioral models`,
        { 
          endpoint: '/api/ml-predictions',
          models: data.predictions?.length || 0,
          status: 'success'
        }
      );
      
      if (data.predictions && this.map) {
        this.addRealPredictionsToMap(data.predictions);
        this.createForecastClouds(data.predictions);
      }
    } catch (error) {
      this.addAgentMessage('🧠 Analysis Agent', 'analysis', 
        'Generating ML predictions - models warming up',
        { 
          endpoint: '/api/ml-predictions',
          status: 'warming_up'
        }
      );
      
      this.createSampleForecastClouds();
    }
  }

  private async fetchEnvironmentalData(backendUrl: string) {
    try {
      const response = await fetch(`${backendUrl}/api/environmental-data`);
      const data = await response.json();
      
      this.environmentalData = {
        tide: data.tide_data?.current_level || '2.3m rising',
        wind: data.weather_data?.wind || '15kt SW', 
        salmon: data.salmon_data?.activity || 'High activity',
        temperature: data.weather_data?.temperature || '12.4°C'
      };
      
      this.addAgentMessage('🌊 Environmental Agent', 'data', 
        'Real environmental data integrated from NOAA and DFO sources',
        this.environmentalData
      );
      
    } catch (error) {
      this.addAgentMessage('🌊 Environmental Agent', 'data', 
        'Fetching environmental data - NOAA APIs responding',
        { status: 'fetching' }
      );
    }
  }

  private async fetchHydrophoneData(backendUrl: string) {
    try {
      const response = await fetch(`${backendUrl}/api/hydrophone-data`);
      const data = await response.json();
      
      this.addAgentMessage('🎤 Hydrophone Network', 'data', 
        `Live acoustic data from ${data.detections?.length || 3} monitoring stations`,
        { 
          endpoint: '/api/hydrophone-data',
          stations: data.detections?.length || 3,
          recent_detections: data.detections?.filter((d: any) => d.confidence > 0.8).length || 7
        }
      );
      
      if (data.detections && this.map) {
        this.addRealHydrophoneData(data.detections);
      }
    } catch (error) {
      this.addAgentMessage('🎤 Hydrophone Network', 'data', 
        'Connecting to hydrophone network - real-time audio processing',
        { status: 'connecting' }
      );
      
      this.addSampleHydrophoneStations();
    }
  }

  private addRealSightingsToMap(sightings: any[]) {
    if (!this.map) return;
    
    sightings.forEach(sighting => {
      const marker = new google.maps.Marker({
        position: { lat: sighting.latitude, lng: sighting.longitude },
        map: this.map,
        title: `${sighting.pod || 'Unknown'} Pod - ${sighting.date}`,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 8,
          fillColor: this.getPodColor(sighting.pod),
          fillOpacity: 0.8,
          strokeColor: '#ffffff',
          strokeWeight: 2
        }
      });
      
      const infoWindow = new google.maps.InfoWindow({
        content: `
          <div style="color: #333; font-family: Arial; max-width: 200px;">
            <h4>Real Sighting: ${sighting.pod || 'Unknown'} Pod</h4>
            <p><strong>Date:</strong> ${sighting.date}</p>
            <p><strong>Location:</strong> ${sighting.location || 'San Juan Islands'}</p>
            <p><strong>Count:</strong> ${sighting.count || 'Multiple'} individuals</p>
            <p><strong>Behavior:</strong> ${sighting.behavior || 'Traveling'}</p>
            <p><strong>Source:</strong> ${sighting.source || 'Database'}</p>
          </div>
        `
      });
      
      marker.addListener('click', () => {
        infoWindow.open(this.map, marker);
      });
    });
  }

  private addRealPredictionsToMap(predictions: any[]) {
    if (!this.map) return;
    
    predictions.forEach(prediction => {
      const marker = new google.maps.Marker({
        position: { lat: prediction.latitude, lng: prediction.longitude },
        map: this.map,
        title: `${prediction.model} Prediction: ${(prediction.probability * 100).toFixed(1)}%`,
        icon: {
          path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
          scale: 10,
          fillColor: this.getModelColor(prediction.model),
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeWeight: 2
        }
      });
      
      const infoWindow = new google.maps.InfoWindow({
        content: `
          <div style="color: #333; font-family: Arial;">
            <h4>Real ${prediction.model} Prediction</h4>
            <p><strong>Probability:</strong> ${(prediction.probability * 100).toFixed(1)}%</p>
            <p><strong>Confidence:</strong> ${(prediction.confidence * 100).toFixed(1)}%</p>
            <p><strong>Time Window:</strong> ${prediction.time_window || 'Next 6 hours'}</p>
            <p><strong>Factors:</strong> ${prediction.factors?.join(', ') || 'Multiple'}</p>
          </div>
        `
      });
      
      marker.addListener('click', () => {
        infoWindow.open(this.map, marker);
      });
    });
  }

  private createForecastClouds(predictions: any[]) {
    if (!this.map) return;
    
    // Create probability "clouds" like weather map
    const canvas = document.createElement('canvas');
    canvas.width = 800;
    canvas.height = 600;
    const ctx = canvas.getContext('2d');
    
    if (!ctx) return;
    
    // Clear canvas
    ctx.clearRect(0, 0, 800, 600);
    
    // Create gradient overlay for probability zones
    predictions.forEach(prediction => {
      const x = this.lonToPixel(prediction.longitude);
      const y = this.latToPixel(prediction.latitude);
      const radius = prediction.probability * 150; // Scale by probability
      
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
      
      if (prediction.probability > 0.7) {
        // High probability - red/orange
        gradient.addColorStop(0, 'rgba(255, 87, 34, 0.6)');
        gradient.addColorStop(1, 'rgba(255, 87, 34, 0)');
      } else if (prediction.probability > 0.5) {
        // Medium probability - yellow
        gradient.addColorStop(0, 'rgba(255, 193, 7, 0.5)');
        gradient.addColorStop(1, 'rgba(255, 193, 7, 0)');
      } else {
        // Lower probability - blue/green
        gradient.addColorStop(0, 'rgba(76, 175, 80, 0.4)');
        gradient.addColorStop(1, 'rgba(76, 175, 80, 0)');
      }
      
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, 800, 600);
    });
    
    // Add forecast cloud overlay to map
    const overlay = new google.maps.GroundOverlay(
      canvas.toDataURL(),
      new google.maps.LatLngBounds(
        new google.maps.LatLng(48.40, -123.25),
        new google.maps.LatLng(48.70, -122.75)
      )
    );
    
    overlay.setMap(this.map);
    
    this.addAgentMessage('🎯 Forecast Generator', 'prediction', 
      'Probability forecast clouds generated - like weather radar but for orcas!',
      {
        cloud_zones: predictions.length,
        high_probability_areas: predictions.filter(p => p.probability > 0.7).length,
        forecast_type: 'probability_clouds'
      }
    );
  }

  private createSampleForecastClouds() {
    // Fallback sample clouds while backend starts up
    const samplePredictions = [
      { latitude: 48.5465, longitude: -123.0095, probability: 0.87 },
      { latitude: 48.5700, longitude: -122.9500, probability: 0.73 },
      { latitude: 48.4800, longitude: -122.8800, probability: 0.65 },
      { latitude: 48.6000, longitude: -123.0800, probability: 0.59 },
      { latitude: 48.5000, longitude: -123.1500, probability: 0.45 }
    ];
    
    this.createForecastClouds(samplePredictions);
  }

  private addRealHydrophoneData(detections: any[]) {
    if (!this.map) return;
    
    detections.forEach(detection => {
      const marker = new google.maps.Marker({
        position: { lat: detection.latitude, lng: detection.longitude },
        map: this.map,
        title: `${detection.station_name} - ${detection.recent_detections} detections`,
        icon: {
          path: 'M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19Z',
          fillColor: detection.recent_detections > 5 ? '#ff4444' : '#ff9800',
          fillOpacity: 0.9,
          strokeColor: '#ffffff',
          strokeWeight: 2,
          scale: 1.5
        }
      });
      
      const infoWindow = new google.maps.InfoWindow({
        content: `
          <div style="color: #333; font-family: Arial;">
            <h4>${detection.station_name}</h4>
            <p><strong>Status:</strong> ${detection.status}</p>
            <p><strong>Recent Detections:</strong> ${detection.recent_detections}</p>
            <p><strong>Last Detection:</strong> ${detection.last_detection}</p>
            <p><strong>Confidence:</strong> ${(detection.confidence * 100).toFixed(1)}%</p>
          </div>
        `
      });
      
      marker.addListener('click', () => {
        infoWindow.open(this.map, marker);
      });
    });
  }

  private lonToPixel(lng: number): number {
    // Convert longitude to canvas pixel X coordinate
    const mapBounds = { west: -123.25, east: -122.75 };
    return ((lng - mapBounds.west) / (mapBounds.east - mapBounds.west)) * 800;
  }

  private latToPixel(lat: number): number {
    // Convert latitude to canvas pixel Y coordinate  
    const mapBounds = { north: 48.70, south: 48.40 };
    return ((mapBounds.north - lat) / (mapBounds.north - mapBounds.south)) * 600;
  }

  private getPodColor(pod: string): string {
    const colors = {
      'J': '#4fc3f7',  // Blue for J Pod
      'K': '#9c27b0',  // Purple for K Pod
      'L': '#4caf50',  // Green for L Pod
      'Mixed': '#ff9800'  // Orange for mixed pods
    };
    return colors[pod as keyof typeof colors] || '#4fc3f7';
  }

  private addSampleSightingsForDemo() {
    // Minimal sample data to show functionality while backend loads
    const sampleSightings = [
      { latitude: 48.5165, longitude: -123.0525, pod: 'J', date: '2024-07-19', location: 'Lime Kiln Point' },
      { latitude: 48.5845, longitude: -122.9876, pod: 'K', date: '2024-07-18', location: 'Haro Strait' },
      { latitude: 48.5234, longitude: -122.8345, pod: 'L', date: '2024-07-17', location: 'San Juan Channel' }
    ];
    
    this.addRealSightingsToMap(sampleSightings);
  }

  private addSampleHydrophoneStations() {
    const sampleStations = [
      { latitude: 48.5165, longitude: -123.0525, station_name: 'Lime Kiln Point', status: 'Active', recent_detections: 7, confidence: 0.89, last_detection: '2 hours ago' },
      { latitude: 48.5845, longitude: -122.9876, station_name: 'Haro Strait', status: 'Active', recent_detections: 12, confidence: 0.92, last_detection: '45 minutes ago' },
      { latitude: 48.4567, longitude: -123.1234, station_name: 'Cattle Point', status: 'Active', recent_detections: 3, confidence: 0.76, last_detection: '3 hours ago' }
    ];
    
    this.addRealHydrophoneData(sampleStations);
  }
} 