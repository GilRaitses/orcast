/**
 * Internal Agent API for ORCAST Multi-Agent Research Platform
 * 
 * This API serves as the bridge between the map interface and the Gemma agent orchestra,
 * enabling hierarchical planning, multi-source data integration, and coordinated research.
 */

class InternalAgentAPI {
    constructor(config) {
        this.map = config.map;
        this.temporalConfig = config.temporalConfig;
        this.agentConfig = config.agentConfig;
        
        // Data caches for different sources
        this.dataCache = {
            obis: null,
            noaa: null,
            citizen: null,
            dtag: null,
            predictions: null
        };
        
        // Agent orchestration state
        this.agentOrchestra = null;
        this.researchAgent = null;
        this.plannerAgent = null;
        this.analyticsAgent = null;
        
        // Map visualization layers
        this.mapLayers = {
            heatmaps: [],
            markers: [],
            routes: [],
            zones: []
        };
        
        // Hierarchical planning state
        this.planningHierarchy = {
            level1: { status: 'pending', results: null }, // Strategic
            level2: { status: 'pending', results: null }, // Route Planning
            level3: { status: 'pending', results: null }, // Tactical
            level4: { status: 'pending', results: null }  // Real-time
        };
        
        console.log('🔗 Internal Agent API initialized');
    }

    /**
     * MULTI-SOURCE DATA LOADING METHODS
     */

    async loadOBISData(historicalYears) {
        console.log(`📊 Loading OBIS data for ${historicalYears} years...`);
        
        try {
            // Calculate date range
            const endDate = new Date();
            const startDate = new Date();
            startDate.setFullYear(endDate.getFullYear() - historicalYears);
            
            // Load from verified sightings API
            const response = await fetch(`/api/verified-sightings?start=${startDate.toISOString()}&end=${endDate.toISOString()}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.dataCache.obis = {
                    type: 'historical',
                    source: 'OBIS',
                    count: data.total_count,
                    sightings: data.sightings || [],
                    timeRange: { start: startDate, end: endDate },
                    lastUpdated: new Date()
                };
                
                console.log(`✅ Loaded ${data.total_count} OBIS sightings`);
                return this.dataCache.obis;
            }
            
            throw new Error('OBIS API returned error status');
            
        } catch (error) {
            console.error('Error loading OBIS data:', error);
            return { type: 'historical', source: 'OBIS', count: 0, error: error.message };
        }
    }

    async loadNOAAData() {
        console.log('🌊 Loading NOAA environmental data...');
        
        try {
            // Load real-time NOAA data
            const response = await fetch('/api/environmental');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.dataCache.noaa = {
                    type: 'environmental',
                    source: 'NOAA',
                    data: data.environmentalData,
                    lastUpdated: new Date()
                };
                
                console.log('✅ Loaded NOAA environmental data');
                return this.dataCache.noaa;
            }
            
            throw new Error('NOAA API returned error status');
            
        } catch (error) {
            console.error('Error loading NOAA data:', error);
            return { type: 'environmental', source: 'NOAA', error: error.message };
        }
    }

    async loadCitizenScienceData() {
        console.log('👥 Loading citizen science reports...');
        
        try {
            // Load citizen science sightings
            const response = await fetch('/api/sightings?source=citizen');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.dataCache.citizen = {
                    type: 'community',
                    source: 'Citizen Science',
                    count: data.count,
                    sightings: data.sightings || [],
                    lastUpdated: new Date()
                };
                
                console.log(`✅ Loaded ${data.count} citizen science reports`);
                return this.dataCache.citizen;
            }
            
            throw new Error('Citizen science API returned error status');
            
        } catch (error) {
            console.error('Error loading citizen science data:', error);
            return { type: 'community', source: 'Citizen Science', count: 0, error: error.message };
        }
    }

    async loadDTAGData() {
        console.log('🏷️ Loading DTAG biologging data...');
        
        try {
            // Load DTAG behavioral data
            const response = await fetch('/api/dtag-data');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.dataCache.dtag = {
                    type: 'biologging',
                    source: 'DTAG',
                    data: data.data,
                    lastUpdated: new Date()
                };
                
                console.log('✅ Loaded DTAG biologging data');
                return this.dataCache.dtag;
            }
            
            throw new Error('DTAG API returned error status');
            
        } catch (error) {
            console.error('Error loading DTAG data:', error);
            return { type: 'biologging', source: 'DTAG', error: error.message };
        }
    }

    async loadPredictionData(forecastDays) {
        console.log(`🔮 Loading ML predictions for ${forecastDays} days...`);
        
        try {
            // Load ML predictions
            const response = await fetch(`/api/predictions?forecast=${forecastDays}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.dataCache.predictions = {
                    type: 'predictions',
                    source: 'ML Models',
                    data: data.data,
                    forecastDays: forecastDays,
                    lastUpdated: new Date()
                };
                
                console.log('✅ Loaded ML prediction data');
                return this.dataCache.predictions;
            }
            
            throw new Error('Predictions API returned error status');
            
        } catch (error) {
            console.error('Error loading prediction data:', error);
            return { type: 'predictions', source: 'ML Models', error: error.message };
        }
    }

