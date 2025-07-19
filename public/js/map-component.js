// ORCAST Map Component
// Handles Google Maps integration, heatmap rendering, and interactive markers

class ORCASTMap {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.map = null;
        this.heatmapLayer = null;
        this.markers = [];
        this.center = options.center || { lat: 48.5465, lng: -123.0307 };
        this.zoom = options.zoom || 11;
        
        // State
        this.currentTimeUnit = 'months';
        this.currentPeriodOffset = 0;
        this.currentThreshold = 50;
        this.currentTimePeriod = 720; // 1 month in hours
    }

    async initialize() {
        console.log('Initializing ORCAST map with real data...');
        
        this.map = new google.maps.Map(document.getElementById(this.containerId), {
            zoom: this.zoom,
            center: this.center,
            mapTypeId: 'satellite',
            styles: [
                {
                    featureType: 'water',
                    elementType: 'geometry',
                    stylers: [{ color: '#263D5B' }]
                }
            ]
        });

        // Load real data files
        await Promise.all([
            window.dataLoader.loadRealSightingsData(),
            window.dataLoader.loadRealProbabilityData(),
            window.dataLoader.loadRealEnvironmentalData()
        ]);

        // Initialize heatmap and markers with real data
        this.updateHeatmapData();
        this.setupEventListeners();
    }

    updateHeatmapData() {
        console.log(`updateHeatmapData called - ${this.currentTimeUnit}, offset: ${this.currentPeriodOffset}, threshold: ${this.currentThreshold}%`);
        
        // Check if Google Maps is ready
        if (!google || !google.maps || !google.maps.visualization) {
            console.error('Google Maps visualization library not loaded yet');
            setTimeout(() => this.updateHeatmapData(), 1000);
            return;
        }
        
        console.log('Google Maps ready, filtering real sightings data...');
        
        try {
            // Use real sightings data filtered by time and threshold
            const filteredData = window.dataLoader.filterRealSightingsData(
                this.currentTimeUnit, 
                this.currentPeriodOffset, 
                this.currentThreshold
            );

            console.log(`Filtered ${filteredData.length} real sightings above ${this.currentThreshold}% confidence threshold`);

            // Create weighted heatmap points
            const heatmapData = [];
            filteredData.forEach(point => {
                heatmapData.push({
                    location: new google.maps.LatLng(point.lat, point.lng),
                    weight: point.probability / 100
                });
            });

            // Remove existing heatmap
            if (this.heatmapLayer) {
                this.heatmapLayer.setMap(null);
            }

            // Create new heatmap layer
            this.heatmapLayer = new google.maps.visualization.HeatmapLayer({
                data: heatmapData,
                map: this.map,
                radius: 40,
                opacity: 0.8,
                gradient: [
                    'rgba(0, 255, 128, 0)',
                    'rgba(0, 255, 128, 1)',
                    'rgba(128, 255, 0, 1)',
                    'rgba(255, 255, 0, 1)',
                    'rgba(255, 128, 0, 1)',
                    'rgba(255, 0, 0, 1)'
                ]
            });

            // Add interactive markers with hover info
            this.addInteractiveMarkers(filteredData);
        } catch (error) {
            console.error('Error updating heatmap data:', error);
            setTimeout(() => this.updateHeatmapData(), 1000);
        }
    }

    addInteractiveMarkers(data) {
        // Clear existing markers
        this.markers.forEach(marker => marker.setMap(null));
        this.markers = [];

        data.forEach(point => {
            const marker = new google.maps.Marker({
                position: { lat: point.lat, lng: point.lng },
                map: this.map,
                title: point.location,
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 8,
                    fillColor: point.probability > 70 ? '#FF0000' : point.probability > 50 ? '#FF8000' : '#00FF80',
                    fillOpacity: 0.8,
                    strokeColor: '#ffffff',
                    strokeWeight: 2
                }
            });

            // Add hover listeners
            marker.addListener('mouseover', (e) => {
                this.showTooltip(e, point);
            });

            marker.addListener('mouseout', () => {
                this.hideTooltip();
            });

            this.markers.push(marker);
        });
    }

    showTooltip(event, data) {
        const tooltip = document.getElementById('infoTooltip');
        document.getElementById('tooltipTitle').textContent = data.location;
        document.getElementById('tooltipProbability').textContent = `Probability: ${data.probability}%`;
        document.getElementById('tooltipLastSeen').textContent = `Last seen: ${data.lastSeen}`;
        document.getElementById('tooltipDepth').textContent = `Avg depth: ${data.depth}m`;
        document.getElementById('tooltipPodSize').textContent = `Typical pod size: ${data.podSize}`;
        
        tooltip.style.display = 'block';
        tooltip.style.left = (event.domEvent.clientX + 10) + 'px';
        tooltip.style.top = (event.domEvent.clientY - 10) + 'px';
    }

    hideTooltip() {
        document.getElementById('infoTooltip').style.display = 'none';
    }

    setupEventListeners() {
        // Period slider
        document.getElementById('timeSlider').addEventListener('input', (e) => {
            this.currentPeriodOffset = parseInt(e.target.value);
            this.updatePeriodDisplay();
            this.updateHeatmapData();
        });

        // Threshold slider
        document.getElementById('thresholdSlider').addEventListener('input', (e) => {
            this.currentThreshold = parseInt(e.target.value);
            this.updateThresholdDisplay();
            this.updateHeatmapData();
        });
    }

    setTimeUnit(unit) {
        this.currentTimeUnit = unit;
        this.currentPeriodOffset = 0; // Reset to current period
        
        // Update slider range based on unit
        const slider = document.getElementById('timeSlider');
        
        if (unit === 'weeks') {
            slider.min = -24;
            slider.max = 4;
            this.currentTimePeriod = 168; // 1 week in hours
        } else if (unit === 'months') {
            slider.min = -12;
            slider.max = 2;
            this.currentTimePeriod = 720; // 1 month in hours
        } else if (unit === 'years') {
            slider.min = -5;
            slider.max = 1;
            this.currentTimePeriod = 8760; // 1 year in hours
        }
        
        slider.value = this.currentPeriodOffset;
        this.updatePeriodDisplay();
        this.updateHeatmapData();
    }

    updateThresholdDisplay() {
        let display = "";
        if (this.currentThreshold < 25) display = "Very Low";
        else if (this.currentThreshold < 50) display = "Low";
        else if (this.currentThreshold < 75) display = "Medium";
        else display = "High";
        document.getElementById('thresholdValue').textContent = display;
    }

    updatePeriodDisplay() {
        // Implementation for updating period display
        // This would update the UI to show current time period
    }

    navigateRelative(offset) {
        const slider = document.getElementById('timeSlider');
        const min = parseInt(slider.min);
        const max = parseInt(slider.max);
        
        this.currentPeriodOffset = Math.max(min, Math.min(max, offset));
        slider.value = this.currentPeriodOffset;
        this.updatePeriodDisplay();
        this.updateHeatmapData();
    }

    updateThreshold(value) {
        this.currentThreshold = parseInt(value);
        this.updateThresholdDisplay();
        this.updateHeatmapData();
    }
}

// Export for use
window.ORCASTMap = ORCASTMap; 