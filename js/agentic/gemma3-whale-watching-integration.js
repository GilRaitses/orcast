/**
 * Gemma 3 Whale Watching Integration
 * Connects SINDy + HMC research and planning agents to the existing Gemma 3 trip planner
 * 
 * This enhances the existing trip planner with scientific equation-based route optimization
 */

class Gemma3WhaleWatchingIntegration {
    constructor(config = {}) {
        // Connect to existing Gemma 3 system
        this.gemma3_planner = config.existingGemmaPla‌nner || window.agenticPlanner;
        this.multi_agent_orchestrator = config.orchestrator || window.multiAgentOrchestrator;
        
        // Initialize our scientific agents
        this.research_agent = new WhaleWatchingResearchAgent({
            sindyServiceUrl: config.sindyServiceUrl || '/api/sindy-predictions',
            hmcServiceUrl: config.hmcServiceUrl || '/api/hmc-uncertainty',
            firestoreDB: config.firestoreDB
        });
        
        this.planner_agent = new WhaleWatchingPlannerAgent({
            researchAgent: this.research_agent,
            googleMapsAPI: config.googleMapsAPI
        });
        
        // Integration state
        this.current_research = null;
        this.current_plan = null;
        this.enhancement_active = true;
        
        console.log('🌊 Gemma 3 Whale Watching Integration initialized');
        this.integrateWithExistingSystem();
    }

    /**
     * MAIN INTEGRATION METHODS
     */

    integrateWithExistingSystem() {
        // Hook into existing Gemma 3 trip planning flow
        if (this.gemma3_planner && typeof this.gemma3_planner.planTrip === 'function') {
            this.enhanceGemma3Planning();
        }
        
        if (this.multi_agent_orchestrator) {
            this.integrateWithOrchestrator();
        }
        
        // Add scientific enhancement UI controls
        this.addScientificEnhancementControls();
    }

    enhanceGemma3Planning() {
        // Store original planning method
        const original_planTrip = this.gemma3_planner.planTrip.bind(this.gemma3_planner);
        
        // Enhance with scientific agents
        this.gemma3_planner.planTrip = async (userInput, options = {}) => {
            console.log('🧬 Enhancing Gemma 3 planning with SINDy + HMC science...');
            
            try {
                // Step 1: Get original Gemma 3 plan
                const gemma3_plan = await original_planTrip(userInput, options);
                
                // Step 2: Extract constraints for scientific analysis
                const scientific_constraints = this.extractConstraintsFromGemma3Plan(gemma3_plan, userInput);
                
                // Step 3: Run scientific research using SINDy equations
                console.log('🔬 Running SINDy equation research...');
                const research_findings = await this.research_agent.researchOptimalViewingLocations(scientific_constraints);
                
                // Step 4: Generate scientifically-optimized routes
                console.log('📋 Creating science-based route plans...');
                const scientific_route_plan = await this.planner_agent.planSustainableViewingRoutes(scientific_constraints, research_findings);
                
                // Step 5: Merge Gemma 3 intelligence with scientific evidence
                const enhanced_plan = this.mergeGemma3WithScience(gemma3_plan, research_findings, scientific_route_plan);
                
                // Step 6: Store for reference
                this.current_research = research_findings;
                this.current_plan = scientific_route_plan;
                
                console.log('✨ Enhanced plan with scientific evidence ready');
                return enhanced_plan;
                
            } catch (error) {
                console.error('Scientific enhancement error:', error);
                // Fallback to original Gemma 3 plan
                return await original_planTrip(userInput, options);
            }
        };
    }

    extractConstraintsFromGemma3Plan(gemma3_plan, userInput) {
        // Extract planning constraints from Gemma 3's analysis
        const constraints = {
            // Temporal constraints from Gemma 3
            dates: {
                start: gemma3_plan.startDate || new Date(),
                end: gemma3_plan.endDate || new Date(Date.now() + 3 * 24 * 60 * 60 * 1000)
            },
            
            // Spatial constraints
            viewing_mode: this.extractViewingMode(userInput, gemma3_plan),
            max_distance: this.extractMaxDistance(gemma3_plan),
            accessibility: gemma3_plan.accessibility || 'standard',
            
            // Experience preferences from Gemma 3's NLP
            behaviors: this.extractBehaviorInterests(userInput),
            group_size: this.extractGroupSize(userInput, gemma3_plan),
            experience_level: this.extractExperienceLevel(userInput),
            
            // Sustainability preferences
            sustainability: this.extractSustainabilityLevel(userInput),
            environmental_priority: 'high', // Default for whale watching
            
            // Logistics
            accommodation: gemma3_plan.accommodation || { lat: 48.516, lng: -123.012 },
            transport: this.extractTransportMode(userInput, gemma3_plan),
            duration: this.extractTripDuration(gemma3_plan)
        };
        
        console.log('📋 Extracted constraints for scientific analysis:', constraints);
        return constraints;
    }

