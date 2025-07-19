/**
 * Multi-Agent Orchestration System for ORCAST
 * 
 * Architecture:
 * - PrimaryAgent: Main trip planning orchestrator
 * - AnalyticsAgent: Statistics gathering and dashboard preparation
 * - VectorAgent: Viewing zone vector space management
 * - ReasoningAgent: Interpretable planning materials and explanations
 */

class MultiAgentOrchestrator {
    constructor(config) {
        this.config = config;
        this.agents = {};
        this.eventBus = new EventTarget();
        this.vectorSpace = new Map(); // Zone vectors and embeddings
        this.analytics = new Map(); // Analytics cache
        this.activeSessions = new Map(); // Active planning sessions
        
        this.initializeAgents();
        this.setupEventHandlers();
    }

    initializeAgents() {
        // Primary trip planning agent
        this.agents.primary = new PrimaryPlanningAgent({
            geminiIntegration: this.config.geminiIntegration,
            orchestrator: this
        });

        // Analytics and statistics agent
        this.agents.analytics = new AnalyticsAgent({
            bigQueryClient: this.config.bigQueryClient,
            firebaseDB: this.config.firebaseDB,
            orchestrator: this
        });

        // Vector space management agent
        this.agents.vector = new VectorSpaceAgent({
            vectorDB: this.config.vectorDB,
            orchestrator: this
        });

        // Reasoning and explanation agent
        this.agents.reasoning = new ReasoningAgent({
            geminiIntegration: this.config.geminiIntegration,
            orchestrator: this
        });
    }

    setupEventHandlers() {
        this.eventBus.addEventListener('analytics-ready', (event) => {
            this.handleAnalyticsReady(event.detail);
        });

        this.eventBus.addEventListener('vector-space-updated', (event) => {
            this.handleVectorSpaceUpdate(event.detail);
        });

        this.eventBus.addEventListener('reasoning-complete', (event) => {
            this.handleReasoningComplete(event.detail);
        });
    }

    /**
     * Main orchestration method for trip planning
     */
    async orchestrateTripPlanning(userInput, sessionId = null) {
        sessionId = sessionId || this.generateSessionId();
        
        try {
            // Initialize planning session
            const session = await this.initializePlanningSession(sessionId, userInput);
            
            // Step 1: Analytics agent gathers statistics and prepares dashboards
            console.log('[Orchestrator] Step 1: Gathering analytics...');
            const analyticsTask = this.agents.analytics.gatherTripStatistics(session);
            
            // Step 2: Vector agent updates viewing zone vectors
            console.log('[Orchestrator] Step 2: Updating vector space...');
            const vectorTask = this.agents.vector.updateViewingZoneVectors(session);
            
            // Step 3: Wait for both agents to complete preparation
            const [analytics, vectors] = await Promise.all([analyticsTask, vectorTask]);
            
            // Step 4: Reasoning agent prepares interpretable materials
            console.log('[Orchestrator] Step 3: Preparing reasoning materials...');
            const reasoning = await this.agents.reasoning.prepareReasoningMaterials(
                session, analytics, vectors
            );
            
            // Step 5: Primary agent orchestrates the full trip plan
            console.log('[Orchestrator] Step 4: Orchestrating trip plan...');
            const tripPlan = await this.agents.primary.orchestrateTripPlan(
                session, analytics, vectors, reasoning
            );
            
            // Step 6: Update session with results
            session.analytics = analytics;
            session.vectors = vectors;
            session.reasoning = reasoning;
            session.tripPlan = tripPlan;
            session.status = 'completed';
            session.completedAt = new Date().toISOString();
            
            this.activeSessions.set(sessionId, session);
            
            return {
                sessionId,
                tripPlan,
                analytics,
                reasoning,
                metadata: {
                    processingTime: Date.now() - session.startTime,
                    agentsUsed: Object.keys(this.agents),
                    vectorZones: vectors.zones.length,
                    analyticsMetrics: analytics.metrics.length
                }
            };
            
        } catch (error) {
            console.error('[Orchestrator] Trip planning failed:', error);
            throw new Error(`Trip planning orchestration failed: ${error.message}`);
        }
    }

    async initializePlanningSession(sessionId, userInput) {
        const session = {
            id: sessionId,
            userInput,
            constraints: await this.extractConstraints(userInput),
            startTime: Date.now(),
            status: 'initializing',
            createdAt: new Date().toISOString()
        };
        
        this.activeSessions.set(sessionId, session);
        return session;
    }

