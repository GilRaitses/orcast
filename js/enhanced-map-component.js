/**
 * Enhanced ORCAST Map Component
 * Multiple time-based probability layers with independent controls
 */

class EnhancedORCASTMap {
    constructor(containerId, config = {}) {
        this.container = document.getElementById(containerId);
        this.config = {
            center: { lat: 48.5465, lng: -123.0307 },
            zoom: 11,
            updateInterval: 30000, // 30 seconds
            ...config
        };
        
        this.map = null;
        this.layers = {
            realtime: {
                heatmap: null,
                data: [],
                enabled: true,
                opacity: 0.8,
                lastUpdate: null
            },
            future: {
                heatmap: null,
                data: [],
                enabled: true,
                opacity: 0.6,
                forecast: '24h' // 24h, 48h, 7d
            },
            historical: {
                heatmap: null,
                data: [],
                enabled: true,
                opacity: 0.5,
                period: 'week', // day, week, month, year
                offset: 0 // 0 = current, -1 = previous period, etc.
            }
        };
        
        this.dataProviders = {
            realtime: new RealtimeDataProvider(),
            future: new ForecastDataProvider(), 
            historical: new HistoricalDataProvider()
        };
        
        this.initialize();
    }

    async initialize() {
        await this.initializeMap();
        this.createUI();
        this.setupEventListeners();
        await this.loadAllLayers();
        this.startAutoUpdate();
    }

    async initializeMap() {
        // Wait for Google Maps to load
        await this.waitForGoogleMaps();
        
        this.map = new google.maps.Map(this.container.querySelector('#enhanced-map'), {
            zoom: this.config.zoom,
            center: this.config.center,
            mapTypeId: 'hybrid',
            restriction: {
                latLngBounds: {
                    north: 48.8,
                    south: 48.3,
                    east: -122.7,
                    west: -123.4
                },
                strictBounds: false
            }
        });
    }

