/**
 * Whale Watching Planner Agent
 * Creates sustainable viewing routes using SINDy research and HMC uncertainty data
 * Supports the existing Gemma 3 trip planning agent
 */

class WhaleWatchingPlannerAgent {
    constructor(config = {}) {
        this.research_agent = config.researchAgent || new WhaleWatchingResearchAgent(config);
        this.google_maps_api = config.googleMapsAPI;
        this.sustainability_weights = config.sustainabilityWeights || {
            environmental_impact: 0.3,
            wildlife_disturbance: 0.4,
            community_benefit: 0.2,
            educational_value: 0.1
        };
        
        // Route planning cache
        this.route_cache = new Map();
        this.optimization_cache = new Map();
        
        console.log('📋 Whale Watching Planner Agent initialized');
    }

    /**
     * CORE PLANNING METHODS for Gemma 3 Trip Planner
     */

    async planSustainableViewingRoutes(constraints, research_findings) {
        console.log('🗺️ Planning sustainable whale watching routes...');
        
        try {
            // Extract planning parameters from constraints
            const planning_params = this.extractPlanningParameters(constraints);
            
            // Create route options using research findings
            const route_options = await this.createRouteOptions(research_findings, planning_params);
            
            // Optimize routes for sustainability
            const optimized_routes = await this.optimizeForSustainability(route_options, planning_params);
            
            // Add timing and logistics
            const detailed_routes = await this.addRouteTiming(optimized_routes, research_findings);
            
            // Generate contingency plans
            const contingency_plans = await this.generateContingencyPlans(detailed_routes, research_findings);
            
            // Compile final route plan
            const final_plan = this.compileRoutePlan({
                primary_routes: detailed_routes,
                contingency_plans,
                research_evidence: research_findings,
                sustainability_metrics: this.calculateSustainabilityMetrics(detailed_routes)
            });
            
            // Cache for trip planner
            this.cacheRoutePlan(constraints, final_plan);
            
            return final_plan;
            
        } catch (error) {
            console.error('Planner agent error:', error);
            return this.getFallbackPlan(constraints);
        }
    }

    extractPlanningParameters(constraints) {
        return {
            // Trip structure
            trip_duration: constraints.duration || 3, // days
            daily_viewing_hours: constraints.viewing_hours || 6,
            travel_budget_hours: constraints.travel_time || 3, // max travel per day
            
            // Sustainability requirements
            max_daily_distance: constraints.max_distance || 100, // km
            group_size: constraints.group_size || 4,
            environmental_priority: constraints.sustainability || 'high',
            
            // Viewing preferences
            viewing_modes: constraints.viewing_modes || ['land', 'boat'],
            accessibility_needs: constraints.accessibility || [],
            photography_interests: constraints.photography || false,
            
            // Logistics
            accommodation_base: constraints.accommodation || { lat: 48.516, lng: -123.012 },
            transportation_mode: constraints.transport || 'car',
            meal_preferences: constraints.meals || 'local'
        };
    }

    async createRouteOptions(research_findings, params) {
        console.log('🛣️ Creating route options from research findings...');
        
        const primary_locations = research_findings.top_recommendations.primary_locations;
        const backup_locations = research_findings.top_recommendations.backup_locations;
        
        // Create different route strategies
        const route_strategies = [
            this.createHighProbabilityRoute(primary_locations, params),
            this.createDiverseBehaviorRoute(research_findings, params),
            this.createSustainabilityOptimizedRoute(primary_locations, params),
            this.createWeatherContingencyRoute(backup_locations, params)
        ];
        
        // Evaluate each route option
        const evaluated_routes = await Promise.all(
            route_strategies.map(async (route) => {
                const evaluation = await this.evaluateRoute(route, research_findings);
                return { ...route, evaluation };
            })
        );
        
        return evaluated_routes.sort((a, b) => b.evaluation.overall_score - a.evaluation.overall_score);
    }

    createHighProbabilityRoute(locations, params) {
        // Route focusing on highest probability locations
        const sorted_locations = locations
            .sort((a, b) => b.probability - a.probability)
            .slice(0, Math.min(6, locations.length));
        
        return {
            strategy: 'high_probability',
            name: 'Maximum Success Route',
            locations: sorted_locations.map((loc, index) => ({
                ...loc,
                sequence: index + 1,
                visit_duration: this.calculateOptimalVisitTime(loc),
                travel_time: index > 0 ? this.estimateTravelTime(sorted_locations[index-1], loc) : 0
            })),
            target_behaviors: ['feeding', 'socializing'],
            success_probability: this.calculateRouteSuccessProbability(sorted_locations),
            sustainability_score: 0.7 // Will be calculated properly later
        };
    }

