/**
 * ORCAST Multi-Agent Integration Module
 * 
 * Main integration point for the hierarchical trip planning system with:
 * - Multi-agent orchestration
 * - Analytics dashboards  
 * - Vector space management
 * - Hierarchical trip structure
 * - Real-time updates
 */

class ORCASTMultiAgentSystem {
    constructor(config) {
        this.config = {
            // API configurations
            geminiApiKey: config.geminiApiKey,
            firebaseConfig: config.firebaseConfig,
            bigQueryConfig: config.bigQueryConfig,
            
            // Service URLs
            gemmaServiceUrl: config.gemmaServiceUrl,
            
            // Dashboard configuration
            dashboardContainer: config.dashboardContainer || 'orcast-dashboard',
            
            // Features
            enableAnalytics: config.enableAnalytics !== false,
            enableVectorSpace: config.enableVectorSpace !== false,
            enableRealtimeUpdates: config.enableRealtimeUpdates !== false,
            
            ...config
        };
        
        this.components = {};
        this.activeSessions = new Map();
        this.eventBus = new EventTarget();
        
        this.initialize();
    }

    async initialize() {
        console.log('[ORCAST] Initializing multi-agent system...');
        
        try {
            // Initialize core components
            await this.initializeGeminiIntegration();
            await this.initializeTripHierarchyModel();
            await this.initializeMultiAgentOrchestrator();
            await this.initializeAnalyticsDashboard();
            
            // Setup event handlers
            this.setupGlobalEventHandlers();
            
            // Initialize real-time data connections
            if (this.config.enableRealtimeUpdates) {
                await this.initializeRealtimeUpdates();
            }
            
            console.log('[ORCAST] Multi-agent system initialized successfully');
            
            // Emit ready event
            this.eventBus.dispatchEvent(new CustomEvent('orcast-ready', {
                detail: { system: this, capabilities: this.getSystemCapabilities() }
            }));
            
        } catch (error) {
            console.error('[ORCAST] Initialization failed:', error);
            throw new Error(`ORCAST initialization failed: ${error.message}`);
        }
    }

    async initializeGeminiIntegration() {
        console.log('[ORCAST] Initializing Gemini integration...');
        
        this.components.gemini = new GeminiIntegration({
            apiKey: this.config.geminiApiKey,
            gemmaService: {
                baseUrl: this.config.gemmaServiceUrl,
                useGemmaInstead: this.config.useGemmaInstead || false
            }
        });
    }

    async initializeTripHierarchyModel() {
        console.log('[ORCAST] Initializing trip hierarchy model...');
        
        this.components.tripModel = new TripHierarchyModel();
    }

    async initializeMultiAgentOrchestrator() {
        console.log('[ORCAST] Initializing multi-agent orchestrator...');
        
        this.components.orchestrator = new MultiAgentOrchestrator({
            geminiIntegration: this.components.gemini,
            bigQueryClient: this.config.bigQueryConfig,
            firebaseDB: this.config.firebaseConfig,
            vectorDB: this.config.vectorDBConfig
        });
    }

    async initializeAnalyticsDashboard() {
        if (!this.config.enableAnalytics) return;
        
        console.log('[ORCAST] Initializing analytics dashboard...');
        
        this.components.dashboard = new AnalyticsDashboard(
            this.config.dashboardContainer,
            {
                enableRealtime: this.config.enableRealtimeUpdates,
                updateInterval: this.config.dashboardUpdateInterval || 30000
            }
        );
    }

    async initializeRealtimeUpdates() {
        console.log('[ORCAST] Setting up real-time updates...');
        
        // Initialize Firebase real-time listeners
        if (this.config.firebaseConfig) {
            this.setupFirebaseListeners();
        }
        
        // Start periodic data updates
        this.startPeriodicUpdates();
    }

    setupGlobalEventHandlers() {
        // Listen for orchestrator events
        this.components.orchestrator?.eventBus.addEventListener('analytics-ready', (event) => {
            this.handleAnalyticsReady(event.detail);
        });

        this.components.orchestrator?.eventBus.addEventListener('vector-space-updated', (event) => {
            this.handleVectorSpaceUpdate(event.detail);
        });

        this.components.orchestrator?.eventBus.addEventListener('reasoning-complete', (event) => {
            this.handleReasoningComplete(event.detail);
        });

        // Listen for dashboard events
        document.addEventListener('dashboard-action', (event) => {
            this.handleDashboardAction(event.detail);
        });
    }

