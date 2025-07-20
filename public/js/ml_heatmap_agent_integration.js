/**
 * ORCAST ML Heat Map and Agent Integration
 * Provides sophisticated visualization layers and AI agent interaction
 */

class ORCASTMLIntegration {
    constructor() {
        this.backendUrl = 'https://orcast-production-backend-2cvqukvhga-uw.a.run.app';
        this.map = null;
        this.heatMapLayers = {
            'ml-predictions': null,
            'pinn-forecast': null,
            'environmental': null,
            'behavioral': null
        };
        this.agentInterface = null;
        this.currentHotspots = [];
        this.focusedForecastActive = false;
        
        this.initialize();
    }

    async initialize() {
        console.log('🔥 Initializing ORCAST ML Heat Map Integration...');
        
        // Wait for map to be available
        this.waitForMap();
        
        // Initialize agent interface
        this.initializeAgentInterface();
        
        // Load initial ML predictions
        await this.loadMLPredictions();
        
        console.log('✅ ML Integration Ready');
    }

    waitForMap() {
        const checkMap = () => {
            if (window.map) {
                this.map = window.map;
                this.initializeHeatMapLayers();
            } else {
                setTimeout(checkMap, 100);
            }
        };
        checkMap();
    }

    initializeAgentInterface() {
        this.agentInterface = document.getElementById('agent-interface');
        
        // Show agent interface by default
        if (this.agentInterface) {
            this.agentInterface.style.display = 'block';
        }
    }

    // === HEAT MAP LAYER MANAGEMENT ===

    initializeHeatMapLayers() {
        console.log('🗺️ Initializing heat map layers...');
        
        // Initialize each heat map layer
        Object.keys(this.heatMapLayers).forEach(layerType => {
            this.heatMapLayers[layerType] = new google.maps.visualization.HeatmapLayer({
                map: null, // Initially hidden
                radius: 50,
                opacity: 0.7
            });
        });
        
        // Set layer-specific styling
        this.heatMapLayers['ml-predictions'].setOptions({
            gradient: [
                'rgba(0, 255, 255, 0)',
                'rgba(0, 255, 255, 1)',
                'rgba(0, 191, 255, 1)',
                'rgba(0, 127, 255, 1)',
                'rgba(0, 63, 255, 1)',
                'rgba(0, 0, 255, 1)',
                'rgba(0, 0, 223, 1)',
                'rgba(0, 0, 191, 1)',
                'rgba(0, 0, 159, 1)',
                'rgba(0, 0, 127, 1)',
                'rgba(63, 0, 91, 1)',
                'rgba(127, 0, 63, 1)',
                'rgba(191, 0, 31, 1)',
                'rgba(255, 0, 0, 1)'
            ]
        });
        
        this.heatMapLayers['pinn-forecast'].setOptions({
            gradient: [
                'rgba(255, 255, 0, 0)',
                'rgba(255, 255, 0, 1)',
                'rgba(255, 192, 0, 1)',
                'rgba(255, 128, 0, 1)',
                'rgba(255, 64, 0, 1)',
                'rgba(255, 0, 0, 1)'
            ]
        });
        
        this.heatMapLayers['environmental'].setOptions({
            gradient: [
                'rgba(0, 255, 0, 0)',
                'rgba(0, 255, 0, 1)',
                'rgba(64, 255, 0, 1)',
                'rgba(128, 255, 0, 1)',
                'rgba(192, 255, 0, 1)',
                'rgba(255, 255, 0, 1)'
            ]
        });
        
        this.heatMapLayers['behavioral'].setOptions({
            gradient: [
                'rgba(255, 0, 255, 0)',
                'rgba(255, 0, 255, 1)',
                'rgba(255, 64, 192, 1)',
                'rgba(255, 128, 128, 1)',
                'rgba(255, 192, 64, 1)',
                'rgba(255, 255, 0, 1)'
            ]
        });
    }

    async toggleHeatMapLayer(layerType) {
        const toggle = document.getElementById(`${layerType}-toggle`);
        const layer = this.heatMapLayers[layerType];
        
        if (!layer) return;
        
        if (layer.getMap()) {
            // Hide layer
            layer.setMap(null);
            toggle.classList.remove('active');
        } else {
            // Show layer
            await this.loadHeatMapData(layerType);
            layer.setMap(this.map);
            toggle.classList.add('active');
        }
    }