    createDiverseBehaviorRoute(research_findings, params) {
        // Route that covers different orca behaviors
        const feeding_spots = research_findings.sindy_insights.feeding_hotspots.slice(0, 2);
        const social_zones = research_findings.sindy_insights.socializing_zones.slice(0, 2);
        const travel_corridors = research_findings.sindy_insights.travel_corridors.slice(0, 1);
        
        const diverse_locations = [
            ...feeding_spots.map(l => ({ ...l, primary_behavior: 'feeding' })),
            ...social_zones.map(l => ({ ...l, primary_behavior: 'socializing' })),
            ...travel_corridors.map(l => ({ ...l, primary_behavior: 'traveling' }))
        ];
        
        return {
            strategy: 'diverse_behavior',
            name: 'Complete Orca Experience Route',
            locations: this.optimizeLocationSequence(diverse_locations, params.accommodation_base),
            target_behaviors: ['feeding', 'socializing', 'traveling'],
            educational_value: 0.9,
            sustainability_score: 0.8
        };
    }

    createSustainabilityOptimizedRoute(locations, params) {
        // Route optimized for minimal environmental impact
        const base = params.accommodation_base;
        
        // Sort by distance from accommodation to minimize travel
        const local_locations = locations
            .map(loc => ({
                ...loc,
                distance_from_base: this.calculateDistance(base, loc.location)
            }))
            .sort((a, b) => a.distance_from_base - b.distance_from_base)
            .slice(0, 4); // Fewer locations, more time at each
        
        return {
            strategy: 'sustainability_optimized',
            name: 'Eco-Friendly Local Route',
            locations: local_locations.map((loc, index) => ({
                ...loc,
                sequence: index + 1,
                visit_duration: '3-4 hours', // Longer stays
                sustainable_practices: this.getSustainablePractices(loc)
            })),
            environmental_impact: 'minimal',
            carbon_footprint: this.calculateCarbonFootprint(local_locations),
            sustainability_score: 0.95
        };
    }

    async optimizeForSustainability(route_options, params) {
        console.log('🌱 Optimizing routes for sustainability...');
        
        return await Promise.all(
            route_options.map(async (route) => {
                // Calculate sustainability metrics
                const sustainability_metrics = await this.calculateDetailedSustainabilityMetrics(route);
                
                // Optimize location sequence for minimal travel
                const optimized_sequence = this.optimizeLocationSequence(route.locations, params.accommodation_base);
                
                // Add sustainable viewing practices
                const sustainable_practices = this.addSustainablePractices(route, params);
                
                // Calculate environmental impact
                const environmental_impact = this.calculateEnvironmentalImpact(route, params);
                
                return {
                    ...route,
                    locations: optimized_sequence,
                    sustainability_metrics,
                    sustainable_practices,
                    environmental_impact,
                    sustainability_optimized: true
                };
            })
        );
    }

    async addRouteTiming(routes, research_findings) {
        console.log('⏰ Adding optimal timing to routes...');
        
        return routes.map(route => {
            const timed_locations = route.locations.map(location => {
                // Use SINDy insights for optimal timing
                const optimal_times = this.extractLocationOptimalTimes(location, research_findings);
                
                return {
                    ...location,
                    recommended_arrival: optimal_times.best_arrival,
                    optimal_viewing_window: optimal_times.viewing_window,
                    tide_considerations: optimal_times.tidal_factors,
                    weather_window: optimal_times.weather_factors,
                    uncertainty_buffer: this.calculateTimingUncertainty(location, research_findings)
                };
            });
            
            // Calculate daily schedule
            const daily_schedule = this.createDailySchedule(timed_locations, route.strategy);
            
            return {
                ...route,
                locations: timed_locations,
                daily_schedule,
                total_duration: this.calculateTotalDuration(daily_schedule),
                timing_confidence: this.calculateTimingConfidence(timed_locations, research_findings)
            };
        });
    }

    async generateContingencyPlans(routes, research_findings) {
        console.log('🔄 Generating contingency plans...');
        
        const contingencies = [];
        
        // Weather contingencies
        contingencies.push({
            trigger: 'poor_weather',
            name: 'Indoor/Sheltered Viewing Plan',
            alternative_locations: this.identifyShelteredLocations(research_findings),
            modified_schedule: 'flexible_timing',
            backup_activities: ['visitor_center', 'marine_education', 'local_culture']
        });
        
        // Low orca activity contingencies
        contingencies.push({
            trigger: 'low_orca_activity',
            name: 'Wildlife Diversity Plan',
            alternative_focus: ['seals', 'sea_lions', 'dolphins', 'seabirds'],
            modified_expectations: 'broader_marine_life',
            educational_opportunities: this.getAlternativeEducation()
        });
        
        // High uncertainty contingencies
        const high_uncertainty_locations = research_findings.top_recommendations.backup_locations;
        contingencies.push({
            trigger: 'high_prediction_uncertainty',
            name: 'Conservative Success Plan',
            conservative_locations: high_uncertainty_locations.filter(l => l.confidence > 0.8),
            longer_stays: true,
            patience_strategy: 'extended_observation'
        });
        
        return contingencies;
    }