    async extractConstraints(userInput) {
        // Use existing Gemini integration to extract trip constraints
        if (this.config.geminiIntegration) {
            return await this.config.geminiIntegration.extractConstraints(userInput);
        }
        
        // Fallback rule-based extraction
        return this.fallbackConstraintExtraction(userInput);
    }

    fallbackConstraintExtraction(input) {
        const constraints = {
            duration: this.extractDuration(input),
            dates: this.extractDates(input),
            groupSize: this.extractGroupSize(input),
            accommodationType: this.extractAccommodationType(input),
            budget: this.extractBudget(input),
            viewingPreferences: this.extractViewingPreferences(input)
        };
        
        return constraints;
    }

    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    handleAnalyticsReady(data) {
        console.log('[Orchestrator] Analytics ready:', data);
        this.analytics.set(data.sessionId, data);
    }

    handleVectorSpaceUpdate(data) {
        console.log('[Orchestrator] Vector space updated:', data);
        this.vectorSpace.set(data.sessionId, data);
    }

    handleReasoningComplete(data) {
        console.log('[Orchestrator] Reasoning complete:', data);
    }

    // Utility methods for constraint extraction
    extractDuration(input) {
        const durationMatch = input.match(/(\d+)\s*(day|week|hour)s?/i);
        return durationMatch ? {
            value: parseInt(durationMatch[1]),
            unit: durationMatch[2].toLowerCase()
        } : null;
    }

    extractDates(input) {
        // Simple date extraction - can be enhanced
        const dateMatch = input.match(/(\w+\s+\d{1,2}|\d{1,2}\/\d{1,2}\/\d{4})/g);
        return dateMatch || [];
    }

    extractGroupSize(input) {
        const groupMatch = input.match(/(\d+)\s*(people|person|adult|guest)s?/i);
        return groupMatch ? parseInt(groupMatch[1]) : 1;
    }

    extractAccommodationType(input) {
        const accommodationTypes = ['hotel', 'airbnb', 'camping', 'resort', 'lodge', 'balcony'];
        for (const type of accommodationTypes) {
            if (input.toLowerCase().includes(type)) {
                return type;
            }
        }
        return null;
    }

    extractBudget(input) {
        const budgetMatch = input.match(/\$(\d+(?:,\d{3})*(?:\.\d{2})?)/);
        return budgetMatch ? parseFloat(budgetMatch[1].replace(',', '')) : null;
    }

    extractViewingPreferences(input) {
        const preferences = [];
        if (input.toLowerCase().includes('land')) preferences.push('land-based');
        if (input.toLowerCase().includes('boat')) preferences.push('boat-based');
        if (input.toLowerCase().includes('photography')) preferences.push('photography');
        if (input.toLowerCase().includes('research')) preferences.push('research');
        return preferences;
    }
}

/**
 * Primary Planning Agent - Main trip orchestrator
 */
class PrimaryPlanningAgent {
    constructor(config) {
        this.geminiIntegration = config.geminiIntegration;
        this.orchestrator = config.orchestrator;
    }

    async orchestrateTripPlan(session, analytics, vectors, reasoning) {
        console.log('[PrimaryAgent] Orchestrating comprehensive trip plan...');
        
        // Build hierarchical structure: Trip → Days → DayTrips → Stops → Activities → ViewingZones
        const tripStructure = await this.buildTripHierarchy(session, analytics, vectors);
        
        // Generate detailed itinerary with AI reasoning
        const itinerary = await this.generateDetailedItinerary(tripStructure, reasoning);
        
        // Add dynamic options and alternatives
        const options = await this.generateTripOptions(tripStructure, analytics);
        
        return {
            id: this.generateTripId(),
            structure: tripStructure,
            itinerary,
            options,
            analytics: analytics.summary,
            reasoning: reasoning.explanations,
            confidence: this.calculateOverallConfidence(tripStructure, analytics),
            created: new Date().toISOString()
        };
    }

    async buildTripHierarchy(session, analytics, vectors) {
        const constraints = session.constraints;
        const duration = constraints.duration?.value || 3;
        
        const trip = {
            id: this.generateTripId(),
            title: this.generateTripTitle(constraints),
            duration: duration,
            days: []
        };

        // Build each day
        for (let dayIndex = 0; dayIndex < duration; dayIndex++) {
            const day = await this.buildDayStructure(dayIndex, constraints, analytics, vectors);
            trip.days.push(day);
        }

        return trip;
    }