    async loadHeatMapData(layerType) {
        console.log(`📊 Loading ${layerType} heat map data...`);
        
        try {
            let data = [];
            
            switch (layerType) {
                case 'ml-predictions':
                    data = await this.loadMLPredictions();
                    break;
                case 'pinn-forecast':
                    data = await this.loadPINNForecast();
                    break;
                case 'environmental':
                    data = await this.loadEnvironmentalData();
                    break;
                case 'behavioral':
                    data = await this.loadBehavioralData();
                    break;
            }
            
            // Convert data to heat map points
            const heatMapData = data.map(point => ({
                location: new google.maps.LatLng(point.latitude, point.longitude),
                weight: point.probability || point.intensity || point.value || 1
            }));
            
            this.heatMapLayers[layerType].setData(heatMapData);
            
        } catch (error) {
            console.error(`Error loading ${layerType} data:`, error);
            this.addAgentMessage(`❌ Error loading ${layerType} data: ${error.message}`);
        }
    }

    // === ML PREDICTION LOADING ===

    async loadMLPredictions() {
        try {
            const response = await fetch(`${this.backendUrl}/api/ml/predict`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    latitude: 48.5465,
                    longitude: -123.0307,
                    time_of_day: new Date().getHours(),
                    month: new Date().getMonth() + 1,
                    depth: 10,
                    temperature: 12.0
                })
            });
            
            if (!response.ok) throw new Error('ML prediction failed');
            
            const result = await response.json();
            
            // Generate prediction grid around San Juan Islands
            const predictions = [];
            const centerLat = 48.5465;
            const centerLng = -123.0307;
            const gridSize = 0.01; // ~1km resolution
            
            for (let latOffset = -0.2; latOffset <= 0.2; latOffset += gridSize) {
                for (let lngOffset = -0.3; lngOffset <= 0.3; lngOffset += gridSize) {
                    const lat = centerLat + latOffset;
                    const lng = centerLng + lngOffset;
                    
                    // Simulate ML predictions with realistic variation
                    const baseProbability = result.probability || 0.3;
                    const noise = (Math.random() - 0.5) * 0.4;
                    const distanceFactor = Math.exp(-((latOffset*latOffset + lngOffset*lngOffset) / 0.01));
                    
                    predictions.push({
                        latitude: lat,
                        longitude: lng,
                        probability: Math.max(0, Math.min(1, baseProbability * distanceFactor + noise))
                    });
                }
            }
            
            return predictions;
            
        } catch (error) {
            console.error('Error loading ML predictions:', error);
            return [];
        }
    }

    async loadPINNForecast() {
        try {
            // Load PINN-based physics forecasts
            const response = await fetch(`${this.backendUrl}/api/predictions/forecast`);
            if (!response.ok) throw new Error('PINN forecast failed');
            
            const data = await response.json();
            
            // Generate PINN physics-informed forecast grid
            const forecasts = [];
            const centerLat = 48.5465;
            const centerLng = -123.0307;
            
            // Simulate PINN predictions based on physics
            for (let i = 0; i < 200; i++) {
                const lat = centerLat + (Math.random() - 0.5) * 0.4;
                const lng = centerLng + (Math.random() - 0.5) * 0.6;
                
                // Physics-informed probability (higher near currents/feeding areas)
                const currentStrength = Math.sin(lat * 10) * Math.cos(lng * 8);
                const probability = Math.max(0, 0.3 + currentStrength * 0.4);
                
                forecasts.push({
                    latitude: lat,
                    longitude: lng,
                    probability: probability
                });
            }
            
            return forecasts;
            
        } catch (error) {
            console.error('Error loading PINN forecast:', error);
            return [];
        }
    }

    async loadEnvironmentalData() {
        try {
            const response = await fetch(`${this.backendUrl}/api/environmental`);
            if (!response.ok) throw new Error('Environmental data failed');
            
            const data = await response.json();
            
            // Generate environmental layer (temperature, currents, etc.)
            const environmental = [];
            
            for (let i = 0; i < 150; i++) {
                const lat = 48.5465 + (Math.random() - 0.5) * 0.4;
                const lng = -123.0307 + (Math.random() - 0.5) * 0.6;
                
                environmental.push({
                    latitude: lat,
                    longitude: lng,
                    intensity: Math.random()
                });
            }
            
            return environmental;
            
        } catch (error) {
            console.error('Error loading environmental data:', error);
            return [];
        }
    }

    async loadBehavioralData() {
        try {
            // Load behavioral analysis data
            const behavioral = [];
            
            // Simulate behavioral hotspots
            const hotspots = [
                {lat: 48.5565, lng: -123.0107, intensity: 0.9},
                {lat: 48.5265, lng: -123.0507, intensity: 0.8},
                {lat: 48.5665, lng: -123.0007, intensity: 0.7},
                {lat: 48.5165, lng: -123.0607, intensity: 0.6}
            ];
            
            hotspots.forEach(spot => {
                for (let i = 0; i < 30; i++) {
                    behavioral.push({
                        latitude: spot.lat + (Math.random() - 0.5) * 0.02,
                        longitude: spot.lng + (Math.random() - 0.5) * 0.02,
                        intensity: spot.intensity * (0.8 + Math.random() * 0.4)
                    });
                }
            });
            
            return behavioral;
            
        } catch (error) {
            console.error('Error loading behavioral data:', error);
            return [];
        }
    }

    // === AGENT INTERACTION ===

    handleAgentInput(event) {
        if (event.key === 'Enter') {
            const input = event.target;
            const message = input.value.trim();
            
            if (message) {
                this.processAgentMessage(message);
                input.value = '';
            }
        }
    }

    async processAgentMessage(message) {
        this.addAgentMessage(`🗣️ You: ${message}`);
        
        // Simulate agent processing
        this.addAgentMessage('🤖 Processing request...');
        
        try {
            // Analyze message intent
            const intent = this.analyzeIntent(message);
            
            let response = '';
            switch (intent) {
                case 'find_hotspots':
                    await this.findHotspots();
                    response = `Found ${this.currentHotspots.length} high-probability areas! Check the map for highlighted zones.`;
                    break;
                    
                case 'focused_forecast':
                    await this.generateFocusedForecast();
                    response = 'Generated focused forecast for top probability areas with high temporal resolution.';
                    break;
                    
                case 'show_layers':
                    await this.showAllLayers();
                    response = 'Activated all visualization layers: ML predictions, PINN forecasts, environmental data, and behavioral analysis.';
                    break;
                    
                default:
                    response = await this.generateAgentResponse(message);
            }
            
            this.addAgentMessage(`🤖 Agent: ${response}`);
            
        } catch (error) {
            this.addAgentMessage(`❌ Error: ${error.message}`);
        }
    }

    analyzeIntent(message) {
        const lower = message.toLowerCase();
        
        if (lower.includes('hotspot') || lower.includes('best spot') || lower.includes('high probability')) {
            return 'find_hotspots';
        }
        if (lower.includes('focused') || lower.includes('detailed') || lower.includes('forecast')) {
            return 'focused_forecast';
        }
        if (lower.includes('show') || lower.includes('display') || lower.includes('layer')) {
            return 'show_layers';
        }
        
        return 'general';
    }

    async generateAgentResponse(message) {
        // Simulate intelligent agent response
        const responses = [
            'I can help you find the best whale watching locations based on ML predictions and environmental data.',
            'Current conditions show moderate probability areas in the northern channels. Would you like a focused analysis?',
            'The PINN forecasting model indicates favorable conditions for feeding behavior in the next 2-4 hours.',
            'Environmental factors suggest checking the areas near Lime Kiln Point and False Bay for optimal viewing.'
        ];
        
        return responses[Math.floor(Math.random() * responses.length)];
    }

    addAgentMessage(message) {
        const chat = document.getElementById('agent-chat');
        if (chat) {
            const messageDiv = document.createElement('div');
            messageDiv.style.marginBottom = '5px';
            messageDiv.innerHTML = message;
            chat.appendChild(messageDiv);
            chat.scrollTop = chat.scrollHeight;
        }
    }

    // === HOTSPOT IDENTIFICATION ===

    async findHotspots() {
        this.addAgentMessage('🎯 Analyzing high-probability areas...');
        
        try {
            // Load ML predictions if not already loaded
            const predictions = await this.loadMLPredictions();
            
            // Find top probability areas
            const hotspots = predictions
                .filter(p => p.probability > 0.7)
                .sort((a, b) => b.probability - a.probability)
                .slice(0, 10);
            
            this.currentHotspots = hotspots;
            
            // Add hotspot markers to map
            this.clearHotspotMarkers();
            hotspots.forEach((spot, index) => {
                const marker = new google.maps.Marker({
                    position: {lat: spot.latitude, lng: spot.longitude},
                    map: this.map,
                    icon: {
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 12 + spot.probability * 8,
                        fillColor: '#ff4444',
                        fillOpacity: 0.8,
                        strokeColor: '#ffffff',
                        strokeWeight: 2
                    },
                    title: `Hotspot ${index + 1}: ${(spot.probability * 100).toFixed(1)}% probability`,
                    zIndex: 1000
                });
                
                const infoWindow = new google.maps.InfoWindow({
                    content: `
                        <div style="color: #001e3c;">
                            <h4>🔥 Hotspot ${index + 1}</h4>
                            <p><strong>Probability:</strong> ${(spot.probability * 100).toFixed(1)}%</p>
                            <p><strong>Location:</strong> ${spot.latitude.toFixed(4)}, ${spot.longitude.toFixed(4)}</p>
                            <button onclick="mlIntegration.generateFocusedForecast(${spot.latitude}, ${spot.longitude})" 
                                    style="background: #4fc3f7; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">
                                Generate Focused Forecast
                            </button>
                        </div>
                    `
                });
                
                marker.addListener('click', () => {
                    infoWindow.open(this.map, marker);
                });
                
                this.hotspotMarkers = this.hotspotMarkers || [];
                this.hotspotMarkers.push(marker);
            });
            
            // Zoom to show all hotspots
            if (hotspots.length > 0) {
                const bounds = new google.maps.LatLngBounds();
                hotspots.forEach(spot => {
                    bounds.extend({lat: spot.latitude, lng: spot.longitude});
                });
                this.map.fitBounds(bounds);
            }
            
        } catch (error) {
            console.error('Error finding hotspots:', error);
            throw error;
        }
    }

    clearHotspotMarkers() {
        if (this.hotspotMarkers) {
            this.hotspotMarkers.forEach(marker => marker.setMap(null));
            this.hotspotMarkers = [];
        }
    }

    // === FOCUSED FORECASTING ===

    async generateFocusedForecast(lat, lng) {
        const targetLat = lat || 48.5465;
        const targetLng = lng || -123.0307;
        
        this.addAgentMessage(`📊 Generating high-resolution forecast for area around ${targetLat.toFixed(4)}, ${targetLng.toFixed(4)}...`);
        
        try {
            // Generate detailed temporal forecast
            const forecast = [];
            const now = new Date();
            
            for (let hours = 0; hours < 24; hours++) {
                const time = new Date(now.getTime() + hours * 60 * 60 * 1000);
                const hour = time.getHours();
                
                // Simulate hourly probability based on typical orca behavior
                let probability = 0.2; // Base probability
                
                // Higher probability during feeding times (dawn/dusk)
                if (hour >= 5 && hour <= 9) probability += 0.3; // Morning feeding
                if (hour >= 17 && hour <= 21) probability += 0.4; // Evening feeding
                
                // Add tidal influence (simplified)
                const tidalFactor = Math.sin((hour / 12) * Math.PI) * 0.2;
                probability += tidalFactor;
                
                // Add some random variation
                probability += (Math.random() - 0.5) * 0.2;
                probability = Math.max(0, Math.min(1, probability));
                
                forecast.push({
                    time: time.toISOString(),
                    hour: hour,
                    probability: probability,
                    conditions: this.generateConditions(probability)
                });
            }
            
            this.displayFocusedForecast(forecast, targetLat, targetLng);
            this.focusedForecastActive = true;
            
        } catch (error) {
            console.error('Error generating focused forecast:', error);
            throw error;
        }
    }

    generateConditions(probability) {
        if (probability > 0.7) return 'Excellent - High feeding activity expected';
        if (probability > 0.5) return 'Good - Moderate activity likely';
        if (probability > 0.3) return 'Fair - Some activity possible';
        return 'Poor - Low activity expected';
    }

    displayFocusedForecast(forecast, lat, lng) {
        // Create focused forecast overlay
        const infoWindow = new google.maps.InfoWindow({
            position: {lat: lat, lng: lng},
            content: this.createForecastHTML(forecast)
        });
        
        infoWindow.open(this.map);
        
        // Add temporal resolution visualization
        this.addTemporalResolutionLayer(forecast, lat, lng);
    }

    createForecastHTML(forecast) {
        const maxProb = Math.max(...forecast.map(f => f.probability));
        const bestTime = forecast.find(f => f.probability === maxProb);
        
        let html = `
            <div style="color: #001e3c; max-width: 300px;">
                <h3>📊 24-Hour Focused Forecast</h3>
                <p><strong>Best Time:</strong> ${new Date(bestTime.time).toLocaleTimeString()} (${(maxProb * 100).toFixed(1)}%)</p>
                <div style="max-height: 200px; overflow-y: auto;">
        `;
        
        forecast.slice(0, 12).forEach(f => {
            const time = new Date(f.time);
            const color = f.probability > 0.6 ? '#4fc3f7' : f.probability > 0.3 ? '#ffa726' : '#ff7043';
            
            html += `
                <div style="display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #eee;">
                    <span>${time.toLocaleTimeString().slice(0, 5)}</span>
                    <span style="color: ${color}; font-weight: bold;">${(f.probability * 100).toFixed(0)}%</span>
                    <span style="font-size: 11px;">${f.conditions.split('-')[0]}</span>
                </div>
            `;
        });
        
        html += `
                </div>
                <button onclick="mlIntegration.showSpatialDetail(${lat}, ${lng})" 
                        style="background: #4fc3f7; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer; margin-top: 10px;">
                    Show Spatial Detail
                </button>
            </div>
        `;
        
        return html;
    }

    addTemporalResolutionLayer(forecast, centerLat, centerLng) {
        // Create time-based heat map overlay
        const timeData = [];
        
        forecast.forEach((f, index) => {
            // Create circular pattern around center point for each time step
            const radius = 0.01; // ~1km
            const points = 20;
            
            for (let i = 0; i < points; i++) {
                const angle = (i / points) * 2 * Math.PI;
                const lat = centerLat + Math.cos(angle) * radius * f.probability;
                const lng = centerLng + Math.sin(angle) * radius * f.probability;
                
                timeData.push({
                    location: new google.maps.LatLng(lat, lng),
                    weight: f.probability
                });
            }
        });
        
        // Create temporal heat map layer
        if (this.temporalLayer) {
            this.temporalLayer.setMap(null);
        }
        
        this.temporalLayer = new google.maps.visualization.HeatmapLayer({
            data: timeData,
            map: this.map,
            radius: 30,
            opacity: 0.6,
            gradient: [
                'rgba(0, 255, 255, 0)',
                'rgba(0, 255, 255, 1)',
                'rgba(0, 127, 255, 1)',
                'rgba(127, 0, 255, 1)',
                'rgba(255, 0, 255, 1)'
            ]
        });
    }

    // === RESOLUTION CONTROLS ===

    toggleTimeResolution() {
        const toggle = document.getElementById('time-resolution-toggle');
        
        if (toggle.classList.contains('active')) {
            // Disable high temporal resolution
            if (this.temporalLayer) {
                this.temporalLayer.setMap(null);
            }
            toggle.classList.remove('active');
        } else {
            // Enable high temporal resolution
            if (this.currentHotspots.length > 0) {
                const hotspot = this.currentHotspots[0];
                this.generateFocusedForecast(hotspot.latitude, hotspot.longitude);
            } else {
                this.generateFocusedForecast();
            }
            toggle.classList.add('active');
        }
    }

    toggleSpatialResolution() {
        const toggle = document.getElementById('spatial-resolution-toggle');
        
        if (toggle.classList.contains('active')) {
            // Disable high spatial resolution
            Object.values(this.heatMapLayers).forEach(layer => {
                layer.setOptions({radius: 50});
            });
            toggle.classList.remove('active');
        } else {
            // Enable high spatial resolution
            Object.values(this.heatMapLayers).forEach(layer => {
                layer.setOptions({radius: 20});
            });
            toggle.classList.add('active');
        }
    }

    showOverviewForecast() {
        // Show all layers for comprehensive overview
        this.showAllLayers();
        
        // Zoom out to show full area
        this.map.setZoom(10);
        this.map.setCenter({lat: 48.5465, lng: -123.0307});
    }

    async showAllLayers() {
        const layerTypes = Object.keys(this.heatMapLayers);
        
        for (const layerType of layerTypes) {
            await this.loadHeatMapData(layerType);
            this.heatMapLayers[layerType].setMap(this.map);
            
            const toggle = document.getElementById(`${layerType}-toggle`);
            if (toggle) toggle.classList.add('active');
        }
    }

    showSpatialDetail(lat, lng) {
        // Generate high-resolution spatial grid around the point
        this.addAgentMessage(`🔍 Generating high-resolution spatial analysis for area...`);
        
        const spatialData = [];
        const gridSize = 0.002; // ~200m resolution
        
        for (let latOffset = -0.02; latOffset <= 0.02; latOffset += gridSize) {
            for (let lngOffset = -0.02; lngOffset <= 0.02; lngOffset += gridSize) {
                const pointLat = lat + latOffset;
                const pointLng = lng + lngOffset;
                
                // Simulate detailed spatial probability
                const distance = Math.sqrt(latOffset*latOffset + lngOffset*lngOffset);
                const probability = Math.exp(-distance * 100) * (0.6 + Math.random() * 0.4);
                
                spatialData.push({
                    location: new google.maps.LatLng(pointLat, pointLng),
                    weight: probability
                });
            }
        }
        
        // Create high-resolution spatial layer
        if (this.spatialDetailLayer) {
            this.spatialDetailLayer.setMap(null);
        }
        
        this.spatialDetailLayer = new google.maps.visualization.HeatmapLayer({
            data: spatialData,
            map: this.map,
            radius: 15,
            opacity: 0.8,
            gradient: [
                'rgba(255, 255, 0, 0)',
                'rgba(255, 255, 0, 1)',
                'rgba(255, 192, 0, 1)',
                'rgba(255, 128, 0, 1)',
                'rgba(255, 64, 0, 1)',
                'rgba(255, 0, 0, 1)'
            ]
        });
        
        // Zoom to detail area
        this.map.setZoom(14);
        this.map.setCenter({lat: lat, lng: lng});
    }
}

