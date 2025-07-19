/**
 * ORCAST Frontend Integration Example
 * Shows how to consume spatial forecast data for map UI time slider
 */

class ORCASTMapController {
    constructor(mapElementId, timeSliderElementId) {
        this.map = this.initializeMap(mapElementId);
        this.timeSlider = document.getElementById(timeSliderElementId);
        this.currentForecast = null;
        this.heatmapLayer = null;
        this.currentTimeIndex = 0;
        
        this.setupEventListeners();
        this.loadCurrentForecast();
    }
    
    initializeMap(elementId) {
        // Initialize Leaflet map (example)
        const map = L.map(elementId).setView([48.6, -123.0], 10);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        return map;
    }
    
    async loadCurrentForecast() {
        try {
            console.log('📡 Loading current forecast from ORCAST ML Service...');
            
            const response = await fetch('http://localhost:8082/forecast/current');
            
            if (response.ok) {
                this.currentForecast = await response.json();
                console.log('✅ Forecast loaded:', {
                    forecastId: this.currentForecast.forecast_id,
                    region: this.currentForecast.metadata.region,
                    timeSlices: this.currentForecast.time_series.length,
                    gridPoints: this.currentForecast.time_series[0]?.grid_points.length
                });
                
                this.setupTimeSlider();
                this.updateMapVisualization(0);
                
            } else if (response.status === 404) {
                console.log('⚠️ No forecast available, generating new one...');
                await this.generateNewForecast();
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
        } catch (error) {
            console.error('❌ Failed to load forecast:', error);
            this.showErrorMessage('Failed to load orca behavior forecast');
        }
    }
    
    async generateNewForecast() {
        try {
            console.log('🔄 Generating new spatial forecast...');
            
            const response = await fetch('http://localhost:8082/forecast/quick', {
                method: 'POST'
            });
            
            if (response.ok) {
                const result = await response.json();
                console.log('✅ New forecast generated:', result);
                
                // Wait a moment for it to be saved, then reload
                setTimeout(() => this.loadCurrentForecast(), 3000);
                
            } else {
                throw new Error(`Failed to generate forecast: ${response.statusText}`);
            }
            
        } catch (error) {
            console.error('❌ Failed to generate forecast:', error);
        }
    }
    
    setupTimeSlider() {
        if (!this.currentForecast?.time_series) return;
        
        const timeSlices = this.currentForecast.time_series;
        
        // Configure slider
        this.timeSlider.min = 0;
        this.timeSlider.max = timeSlices.length - 1;
        this.timeSlider.value = 0;
        this.timeSlider.step = 1;
        
        // Add time labels
        this.updateTimeDisplay(0);
        
        console.log(`🎛️ Time slider configured: ${timeSlices.length} time steps`);
    }
    
    setupEventListeners() {
        // Time slider change
        this.timeSlider.addEventListener('input', (event) => {
            const timeIndex = parseInt(event.target.value);
            this.updateMapVisualization(timeIndex);
            this.updateTimeDisplay(timeIndex);
        });
        
        // Behavior type selector (if you have radio buttons)
        document.querySelectorAll('input[name="behavior-type"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.updateMapVisualization(this.currentTimeIndex);
            });
        });
    }
    
    updateMapVisualization(timeIndex) {
        if (!this.currentForecast?.time_series?.[timeIndex]) return;
        
        this.currentTimeIndex = timeIndex;
        const timeSlice = this.currentForecast.time_series[timeIndex];
        const selectedBehavior = this.getSelectedBehaviorType();
        
        console.log(`🗺️ Updating map for time slice ${timeIndex} (${selectedBehavior} behavior)`);
        
        // Remove existing heatmap
        if (this.heatmapLayer) {
            this.map.removeLayer(this.heatmapLayer);
        }
        
        // Create heatmap data
        const heatmapData = this.createHeatmapData(timeSlice.grid_points, selectedBehavior);
        
        // Add new heatmap layer
        this.heatmapLayer = L.heatLayer(heatmapData, {
            radius: 20,
            blur: 15,
            maxZoom: 17,
            gradient: {
                0.0: 'blue',
                0.3: 'cyan', 
                0.5: 'lime',
                0.7: 'yellow',
                1.0: 'red'
            }
        }).addTo(this.map);
        
        // Update statistics display
        this.updateStatisticsDisplay(timeSlice, selectedBehavior);
    }
    
    createHeatmapData(gridPoints, behaviorType) {
        return gridPoints.map(point => {
            let intensity;
            
            switch (behaviorType) {
                case 'feeding':
                    intensity = point.feeding_prob;
                    break;
                case 'socializing':
                    intensity = point.socializing_prob;
                    break;
                case 'traveling':
                    intensity = point.traveling_prob;
                    break;
                case 'confidence':
                    intensity = point.confidence;
                    break;
                default:
                    // Overall activity (1 - unknown probability)
                    intensity = 1 - (point.probabilities?.unknown || 0);
            }
            
            return [point.lat, point.lng, intensity];
        });
    }
    
    getSelectedBehaviorType() {
        const selected = document.querySelector('input[name="behavior-type"]:checked');
        return selected ? selected.value : 'feeding';
    }
    
    updateTimeDisplay(timeIndex) {
        if (!this.currentForecast?.time_series?.[timeIndex]) return;
        
        const timeSlice = this.currentForecast.time_series[timeIndex];
        const timestamp = new Date(timeSlice.timestamp);
        
        const timeDisplay = document.getElementById('time-display');
        if (timeDisplay) {
            timeDisplay.textContent = timestamp.toLocaleString();
        }
        
        const hourOffset = document.getElementById('hour-offset');
        if (hourOffset) {
            hourOffset.textContent = `+${timeSlice.hour_offset} hours`;
        }
    }
    
    updateStatisticsDisplay(timeSlice, behaviorType) {
        const gridPoints = timeSlice.grid_points;
        
        // Calculate statistics for current behavior type
        let values;
        switch (behaviorType) {
            case 'feeding':
                values = gridPoints.map(p => p.feeding_prob);
                break;
            case 'socializing':
                values = gridPoints.map(p => p.socializing_prob);
                break;
            case 'traveling':
                values = gridPoints.map(p => p.traveling_prob);
                break;
            default:
                values = gridPoints.map(p => p.confidence);
        }
        
        const stats = {
            min: Math.min(...values),
            max: Math.max(...values),
            avg: values.reduce((a, b) => a + b, 0) / values.length,
            count: values.length
        };
        
        // Update UI elements
        this.updateStatElement('min-prob', stats.min.toFixed(3));
        this.updateStatElement('max-prob', stats.max.toFixed(3));
        this.updateStatElement('avg-prob', stats.avg.toFixed(3));
        this.updateStatElement('grid-count', stats.count);
        
        // Behavior distribution
        const behaviors = gridPoints.map(p => p.predicted_behavior);
        const distribution = {};
        behaviors.forEach(b => distribution[b] = (distribution[b] || 0) + 1);
        
        this.updateBehaviorDistribution(distribution);
    }
    
    updateStatElement(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }
    
    updateBehaviorDistribution(distribution) {
        const container = document.getElementById('behavior-distribution');
        if (!container) return;
        
        container.innerHTML = '';
        
        Object.entries(distribution).forEach(([behavior, count]) => {
            const percentage = ((count / Object.values(distribution).reduce((a, b) => a + b, 0)) * 100).toFixed(1);
            
            const item = document.createElement('div');
            item.className = 'behavior-item';
            item.innerHTML = `
                <span class="behavior-name">${behavior}</span>
                <span class="behavior-count">${count} (${percentage}%)</span>
            `;
            container.appendChild(item);
        });
    }
    
    showErrorMessage(message) {
        const errorElement = document.getElementById('error-message');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }
    
    // Public methods for external control
    async refreshForecast() {
        console.log('🔄 Refreshing forecast...');
        await this.generateNewForecast();
    }
    
    setBehaviorType(behaviorType) {
        const radio = document.querySelector(`input[name="behavior-type"][value="${behaviorType}"]`);
        if (radio) {
            radio.checked = true;
            this.updateMapVisualization(this.currentTimeIndex);
        }
    }
    
    setTimeIndex(index) {
        if (index >= 0 && index < this.currentForecast?.time_series?.length) {
            this.timeSlider.value = index;
            this.updateMapVisualization(index);
            this.updateTimeDisplay(index);
        }
    }
}

