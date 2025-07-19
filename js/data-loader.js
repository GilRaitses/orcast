// ORCAST Data Loader
// Handles loading and processing of real orca sighting and environmental data

class DataLoader {
    constructor() {
        this.realSightingsData = null;
        this.realProbabilityData = null;
        this.realEnvironmentalData = null;
    }

    async loadRealSightingsData() {
        try {
            const response = await fetch('/data/sample_user_sightings.json');
            const data = await response.json();
            this.realSightingsData = data.userSightings;
            console.log(`Loaded ${Object.keys(this.realSightingsData).length} real orca sightings`);
        } catch (error) {
            console.error('Failed to load real sightings data:', error);
        }
    }

    async loadRealProbabilityData() {
        try {
            const response = await fetch('/data/firebase_orca_probability_data.json');
            const data = await response.json();
            this.realProbabilityData = data;
            console.log('Loaded real probability grid data', data.metadata);
        } catch (error) {
            console.error('Failed to load real probability data:', error);
        }
    }

    async loadRealEnvironmentalData() {
        try {
            const response = await fetch('/data/environmental_data_20250717_002707.json');
            const data = await response.json();
            this.realEnvironmentalData = data;
            console.log('Loaded real environmental data from', data.lastUpdated);
        } catch (error) {
            console.error('Failed to load real environmental data:', error);
        }
    }

    filterRealSightingsData(currentTimeUnit, currentPeriodOffset, currentThreshold) {
        if (!this.realSightingsData) {
            console.warn('Real sightings data not loaded yet');
            return [];
        }

        const now = Date.now();
        let timeRangeMs;
        
        // Calculate time range based on current settings
        if (currentTimeUnit === 'weeks') {
            timeRangeMs = (7 * 24 * 60 * 60 * 1000) * (Math.abs(currentPeriodOffset) + 1);
        } else if (currentTimeUnit === 'months') {
            timeRangeMs = (30 * 24 * 60 * 60 * 1000) * (Math.abs(currentPeriodOffset) + 1);
        } else { // years
            timeRangeMs = (365 * 24 * 60 * 60 * 1000) * (Math.abs(currentPeriodOffset) + 1);
        }

        const cutoffTime = now - timeRangeMs;

        // Filter and convert real sightings
        const filteredSightings = [];
        Object.values(this.realSightingsData).forEach(sighting => {
            // Skip if too old for current time range
            if (sighting.timestamp < cutoffTime) return;
            
            // Calculate confidence-based probability
            let probability = 30; // base probability
            if (sighting.confidence === 'high') probability += 40;
            else if (sighting.confidence === 'medium') probability += 25;
            else if (sighting.confidence === 'low') probability += 10;
            
            if (sighting.verified) probability += 20;
            
            // Behavior-based probability boost
            if (sighting.behavior === 'foraging') probability += 15;
            else if (sighting.behavior === 'socializing') probability += 10;
            
            probability = Math.min(95, probability);
            
            // Skip if below threshold
            if (probability < currentThreshold) return;

            // Format time ago
            const hoursAgo = (now - sighting.timestamp) / (1000 * 60 * 60);
            let timeDisplay;
            if (hoursAgo < 48) {
                timeDisplay = `${Math.round(hoursAgo)} hours ago`;
            } else if (hoursAgo < 720) {
                timeDisplay = `${Math.round(hoursAgo / 24)} days ago`;
            } else {
                timeDisplay = `${Math.round(hoursAgo / 720)} months ago`;
            }

            filteredSightings.push({
                lat: sighting.location.lat,
                lng: sighting.location.lng,
                probability: probability,
                lastSeen: timeDisplay,
                depth: Math.round(Math.random() * 40 + 20), // Depth not in sighting data
                podSize: sighting.orcaCount,
                location: sighting.locationName,
                behavior: sighting.behavior,
                confidence: sighting.confidence,
                verified: sighting.verified,
                hoursAgo: hoursAgo
            });
        });

        return filteredSightings.sort((a, b) => b.probability - a.probability);
    }

    getEnvironmentalData() {
        return this.realEnvironmentalData;
    }

    getProbabilityGridData() {
        return this.realProbabilityData;
    }
}

// Export for use
window.dataLoader = new DataLoader(); 