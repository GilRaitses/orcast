// OrCast Feeding Zone Visualization UI
// Interactive ecosystem dynamics interface with temporal analysis

class FeedingZoneVisualizationUI {
    constructor() {
        this.currentYear = new Date().getFullYear();
        this.selectedYear = this.currentYear;
        this.selectedSpecies = 'chinook_salmon';
        this.visualizationMode = 'zones'; // 'zones', 'bathymetry', 'food_density', 'temporal'
        this.isVisible = false;
        this.animationSpeed = 1000; // ms between frames
        this.isAnimating = false;
        
        this.initializeUI();
    }
    
    initializeUI() {
        this.createFeedingZonePanel();
        this.setupEventListeners();
        this.loadFeedingZoneCSS();
    }
    
    loadFeedingZoneCSS() {
        // Load feeding zone CSS if not already loaded
        if (!document.querySelector('link[href="feeding_zone_ui.css"]')) {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = 'feeding_zone_ui.css';
            document.head.appendChild(link);
        }
    }
    
    createFeedingZonePanel() {
        const panelHTML = `
            <div id="feedingZonePanel" class="feeding-zone-panel" style="display: none;">
                <!-- Panel Header -->
                <div class="feeding-zone-header">
                    <div class="feeding-zone-icon">ORCA</div>
                    <div class="feeding-zone-title">
                        <h3>Orca Feeding Zone Dynamics</h3>
                        <div class="feeding-zone-subtitle">Marine ecosystem visualization and temporal analysis</div>
                    </div>
                    <div class="feeding-zone-controls">
                        <button onclick="feedingZoneUI.toggleFullscreen()" class="zone-btn-small">⛶</button>
                        <button onclick="feedingZoneUI.hide()" class="zone-btn-small">✖️</button>
                    </div>
                </div>
                
                <!-- Visualization Mode Selector -->
                <div class="visualization-mode-selector">
                    <button onclick="feedingZoneUI.setMode('zones')" class="zone-btn ${this.currentMode === 'zones' ? 'active' : ''}">
                        TARGET Feeding Zones
                    </button>
                    <button onclick="feedingZoneUI.setMode('bathymetry')" class="zone-btn ${this.currentMode === 'bathymetry' ? 'active' : ''}">
                        DEPTH Bathymetry
                    </button>
                    <button onclick="feedingZoneUI.setMode('food')" class="zone-btn ${this.currentMode === 'food' ? 'active' : ''}">
                        FOOD Food Density
                    </button>
                    <button onclick="feedingZoneUI.setMode('temporal')" class="zone-btn ${this.currentMode === 'temporal' ? 'active' : ''}">
                        CHART Temporal Analysis
                    </button>
                    <button onclick="feedingZoneUI.resetToPresent()" class="zone-btn-small">RESET</button>
                </div>
                
                <!-- Time Control Section -->
                <div class="time-control-section">
                    <div class="time-control-header">
                        <h4>Time Navigation</h4>
                        <div class="selected-year-display">
                            <span class="year-label">Year:</span>
                            <span class="year-value" id="selectedYearDisplay">${this.currentYear}</span>
                        </div>
                    </div>
                    
                    <div class="time-slider-container">
                        <div class="time-slider-labels">
                            <span class="time-label">2010</span>
                            <span class="time-label">Historical</span>
                            <span class="time-label">Present</span>
                            <span class="time-label">2030</span>
                        </div>
                        
                        <input type="range" 
                               id="timeSlider" 
                               class="time-slider"
                               min="2010" 
                               max="2030" 
                               value="${this.currentYear}"
                               onchange="feedingZoneUI.updateYear(this.value)"
                               oninput="feedingZoneUI.previewYear(this.value)">
                        
                        <div class="time-slider-markers">
                            <div class="time-marker historical" style="left: 0%;"></div>
                            <div class="time-marker present" style="left: 70%;"></div>
                            <div class="time-marker future" style="left: 100%;"></div>
                        </div>
                    </div>
                    
                    <div class="time-controls">
                        <button onclick="feedingZoneUI.previousYear()" class="zone-btn-small">◀️</button>
                        <button onclick="feedingZoneUI.playAnimation()" class="zone-btn-small" id="playButton">▶️</button>
                        <button onclick="feedingZoneUI.nextYear()" class="zone-btn-small">▶️</button>
                        <button onclick="feedingZoneUI.resetToPresent()" class="zone-btn-small">🔄</button>
                    </div>
                </div>
                
                <!-- Species Selector (for food density mode) -->
                <div class="species-selector" id="speciesSelector" style="display: none;">
                    <h4>Prey Species</h4>
                    <div class="species-buttons">
                        <button class="species-btn active" data-species="chinook_salmon" onclick="feedingZoneUI.setSpecies('chinook_salmon')">
                            FISH Chinook Salmon
                        </button>
                        <button class="species-btn" data-species="coho_salmon" onclick="feedingZoneUI.setSpecies('coho_salmon')">
                            FISH Coho Salmon  
                        </button>
                        <button class="species-btn" data-species="pacific_herring" onclick="feedingZoneUI.setSpecies('pacific_herring')">
                            FISH Pacific Herring
                        </button>
                    </div>
                </div>
                
                <!-- Main Visualization Container -->
                <div class="visualization-container" id="visualizationContainer">
                    <!-- Loading State -->
                    <div id="feedingZoneLoading" class="feeding-zone-loading">
                        <div class="loading-spinner-large"></div>
                        <div>Loading ecosystem data...</div>
                    </div>
                    
                    <!-- Visualization Content -->
                    <div id="feedingZoneContent" class="feeding-zone-content">
                        <!-- Map container -->
                        <div id="feedingZoneMap" class="feeding-zone-map">
                            <!-- Map will be populated by visualization engine -->
                        </div>
                        
                        <!-- Data overlay -->
                        <div id="dataOverlay" class="data-overlay">
                            <!-- Dynamic content based on mode -->
                        </div>
                    </div>
                </div>
                
                <!-- Information Panel -->
                <div class="info-panel" id="infoPanel">
                    <div class="info-header">
                        <h4 id="infoPanelTitle">Feeding Zone Information</h4>
                    </div>
                    <div class="info-content" id="infoPanelContent">
                        <!-- Dynamic content populated by JavaScript -->
                    </div>
                </div>
                
                <!-- Legend -->
                <div class="visualization-legend" id="visualizationLegend">
                    <!-- Dynamic legend content -->
                </div>
                
                <!-- Temporal Analysis Chart (shown in temporal mode) -->
                <div class="temporal-analysis-chart" id="temporalAnalysisChart" style="display: none;">
                    <canvas id="temporalChart" width="800" height="400"></canvas>
                </div>
                
                <!-- Forecast Disclaimer -->
                <div class="forecast-disclaimer" id="forecastDisclaimer" style="display: none;">
                    <div class="disclaimer-icon">WARNING</div>
                    <div class="disclaimer-content">
                        <strong>Forecast Disclaimer:</strong>
                        <p>Future projections (2025-2030) are scenario-based estimates, not predictions. Marine ecosystems are complex and may not follow historical patterns. Climate change could cause unprecedented ecosystem changes.</p>
                    </div>
                </div>
                
                <!-- Data Quality Indicator -->
                <div class="data-quality-indicator" id="dataQualityIndicator">
                    <div class="quality-icon">DATA</div>
                    <div class="quality-text">
                        <span class="quality-label">Data Quality:</span>
                        <span class="quality-value" id="dataQualityValue">High</span>
                    </div>
                </div>
                
                <!-- Food Density Legend (shown in food mode) -->
                <div class="food-density-legend" id="foodDensityLegend" style="display: none;">
                    <div class="legend-title">Food Density by Species</div>
                    <div class="legend-items">
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #ff4444;"></div>
                            FISH Chinook Salmon
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #44ff44;"></div>
                            FISH Coho Salmon
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #4444ff;"></div>
                            FISH Pacific Herring
                        </div>
                    </div>
                </div>
                
                <button onclick="feedingZoneUI.resetToPresent()" class="zone-btn-small">RESET</button>
            </div>
        `;
        
        // Add to controls panel or create new section
        const controlsPanel = document.querySelector('.controls-panel');
        if (controlsPanel) {
            controlsPanel.insertAdjacentHTML('beforeend', panelHTML);
        } else {
            document.body.insertAdjacentHTML('beforeend', panelHTML);
        }
    }
    