    createUI() {
        this.container.innerHTML = `
            <div class="enhanced-map-container">
                <!-- Map -->
                <div id="enhanced-map" class="map-display"></div>
                
                <!-- Layer Controls -->
                <div class="layer-controls-panel">
                    <h3>📊 Probability Layers</h3>
                    
                    <!-- Real-time Layer -->
                    <div class="layer-section realtime-layer">
                        <div class="layer-header">
                            <h4>🔴 Real-time Data</h4>
                            <label class="layer-toggle">
                                <input type="checkbox" id="realtime-enabled" checked>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="layer-info">
                            <span class="time-indicator" id="realtime-time">Loading...</span>
                            <span class="data-points" id="realtime-points">-- points</span>
                        </div>
                        <div class="layer-controls">
                            <label>Probability Threshold:</label>
                            <input type="range" id="realtime-threshold" min="0" max="100" value="30" class="threshold-slider">
                            <span id="realtime-threshold-value">30%</span>
                            
                            <label>Opacity:</label>
                            <input type="range" id="realtime-opacity" min="0" max="100" value="80" class="opacity-slider">
                            <span id="realtime-opacity-value">80%</span>
                            
                            <label>Auto-refresh:</label>
                            <input type="range" id="realtime-refresh" min="10" max="300" value="30" class="refresh-slider">
                            <span id="realtime-refresh-value">30s</span>
                        </div>
                    </div>
                    
                    <!-- Future/Forecast Layer -->
                    <div class="layer-section future-layer">
                        <div class="layer-header">
                            <h4>🔮 Future Forecast</h4>
                            <label class="layer-toggle">
                                <input type="checkbox" id="future-enabled" checked>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="layer-info">
                            <span class="time-indicator" id="future-time">Next 24 hours</span>
                            <span class="confidence-indicator" id="future-confidence">-- confidence</span>
                        </div>
                        <div class="layer-controls">
                            <label>Forecast Period:</label>
                            <select id="future-period" class="period-select">
                                <option value="24h">Next 24 hours</option>
                                <option value="48h">Next 48 hours</option>
                                <option value="7d">Next 7 days</option>
                            </select>
                            
                            <label>Probability Threshold:</label>
                            <input type="range" id="future-threshold" min="0" max="100" value="40" class="threshold-slider">
                            <span id="future-threshold-value">40%</span>
                            
                            <label>Opacity:</label>
                            <input type="range" id="future-opacity" min="0" max="100" value="60" class="opacity-slider">
                            <span id="future-opacity-value">60%</span>
                        </div>
                    </div>
                    
                    <!-- Historical Layer -->
                    <div class="layer-section historical-layer">
                        <div class="layer-header">
                            <h4>📈 Historical Data</h4>
                            <label class="layer-toggle">
                                <input type="checkbox" id="historical-enabled" checked>
                                <span class="toggle-slider"></span>
                            </label>
                        </div>
                        <div class="layer-info">
                            <span class="time-indicator" id="historical-time">Current week</span>
                            <span class="data-points" id="historical-points">-- sightings</span>
                        </div>
                        <div class="layer-controls">
                            <label>Time Period:</label>
                            <select id="historical-period" class="period-select">
                                <option value="day">Daily</option>
                                <option value="week" selected>Weekly</option>
                                <option value="month">Monthly</option>
                                <option value="year">Yearly</option>
                            </select>
                            
                            <label>Period Navigation:</label>
                            <div class="period-navigation">
                                <button id="historical-prev" class="nav-btn">‹ Previous</button>
                                <span id="historical-current">Current</span>
                                <button id="historical-next" class="nav-btn">Next ›</button>
                            </div>
                            
                            <label>Confidence Level:</label>
                            <input type="range" id="historical-confidence" min="0" max="100" value="50" class="threshold-slider">
                            <span id="historical-confidence-value">50%</span>
                            
                            <label>Opacity:</label>
                            <input type="range" id="historical-opacity" min="0" max="100" value="50" class="opacity-slider">
                            <span id="historical-opacity-value">50%</span>
                        </div>
                    </div>
                    
                    <!-- Global Controls -->
                    <div class="global-controls">
                        <h4>🎛️ Global Settings</h4>
                        <button id="refresh-all" class="action-btn">🔄 Refresh All Layers</button>
                        <button id="reset-view" class="action-btn">🎯 Reset Map View</button>
                        <label class="auto-update-toggle">
                            <input type="checkbox" id="auto-update" checked>
                            <span>Auto-update enabled</span>
                        </label>
                    </div>
                </div>
                
                <!-- Status Bar -->
                <div class="status-bar">
                    <div class="status-section">
                        <span class="status-label">System Status:</span>
                        <span id="system-status" class="status-value">Initializing...</span>
                    </div>
                    <div class="status-section">
                        <span class="status-label">Last Update:</span>
                        <span id="last-update" class="status-value">--</span>
                    </div>
                    <div class="status-section">
                        <span class="status-label">Active Layers:</span>
                        <span id="active-layers" class="status-value">3/3</span>
                    </div>
                </div>
                
                <!-- Legend -->
                <div class="enhanced-legend">
                    <h4>Legend</h4>
                    <div class="legend-section">
                        <div class="legend-item realtime">
                            <div class="legend-color realtime-color"></div>
                            <span>Real-time (Live data)</span>
                        </div>
                        <div class="legend-item future">
                            <div class="legend-color future-color"></div>
                            <span>Forecast (Predicted)</span>
                        </div>
                        <div class="legend-item historical">
                            <div class="legend-color historical-color"></div>
                            <span>Historical (Past data)</span>
                        </div>
                    </div>
                    <div class="probability-scale">
                        <span>Low</span>
                        <div class="gradient-bar"></div>
                        <span>High</span>
                    </div>
                </div>
            </div>
        `;
    }

