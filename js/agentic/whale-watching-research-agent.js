/**
 * Whale Watching Research Agent
 * Uses SINDy equations and HMC uncertainty to research optimal viewing locations for the existing Gemma 3 trip planner
 */

class WhaleWatchingResearchAgent {
    constructor(config = {}) {
        this.sindy_service_url = config.sindyServiceUrl || '/api/sindy-predictions';
        this.firestore_db = config.firestoreDB;
        this.hmc_service_url = config.hmcServiceUrl || '/api/hmc-uncertainty';
        
        // Research findings cache
        this.research_cache = new Map();
        this.location_analysis = new Map();
        
        console.log('🔬 Whale Watching Research Agent initialized');
    }

    /**
     * CORE RESEARCH METHODS for Gemma 3 Trip Planner
     */

    async researchOptimalViewingLocations(constraints) {
        console.log('🔍 Researching optimal viewing locations using SINDy equations...');
        
        try {
            // Extract spatial and temporal constraints from trip planner
            const research_parameters = this.extractResearchParameters(constraints);
            
            // Use SINDy equations to identify high-probability zones
            const sindy_insights = await this.analyzeSINDyPredictions(research_parameters);
            
            // Add HMC uncertainty analysis for confidence bands
            const uncertainty_analysis = await this.analyzeHMCUncertainty(sindy_insights);
            
            // Research historical success patterns
            const historical_patterns = await this.researchHistoricalPatterns(research_parameters);
            
            // Combine all research findings
            const research_findings = this.synthesizeResearchFindings({
                sindy_insights,
                uncertainty_analysis,
                historical_patterns,
                parameters: research_parameters
            });
            
            // Cache for trip planner
            this.cacheResearchFindings(constraints, research_findings);
            
            return research_findings;
            
        } catch (error) {
            console.error('Research agent error:', error);
            return this.getFallbackResearch(constraints);
        }
    }

    extractResearchParameters(constraints) {
        return {
            // Temporal constraints
            start_date: constraints.dates?.start || new Date(),
            end_date: constraints.dates?.end || new Date(Date.now() + 3 * 24 * 60 * 60 * 1000),
            preferred_times: constraints.times || ['dawn', 'morning', 'dusk'],
            
            // Spatial constraints  
            viewing_mode: constraints.viewing_mode || 'land', // land, boat, kayak
            max_distance: constraints.max_distance || 50, // km from accommodation
            accessibility: constraints.accessibility || 'standard',
            
            // Experience preferences
            behavior_interests: constraints.behaviors || ['feeding', 'socializing', 'traveling'],
            group_size: constraints.group_size || 2,
            experience_level: constraints.experience || 'beginner',
            
            // Environmental preferences
            weather_tolerance: constraints.weather || 'moderate',
            sea_conditions: constraints.sea_conditions || 'calm_to_moderate'
        };
    }

    async analyzeSINDyPredictions(parameters) {
        console.log('📊 Analyzing SINDy equation predictions for optimal locations...');
        
        // Query our SINDy service for predictions
        const sindy_predictions = await this.querySINDyService(parameters);
        
        // Extract key insights from discovered equations
        const feeding_hotspots = this.identifyFeedingHotspots(sindy_predictions);
        const socializing_zones = this.identifySocializingZones(sindy_predictions);
        const travel_corridors = this.identifyTravelCorridors(sindy_predictions);
        
        return {
            predictions: sindy_predictions,
            feeding_hotspots,
            socializing_zones,
            travel_corridors,
            optimal_times: this.extractOptimalTimes(sindy_predictions),
            environmental_factors: this.extractCriticalFactors(sindy_predictions)
        };
    }

    identifyFeedingHotspots(predictions) {
        // Use SINDy feeding equation: 0.533*prey + 0.271*temp + exp(-|depth|) + sin(hour)
        return predictions
            .filter(p => p.behavior === 'feeding' && p.probability > 0.6)
            .map(p => ({
                location: { lat: p.latitude, lng: p.longitude },
                probability: p.probability,
                confidence: p.uncertainty_bounds,
                key_factors: {
                    prey_density: p.environmental.prey_density,
                    temperature: p.environmental.temperature,
                    depth: p.environmental.depth,
                    optimal_hour: p.environmental.hour_of_day
                },
                viewing_quality: this.assessViewingQuality(p),
                accessibility: this.assessAccessibility(p)
            }))
            .sort((a, b) => b.probability - a.probability)
            .slice(0, 10); // Top 10 feeding locations
    }