    async buildDayStructure(dayIndex, constraints, analytics, vectors) {
        const day = {
            day: dayIndex + 1,
            date: this.calculateDayDate(dayIndex, constraints),
            dayTrips: []
        };

        // Determine optimal day trips based on analytics
        const optimalTrips = analytics.recommendations.dayTrips[dayIndex] || [];
        
        for (const tripRec of optimalTrips) {
            const dayTrip = await this.buildDayTripStructure(tripRec, vectors);
            day.dayTrips.push(dayTrip);
        }

        return day;
    }

    async buildDayTripStructure(tripRecommendation, vectors) {
        const dayTrip = {
            id: this.generateDayTripId(),
            title: tripRecommendation.title,
            timeRange: tripRecommendation.timeRange,
            stops: []
        };

        // Build stops based on vector zone recommendations
        for (const stopRec of tripRecommendation.stops) {
            const stop = await this.buildStopStructure(stopRec, vectors);
            dayTrip.stops.push(stop);
        }

        return dayTrip;
    }

    async buildStopStructure(stopRecommendation, vectors) {
        const stop = {
            id: this.generateStopId(),
            name: stopRecommendation.name,
            location: stopRecommendation.location,
            duration: stopRecommendation.duration,
            activities: []
        };

        // Build activities at this stop
        for (const activityRec of stopRecommendation.activities) {
            const activity = await this.buildActivityStructure(activityRec, vectors);
            stop.activities.push(activity);
        }

        return stop;
    }

    async buildActivityStructure(activityRecommendation, vectors) {
        const activity = {
            id: this.generateActivityId(),
            type: activityRecommendation.type,
            title: activityRecommendation.title,
            description: activityRecommendation.description,
            duration: activityRecommendation.duration,
            viewingZones: []
        };

        // Find relevant viewing zones from vector space
        const relevantZones = vectors.findZonesForActivity(activity);
        
        for (const zone of relevantZones) {
            const viewingZone = await this.buildViewingZoneStructure(zone, vectors);
            activity.viewingZones.push(viewingZone);
        }

        return activity;
    }

    async buildViewingZoneStructure(zoneData, vectors) {
        const zone = {
            id: zoneData.id,
            name: zoneData.name,
            coordinates: zoneData.coordinates,
            probability: zoneData.probability,
            confidence: zoneData.confidence,
            content: await this.getZoneContent(zoneData, vectors),
            environmental: zoneData.environmental,
            historicalData: zoneData.historical
        };

        return zone;
    }

    async getZoneContent(zoneData, vectors) {
        // Get available content for this viewing zone
        const content = vectors.getZoneContent(zoneData.id);
        
        return {
            photos: content.photos || [],
            videos: content.videos || [],
            descriptions: content.descriptions || [],
            tips: content.tips || [],
            recentSightings: content.recentSightings || []
        };
    }

    generateTripId() {
        return `trip_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    generateDayTripId() {
        return `daytrip_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    }

    generateStopId() {
        return `stop_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    }

    generateActivityId() {
        return `activity_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    }

    generateTripTitle(constraints) {
        const duration = constraints.duration?.value || 3;
        const type = constraints.viewingPreferences?.join(' & ') || 'orca watching';
        return `${duration}-Day ${type.charAt(0).toUpperCase()}${type.slice(1)} Adventure`;
    }

    calculateDayDate(dayIndex, constraints) {
        const startDate = constraints.dates?.[0] ? new Date(constraints.dates[0]) : new Date();
        const dayDate = new Date(startDate);
        dayDate.setDate(dayDate.getDate() + dayIndex);
        return dayDate.toISOString().split('T')[0];
    }

    calculateOverallConfidence(tripStructure, analytics) {
        // Calculate confidence based on analytics and zone probabilities
        let totalConfidence = 0;
        let zoneCount = 0;

        tripStructure.days.forEach(day => {
            day.dayTrips.forEach(dayTrip => {
                dayTrip.stops.forEach(stop => {
                    stop.activities.forEach(activity => {
                        activity.viewingZones.forEach(zone => {
                            totalConfidence += zone.confidence;
                            zoneCount++;
                        });
                    });
                });
            });
        });

        return zoneCount > 0 ? totalConfidence / zoneCount : 0.5;
    }
}