    setupEventListeners() {
        // Layer toggles
        ['realtime', 'future', 'historical'].forEach(layerType => {
            document.getElementById(`${layerType}-enabled`).addEventListener('change', (e) => {
                this.toggleLayer(layerType, e.target.checked);
            });
            
            // Threshold sliders
            const thresholdSlider = document.getElementById(`${layerType}-threshold`) ||
                                  document.getElementById(`${layerType}-confidence`);
            if (thresholdSlider) {
                thresholdSlider.addEventListener('input', (e) => {
                    this.updateLayerThreshold(layerType, parseInt(e.target.value));
                });
            }
            
            // Opacity sliders
            document.getElementById(`${layerType}-opacity`).addEventListener('input', (e) => {
                this.updateLayerOpacity(layerType, parseInt(e.target.value) / 100);
            });
        });

        // Period selectors
        document.getElementById('future-period').addEventListener('change', (e) => {
            this.updateForecastPeriod(e.target.value);
        });

        document.getElementById('historical-period').addEventListener('change', (e) => {
            this.updateHistoricalPeriod(e.target.value);
        });

        // Historical navigation
        document.getElementById('historical-prev').addEventListener('click', () => {
            this.navigateHistorical(-1);
        });

        document.getElementById('historical-next').addEventListener('click', () => {
            this.navigateHistorical(1);
        });

        // Global controls
        document.getElementById('refresh-all').addEventListener('click', () => {
            this.refreshAllLayers();
        });

        document.getElementById('reset-view').addEventListener('click', () => {
            this.resetMapView();
        });

        document.getElementById('auto-update').addEventListener('change', (e) => {
            this.toggleAutoUpdate(e.target.checked);
        });

        // Real-time refresh rate
        document.getElementById('realtime-refresh').addEventListener('input', (e) => {
            this.updateRefreshRate(parseInt(e.target.value) * 1000);
        });
    }

    async loadAllLayers() {
        this.updateStatus('Loading all layers...');
        
        try {
            // Load all layers in parallel
            await Promise.all([
                this.loadRealtimeLayer(),
                this.loadFutureLayer(),
                this.loadHistoricalLayer()
            ]);
            
            this.updateStatus('All layers loaded');
            this.updateLastUpdate();
            
        } catch (error) {
            console.error('Failed to load layers:', error);
            this.updateStatus('Error loading layers');
        }
    }

    async loadRealtimeLayer() {
        const data = await this.dataProviders.realtime.getCurrentData();
        this.layers.realtime.data = data;
        this.layers.realtime.lastUpdate = new Date();
        
        this.updateLayerDisplay('realtime');
        this.updateTimeIndicator('realtime', 'Live - Updated now');
        this.updateDataPoints('realtime', data.length);
    }

    async loadFutureLayer() {
        const period = this.layers.future.forecast;
        const data = await this.dataProviders.future.getForecastData(period);
        this.layers.future.data = data;
        
        this.updateLayerDisplay('future');
        this.updateTimeIndicator('future', this.formatForecastPeriod(period));
        this.updateConfidenceIndicator(data.avgConfidence || 0.75);
    }

    async loadHistoricalLayer() {
        const period = this.layers.historical.period;
        const offset = this.layers.historical.offset;
        const data = await this.dataProviders.historical.getHistoricalData(period, offset);
        this.layers.historical.data = data;
        
        this.updateLayerDisplay('historical');
        this.updateTimeIndicator('historical', this.formatHistoricalPeriod(period, offset));
        this.updateDataPoints('historical', data.length, 'sightings');
    }

    updateLayerDisplay(layerType) {
        const layer = this.layers[layerType];
        if (!layer.enabled || !layer.data.length) {
            if (layer.heatmap) {
                layer.heatmap.setMap(null);
            }
            return;
        }

        // Filter data by threshold
        const threshold = this.getLayerThreshold(layerType);
        const filteredData = layer.data.filter(point => point.probability >= threshold);

        // Create heatmap data
        const heatmapData = filteredData.map(point => ({
            location: new google.maps.LatLng(point.lat, point.lng),
            weight: point.probability / 100
        }));

        // Remove existing heatmap
        if (layer.heatmap) {
            layer.heatmap.setMap(null);
        }

        // Create new heatmap
        layer.heatmap = new google.maps.visualization.HeatmapLayer({
            data: heatmapData,
            map: this.map,
            radius: this.getLayerRadius(layerType),
            opacity: layer.opacity,
            gradient: this.getLayerGradient(layerType)
        });
    }

    getLayerThreshold(layerType) {
        const slider = document.getElementById(`${layerType}-threshold`) ||
                      document.getElementById(`${layerType}-confidence`);
        return slider ? parseInt(slider.value) : 30;
    }

    getLayerRadius(layerType) {
        const radii = { realtime: 30, future: 35, historical: 25 };
        return radii[layerType] || 30;
    }