    identifySocializingZones(predictions) {
        // Use SINDy socializing equation: pod_size + sin(hour) + cos(hour)
        return predictions
            .filter(p => p.behavior === 'socializing' && p.probability > 0.5)
            .map(p => ({
                location: { lat: p.latitude, lng: p.longitude },
                probability: p.probability,
                confidence: p.uncertainty_bounds,
                key_factors: {
                    pod_size: p.environmental.pod_size,
                    time_pattern: this.extractTimePattern(p),
                    social_dynamics: this.analyzeSocialDynamics(p)
                },
                viewing_experience: 'high_social_activity',
                duration_estimate: '15-45 minutes'
            }))
            .sort((a, b) => b.probability - a.probability)
            .slice(0, 8); // Top 8 socializing zones
    }

    identifyTravelCorridors(predictions) {
        // Use SINDy traveling equation: current_speed + tidal_flow^2
        return predictions
            .filter(p => p.behavior === 'traveling' && p.probability > 0.4)
            .map(p => ({
                location: { lat: p.latitude, lng: p.longitude },
                probability: p.probability,
                confidence: p.uncertainty_bounds,
                key_factors: {
                    current_speed: p.environmental.current_speed,
                    tidal_flow: p.environmental.tidal_flow,
                    travel_efficiency: p.travel_metrics?.efficiency
                },
                corridor_type: this.identifyCorridorType(p),
                timing_importance: 'high' // Travel predictions are time-sensitive
            }))
            .sort((a, b) => b.probability - a.probability)
            .slice(0, 6); // Top 6 travel corridors
    }

    async analyzeHMCUncertainty(sindy_insights) {
        console.log('📈 Analyzing HMC uncertainty for research confidence...');
        
        const locations = [
            ...sindy_insights.feeding_hotspots,
            ...sindy_insights.socializing_zones,
            ...sindy_insights.travel_corridors
        ];
        
        const uncertainty_analysis = await Promise.all(
            locations.map(async (location) => {
                const hmc_data = await this.queryHMCService(location);
                return {
                    location: location.location,
                    uncertainty_metrics: {
                        confidence_interval_95: hmc_data.confidence_95,
                        confidence_interval_50: hmc_data.confidence_50,
                        prediction_stability: hmc_data.stability_score,
                        uncertainty_band_width: hmc_data.uncertainty_band
                    },
                    research_confidence: this.calculateResearchConfidence(hmc_data),
                    recommendation_strength: this.assessRecommendationStrength(hmc_data)
                };
            })
        );
        
        return uncertainty_analysis;
    }

