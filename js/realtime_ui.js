/**
 * Real-time UI Integration with Redis Pub/Sub
 * 
 * Provides live updates for:
 * - New sightings
 * - Prediction updates
 * - Environmental condition changes
 * - High-confidence alerts
 * - User analytics
 */

class OrCastRealTimeUI {
    constructor() {
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        // UI elements
        this.sightingFeed = null;
        this.predictionPanel = null;
        this.environmentalPanel = null;
        this.alertsPanel = null;
        this.userDashboard = null;
        
        // Cache for UI updates
        this.uiCache = new Map();
        
        // Initialize UI components
        this.initializeUIComponents();
        
        // Start real-time connection
        this.startRealTimeConnection();
    }
    
    initializeUIComponents() {
        // Create main real-time dashboard
        this.createRealTimeDashboard();
        
        // Initialize individual panels
        this.initializeSightingFeed();
        this.initializePredictionPanel();
        this.initializeEnvironmentalPanel();
        this.initializeAlertsPanel();
        this.initializeUserDashboard();
    }
    
    createRealTimeDashboard() {
        const dashboard = document.createElement('div');
        dashboard.id = 'realtime-dashboard';
        dashboard.className = 'realtime-dashboard';
        dashboard.innerHTML = `
            <div class="dashboard-header">
                <h3>Live OrCast Updates</h3>
                <div class="connection-status" id="connection-status">
                    <span class="status-indicator"></span>
                    <span class="status-text">Connecting...</span>
                </div>
            </div>
            
            <div class="dashboard-content">
                <div class="dashboard-left">
                    <div class="panel" id="sighting-feed-panel">
                        <h4>Live Sightings</h4>
                        <div id="sighting-feed" class="feed-container"></div>
                    </div>
                    
                    <div class="panel" id="alerts-panel">
                        <h4>Alerts</h4>
                        <div id="alerts-feed" class="feed-container"></div>
                    </div>
                </div>
                
                <div class="dashboard-right">
                    <div class="panel" id="prediction-panel">
                        <h4>Live Predictions</h4>
                        <div id="prediction-feed" class="feed-container"></div>
                    </div>
                    
                    <div class="panel" id="environmental-panel">
                        <h4>Environmental Conditions</h4>
                        <div id="environmental-feed" class="feed-container"></div>
                    </div>
                </div>
            </div>
            
            <div class="dashboard-footer">
                <div class="stats" id="realtime-stats">
                    <span>Sightings: <span id="sighting-count">0</span></span>
                    <span>Predictions: <span id="prediction-count">0</span></span>
                    <span>Alerts: <span id="alert-count">0</span></span>
                </div>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(dashboard);
        
        // Store references
        this.sightingFeed = document.getElementById('sighting-feed');
        this.predictionPanel = document.getElementById('prediction-feed');
        this.environmentalPanel = document.getElementById('environmental-feed');
        this.alertsPanel = document.getElementById('alerts-feed');
    }
    
    initializeSightingFeed() {
        this.sightingFeed.innerHTML = `
            <div class="feed-placeholder">
                <div class="placeholder-icon">SIGHT</div>
                <div class="placeholder-text">Waiting for live sightings...</div>
            </div>
        `;
    }
    
    initializePredictionPanel() {
        this.predictionPanel.innerHTML = `
            <div class="feed-placeholder">
                <div class="placeholder-icon">PRED</div>
                <div class="placeholder-text">Waiting for predictions...</div>
            </div>
        `;
    }
    
    initializeEnvironmentalPanel() {
        this.environmentalPanel.innerHTML = `
            <div class="feed-placeholder">
                <div class="placeholder-icon">ENV</div>
                <div class="placeholder-text">Waiting for environmental data...</div>
            </div>
        `;
    }
    
    initializeAlertsPanel() {
        this.alertsPanel.innerHTML = `
            <div class="feed-placeholder">
                <div class="placeholder-icon">ALERT</div>
                <div class="placeholder-text">No alerts</div>
            </div>
        `;
    }
    
    initializeUserDashboard() {
        // This would initialize user-specific dashboard
        // Connected to Redis user session data
    }
    
    startRealTimeConnection() {
        try {
            // Connect to Server-Sent Events endpoint
            this.eventSource = new EventSource('/api/realtime/events');
            
            // Handle connection events
            this.eventSource.onopen = () => {
                this.onConnectionOpen();
            };
            
            this.eventSource.onerror = (error) => {
                this.onConnectionError(error);
            };
            
            // Handle different message types
            this.eventSource.addEventListener('sighting', (event) => {
                this.handleSightingUpdate(JSON.parse(event.data));
            });
            
            this.eventSource.addEventListener('prediction', (event) => {
                this.handlePredictionUpdate(JSON.parse(event.data));
            });
            
            this.eventSource.addEventListener('environmental', (event) => {
                this.handleEnvironmentalUpdate(JSON.parse(event.data));
            });
            
            this.eventSource.addEventListener('alert', (event) => {
                this.handleAlertUpdate(JSON.parse(event.data));
            });
            
            this.eventSource.addEventListener('analytics', (event) => {
                this.handleAnalyticsUpdate(JSON.parse(event.data));
            });
            
        } catch (error) {
            console.error('Failed to start real-time connection:', error);
            this.scheduleReconnect();
        }
    }
    
    onConnectionOpen() {
        console.log('Real-time connection established');
        this.reconnectAttempts = 0;
        this.updateConnectionStatus('connected', 'Connected');
    }
    
    onConnectionError(error) {
        console.error('Real-time connection error:', error);
        this.updateConnectionStatus('error', 'Connection Error');
        this.scheduleReconnect();
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.updateConnectionStatus('reconnecting', `Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.startRealTimeConnection();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            this.updateConnectionStatus('failed', 'Connection Failed');
        }
    }
    
    updateConnectionStatus(status, text) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = `connection-status ${status}`;
            statusElement.querySelector('.status-text').textContent = text;
        }
    }
    
    handleSightingUpdate(data) {
        console.log('New sighting update:', data);
        
        // Clear placeholder
        this.clearPlaceholder(this.sightingFeed);
        
        // Create sighting item
        const sightingItem = this.createSightingItem(data);
        
        // Add to feed (prepend to show newest first)
        this.sightingFeed.insertBefore(sightingItem, this.sightingFeed.firstChild);
        
        // Limit feed to 10 items
        this.limitFeedItems(this.sightingFeed, 10);
        
        // Update statistics
        this.updateStatistic('sighting-count', 1);
        
        // Show notification
        this.showNotification('New Sighting', `${data.data.behavior} behavior observed at ${data.data.location}`);
    }
    
    handlePredictionUpdate(data) {
        console.log('Prediction update:', data);
        
        // Clear placeholder
        this.clearPlaceholder(this.predictionPanel);
        
        // Create prediction item
        const predictionItem = this.createPredictionItem(data);
        
        // Add to feed
        this.predictionPanel.insertBefore(predictionItem, this.predictionPanel.firstChild);
        
        // Limit feed items
        this.limitFeedItems(this.predictionPanel, 8);
        
        // Update statistics
        this.updateStatistic('prediction-count', 1);
        
        // Update map if available
        if (window.updatePredictionOnMap) {
            window.updatePredictionOnMap(data.location, data.prediction);
        }
    }
    
    handleEnvironmentalUpdate(data) {
        console.log('Environmental update:', data);
        
        // Clear placeholder
        this.clearPlaceholder(this.environmentalPanel);
        
        // Create environmental item
        const envItem = this.createEnvironmentalItem(data);
        
        // Add to feed
        this.environmentalPanel.insertBefore(envItem, this.environmentalPanel.firstChild);
        
        // Limit feed items
        this.limitFeedItems(this.environmentalPanel, 5);
        
        // Update environmental display
        this.updateEnvironmentalDisplay(data);
    }
    
    handleAlertUpdate(data) {
        console.log('Alert update:', data);
        
        // Clear placeholder
        this.clearPlaceholder(this.alertsPanel);
        
        // Create alert item
        const alertItem = this.createAlertItem(data);
        
        // Add to feed
        this.alertsPanel.insertBefore(alertItem, this.alertsPanel.firstChild);
        
        // Limit feed items
        this.limitFeedItems(this.alertsPanel, 5);
        
        // Update statistics
        this.updateStatistic('alert-count', 1);
        
        // Show prominent notification for high-confidence alerts
        if (data.confidence && data.confidence > 0.8) {
            this.showHighPriorityNotification(data.message, data.location);
        }
    }
    
    handleAnalyticsUpdate(data) {
        console.log('Analytics update:', data);
        
        // Update user dashboard if visible
        if (this.userDashboard) {
            this.updateUserAnalytics(data);
        }
    }
    
    createSightingItem(data) {
        const item = document.createElement('div');
        item.className = 'feed-item sighting-item';
        
        const sightingData = data.data;
        const timestamp = new Date(data.timestamp).toLocaleTimeString();
        
        item.innerHTML = `
            <div class="item-header">
                <span class="item-type">SIGHT</span>
                <span class="item-time">${timestamp}</span>
            </div>
            <div class="item-content">
                <div class="sighting-info">
                    <div class="behavior-tag ${sightingData.behavior}">${sightingData.behavior.toUpperCase()}</div>
                    <div class="location-info">${sightingData.location || 'Unknown Location'}</div>
                </div>
                <div class="sighting-details">
                    <span>Pod Size: ${sightingData.pod_size || 'Unknown'}</span>
                    <span>Confidence: ${Math.round((sightingData.confidence || 0) * 100)}%</span>
                </div>
            </div>
        `;
        
        return item;
    }
    
    createPredictionItem(data) {
        const item = document.createElement('div');
        item.className = 'feed-item prediction-item';
        
        const prediction = data.prediction;
        const timestamp = new Date(data.timestamp).toLocaleTimeString();
        
        item.innerHTML = `
            <div class="item-header">
                <span class="item-type">PRED</span>
                <span class="item-time">${timestamp}</span>
            </div>
            <div class="item-content">
                <div class="prediction-info">
                    <div class="location-info">${data.location}</div>
                    <div class="prediction-details">
                        <span class="behavior-prediction">${prediction.behavior}</span>
                        <span class="confidence-score">${Math.round((prediction.confidence || 0) * 100)}%</span>
                    </div>
                </div>
                ${prediction.hmc_uncertainty ? `
                    <div class="uncertainty-info">
                        <span>Uncertainty: ±${Math.round(prediction.hmc_uncertainty.uncertainty_std * 100)}%</span>
                    </div>
                ` : ''}
            </div>
        `;
        
        return item;
    }
    
    createEnvironmentalItem(data) {
        const item = document.createElement('div');
        item.className = 'feed-item environmental-item';
        
        const envData = data.data;
        const timestamp = new Date(data.timestamp).toLocaleTimeString();
        
        item.innerHTML = `
            <div class="item-header">
                <span class="item-type">ENV</span>
                <span class="item-time">${timestamp}</span>
            </div>
            <div class="item-content">
                <div class="location-info">${data.location}</div>
                <div class="environmental-grid">
                    ${envData.tidal_flow ? `<div class="env-stat">
                        <span class="env-label">Tidal Flow</span>
                        <span class="env-value">${envData.tidal_flow}</span>
                    </div>` : ''}
                    ${envData.temperature ? `<div class="env-stat">
                        <span class="env-label">Temperature</span>
                        <span class="env-value">${envData.temperature}°C</span>
                    </div>` : ''}
                    ${envData.weather_conditions ? `<div class="env-stat">
                        <span class="env-label">Weather</span>
                        <span class="env-value">${envData.weather_conditions}</span>
                    </div>` : ''}
                </div>
            </div>
        `;
        
        return item;
    }
    
    createAlertItem(data) {
        const item = document.createElement('div');
        item.className = `feed-item alert-item alert-${data.type}`;
        
        const timestamp = new Date(data.timestamp).toLocaleTimeString();
        
        item.innerHTML = `
            <div class="item-header">
                <span class="item-type alert-type">ALERT</span>
                <span class="item-time">${timestamp}</span>
            </div>
            <div class="item-content">
                <div class="alert-message">${data.message}</div>
                ${data.location ? `<div class="alert-location">${data.location}</div>` : ''}
                ${data.confidence ? `<div class="alert-confidence">Confidence: ${Math.round(data.confidence * 100)}%</div>` : ''}
            </div>
        `;
        
        return item;
    }
    
    clearPlaceholder(container) {
        const placeholder = container.querySelector('.feed-placeholder');
        if (placeholder) {
            placeholder.remove();
        }
    }
    
    limitFeedItems(container, maxItems) {
        const items = container.querySelectorAll('.feed-item');
        if (items.length > maxItems) {
            for (let i = maxItems; i < items.length; i++) {
                items[i].remove();
            }
        }
    }
    
    updateStatistic(statId, increment) {
        const statElement = document.getElementById(statId);
        if (statElement) {
            const currentValue = parseInt(statElement.textContent) || 0;
            statElement.textContent = currentValue + increment;
        }
    }
    
    showNotification(title, message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'realtime-notification';
        notification.innerHTML = `
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    showHighPriorityNotification(message, location) {
        // Create high-priority notification
        const notification = document.createElement('div');
        notification.className = 'realtime-notification high-priority';
        notification.innerHTML = `
            <div class="notification-title">High Confidence Alert</div>
            <div class="notification-message">${message}</div>
            <div class="notification-location">${location || ''}</div>
            <button class="notification-close">×</button>
        `;
        
        // Add close functionality
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            notification.remove();
        }, 10000);
    }
    
    updateEnvironmentalDisplay(data) {
        // Update environmental conditions on map or other displays
        if (window.updateEnvironmentalDisplay) {
            window.updateEnvironmentalDisplay(data.location, data.data);
        }
    }
    
    updateUserAnalytics(data) {
        // Update user dashboard with analytics
        if (this.userDashboard) {
            // This would update charts, statistics, etc.
            console.log('Updating user analytics:', data);
        }
    }
    
    // === CACHE MANAGEMENT ===
    
    getCachedPrediction(location) {
        return this.uiCache.get(`prediction:${location}`);
    }
    
    setCachedPrediction(location, prediction) {
        this.uiCache.set(`prediction:${location}`, prediction);
        
        // Clear cache after 30 minutes
        setTimeout(() => {
            this.uiCache.delete(`prediction:${location}`);
        }, 30 * 60 * 1000);
    }
    
    // === USER INTERACTION ===
    
    subscribeToLocation(location) {
        // Subscribe to updates for specific location
        fetch('/api/realtime/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ location: location })
        });
    }
    
    unsubscribeFromLocation(location) {
        // Unsubscribe from location updates
        fetch('/api/realtime/unsubscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ location: location })
        });
    }
    
    // === CLEANUP ===
    
    destroy() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        // Clear UI cache
        this.uiCache.clear();
        
        // Remove dashboard
        const dashboard = document.getElementById('realtime-dashboard');
        if (dashboard) {
            dashboard.remove();
        }
    }
}

// === INTEGRATION WITH EXISTING SYSTEMS ===

class RealTimeIntegration {
    constructor() {
        this.realTimeUI = null;
        this.transparencyEngine = null;
        this.feedingZoneUI = null;
        this.behavioralML = null;
    }
    
    initialize() {
        // Initialize real-time UI
        this.realTimeUI = new OrCastRealTimeUI();
        
        // Connect to existing systems
        this.connectToTransparencyEngine();
        this.connectToFeedingZoneUI();
        this.connectToBehavioralML();
    }
    
    connectToTransparencyEngine() {
        // Connect real-time updates to transparency system
        if (window.transparencyEngine) {
            this.transparencyEngine = window.transparencyEngine;
            
            // Update transparency when new predictions arrive
            this.realTimeUI.eventSource.addEventListener('prediction', (event) => {
                const data = JSON.parse(event.data);
                if (this.transparencyEngine) {
                    this.transparencyEngine.updateWithRealTimeData(data);
                }
            });
        }
    }
    
    connectToFeedingZoneUI() {
        // Connect real-time updates to feeding zone system
        if (window.feedingZoneUI) {
            this.feedingZoneUI = window.feedingZoneUI;
            
            // Update feeding zones when environmental data changes
            this.realTimeUI.eventSource.addEventListener('environmental', (event) => {
                const data = JSON.parse(event.data);
                if (this.feedingZoneUI) {
                    this.feedingZoneUI.updateEnvironmentalConditions(data);
                }
            });
        }
    }
    
    connectToBehavioralML() {
        // Connect real-time updates to behavioral ML system
        if (window.behavioralML) {
            this.behavioralML = window.behavioralML;
            
            // Update ML insights when new sightings arrive
            this.realTimeUI.eventSource.addEventListener('sighting', (event) => {
                const data = JSON.parse(event.data);
                if (this.behavioralML) {
                    this.behavioralML.processSightingUpdate(data);
                }
            });
        }
    }
}

// === GLOBAL INITIALIZATION ===

let realTimeIntegration = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    realTimeIntegration = new RealTimeIntegration();
    realTimeIntegration.initialize();
});

// Make globally available
window.OrCastRealTimeUI = OrCastRealTimeUI;
window.RealTimeIntegration = RealTimeIntegration;
window.realTimeIntegration = realTimeIntegration;

// === STYLES ===

const realTimeStyles = `
<style>
.realtime-dashboard {
    position: fixed;
    top: 80px;
    right: 20px;
    width: 400px;
    max-height: 70vh;
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    overflow: hidden;
    z-index: 1000;
}

.dashboard-header {
    background: #2c3e50;
    color: white;
    padding: 12px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.dashboard-header h3 {
    margin: 0;
    font-size: 14px;
}

.connection-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
}

.status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #95a5a6;
}

