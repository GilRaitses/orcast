import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { GoogleMapsModule } from '@angular/google-maps';
import { Subject, takeUntil, interval } from 'rxjs';

import { NavHeaderComponent } from '../shared/nav-header.component';
import { BackendService } from '../../services/backend.service';
import { MapService } from '../../services/map.service';
import { StateService } from '../../services/state.service';
import { HydrophoneData, Detection } from '../../models/orca-sighting.model';

interface DetectionStats {
  totalDetections: number;
  highConfidenceDetections: number;
  mostActiveHydrophone: string;
}

interface FrequencyData {
  lowFreq: number;
  midFreq: number;
  highFreq: number;
}

@Component({
  selector: 'orcast-realtime-detection',
  standalone: true,
  imports: [CommonModule, FormsModule, GoogleMapsModule, NavHeaderComponent],
  template: `
    <orcast-nav-header currentPage="realtime"></orcast-nav-header>

    <!-- Real-time Controls Panel -->
    <div class="realtime-controls">
      <h3>🎧 Live Hydrophones</h3>
      <p>Real-time OrcaHello AI Detection</p>
      
      <button 
        (click)="refreshHydrophones()" 
        class="refresh-btn"
        [disabled]="isLoading">
        {{ isLoading ? '🔄 Refreshing...' : '🔄 Refresh Feeds' }}
      </button>
      
      <div class="hydrophone-list">
        <div 
          *ngFor="let hydrophone of hydrophones"
          class="hydrophone-item"
          [class.active]="selectedHydrophone?.id === hydrophone.id"
          [class.detecting]="hydrophone.detecting"
          (click)="selectHydrophone(hydrophone)">
          
          <div>
            <div class="hydrophone-name">{{ hydrophone.name }}</div>
            <div class="hydrophone-location">{{ hydrophone.location }}</div>
            <div *ngIf="hydrophone.lastDetection" class="last-detection">
              Last: {{ getTimeAgo(hydrophone.lastDetection) }}
            </div>
          </div>
          
          <div class="hydrophone-status"
               [class]="'status-' + hydrophone.status"
               [class.status-detecting]="hydrophone.detecting">
            {{ hydrophone.detecting ? 'DETECTING' : hydrophone.status.toUpperCase() }}
          </div>
        </div>
      </div>
      
      <div class="audio-settings">
        <h4>🔊 Audio Settings</h4>
        <label>
          <input type="checkbox" [(ngModel)]="autoPlay"> Auto-play detections
        </label><br>
        <label>
          <input type="checkbox" [(ngModel)]="notifications"> Sound alerts
        </label><br>
        <label>
          Volume: <input type="range" min="0" max="100" [(ngModel)]="volume" (input)="updateVolume()">
        </label>
      </div>
    </div>

    <!-- Detection Panel -->
    <div class="detection-panel">
      <h3>🚨 Recent Detections</h3>
      
      <div class="detection-list" *ngIf="recentDetections.length > 0; else noDetections">
        <div 
          *ngFor="let detection of recentDetections.slice(0, 10)"
          class="detection-item"
          (click)="playDetection(detection)">
          
          <div class="detection-timestamp">
            {{ detection.timestamp | date:'mediumTime' }}
          </div>
          <div class="detection-confidence">
            {{ (detection.confidence * 100) | number:'1.1-1' }}%
          </div>
          <div class="detection-details">
            <strong>{{ detection.hydrophone }}</strong><br>
            Call type: {{ detection.callType }}<br>
            Frequency: {{ detection.frequency | number:'1.0-0' }}Hz<br>
            Duration: {{ detection.duration | number:'1.1-1' }}s
          </div>
        </div>
      </div>
      
      <ng-template #noDetections>
        <p class="no-detections">Listening for whale calls...</p>
      </ng-template>
      
      <div class="detection-stats">
        <h4>📊 Detection Stats (24h)</h4>
        <div class="stat-row">
          <span>Total Detections:</span>
          <span>{{ detectionStats.totalDetections }}</span>
        </div>
        <div class="stat-row">
          <span>High Confidence:</span>
          <span>{{ detectionStats.highConfidenceDetections }}</span>
        </div>
        <div class="stat-row">
          <span>Most Active:</span>
          <span>{{ detectionStats.mostActiveHydrophone }}</span>
        </div>
      </div>
    </div>

    <!-- Map Container -->
    <google-map 
      #map
      [options]="mapOptions"
      (mapInitialized)="onMapInitialized($event)">
    </google-map>

    <!-- Audio Controls -->
    <div class="audio-controls">
      <h4>🔊 Audio Playback</h4>
      <div class="current-detection">{{ currentDetectionText }}</div>
      <audio #audioPlayer class="audio-player" controls>
        Your browser does not support the audio element.
      </audio>
      <div class="audio-note">
        Latest whale call will play here automatically
      </div>
    </div>

    <!-- Frequency Display -->
    <div class="frequency-display">
      <h4>📈 Frequency Analysis</h4>
      <div class="frequency-item">
        <div>Low Freq (0-1kHz)</div>
        <div class="frequency-bar">
          <div class="frequency-indicator" [style.width.%]="frequencyData.lowFreq"></div>
        </div>
      </div>
      <div class="frequency-item">
        <div>Mid Freq (1-5kHz)</div>
        <div class="frequency-bar">
          <div class="frequency-indicator" [style.width.%]="frequencyData.midFreq"></div>
        </div>
      </div>
      <div class="frequency-item">
        <div>High Freq (5-20kHz)</div>
        <div class="frequency-bar">
          <div class="frequency-indicator" [style.width.%]="frequencyData.highFreq"></div>
        </div>
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

    .realtime-controls {
      position: absolute;
      top: 20px;
      left: 20px;
      background: rgba(0, 30, 60, 0.95);
      padding: 20px;
      border-radius: 10px;
      border: 1px solid #4fc3f7;
      color: white;
      z-index: 1000;
      width: 320px;
      max-height: 80vh;
      overflow-y: auto;
    }

    .refresh-btn {
      width: 100%;
      padding: 8px;
      background: #4fc3f7;
      color: #001e3c;
      border: none;
      border-radius: 5px;
      cursor: pointer;
      margin-bottom: 10px;
      font-weight: bold;
    }

    .refresh-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    .hydrophone-list {
      max-height: 300px;
      overflow-y: auto;
      margin: 15px 0;
    }
    
    .hydrophone-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px;
      margin: 5px 0;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 5px;
      border: 1px solid transparent;
      transition: all 0.3s ease;
      cursor: pointer;
    }
    
    .hydrophone-item.active {
      border-color: #4fc3f7;
      background: rgba(79, 195, 247, 0.1);
    }
    
    .hydrophone-item.detecting {
      border-color: #ff4444;
      background: rgba(255, 68, 68, 0.1);
      animation: pulse 2s infinite;
    }
    
    .hydrophone-name {
      font-weight: bold;
      color: #4fc3f7;
    }
    
    .hydrophone-location {
      font-size: 0.8rem;
      opacity: 0.8;
    }

    .last-detection {
      font-size: 0.7rem;
      color: #4fc3f7;
    }
    
    .hydrophone-status {
      font-size: 0.8rem;
      padding: 2px 6px;
      border-radius: 3px;
    }
    
    .status-online {
      background: #4caf50;
      color: white;
    }
    
    .status-offline {
      background: #f44336;
      color: white;
    }
    
    .status-detecting {
      background: #ff4444 !important;
      color: white;
      animation: blink 1s infinite;
    }

    .audio-settings {
      margin-top: 15px;
      padding-top: 15px;
      border-top: 1px solid rgba(79, 195, 247, 0.3);
    }

    .audio-settings h4 {
      margin-bottom: 10px;
    }

    .audio-settings label {
      display: block;
      margin: 8px 0;
      font-size: 0.9rem;
    }
    
    .detection-panel {
      position: absolute;
      top: 20px;
      right: 20px;
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
    
    .detection-list {
      max-height: 300px;
      overflow-y: auto;
    }

    .no-detections {
      opacity: 0.7;
      text-align: center;
      padding: 20px;
    }
    
    .detection-item {
      padding: 12px;
      margin: 8px 0;
      background: rgba(255, 68, 68, 0.1);
      border: 1px solid #ff4444;
      border-radius: 5px;
      font-size: 0.9rem;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .detection-item:hover {
      background: rgba(255, 68, 68, 0.2);
    }
    
    .detection-timestamp {
      color: #4fc3f7;
      font-weight: bold;
    }
    
    .detection-confidence {
      float: right;
      color: #4caf50;
    }

    .detection-details {
      margin-top: 5px;
    }

    .detection-stats {
      margin-top: 15px;
      padding-top: 15px;
      border-top: 1px solid rgba(79, 195, 247, 0.3);
    }

    .stat-row {
      display: flex;
      justify-content: space-between;
      margin: 5px 0;
    }
    
    .audio-controls {
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
    
    .audio-player {
      width: 100%;
      margin: 10px 0;
    }

    .current-detection {
      margin: 10px 0;
      font-weight: bold;
    }

    .audio-note {
      font-size: 0.8rem;
      opacity: 0.7;
    }
    
    .frequency-display {
      position: absolute;
      bottom: 20px;
      right: 20px;
      background: rgba(0, 30, 60, 0.95);
      padding: 15px;
      border-radius: 8px;
      border: 1px solid #4fc3f7;
      color: white;
      z-index: 1000;
      width: 300px;
    }

    .frequency-item {
      margin: 10px 0;
    }
    
    .frequency-bar {
      height: 20px;
      background: linear-gradient(90deg, #4fc3f7, #ff4444);
      margin: 5px 0;
      border-radius: 10px;
      position: relative;
      overflow: hidden;
    }
    
    .frequency-indicator {
      position: absolute;
      top: 0;
      left: 0;
      height: 100%;
      background: rgba(255, 255, 255, 0.5);
      transition: width 0.1s ease;
    }
    
    @keyframes pulse {
      0% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.7; transform: scale(1.02); }
      100% { opacity: 1; transform: scale(1); }
    }
    
    @keyframes blink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
  `]
})
export class RealtimeDetectionComponent implements OnInit, OnDestroy {
  @ViewChild('audioPlayer') audioPlayer!: ElementRef<HTMLAudioElement>;