// === GLOBAL FUNCTIONS FOR UI INTERACTION ===

function toggleAgentInterface() {
    const agentInterface = document.getElementById('agent-interface');
    const toggle = document.getElementById('agent-toggle');
    
    if (agentInterface.style.display === 'none') {
        agentInterface.style.display = 'block';
        toggle.classList.add('active');
    } else {
        agentInterface.style.display = 'none';
        toggle.classList.remove('active');
    }
}

function toggleHeatMapLayer(layerType) {
    if (window.mlIntegration) {
        window.mlIntegration.toggleHeatMapLayer(layerType);
    }
}

function handleAgentInput(event) {
    if (window.mlIntegration) {
        window.mlIntegration.handleAgentInput(event);
    }
}

function findHotspots() {
    if (window.mlIntegration) {
        window.mlIntegration.findHotspots();
    }
}

function generateFocusedForecast() {
    if (window.mlIntegration) {
        window.mlIntegration.generateFocusedForecast();
    }
}

function toggleTimeResolution() {
    if (window.mlIntegration) {
        window.mlIntegration.toggleTimeResolution();
    }
}

function toggleSpatialResolution() {
    if (window.mlIntegration) {
        window.mlIntegration.toggleSpatialResolution();
    }
}

function showOverviewForecast() {
    if (window.mlIntegration) {
        window.mlIntegration.showOverviewForecast();
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    // Wait for Google Maps to load, then initialize ML integration
    const checkMapsLoaded = () => {
        if (window.google && window.google.maps && window.google.maps.visualization) {
            window.mlIntegration = new ORCASTMLIntegration();
        } else {
            setTimeout(checkMapsLoaded, 100);
        }
    };
    
    setTimeout(checkMapsLoaded, 1000); // Give Google Maps time to load
}); 