/**
 * Analytics Agent - Statistics gathering and dashboard preparation
 */
class AnalyticsAgent {
    constructor(config) {
        this.bigQueryClient = config.bigQueryClient;
        this.firebaseDB = config.firebaseDB;
        this.orchestrator = config.orchestrator;
    }

    async gatherTripStatistics(session) {
        console.log('[AnalyticsAgent] Gathering comprehensive trip statistics...');
        
        const constraints = session.constraints;
        
        // Parallel data gathering
        const [
            behaviorStats,
            environmentalStats,
            historicalTrends,
            zoneProductivity,
            seasonalPatterns,
            successMetrics
        ] = await Promise.all([
            this.gatherBehaviorStatistics(constraints),
            this.gatherEnvironmentalStatistics(constraints),
            this.gatherHistoricalTrends(constraints),
            this.gatherZoneProductivity(constraints),
            this.gatherSeasonalPatterns(constraints),
            this.gatherSuccessMetrics(constraints)
        ]);

        const analytics = {
            sessionId: session.id,
            behavior: behaviorStats,
            environmental: environmentalStats,
            historical: historicalTrends,
            zones: zoneProductivity,
            seasonal: seasonalPatterns,
            success: successMetrics,
            recommendations: await this.generateRecommendations(constraints),
            dashboards: await this.prepareDashboards(),
            summary: this.generateAnalyticsSummary(),
            confidence: this.calculateAnalyticsConfidence(),
            generatedAt: new Date().toISOString()
        };

        // Emit analytics ready event
        this.orchestrator.eventBus.dispatchEvent(new CustomEvent('analytics-ready', {
            detail: analytics
        }));

        return analytics;
    }

    async gatherBehaviorStatistics(constraints) {
        // Query BigQuery for behavioral patterns
        const query = `
            SELECT 
                behavior_primary,
                COUNT(*) as frequency,
                AVG(behavior_confidence) as avg_confidence,
                AVG(pod_size) as avg_pod_size
            FROM \`orca-904de.orca_data.sightings\`
            WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            GROUP BY behavior_primary
            ORDER BY frequency DESC
        `;

        try {
            const results = await this.queryBigQuery(query);
            return {
                patterns: results,
                totalSightings: results.reduce((sum, r) => sum + r.frequency, 0),
                dominantBehavior: results[0]?.behavior_primary || 'unknown',
                avgConfidence: results.reduce((sum, r) => sum + r.avg_confidence, 0) / results.length
            };
        } catch (error) {
            console.error('[AnalyticsAgent] Behavior stats failed:', error);
            return this.getMockBehaviorStats();
        }
    }

    async gatherEnvironmentalStatistics(constraints) {
        // Get current environmental conditions
        return {
            current: await this.getCurrentEnvironmental(),
            forecast: await this.getEnvironmentalForecast(),
            optimal: await this.getOptimalConditions(),
            alerts: await this.getEnvironmentalAlerts()
        };
    }

    async gatherZoneProductivity(constraints) {
        const query = `
            SELECT 
                zone_id,
                zone_name,
                feeding_events_count,
                success_rate,
                avg_feeding_duration_minutes,
                productivity_trend
            FROM \`orca-904de.orca_data.feeding_zones\`
            WHERE analysis_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
            ORDER BY success_rate DESC, feeding_events_count DESC
        `;

        try {
            const results = await this.queryBigQuery(query);
            return {
                zones: results,
                topPerformers: results.slice(0, 5),
                trends: this.analyzeTrends(results)
            };
        } catch (error) {
            console.error('[AnalyticsAgent] Zone productivity failed:', error);
            return this.getMockZoneProductivity();
        }
    }

    async generateRecommendations(constraints) {
        // Generate intelligent recommendations based on analytics
        return {
            dayTrips: await this.generateDayTripRecommendations(constraints),
            timing: await this.generateTimingRecommendations(constraints),
            zones: await this.generateZoneRecommendations(constraints),
            conditions: await this.generateConditionRecommendations(constraints)
        };
    }

    async prepareDashboards() {
        // Prepare dashboard data for the frontend
        return {
            overview: await this.prepareOverviewDashboard(),
            analytics: await this.prepareAnalyticsDashboard(),
            zones: await this.prepareZonesDashboard(),
            environmental: await this.prepareEnvironmentalDashboard()
        };
    }

