/**
 * BigQuery-Only Data Loader for ORCAST
 * Uses ONLY the 473 verified whale sightings from OBIS research database
 * 237 unique ocean locations in San Juan Islands waters
 * 2019-2024 timespan of real observations
 */

class BigQueryDataLoader {
    constructor() {
        this.baseURL = 'https://orcast.org/api';
        this.cache = {
            verified_sightings: null,
            environmental_data: null,
            behavioral_features: null,
            last_updated: null
        };
        
        // Configuration for OBIS verified data only
        this.config = {
            data_source: 'OBIS_verified_only',
            total_sightings: 473,
            unique_locations: 237,
            timespan: '2019-2024',
            coordinates_only: 'real_observations',
            no_synthetic_data: true,
            no_placeholder_coordinates: true
        };
    }

    /**
     * Load only verified OBIS whale sightings - no artificial data
     */
    async loadVerifiedSightingsOnly() {
        try {
            console.log('🔄 Loading 473 verified OBIS whale sightings...');
            
            // Load from BigQuery-backed API endpoint
            const response = await fetch(`${this.baseURL}/verified-sightings`);
            if (!response.ok) {
                throw new Error(`BigQuery API error: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Validate that we're getting real data, not synthetic
            if (data.data_source !== 'OBIS_verified' || data.total_count !== 473) {
                console.warn('⚠️ Data validation failed - may contain synthetic data');
                return await this.loadBackupVerifiedData();
            }
            
            // Process verified sightings only
            this.cache.verified_sightings = data.sightings.map(sighting => ({
                id: sighting.sighting_id,
                location: {
                    lat: sighting.latitude,
                    lng: sighting.longitude
                },
                timestamp: new Date(sighting.observation_timestamp),
                behavior: sighting.behavior_primary,
                pod_size: sighting.pod_size || 1,
                confidence: sighting.data_quality_score,
                verified: true,
                source: 'OBIS_research_database',
                location_name: sighting.location_name || 'San Juan Islands',
                environmental_context: sighting.environmental_context
            }));
            
            console.log(`✅ Loaded ${this.cache.verified_sightings.length} verified OBIS sightings`);
            console.log(`📍 ${this.getUniqueLocations().length} unique ocean locations`);
            console.log(`📅 Timespan: ${this.getDateRange()}`);
            
            return this.cache.verified_sightings;
            
        } catch (error) {
            console.error('❌ Failed to load verified sightings:', error);
            return await this.loadBackupVerifiedData();
        }
    }

    /**
     * Load environmental data aligned with verified sightings
     */
    async loadEnvironmentalData() {
        try {
            console.log('🌊 Loading environmental data for verified sightings...');
            
            const response = await fetch(`${this.baseURL}/environmental-features`);
            const data = await response.json();
            
            // Filter to only environmental data matching our 473 verified sightings
            this.cache.environmental_data = data.features.filter(env => 
                this.cache.verified_sightings.some(s => s.id === env.sighting_id)
            );
            
            console.log(`✅ Loaded environmental data for ${this.cache.environmental_data.length} verified sightings`);
            return this.cache.environmental_data;
            
        } catch (error) {
            console.error('❌ Failed to load environmental data:', error);
            return [];
        }
    }

    /**
     * Load behavioral features from BigQuery ML training data
     */
    async loadBehavioralFeatures() {
        try {
            console.log('🧠 Loading behavioral features from ML training data...');
            
            const response = await fetch(`${this.baseURL}/behavioral-features`);
            const data = await response.json();
            
            // Only features for our verified sightings
            this.cache.behavioral_features = data.features.filter(feature => 
                this.cache.verified_sightings.some(s => s.id === feature.sighting_id)
            );
            
            console.log(`✅ Loaded behavioral features for ${this.cache.behavioral_features.length} verified sightings`);
            return this.cache.behavioral_features;
            
        } catch (error) {
            console.error('❌ Failed to load behavioral features:', error);
            return [];
        }
    }

    /**
     * Generate realistic probability heatmap using ONLY verified data
     */
    generateRealisticProbabilities() {
        if (!this.cache.verified_sightings) {
            console.error('❌ No verified sightings loaded');
            return { overall: [], feeding: [], socializing: [], traveling: [] };
        }

        const probabilities = {
            overall: [],
            feeding: [],
            socializing: [],
            traveling: []
        };

        // Create probability points based on REAL sighting locations only
        this.cache.verified_sightings.forEach(sighting => {
            const location = new google.maps.LatLng(sighting.location.lat, sighting.location.lng);
            
            // Base probability from data quality and recency
            const baseWeight = sighting.confidence * this.getRecencyWeight(sighting.timestamp);
            
            probabilities.overall.push({
                location: location,
                weight: baseWeight
            });

            // Behavior-specific probabilities
            if (sighting.behavior === 'foraging' || sighting.behavior === 'feeding') {
                probabilities.feeding.push({
                    location: location,
                    weight: baseWeight * 1.2
                });
            }
            
            if (sighting.behavior === 'socializing' || sighting.behavior === 'social') {
                probabilities.socializing.push({
                    location: location,
                    weight: baseWeight * 1.1
                });
            }
            
            if (sighting.behavior === 'traveling' || sighting.behavior === 'transit') {
                probabilities.traveling.push({
                    location: location,
                    weight: baseWeight * 0.9
                });
            }
        });

        console.log(`📊 Generated realistic probabilities from ${this.cache.verified_sightings.length} verified sightings`);
        return probabilities;
    }

    /**
     * Get configuration toggles for map modes
     */
    getMapConfigurationModes() {
        return {
            'verified-sightings': {
                name: 'Verified Sightings Only',
                description: '473 OBIS research database observations',
                active: true,
                data_source: 'BigQuery verified sightings'
            },
            'behavioral-analysis': {
                name: 'Behavioral Analysis',
                description: 'ML-driven behavior classification',
                active: false,
                data_source: 'BigQuery behavioral features'
            },
            'environmental-context': {
                name: 'Environmental Context',
                description: 'Environmental conditions at sighting locations',
                active: false,
                data_source: 'BigQuery environmental features'
            },
            'temporal-analysis': {
                name: 'Temporal Analysis',
                description: '2019-2024 temporal patterns',
                active: false,
                data_source: 'BigQuery temporal features'
            }
        };
    }

    /**
     * Switch between map configuration modes
     */
    async switchMapMode(mode) {
        console.log(`🔄 Switching to map mode: ${mode}`);
        
        switch (mode) {
            case 'verified-sightings':
                return this.generateRealisticProbabilities();
                
            case 'behavioral-analysis':
                if (!this.cache.behavioral_features) {
                    await this.loadBehavioralFeatures();
                }
                return this.generateBehavioralProbabilities();
                
            case 'environmental-context':
                if (!this.cache.environmental_data) {
                    await this.loadEnvironmentalData();
                }
                return this.generateEnvironmentalProbabilities();
                
            case 'temporal-analysis':
                return this.generateTemporalProbabilities();
                
            default:
                return this.generateRealisticProbabilities();
        }
    }

    /**
     * Helper methods
     */
    getUniqueLocations() {
        if (!this.cache.verified_sightings) return [];
        
        const locations = new Set();
        this.cache.verified_sightings.forEach(sighting => {
            locations.add(`${sighting.location.lat.toFixed(4)},${sighting.location.lng.toFixed(4)}`);
        });
        
        return Array.from(locations);
    }

    getDateRange() {
        if (!this.cache.verified_sightings) return 'Unknown';
        
        const dates = this.cache.verified_sightings.map(s => s.timestamp);
        const earliest = new Date(Math.min(...dates));
        const latest = new Date(Math.max(...dates));
        
        return `${earliest.getFullYear()}-${latest.getFullYear()}`;
    }

    getRecencyWeight(timestamp) {
        const now = new Date();
        const daysSince = (now - timestamp) / (1000 * 60 * 60 * 24);
        
        // More recent sightings get higher weight
        if (daysSince < 30) return 1.0;
        if (daysSince < 90) return 0.8;
        if (daysSince < 365) return 0.6;
        return 0.4;
    }

    /**
     * Backup data loader - loads from local files if API fails
     */
    async loadBackupVerifiedData() {
        try {
            console.log('🔄 Loading backup verified data...');
            
            // This should load from a local file containing only the 473 verified sightings
            const response = await fetch('/data/verified-obis-sightings.json');
            const data = await response.json();
            
            if (data.total_sightings !== 473) {
                throw new Error('Backup data does not match expected 473 verified sightings');
            }
            
            this.cache.verified_sightings = data.sightings;
            console.log('✅ Loaded backup verified data');
            return this.cache.verified_sightings;
            
        } catch (error) {
            console.error('❌ Failed to load backup data:', error);
            return [];
        }
    }

    /**
     * Data validation to ensure no synthetic data
     */
    validateRealDataOnly(data) {
        const validation = {
            is_real_data: true,
            issues: []
        };

        // Check for common synthetic data patterns
        if (data.some(d => d.source && d.source.includes('synthetic'))) {
            validation.is_real_data = false;
            validation.issues.push('Contains synthetic data sources');
        }

        if (data.some(d => d.location && (d.location.lat === 0 && d.location.lng === 0))) {
            validation.is_real_data = false;
            validation.issues.push('Contains null island coordinates (0,0)');
        }

        if (data.some(d => d.confidence === 1.0)) {
            validation.is_real_data = false;
            validation.issues.push('Contains perfect confidence scores (likely synthetic)');
        }

        return validation;
    }
}

// Export for use in other modules
window.BigQueryDataLoader = BigQueryDataLoader; 