    getLayerGradient(layerType) {
        const gradients = {
            realtime: [
                'rgba(255, 0, 0, 0)',
                'rgba(255, 0, 0, 0.8)',
                'rgba(255, 128, 0, 1)',
                'rgba(255, 255, 0, 1)'
            ],
            future: [
                'rgba(0, 0, 255, 0)',
                'rgba(0, 128, 255, 0.8)',
                'rgba(128, 0, 255, 1)',
                'rgba(255, 0, 255, 1)'
            ],
            historical: [
                'rgba(0, 255, 0, 0)',
                'rgba(128, 255, 0, 0.6)',
                'rgba(255, 255, 0, 0.8)',
                'rgba(255, 128, 0, 1)'
            ]
        };
        return gradients[layerType];
    }

    toggleLayer(layerType, enabled) {
        this.layers[layerType].enabled = enabled;
        this.updateLayerDisplay(layerType);
        this.updateActiveLayersCount();
    }

    updateLayerThreshold(layerType, threshold) {
        const valueSpan = document.getElementById(`${layerType}-threshold-value`) ||
                         document.getElementById(`${layerType}-confidence-value`);
        if (valueSpan) {
            valueSpan.textContent = `${threshold}%`;
        }
        this.updateLayerDisplay(layerType);
    }

    updateLayerOpacity(layerType, opacity) {
        this.layers[layerType].opacity = opacity;
        document.getElementById(`${layerType}-opacity-value`).textContent = `${Math.round(opacity * 100)}%`;
        
        if (this.layers[layerType].heatmap) {
            this.layers[layerType].heatmap.setOptions({ opacity });
        }
    }

    async updateForecastPeriod(period) {
        this.layers.future.forecast = period;
        await this.loadFutureLayer();
    }

    async updateHistoricalPeriod(period) {
        this.layers.historical.period = period;
        this.layers.historical.offset = 0; // Reset to current period
        await this.loadHistoricalLayer();
    }

    async navigateHistorical(direction) {
        this.layers.historical.offset += direction;
        await this.loadHistoricalLayer();
        
        // Update navigation button states
        const nextBtn = document.getElementById('historical-next');
        nextBtn.disabled = this.layers.historical.offset >= 0;
    }

    formatForecastPeriod(period) {
        const formats = {
            '24h': 'Next 24 hours',
            '48h': 'Next 48 hours', 
            '7d': 'Next 7 days'
        };
        return formats[period] || period;
    }

    formatHistoricalPeriod(period, offset) {
        const now = new Date();
        const periodNames = {
            day: 'day',
            week: 'week', 
            month: 'month',
            year: 'year'
        };
        
        if (offset === 0) {
            return `Current ${periodNames[period]}`;
        } else if (offset < 0) {
            const abs = Math.abs(offset);
            return `${abs} ${periodNames[period]}${abs > 1 ? 's' : ''} ago`;
        } else {
            return `${offset} ${periodNames[period]}${offset > 1 ? 's' : ''} ahead`;
        }
    }

    updateTimeIndicator(layerType, text) {
        document.getElementById(`${layerType}-time`).textContent = text;
    }

    updateDataPoints(layerType, count, unit = 'points') {
        document.getElementById(`${layerType}-points`).textContent = `${count} ${unit}`;
    }

    updateConfidenceIndicator(confidence) {
        document.getElementById('future-confidence').textContent = `${Math.round(confidence * 100)}% confidence`;
    }

    updateActiveLayersCount() {
        const activeCount = Object.values(this.layers).filter(layer => layer.enabled).length;
        document.getElementById('active-layers').textContent = `${activeCount}/3`;
    }

    updateStatus(message) {
        document.getElementById('system-status').textContent = message;
    }

    updateLastUpdate() {
        document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
    }

    async refreshAllLayers() {
        await this.loadAllLayers();
    }

    resetMapView() {
        this.map.setCenter(this.config.center);
        this.map.setZoom(this.config.zoom);
    }

    toggleAutoUpdate(enabled) {
        if (enabled) {
            this.startAutoUpdate();
        } else {
            this.stopAutoUpdate();
        }
    }

    updateRefreshRate(milliseconds) {
        this.config.updateInterval = milliseconds;
        document.getElementById('realtime-refresh-value').textContent = `${milliseconds / 1000}s`;
        
        if (this.autoUpdateInterval) {
            this.stopAutoUpdate();
            this.startAutoUpdate();
        }
    }