    // Mock data methods for fallback
    getMockBehaviorStats() {
        return {
            patterns: [
                { behavior_primary: 'foraging', frequency: 45, avg_confidence: 0.85, avg_pod_size: 8 },
                { behavior_primary: 'traveling', frequency: 32, avg_confidence: 0.92, avg_pod_size: 12 },
                { behavior_primary: 'socializing', frequency: 18, avg_confidence: 0.78, avg_pod_size: 15 }
            ],
            totalSightings: 95,
            dominantBehavior: 'foraging',
            avgConfidence: 0.85
        };
    }

    getMockZoneProductivity() {
        return {
            zones: [
                { zone_id: 'lime_kiln', zone_name: 'Lime Kiln Point', success_rate: 0.85, feeding_events_count: 23 },
                { zone_id: 'salmon_bank', zone_name: 'Salmon Bank', success_rate: 0.72, feeding_events_count: 18 }
            ],
            topPerformers: [],
            trends: { increasing: 2, stable: 1, decreasing: 0 }
        };
    }

    async queryBigQuery(query) {
        // Placeholder for BigQuery integration
        console.log('[AnalyticsAgent] Would execute BigQuery:', query);
        return [];
    }
}

/**
 * Vector Space Agent - Viewing zone vector management
 */
class VectorSpaceAgent {
    constructor(config) {
        this.vectorDB = config.vectorDB;
        this.orchestrator = config.orchestrator;
        this.zoneVectors = new Map();
        this.zoneContent = new Map();
    }

    async updateViewingZoneVectors(session) {
        console.log('[VectorAgent] Updating viewing zone vector space...');
        
        const constraints = session.constraints;
        
        // Get all relevant viewing zones
        const zones = await this.getRelevantZones(constraints);
        
        // Update vectors for each zone
        const updatedZones = await Promise.all(
            zones.map(zone => this.updateZoneVector(zone, constraints))
        );

        const vectorSpace = {
            sessionId: session.id,
            zones: updatedZones,
            vectors: this.buildVectorMatrix(updatedZones),
            similarity: this.calculateZoneSimilarity(updatedZones),
            content: this.aggregateZoneContent(updatedZones),
            metadata: {
                totalZones: updatedZones.length,
                vectorDimensions: 128,
                lastUpdated: new Date().toISOString()
            }
        };

        // Emit vector space updated event
        this.orchestrator.eventBus.dispatchEvent(new CustomEvent('vector-space-updated', {
            detail: vectorSpace
        }));

        return vectorSpace;
    }

    async getRelevantZones(constraints) {
        // Get zones relevant to trip constraints
        return [
            {
                id: 'lime_kiln_point',
                name: 'Lime Kiln Point State Park',
                coordinates: { lat: 48.515, lng: -123.152 },
                type: 'land-based',
                probability: 0.85
            },
            {
                id: 'salmon_bank',
                name: 'Salmon Bank',
                coordinates: { lat: 48.524, lng: -123.164 },
                type: 'boat-based', 
                probability: 0.72
            },
            {
                id: 'stuart_island',
                name: 'Stuart Island',
                coordinates: { lat: 48.683, lng: -123.17 },
                type: 'land-based',
                probability: 0.68
            }
        ];
    }

    async updateZoneVector(zone, constraints) {
        // Create vector embedding for the zone
        const vector = await this.generateZoneVector(zone, constraints);
        
        // Get zone content
        const content = await this.getZoneContent(zone.id);
        
        const updatedZone = {
            ...zone,
            vector,
            content,
            environmental: await this.getZoneEnvironmental(zone),
            historical: await this.getZoneHistorical(zone),
            lastUpdated: new Date().toISOString()
        };

        this.zoneVectors.set(zone.id, vector);
        this.zoneContent.set(zone.id, content);

        return updatedZone;
    }

    async generateZoneVector(zone, constraints) {
        // Generate 128-dimensional vector for the zone
        // This would typically use embeddings from recent sightings, environmental data, etc.
        const features = [
            zone.probability,
            zone.coordinates.lat,
            zone.coordinates.lng,
            constraints.duration?.value || 3,
            constraints.groupSize || 1,
            // ... additional features
        ];

        // Pad or truncate to 128 dimensions
        const vector = new Array(128).fill(0);
        features.forEach((feature, index) => {
            if (index < 128) vector[index] = feature;
        });

        return vector;
    }