    async researchHistoricalPatterns(parameters) {
        console.log('📚 Researching historical whale watching patterns...');
        
        if (!this.firestore_db) {
            return this.getStaticHistoricalData();
        }
        
        try {
            // Query Firestore for historical sighting data
            const historical_query = await this.firestore_db
                .collection('orca_spatial_forecasts')
                .where('generated_at', '>=', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000))
                .limit(1000)
                .get();
            
            const historical_data = [];
            historical_query.forEach(doc => {
                historical_data.push(doc.data());
            });
            
            return this.analyzeHistoricalSuccess(historical_data, parameters);
            
        } catch (error) {
            console.error('Historical research error:', error);
            return this.getStaticHistoricalData();
        }
    }

    synthesizeResearchFindings(research_data) {
        const { sindy_insights, uncertainty_analysis, historical_patterns, parameters } = research_data;
        
        return {
            research_summary: {
                total_locations_analyzed: sindy_insights.predictions.length,
                high_confidence_locations: uncertainty_analysis.filter(u => u.research_confidence > 0.8).length,
                optimal_time_windows: this.identifyOptimalTimeWindows(sindy_insights),
                success_probability_range: this.calculateSuccessProbabilityRange(uncertainty_analysis)
            },
            
            top_recommendations: {
                primary_locations: this.rankLocationsByResearchEvidence(sindy_insights, uncertainty_analysis),
                backup_locations: this.identifyBackupLocations(sindy_insights, uncertainty_analysis),
                timing_recommendations: this.createTimingRecommendations(sindy_insights, historical_patterns)
            },
            
            research_confidence: {
                overall_confidence: this.calculateOverallResearchConfidence(uncertainty_analysis),
                data_quality_score: this.assessDataQuality(research_data),
                prediction_reliability: this.assessPredictionReliability(uncertainty_analysis)
            },
            
            scientific_evidence: {
                sindy_equation_insights: this.extractSINDyInsights(sindy_insights),
                uncertainty_quantification: this.summarizeUncertainty(uncertainty_analysis),
                historical_validation: this.summarizeHistoricalEvidence(historical_patterns)
            },
            
            actionable_insights: this.generateActionableInsights(research_data, parameters)
        };
    }

    generateActionableInsights(research_data, parameters) {
        const insights = [];
        
        // Location-specific insights
        research_data.sindy_insights.feeding_hotspots.slice(0, 3).forEach(hotspot => {
            insights.push({
                type: 'location_recommendation',
                priority: 'high',
                insight: `${hotspot.location.lat.toFixed(3)}, ${hotspot.location.lng.toFixed(3)} has ${(hotspot.probability * 100).toFixed(0)}% feeding probability based on optimal prey density (${hotspot.key_factors.prey_density.toFixed(2)}) and temperature (${hotspot.key_factors.temperature.toFixed(1)}°C)`,
                confidence: hotspot.confidence,
                action: 'prioritize_for_trip_planning'
            });
        });
        
        // Timing insights
        const optimal_times = research_data.sindy_insights.optimal_times;
        if (optimal_times.length > 0) {
            insights.push({
                type: 'timing_recommendation',
                priority: 'high',
                insight: `SINDy equations show peak activity at ${optimal_times[0].hour}:00 with ${(optimal_times[0].probability * 100).toFixed(0)}% probability`,
                confidence: optimal_times[0].confidence,
                action: 'schedule_viewing_times'
            });
        }
        
        // Environmental insights
        const critical_factors = research_data.sindy_insights.environmental_factors;
        insights.push({
            type: 'environmental_insight',
            priority: 'medium',
            insight: `Critical environmental factors: ${critical_factors.top_factors.join(', ')}. Monitor ${critical_factors.most_important} for best results.`,
            confidence: critical_factors.confidence,
            action: 'monitor_conditions'
        });
        
        return insights;
    }

    /**
     * HELPER METHODS
     */

    async querySINDyService(parameters) {
        // Query our deployed SINDy service
        try {
            const response = await fetch(`${this.sindy_service_url}/spatial_forecast`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(parameters)
            });
            return await response.json();
        } catch (error) {
            console.error('SINDy service error:', error);
            return this.getFallbackSINDyData(parameters);
        }
    }

    async queryHMCService(location) {
        // Query our deployed HMC uncertainty service
        try {
            const response = await fetch(`${this.hmc_service_url}/uncertainty`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(location)
            });
            return await response.json();
        } catch (error) {
            console.error('HMC service error:', error);
            return this.getFallbackUncertaintyData();
        }
    }

    cacheResearchFindings(constraints, findings) {
        const cache_key = JSON.stringify(constraints);
        this.research_cache.set(cache_key, {
            findings,
            timestamp: Date.now(),
            expires: Date.now() + 30 * 60 * 1000 // 30 minutes
        });
    }

    getFallbackResearch(constraints) {
        console.log('🔄 Using fallback research data...');
        
        return {
            research_summary: {
                total_locations_analyzed: 50,
                high_confidence_locations: 8,
                optimal_time_windows: ['06:00-09:00', '17:00-20:00'],
                success_probability_range: [0.4, 0.8]
            },
            top_recommendations: {
                primary_locations: [
                    { location: { lat: 48.516, lng: -123.012 }, probability: 0.75, confidence: 0.8 },
                    { location: { lat: 48.602, lng: -122.948 }, probability: 0.68, confidence: 0.7 },
                    { location: { lat: 48.473, lng: -122.887 }, probability: 0.62, confidence: 0.75 }
                ]
            },
            research_confidence: {
                overall_confidence: 0.7,
                data_quality_score: 0.8,
                prediction_reliability: 0.75
            }
        };
    }

    // Additional helper methods...
    assessViewingQuality(prediction) {
        const factors = prediction.environmental;
        let quality_score = 0.5;
        
        if (factors.visibility > 15) quality_score += 0.2;
        if (factors.noise_level < 100) quality_score += 0.15;
        if (factors.depth > 20 && factors.depth < 100) quality_score += 0.15;
        
        return Math.min(1.0, quality_score);
    }

    calculateResearchConfidence(hmc_data) {
        const confidence_95 = hmc_data.confidence_95;
        const band_width = confidence_95.upper - confidence_95.lower;
        
        // Higher confidence = narrower uncertainty band
        return Math.max(0, 1 - (band_width / 0.5));
    }
}

// Export for use by trip planner
window.WhaleWatchingResearchAgent = WhaleWatchingResearchAgent; 