// Example HTML structure needed for this integration:
const exampleHTML = `
<div id="orcast-map-container">
    <div id="map" style="height: 500px;"></div>
    
    <div id="controls">
        <div class="time-control">
            <label for="time-slider">Time:</label>
            <input type="range" id="time-slider" min="0" max="10" value="0">
            <div id="time-display">Loading...</div>
            <div id="hour-offset">+0 hours</div>
        </div>
        
        <div class="behavior-selector">
            <label>Behavior Type:</label>
            <input type="radio" name="behavior-type" value="feeding" checked> Feeding
            <input type="radio" name="behavior-type" value="socializing"> Socializing  
            <input type="radio" name="behavior-type" value="traveling"> Traveling
            <input type="radio" name="behavior-type" value="confidence"> Confidence
        </div>
        
        <div class="statistics">
            <h4>Current View Statistics</h4>
            <div>Min: <span id="min-prob">-</span></div>
            <div>Max: <span id="max-prob">-</span></div>
            <div>Avg: <span id="avg-prob">-</span></div>
            <div>Points: <span id="grid-count">-</span></div>
        </div>
        
        <div class="behavior-distribution">
            <h4>Behavior Distribution</h4>
            <div id="behavior-distribution"></div>
        </div>
    </div>
    
    <div id="error-message" style="display: none; color: red;"></div>
</div>
`;

// Usage example:
/*
// Initialize the map controller
const orcaMap = new ORCASTMapController('map', 'time-slider');

// Programmatic control examples:
// orcaMap.setBehaviorType('socializing');
// orcaMap.setTimeIndex(2);
// orcaMap.refreshForecast();
*/

console.log('🗺️ ORCAST Frontend Integration Example loaded');
console.log('📋 Required HTML structure:', exampleHTML); 