    mergeGemma3WithScience(gemma3_plan, research_findings, scientific_route_plan) {
        // Create enhanced plan that combines Gemma 3's intelligence with scientific evidence
        
        const enhanced_plan = {
            // Original Gemma 3 plan
            original_gemma3_plan: gemma3_plan,
            
            // Scientific enhancement
            scientific_enhancement: {
                research_evidence: research_findings,
                scientific_routes: scientific_route_plan,
                enhancement_type: 'sindy_hmc_integration'
            },
            
            // Merged recommendations
            enhanced_recommendations: {
                // Best of both: Gemma 3 intelligence + SINDy science
                primary_itinerary: this.mergePrimaryItinerary(gemma3_plan, scientific_route_plan),
                alternative_options: this.mergeAlternativeOptions(gemma3_plan, scientific_route_plan),
                
                // Scientific backing for recommendations
                scientific_justification: {
                    equation_insights: research_findings.scientific_evidence.sindy_equation_insights,
                    uncertainty_analysis: research_findings.scientific_evidence.uncertainty_quantification,
                    confidence_metrics: research_findings.research_confidence
                },
                
                // Enhanced timing with SINDy optimal times
                optimal_timing: this.enhanceTimingWithSINDy(gemma3_plan, research_findings),
                
                // Sustainability integration
                sustainability_enhancement: scientific_route_plan.sustainability_plan
            },
            
            // User experience improvements
            enhanced_user_experience: {
                success_probability: this.calculateEnhancedSuccessProbability(research_findings, scientific_route_plan),
                scientific_confidence: research_findings.research_confidence.overall_confidence,
                personalization_score: this.calculatePersonalizationScore(gemma3_plan),
                educational_value: this.calculateEducationalValue(research_findings)
            },
            
            // Actionable insights combining both systems
            actionable_insights: [
                ...this.extractGemma3Insights(gemma3_plan),
                ...research_findings.actionable_insights
            ],
            
            // Export capabilities
            export_options: {
                detailed_itinerary: true,
                scientific_report: true,
                sustainability_commitment: true,
                emergency_contacts: true,
                gemma3_original: true
            }
        };
        
        return enhanced_plan;
    }

    mergePrimaryItinerary(gemma3_plan, scientific_route_plan) {
        const gemma3_locations = gemma3_plan.locations || [];
        const scientific_locations = scientific_route_plan.route_recommendations.primary_route.locations || [];
        
        // Merge location recommendations using both AI and science
        const merged_locations = this.smartMergeLocations(gemma3_locations, scientific_locations);
        
        return {
            strategy: 'gemma3_sindy_hybrid',
            name: 'AI-Enhanced Scientific Route',
            locations: merged_locations,
            
            // Timing from SINDy research
            optimal_timing: scientific_route_plan.timing_strategy.optimal_schedules,
            
            // Logistics from Gemma 3
            logistics: gemma3_plan.logistics,
            
            // Success metrics from both
            success_indicators: {
                gemma3_confidence: gemma3_plan.confidence || 0.8,
                scientific_probability: scientific_route_plan.success_metrics.predicted_success_rate,
                combined_score: this.calculateCombinedSuccessScore(gemma3_plan, scientific_route_plan)
            }
        };
    }

    smartMergeLocations(gemma3_locations, scientific_locations) {
        const merged = [];
        const location_scores = new Map();
        
        // Score Gemma 3 locations
        gemma3_locations.forEach(loc => {
            const key = `${loc.lat.toFixed(3)}_${loc.lng.toFixed(3)}`;
            location_scores.set(key, {
                location: loc,
                gemma3_score: loc.confidence || 0.7,
                scientific_score: 0,
                combined_score: 0,
                sources: ['gemma3']
            });
        });
        
        // Add scientific locations and boost scores for matches
        scientific_locations.forEach(loc => {
            const key = `${loc.location.lat.toFixed(3)}_${loc.location.lng.toFixed(3)}`;
            
            if (location_scores.has(key)) {
                // Location recommended by both systems - high confidence
                const existing = location_scores.get(key);
                existing.scientific_score = loc.probability;
                existing.combined_score = (existing.gemma3_score * 0.4) + (loc.probability * 0.6);
                existing.sources.push('sindy_science');
                existing.scientific_evidence = loc;
            } else {
                // New scientific location
                location_scores.set(key, {
                    location: loc.location,
                    gemma3_score: 0,
                    scientific_score: loc.probability,
                    combined_score: loc.probability * 0.8, // Slight penalty for single-source
                    sources: ['sindy_science'],
                    scientific_evidence: loc
                });
            }
        });
        
        // Sort by combined score and return top locations
        return Array.from(location_scores.values())
            .sort((a, b) => b.combined_score - a.combined_score)
            .slice(0, 6) // Top 6 locations
            .map((item, index) => ({
                ...item.location,
                sequence: index + 1,
                confidence: item.combined_score,
                recommendation_sources: item.sources,
                scientific_backing: item.scientific_evidence || null
            }));
    }