    /**
     * Main public method: Plan a trip with full multi-agent orchestration
     */
    async planTrip(userInput, options = {}) {
        console.log('[ORCAST] Starting multi-agent trip planning...');
        
        const sessionId = options.sessionId || this.generateSessionId();
        
        try {
            // Step 1: Orchestrate multi-agent planning
            const orchestrationResult = await this.components.orchestrator.orchestrateTripPlanning(
                userInput, 
                sessionId
            );
            
            // Step 2: Build hierarchical trip structure
            const trip = await this.buildTripFromOrchestration(orchestrationResult);
            
            // Step 3: Update dashboard if enabled
            if (this.components.dashboard) {
                this.components.dashboard.updateDashboard(
                    orchestrationResult.analytics,
                    orchestrationResult.vectors,
                    orchestrationResult.reasoning
                );
            }
            
            // Step 4: Store session data
            this.activeSessions.set(sessionId, {
                userInput,
                orchestrationResult,
                trip,
                createdAt: new Date().toISOString(),
                status: 'completed'
            });
            
            // Step 5: Emit trip planned event
            this.eventBus.dispatchEvent(new CustomEvent('trip-planned', {
                detail: {
                    sessionId,
                    trip,
                    analytics: orchestrationResult.analytics,
                    reasoning: orchestrationResult.reasoning
                }
            }));
            
            return {
                sessionId,
                trip,
                analytics: orchestrationResult.analytics,
                reasoning: orchestrationResult.reasoning,
                metadata: orchestrationResult.metadata
            };
            
        } catch (error) {
            console.error('[ORCAST] Trip planning failed:', error);
            
            // Update session with error
            this.activeSessions.set(sessionId, {
                userInput,
                error: error.message,
                createdAt: new Date().toISOString(),
                status: 'failed'
            });
            
            throw error;
        }
    }

    async buildTripFromOrchestration(orchestrationResult) {
        console.log('[ORCAST] Building hierarchical trip structure...');
        
        const { tripPlan, analytics, vectors } = orchestrationResult;
        
        // Create the base trip
        const trip = this.components.tripModel.createTrip({
            title: tripPlan.structure.title,
            duration: tripPlan.structure.duration,
            startDate: tripPlan.structure.startDate,
            constraints: tripPlan.structure.constraints,
            groupSize: tripPlan.structure.groupSize || 1
        });
        
        // Build the hierarchical structure
        for (const dayData of tripPlan.structure.days) {
            const day = this.components.tripModel.addDay(trip, {
                theme: dayData.theme,
                weather: dayData.weather,
                tidalConditions: dayData.tidalConditions
            });
            
            for (const dayTripData of dayData.dayTrips) {
                const dayTrip = this.components.tripModel.addDayTrip(day, {
                    title: dayTripData.title,
                    startTime: dayTripData.startTime,
                    endTime: dayTripData.endTime,
                    type: dayTripData.type,
                    cost: dayTripData.cost,
                    reasoning: dayTripData.reasoning
                });
                
                for (const stopData of dayTripData.stops) {
                    const stop = this.components.tripModel.addStop(dayTrip, {
                        name: stopData.name,
                        coordinates: stopData.coordinates,
                        duration: stopData.duration,
                        probabilityScore: stopData.probabilityScore
                    });
                    
                    for (const activityData of stopData.activities) {
                        const activity = this.components.tripModel.addActivity(stop, {
                            title: activityData.title,
                            type: activityData.type,
                            duration: activityData.duration,
                            expectedBehaviors: activityData.expectedBehaviors
                        });
                        
                        for (const zoneData of activityData.viewingZones) {
                            this.components.tripModel.addViewingZone(activity, {
                                name: zoneData.name,
                                coordinates: zoneData.coordinates,
                                probability: zoneData.probability,
                                confidence: zoneData.confidence,
                                content: zoneData.content,
                                vectorEmbedding: zoneData.vectorEmbedding
                            });
                        }
                    }
                }
            }
        }
        
        return trip;
    }

    /**
     * Get trip by session ID
     */
    getTrip(sessionId) {
        const session = this.activeSessions.get(sessionId);
        return session?.trip || null;
    }

    /**
     * Update trip with new information
     */
    async updateTrip(sessionId, updates) {
        const session = this.activeSessions.get(sessionId);
        if (!session) {
            throw new Error(`Session ${sessionId} not found`);
        }
        
        // Apply updates to the trip
        const trip = session.trip;
        Object.assign(trip, updates);
        
        // Recalculate metadata
        this.components.tripModel.updateTripMetadata(trip);
        
        // Update dashboard
        if (this.components.dashboard) {
            this.components.dashboard.updateTripStatistics(session.analytics, session.vectors);
        }
        
        // Emit update event
        this.eventBus.dispatchEvent(new CustomEvent('trip-updated', {
            detail: { sessionId, trip, updates }
        }));
        
        return trip;
    }

    /**
     * Get all viewing zones with high probability
     */
    getHighProbabilityZones(sessionId, minProbability = 0.7) {
        const session = this.activeSessions.get(sessionId);
        if (!session?.trip) return [];
        
        return this.components.tripModel.findViewingZonesByProbability(
            session.trip, 
            minProbability
        );
    }

    /**
     * Get recommendations for a specific day
     */
    async getDayRecommendations(sessionId, dayNumber) {
        const session = this.activeSessions.get(sessionId);
        if (!session) return [];
        
        const day = session.trip.days[dayNumber - 1];
        if (!day) return [];
        
        // Use analytics agent to generate fresh recommendations
        return await this.components.orchestrator.agents.analytics.generateDayRecommendations(
            day, 
            session.orchestrationResult.analytics
        );
    }

