import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { interval, Subscription, timer } from 'rxjs';

interface AgentStep {
  agent: string;
  status: 'waiting' | 'processing' | 'completed' | 'error';
  message: string;
  duration: number;
  data?: any;
}

interface DemoSlide {
  title: string;
  content: string;
  duration: number;
  mapConfig?: any;
  agentActions?: AgentStep[];
}

@Component({
  selector: 'orcast-automated-demo',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="demo-container" [class.running]="isRunning">
      <!-- Demo Control Panel -->
      <div class="demo-controls">
        <h2>🎬 ORCAST Automated Demo</h2>
        <div class="control-buttons">
          <button 
            (click)="startDemo()" 
            [disabled]="isRunning"
            class="start-btn">
            ▶️ Start Automated Demo
          </button>
          <button 
            (click)="stopDemo()" 
            [disabled]="!isRunning"
            class="stop-btn">
            ⏹️ Stop Demo
          </button>
          <button 
            (click)="resetDemo()"
            class="reset-btn">
            🔄 Reset
          </button>
        </div>
        <div class="demo-progress">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              [style.width.%]="progressPercentage">
            </div>
          </div>
          <p>Slide {{currentSlideIndex + 1}} of {{demoSlides.length}} - {{progressPercentage.toFixed(1)}}% Complete</p>
        </div>
      </div>

      <!-- Main Demo Display -->
      <div class="demo-stage" *ngIf="currentSlide">
        <div class="slide-header">
          <h1>{{currentSlide.title}}</h1>
          <div class="slide-timer">⏱️ {{slideTimeRemaining}}s</div>
        </div>
        
        <div class="slide-content">
          <div class="content-area">
            <div class="slide-text" [innerHTML]="currentSlide.content"></div>
            
            <!-- Map Configuration Area -->
            <div class="map-demo-area" *ngIf="currentSlide.mapConfig">
              <h3>🗺️ Map Configuration</h3>
              <div class="map-preview">
                <div class="map-placeholder">
                  <p>📍 {{currentSlide.mapConfig.location}}</p>
                  <p>🎯 Focus: {{currentSlide.mapConfig.focus}}</p>
                  <p>📊 Data Layers: {{currentSlide.mapConfig.layers?.join(', ')}}</p>
                </div>
                <div class="map-animations" *ngIf="currentSlide.mapConfig.animations">
                  <div 
                    *ngFor="let animation of currentSlide.mapConfig.animations" 
                    class="map-point"
                    [style.left.%]="animation.x"
                    [style.top.%]="animation.y"
                    [class]="'point-' + animation.type">
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Agent Coordination Panel -->
          <div class="agent-panel" *ngIf="currentSlide.agentActions">
            <h3>🤖 Multi-Agent Coordination</h3>
            <div class="agent-workflow">
              <div 
                *ngFor="let step of currentSlide.agentActions; trackBy: trackAgentStep" 
                class="agent-step"
                [class]="'status-' + step.status">
                <div class="agent-header">
                  <span class="agent-name">{{step.agent}}</span>
                  <span class="agent-status">{{step.status}}</span>
                </div>
                <div class="agent-message">{{step.message}}</div>
                <div class="agent-progress" *ngIf="step.status === 'processing'">
                  <div class="processing-bar"></div>
                </div>
                <div class="agent-data" *ngIf="step.data && step.status === 'completed'">
                  <pre>{{step.data | json}}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Demo Results Summary -->
      <div class="demo-results" *ngIf="isCompleted">
        <h2>✅ Demo Completed Successfully!</h2>
        <div class="results-summary">
          <div class="result-item">
            <h4>🎯 Trip Plan Generated</h4>
            <p>Optimized 3-day San Juan Islands itinerary with 87% whale encounter probability</p>
          </div>
          <div class="result-item">
            <h4>🗺️ Map Configurations</h4>
            <p>{{mapConfigurationsCount}} different map views and data overlays demonstrated</p>
          </div>
          <div class="result-item">
            <h4>🤖 Agent Interactions</h4>
            <p>{{agentInteractionsCount}} multi-agent coordination steps executed successfully</p>
          </div>
          <div class="result-item">
            <h4>📊 Data Processing</h4>
            <p>Real-time environmental data, ML predictions, and behavioral analysis integrated</p>
          </div>
        </div>
        <button class="restart-btn" (click)="restartDemo()">🔄 Restart Demo</button>
      </div>
    </div>
  `,
  styles: [`
    .demo-container {
      min-height: 100vh;
      background: linear-gradient(135deg, #001122 0%, #001f3f 100%);
      color: white;
      font-family: 'Inter', sans-serif;
      padding: 20px;
    }

    .demo-controls {
      background: rgba(79, 195, 247, 0.1);
      padding: 20px;
      border-radius: 12px;
      border: 2px solid #4fc3f7;
      margin-bottom: 30px;
    }

    .demo-controls h2 {
      color: #4fc3f7;
      margin-bottom: 20px;
      text-align: center;
    }

    .control-buttons {
      display: flex;
      gap: 15px;
      justify-content: center;
      margin-bottom: 20px;
    }

    .start-btn, .stop-btn, .reset-btn, .restart-btn {
      padding: 12px 24px;
      border: 2px solid #4fc3f7;
      border-radius: 8px;
      background: rgba(79, 195, 247, 0.2);
      color: white;
      font-size: 1rem;
      cursor: pointer;
      transition: all 0.3s ease;
    }

    .start-btn:hover, .restart-btn:hover {
      background: #4fc3f7;
      color: #001122;
      transform: translateY(-2px);
    }

    .stop-btn:hover {
      background: #ff4444;
      border-color: #ff4444;
    }

    .demo-progress {
      text-align: center;
    }

    .progress-bar {
      width: 100%;
      height: 8px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 10px;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #4fc3f7, #81d4fa);
      transition: width 0.5s ease;
      border-radius: 4px;
    }

    .demo-stage {
      background: rgba(0, 30, 60, 0.8);
      border: 2px solid #4fc3f7;
      border-radius: 15px;
      padding: 30px;
      margin-bottom: 30px;
      min-height: 600px;
    }

    .slide-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 30px;
      padding-bottom: 20px;
      border-bottom: 2px solid #4fc3f7;
    }

    .slide-header h1 {
      color: #4fc3f7;
      font-size: 2.5rem;
      margin: 0;
    }

    .slide-timer {
      background: rgba(79, 195, 247, 0.2);
      padding: 10px 20px;
      border-radius: 25px;
      border: 1px solid #4fc3f7;
      font-size: 1.2rem;
      color: #81d4fa;
    }

    .slide-content {
      display: grid;
      grid-template-columns: 1fr 400px;
      gap: 30px;
      height: 500px;
    }

    .content-area {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .slide-text {
      background: rgba(0, 0, 0, 0.3);
      padding: 25px;
      border-radius: 10px;
      border-left: 4px solid #4fc3f7;
      font-size: 1.1rem;
      line-height: 1.6;
      flex: 1;
    }

    .map-demo-area {
      background: rgba(0, 0, 0, 0.4);
      padding: 20px;
      border-radius: 10px;
      border: 1px solid #00bcd4;
    }

    .map-demo-area h3 {
      color: #00bcd4;
      margin-bottom: 15px;
    }

    .map-preview {
      position: relative;
      height: 200px;
      background: linear-gradient(45deg, #001122, #004d40);
      border-radius: 8px;
      border: 1px solid #4fc3f7;
      overflow: hidden;
    }

    .map-placeholder {
      padding: 15px;
      color: #81d4fa;
    }

    .map-placeholder p {
      margin: 5px 0;
      font-size: 0.9rem;
    }

    .map-point {
      position: absolute;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      animation: pulse 2s infinite;
    }

    .point-whale {
      background: #4fc3f7;
      box-shadow: 0 0 15px #4fc3f7;
    }

    .point-hotspot {
      background: #ff6b6b;
      box-shadow: 0 0 15px #ff6b6b;
    }

    .point-route {
      background: #4caf50;
      box-shadow: 0 0 10px #4caf50;
    }

    @keyframes pulse {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.5); opacity: 0.7; }
    }

    .agent-panel {
      background: rgba(0, 0, 0, 0.4);
      padding: 20px;
      border-radius: 10px;
      border: 1px solid #4fc3f7;
      overflow-y: auto;
    }

    .agent-panel h3 {
      color: #4fc3f7;
      margin-bottom: 20px;
    }

    .agent-workflow {
      display: flex;
      flex-direction: column;
      gap: 15px;
    }

    .agent-step {
      background: rgba(0, 0, 0, 0.3);
      padding: 15px;
      border-radius: 8px;
      border-left: 4px solid #666;
      transition: all 0.3s ease;
    }

    .agent-step.status-waiting {
      border-left-color: #666;
      opacity: 0.6;
    }

    .agent-step.status-processing {
      border-left-color: #ffeb3b;
      background: rgba(255, 235, 59, 0.1);
    }

    .agent-step.status-completed {
      border-left-color: #4caf50;
      background: rgba(76, 175, 80, 0.1);
    }

    .agent-step.status-error {
      border-left-color: #f44336;
      background: rgba(244, 67, 54, 0.1);
    }

    .agent-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .agent-name {
      font-weight: 600;
      color: #4fc3f7;
    }

    .agent-status {
      padding: 4px 8px;
      border-radius: 12px;
      font-size: 0.8rem;
      background: rgba(79, 195, 247, 0.2);
      color: #81d4fa;
    }

    .agent-message {
      color: #ccc;
      font-size: 0.9rem;
      margin-bottom: 10px;
    }

    .processing-bar {
      height: 4px;
      background: linear-gradient(90deg, #ffeb3b, #ff9800);
      border-radius: 2px;
      animation: processing 2s infinite;
    }

    @keyframes processing {
      0% { transform: translateX(-100%); }
      100% { transform: translateX(100%); }
    }

    .agent-data {
      background: rgba(0, 0, 0, 0.5);
      padding: 10px;
      border-radius: 4px;
      margin-top: 10px;
    }

    .agent-data pre {
      color: #4fc3f7;
      font-size: 0.8rem;
      margin: 0;
      white-space: pre-wrap;
    }

    .demo-results {
      background: rgba(76, 175, 80, 0.1);
      border: 2px solid #4caf50;
      border-radius: 15px;
      padding: 30px;
      text-align: center;
    }

    .demo-results h2 {
      color: #4caf50;
      margin-bottom: 30px;
    }

    .results-summary {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 30px;
    }

    .result-item {
      background: rgba(0, 0, 0, 0.3);
      padding: 20px;
      border-radius: 10px;
      border: 1px solid #4caf50;
    }

    .result-item h4 {
      color: #81c784;
      margin-bottom: 10px;
    }

    .result-item p {
      color: #ccc;
      font-size: 0.9rem;
      line-height: 1.4;
    }

    @media (max-width: 768px) {
      .slide-content {
        grid-template-columns: 1fr;
        gap: 20px;
      }
      
      .results-summary {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class AutomatedDemoComponent implements OnInit, OnDestroy {
  isRunning = false;
  isCompleted = false;
  currentSlideIndex = 0;
  currentSlide: DemoSlide | null = null;
  slideTimeRemaining = 0;
  progressPercentage = 0;
  
  mapConfigurationsCount = 0;
  agentInteractionsCount = 0;
  
  private subscription?: Subscription;
  private slideTimer?: Subscription;

  demoSlides: DemoSlide[] = [
    {
      title: "🎬 ORCAST System Introduction",
      content: `
        <h3>Welcome to the ORCAST Multi-Agent Demonstration</h3>
        <p>This automated demo showcases our <strong>Gemma 3 AI orchestration platform</strong> for marine wildlife conservation.</p>
        <ul>
          <li>🤖 <strong>Multi-agent coordination</strong> for complex decision making</li>
          <li>🌊 <strong>Real-time data integration</strong> from multiple sources</li>
          <li>🗺️ <strong>Interactive map visualizations</strong> with predictive overlays</li>
          <li>🎯 <strong>Personalized trip planning</strong> with conservation focus</li>
        </ul>
        <p>Watch as our AI agents work together to create the perfect whale watching experience!</p>
      `,
      duration: 8000,
      mapConfig: {
        location: "San Juan Islands Overview",
        focus: "Regional view with historical sighting data",
        layers: ["Base Map", "Water Depth", "Ferry Routes"],
        animations: [
          { x: 45, y: 30, type: "whale" },
          { x: 65, y: 50, type: "whale" },
          { x: 30, y: 70, type: "whale" }
        ]
      }
    },
    {
      title: "📊 Data Collection Agent Activation",
      content: `
        <h3>Step 1: Environmental Data Gathering</h3>
        <p>Our <strong>Data Collection Agent</strong> is now retrieving and processing multiple data streams:</p>
        <ul>
          <li>🌊 <strong>NOAA tidal data</strong> - Current and predicted tide levels</li>
          <li>☁️ <strong>Weather conditions</strong> - Wind, precipitation, visibility</li>
          <li>🐟 <strong>Salmon migration data</strong> - Primary orca food source tracking</li>
          <li>🎤 <strong>Hydrophone audio</strong> - Underwater sound detection</li>
          <li>🚢 <strong>Ferry schedules</strong> - Marine traffic patterns</li>
        </ul>
        <p>Real-time data integration ensures our predictions are accurate and current.</p>
      `,
      duration: 10000,
      mapConfig: {
        location: "San Juan Islands - Data Sources",
        focus: "Real-time data overlay visualization",
        layers: ["Tidal Data", "Weather Stations", "Hydrophones", "Ferry Routes"],
        animations: [
          { x: 25, y: 25, type: "hotspot" },
          { x: 75, y: 35, type: "hotspot" },
          { x: 50, y: 60, type: "hotspot" },
          { x: 40, y: 80, type: "hotspot" }
        ]
      },
      agentActions: [
        {
          agent: "🔍 Data Collection Agent",
          status: "processing",
          message: "Fetching NOAA tidal data for San Juan Islands region...",
          duration: 3000
        },
        {
          agent: "🔍 Data Collection Agent",
          status: "processing", 
          message: "Processing hydrophone audio from Lime Kiln Point station...",
          duration: 2000
        },
        {
          agent: "🔍 Data Collection Agent",
          status: "completed",
          message: "Environmental data collection complete",
          duration: 0,
          data: {
            tide_level: "2.3m rising",
            weather: "Clear, 15kt SW winds",
            salmon_count: "High activity in Haro Strait",
            hydrophone_detections: 3
          }
        }
      ]
    },
    {
      title: "🧠 Analysis Agent Processing",
      content: `
        <h3>Step 2: AI-Powered Behavioral Analysis</h3>
        <p>The <strong>Analysis Agent</strong> processes collected data through multiple ML models:</p>
        <ul>
          <li>🧠 <strong>PINN Physics Models</strong> - Ocean current and behavioral physics</li>
          <li>📈 <strong>Behavioral ML</strong> - Orca movement pattern recognition</li>
          <li>🎯 <strong>Ensemble Forecasting</strong> - Multi-model prediction fusion</li>
          <li>📊 <strong>Probability Mapping</strong> - Spatial likelihood calculations</li>
        </ul>
        <p>Advanced algorithms identify optimal whale watching locations and timing.</p>
      `,
      duration: 12000,
      mapConfig: {
        location: "Predictive Analysis Results",
        focus: "ML model probability heat maps",
        layers: ["PINN Predictions", "Behavioral ML", "Ensemble Model", "Probability Heat Map"],
        animations: [
          { x: 35, y: 40, type: "whale" },
          { x: 55, y: 45, type: "whale" },
          { x: 65, y: 35, type: "hotspot" },
          { x: 45, y: 65, type: "hotspot" },
          { x: 25, y: 55, type: "route" }
        ]
      },
      agentActions: [
        {
          agent: "📊 Analysis Agent",
          status: "processing",
          message: "Running PINN physics-informed neural network models...",
          duration: 4000
        },
        {
          agent: "📊 Analysis Agent", 
          status: "processing",
          message: "Analyzing behavioral patterns from historical sighting data...",
          duration: 3000
        },
        {
          agent: "📊 Analysis Agent",
          status: "processing",
          message: "Generating ensemble probability predictions...",
          duration: 2000
        },
        {
          agent: "📊 Analysis Agent",
          status: "completed",
          message: "Behavioral analysis complete - High probability zones identified",
          duration: 0,
          data: {
            prediction_accuracy: "87%",
            high_probability_zones: 4,
            optimal_time_window: "10:00-14:00",
            recommended_approach: "Lime Kiln Point area"
          }
        }
      ]
    },
    {
      title: "🗺️ Trip Planning Agent Coordination",
      content: `
        <h3>Step 3: Intelligent Trip Optimization</h3>
        <p>The <strong>Planning Agent</strong> creates personalized itineraries using analysis results:</p>
        <ul>
          <li>🎯 <strong>Route Optimization</strong> - Maximum whale encounter probability</li>
          <li>⏰ <strong>Timing Coordination</strong> - Peak activity window alignment</li>
          <li>🚤 <strong>Resource Allocation</strong> - Kayak rentals and guide availability</li>
          <li>🌱 <strong>Conservation Focus</strong> - Minimal ecosystem disturbance</li>
          <li>📱 <strong>Real-time Updates</strong> - Dynamic plan adjustments</li>
        </ul>
        <p>Generating comprehensive 3-day San Juan Islands whale watching itinerary...</p>
      `,
      duration: 15000,
      mapConfig: {
        location: "Optimized Trip Route",
        focus: "Multi-day itinerary with waypoints",
        layers: ["Optimal Routes", "Waypoints", "Activity Zones", "Conservation Areas"],
        animations: [
          { x: 20, y: 30, type: "route" },
          { x: 35, y: 40, type: "route" },
          { x: 50, y: 35, type: "route" },
          { x: 65, y: 45, type: "route" },
          { x: 80, y: 40, type: "route" },
          { x: 45, y: 55, type: "whale" },
          { x: 35, y: 65, type: "whale" }
        ]
      },
      agentActions: [
        {
          agent: "🗺️ Planning Agent",
          status: "processing",
          message: "Optimizing routes based on probability analysis...",
          duration: 5000
        },
        {
          agent: "🗺️ Planning Agent",
          status: "processing", 
          message: "Coordinating with local service providers...",
          duration: 3000
        },
        {
          agent: "🗺️ Planning Agent",
          status: "processing",
          message: "Generating personalized itinerary for Gil's preferences...",
          duration: 4000
        },
        {
          agent: "🗺️ Planning Agent",
          status: "completed",
          message: "Comprehensive trip plan generated successfully",
          duration: 0,
          data: {
            trip_duration: "3 days",
            whale_encounter_probability: "87%",
            optimal_locations: ["Lime Kiln Point", "San Juan Channel", "Haro Strait"],
            activities: ["Kayaking", "Photography", "Research Participation"]
          }
        }
      ]
    },
    {
      title: "🎯 Multi-Agent Coordination Results",
      content: `
        <h3>Step 4: Final Plan Integration & User Acceptance</h3>
        <p><strong>All agents have successfully coordinated</strong> to produce an optimal whale watching experience:</p>
        <ul>
          <li>📍 <strong>Day 1</strong>: Lime Kiln Point (Morning) → San Juan Channel (Afternoon)</li>
          <li>📍 <strong>Day 2</strong>: Haro Strait Kayaking → Underwater photography session</li>
          <li>📍 <strong>Day 3</strong>: Research vessel participation → Orcas Island finale</li>
        </ul>
        <p><strong>87% whale encounter probability</strong> with minimal environmental impact.</p>
        <div style="background: rgba(76, 175, 80, 0.2); padding: 15px; border-radius: 8px; margin-top: 20px;">
          <strong>✅ Plan Accepted by User "Gil"</strong><br>
          <em>Automated acceptance based on preference matching and probability thresholds</em>
        </div>
      `,
      duration: 10000,
      mapConfig: {
        location: "Final Trip Plan Overview", 
        focus: "Complete 3-day itinerary visualization",
        layers: ["Day 1 Route", "Day 2 Route", "Day 3 Route", "Accommodation", "Activities"],
        animations: [
          { x: 30, y: 35, type: "whale" },
          { x: 45, y: 50, type: "whale" },
          { x: 60, y: 40, type: "whale" },
          { x: 25, y: 60, type: "route" },
          { x: 70, y: 55, type: "route" },
          { x: 55, y: 70, type: "hotspot" }
        ]
      },
      agentActions: [
        {
          agent: "🤖 Agent Coordinator",
          status: "completed",
          message: "Multi-agent workflow completed successfully",
          duration: 0,
          data: {
            total_execution_time: "45 seconds",
            agents_coordinated: 3,
            data_sources_integrated: 7,
            final_accuracy: "87%"
          }
        },
        {
          agent: "👤 User Simulation",
          status: "completed", 
          message: "Plan automatically accepted - meets all criteria",
          duration: 0,
          data: {
            user_preferences_matched: "100%",
            probability_threshold_met: true,
            conservation_guidelines_followed: true,
            budget_within_range: true
          }
        }
      ]
    }
  ];

  ngOnInit() {
    this.resetDemo();
  }

  ngOnDestroy() {
    this.stopDemo();
  }

  startDemo() {
    this.isRunning = true;
    this.isCompleted = false;
    this.currentSlideIndex = 0;
    this.progressPercentage = 0;
    this.mapConfigurationsCount = 0;
    this.agentInteractionsCount = 0;
    
    this.runSlideshow();
  }

  stopDemo() {
    this.isRunning = false;
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
    if (this.slideTimer) {
      this.slideTimer.unsubscribe();
    }
  }

  resetDemo() {
    this.stopDemo();
    this.currentSlideIndex = 0;
    this.currentSlide = null;
    this.isCompleted = false;
    this.progressPercentage = 0;
    this.slideTimeRemaining = 0;
  }

  restartDemo() {
    this.resetDemo();
    this.startDemo();
  }

  private runSlideshow() {
    if (this.currentSlideIndex >= this.demoSlides.length) {
      this.completeDemo();
      return;
    }

    this.currentSlide = this.demoSlides[this.currentSlideIndex];
    this.slideTimeRemaining = Math.ceil(this.currentSlide.duration / 1000);
    
    // Count configurations and interactions
    if (this.currentSlide.mapConfig) {
      this.mapConfigurationsCount++;
    }
    if (this.currentSlide.agentActions) {
      this.agentInteractionsCount += this.currentSlide.agentActions.length;
    }

    // Run agent actions
    if (this.currentSlide.agentActions) {
      this.runAgentActions(this.currentSlide.agentActions);
    }

    // Update slide timer
    this.slideTimer = interval(1000).subscribe(() => {
      this.slideTimeRemaining--;
      if (this.slideTimeRemaining <= 0) {
        this.nextSlide();
      }
    });

    // Update progress
    this.progressPercentage = ((this.currentSlideIndex + 1) / this.demoSlides.length) * 100;
  }

  private runAgentActions(actions: AgentStep[]) {
    let currentTime = 0;
    
    actions.forEach((action, index) => {
      if (action.status === 'processing') {
        timer(currentTime).subscribe(() => {
          action.status = 'processing';
        });
        
        timer(currentTime + action.duration).subscribe(() => {
          action.status = 'completed';
        });
        
        currentTime += action.duration;
      }
    });
  }

  private nextSlide() {
    if (this.slideTimer) {
      this.slideTimer.unsubscribe();
    }
    
    this.currentSlideIndex++;
    this.runSlideshow();
  }

  private completeDemo() {
    this.isRunning = false;
    this.isCompleted = true;
    this.progressPercentage = 100;
    
    if (this.slideTimer) {
      this.slideTimer.unsubscribe();
    }
  }

  trackAgentStep(index: number, step: AgentStep): string {
    return `${step.agent}-${index}`;
  }
} 