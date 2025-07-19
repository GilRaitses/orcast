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

        const now = new Date();
        let windowStart, windowEnd;
        if (currentTimeUnit === 'weeks') {
            // Calculate start of the week at the given offset
            const start = new Date(now);
            start.setDate(now.getDate() - now.getDay() + (currentPeriodOffset * 7));
            start.setHours(0, 0, 0, 0);
            windowStart = start.getTime();
            const end = new Date(start);
            end.setDate(start.getDate() + 7);
            windowEnd = end.getTime();
        } else if (currentTimeUnit === 'months') {
            // Calculate start of the month at the given offset
            const start = new Date(now.getFullYear(), now.getMonth() + currentPeriodOffset, 1);
            windowStart = start.getTime();
            const end = new Date(now.getFullYear(), now.getMonth() + currentPeriodOffset + 1, 1);
            windowEnd = end.getTime();
        } else { // years
            // Calculate start of the year at the given offset
            const start = new Date(now.getFullYear() + currentPeriodOffset, 0, 1);
            windowStart = start.getTime();
            const end = new Date(now.getFullYear() + currentPeriodOffset + 1, 0, 1);
            windowEnd = end.getTime();
        }

        // Filter and convert real sightings
        const filteredSightings = [];
        Object.values(this.realSightingsData).forEach(sighting => {
            // Only include if in the window
            if (sighting.timestamp < windowStart || sighting.timestamp >= windowEnd) return;
            
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

    filterCurrentData(currentTimeUnit) {
        if (!this.realSightingsData) {
            console.warn('Real sightings data not loaded yet');
            return [];
        }
        const now = new Date();
        let startTime;
        if (currentTimeUnit === 'weeks') {
            // Start of current week (Sunday)
            startTime = new Date(now);
            startTime.setDate(now.getDate() - now.getDay());
            startTime.setHours(0, 0, 0, 0);
        } else if (currentTimeUnit === 'months') {
            // Start of current month
            startTime = new Date(now.getFullYear(), now.getMonth(), 1);
        } else if (currentTimeUnit === 'years') {
            // Start of current year
            startTime = new Date(now.getFullYear(), 0, 1);
        } else {
            startTime = new Date(0); // fallback: all data
        }
        const startTimestamp = startTime.getTime();
        const filteredSightings = [];
        Object.values(this.realSightingsData).forEach(sighting => {
            if (sighting.timestamp >= startTimestamp) {
                // Calculate confidence-based probability (same as filterRealSightingsData)
                let probability = 30;
                if (sighting.confidence === 'high') probability += 40;
                else if (sighting.confidence === 'medium') probability += 25;
                else if (sighting.confidence === 'low') probability += 10;
                if (sighting.verified) probability += 20;
                if (sighting.behavior === 'foraging') probability += 15;
                else if (sighting.behavior === 'socializing') probability += 10;
                probability = Math.min(95, probability);
                // Format time ago
                const hoursAgo = (Date.now() - sighting.timestamp) / (1000 * 60 * 60);
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
                    depth: Math.round(Math.random() * 40 + 20),
                    podSize: sighting.orcaCount,
                    location: sighting.locationName,
                    behavior: sighting.behavior,
                    confidence: sighting.confidence,
                    verified: sighting.verified,
                    hoursAgo: hoursAgo
                });
            }
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