.connection-status.connected .status-indicator {
    background: #27ae60;
}

.connection-status.error .status-indicator {
    background: #e74c3c;
}

.connection-status.reconnecting .status-indicator {
    background: #f39c12;
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.dashboard-content {
    max-height: 400px;
    overflow-y: auto;
}

.panel {
    border-bottom: 1px solid #ecf0f1;
    padding: 12px;
}

.panel h4 {
    margin: 0 0 8px 0;
    font-size: 12px;
    color: #7f8c8d;
    text-transform: uppercase;
}

.feed-container {
    max-height: 120px;
    overflow-y: auto;
}

.feed-placeholder {
    text-align: center;
    padding: 20px;
    color: #bdc3c7;
}

.placeholder-icon {
    font-size: 12px;
    font-weight: bold;
    margin-bottom: 4px;
}

.feed-item {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 4px;
    padding: 8px;
    margin-bottom: 6px;
    font-size: 12px;
}

.item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
}

.item-type {
    background: #3498db;
    color: white;
    padding: 2px 6px;
    border-radius: 2px;
    font-size: 10px;
    font-weight: bold;
}

.alert-type {
    background: #e74c3c;
}

.item-time {
    font-size: 10px;
    color: #7f8c8d;
}

.behavior-tag {
    background: #27ae60;
    color: white;
    padding: 2px 6px;
    border-radius: 2px;
    font-size: 10px;
    margin-right: 6px;
}

