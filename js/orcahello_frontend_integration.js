/**
 * ORCAST-OrcaHello Frontend Integration
 * Real-time whale detection visualization and route optimization
 */

class ORCASTOrcaHelloFrontend {
    constructor(mapInstance, firebaseDb) {
        this.map = mapInstance;
        this.db = firebaseDb;
        
        // Data layers
        this.hydrophoneMarkers = new Map();
        this.detectionMarkers = new Map();
        this.hotspotOverlays = new Map();
        this.routePolylines = new Map();
        this.predictionCircles = new Map();
        
        // UI components
        this.statusPanel = null;
        this.controlPanel = null;
        this.activeDetections = [];
        this.behavioralInsights = null;
        this.routeRecommendations = null;
        
        // Configuration
        this.updateInterval = 30000; // 30 seconds
        this.maxDetectionAge = 6 * 60 * 60 * 1000; // 6 hours
        this.autoUpdate = true;
        
        this.initialize();
    }
    
    async initialize() {
        console.log('🐋 Initializing ORCAST-OrcaHello Frontend Integration...');
        
        // Create UI components
        this.createControlPanel();
        this.createStatusPanel();
        
        // Load hydrophone locations
        await this.loadHydrophoneLocations();
        
        // Start real-time data updates
        this.startRealTimeUpdates();
        
        // Setup Firebase listeners
        this.setupFirebaseListeners();
        
        console.log('✅ OrcaHello integration initialized successfully');
    }
    
    createControlPanel() {
        // Create OrcaHello control panel
        const controlHtml = `
            <div id="orcahello-controls" class="control-panel">
                <div class="panel-header">
                    <h3>🎵 OrcaHello Live Data</h3>
                    <button id="orcahello-toggle" class="toggle-btn active">ON</button>
                </div>
                
                <div class="data-layers">
                    <label class="layer-control">
                        <input type="checkbox" id="show-hydrophones" checked>
                        <span>🎙️ Hydrophone Locations</span>
                    </label>
                    
                    <label class="layer-control">
                        <input type="checkbox" id="show-detections" checked>
                        <span>🐋 Live Detections</span>
                    </label>
                    
                    <label class="layer-control">
                        <input type="checkbox" id="show-hotspots" checked>
                        <span>🔥 Activity Hotspots</span>
                    </label>
                    
                    <label class="layer-control">
                        <input type="checkbox" id="show-routes" checked>
                        <span>🗺️ Recommended Routes</span>
                    </label>
                    
                    <label class="layer-control">
                        <input type="checkbox" id="show-predictions" checked>
                        <span>🔮 Location Predictions</span>
                    </label>
                </div>
                
                <div class="time-controls">
                    <label>Detection Age Filter:</label>
                    <select id="detection-age-filter">
                        <option value="1">Last 1 hour</option>
                        <option value="3">Last 3 hours</option>
                        <option value="6" selected>Last 6 hours</option>
                        <option value="12">Last 12 hours</option>
                        <option value="24">Last 24 hours</option>
                    </select>
                </div>
                
                <div class="confidence-filter">
                    <label>Min Confidence: <span id="confidence-value">30%</span></label>
                    <input type="range" id="confidence-slider" min="0" max="100" value="30">
                </div>
            </div>
        `;
        
        // Add to sidebar
        const sidebar = document.querySelector('.controls-sidebar') || document.body;
        const controlDiv = document.createElement('div');
        controlDiv.innerHTML = controlHtml;
        sidebar.appendChild(controlDiv);
        
        // Bind event listeners
        this.bindControlEvents();
    }
    