    getZoneContent(zoneId) {
        // Get available content for a zone
        return {
            photos: this.getMockPhotos(zoneId),
            videos: this.getMockVideos(zoneId),
            descriptions: this.getMockDescriptions(zoneId),
            tips: this.getMockTips(zoneId),
            recentSightings: this.getMockRecentSightings(zoneId)
        };
    }

    findZonesForActivity(activity) {
        // Find zones relevant to a specific activity
        return Array.from(this.zoneVectors.entries())
            .map(([zoneId, vector]) => ({
                id: zoneId,
                similarity: this.calculateActivitySimilarity(activity, vector)
            }))
            .filter(zone => zone.similarity > 0.3)
            .sort((a, b) => b.similarity - a.similarity);
    }

    // Mock content methods
    getMockPhotos(zoneId) {
        return [
            { url: `/photos/${zoneId}_1.jpg`, caption: 'Recent orca sighting' },
            { url: `/photos/${zoneId}_2.jpg`, caption: 'Feeding behavior observed' }
        ];
    }

    getMockVideos(zoneId) {
        return [
            { url: `/videos/${zoneId}_feeding.mp4`, caption: 'Orca feeding sequence' }
        ];
    }

    getMockDescriptions(zoneId) {
        return [
            'Prime viewing location with high probability during flood tides',
            'Best accessed via trail from parking area'
        ];
    }

    getMockTips(zoneId) {
        return [
            'Bring binoculars for distant sightings',
            'Check tide charts before visiting'
        ];
    }

    getMockRecentSightings(zoneId) {
        return [
            { timestamp: '2025-07-18T14:30:00Z', podSize: 8, behavior: 'foraging' },
            { timestamp: '2025-07-18T11:15:00Z', podSize: 12, behavior: 'traveling' }
        ];
    }
}

/**
 * Reasoning Agent - Interpretable planning and explanations
 */
class ReasoningAgent {
    constructor(config) {
        this.geminiIntegration = config.geminiIntegration;
        this.orchestrator = config.orchestrator;
    }

    async prepareReasoningMaterials(session, analytics, vectors) {
        console.log('[ReasoningAgent] Preparing interpretable reasoning materials...');
        
        const reasoning = {
            sessionId: session.id,
            explanations: await this.generateExplanations(session, analytics, vectors),
            justifications: await this.generateJustifications(analytics, vectors),
            alternatives: await this.generateAlternatives(session, analytics),
            confidence: await this.generateConfidenceExplanations(analytics, vectors),
            insights: await this.generateInsights(analytics, vectors),
            metadata: {
                generatedAt: new Date().toISOString(),
                sourcesUsed: ['analytics', 'vectors', 'historical_data']
            }
        };

        // Emit reasoning complete event
        this.orchestrator.eventBus.dispatchEvent(new CustomEvent('reasoning-complete', {
            detail: reasoning
        }));

        return reasoning;
    }

    async generateExplanations(session, analytics, vectors) {
        return {
            tripRationale: await this.explainTripRationale(session, analytics),
            zoneSelections: await this.explainZoneSelections(vectors),
            timingChoices: await this.explainTimingChoices(analytics),
            routeLogic: await this.explainRouteLogic(vectors)
        };
    }

    async explainTripRationale(session, analytics) {
        const constraints = session.constraints;
        return {
            summary: `Based on your ${constraints.duration?.value || 3}-day request, we've optimized for the highest probability orca encounters during this period.`,
            factors: [
                `Current success rate: ${(analytics.success?.rate * 100).toFixed(1)}%`,
                `Dominant behavior: ${analytics.behavior?.dominantBehavior}`,
                `Optimal viewing conditions: ${analytics.environmental?.optimal?.description}`
            ],
            reasoning: 'Trip structure prioritizes high-probability zones during peak activity periods while maintaining flexibility for weather contingencies.'
        };
    }

    async explainZoneSelections(vectors) {
        return vectors.zones.map(zone => ({
            zone: zone.name,
            score: zone.probability,
            reasons: [
                `${(zone.probability * 100).toFixed(1)}% success probability`,
                `${zone.content.recentSightings.length} recent sightings`,
                `Optimal for ${zone.environmental?.optimalConditions || 'current conditions'}`
            ]
        }));
    }
}

// Export the orchestrator
window.MultiAgentOrchestrator = MultiAgentOrchestrator; 