    /**
     * INTEGRATION WITH EXISTING ORCHESTRATOR
     */

    integrateWithOrchestrator() {
        if (!this.multi_agent_orchestrator) return;
        
        // Add our agents to the orchestrator
        this.multi_agent_orchestrator.agents.whale_research = this.research_agent;
        this.multi_agent_orchestrator.agents.whale_planner = this.planner_agent;
        
        // Hook into orchestration flow
        const original_orchestrate = this.multi_agent_orchestrator.orchestrateTripPlanning.bind(this.multi_agent_orchestrator);
        
        this.multi_agent_orchestrator.orchestrateTripPlanning = async (userInput, sessionId) => {
            // Run original orchestration
            const original_result = await original_orchestrate(userInput, sessionId);
            
            // Add our scientific enhancement
            if (this.enhancement_active) {
                console.log('🔬 Adding scientific whale watching enhancement...');
                
                const constraints = this.extractConstraintsFromUserInput(userInput);
                const research = await this.research_agent.researchOptimalViewingLocations(constraints);
                const routes = await this.planner_agent.planSustainableViewingRoutes(constraints, research);
                
                original_result.scientific_enhancement = {
                    research_findings: research,
                    scientific_routes: routes,
                    integration_timestamp: new Date().toISOString()
                };
            }
            
            return original_result;
        };
    }

    /**
     * UI ENHANCEMENT METHODS
     */

    addScientificEnhancementControls() {
        // Add toggle for scientific enhancement
        const enhancement_control = document.createElement('div');
        enhancement_control.className = 'scientific-enhancement-control';
        enhancement_control.innerHTML = `
            <div class="enhancement-toggle">
                <label>
                    <input type="checkbox" id="scientific-enhancement" ${this.enhancement_active ? 'checked' : ''}>
                    🧬 SINDy + HMC Scientific Enhancement
                </label>
                <div class="enhancement-info">
                    Uses discovered mathematical equations and uncertainty analysis
                </div>
            </div>
        `;
        
        // Add to existing UI
        const control_panel = document.querySelector('.trip-planner-controls') || document.body;
        control_panel.appendChild(enhancement_control);
        
        // Add event listener
        document.getElementById('scientific-enhancement').addEventListener('change', (e) => {
            this.enhancement_active = e.target.checked;
            console.log(`Scientific enhancement ${this.enhancement_active ? 'enabled' : 'disabled'}`);
        });
    }

    /**
     * HELPER METHODS
     */

    extractViewingMode(userInput, gemma3_plan) {
        const input_lower = userInput.toLowerCase();
        if (input_lower.includes('boat') || input_lower.includes('water')) return 'boat';
        if (input_lower.includes('land') || input_lower.includes('shore')) return 'land';
        if (input_lower.includes('kayak')) return 'kayak';
        return gemma3_plan.viewing_mode || 'land';
    }

    extractBehaviorInterests(userInput) {
        const input_lower = userInput.toLowerCase();
        const interests = [];
        
        if (input_lower.includes('feeding') || input_lower.includes('hunting')) interests.push('feeding');
        if (input_lower.includes('social') || input_lower.includes('playing')) interests.push('socializing');
        if (input_lower.includes('travel') || input_lower.includes('migration')) interests.push('traveling');
        
        return interests.length > 0 ? interests : ['feeding', 'socializing', 'traveling'];
    }

    calculateCombinedSuccessScore(gemma3_plan, scientific_route_plan) {
        const gemma3_confidence = gemma3_plan.confidence || 0.8;
        const scientific_probability = scientific_route_plan.success_metrics.predicted_success_rate || 0.7;
        
        // Weighted combination
        return (gemma3_confidence * 0.4) + (scientific_probability * 0.6);
    }

    // Export current research for external use
    getCurrentResearch() {
        return this.current_research;
    }

    getCurrentPlan() {
        return this.current_plan;
    }
}

// Initialize integration when both systems are available
window.initializeGemma3WhaleWatchingIntegration = function(config = {}) {
    if (window.WhaleWatchingResearchAgent && window.WhaleWatchingPlannerAgent) {
        window.gemma3WhaleWatchingIntegration = new Gemma3WhaleWatchingIntegration(config);
        console.log('✨ Gemma 3 + SINDy + HMC integration ready!');
        return window.gemma3WhaleWatchingIntegration;
    } else {
        console.warn('⚠️ Waiting for research and planner agents to load...');
        setTimeout(() => window.initializeGemma3WhaleWatchingIntegration(config), 1000);
    }
};

// Auto-initialize if all components are ready
if (typeof window !== 'undefined' && window.WhaleWatchingResearchAgent && window.WhaleWatchingPlannerAgent) {
    window.initializeGemma3WhaleWatchingIntegration();
} 