  private destroy$ = new Subject<void>();
  private detectionSimulation$ = new Subject<void>();
  
  // Data
  hydrophones: HydrophoneData[] = [];
  recentDetections: Detection[] = [];
  selectedHydrophone: HydrophoneData | null = null;
  
  // UI State
  isLoading = false;
  autoPlay = true;
  notifications = true;
  volume = 50;
  currentDetectionText = 'No active detection';
  
  // Stats
  detectionStats: DetectionStats = {
    totalDetections: 0,
    highConfidenceDetections: 0,
    mostActiveHydrophone: '-'
  };

  // Frequency data
  frequencyData: FrequencyData = {
    lowFreq: 0,
    midFreq: 0,
    highFreq: 0
  };

  // Map
  mapOptions: google.maps.MapOptions = {
    zoom: 10,
    center: { lat: 48.5465, lng: -123.0307 },
    mapTypeId: google.maps.MapTypeId.HYBRID,
    styles: [
      {
        featureType: 'poi',
        stylers: [{ visibility: 'off' }]
      }
    ]
  };

  constructor(
    private backendService: BackendService,
    private mapService: MapService,
    private stateService: StateService
  ) {}

  ngOnInit(): void {
    this.stateService.updateCurrentView('realtime');
    this.loadHydrophoneData();
    this.startRealtimeSimulation();
    this.startFrequencySimulation();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.detectionSimulation$.next();
    this.detectionSimulation$.complete();
  }