    /**
     * Real-time event handlers
     */
    handleAnalyticsReady(analyticsData) {
        console.log('[ORCAST] Analytics ready for session:', analyticsData.sessionId);
        
        if (this.components.dashboard) {
            this.components.dashboard.updateDashboard(analyticsData, null, null);
        }
    }

    handleVectorSpaceUpdate(vectorData) {
        console.log('[ORCAST] Vector space updated for session:', vectorData.sessionId);
        
        if (this.components.dashboard) {
            this.components.dashboard.updateZoneAnalytics(vectorData);
        }
    }

    handleReasoningComplete(reasoningData) {
        console.log('[ORCAST] Reasoning complete for session:', reasoningData.sessionId);
        
        if (this.components.dashboard) {
            this.components.dashboard.updateAgentReasoning(reasoningData);
        }
    }

    handleDashboardAction(action) {
        console.log('[ORCAST] Dashboard action:', action);
        
        switch (action.type) {
            case 'refresh-data':
                this.refreshDashboardData();
                break;
            case 'update-trip':
                this.updateTrip(action.sessionId, action.updates);
                break;
            case 'get-recommendations':
                this.getDayRecommendations(action.sessionId, action.dayNumber);
                break;
        }
    }

    async refreshDashboardData() {
        if (this.components.dashboard) {
            // Refresh with latest data from all active sessions
            const latestSession = Array.from(this.activeSessions.values())
                .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))[0];
            
            if (latestSession) {
                this.components.dashboard.updateDashboard(
                    latestSession.orchestrationResult.analytics,
                    latestSession.orchestrationResult.vectors,
                    latestSession.orchestrationResult.reasoning
                );
            }
        }
    }

    setupFirebaseListeners() {
        // Setup Firebase real-time database listeners for live updates
        if (typeof firebase !== 'undefined' && firebase.database) {
            const db = firebase.database();
            
            // Listen for orca sightings
            db.ref('orcaSightings').on('child_added', (snapshot) => {
                this.handleNewSighting(snapshot.val());
            });
            
            // Listen for environmental updates
            db.ref('environmentalData').on('value', (snapshot) => {
                this.handleEnvironmentalUpdate(snapshot.val());
            });
        }
    }

    startPeriodicUpdates() {
        // Update dashboard every 30 seconds
        setInterval(() => {
            this.refreshDashboardData();
        }, this.config.dashboardUpdateInterval || 30000);
    }

    handleNewSighting(sighting) {
        console.log('[ORCAST] New orca sighting:', sighting);
        
        // Update dashboard with new sighting
        if (this.components.dashboard) {
            this.components.dashboard.widgets.updates.addUpdate({
                timestamp: new Date(),
                type: 'sighting',
                message: `New orca sighting: ${sighting.count} orcas at ${sighting.location}`
            });
        }
        
        // Emit sighting event
        this.eventBus.dispatchEvent(new CustomEvent('new-sighting', {
            detail: sighting
        }));
    }

    handleEnvironmentalUpdate(envData) {
        console.log('[ORCAST] Environmental data updated');
        
        // Update dashboard environmental conditions
        if (this.components.dashboard) {
            this.components.dashboard.updateEnvironmentalConditions({
                environmental: { current: envData }
            });
        }
    }

    generateSessionId() {
        return `orcast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    getSystemCapabilities() {
        return {
            multiAgentOrchestration: true,
            hierarchicalTripPlanning: true,
            analyticsSupport: this.config.enableAnalytics,
            vectorSpaceManagement: this.config.enableVectorSpace,
            realtimeUpdates: this.config.enableRealtimeUpdates,
            geminiIntegration: !!this.config.geminiApiKey,
            gemmaGPUService: !!this.config.gemmaServiceUrl,
            dashboardVisualization: !!this.components.dashboard
        };
    }

    /**
     * Export trip data
     */
    exportTrip(sessionId, format = 'json') {
        const session = this.activeSessions.get(sessionId);
        if (!session?.trip) {
            throw new Error(`Trip not found for session ${sessionId}`);
        }
        
        switch (format) {
            case 'json':
                return this.components.tripModel.exportTrip(session.trip);
            case 'summary':
                return this.generateTripSummary(session.trip);
            default:
                throw new Error(`Unsupported export format: ${format}`);
        }
    }

    generateTripSummary(trip) {
        const zones = this.components.tripModel.findViewingZonesByProbability(trip, 0);
        const activities = this.components.tripModel.findActivitiesByType(trip, 'viewing');
        
        return {
            tripId: trip.id,
            title: trip.title,
            duration: trip.duration,
            totalCost: trip.totalCost,
            overallProbability: trip.overallProbability,
            confidence: trip.confidence,
            totalZones: zones.length,
            totalActivities: activities.length,
            highProbabilityZones: zones.filter(z => z.probability >= 0.7).length,
            summary: `${trip.duration}-day orca watching adventure with ${zones.length} viewing zones and ${(trip.overallProbability * 100).toFixed(1)}% success probability`
        };
    }
}

/**
 * Global initialization function
 */
window.initializeORCAST = function(config) {
    return new ORCASTMultiAgentSystem(config);
};

// Export the main system
window.ORCASTMultiAgentSystem = ORCASTMultiAgentSystem; 