    createStatusPanel() {
        const statusHtml = `
            <div id="orcahello-status" class="status-panel">
                <div class="status-header">
                    <h4>🎵 OrcaHello Status</h4>
                    <div id="connection-indicator" class="indicator connecting">●</div>
                </div>
                
                <div class="status-metrics">
                    <div class="metric">
                        <span class="label">Active Hydrophones:</span>
                        <span id="active-hydrophones">-</span>
                    </div>
                    
                    <div class="metric">
                        <span class="label">Recent Detections:</span>
                        <span id="recent-detections">-</span>
                    </div>
                    
                    <div class="metric">
                        <span class="label">Activity Hotspots:</span>
                        <span id="activity-hotspots">-</span>
                    </div>
                    
                    <div class="metric">
                        <span class="label">Route Recommendations:</span>
                        <span id="route-recommendations">-</span>
                    </div>
                    
                    <div class="metric">
                        <span class="label">System Confidence:</span>
                        <span id="system-confidence">-</span>
                    </div>
                </div>
                
                <div class="recent-activity">
                    <h5>Recent Activity</h5>
                    <div id="activity-feed" class="activity-list">
                        <div class="activity-item">Initializing...</div>
                    </div>
                </div>
            </div>
        `;
        
        // Add to map interface
        const statusDiv = document.createElement('div');
        statusDiv.innerHTML = statusHtml;
        statusDiv.style.cssText = `
            position: absolute;
            top: 10px;
            right: 10px;
            width: 300px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
        `;
        
        document.body.appendChild(statusDiv);
    }
    
    bindControlEvents() {
        // Toggle OrcaHello integration
        document.getElementById('orcahello-toggle').addEventListener('click', (e) => {
            this.autoUpdate = !this.autoUpdate;
            e.target.textContent = this.autoUpdate ? 'ON' : 'OFF';
            e.target.className = this.autoUpdate ? 'toggle-btn active' : 'toggle-btn';
            
            if (this.autoUpdate) {
                this.startRealTimeUpdates();
            }
        });
        
        // Layer toggles
        document.getElementById('show-hydrophones').addEventListener('change', (e) => {
            this.toggleHydrophones(e.target.checked);
        });
        
        document.getElementById('show-detections').addEventListener('change', (e) => {
            this.toggleDetections(e.target.checked);
        });
        
        document.getElementById('show-hotspots').addEventListener('change', (e) => {
            this.toggleHotspots(e.target.checked);
        });
        
        document.getElementById('show-routes').addEventListener('change', (e) => {
            this.toggleRoutes(e.target.checked);
        });
        
        document.getElementById('show-predictions').addEventListener('change', (e) => {
            this.togglePredictions(e.target.checked);
        });
        
        // Time filter
        document.getElementById('detection-age-filter').addEventListener('change', (e) => {
            this.maxDetectionAge = parseInt(e.target.value) * 60 * 60 * 1000;
            this.updateDetectionDisplay();
        });
        
        // Confidence filter
        const confidenceSlider = document.getElementById('confidence-slider');
        confidenceSlider.addEventListener('input', (e) => {
            const value = e.target.value;
            document.getElementById('confidence-value').textContent = value + '%';
            this.updateDetectionDisplay();
        });
    }
    