    /**
     * MAP VISUALIZATION METHODS
     */

    async updateMapVisualization(loadedData) {
        console.log('🗺️ Updating map visualization with loaded data...');
        
        try {
            // Clear existing layers
            this.clearAllMapLayers();
            
            // Process each data source
            for (const dataset of loadedData) {
                await this.renderDataOnMap(dataset);
            }
            
            console.log(`✅ Updated map with ${loadedData.length} data sources`);
            
        } catch (error) {
            console.error('Error updating map visualization:', error);
        }
    }

    async renderDataOnMap(dataset) {
        if (!dataset || dataset.error) return;
        
        switch (dataset.type) {
            case 'historical':
                await this.renderHistoricalSightings(dataset);
                break;
                
            case 'environmental':
                await this.renderEnvironmentalData(dataset);
                break;
                
            case 'community':
                await this.renderCommunityReports(dataset);
                break;
                
            case 'biologging':
                await this.renderBiologgingData(dataset);
                break;
                
            case 'predictions':
                await this.renderPredictions(dataset);
                break;
        }
    }

    async renderHistoricalSightings(dataset) {
        if (!dataset.sightings || dataset.sightings.length === 0) return;
        
        const heatmapData = dataset.sightings.map(sighting => ({
            location: new google.maps.LatLng(sighting.latitude, sighting.longitude),
            weight: this.calculateSightingWeight(sighting)
        }));
        
        const heatmap = new google.maps.visualization.HeatmapLayer({
            data: heatmapData,
            map: this.map,
            radius: 25,
            opacity: 0.6,
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
        
        this.mapLayers.heatmaps.push(heatmap);
    }

    async renderPredictions(dataset) {
        if (!dataset.data || !dataset.data.zones) return;
        
        const predictionData = dataset.data.zones
            .filter(zone => zone.probability >= this.temporalConfig.confidenceThreshold)
            .map(zone => ({
                location: new google.maps.LatLng(zone.center.lat, zone.center.lng),
                weight: zone.probability
            }));
        
        if (predictionData.length > 0) {
            const predictionHeatmap = new google.maps.visualization.HeatmapLayer({
                data: predictionData,
                map: this.map,
                radius: 35,
                opacity: 0.7,
                gradient: [
                    'rgba(255, 255, 0, 0)',
                    'rgba(255, 255, 0, 1)',
                    'rgba(255, 191, 0, 1)',
                    'rgba(255, 127, 0, 1)',
                    'rgba(255, 63, 0, 1)',
                    'rgba(255, 0, 0, 1)'
                ]
            });
            
            this.mapLayers.heatmaps.push(predictionHeatmap);
        }
    }

    /**
     * AGENT ORCHESTRATION METHODS
     */

    async initializeAgentOrchestra() {
        console.log('🎼 Initializing agent orchestra...');
        
        try {
            // Initialize the multi-agent orchestrator
            if (window.ORCASTMultiAgentSystem) {
                this.agentOrchestra = new window.ORCASTMultiAgentSystem({
                    firebaseConfig: {
                        apiKey: "AIzaSyCqHFjW-FQVFGqZj5K8GZj8xJZP3r8jdRI",
                        authDomain: "orca-904de.firebaseapp.com",
                        projectId: "orca-904de"
                    },
                    internalAPI: this,
                    map: this.map,
                    agentConfig: this.agentConfig
                });
                
                await this.agentOrchestra.initialize();
            }
            
            // Initialize individual agents
            if (window.WhaleWatchingResearchAgent) {
                this.researchAgent = new window.WhaleWatchingResearchAgent({
                    sindyServiceUrl: '/api/sindy-predictions',
                    hmcServiceUrl: '/api/hmc-uncertainty',
                    agentConfig: this.agentConfig
                });
            }
            
            if (window.WhaleWatchingPlannerAgent) {
                this.plannerAgent = new window.WhaleWatchingPlannerAgent({
                    researchAgent: this.researchAgent,
                    googleMapsAPI: this.map,
                    agentConfig: this.agentConfig
                });
            }
            
            console.log('✅ Agent orchestra initialized successfully');
            return true;
            
        } catch (error) {
            console.error('Error initializing agent orchestra:', error);
            return false;
        }
    }

    async planWhaleWatchingTrip(userInput, options = {}) {
        console.log('🗺️ Planning whale watching trip with agent orchestra...');
        
        try {
            if (!this.agentOrchestra) {
                await this.initializeAgentOrchestra();
            }
            
            // Prepare planning context
            const planningContext = {
                userInput: userInput,
                temporalConfig: this.temporalConfig,
                agentConfig: this.agentConfig,
                dataSources: this.getAvailableDataSources(),
                mapBounds: this.getCurrentMapBounds(),
                ...options
            };
            
            // Execute trip planning through agent orchestra
            const tripPlan = await this.agentOrchestra.planTrip(userInput, planningContext);
            
            console.log('✅ Trip planning completed successfully');
            return tripPlan;
            
        } catch (error) {
            console.error('Error planning whale watching trip:', error);
            throw error;
        }
    }

    /**
     * HIERARCHICAL PLANNING METHODS
     */

    async executeHierarchyLevel(level, config) {
        console.log(`🔄 Executing hierarchy level ${level}...`);
        
        try {
            this.planningHierarchy[`level${level}`].status = 'executing';
            
            let result;
            switch (level) {
                case 1:
                    result = await this.executeStrategicPlanning(config);
                    break;
                case 2:
                    result = await this.executeRoutePlanning(config);
                    break;
                case 3:
                    result = await this.executeTacticalOptimization(config);
                    break;
                case 4:
                    result = await this.executeRealtimeAdaptation(config);
                    break;
                default:
                    throw new Error(`Invalid hierarchy level: ${level}`);
            }
            
            this.planningHierarchy[`level${level}`].status = 'completed';
            this.planningHierarchy[`level${level}`].results = result;
            
            console.log(`✅ Hierarchy level ${level} completed successfully`);
            return result;
            
        } catch (error) {
            this.planningHierarchy[`level${level}`].status = 'error';
            console.error(`Error executing hierarchy level ${level}:`, error);
            throw error;
        }
    }

    async executeStrategicPlanning(config) {
        console.log('📋 Executing strategic planning...');
        
        // Analyze available data sources and constraints
        const dataAnalysis = this.analyzeAvailableData();
        
        // Determine optimal viewing windows
        const temporalAnalysis = this.analyzeTemporalPatterns(config);
        
        // Identify high-probability zones
        const spatialAnalysis = this.analyzeSpatialPatterns(config);
        
        return {
            level: 1,
            type: 'strategic',
            dataAnalysis,
            temporalAnalysis,
            spatialAnalysis,
            recommendations: this.generateStrategicRecommendations(dataAnalysis, temporalAnalysis, spatialAnalysis)
        };
    }

    async executeRoutePlanning(config) {
        console.log('🛣️ Executing route planning...');
        
        if (!this.plannerAgent) {
            throw new Error('Planner agent not initialized');
        }
        
        // Get strategic planning results
        const strategicResults = this.planningHierarchy.level1.results;
        if (!strategicResults) {
            throw new Error('Strategic planning must be completed first');
        }
        
        // Execute route planning through planner agent
        const routePlan = await this.plannerAgent.planSustainableViewingRoutes(
            config,
            strategicResults
        );
        
        return {
            level: 2,
            type: 'route_planning',
            routes: routePlan.route_recommendations,
            timing: routePlan.timing_strategy,
            sustainability: routePlan.sustainability_plan
        };
    }

    async executeTacticalOptimization(config) {
        console.log('⚡ Executing tactical optimization...');
        
        const routeResults = this.planningHierarchy.level2.results;
        if (!routeResults) {
            throw new Error('Route planning must be completed first');
        }
        
        // Optimize routes based on current conditions
        const optimizedRoutes = await this.optimizeRoutes(routeResults.routes, config);
        
        // Calculate real-time adjustments
        const adjustments = await this.calculateRouteAdjustments(optimizedRoutes, config);
        
        return {
            level: 3,
            type: 'tactical_optimization',
            optimizedRoutes,
            adjustments,
            performanceMetrics: this.calculatePerformanceMetrics(optimizedRoutes)
        };
    }

    async executeRealtimeAdaptation(config) {
        console.log('🔄 Executing real-time adaptation...');
        
        const tacticalResults = this.planningHierarchy.level3.results;
        if (!tacticalResults) {
            throw new Error('Tactical optimization must be completed first');
        }
        
        // Monitor real-time conditions
        const currentConditions = await this.getCurrentConditions();
        
        // Generate adaptive recommendations
        const adaptiveRecommendations = await this.generateAdaptiveRecommendations(
            tacticalResults,
            currentConditions
        );
        
        return {
            level: 4,
            type: 'realtime_adaptation',
            currentConditions,
            adaptiveRecommendations,
            contingencyPlans: this.generateContingencyPlans(adaptiveRecommendations)
        };
    }

    /**
     * RESEARCH ORCHESTRATION METHODS
     */

    async executeResearchAnalysis(params) {
        console.log('🔬 Executing comprehensive research analysis...');
        
        try {
            if (!this.researchAgent) {
                await this.initializeAgentOrchestra();
            }
            
            // Execute research through research agent
            const researchFindings = await this.researchAgent.researchOptimalViewingLocations(params);
            
            return {
                type: 'research_analysis',
                findings: researchFindings,
                confidence: this.calculateResearchConfidence(researchFindings),
                recommendations: this.synthesizeResearchRecommendations(researchFindings)
            };
            
        } catch (error) {
            console.error('Error executing research analysis:', error);
            throw error;
        }
    }

    async pullPublicDataSources(sources) {
        console.log('🌐 Pulling from public data sources...');
        
        const promises = sources.map(source => this.pullFromPublicSource(source));
        const results = await Promise.allSettled(promises);
        
        const successfulPulls = results
            .filter(result => result.status === 'fulfilled')
            .map(result => result.value);
        
        console.log(`✅ Successfully pulled ${successfulPulls.length}/${sources.length} public data sources`);
        return successfulPulls;
    }

    async pullFromPublicSource(source) {
        console.log(`📡 Pulling data from ${source}...`);
        
        switch (source) {
            case 'noaa_tides':
                return await this.pullNOAATidalData();
            case 'ais_vessels':
                return await this.pullAISVesselData();
            case 'salmon_counts':
                return await this.pullSalmonCountData();
            case 'weather_marine':
                return await this.pullMarineWeatherData();
            default:
                throw new Error(`Unknown public data source: ${source}`);
        }
    }

    /**
     * UTILITY METHODS
     */

    getCurrentMapBounds() {
        if (!this.map) return null;
        
        const bounds = this.map.getBounds();
        if (!bounds) return null;
        
        return {
            north: bounds.getNorthEast().lat(),
            south: bounds.getSouthWest().lat(),
            east: bounds.getNorthEast().lng(),
            west: bounds.getSouthWest().lng()
        };
    }

    getAvailableDataSources() {
        return Object.keys(this.dataCache).filter(source => 
            this.dataCache[source] && !this.dataCache[source].error
        );
    }

    updateConfidenceThreshold(threshold) {
        this.temporalConfig.confidenceThreshold = threshold;
        
        // Update existing prediction visualizations
        this.updatePredictionVisualizations();
    }

    clearAllMapLayers() {
        // Clear heatmaps
        this.mapLayers.heatmaps.forEach(heatmap => heatmap.setMap(null));
        this.mapLayers.heatmaps = [];
        
        // Clear markers
        this.mapLayers.markers.forEach(marker => marker.setMap(null));
        this.mapLayers.markers = [];
        
        // Clear routes
        this.mapLayers.routes.forEach(route => route.setMap(null));
        this.mapLayers.routes = [];
        
        // Clear zones
        this.mapLayers.zones.forEach(zone => zone.setMap(null));
        this.mapLayers.zones = [];
    }

    calculateSightingWeight(sighting) {
        let weight = 1.0;
        
        // Adjust weight based on data quality
        if (sighting.data_quality_score) {
            weight *= sighting.data_quality_score;
        }
        
        // Adjust weight based on recency
        if (sighting.observation_timestamp) {
            const daysSince = (new Date() - new Date(sighting.observation_timestamp)) / (1000 * 60 * 60 * 24);
            if (daysSince < 30) weight *= 1.2;
            else if (daysSince < 90) weight *= 1.0;
            else if (daysSince < 365) weight *= 0.8;
            else weight *= 0.6;
        }
        
        // Adjust weight based on pod size
        if (sighting.pod_size) {
            weight *= Math.log(sighting.pod_size + 1) / Math.log(10);
        }
        
        return Math.min(weight, 2.0); // Cap at 2.0
    }

    analyzeAvailableData() {
        const analysis = {
            totalSources: 0,
            historicalRange: null,
            predictionRange: null,
            dataQuality: 'unknown',
            coverage: 'unknown'
        };
        
        Object.values(this.dataCache).forEach(dataset => {
            if (dataset && !dataset.error) {
                analysis.totalSources++;
                
                if (dataset.type === 'historical' && dataset.timeRange) {
                    analysis.historicalRange = dataset.timeRange;
                }
                
                if (dataset.type === 'predictions' && dataset.forecastDays) {
                    analysis.predictionRange = dataset.forecastDays;
                }
            }
        });
        
        return analysis;
    }

    analyzeTemporalPatterns(config) {
        // Analyze temporal patterns in the loaded data
        return {
            optimalTimeWindows: this.identifyOptimalTimeWindows(),
            seasonalPatterns: this.analyzeSeasonalPatterns(),
            dailyPatterns: this.analyzeDailyPatterns(),
            tidalInfluence: this.analyzeTidalInfluence()
        };
    }

    analyzeSpatialPatterns(config) {
        // Analyze spatial patterns in the loaded data
        return {
            hotspots: this.identifyHighProbabilityZones(),
            corridors: this.identifyMovementCorridors(),
            avoidanceZones: this.identifyAvoidanceZones(),
            optimalViewingLocations: this.identifyOptimalViewingLocations()
        };
    }

    generateStrategicRecommendations(dataAnalysis, temporalAnalysis, spatialAnalysis) {
        return {
            primaryRecommendation: 'Focus on high-probability zones during optimal time windows',
            secondaryRecommendations: [
                'Monitor real-time conditions for adaptive routing',
                'Consider seasonal migration patterns',
                'Integrate tidal influence into timing decisions'
            ],
            confidence: 0.85
        };
    }

    // Placeholder methods for complex analysis
    identifyOptimalTimeWindows() { return []; }
    analyzeSeasonalPatterns() { return {}; }
    analyzeDailyPatterns() { return {}; }
    analyzeTidalInfluence() { return {}; }
    identifyHighProbabilityZones() { return []; }
    identifyMovementCorridors() { return []; }
    identifyAvoidanceZones() { return []; }
    identifyOptimalViewingLocations() { return []; }
    
    async optimizeRoutes(routes, config) { return routes; }
    async calculateRouteAdjustments(routes, config) { return []; }
    calculatePerformanceMetrics(routes) { return {}; }
    async getCurrentConditions() { return {}; }
    async generateAdaptiveRecommendations(tactical, conditions) { return []; }
    generateContingencyPlans(recommendations) { return []; }
    calculateResearchConfidence(findings) { return 0.75; }
    synthesizeResearchRecommendations(findings) { return []; }
    
    async pullNOAATidalData() { return { source: 'noaa_tides', data: {} }; }
    async pullAISVesselData() { return { source: 'ais_vessels', data: {} }; }
    async pullSalmonCountData() { return { source: 'salmon_counts', data: {} }; }
    async pullMarineWeatherData() { return { source: 'weather_marine', data: {} }; }
    
    updatePredictionVisualizations() {
        // Re-render prediction layers with new confidence threshold
        const predictionData = this.dataCache.predictions;
        if (predictionData) {
            this.renderPredictions(predictionData);
        }
    }

    async displayTripRecommendations(trip) {
        console.log('🗺️ Displaying trip recommendations on map...');
        // Implementation for displaying trip routes and recommendations
    }

    async displayResearchFindings(research) {
        console.log('🔬 Displaying research findings on map...');
        // Implementation for displaying research results
    }

    async renderEnvironmentalData(dataset) {
        // Implementation for rendering environmental data
    }

    async renderCommunityReports(dataset) {
        // Implementation for rendering community reports
    }

    async renderBiologgingData(dataset) {
        // Implementation for rendering biologging data
    }
}

// Make available globally for the map interface
window.InternalAgentAPI = InternalAgentAPI;

console.log('🔗 Internal Agent API module loaded'); 