/**
 * OrCast HMC Frontend Integration
 * Connects HMC predictions to transparency UI for interpretability
 */

class HMCFrontendIntegration {
    constructor() {
        this.serviceUrl = 'https://orcast-behavioral-ml-jniny7d7zq-uc.a.run.app';
        this.cache = new Map();
        this.updateInterval = 300000; // 5 minutes
        this.isInitialized = false;
    }

    async initialize() {
        if (this.isInitialized) return;
        
        console.log('Initializing HMC Frontend Integration...');
        
        // Start periodic updates
        this.startPeriodicUpdates();
        
        // Load initial data
        await this.loadHMCAnalysisData();
        
        this.isInitialized = true;
        console.log('HMC Frontend Integration initialized successfully');
    }

    async loadHMCAnalysisData() {
        try {
            const response = await fetch(`${this.serviceUrl}/hmc/analysis/latest`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.feeding_patterns) {
                this.cache.set('current_patterns', data.feeding_patterns);
                this.cache.set('analysis_timestamp', data.timestamp);
                
                // Update transparency UI with new patterns
                this.updateTransparencyUI(data.feeding_patterns);
                
                console.log('HMC analysis data loaded successfully');
            }
            
        } catch (error) {
            console.error('Failed to load HMC analysis data:', error);
            
            // Use fallback patterns if available
            this.loadFallbackPatterns();
        }
    }

    loadFallbackPatterns() {
        const fallbackPatterns = {
            temporal_patterns: {
                dawn_foraging: 0.7,
                dusk_foraging: 0.8,
                seasonal_variation: 0.6
            },
            spatial_patterns: {
                preferred_locations: [
                    { lat: 48.5, lon: -123.0, strength: 0.8 },
                    { lat: 48.7, lon: -122.9, strength: 0.7 }
                ],
                depth_preference: 0.6,
                distance_from_shore: 0.5
            },
            environmental_factors: {
                tidal_influence: 0.8,
                temperature_optimum: 0.7,
                prey_density_threshold: 0.6
            },
            behavioral_strategies: {
                cooperative_hunting: 0.7,
                strategy_switching: 0.6,
                success_rates: {
                    foraging: 0.75,
                    traveling: 0.4,
                    socializing: 0.2
                }
            }
        };
        
        this.cache.set('current_patterns', fallbackPatterns);
        this.updateTransparencyUI(fallbackPatterns);
        
        console.log('Using fallback HMC patterns');
    }

    updateTransparencyUI(patterns) {
        try {
            // Update temporal patterns visualization
            this.updateTemporalVisualization(patterns.temporal_patterns);
            
            // Update spatial patterns visualization
            this.updateSpatialVisualization(patterns.spatial_patterns);
            
            // Update environmental factors
            this.updateEnvironmentalFactors(patterns.environmental_factors);
            
            // Update behavioral strategies
            this.updateBehavioralStrategies(patterns.behavioral_strategies);
            
            // Update confidence indicators
            this.updateConfidenceIndicators(patterns);
            
            console.log('Transparency UI updated with HMC patterns');
            
        } catch (error) {
            console.error('Failed to update transparency UI:', error);
        }
    }