    async loadHydrophoneLocations() {
        // Hardcoded hydrophone locations from OrcaHello
        const hydrophones = [
            { id: 'rpi_bush_point', name: 'Bush Point', lat: 48.0336664, lng: -122.6040035 },
            { id: 'rpi_mast_center', name: 'Mast Center', lat: 47.34922, lng: -122.32512 },
            { id: 'rpi_north_sjc', name: 'North San Juan Channel', lat: 48.591294, lng: -123.058779 },
            { id: 'rpi_orcasound_lab', name: 'Orcasound Lab', lat: 48.5583362, lng: -123.1735774 },
            { id: 'rpi_point_robinson', name: 'Point Robinson', lat: 47.388383, lng: -122.37267 },
            { id: 'rpi_port_townsend', name: 'Port Townsend', lat: 48.135743, lng: -122.760614 },
            { id: 'rpi_sunset_bay', name: 'Sunset Bay', lat: 47.86497296593844, lng: -122.33393605795372 }
        ];
        
        hydrophones.forEach(hydrophone => {
            const marker = new google.maps.Marker({
                position: { lat: hydrophone.lat, lng: hydrophone.lng },
                map: this.map,
                title: hydrophone.name,
                icon: {
                    url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="12" cy="12" r="10" fill="#2196F3" stroke="#1976D2" stroke-width="2"/>
                            <path d="M8 12L16 12M12 8L12 16" stroke="white" stroke-width="2"/>
                        </svg>
                    `),
                    scaledSize: new google.maps.Size(24, 24)
                }
            });
            
            // Info window
            const infoWindow = new google.maps.InfoWindow({
                content: `
                    <div class="hydrophone-info">
                        <h4>🎙️ ${hydrophone.name}</h4>
                        <p><strong>Location ID:</strong> ${hydrophone.id}</p>
                        <p><strong>Coordinates:</strong> ${hydrophone.lat.toFixed(4)}, ${hydrophone.lng.toFixed(4)}</p>
                        <p><strong>Status:</strong> <span class="status-active">Active</span></p>
                        <div id="hydrophone-detections-${hydrophone.id}" class="hydrophone-detections">
                            <p>Loading recent detections...</p>
                        </div>
                    </div>
                `
            });
            
            marker.addListener('click', () => {
                infoWindow.open(this.map, marker);
                this.loadHydrophoneDetections(hydrophone.id);
            });
            
            this.hydrophoneMarkers.set(hydrophone.id, marker);
        });
        
        this.updateStatus('active-hydrophones', hydrophones.length);
    }
    
    async loadHydrophoneDetections(hydrophoneId) {
        try {
            // This would call the OrcaHello API in production
            // For now, show placeholder info
            const detectionsHtml = `
                <p><strong>Recent 6h Activity:</strong></p>
                <ul>
                    <li>🐋 3 whale call detections</li>
                    <li>🔊 Avg confidence: 72%</li>
                    <li>⏰ Last detection: 15 min ago</li>
                </ul>
                <button onclick="this.focusHydrophone('${hydrophoneId}')" class="btn-small">
                    Focus on Activity
                </button>
            `;
            
            const container = document.getElementById(`hydrophone-detections-${hydrophoneId}`);
            if (container) {
                container.innerHTML = detectionsHtml;
            }
        } catch (error) {
            console.error('Error loading hydrophone detections:', error);
        }
    }
    
    startRealTimeUpdates() {
        if (!this.autoUpdate) return;
        
        // Update connection indicator
        this.updateConnectionStatus('active');
        
        // Fetch initial data
        this.updateAllData();
        
        // Set up periodic updates
        this.updateInterval = setInterval(() => {
            if (this.autoUpdate) {
                this.updateAllData();
            }
        }, 30000); // Every 30 seconds
    }
    
    async updateAllData() {
        try {
            console.log('🔄 Updating OrcaHello data...');
            
            // Update detection data
            await this.updateDetections();
            
            // Update behavioral insights
            await this.updateBehavioralInsights();
            
            // Update route recommendations
            await this.updateRouteRecommendations();
            
            // Update predictions
            await this.updatePredictions();
            
            this.updateConnectionStatus('active');
            this.addActivityFeedItem('✅ Data updated successfully');
            
        } catch (error) {
            console.error('Error updating OrcaHello data:', error);
            this.updateConnectionStatus('error');
            this.addActivityFeedItem('❌ Update failed: ' + error.message);
        }
    }
    
    async updateDetections() {
        // In production, this would fetch from Firebase/API
        // For now, simulate some recent detections
        const mockDetections = [
            {
                id: 'det_001',
                timestamp: new Date(Date.now() - 10 * 60 * 1000), // 10 min ago
                location: { lat: 48.5583362, lng: -123.1735774 },
                locationName: 'Orcasound Lab',
                confidence: 85,
                predictions: [{ duration: 2.5, confidence: 0.85 }]
            },
            {
                id: 'det_002',
                timestamp: new Date(Date.now() - 25 * 60 * 1000), // 25 min ago
                location: { lat: 48.591294, lng: -123.058779 },
                locationName: 'North San Juan Channel',
                confidence: 72,
                predictions: [{ duration: 3.2, confidence: 0.72 }]
            },
            {
                id: 'det_003',
                timestamp: new Date(Date.now() - 45 * 60 * 1000), // 45 min ago
                location: { lat: 48.0336664, lng: -122.6040035 },
                locationName: 'Bush Point',
                confidence: 91,
                predictions: [{ duration: 1.8, confidence: 0.91 }]
            }
        ];
        
        this.activeDetections = mockDetections;
        this.updateDetectionDisplay();
        this.updateStatus('recent-detections', mockDetections.length);
    }
    
    updateDetectionDisplay() {
        // Clear existing detection markers
        this.detectionMarkers.forEach(marker => marker.setMap(null));
        this.detectionMarkers.clear();
        
        const minConfidence = parseInt(document.getElementById('confidence-slider').value);
        const maxAge = this.maxDetectionAge;
        const now = Date.now();
        
        this.activeDetections.forEach(detection => {
            // Apply filters
            if (detection.confidence < minConfidence) return;
            if (now - detection.timestamp.getTime() > maxAge) return;
            
            // Create detection marker
            const marker = new google.maps.Marker({
                position: detection.location,
                map: this.map,
                title: `Whale Detection - ${detection.locationName}`,
                icon: {
                    url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="16" cy="16" r="14" fill="#4CAF50" stroke="#2E7D32" stroke-width="2"/>
                            <text x="16" y="20" text-anchor="middle" fill="white" font-size="16">🐋</text>
                        </svg>
                    `),
                    scaledSize: new google.maps.Size(32, 32)
                }
            });
            
            // Detection info window
            const ageMinutes = Math.floor((now - detection.timestamp.getTime()) / (1000 * 60));
            const infoWindow = new google.maps.InfoWindow({
                content: `
                    <div class="detection-info">
                        <h4>🐋 Whale Detection</h4>
                        <p><strong>Location:</strong> ${detection.locationName}</p>
                        <p><strong>Confidence:</strong> ${detection.confidence}%</p>
                        <p><strong>Time:</strong> ${ageMinutes} minutes ago</p>
                        <p><strong>Detection ID:</strong> ${detection.id}</p>
                        <div class="detection-actions">
                            <button onclick="this.focusDetection('${detection.id}')" class="btn-small">
                                View Details
                            </button>
                            <button onclick="this.planRouteToDetection('${detection.id}')" class="btn-small">
                                Plan Route
                            </button>
                        </div>
                    </div>
                `
            });
            
            marker.addListener('click', () => {
                infoWindow.open(this.map, marker);
            });
            
            this.detectionMarkers.set(detection.id, marker);
        });
    }
    
    async updateBehavioralInsights() {
        // Mock behavioral insights
        const mockInsights = {
            hotspots: [
                {
                    location: 'Orcasound Lab',
                    coordinates: [48.5583362, -123.1735774],
                    activity_score: 8.5,
                    whale_watching_suitability: 0.85,
                    behavioral_features: {
                        foraging_probability: 0.7,
                        social_activity_score: 0.6
                    }
                },
                {
                    location: 'North San Juan Channel',
                    coordinates: [48.591294, -123.058779],
                    activity_score: 6.2,
                    whale_watching_suitability: 0.62,
                    behavioral_features: {
                        foraging_probability: 0.4,
                        social_activity_score: 0.8
                    }
                }
            ]
        };
        
        this.behavioralInsights = mockInsights;
        this.updateHotspotDisplay();
        this.updateStatus('activity-hotspots', mockInsights.hotspots.length);
    }
    
    updateHotspotDisplay() {
        // Clear existing hotspot overlays
        this.hotspotOverlays.forEach(overlay => overlay.setMap(null));
        this.hotspotOverlays.clear();
        
        if (!this.behavioralInsights) return;
        
        this.behavioralInsights.hotspots.forEach((hotspot, index) => {
            const [lat, lng] = hotspot.coordinates;
            
            // Create hotspot circle
            const circle = new google.maps.Circle({
                strokeColor: '#FF5722',
                strokeOpacity: 0.8,
                strokeWeight: 2,
                fillColor: '#FF5722',
                fillOpacity: 0.15,
                map: this.map,
                center: { lat, lng },
                radius: hotspot.activity_score * 500 // Radius based on activity score
            });
            
            // Hotspot marker
            const marker = new google.maps.Marker({
                position: { lat, lng },
                map: this.map,
                title: `Activity Hotspot - ${hotspot.location}`,
                icon: {
                    url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="12" cy="12" r="10" fill="#FF5722" stroke="#D84315" stroke-width="2"/>
                            <text x="12" y="16" text-anchor="middle" fill="white" font-size="12">🔥</text>
                        </svg>
                    `),
                    scaledSize: new google.maps.Size(24, 24)
                }
            });
            
            // Hotspot info
            const infoWindow = new google.maps.InfoWindow({
                content: `
                    <div class="hotspot-info">
                        <h4>🔥 Activity Hotspot</h4>
                        <p><strong>Location:</strong> ${hotspot.location}</p>
                        <p><strong>Activity Score:</strong> ${hotspot.activity_score.toFixed(1)}/10</p>
                        <p><strong>Watching Suitability:</strong> ${(hotspot.whale_watching_suitability * 100).toFixed(0)}%</p>
                        <p><strong>Foraging Probability:</strong> ${(hotspot.behavioral_features.foraging_probability * 100).toFixed(0)}%</p>
                        <p><strong>Social Activity:</strong> ${(hotspot.behavioral_features.social_activity_score * 100).toFixed(0)}%</p>
                        <button onclick="this.planRouteToHotspot('${index}')" class="btn-small">
                            Plan Route Here
                        </button>
                    </div>
                `
            });
            
            marker.addListener('click', () => {
                infoWindow.open(this.map, marker);
            });
            
            this.hotspotOverlays.set(hotspot.location, { circle, marker });
        });
    }
    
    async updateRouteRecommendations() {
        // Mock route recommendations
        const mockRoutes = {
            recommended_routes: [
                {
                    route_id: 'route_orcasound_lab',
                    primary_destination: {
                        location: 'Orcasound Lab',
                        coordinates: [48.5583362, -123.1735774]
                    },
                    waypoints: [],
                    estimated_duration_hours: 2.5,
                    success_probability: 0.85,
                    recommendations: ['High foraging activity - expect feeding behaviors']
                }
            ]
        };
        
        this.routeRecommendations = mockRoutes;
        this.updateRouteDisplay();
        this.updateStatus('route-recommendations', mockRoutes.recommended_routes.length);
    }
    
    updateRouteDisplay() {
        // Clear existing route polylines
        this.routePolylines.forEach(polyline => polyline.setMap(null));
        this.routePolylines.clear();
        
        if (!this.routeRecommendations) return;
        
        // For simplicity, just show markers for destinations
        this.routeRecommendations.recommended_routes.forEach(route => {
            const [lat, lng] = route.primary_destination.coordinates;
            
            const marker = new google.maps.Marker({
                position: { lat, lng },
                map: this.map,
                title: `Recommended Route - ${route.primary_destination.location}`,
                icon: {
                    url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="16" cy="16" r="14" fill="#9C27B0" stroke="#7B1FA2" stroke-width="2"/>
                            <text x="16" y="20" text-anchor="middle" fill="white" font-size="14">🗺️</text>
                        </svg>
                    `),
                    scaledSize: new google.maps.Size(32, 32)
                }
            });
            
            this.routePolylines.set(route.route_id, marker);
        });
    }
    
    async updatePredictions() {
        // Implementation for prediction visualization
        // This would show predicted whale locations based on behavioral models
    }
    
    setupFirebaseListeners() {
        if (!this.db) return;
        
        // Listen for behavioral insights updates
        this.db.collection('orcast_behavioral_predictions')
            .orderBy('timestamp', 'desc')
            .limit(1)
            .onSnapshot((snapshot) => {
                snapshot.forEach((doc) => {
                    this.behavioralInsights = doc.data();
                    this.updateHotspotDisplay();
                });
            });
        
        // Listen for route recommendation updates
        this.db.collection('orcast_route_recommendations')
            .orderBy('timestamp', 'desc')
            .limit(1)
            .onSnapshot((snapshot) => {
                snapshot.forEach((doc) => {
                    this.routeRecommendations = doc.data();
                    this.updateRouteDisplay();
                });
            });
    }
    
    // Utility methods for UI updates
    updateStatus(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }
    
    updateConnectionStatus(status) {
        const indicator = document.getElementById('connection-indicator');
        if (indicator) {
            indicator.className = `indicator ${status}`;
            indicator.title = {
                'connecting': 'Connecting to OrcaHello...',
                'active': 'Connected to OrcaHello',
                'error': 'Connection error'
            }[status] || 'Unknown status';
        }
    }
    
    addActivityFeedItem(message) {
        const feed = document.getElementById('activity-feed');
        if (feed) {
            const timestamp = new Date().toLocaleTimeString();
            const item = document.createElement('div');
            item.className = 'activity-item';
            item.innerHTML = `<span class="time">${timestamp}</span> ${message}`;
            
            feed.insertBefore(item, feed.firstChild);
            
            // Keep only last 5 items
            while (feed.children.length > 5) {
                feed.removeChild(feed.lastChild);
            }
        }
    }
    
    // Layer toggle methods
    toggleHydrophones(show) {
        this.hydrophoneMarkers.forEach(marker => {
            marker.setVisible(show);
        });
    }
    
    toggleDetections(show) {
        this.detectionMarkers.forEach(marker => {
            marker.setVisible(show);
        });
    }
    
    toggleHotspots(show) {
        this.hotspotOverlays.forEach(overlay => {
            overlay.circle.setVisible(show);
            overlay.marker.setVisible(show);
        });
    }
    
    toggleRoutes(show) {
        this.routePolylines.forEach(polyline => {
            polyline.setVisible(show);
        });
    }
    
    togglePredictions(show) {
        this.predictionCircles.forEach(circle => {
            circle.setVisible(show);
        });
    }
    
    // Cleanup
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        // Remove all markers and overlays
        this.hydrophoneMarkers.forEach(marker => marker.setMap(null));
        this.detectionMarkers.forEach(marker => marker.setMap(null));
        this.hotspotOverlays.forEach(overlay => {
            overlay.circle.setMap(null);
            overlay.marker.setMap(null);
        });
        this.routePolylines.forEach(polyline => polyline.setMap(null));
        this.predictionCircles.forEach(circle => circle.setMap(null));
        
        // Remove UI elements
        const controlPanel = document.getElementById('orcahello-controls');
        const statusPanel = document.getElementById('orcahello-status');
        if (controlPanel) controlPanel.remove();
        if (statusPanel) statusPanel.remove();
    }
}

// Global instance for integration with existing ORCAST frontend
let orcaHelloIntegration = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Wait for ORCAST map to be ready
    if (window.map && window.db) {
        orcaHelloIntegration = new ORCASTOrcaHelloFrontend(window.map, window.db);
    } else {
        // Retry after a short delay
        setTimeout(() => {
            if (window.map && window.db) {
                orcaHelloIntegration = new ORCASTOrcaHelloFrontend(window.map, window.db);
            }
        }, 2000);
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ORCASTOrcaHelloFrontend;
} 