    setupEventListeners() {
        // Add feeding zone toggle to transparency panel
        this.addFeedingZoneToggle();
        
        // Map interaction listeners
        this.setupMapListeners();
        
        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
    }
    
    addFeedingZoneToggle() {
        // Add feeding zone button to transparency panel
        const transparencyPanel = document.querySelector('#transparencyPanel');
        if (transparencyPanel) {
            const toggleButton = document.createElement('button');
            toggleButton.className = 'ai-btn';
            toggleButton.style.width = '100%';
            toggleButton.style.marginTop = '1rem';
            toggleButton.innerHTML = '🐋 Feeding Zone Dynamics';
            toggleButton.onclick = () => this.toggle();
            
            transparencyPanel.appendChild(toggleButton);
        }
    }
    
    setupMapListeners() {
        // Listen for map interactions to update feeding zone display
        if (window.map) {
            window.map.addListener('click', (e) => {
                this.handleMapClick(e.latLng.lat(), e.latLng.lng());
            });
            
            window.map.addListener('zoom_changed', () => {
                this.updateVisualizationForZoom();
            });
        }
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (!this.isVisible) return;
            
            switch (e.key) {
                case 'ArrowLeft':
                    e.preventDefault();
                    this.previousYear();
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    this.nextYear();
                    break;
                case ' ':
                    e.preventDefault();
                    this.playAnimation();
                    break;
                case 'r':
                    e.preventDefault();
                    this.resetToPresent();
                    break;
                case 'Escape':
                    e.preventDefault();
                    this.hide();
                    break;
            }
        });
    }
    
    // === MAIN CONTROL METHODS ===
    
    async show() {
        const panel = document.getElementById('feedingZonePanel');
        if (panel) {
            panel.style.display = 'block';
            this.isVisible = true;
            
            // Load initial visualization
            await this.updateVisualization();
        }
    }
    
    hide() {
        const panel = document.getElementById('feedingZonePanel');
        if (panel) {
            panel.style.display = 'none';
            this.isVisible = false;
            this.stopAnimation();
        }
    }
    
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }
    
    toggleFullscreen() {
        const panel = document.getElementById('feedingZonePanel');
        if (panel) {
            panel.classList.toggle('fullscreen');
            this.updateVisualizationForZoom();
        }
    }
    
    // === VISUALIZATION MODE METHODS ===
    
    setVisualizationMode(mode) {
        this.visualizationMode = mode;
        
        // Update active button
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-mode="${mode}"]`).classList.add('active');
        
        // Show/hide species selector for food density mode
        const speciesSelector = document.getElementById('speciesSelector');
        if (mode === 'food_density') {
            speciesSelector.style.display = 'block';
        } else {
            speciesSelector.style.display = 'none';
        }
        
        // Show/hide temporal chart
        const temporalChart = document.getElementById('temporalAnalysisChart');
        if (mode === 'temporal') {
            temporalChart.style.display = 'block';
        } else {
            temporalChart.style.display = 'none';
        }
        
        this.updateVisualization();
    }
    
    setSpecies(species) {
        this.selectedSpecies = species;
        
        // Update active species button
        document.querySelectorAll('.species-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-species="${species}"]`).classList.add('active');
        
        if (this.visualizationMode === 'food_density') {
            this.updateVisualization();
        }
    }
    
    // === TIME CONTROL METHODS ===
    
    updateYear(year) {
        this.selectedYear = parseInt(year);
        this.updateSelectedYearDisplay();
        this.updateDataQualityIndicator();
        this.updateForecastDisclaimer();
        this.updateVisualization();
    }
    
    previewYear(year) {
        // Show preview without full update (for slider dragging)
        document.getElementById('selectedYearDisplay').textContent = year;
        this.updateDataQualityIndicator();
        this.updateForecastDisclaimer();
    }
    
    previousYear() {
        if (this.selectedYear > 2010) {
            this.selectedYear--;
            this.updateTimeSlider();
            this.updateVisualization();
        }
    }
    
    nextYear() {
        if (this.selectedYear < 2030) {
            this.selectedYear++;
            this.updateTimeSlider();
            this.updateVisualization();
        }
    }
    
    resetToPresent() {
        this.selectedYear = this.currentYear;
        this.updateTimeSlider();
        this.updateVisualization();
    }
    
    updateTimeSlider() {
        const slider = document.getElementById('timeSlider');
        if (slider) {
            slider.value = this.selectedYear;
        }
        this.updateSelectedYearDisplay();
        this.updateDataQualityIndicator();
        this.updateForecastDisclaimer();
    }
    
    updateSelectedYearDisplay() {
        const display = document.getElementById('selectedYearDisplay');
        if (display) {
            display.textContent = this.selectedYear;
        }
    }
    
    updateDataQualityIndicator() {
        const indicator = document.getElementById('dataQualityValue');
        if (indicator) {
            const quality = window.feedingZoneDynamics.getDataQuality(this.selectedYear);
            indicator.textContent = quality;
            
            // Update color based on quality
            const qualityIndicator = document.getElementById('dataQualityIndicator');
            qualityIndicator.className = 'data-quality-indicator';
            
            if (quality.includes('High')) {
                qualityIndicator.classList.add('high-quality');
            } else if (quality.includes('Medium')) {
                qualityIndicator.classList.add('medium-quality');
            } else {
                qualityIndicator.classList.add('low-quality');
            }
        }
    }
    
    updateForecastDisclaimer() {
        const disclaimer = document.getElementById('forecastDisclaimer');
        if (disclaimer) {
            if (this.selectedYear > this.currentYear) {
                disclaimer.style.display = 'flex';
            } else {
                disclaimer.style.display = 'none';
            }
        }
    }
    
    // === ANIMATION METHODS ===
    
    playAnimation() {
        const playButton = document.getElementById('playButton');
        
        if (this.isAnimating) {
            this.stopAnimation();
            playButton.textContent = '▶️';
        } else {
            this.startAnimation();
            playButton.textContent = '⏸️';
        }
    }
    
    startAnimation() {
        this.isAnimating = true;
        this.animationInterval = setInterval(() => {
            if (this.selectedYear >= 2030) {
                this.selectedYear = 2010;
            } else {
                this.selectedYear++;
            }
            
            this.updateTimeSlider();
            this.updateVisualization();
        }, this.animationSpeed);
    }
    
    stopAnimation() {
        this.isAnimating = false;
        if (this.animationInterval) {
            clearInterval(this.animationInterval);
            this.animationInterval = null;
        }
    }
    
    // === VISUALIZATION UPDATE METHODS ===
    
    async updateVisualization() {
        if (!this.isVisible) return;
        
        this.showLoading();
        
        try {
            switch (this.visualizationMode) {
                case 'zones':
                    await this.renderFeedingZones();
                    break;
                case 'bathymetry':
                    await this.renderBathymetry();
                    break;
                case 'food_density':
                    await this.renderFoodDensity();
                    break;
                case 'temporal':
                    await this.renderTemporalAnalysis();
                    break;
            }
            
            this.hideLoading();
        } catch (error) {
            console.error('Error updating visualization:', error);
            this.showError('Failed to update visualization');
        }
    }
    
    async renderFeedingZones() {
        const snapshot = await window.feedingZoneDynamics.getFeedingZoneSnapshot(this.selectedYear);
        
        // Clear existing visualization
        const mapContainer = document.getElementById('feedingZoneMap');
        mapContainer.innerHTML = '';
        
        // Create feeding zone visualization
        const zones = snapshot.feeding_zones.zones;
        
        zones.forEach(zone => {
            const zoneElement = this.createFeedingZoneElement(zone);
            mapContainer.appendChild(zoneElement);
        });
        
        // Update legend
        this.updateLegend('feeding_zones');
        
        // Update info panel
        this.updateInfoPanel('feeding_zones', snapshot);
    }
    
    async renderBathymetry() {
        const bathymetry = await window.feedingZoneDynamics.generateBathymetryVisualization();
        
        // Clear existing visualization
        const mapContainer = document.getElementById('feedingZoneMap');
        mapContainer.innerHTML = '';
        
        // Create bathymetry visualization
        bathymetry.features.forEach(feature => {
            const featureElement = this.createBathymetryElement(feature);
            mapContainer.appendChild(featureElement);
        });
        
        // Update legend
        this.updateLegend('bathymetry', bathymetry.depth_legend);
        
        // Update info panel
        this.updateInfoPanel('bathymetry', bathymetry);
    }
    
    async renderFoodDensity() {
        const foodDensity = await window.feedingZoneDynamics.generateFoodDensityVisualization(
            this.selectedYear, 
            this.selectedSpecies
        );
        
        // Clear existing visualization
        const mapContainer = document.getElementById('feedingZoneMap');
        mapContainer.innerHTML = '';
        
        // Create food density heatmap
        foodDensity.density_zones.forEach(zone => {
            const densityElement = this.createFoodDensityElement(zone);
            mapContainer.appendChild(densityElement);
        });
        
        // Update legend
        this.updateLegend('food_density', foodDensity.species_info);
        
        // Update info panel
        this.updateInfoPanel('food_density', foodDensity);
    }
    
    async renderTemporalAnalysis() {
        const analysis = await window.feedingZoneDynamics.getTemporalAnalysis(2010, 2030);
        
        // Create temporal chart
        this.createTemporalChart(analysis);
        
        // Update info panel
        this.updateInfoPanel('temporal', analysis);
        
        // Update legend
        this.updateLegend('temporal');
    }
    
    // === ELEMENT CREATION METHODS ===
    
    createFeedingZoneElement(zone) {
        const element = document.createElement('div');
        element.className = 'feeding-zone-marker';
        element.style.cssText = `
            position: absolute;
            left: ${this.coordToPixel(zone.center.lng, 'x')}px;
            top: ${this.coordToPixel(zone.center.lat, 'y')}px;
            width: ${zone.radius * 20}px;
            height: ${zone.radius * 20}px;
            background-color: ${zone.visual_properties.color};
            opacity: ${zone.visual_properties.opacity};
            border: 2px ${zone.visual_properties.border_style} #ffffff;
            border-radius: 50%;
            transform: translate(-50%, -50%);
            cursor: pointer;
        `;
        
        // Add tooltip
        element.title = `${zone.name}\n${zone.tooltip_info.primary_prey}\n${zone.tooltip_info.success_rate} success rate`;
        
        // Add click handler
        element.onclick = () => this.selectFeedingZone(zone);
        
        return element;
    }
    
    createBathymetryElement(feature) {
        const element = document.createElement('div');
        element.className = 'bathymetry-marker';
        element.style.cssText = `
            position: absolute;
            left: ${this.coordToPixel(feature.location.lng, 'x')}px;
            top: ${this.coordToPixel(feature.location.lat, 'y')}px;
            width: ${feature.visual_properties.size}px;
            height: ${feature.visual_properties.size}px;
            background-color: ${feature.visual_properties.color};
            border-radius: 50%;
            transform: translate(-50%, -50%);
            cursor: pointer;
        `;
        
        // Add depth indicator
        const depthLabel = document.createElement('div');
        depthLabel.className = 'depth-label';
        depthLabel.textContent = `${feature.depth}m`;
        element.appendChild(depthLabel);
        
        // Add icon
        const icon = document.createElement('div');
        icon.className = 'feature-icon';
        icon.textContent = feature.visual_properties.icon;
        element.appendChild(icon);
        
        // Add tooltip
        element.title = `${feature.name}\n${feature.depth}m depth\n${feature.explanation}`;
        
        return element;
    }
    
    createFoodDensityElement(zone) {
        const element = document.createElement('div');
        element.className = 'food-density-zone';
        element.style.cssText = `
            position: absolute;
            left: ${this.coordToPixel(zone.zone_id, 'x')}px;
            top: ${this.coordToPixel(zone.zone_id, 'y')}px;
            width: 60px;
            height: 60px;
            background-color: ${zone.visual_properties.color};
            opacity: ${zone.visual_properties.opacity};
            border-radius: 50%;
            transform: translate(-50%, -50%);
            cursor: pointer;
        `;
        
        // Add density label
        const densityLabel = document.createElement('div');
        densityLabel.className = 'density-label';
        densityLabel.textContent = `${zone.current_density}`;
        element.appendChild(densityLabel);
        
        // Add tooltip
        element.title = `${zone.zone_name}\n${zone.current_density} ${zone.unit}\nConfidence: ${Math.round(zone.confidence * 100)}%`;
        
        return element;
    }
    
    // === UTILITY METHODS ===
    
    coordToPixel(coord, axis) {
        // Convert lat/lng to pixel coordinates
        // This is a simplified conversion - in production, use proper map projection
        const mapWidth = 800;
        const mapHeight = 600;
        
        if (axis === 'x') {
            // Longitude to X
            return ((coord + 123.5) / 1.0) * mapWidth;
        } else {
            // Latitude to Y
            return (1 - ((coord - 48.0) / 1.0)) * mapHeight;
        }
    }
    
    selectFeedingZone(zone) {
        // Handle feeding zone selection
        console.log('Selected feeding zone:', zone.name);
        
        // Update info panel with zone details
        this.updateInfoPanel('zone_details', zone);
        
        // Highlight selected zone
        document.querySelectorAll('.feeding-zone-marker').forEach(marker => {
            marker.classList.remove('selected');
        });
        event.target.classList.add('selected');
    }
    
    updateLegend(type, data = null) {
        const legend = document.getElementById('visualizationLegend');
        let legendHTML = '';
        
        switch (type) {
            case 'feeding_zones':
                legendHTML = this.createFeedingZoneLegend();
                break;
            case 'bathymetry':
                legendHTML = this.createBathymetryLegend(data);
                break;
            case 'food_density':
                legendHTML = this.createFoodDensityLegend(data);
                break;
            case 'temporal':
                legendHTML = this.createTemporalLegend();
                break;
        }
        
        legend.innerHTML = legendHTML;
    }
    
    createFeedingZoneLegend() {
        return `
            <div class="legend-title">Feeding Zone Productivity</div>
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #00FF00;"></div>
                    <span>High (80%+)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #FFFF00;"></div>
                    <span>Medium (60-80%)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #FFA500;"></div>
                    <span>Low (40-60%)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #FF0000;"></div>
                    <span>Very Low (<40%)</span>
                </div>
            </div>
        `;
    }
    
    createBathymetryLegend(depthLegend) {
        let legendHTML = '<div class="legend-title">Water Depth</div><div class="legend-items">';
        
        Object.entries(depthLegend).forEach(([depth, info]) => {
            legendHTML += `
                <div class="legend-item">
                    <div class="legend-color" style="background-color: ${info.color};"></div>
                    <span>${depth}: ${info.description}</span>
                </div>
            `;
        });
        
        legendHTML += '</div>';
        return legendHTML;
    }
    
    createFoodDensityLegend(speciesInfo) {
        return `
            <div class="legend-title">Food Density: ${speciesInfo.name}</div>
            <div class="legend-subtitle">${speciesInfo.orca_preference}</div>
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: rgb(255, 0, 0);"></div>
                    <span>High Density</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: rgb(255, 127, 127);"></div>
                    <span>Medium Density</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: rgb(127, 127, 255);"></div>
                    <span>Low Density</span>
                </div>
            </div>
        `;
    }
    
    updateInfoPanel(type, data) {
        const title = document.getElementById('infoPanelTitle');
        const content = document.getElementById('infoPanelContent');
        
        switch (type) {
            case 'feeding_zones':
                title.textContent = `Feeding Zones - ${this.selectedYear}`;
                content.innerHTML = this.createFeedingZoneInfo(data);
                break;
            case 'bathymetry':
                title.textContent = 'Bathymetry Features';
                content.innerHTML = this.createBathymetryInfo(data);
                break;
            case 'food_density':
                title.textContent = `Food Density - ${this.selectedYear}`;
                content.innerHTML = this.createFoodDensityInfo(data);
                break;
            case 'temporal':
                title.textContent = 'Temporal Analysis';
                content.innerHTML = this.createTemporalInfo(data);
                break;
        }
    }
    
    createFeedingZoneInfo(data) {
        const zones = data.feeding_zones.zones;
        let info = '<div class="zone-summary">';
        
        zones.forEach(zone => {
            info += `
                <div class="zone-info-item">
                    <h5>${zone.name}</h5>
                    <p><strong>Productivity:</strong> ${Math.round(zone.productivity * 100)}%</p>
                    <p><strong>Primary Prey:</strong> ${zone.tooltip_info.primary_prey}</p>
                    <p><strong>Peak Season:</strong> ${zone.tooltip_info.peak_season}</p>
                </div>
            `;
        });
        
        info += '</div>';
        return info;
    }
    
    showLoading() {
        document.getElementById('feedingZoneLoading').style.display = 'block';
        document.getElementById('feedingZoneContent').style.display = 'none';
    }
    
    hideLoading() {
        document.getElementById('feedingZoneLoading').style.display = 'none';
        document.getElementById('feedingZoneContent').style.display = 'block';
    }
    
    showError(message) {
        const container = document.getElementById('visualizationContainer');
        container.innerHTML = `
            <div class="error-message">
                <div class="error-icon">❌</div>
                <div class="error-text">${message}</div>
                <button onclick="feedingZoneUI.updateVisualization()" class="zone-btn">Try Again</button>
            </div>
        `;
    }
}

// Initialize feeding zone UI when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        if (window.feedingZoneDynamics) {
            window.feedingZoneUI = new FeedingZoneVisualizationUI();
        }
    }, 1500);
});

// Export for external use
window.FeedingZoneVisualizationUI = FeedingZoneVisualizationUI; 