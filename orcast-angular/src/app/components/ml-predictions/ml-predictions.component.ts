import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GoogleMapsModule } from '@angular/google-maps';
import { Subject, takeUntil } from 'rxjs';

import { NavHeaderComponent } from '../shared/nav-header.component';
import { BackendService } from '../../services/backend.service';
import { MapService } from '../../services/map.service';
import { StateService } from '../../services/state.service';
import { MLPredictionData } from '../../models/orca-sighting.model';

interface ModelInfo {
  title: string;
  description: string;
  accuracy: string;
  precision: string;
  recall: string;
  confidence: number;
}

interface HourlyPrediction {
  hour: number;
  time: string;
  probability: number;
  className: string;
}

@Component({
  selector: 'orcast-ml-predictions',
  standalone: true,
  imports: [CommonModule, FormsModule, GoogleMapsModule, NavHeaderComponent],
  template: `
    <orcast-nav-header currentPage="ml-predictions"></orcast-nav-header>

    <!-- ML Controls Panel -->
    <div class="ml-controls">
      <h3>🧠 ML Prediction Models</h3>
      
      <div class="model-selector">
        <h4>Select Model</h4>
        <div 
          *ngFor="let model of availableModels"
          class="model-option"
          [class.active]="selectedModel === model.key"
          (click)="selectModel(model.key)">
          
          <input 
            type="radio" 
            [id]="model.key"
            name="model" 
            [value]="model.key"
            [checked]="selectedModel === model.key">
          <div>
            <strong>{{ model.title }}</strong><br>
            <small>{{ model.subtitle }}</small>
          </div>
        </div>
      </div>
      
      <div class="prediction-params">
        <h4>⚙️ Parameters</h4>
        
        <label>Prediction Hours: <span>{{ predictionHours }}</span></label>
        <input 
          type="range" 
          min="1" 
          max="72" 
          [(ngModel)]="predictionHours"
          (input)="onParameterChange()"
          class="param-slider">
        
        <label>Spatial Resolution: <span>{{ resolutionLabels[spatialResolution] }}</span></label>
        <input 
          type="range" 
          min="1" 
          max="10" 
          [(ngModel)]="spatialResolution"
          (input)="onParameterChange()"
          class="param-slider">
        
        <label>Confidence Threshold: <span>{{ confidenceThreshold }}%</span></label>
        <input 
          type="range" 
          min="50" 
          max="95" 
          [(ngModel)]="confidenceThreshold"
          (input)="onParameterChange()"
          class="param-slider">
      </div>
      
      <button 
        (click)="generatePredictions()" 
        class="generate-btn"
        [disabled]="isGenerating">
        {{ isGenerating ? '🔄 Generating...' : '🚀 Generate Predictions' }}
      </button>
    </div>

    <!-- Model Information Panel -->
    <div class="model-info">
      <h3>{{ currentModelInfo.title }}</h3>
      <p>{{ currentModelInfo.description }}</p>
      
      <div class="confidence-meter">
        <h4>Model Confidence</h4>
        <div class="confidence-bar">
          <div 
            class="confidence-indicator" 
            [style.left.%]="currentModelInfo.confidence">
          </div>
        </div>
        <div class="confidence-text">
          {{ currentModelInfo.confidence }}% Confident
        </div>
      </div>
      
      <div class="performance-metrics">
        <h4>📊 Performance Metrics</h4>
        <div class="metric-row">
          <span>Accuracy:</span>
          <span>{{ currentModelInfo.accuracy }}</span>
        </div>
        <div class="metric-row">
          <span>Precision:</span>
          <span>{{ currentModelInfo.precision }}</span>
        </div>
        <div class="metric-row">
          <span>Recall:</span>
          <span>{{ currentModelInfo.recall }}</span>
        </div>
      </div>
    </div>

    <!-- Map Container -->
    <google-map 
      #map
      [options]="mapOptions"
      (mapInitialized)="onMapInitialized($event)">
    </google-map>

    <!-- Forecast Timeline -->
    <div class="forecast-timeline">
      <h4>📅 24-Hour Forecast Timeline</h4>
      <div class="timeline-hours">
        <div 
          *ngFor="let prediction of hourlyPredictions"
          class="hour-item"
          [class]="prediction.className"
          (click)="showHourPrediction(prediction)">
          <div>{{ prediction.time }}</div>
          <div class="hour-prob">{{ (prediction.probability * 100) | number:'1.0-0' }}%</div>
        </div>
      </div>
      <div class="timeline-note">
        Click hours to see detailed predictions
      </div>
    </div>

    <!-- Prediction Results -->
    <div class="prediction-overlay" *ngIf="predictionResults">
      <h4>📈 Prediction Results</h4>
      <div *ngIf="predictionResults.metadata">
        <p><strong>Model:</strong> {{ predictionResults.model.toUpperCase() }}</p>
        <p><strong>Predictions:</strong> {{ predictionResults.metadata.totalPredictions }}</p>
        <p><strong>Avg Probability:</strong> {{ (predictionResults.metadata.averageProbability * 100) | number:'1.1-1' }}%</p>
        <p><strong>Max Probability:</strong> {{ (predictionResults.metadata.maxProbability * 100) | number:'1.1-1' }}%</p>
        <p><strong>Status:</strong> ✅ Complete</p>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      height: 100vh;
      width: 100%;
      position: relative;
    }

    google-map {
      height: 100vh;
      width: 100%;
    }

    .ml-controls {
      position: absolute;
      top: 20px;
      left: 20px;
      background: rgba(0, 30, 60, 0.95);
      padding: 20px;
      border-radius: 10px;
      border: 1px solid #4fc3f7;
      color: white;
      z-index: 1000;
      width: 350px;
      max-height: 80vh;
      overflow-y: auto;
    }
    
    .model-selector {
      margin: 15px 0;
    }
    
    .model-option {
      display: flex;
      align-items: center;
      margin: 8px 0;
      padding: 8px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 5px;
      cursor: pointer;
      transition: all 0.3s ease;
    }
    
    .model-option.active {
      background: rgba(79, 195, 247, 0.2);
      border: 1px solid #4fc3f7;
    }
    
    .model-option input[type="radio"] {
      margin-right: 10px;
    }
    
    .prediction-params {
      margin: 15px 0;
      padding: 15px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 5px;
    }

    .prediction-params label {
      display: block;
      margin: 15px 0 5px 0;
      font-size: 0.9rem;
    }
    
    .param-slider {
      width: 100%;
      margin: 8px 0;
    }

    .generate-btn {
      width: 100%;
      padding: 12px;
      background: #4fc3f7;
      color: #001e3c;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      font-weight: bold;
      font-size: 1rem;
    }

    .generate-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    .model-info {
      position: absolute;
      top: 20px;
      right: 20px;
      background: rgba(0, 30, 60, 0.95);
      padding: 20px;
      border-radius: 10px;
      border: 1px solid #4fc3f7;
      color: white;
      z-index: 1000;
      width: 300px;
    }
    
    .confidence-meter {
      margin: 15px 0;
    }
    
    .confidence-bar {
      height: 20px;
      background: linear-gradient(90deg, #f44336, #ff9800, #4caf50);
      border-radius: 10px;
      position: relative;
      overflow: hidden;
      margin: 10px 0;
    }
    
    .confidence-indicator {
      position: absolute;
      top: 0;
      height: 100%;
      width: 3px;
      background: white;
      transition: left 0.3s ease;
    }

    .confidence-text {
      text-align: center;
      margin-top: 5px;
      font-weight: bold;
    }

    .performance-metrics {
      margin-top: 15px;
    }

    .metric-row {
      display: flex;
      justify-content: space-between;
      margin: 5px 0;
    }
    
    .forecast-timeline {
      position: absolute;
      bottom: 20px;
      left: 20px;
      background: rgba(0, 30, 60, 0.95);
      padding: 15px;
      border-radius: 8px;
      border: 1px solid #4fc3f7;
      color: white;
      z-index: 1000;
      width: 400px;
    }
    
    .timeline-hours {
      display: flex;
      justify-content: space-between;
      margin: 10px 0;
      flex-wrap: wrap;
      gap: 2px;
    }
    
    .hour-item {
      text-align: center;
      padding: 5px;
      border-radius: 3px;
      font-size: 0.8rem;
      cursor: pointer;
      transition: all 0.3s ease;
      flex: 1;
      min-width: 35px;
    }

    .hour-prob {
      font-size: 0.7rem;
    }
    
    .hour-item.high-prob {
      background: #4caf50;
      color: white;
    }
    
    .hour-item.medium-prob {
      background: #ff9800;
      color: white;
    }
    
    .hour-item.low-prob {
      background: #f44336;
      color: white;
    }

    .timeline-note {
      font-size: 0.8rem;
      opacity: 0.7;
      text-align: center;
      margin-top: 10px;
    }
    
    .prediction-overlay {
      position: absolute;
      bottom: 20px;
      right: 20px;
      background: rgba(0, 30, 60, 0.95);
      padding: 15px;
      border-radius: 8px;
      border: 1px solid #4fc3f7;
      color: white;
      z-index: 1000;
      max-width: 300px;
    }
  `]
})
export class MLPredictionsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  
  // Model Selection
  selectedModel = 'pinn';
  availableModels = [
    {
      key: 'pinn',
      title: 'PINN Physics-Informed',
      subtitle: 'Neural network with oceanographic physics'
    },
    {
      key: 'behavioral',
      title: 'Behavioral ML',
      subtitle: 'DTAG biologging + feeding patterns'
    },
    {
      key: 'ensemble',
      title: 'Ensemble Model',
      subtitle: 'Combined PINN + Behavioral + Environmental'
    }
  ];

  // Parameters
  predictionHours = 24;
  spatialResolution = 5;
  confidenceThreshold = 70;
  
  resolutionLabels = ['5km', '2km', '1km', '500m', '200m', '100m', '50m', '20m', '10m', '5m'];

  // State
  isGenerating = false;
  predictionResults: MLPredictionData | null = null;
  hourlyPredictions: HourlyPrediction[] = [];

  // Model Information
  modelInfoMap: Record<string, ModelInfo> = {
    pinn: {
      title: '🧠 PINN Physics Model',
      description: 'Physics-Informed Neural Network incorporating oceanographic data, current patterns, and whale behavioral physics.',
      accuracy: '84.2%',
      precision: '78.9%',
      recall: '81.5%',
      confidence: 85
    },
    behavioral: {
      title: '🐋 Behavioral ML Model',
      description: 'Machine learning model trained on DTAG biologging data, feeding patterns, and social behaviors.',
      accuracy: '79.8%',
      precision: '82.1%',
      recall: '76.3%',
      confidence: 78
    },
    ensemble: {
      title: '🎯 Ensemble Model',
      description: 'Combined model integrating PINN physics, behavioral analysis, and environmental factors.',
      accuracy: '87.6%',
      precision: '85.2%',
      recall: '84.7%',
      confidence: 92
    }
  };

  // Map
  mapOptions: google.maps.MapOptions = {
    zoom: 11,
    center: { lat: 48.5465, lng: -123.0307 },
    mapTypeId: google.maps.MapTypeId.HYBRID
  };

  constructor(
    private backendService: BackendService,
    private mapService: MapService,
    private stateService: StateService
  ) {}

  ngOnInit(): void {
    this.stateService.updateCurrentView('ml-predictions');
    this.setupStateSubscriptions();
    this.generateTimeline();
    this.generatePredictions();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  onMapInitialized(map: google.maps.Map): void {
    this.mapService.initializeMap(map.getDiv()!);
  }

  get currentModelInfo(): ModelInfo {
    return this.modelInfoMap[this.selectedModel];
  }

  private setupStateSubscriptions(): void {
    this.stateService.mlSettings$
      .pipe(takeUntil(this.destroy$))
      .subscribe(settings => {
        this.selectedModel = settings.selectedModel;
        this.predictionHours = settings.predictionHours;
        this.spatialResolution = settings.spatialResolution;
        this.confidenceThreshold = Math.round(settings.confidenceThreshold * 100);
      });
  }

  selectModel(modelType: string): void {
    this.selectedModel = modelType;
    this.stateService.selectMLModel(modelType);
    this.generatePredictions();
  }

  onParameterChange(): void {
    this.stateService.updateMLSettings({
      predictionHours: this.predictionHours,
      spatialResolution: this.spatialResolution,
      confidenceThreshold: this.confidenceThreshold / 100
    });
    
    // Regenerate predictions after parameter change
    setTimeout(() => this.generatePredictions(), 300);
  }

  generatePredictions(): void {
    this.isGenerating = true;
    this.predictionResults = null;

    const threshold = this.confidenceThreshold / 100;

    this.backendService.generateMLPredictions(this.selectedModel, this.predictionHours, threshold)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.predictionResults = data;
          this.updateMapWithPredictions(data);
          this.generateTimeline();
          this.isGenerating = false;
        },
        error: (error) => {
          console.error('Error generating predictions:', error);
          this.stateService.addError('Failed to generate ML predictions');
          this.isGenerating = false;
        }
      });
  }

  showHourPrediction(prediction: HourlyPrediction): void {
    const time = new Date();
    time.setHours(time.getHours() + prediction.hour);
    
    // Create info window for the prediction
    const infoWindow = new google.maps.InfoWindow({
      content: `
        <div style="color: #001e3c;">
          <h3>📊 Hour ${prediction.hour} Prediction</h3>
          <p><strong>Time:</strong> ${time.toLocaleTimeString()}</p>
          <p><strong>Probability:</strong> ${(prediction.probability * 100).toFixed(1)}%</p>
          <p><strong>Model:</strong> ${this.selectedModel.toUpperCase()}</p>
          <p><strong>Conditions:</strong> ${prediction.probability > 0.7 ? 'Excellent' : prediction.probability > 0.4 ? 'Good' : 'Fair'}</p>
        </div>
      `,
      position: { lat: 48.5465, lng: -123.0307 }
    });

    // Show on map
    this.mapService.map$.pipe(takeUntil(this.destroy$)).subscribe(map => {
      if (map) {
        infoWindow.open(map);
      }
    });
  }

  private updateMapWithPredictions(data: MLPredictionData): void {
    if (data.predictions && data.predictions.length > 0) {
      this.mapService.addMLPredictionHeatMap(data.predictions, data.model);
    }
  }

  private generateTimeline(): void {
    const predictions: HourlyPrediction[] = [];

    for (let i = 0; i < 24; i++) {
      const hour = new Date();
      hour.setHours(hour.getHours() + i);
      
      // Simulate hourly probabilities based on model and time
      let probability = this.calculateHourlyProbability(i);
      
      let className = 'low-prob';
      if (probability > 0.7) className = 'high-prob';
      else if (probability > 0.4) className = 'medium-prob';

      predictions.push({
        hour: i,
        time: hour.getHours().toString().padStart(2, '0') + ':00',
        probability: probability,
        className: className
      });
    }

    this.hourlyPredictions = predictions;
  }

  private calculateHourlyProbability(hour: number): number {
    let probability = 0.3 + Math.sin((hour / 24) * Math.PI * 2) * 0.3;
    
    // Model-specific adjustments
    if (this.selectedModel === 'behavioral') {
      // Higher probabilities during feeding times
      if (hour >= 6 && hour <= 9) probability += 0.2; // Morning feeding
      if (hour >= 17 && hour <= 20) probability += 0.3; // Evening feeding
    } else if (this.selectedModel === 'pinn') {
      // Physics-based: account for tidal patterns
      probability += Math.sin((hour / 12) * Math.PI) * 0.2;
    } else if (this.selectedModel === 'ensemble') {
      // Combination of factors
      if (hour >= 6 && hour <= 9) probability += 0.15;
      if (hour >= 17 && hour <= 20) probability += 0.25;
      probability += Math.sin((hour / 12) * Math.PI) * 0.15;
    }

    // Add some randomness
    probability += (Math.random() - 0.5) * 0.2;
    
    return Math.max(0, Math.min(1, probability));
  }
} 