  onMapInitialized(map: google.maps.Map): void {
    this.mapService.initializeMap(map.getDiv()!);
    this.updateMapMarkers();
  }

  loadHydrophoneData(): void {
    this.isLoading = true;
    this.backendService.getHydrophoneData()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (hydrophones) => {
          this.hydrophones = hydrophones;
          this.updateMapMarkers();
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error loading hydrophone data:', error);
          this.stateService.addError('Failed to load hydrophone data');
          this.isLoading = false;
        }
      });
  }

  refreshHydrophones(): void {
    this.loadHydrophoneData();
  }

  selectHydrophone(hydrophone: HydrophoneData): void {
    this.selectedHydrophone = hydrophone;
    
    // Center map on hydrophone
    this.mapService.centerMap(hydrophone.latitude, hydrophone.longitude, 13);
    
    // Simulate stream connection if available
    if (hydrophone.streamUrl) {
      this.currentDetectionText = `Live stream: ${hydrophone.name}`;
    }
  }

  playDetection(detection: Detection): void {
    this.currentDetectionText = 
      `${detection.hydrophone} - ${detection.callType} call (${(detection.confidence * 100).toFixed(1)}%)`;
    
    // Simulate frequency response for this detection
    this.simulateDetectionFrequency(detection);
    
    // In a real implementation, you would load actual audio
    console.log(`Playing detection: ${detection.id}`);
  }

  updateVolume(): void {
    if (this.audioPlayer?.nativeElement) {
      this.audioPlayer.nativeElement.volume = this.volume / 100;
    }
  }

  getTimeAgo(date: Date): string {
    const minutes = Math.floor((Date.now() - date.getTime()) / (1000 * 60));
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }

  private updateMapMarkers(): void {
    this.mapService.addHydrophones(this.hydrophones);
  }

  private startRealtimeSimulation(): void {
    // Simulate detections every 5 seconds
    interval(5000)
      .pipe(takeUntil(this.detectionSimulation$))
      .subscribe(() => {
        if (Math.random() < 0.15) { // 15% chance
          this.simulateDetection();
        }
      });
  }

  private startFrequencySimulation(): void {
    // Update frequency display every 200ms
    interval(200)
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        this.simulateFrequencyData();
      });
  }

  private simulateDetection(): void {
    const activeHydrophones = this.hydrophones.filter(h => h.status === 'online');
    if (activeHydrophones.length === 0) return;

    const hydrophone = activeHydrophones[Math.floor(Math.random() * activeHydrophones.length)];
    const confidence = 0.6 + Math.random() * 0.4;
    
    const detection: Detection = {
      id: Date.now(),
      timestamp: new Date(),
      hydrophone: hydrophone.name,
      hydrophoneId: hydrophone.id,
      confidence: confidence,
      frequency: 1000 + Math.random() * 4000,
      duration: 2 + Math.random() * 8,
      callType: ['resident', 'transient', 'unknown'][Math.floor(Math.random() * 3)] as any
    };

    // Update hydrophone status
    hydrophone.detecting = true;
    hydrophone.lastDetection = detection.timestamp;
    
    // Add to recent detections
    this.recentDetections.unshift(detection);
    if (this.recentDetections.length > 20) {
      this.recentDetections = this.recentDetections.slice(0, 20);
    }

    // Update displays
    this.updateDetectionStats();
    this.updateMapMarkers();

    // Auto-play if enabled
    if (this.autoPlay) {
      this.playDetection(detection);
    }

    // Sound alert if enabled
    if (this.notifications) {
      this.playNotificationSound();
    }

    // Reset detecting status after 10 seconds
    setTimeout(() => {
      hydrophone.detecting = false;
      this.updateMapMarkers();
    }, 10000);

    console.log(`🐋 Detection at ${hydrophone.name}: ${(confidence * 100).toFixed(1)}% confidence`);
  }

  private simulateFrequencyData(): void {
    this.frequencyData = {
      lowFreq: Math.random() * 30 + 10,
      midFreq: Math.random() * 50 + 20,
      highFreq: Math.random() * 20 + 5
    };
  }

  private simulateDetectionFrequency(detection: Detection): void {
    const freqRange = detection.frequency;
    let lowFreq = 0, midFreq = 0, highFreq = 0;

    if (freqRange < 1000) {
      lowFreq = 80 + Math.random() * 20;
      midFreq = 20 + Math.random() * 30;
      highFreq = 5 + Math.random() * 15;
    } else if (freqRange < 5000) {
      lowFreq = 10 + Math.random() * 20;
      midFreq = 70 + Math.random() * 30;
      highFreq = 15 + Math.random() * 25;
    } else {
      lowFreq = 5 + Math.random() * 15;
      midFreq = 20 + Math.random() * 30;
      highFreq = 60 + Math.random() * 40;
    }

    this.frequencyData = { lowFreq, midFreq, highFreq };
  }

  private playNotificationSound(): void {
    // Create a simple notification sound using Web Audio API
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gain = audioContext.createGain();
      
      oscillator.connect(gain);
      gain.connect(audioContext.destination);
      
      oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(400, audioContext.currentTime + 0.3);
      
      gain.gain.setValueAtTime(0.1, audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.3);
    } catch (error) {
      console.warn('Could not play notification sound:', error);
    }
  }

  private updateDetectionStats(): void {
    const last24h = this.recentDetections.filter(d => 
      Date.now() - d.timestamp.getTime() < 24 * 60 * 60 * 1000
    );
    
    const highConfidence = last24h.filter(d => d.confidence > 0.8);
    
    // Find most active hydrophone
    const hydrophoneCounts: Record<string, number> = {};
    last24h.forEach(d => {
      hydrophoneCounts[d.hydrophone] = (hydrophoneCounts[d.hydrophone] || 0) + 1;
    });
    
    const mostActive = Object.keys(hydrophoneCounts).reduce((a, b) => 
      hydrophoneCounts[a] > hydrophoneCounts[b] ? a : b, '-');

    this.detectionStats = {
      totalDetections: last24h.length,
      highConfidenceDetections: highConfidence.length,
      mostActiveHydrophone: mostActive
    };
  }
} 