    compileRoutePlan(plan_data) {
        const { primary_routes, contingency_plans, research_evidence, sustainability_metrics } = plan_data;
        
        return {
            route_recommendations: {
                primary_route: primary_routes[0],
                alternative_routes: primary_routes.slice(1, 3),
                route_comparison: this.compareRoutes(primary_routes)
            },
            
            timing_strategy: {
                optimal_schedules: this.extractOptimalSchedules(primary_routes),
                flexibility_windows: this.calculateFlexibilityWindows(primary_routes),
                weather_adaptations: this.createWeatherAdaptations(primary_routes)
            },
            
            sustainability_plan: {
                environmental_commitments: this.createEnvironmentalCommitments(sustainability_metrics),
                sustainable_practices: this.compileSustainablePractices(primary_routes),
                community_engagement: this.identifyCommu‌nityEngagement(primary_routes),
                carbon_offset_suggestions: this.calculateCarbonOffsets(sustainability_metrics)
            },
            
            contingency_strategies: contingency_plans,
            
            scientific_backing: {
                sindy_evidence: research_evidence.scientific_evidence.sindy_equation_insights,
                uncertainty_analysis: research_evidence.scientific_evidence.uncertainty_quantification,
                confidence_levels: research_evidence.research_confidence
            },
            
            success_metrics: {
                predicted_success_rate: this.calculateOverallSuccessRate(primary_routes),
                experience_quality_score: this.calculateExperienceQuality(primary_routes),
                learning_outcome_potential: this.assessLearningOutcomes(primary_routes)
            },
            
            logistics_support: {
                transportation_optimization: this.optimizeTransportation(primary_routes),
                accommodation_recommendations: this.getAccommodationRecommendations(primary_routes),
                equipment_suggestions: this.getEquipmentSuggestions(primary_routes),
                local_guide_connections: this.getLocalGuideRecommendations(primary_routes)
            }
        };
    }

    /**
     * HELPER METHODS
     */

    calculateOptimalVisitTime(location) {
        // Use SINDy insights and HMC uncertainty to determine visit duration
        const probability = location.probability;
        const confidence = location.confidence;
        
        if (probability > 0.8 && confidence > 0.8) return '1-2 hours';
        if (probability > 0.6 && confidence > 0.7) return '2-3 hours';
        return '3-4 hours'; // Lower probability = longer stay needed
    }

    optimizeLocationSequence(locations, base) {
        // Simple nearest-neighbor optimization (could be enhanced with TSP algorithm)
        const optimized = [locations[0]]; // Start with first location
        const remaining = [...locations.slice(1)];
        let current = locations[0];
        
        while (remaining.length > 0) {
            // Find nearest unvisited location
            let nearest = remaining[0];
            let min_distance = this.calculateDistance(current.location, nearest.location);
            
            for (let i = 1; i < remaining.length; i++) {
                const distance = this.calculateDistance(current.location, remaining[i].location);
                if (distance < min_distance) {
                    min_distance = distance;
                    nearest = remaining[i];
                }
            }
            
            optimized.push(nearest);
            remaining.splice(remaining.indexOf(nearest), 1);
            current = nearest;
        }
        
        return optimized.map((loc, index) => ({ ...loc, sequence: index + 1 }));
    }

    calculateDistance(point1, point2) {
        // Haversine formula for distance calculation
        const R = 6371; // Earth's radius in km
        const dLat = (point2.lat - point1.lat) * Math.PI / 180;
        const dLng = (point2.lng - point1.lng) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(point1.lat * Math.PI / 180) * Math.cos(point2.lat * Math.PI / 180) *
                  Math.sin(dLng/2) * Math.sin(dLng/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    getFallbackPlan(constraints) {
        console.log('🔄 Using fallback route plan...');
        
        return {
            route_recommendations: {
                primary_route: {
                    strategy: 'conservative',
                    name: 'San Juan Islands Classic Route',
                    locations: [
                        { location: { lat: 48.516, lng: -123.012 }, name: 'San Juan Island West Side' },
                        { location: { lat: 48.602, lng: -122.948 }, name: 'Orcas Island North' },
                        { location: { lat: 48.473, lng: -122.887 }, name: 'Lopez Island South' }
                    ],
                    success_probability: 0.65
                }
            },
            sustainability_plan: {
                environmental_commitments: ['minimal_disturbance', 'local_economy_support'],
                sustainable_practices: ['quiet_observation', 'pack_out_trash']
            }
        };
    }

    cacheRoutePlan(constraints, plan) {
        const cache_key = JSON.stringify(constraints);
        this.route_cache.set(cache_key, {
            plan,
            timestamp: Date.now(),
            expires: Date.now() + 60 * 60 * 1000 // 1 hour
        });
    }
}

// Export for use by trip planner
window.WhaleWatchingPlannerAgent = WhaleWatchingPlannerAgent; 