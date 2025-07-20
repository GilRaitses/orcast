import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

import { AgentOrchestratorService, AgentMessage, SpatialForecast } from '../../services/agent-orchestrator.service';
import { MapConfigurationService, MapConfiguration, MapConfigRequest } from '../../services/map-configuration.service';

@Component({
  selector: 'orcast-agent-spatial-demo',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="agent-spatial-demo">
      <!-- Header -->
      <div class="header">
        <h1>ORCAST Agent-Driven Spatial Planning</h1>
        <p class="subtitle">Multi-Agent Orchestration for Whale Research & Trip Planning</p>
        
        <div class="demo-controls">
          <button 
            (click)="startAgentDemo()" 
            [disabled]="isRunning"
            class="start-btn">
            🤖 Start Agent Orchestration
          </button>
          <button 
            (click)="generateMapConfig()" 
            [disabled]="isRunning"
            class="map-btn">
            🗺️ Generate Map Configuration
          </button>
          <button 
            (click)="clearLogs()"
            class="clear-btn">
            🧹 Clear Logs
          </button>
        </div>
      </div>

      <!-- Agent Interaction Interface -->
      <div class="agent-interaction-panel">
        <div class="interaction-header">
          <h3>💬 Chat with Individual Agents</h3>
          <button 
            (click)="toggleAgentChat()"
            class="toggle-chat-btn"
            [class.active]="showAgentChat">
            {{showAgentChat ? '🔽 Hide Chat' : '🔼 Show Agent Chat'}}
          </button>
        </div>
        
        <div class="agent-chat-interface" *ngIf="showAgentChat">
          <div class="agent-selector">
            <div class="agent-tabs">
              <button 
                *ngFor="let agent of availableAgents"
                (click)="selectAgent(agent.id)"
                [class.active]="selectedAgent === agent.id"
                class="agent-tab">
                {{agent.icon}} {{agent.name}}
              </button>
            </div>
          </div>
          
          <div class="current-agent-info" *ngIf="getCurrentAgent()">
            <div class="agent-details">
              <h4>{{getCurrentAgent()?.icon}} {{getCurrentAgent()?.name}}</h4>
              <p class="agent-description">{{getCurrentAgent()?.description}}</p>
              <div class="agent-capabilities">
                <span class="capability-label">Capabilities:</span>
                <span *ngFor="let capability of getCurrentAgent()?.capabilities" class="capability-tag">
                  {{capability}}
                </span>
              </div>
            </div>
          </div>
          
          <div class="prompt-interface">
            <div class="prompt-input-section">
              <textarea 
                [(ngModel)]="currentPrompt"
                placeholder="Type your message to {{getCurrentAgent()?.name || 'the selected agent'}}..."
                class="prompt-textarea"
                rows="3"
                (keydown)="onPromptKeydown($event)">
              </textarea>
              <div class="input-controls">
                <div class="input-hints">
                  <span class="hint">Ctrl+Enter to send</span>
                  <span class="char-count">{{currentPrompt.length}}/500</span>
                </div>
                <button 
                  (click)="sendPromptToAgent()"
                  [disabled]="!currentPrompt.trim() || isProcessingPrompt"
                  class="send-prompt-btn">
                  {{isProcessingPrompt ? '⏳ Processing...' : '🚀 Send to ' + (getCurrentAgent()?.name || 'Agent')}}
                </button>
              </div>
            </div>
          </div>
          
          <div class="quick-prompts">
            <h5>💡 Quick Prompts:</h5>
            <div class="quick-prompt-buttons">
              <button 
                *ngFor="let prompt of getQuickPrompts()"
                (click)="useQuickPrompt(prompt.text)"
                class="quick-prompt-btn">
                {{prompt.label}}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="main-content">
        <!-- Left Panel: Agent Communication -->
        <div class="agent-panel">
          <div class="panel-header">
            <h3>🤖 Agent Communication Log</h3>
            <div class="agent-status">
              <span [class.active]="isRunning">
                {{isRunning ? 'Agents Active' : 'Ready'}}
              </span>
            </div>
          </div>
          
          <div class="agent-messages" #messagesContainer>
            <div 
              *ngFor="let message of agentMessages; trackBy: trackMessage"
              class="message"
              [class]="'message-' + message.type">
              
              <div class="message-header">
                <span class="agent-name">{{message.agent}}</span>
                <span class="timestamp">{{message.timestamp | date:'HH:mm:ss.SSS'}}</span>
              </div>
              
              <div class="message-content">{{message.message}}</div>
              
              <div class="message-data" *ngIf="message.data">
                <details>
                  <summary>Data Details</summary>
                  <pre>{{message.data | json}}</pre>
                </details>
              </div>
              
              <div class="data-source-info" *ngIf="message.data?.dataSourcesUsed">
                <h5>📊 Data Sources Used:</h5>
                <ul>
                  <li *ngFor="let source of message.data.dataSourcesUsed">
                    ✅ {{source}}
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <!-- Center: Map Configuration Display -->
        <div class="map-config-panel">
          <div class="panel-header">
            <h3>🗺️ Agent-Generated Map Configuration</h3>
            <div class="config-status">
              <span *ngIf="currentMapConfig">
                Generated by: {{currentMapConfig.generatedBy.agent}}
              </span>
              <button 
                (click)="toggleForecastOverlay()"
                class="toggle-overlay-btn"
                [class.active]="showForecastOverlay">
                {{showForecastOverlay ? '🔽 Hide Forecast' : '🔼 Show Forecast'}}
              </button>
            </div>
          </div>
          
          <div class="map-display" #mapContainer>
            <!-- Map will be rendered here -->
            <div id="agent-map" class="map-canvas"></div>
            
            <!-- Heat Map Canvas Overlay -->
            <canvas 
              #heatmapCanvas 
              class="heatmap-overlay"
              width="800" 
              height="600">
            </canvas>
            
            <!-- Configuration Overlay - Now Collapsible -->
            <div 
              class="config-overlay" 
              *ngIf="currentMapConfig && showForecastOverlay"
              [class.collapsed]="!showForecastOverlay">
              <div class="overlay-header">
                <h4>🎯 Forecast Overview</h4>
                <button 
                  (click)="toggleForecastOverlay()"
                  class="close-overlay-btn">×</button>
              </div>
              
              <div class="overlay-info">
                <p>{{currentMapConfig.UIStates.agentInterface.forecastOverview}}</p>
                
                <h4>⏰ Interactive Timeline</h4>
                <div class="timeline-controls">
                  <button 
                    *ngFor="let slice of currentMapConfig.UIStates.temporalSlider.timeSlices; let i = index"
                    (click)="selectTimeSlice(i)"
                    [class.active]="selectedTimeSlice === i"
                    class="time-slice-btn">
                    {{slice.label}}
                  </button>
                </div>
                
                <h4>🎛️ Layer Controls</h4>
                <div class="layer-controls">
                  <div 
                    *ngFor="let overlay of currentMapConfig.overlays"
                    class="layer-control">
                    <label>
                      <input 
                        type="checkbox" 
                        [checked]="overlay.visible"
                        (change)="toggleLayer(overlay.id, $event)">
                      {{overlay.id | titlecase}}
                    </label>
                    <div class="source-info">
                      📊 Source: {{overlay.source.name}}
                      ({{(overlay.source.confidenceLevel * 100).toFixed(1)}}% confidence)
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Panel: Spatial Forecasts -->
        <div class="forecast-panel">
          <div class="panel-header">
            <h3>🎯 Spatial Forecasts</h3>
            <div class="forecast-count">
              {{spatialForecasts.length}} predictions
            </div>
          </div>
          
          <div class="forecast-list">
            <div 
              *ngFor="let forecast of spatialForecasts.slice(-10); trackBy: trackForecast"
              class="forecast-item"
              [class]="'model-' + forecast.model">
              
              <div class="forecast-header">
                <span class="behavior">{{forecast.behavior | titlecase}}</span>
                <span class="probability">{{(forecast.probability * 100).toFixed(1)}}%</span>
              </div>
              
              <div class="forecast-details">
                <div class="location">
                  📍 {{forecast.location.lat.toFixed(4)}}, {{forecast.location.lng.toFixed(4)}}
                </div>
                <div class="model-info">
                  🤖 Model: {{forecast.model.toUpperCase()}}
                  ({{(forecast.confidence * 100).toFixed(1)}}% confidence)
                </div>
                <div class="timestamp">
                  ⏰ {{forecast.timestamp | date:'HH:mm:ss'}}
                </div>
              </div>
            </div>
          </div>
          
          <div class="data-source-verification">
            <h4>🔍 Data Source Verification</h4>
            <div *ngIf="currentMapConfig" class="source-list">
              <div 
                *ngFor="let source of currentMapConfig.dataSources"
                class="source-item">
                <div class="source-name">{{source.name}}</div>
                <div class="source-details">
                  <span class="provider">{{source.provider}}</span>
                  <span class="verified" [class.yes]="source.verified">
                    {{source.verified ? '✅ Verified' : '❌ Unverified'}}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .agent-spatial-demo {
      height: 100vh;
      background: linear-gradient(135deg, #001122 0%, #001f3f 100%);
      color: white;
      font-family: 'Inter', sans-serif;
      display: flex;
      flex-direction: column;
    }

    .header {
      padding: 20px 30px;
      background: rgba(0, 30, 60, 0.9);
      border-bottom: 2px solid #4fc3f7;
    }

    .header h1 {
      color: #4fc3f7;
      font-size: 2.2rem;
      margin: 0 0 5px 0;
    }

    .subtitle {
      color: #81d4fa;
      margin: 0 0 20px 0;
      font-size: 1.1rem;
    }

    .demo-controls {
      display: flex;
      gap: 15px;
      align-items: center;
    }

    .start-btn, .map-btn, .clear-btn {
      padding: 12px 24px;
      border: 2px solid #4fc3f7;
      background: rgba(79, 195, 247, 0.2);
      color: white;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
      font-weight: 600;
    }

    .start-btn:hover, .map-btn:hover {
      background: #4fc3f7;
      color: #001122;
    }

    .clear-btn:hover {
      background: #ff4444;
      border-color: #ff4444;
    }

    .start-btn:disabled, .map-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .main-content {
      flex: 1;
      display: grid;
      grid-template-columns: 400px 1fr 350px;
      gap: 0;
    }

    /* Agent Panel */
    .agent-panel {
      background: rgba(0, 30, 60, 0.8);
      border-right: 2px solid #4fc3f7;
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

    .agent-status span {
      padding: 5px 12px;
      background: rgba(0, 0, 0, 0.3);
      border-radius: 12px;
      font-size: 0.9rem;
    }

    .agent-status span.active {
      background: rgba(76, 175, 80, 0.3);
      color: #4caf50;
    }

    .agent-messages {
      flex: 1;
      overflow-y: auto;
      padding: 15px;
    }

    .message {
      background: rgba(0, 0, 0, 0.3);
      margin-bottom: 12px;
      padding: 15px;
      border-radius: 8px;
      border-left: 4px solid #666;
      animation: slideIn 0.3s ease;
    }

    .message-processing { border-left-color: #ffeb3b; }
    .message-data { border-left-color: #2196f3; }
    .message-analysis { border-left-color: #9c27b0; }
    .message-prediction { border-left-color: #4caf50; }
    .message-coordination { border-left-color: #ff9800; }
    .message-reasoning { border-left-color: #e91e63; }
    .message-orchestration { border-left-color: #00bcd4; }

    .message-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
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
      font-size: 0.95rem;
      line-height: 1.4;
      margin-bottom: 10px;
    }

    .message-data details {
      margin-top: 8px;
    }

    .message-data summary {
      cursor: pointer;
      color: #81d4fa;
      font-size: 0.9rem;
    }

    .message-data pre {
      font-size: 0.8rem;
      color: #81d4fa;
      margin: 8px 0 0 0;
      background: rgba(0, 0, 0, 0.3);
      padding: 10px;
      border-radius: 4px;
      overflow-x: auto;
    }

    .data-source-info {
      margin-top: 10px;
      padding: 10px;
      background: rgba(76, 175, 80, 0.1);
      border-radius: 4px;
      border: 1px solid #4caf50;
    }

    .data-source-info h5 {
      margin: 0 0 8px 0;
      color: #4caf50;
      font-size: 0.9rem;
    }

    .data-source-info ul {
      margin: 0;
      padding-left: 20px;
    }

    .data-source-info li {
      color: #ccc;
      font-size: 0.85rem;
    }

    /* Map Config Panel */
    .map-config-panel {
      background: rgba(0, 0, 0, 0.2);
      display: flex;
      flex-direction: column;
      position: relative;
    }

    .config-status {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
    }

    .config-status span {
      font-size: 0.9rem;
      color: #81d4fa;
    }

    .toggle-overlay-btn, .close-overlay-btn {
      padding: 6px 12px;
      background: rgba(79, 195, 247, 0.3);
      border: 1px solid #4fc3f7;
      color: white;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.8rem;
      transition: all 0.2s ease;
    }

    .toggle-overlay-btn:hover, .close-overlay-btn:hover {
      background: #4fc3f7;
      color: #001122;
    }

    .toggle-overlay-btn.active {
      background: #4fc3f7;
      color: #001122;
    }

    .map-display {
      flex: 1;
      position: relative;
    }

    .map-canvas {
      width: 100%;
      height: 100%;
      background: linear-gradient(45deg, #001122, #004d40);
      position: relative;
      overflow: visible;
      pointer-events: auto; /* Ensure map can receive scroll events */
    }

    /* Heat Map Overlay */
    .heatmap-overlay {
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 2;
    }

    /* Configuration Overlay - FIXED */
    .config-overlay {
      position: absolute;
      top: 20px;
      left: 20px;
      right: 20px;
      background: rgba(0, 30, 60, 0.95);
      border: 1px solid #4fc3f7;
      border-radius: 8px;
      max-height: calc(100% - 40px);
      overflow-y: auto;
      z-index: 10;
      pointer-events: auto; /* Allow interaction with overlay */
      transition: transform 0.3s ease;
    }

    .config-overlay.collapsed {
      transform: translateY(-100%);
      pointer-events: none;
    }

    .overlay-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 15px 20px;
      border-bottom: 1px solid #4fc3f7;
    }

    .overlay-header h4 {
      margin: 0;
      color: #4fc3f7;
      font-size: 1rem;
    }

    .close-overlay-btn {
      background: none;
      border: none;
      color: white;
      font-size: 1.5rem;
      cursor: pointer;
      padding: 0;
      width: 30px;
      height: 30px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .overlay-info {
      padding: 20px;
    }

    .overlay-info h4 {
      color: #4fc3f7;
      margin: 0 0 10px 0;
      font-size: 1rem;
    }

    .overlay-info p {
      color: #ccc;
      font-size: 0.9rem;
      line-height: 1.4;
      margin-bottom: 20px;
    }

    .timeline-controls {
      display: flex;
      gap: 8px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }

    .time-slice-btn {
      padding: 6px 12px;
      background: rgba(79, 195, 247, 0.2);
      border: 1px solid #4fc3f7;
      color: white;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.8rem;
      transition: all 0.2s ease;
    }

    .time-slice-btn.active {
      background: #4fc3f7;
      color: #001122;
    }

    .layer-controls {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .layer-control label {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      color: #ccc;
      font-size: 0.9rem;
    }

    .source-info {
      font-size: 0.8rem;
      color: #81d4fa;
      margin-left: 24px;
      margin-top: 4px;
    }

    /* Forecast Panel */
    .forecast-panel {
      background: rgba(0, 30, 60, 0.8);
      border-left: 2px solid #4fc3f7;
      display: flex;
      flex-direction: column;
    }

    .forecast-count {
      background: rgba(79, 195, 247, 0.2);
      padding: 5px 10px;
      border-radius: 12px;
      font-size: 0.9rem;
      color: #81d4fa;
    }

    .forecast-list {
      flex: 1;
      overflow-y: auto;
      padding: 15px;
    }

    .forecast-item {
      background: rgba(0, 0, 0, 0.3);
      margin-bottom: 12px;
      padding: 12px;
      border-radius: 6px;
      border-left: 4px solid #666;
    }

    .model-pinn { border-left-color: #4fc3f7; }
    .model-behavioral { border-left-color: #9c27b0; }
    .model-ensemble { border-left-color: #4caf50; }

    .forecast-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
    }

    .behavior {
      font-weight: 600;
      color: #4fc3f7;
    }

    .probability {
      font-weight: 600;
      color: #4caf50;
    }

    .forecast-details {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }

    .location, .model-info, .timestamp {
      font-size: 0.8rem;
      color: #ccc;
    }

    .data-source-verification {
      padding: 15px;
      border-top: 1px solid #4fc3f7;
    }

    .data-source-verification h4 {
      margin: 0 0 10px 0;
      color: #4fc3f7;
      font-size: 1rem;
    }

    .source-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .source-item {
      background: rgba(0, 0, 0, 0.3);
      padding: 10px;
      border-radius: 4px;
    }

    .source-name {
      font-weight: 600;
      color: #81d4fa;
      font-size: 0.9rem;
      margin-bottom: 4px;
    }

    .source-details {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .provider {
      font-size: 0.8rem;
      color: #ccc;
    }

    .verified {
      font-size: 0.8rem;
      padding: 2px 6px;
      border-radius: 3px;
      background: rgba(244, 67, 54, 0.2);
      color: #f44336;
    }

    .verified.yes {
      background: rgba(76, 175, 80, 0.2);
      color: #4caf50;
    }

    @keyframes slideIn {
      from { transform: translateX(-20px); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }

    /* Agent Interaction Panel Styles */
    .agent-interaction-panel {
      background: rgba(0, 20, 40, 0.95);
      border-top: 2px solid #4fc3f7;
      border-bottom: 2px solid #4fc3f7;
    }

    .interaction-header {
      padding: 15px 30px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(0, 30, 60, 0.8);
    }

    .interaction-header h3 {
      margin: 0;
      color: #4fc3f7;
      font-size: 1.4rem;
    }

    .toggle-chat-btn {
      padding: 8px 16px;
      background: rgba(79, 195, 247, 0.3);
      border: 1px solid #4fc3f7;
      color: white;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .toggle-chat-btn:hover, .toggle-chat-btn.active {
      background: #4fc3f7;
      color: #001122;
    }

    .agent-chat-interface {
      padding: 20px 30px;
    }

    .agent-tabs {
      display: flex;
      gap: 10px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }

    .agent-tab {
      padding: 10px 15px;
      background: rgba(79, 195, 247, 0.2);
      border: 1px solid #4fc3f7;
      color: white;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.2s ease;
      font-size: 0.9rem;
    }

    .agent-tab:hover {
      background: rgba(79, 195, 247, 0.4);
    }

    .agent-tab.active {
      background: #4fc3f7;
      color: #001122;
      font-weight: 600;
    }

    .current-agent-info {
      background: rgba(0, 30, 60, 0.6);
      border: 1px solid #4fc3f7;
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 20px;
    }

    .agent-details h4 {
      margin: 0 0 10px 0;
      color: #4fc3f7;
      font-size: 1.2rem;
    }

    .agent-description {
      color: #81d4fa;
      margin: 0 0 15px 0;
      line-height: 1.4;
    }

    .agent-capabilities {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }

    .capability-label {
      color: #ccc;
      font-weight: 600;
      margin-right: 5px;
    }

    .capability-tag {
      background: rgba(76, 175, 80, 0.3);
      color: #81c784;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 0.8rem;
      border: 1px solid #4caf50;
    }

    .prompt-interface {
      margin-bottom: 20px;
    }

    .prompt-textarea {
      width: 100%;
      background: rgba(0, 30, 60, 0.8);
      border: 1px solid #4fc3f7;
      color: white;
      padding: 15px;
      border-radius: 6px;
      font-family: inherit;
      font-size: 0.9rem;
      resize: vertical;
      min-height: 80px;
    }

    .prompt-textarea:focus {
      outline: none;
      border-color: #81d4fa;
      box-shadow: 0 0 0 2px rgba(79, 195, 247, 0.2);
    }

    .prompt-textarea::placeholder {
      color: #666;
    }

    .input-controls {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 10px;
    }

    .input-hints {
      display: flex;
      gap: 15px;
      font-size: 0.8rem;
      color: #666;
    }

    .char-count {
      color: #888;
    }

    .send-prompt-btn {
      padding: 10px 20px;
      background: linear-gradient(45deg, #4fc3f7, #29b6f6);
      border: none;
      color: white;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
      transition: all 0.2s ease;
    }

    .send-prompt-btn:hover:not(:disabled) {
      background: linear-gradient(45deg, #29b6f6, #4fc3f7);
      transform: translateY(-1px);
    }

    .send-prompt-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none;
    }

    .quick-prompts h5 {
      margin: 0 0 10px 0;
      color: #4fc3f7;
      font-size: 1rem;
    }

    .quick-prompt-buttons {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .quick-prompt-btn {
      padding: 8px 12px;
      background: rgba(255, 193, 7, 0.2);
      border: 1px solid #ffc107;
      color: #ffd54f;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.8rem;
      transition: all 0.2s ease;
    }

    .quick-prompt-btn:hover {
      background: rgba(255, 193, 7, 0.3);
      color: white;
    }
  `]
})
export class AgentSpatialDemoComponent implements OnInit, OnDestroy {
  @ViewChild('messagesContainer') messagesContainer!: ElementRef;
  @ViewChild('mapContainer') mapContainer!: ElementRef;
  @ViewChild('heatmapCanvas') heatmapCanvas!: ElementRef<HTMLCanvasElement>;

  agentMessages: AgentMessage[] = [];
  spatialForecasts: SpatialForecast[] = [];
  currentMapConfig: MapConfiguration | null = null;
  selectedTimeSlice = 0;
  isRunning = false;
  showForecastOverlay = false; // Start with overlay hidden

  // Agent interaction properties
  showAgentChat = false;
  selectedAgent = 'primary';
  currentPrompt = '';
  isProcessingPrompt = false;
  
  availableAgents = [
    {
      id: 'primary',
      name: 'Primary Planning Agent',
      icon: '🎯',
      description: 'Orchestrates overall trip planning and coordinates other agents',
      capabilities: ['Trip Planning', 'Coordination', 'Route Optimization']
    },
    {
      id: 'analytics',
      name: 'Analytics Agent',
      icon: '📊',
      description: 'Gathers and analyzes whale sighting statistics and patterns',
      capabilities: ['Data Analysis', 'Statistical Modeling', 'Historical Trends']
    },
    {
      id: 'spatial',
      name: 'Spatial Forecast Agent',
      icon: '🗺️',
      description: 'Generates spatial forecasts and behavioral predictions',
      capabilities: ['ML Predictions', 'Spatial Analysis', 'Behavior Modeling']
    },
    {
      id: 'research',
      name: 'Whale Research Agent',
      icon: '🐋',
      description: 'Specialized in whale behavior and marine biology research',
      capabilities: ['Behavioral Analysis', 'Marine Biology', 'Species Identification']
    },
    {
      id: 'environmental',
      name: 'Environmental Agent',
      icon: '🌊',
      description: 'Analyzes environmental conditions and weather patterns',
      capabilities: ['Weather Analysis', 'Ocean Conditions', 'Environmental Factors']
    }
  ];

  private subscriptions: Subscription[] = [];

  constructor(
    private agentOrchestrator: AgentOrchestratorService,
    private mapConfigService: MapConfigurationService
  ) {}

  ngOnInit() {
    // Subscribe to agent messages
    this.subscriptions.push(
      this.agentOrchestrator.agentMessages$.subscribe(messages => {
        this.agentMessages = messages;
        this.scrollToLatestMessage();
      })
    );

    // Subscribe to spatial forecasts
    this.subscriptions.push(
      this.agentOrchestrator.spatialForecasts$.subscribe(forecasts => {
        this.spatialForecasts = forecasts;
        this.updateHeatMap();
      })
    );

    // Subscribe to map configurations
    this.subscriptions.push(
      this.mapConfigService.mapConfig$.subscribe(config => {
        this.currentMapConfig = config;
        if (config) {
          this.initializeMap(config);
        }
      })
    );

    console.log('🤖 Agent Spatial Demo Component initialized');
  }

  ngOnDestroy() {
    this.subscriptions.forEach(sub => sub.unsubscribe());
  }

  startAgentDemo() {
    this.isRunning = true;
    console.log('🚀 Starting multi-agent demo...');
    
    // Generate some demo forecasts
    this.generateDemoForecasts();
  }

  generateMapConfig() {
    if (!this.isRunning) {
      this.isRunning = true;
    }
    
    // Generate demo map config  
    this.currentMapConfig = {
      generatedBy: { agent: 'ORCAST Spatial Planning Agent' } as any,
      UIStates: {
        agentInterface: {
          forecastOverview: 'Based on analysis of 473 verified whale sightings from OBIS research database and real-time environmental data from NOAA APIs, current whale behavior probability in the San Juan Islands shows excellent conditions for whale watching.'
        } as any,
        temporalSlider: {
          timeSlices: [] as any
        }
      },
      overlays: [] as any,
      dataSources: [] as any,
      mapOptions: {
        center: { lat: 48.5465, lng: -123.0307 },
        zoom: 12
      }
    } as any;
    
    this.showForecastOverlay = true;
    console.log('🗺️ Generated map configuration');
  }

  clearLogs() {
    this.agentOrchestrator.clearAgentMessages();
    this.agentMessages = [];
  }

  selectTimeSlice(index: number) {
    this.selectedTimeSlice = index;
    console.log('⏰ Selected time slice:', index);
    // Update map visualization for selected time slice
  }

  toggleLayer(layerId: string, event: Event) {
    const target = event.target as HTMLInputElement;
    console.log(`🎛️ Toggle layer ${layerId}:`, target.checked);
    // Update map layer visibility
  }

  toggleForecastOverlay() {
    this.showForecastOverlay = !this.showForecastOverlay;
    console.log('🔽 Toggle forecast overlay:', this.showForecastOverlay);
  }

  // Agent interaction methods
  toggleAgentChat() {
    this.showAgentChat = !this.showAgentChat;
    console.log('💬 Toggle agent chat:', this.showAgentChat);
  }

  selectAgent(agentId: string) {
    this.selectedAgent = agentId;
    this.currentPrompt = ''; // Clear prompt when switching agents
    console.log('🤖 Selected agent:', agentId);
  }

  getCurrentAgent() {
    return this.availableAgents.find(agent => agent.id === this.selectedAgent);
  }

  async sendPromptToAgent() {
    if (!this.currentPrompt.trim() || this.isProcessingPrompt) {
      return;
    }

    const prompt = this.currentPrompt.trim();
    const agentId = this.selectedAgent;
    const agent = this.getCurrentAgent();
    
    this.isProcessingPrompt = true;
    console.log(`💬 Sending prompt to ${agent?.name}:`, prompt);

    try {
      // Add user message to the log
      this.agentOrchestrator.addAgentMessage(
        '👤 User', 
        'processing',
        `To ${agent?.name}: "${prompt}"`
      );

      // Process the prompt based on agent type
      await this.processAgentPrompt(agentId, prompt);

      this.currentPrompt = ''; // Clear the prompt after sending
    } catch (error) {
      console.error('❌ Error processing agent prompt:', error);
      this.agentOrchestrator.addAgentMessage(
        '⚠️ System', 
        'coordination',
        `Error processing prompt: ${error}`
      );
    } finally {
      this.isProcessingPrompt = false;
    }
  }

  private async processAgentPrompt(agentId: string, prompt: string) {
    const agent = this.getCurrentAgent();
    
    switch (agentId) {
      case 'primary':
        this.agentOrchestrator.addAgentMessage(
          '🎯 Primary Planning Agent', 
          'orchestration',
          `Processing trip planning request: "${prompt}"`
        );
        
        // Simulate primary agent response
        await this.delay(1000);
        this.agentOrchestrator.addAgentMessage(
          '🎯 Primary Planning Agent', 
          'orchestration',
          `I'll coordinate the other agents to help with: ${prompt}. Starting multi-agent analysis...`
        );
        
        // Start orchestration if not already running
        if (!this.isRunning) {
          this.startAgentDemo();
        }
        break;

      case 'analytics':
        this.agentOrchestrator.addAgentMessage(
          '📊 Analytics Agent', 
          'data',
          `Analyzing historical data for: "${prompt}"`
        );
        
        await this.delay(800);
        this.agentOrchestrator.addAgentMessage(
          '📊 Analytics Agent', 
          'data',
          `Based on 473 verified whale sightings, I can provide statistical analysis relevant to your query: ${prompt}`
        );
        break;

      case 'spatial':
        this.agentOrchestrator.addAgentMessage(
          '🗺️ Spatial Forecast Agent', 
          'prediction',
          `Generating spatial forecasts for: "${prompt}"`
        );
        
        await this.delay(1200);
        // Generate some forecasts
        this.generateDemoForecasts();
        this.agentOrchestrator.addAgentMessage(
          '🗺️ Spatial Forecast Agent', 
          'prediction',
          `Generated spatial behavioral predictions based on your request: ${prompt}`
        );
        break;

      case 'research':
        this.agentOrchestrator.addAgentMessage(
          '🐋 Whale Research Agent', 
          'analysis',
          `Researching whale behavior for: "${prompt}"`
        );
        
        await this.delay(900);
        this.agentOrchestrator.addAgentMessage(
          '🐋 Whale Research Agent', 
          'analysis',
          `Based on marine biology research, here's what I found about: ${prompt}. Orcas in the San Juan Islands exhibit complex social behaviors...`
        );
        break;

      case 'environmental':
        this.agentOrchestrator.addAgentMessage(
          '🌊 Environmental Agent', 
          'data',
          `Analyzing environmental conditions for: "${prompt}"`
        );
        
        await this.delay(700);
        this.agentOrchestrator.addAgentMessage(
          '🌊 Environmental Agent', 
          'data',
          `Current environmental analysis for ${prompt}: Sea conditions are optimal, water temperature favorable for whale activity.`
        );
        break;

      default:
        this.agentOrchestrator.addAgentMessage(
          '❓ Unknown Agent', 
          'coordination',
          `Received prompt: "${prompt}" but agent type "${agentId}" not recognized.`
        );
    }
  }

  getQuickPrompts() {
    const agent = this.getCurrentAgent();
    
    const promptsByAgent: { [key: string]: Array<{label: string, text: string}> } = {
      primary: [
        { label: 'Plan Trip', text: 'Help me plan a 3-day whale watching trip in the San Juan Islands' },
        { label: 'Best Times', text: 'What are the optimal times for whale watching this week?' },
        { label: 'Route Planning', text: 'Suggest the best viewing locations and travel routes' }
      ],
      analytics: [
        { label: 'Historical Data', text: 'Show me whale sighting statistics for the past 6 months' },
        { label: 'Success Rates', text: 'What are the success rates for different viewing locations?' },
        { label: 'Seasonal Patterns', text: 'Analyze seasonal whale behavior patterns' }
      ],
      spatial: [
        { label: 'Generate Forecasts', text: 'Create spatial forecasts for the next 24 hours' },
        { label: 'Behavior Prediction', text: 'Predict feeding and socializing locations' },
        { label: 'Probability Maps', text: 'Generate probability heatmaps for whale sightings' }
      ],
      research: [
        { label: 'Whale Behavior', text: 'Explain current orca pod behaviors and feeding patterns' },
        { label: 'Species Info', text: 'Tell me about the resident orca populations' },
        { label: 'Research Insights', text: 'Share latest marine biology research findings' }
      ],
      environmental: [
        { label: 'Weather Conditions', text: 'Analyze current weather and sea conditions' },
        { label: 'Water Temperature', text: 'How do water temperatures affect whale behavior?' },
        { label: 'Environmental Factors', text: 'What environmental factors influence whale sightings?' }
      ]
    };

    return promptsByAgent[this.selectedAgent] || [];
  }

  useQuickPrompt(promptText: string) {
    this.currentPrompt = promptText;
  }

  onPromptKeydown(event: KeyboardEvent) {
    if (event.ctrlKey && event.key === 'Enter') {
      this.sendPromptToAgent();
    }
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  trackMessage(index: number, message: AgentMessage): string {
    return `${message.timestamp}-${message.agent}`;
  }

  trackForecast(index: number, forecast: SpatialForecast): string {
    return `${forecast.timestamp}-${forecast.location.lat}-${forecast.location.lng}`;
  }

  private scrollToLatestMessage() {
    setTimeout(() => {
      if (this.messagesContainer) {
        const element = this.messagesContainer.nativeElement;
        element.scrollTop = element.scrollHeight;
      }
    }, 100);
  }

  private initializeMap(config: MapConfiguration) {
    console.log('🗺️ Initializing map with configuration:', config);
    
    // Initialize Google Maps with the agent-generated configuration
    if (typeof google !== 'undefined' && google.maps && this.mapContainer) {
      const mapElement = this.mapContainer.nativeElement.querySelector('#agent-map');
      if (mapElement) {
        const map = new google.maps.Map(mapElement, {
          ...config.mapOptions,
          // Ensure map interaction is enabled
          disableDefaultUI: false,
          zoomControl: true,
          gestureHandling: 'greedy', // Allow all gestures
          scrollwheel: true, // Explicitly enable scroll wheel zoom
          clickableIcons: true
        });
        
        // Add overlays from the configuration
        config.overlays.forEach(overlay => {
          if (overlay.visible) {
            this.addMapOverlay(map, overlay);
          }
        });
        
        console.log(`✅ Map initialized with ${config.overlays.length} overlays`);
      }
    }
  }

  private addMapOverlay(map: google.maps.Map, overlay: any) {
    // Add overlay to map based on type
    console.log(`📍 Adding ${overlay.type} overlay: ${overlay.id}`);
    
    // Implementation would add actual overlay data to the map
    // This is a placeholder for the overlay rendering logic
  }

  private updateHeatMap() {
    if (!this.heatmapCanvas || this.spatialForecasts.length === 0) return;

    const canvas = this.heatmapCanvas.nativeElement;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Create heat map from spatial forecasts
    this.spatialForecasts.slice(-20).forEach(forecast => {
      const x = ((forecast.location.lng + 123.25) / 0.5) * canvas.width; 
      const y = ((48.70 - forecast.location.lat) / 0.3) * canvas.height;
      const radius = forecast.probability * 100; // Scale by probability

      const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
      
      if (forecast.probability > 0.7) {
        // High probability - red/orange
        gradient.addColorStop(0, 'rgba(255, 87, 34, 0.8)');
        gradient.addColorStop(1, 'rgba(255, 87, 34, 0)');
      } else if (forecast.probability > 0.5) {
        // Medium probability - yellow
        gradient.addColorStop(0, 'rgba(255, 193, 7, 0.6)');
        gradient.addColorStop(1, 'rgba(255, 193, 7, 0)');
      } else {
        // Lower probability - blue/green
        gradient.addColorStop(0, 'rgba(76, 175, 80, 0.5)');
        gradient.addColorStop(1, 'rgba(76, 175, 80, 0)');
      }

      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, 2 * Math.PI);
      ctx.fill();
    });

    console.log(`🔥 Updated heat map with ${this.spatialForecasts.length} forecasts`);
  }

  private generateDemoForecasts() {
    // Generate demo spatial forecasts
    const demoForecasts: SpatialForecast[] = [
      {
        location: { lat: 48.5465, lng: -123.0307 },
        behavior: 'feeding',
        probability: 0.92,
        confidence: 0.87,
        model: 'pinn',
        timestamp: new Date()
      },
      {
        location: { lat: 48.5200, lng: -123.1500 },
        behavior: 'socializing',
        probability: 0.78,
        confidence: 0.84,
        model: 'behavioral',
        timestamp: new Date()
      },
      {
        location: { lat: 48.6100, lng: -122.9800 },
        behavior: 'traveling',
        probability: 0.65,
        confidence: 0.79,
        model: 'ensemble',
        timestamp: new Date()
      }
    ];

    this.spatialForecasts = demoForecasts;
    this.updateHeatMap();
  }
} 