    startAutoUpdate() {
        this.stopAutoUpdate();
        this.autoUpdateInterval = setInterval(() => {
            this.loadRealtimeLayer();
        }, this.config.updateInterval);
    }

    stopAutoUpdate() {
        if (this.autoUpdateInterval) {
            clearInterval(this.autoUpdateInterval);
            this.autoUpdateInterval = null;
        }
    }

    async waitForGoogleMaps() {
        return new Promise((resolve) => {
            if (typeof google !== 'undefined' && google.maps && google.maps.visualization) {
                resolve();
            } else {
                const checkGoogle = () => {
                    if (typeof google !== 'undefined' && google.maps && google.maps.visualization) {
                        resolve();
                    } else {
                        setTimeout(checkGoogle, 100);
                    }
                };
                checkGoogle();
            }
        });
    }
}

/**
 * Data Provider Classes
 */

class RealtimeDataProvider {
    async getCurrentData() {
        // Simulate real-time API call
        await this.delay(500);
        
        return this.generateRealtimeData();
    }

    generateRealtimeData() {
        const data = [];
        const basePoints = [
            { lat: 48.515, lng: -123.152, base: 85 }, // Lime Kiln Point
            { lat: 48.524, lng: -123.164, base: 72 }, // Salmon Bank
            { lat: 48.683, lng: -123.17, base: 68 },  // Stuart Island
            { lat: 48.4, lng: -122.95, base: 45 },    // South areas
            { lat: 48.7, lng: -123.3, base: 38 }      // North areas
        ];

        basePoints.forEach(point => {
            // Add some randomness for realism
            const probability = Math.max(0, Math.min(100, 
                point.base + (Math.random() - 0.5) * 20
            ));
            
            data.push({
                lat: point.lat + (Math.random() - 0.5) * 0.01,
                lng: point.lng + (Math.random() - 0.5) * 0.01,
                probability: Math.round(probability),
                timestamp: new Date(),
                confidence: Math.random() * 0.3 + 0.7
            });
        });

        return data;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

class ForecastDataProvider {
    async getForecastData(period) {
        await this.delay(800);
        
        return this.generateForecastData(period);
    }

    generateForecastData(period) {
        const data = [];
        const multipliers = { '24h': 1.0, '48h': 0.8, '7d': 0.6 };
        const multiplier = multipliers[period] || 1.0;

        // Generate forecast points with lower confidence
        for (let i = 0; i < 12; i++) {
            data.push({
                lat: 48.3 + Math.random() * 0.5,
                lng: -123.4 + Math.random() * 0.7,
                probability: Math.round(Math.random() * 80 * multiplier),
                confidence: Math.random() * 0.4 + 0.4,
                forecastTime: period
            });
        }

        data.avgConfidence = data.reduce((sum, p) => sum + p.confidence, 0) / data.length;

        return data;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

class HistoricalDataProvider {
    async getHistoricalData(period, offset) {
        await this.delay(600);
        
        return this.generateHistoricalData(period, offset);
    }

    generateHistoricalData(period, offset) {
        const data = [];
        const periodMultipliers = { day: 0.3, week: 1.0, month: 2.5, year: 10.0 };
        const multiplier = periodMultipliers[period] || 1.0;

        // Generate historical sightings
        const sightingCount = Math.round(5 * multiplier * (1 + Math.random()));
        
        for (let i = 0; i < sightingCount; i++) {
            data.push({
                lat: 48.3 + Math.random() * 0.5,
                lng: -123.4 + Math.random() * 0.7,
                probability: Math.round(Math.random() * 90 + 10),
                confidence: Math.random() * 0.5 + 0.5,
                date: this.getHistoricalDate(period, offset),
                verified: Math.random() > 0.3
            });
        }

        return data;
    }

    getHistoricalDate(period, offset) {
        const now = new Date();
        const periodDays = { day: 1, week: 7, month: 30, year: 365 };
        const days = periodDays[period] * Math.abs(offset);
        
        const date = new Date(now);
        date.setDate(date.getDate() - days);
        return date;
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Export for use
window.EnhancedORCASTMap = EnhancedORCASTMap; 