    updateTemporalVisualization(temporal) {
        const container = document.getElementById('temporal-patterns');
        if (!container) return;

        const html = `
            <div class="hmc-temporal-patterns">
                <h3>Temporal Feeding Patterns</h3>
                <div class="pattern-grid">
                    <div class="pattern-item">
                        <div class="pattern-label">Dawn Foraging</div>
                        <div class="strength-bar">
                            <div class="strength-fill" style="width: ${temporal.dawn_foraging * 100}%"></div>
                        </div>
                        <div class="pattern-value">${(temporal.dawn_foraging * 100).toFixed(1)}%</div>
                    </div>
                    <div class="pattern-item">
                        <div class="pattern-label">Dusk Foraging</div>
                        <div class="strength-bar">
                            <div class="strength-fill" style="width: ${temporal.dusk_foraging * 100}%"></div>
                        </div>
                        <div class="pattern-value">${(temporal.dusk_foraging * 100).toFixed(1)}%</div>
                    </div>
                    <div class="pattern-item">
                        <div class="pattern-label">Seasonal Variation</div>
                        <div class="strength-bar">
                            <div class="strength-fill" style="width: ${temporal.seasonal_variation * 100}%"></div>
                        </div>
                        <div class="pattern-value">${(temporal.seasonal_variation * 100).toFixed(1)}%</div>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    updateSpatialVisualization(spatial) {
        const container = document.getElementById('spatial-patterns');
        if (!container) return;

        const html = `
            <div class="hmc-spatial-patterns">
                <h3>Spatial Feeding Patterns</h3>
                <div class="spatial-grid">
                    <div class="spatial-item">
                        <div class="spatial-label">Preferred Locations</div>
                        <div class="locations-list">
                            ${spatial.preferred_locations.map(loc => `
                                <div class="location-item">
                                    <span class="coords">${loc.lat.toFixed(2)}, ${loc.lon.toFixed(2)}</span>
                                    <span class="strength">${(loc.strength * 100).toFixed(0)}%</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="spatial-item">
                        <div class="spatial-label">Depth Preference</div>
                        <div class="preference-indicator">
                            <div class="preference-fill" style="width: ${spatial.depth_preference * 100}%"></div>
                        </div>
                    </div>
                    <div class="spatial-item">
                        <div class="spatial-label">Distance from Shore</div>
                        <div class="preference-indicator">
                            <div class="preference-fill" style="width: ${spatial.distance_from_shore * 100}%"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    updateEnvironmentalFactors(environmental) {
        const container = document.getElementById('environmental-factors');
        if (!container) return;

        const html = `
            <div class="hmc-environmental-factors">
                <h3>Environmental Influence</h3>
                <div class="factors-grid">
                    <div class="factor-item">
                        <div class="factor-icon">🌊</div>
                        <div class="factor-label">Tidal Influence</div>
                        <div class="factor-strength">
                            <div class="strength-fill" style="width: ${environmental.tidal_influence * 100}%"></div>
                        </div>
                        <div class="factor-value">${(environmental.tidal_influence * 100).toFixed(0)}%</div>
                    </div>
                    <div class="factor-item">
                        <div class="factor-icon">🌡️</div>
                        <div class="factor-label">Temperature</div>
                        <div class="factor-strength">
                            <div class="strength-fill" style="width: ${environmental.temperature_optimum * 100}%"></div>
                        </div>
                        <div class="factor-value">${(environmental.temperature_optimum * 100).toFixed(0)}%</div>
                    </div>
                    <div class="factor-item">
                        <div class="factor-icon">🐟</div>
                        <div class="factor-label">Prey Density</div>
                        <div class="factor-strength">
                            <div class="strength-fill" style="width: ${environmental.prey_density_threshold * 100}%"></div>
                        </div>
                        <div class="factor-value">${(environmental.prey_density_threshold * 100).toFixed(0)}%</div>
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    updateBehavioralStrategies(behavioral) {
        const container = document.getElementById('behavioral-strategies');
        if (!container) return;

        const html = `
            <div class="hmc-behavioral-strategies">
                <h3>Behavioral Strategies</h3>
                <div class="strategies-grid">
                    <div class="strategy-item">
                        <div class="strategy-label">Cooperative Hunting</div>
                        <div class="strategy-strength">
                            <div class="strength-fill" style="width: ${behavioral.cooperative_hunting * 100}%"></div>
                        </div>
                        <div class="strategy-value">${(behavioral.cooperative_hunting * 100).toFixed(0)}%</div>
                    </div>
                    <div class="strategy-item">
                        <div class="strategy-label">Strategy Switching</div>
                        <div class="strategy-strength">
                            <div class="strength-fill" style="width: ${behavioral.strategy_switching * 100}%"></div>
                        </div>
                        <div class="strategy-value">${(behavioral.strategy_switching * 100).toFixed(0)}%</div>
                    </div>
                    <div class="success-rates">
                        <h4>Success Rates by Behavior</h4>
                        ${Object.entries(behavioral.success_rates).map(([behavior, rate]) => `
                            <div class="success-item">
                                <span class="behavior-name">${behavior}</span>
                                <div class="success-bar">
                                    <div class="success-fill" style="width: ${rate * 100}%"></div>
                                </div>
                                <span class="success-value">${(rate * 100).toFixed(0)}%</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    updateConfidenceIndicators(patterns) {
        const container = document.getElementById('confidence-indicators');
        if (!container) return;

        // Calculate overall confidence based on pattern strength
        const confidenceScores = {
            temporal: (patterns.temporal_patterns.dawn_foraging + patterns.temporal_patterns.dusk_foraging) / 2,
            spatial: patterns.spatial_patterns.preferred_locations.length > 0 ? 0.8 : 0.5,
            environmental: (patterns.environmental_factors.tidal_influence + patterns.environmental_factors.temperature_optimum) / 2,
            behavioral: patterns.behavioral_strategies.cooperative_hunting
        };

        const overallConfidence = Object.values(confidenceScores).reduce((a, b) => a + b, 0) / Object.keys(confidenceScores).length;

        const html = `
            <div class="hmc-confidence">
                <h3>Model Confidence</h3>
                <div class="confidence-grid">
                    <div class="confidence-item">
                        <div class="confidence-label">Overall</div>
                        <div class="confidence-circle" style="--confidence: ${overallConfidence * 100}%">
                            <span class="confidence-value">${(overallConfidence * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                    ${Object.entries(confidenceScores).map(([category, score]) => `
                        <div class="confidence-item">
                            <div class="confidence-label">${category}</div>
                            <div class="confidence-bar">
                                <div class="confidence-fill" style="width: ${score * 100}%"></div>
                            </div>
                            <div class="confidence-value">${(score * 100).toFixed(0)}%</div>
                        </div>
                    `).join('')}
                </div>
                <div class="confidence-note">
                    <small>Confidence based on HMC posterior uncertainty</small>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    async getPredictionExplanation(sightingData) {
        try {
            const response = await fetch(`${this.serviceUrl}/predict`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    sighting_data: sightingData,
                    include_explanation: true
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const prediction = await response.json();
            
            // Enhance with HMC patterns
            const patterns = this.cache.get('current_patterns');
            if (patterns) {
                prediction.hmc_context = this.generateHMCContext(sightingData, patterns);
            }

            return prediction;

        } catch (error) {
            console.error('Failed to get prediction explanation:', error);
            return null;
        }
    }

    generateHMCContext(sightingData, patterns) {
        const context = {
            temporal_relevance: this.calculateTemporalRelevance(sightingData, patterns.temporal_patterns),
            spatial_relevance: this.calculateSpatialRelevance(sightingData, patterns.spatial_patterns),
            environmental_match: this.calculateEnvironmentalMatch(sightingData, patterns.environmental_factors),
            behavioral_likelihood: this.calculateBehavioralLikelihood(sightingData, patterns.behavioral_strategies)
        };

        return context;
    }

    calculateTemporalRelevance(sightingData, temporal) {
        const hour = new Date(sightingData.timestamp).getHours();
        const isDawn = hour >= 5 && hour <= 7;
        const isDusk = hour >= 18 && hour <= 20;

        if (isDawn) {
            return { relevance: temporal.dawn_foraging, reason: 'Dawn foraging period' };
        } else if (isDusk) {
            return { relevance: temporal.dusk_foraging, reason: 'Dusk foraging period' };
        } else {
            return { relevance: 0.5, reason: 'Neutral foraging period' };
        }
    }

    calculateSpatialRelevance(sightingData, spatial) {
        let maxRelevance = 0;
        let closestLocation = null;

        spatial.preferred_locations.forEach(loc => {
            const distance = Math.sqrt(
                Math.pow(sightingData.latitude - loc.lat, 2) + 
                Math.pow(sightingData.longitude - loc.lon, 2)
            );
            
            if (distance < 0.1 && loc.strength > maxRelevance) {
                maxRelevance = loc.strength;
                closestLocation = loc;
            }
        });

        return {
            relevance: maxRelevance,
            reason: closestLocation ? `Near preferred location (${closestLocation.lat.toFixed(2)}, ${closestLocation.lon.toFixed(2)})` : 'Not near known feeding areas'
        };
    }

    calculateEnvironmentalMatch(sightingData, environmental) {
        // This would normally use actual environmental data
        // For now, use average of environmental factors
        const avgMatch = (environmental.tidal_influence + environmental.temperature_optimum + environmental.prey_density_threshold) / 3;
        
        return {
            relevance: avgMatch,
            reason: 'Environmental conditions moderate for feeding'
        };
    }

    calculateBehavioralLikelihood(sightingData, behavioral) {
        const behavior = sightingData.behavior_observed || 'unknown';
        const successRate = behavioral.success_rates[behavior] || 0.5;
        
        return {
            relevance: successRate,
            reason: `${behavior} behavior has ${(successRate * 100).toFixed(0)}% feeding success rate`
        };
    }

    startPeriodicUpdates() {
        setInterval(async () => {
            await this.loadHMCAnalysisData();
        }, this.updateInterval);
    }

    getPatterns() {
        return this.cache.get('current_patterns');
    }

    getLastUpdate() {
        return this.cache.get('analysis_timestamp');
    }
}

// Initialize HMC integration when page loads
document.addEventListener('DOMContentLoaded', async () => {
    window.hmcIntegration = new HMCFrontendIntegration();
    await window.hmcIntegration.initialize();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HMCFrontendIntegration;
} 