.behavior-tag.feeding {
    background: #27ae60;
}

.behavior-tag.traveling {
    background: #3498db;
}

.behavior-tag.socializing {
    background: #9b59b6;
}

.behavior-tag.resting {
    background: #95a5a6;
}

.location-info {
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 4px;
}

.sighting-details {
    display: flex;
    gap: 12px;
    font-size: 10px;
    color: #7f8c8d;
}

.environmental-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
}

.env-stat {
    display: flex;
    flex-direction: column;
}

.env-label {
    font-size: 10px;
    color: #7f8c8d;
}

.env-value {
    font-weight: bold;
    color: #2c3e50;
}

.dashboard-footer {
    background: #ecf0f1;
    padding: 8px 16px;
    border-top: 1px solid #bdc3c7;
}

.stats {
    display: flex;
    gap: 16px;
    font-size: 11px;
    color: #7f8c8d;
}

.realtime-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    max-width: 300px;
    z-index: 2000;
}

.realtime-notification.high-priority {
    background: #e74c3c;
    color: white;
    border-color: #c0392b;
}

.notification-title {
    font-weight: bold;
    margin-bottom: 4px;
}

.notification-close {
    position: absolute;
    top: 4px;
    right: 8px;
    background: none;
    border: none;
    font-size: 16px;
    cursor: pointer;
    color: inherit;
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', realTimeStyles);

export { OrCastRealTimeUI, RealTimeIntegration }; 