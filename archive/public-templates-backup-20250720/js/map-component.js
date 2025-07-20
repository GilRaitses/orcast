// ORCAST Map Component
// Handles Google Maps integration, heatmap rendering, and probability-colored markers for past, present, and future (multi-layer)

class ORCASTMap {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.map = null;
        this.center = options.center || { lat: 48.5465, lng: -123.0307 };
        this.zoom = options.zoom || 11;
        // State
        this.currentTimeUnit = 'months';
        this.currentThreshold = 50;
        this.showPast = true;
        this.showPresent = false;
        this.showFuture = false;
        this.pastPeriodOffset = 0;
        this.futurePeriodOffset = 1;
        // Marker and heatmap arrays
        this.pastMarkers = [];
        this.presentMarkers = [];
        this.futureMarkers = [];
        this.pastHeatmapLayer = null;
        this.presentHeatmapLayer = null;
        this.futureHeatmapLayer = null;
    }

    async initialize() {
        this.map = new google.maps.Map(document.getElementById(this.containerId), {
            zoom: this.zoom,
            center: this.center,
            mapTypeId: 'hybrid', // Changed from 'satellite' for better balance
            restriction: {
                latLngBounds: {
                    north: 48.8,
                    south: 48.3,
                    east: -122.7,
                    west: -123.4
                },
                strictBounds: false
            },
            styles: [
                // Hide all points of interest and business labels
                {
                    featureType: 'poi',
                    stylers: [{ visibility: 'off' }]
                },
                {
                    featureType: 'poi.business',
                    stylers: [{ visibility: 'off' }]
                },
                {
                    featureType: 'poi.park',
                    stylers: [{ visibility: 'simplified' }]
                },
                // Clean up road labeling
                {
                    featureType: 'road',
                    elementType: 'labels',
                    stylers: [{ visibility: 'off' }]
                },
                {
                    featureType: 'road.highway',
                    elementType: 'labels',
                    stylers: [{ visibility: 'simplified' }]
                },
                // Hide transit stations and other clutter
                {
                    featureType: 'transit',
                    stylers: [{ visibility: 'off' }]
                },
                // Simplify administrative labels
                {
                    featureType: 'administrative.locality',
                    elementType: 'labels.text',
                    stylers: [{ visibility: 'simplified' }]
                },
                {
                    featureType: 'administrative.land_parcel',
                    stylers: [{ visibility: 'off' }]
                },
                // Style water areas
                {
                    featureType: 'water',
                    elementType: 'geometry',
                    stylers: [{ color: '#193E5C' }]
                },
                {
                    featureType: 'water',
                    elementType: 'labels.text',
                    stylers: [{ 
                        color: '#ffffff',
                        fontSize: '12px',
                        fontWeight: 'normal'
                    }]
                },
                // Style landscape/islands
                {
                    featureType: 'landscape',
                    elementType: 'geometry',
                    stylers: [{ color: '#2D5A27' }]
                },
                {
                    featureType: 'landscape.natural',
                    elementType: 'geometry',
                    stylers: [{ color: '#2D5A27' }]
                },
                // Keep only major place names visible
                {
                    featureType: 'administrative.country',
                    elementType: 'labels.text',
                    stylers: [{ visibility: 'simplified' }]
                },
                {
                    featureType: 'administrative.province',
                    elementType: 'labels.text',
                    stylers: [{ visibility: 'simplified' }]
                }
            ]
        });
        await Promise.all([
            window.dataLoader.loadRealSightingsData(),
            window.dataLoader.loadRealProbabilityData(),
            window.dataLoader.loadRealEnvironmentalData()
        ]);
        this.setupLayerToggles();
        this.updateLayers();
    }

    getProbabilityColor(prob) {
        if (prob >= 80) return '#FF0000';      // Very High
        if (prob >= 60) return '#FF8000';      // High
        if (prob >= 40) return '#FFFF00';      // Medium
        if (prob >= 20) return '#00FF80';      // Low
        return '#0078FF';                      // Very Low
    }

    clearMarkers(markerArray) {
        markerArray.forEach(marker => marker.setMap(null));
        markerArray.length = 0;
    }
    clearHeatmap(heatmapLayer) {
        if (heatmapLayer) heatmapLayer.setMap(null);
    }

    setupLayerToggles() {
        document.getElementById('togglePastBtn').addEventListener('click', () => {
            this.showPast = !this.showPast;
            document.getElementById('togglePastBtn').classList.toggle('active', this.showPast);
            document.getElementById('pastSliderWrapper').style.display = this.showPast ? 'block' : 'none';
            this.ensureAtLeastOneLayer();
            this.updateLayers();
        });
        document.getElementById('togglePresentBtn').addEventListener('click', () => {
            this.showPresent = !this.showPresent;
            document.getElementById('togglePresentBtn').classList.toggle('active', this.showPresent);
            this.ensureAtLeastOneLayer();
            this.updateLayers();
        });
        document.getElementById('toggleFutureBtn').addEventListener('click', () => {
            this.showFuture = !this.showFuture;
            document.getElementById('toggleFutureBtn').classList.toggle('active', this.showFuture);
            document.getElementById('futureSliderWrapper').style.display = this.showFuture ? 'block' : 'none';
            this.ensureAtLeastOneLayer();
            this.updateLayers();
        });
        document.getElementById('pastSlider').addEventListener('input', (e) => {
            this.pastPeriodOffset = parseInt(e.target.value);
            this.updatePastPeriodDisplay();
            this.updateLayers();
        });
        document.getElementById('futureSlider').addEventListener('input', (e) => {
            this.futurePeriodOffset = parseInt(e.target.value);
            this.updateFuturePeriodDisplay();
            this.updateLayers();
        });
        document.getElementById('pastSliderWrapper').style.display = this.showPast ? 'block' : 'none';
        document.getElementById('futureSliderWrapper').style.display = this.showFuture ? 'block' : 'none';
        this.updatePastPeriodDisplay();
        this.updateFuturePeriodDisplay();
        this.updateLayers();
    }

    ensureAtLeastOneLayer() {
        if (!this.showPast && !this.showPresent && !this.showFuture) {
            this.showPresent = true;
            document.getElementById('togglePresentBtn').classList.add('active');
        }
    }

    updatePastPeriodDisplay() {
        const display = document.getElementById('pastPeriodDisplay');
        if (this.pastPeriodOffset === 0) {
            display.textContent = `Current ${this.currentTimeUnit.charAt(0).toUpperCase() + this.currentTimeUnit.slice(1, -1)}`;
        } else {
            display.textContent = `${Math.abs(this.pastPeriodOffset)} ${this.currentTimeUnit} ago`;
        }
    }
    updateFuturePeriodDisplay() {
        const display = document.getElementById('futurePeriodDisplay');
        display.textContent = `${this.futurePeriodOffset} ${this.currentTimeUnit} ahead`;
    }

    updateLayers() {
        // Remove existing markers and heatmaps
        this.clearMarkers(this.pastMarkers);
        this.clearMarkers(this.presentMarkers);
        this.clearMarkers(this.futureMarkers);
        this.clearHeatmap(this.pastHeatmapLayer);
        this.clearHeatmap(this.presentHeatmapLayer);
        this.clearHeatmap(this.futureHeatmapLayer);
        this.pastHeatmapLayer = null;
        this.presentHeatmapLayer = null;
        this.futureHeatmapLayer = null;

        // Past Layer (heatmap + markers)
        if (this.showPast) {
            const filteredPast = window.dataLoader.filterRealSightingsData(
                this.currentTimeUnit,
                this.pastPeriodOffset,
                this.currentThreshold
            );
            // Heatmap
            const heatmapData = filteredPast.map(point => ({
                location: new google.maps.LatLng(point.lat, point.lng),
                weight: point.probability / 100
            }));
            this.pastHeatmapLayer = new google.maps.visualization.HeatmapLayer({
                data: heatmapData,
                map: this.map,
                radius: 40,
                opacity: 0.5,
                gradient: [
                    'rgba(0, 255, 128, 0)',
                    'rgba(0, 255, 128, 1)',
                    'rgba(128, 255, 0, 1)',
                    'rgba(255, 255, 0, 1)',
                    'rgba(255, 128, 0, 1)',
                    'rgba(255, 0, 0, 1)'
                ]
            });
            // Markers (probability color)
            filteredPast.forEach(point => {
                const marker = new google.maps.Marker({
                    position: { lat: point.lat, lng: point.lng },
                    map: this.map,
                    title: point.location,
                    icon: {
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 5,
                        fillColor: this.getProbabilityColor(point.probability),
                        fillOpacity: 0.9,
                        strokeColor: '#000000',
                        strokeWeight: 2
                    }
                });
                this.pastMarkers.push(marker);
            });
        }
        // Future Layer (heatmap only)
        if (this.showFuture) {
            const filteredFuture = window.dataLoader.filterPredictionData(
                this.currentTimeUnit,
                this.futurePeriodOffset,
                this.currentThreshold
            );
            // Heatmap only
            const heatmapData = filteredFuture.map(point => ({
                location: new google.maps.LatLng(point.lat, point.lng),
                weight: point.probability / 100
            }));
            this.futureHeatmapLayer = new google.maps.visualization.HeatmapLayer({
                data: heatmapData,
                map: this.map,
                radius: 40,
                opacity: 0.5,
                gradient: [
                    'rgba(0, 128, 255, 0)',
                    'rgba(0, 128, 255, 1)',
                    'rgba(0, 255, 255, 1)',
                    'rgba(0, 255, 128, 1)',
                    'rgba(0, 255, 0, 1)',
                    'rgba(255, 255, 0, 1)'
                ]
            });
        }
        // Present Layer (heatmap + markers)
        if (this.showPresent) {
            const filteredPresent = window.dataLoader.filterCurrentData(this.currentTimeUnit);
            // Heatmap
            const heatmapData = filteredPresent.map(point => ({
                location: new google.maps.LatLng(point.lat, point.lng),
                weight: point.probability / 100
            }));
            this.presentHeatmapLayer = new google.maps.visualization.HeatmapLayer({
                data: heatmapData,
                map: this.map,
                radius: 40,
                opacity: 0.5,
                gradient: [
                    'rgba(255, 255, 255, 0)',
                    'rgba(255, 255, 255, 1)',
                    'rgba(0, 255, 255, 1)',
                    'rgba(0, 255, 128, 1)',
                    'rgba(0, 255, 0, 1)',
                    'rgba(255, 255, 0, 1)'
                ]
            });
            // Markers (probability color)
            filteredPresent.forEach(point => {
                const marker = new google.maps.Marker({
                    position: { lat: point.lat, lng: point.lng },
                    map: this.map,
                    title: point.location,
                    icon: {
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 5,
                        fillColor: this.getProbabilityColor(point.probability),
                        fillOpacity: 0.9,
                        strokeColor: '#000000',
                        strokeWeight: 2
                    }
                });
                this.presentMarkers.push(marker);
            });
        }
    }

    setTimeUnit(unit) {
        this.currentTimeUnit = unit;
        // Update button highlighting
        document.getElementById('weeksBtn').classList.toggle('active', unit === 'weeks');
        document.getElementById('monthsBtn').classList.toggle('active', unit === 'months');
        document.getElementById('yearsBtn').classList.toggle('active', unit === 'years');
        // Reset period offsets to default for new unit
        this.pastPeriodOffset = 0;
        this.futurePeriodOffset = 1;
        document.getElementById('pastSlider').value = 0;
        document.getElementById('futureSlider').value = 1;
        this.updatePastPeriodDisplay();
        this.updateFuturePeriodDisplay();
        this.updateLayers();
    }
}

// Export for use
window.ORCASTMap = ORCASTMap; 