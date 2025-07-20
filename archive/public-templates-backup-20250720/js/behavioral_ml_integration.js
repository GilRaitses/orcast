// OrCast Behavioral ML Integration
// Connects Cloud Run ML service with transparency system and feeding zone dynamics

class BehavioralMLIntegration {
    constructor() {
        this.mlServiceUrl = 'https://orcast-behavioral-ml-service.run.app';
        this.predictionCache = new Map();
        this.cacheExpiration = 5 * 60 * 1000; // 5 minutes
        this.isModelTrained = false;
        this.modelStatus = null;
        
        this.initializeMLIntegration();
    }
    
    async initializeMLIntegration() {
        try {
            // Check model status
            await this.checkModelStatus();
            
            // Set up periodic model status checks
            setInterval(() => this.checkModelStatus(), 30000); // Every 30 seconds
            
            console.log('Behavioral ML Integration initialized');
        } catch (error) {
            console.error('Error initializing ML integration:', error);
        }
    }
    
    // === MODEL STATUS MANAGEMENT ===
    
    async checkModelStatus() {
        try {
            const response = await fetch('/api/ml/health');
            const status = await response.json();
            
            if (!response.ok || !status.models_loaded) {
                throw new Error('ML models not available');
            }
            
            return status;
        } catch (error) {
            console.error('ML service health check failed:', error);
            throw new Error('ML service unavailable - real data required');
        }
    }
    
    updateMLStatusIndicator() {
        const indicator = document.getElementById('mlStatusIndicator');
        if (indicator) {
            if (this.isModelTrained) {
                indicator.innerHTML = `
                    <div class="ml-status-indicator active">
                        <span class="ml-status-icon">🧠</span>
                        <span class="ml-status-text">ML Active</span>
                    </div>
                `;
            } else {
                indicator.innerHTML = `
                    <div class="ml-status-indicator inactive">
                        <span class="ml-status-icon">WARNING</span>
                        <span class="ml-status-text">ML Training</span>
                    </div>
                `;
            }
        }
    }
    
    // === REAL-TIME BEHAVIORAL PREDICTION ===
    
    async predictBehavior(sightingData) {
        if (!this.isModelTrained) {
            throw new Error('ML model not trained - real data required for behavioral classification');
        }
        
        // Check cache first
        const cacheKey = this.generateCacheKey(sightingData);
        const cached = this.predictionCache.get(cacheKey);
        if (cached && Date.now() - cached.timestamp < this.cacheExpiration) {
            return cached.prediction;
        }
        
        try {
            const response = await fetch('/api/ml/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(sightingData)
            });

            if (!response.ok) {
                throw new Error(`ML service error: ${response.status}`);
            }

            const result = await response.json();
            
            // Store prediction in database
            await this.storePrediction(result);
            
            return result;
        } catch (error) {
            console.error('Behavioral ML prediction failed:', error);
            throw new Error('Behavioral prediction service unavailable - real data required');
        }
    }

    async classifyBehaviorFromSighting(sightingData) {
        if (!sightingData || !sightingData.location) {
            throw new Error('Valid sighting data required for behavioral classification');
        }

        try {
            const response = await fetch('/api/ml/classify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(sightingData)
            });

            if (!response.ok) {
                throw new Error(`ML classification error: ${response.status}`);
            }

            const result = await response.json();
            
            // Store classification in database
            await this.storeClassification(result);
            
            return result;
        } catch (error) {
            console.error('Behavioral classification failed:', error);
            throw new Error('Behavioral classification service unavailable - real data required');
        }
    }
    
    prepareSightingForML(sightingData) {
        // Convert sighting data to ML service format
        return {
            timestamp: sightingData.timestamp || new Date().toISOString(),
            latitude: sightingData.latitude,
            longitude: sightingData.longitude,
            pod_size: sightingData.pod_size || 1,
            environmental_context: {
                // Extract environmental data from transparency engine
                tidal_height: window.forecastTransparency?.currentConditions?.tidal?.currentHeight || 0,
                tidal_phase: window.forecastTransparency?.currentConditions?.tidal?.trend || 'unknown',
                water_depth_m: this.estimateWaterDepth(sightingData.latitude, sightingData.longitude),
                sea_surface_temp_c: window.forecastTransparency?.currentConditions?.weather?.seaTemp || 12,
                wind_speed_knots: window.forecastTransparency?.currentConditions?.weather?.windSpeed || 10,
                wave_height_m: window.forecastTransparency?.currentConditions?.weather?.waveHeight || 1,
                chlorophyll_concentration: this.estimateChlorophyll(sightingData.latitude, sightingData.longitude),
                ...sightingData.environmental_context
            },
            data_quality_score: sightingData.data_quality_score || 0.8
        };
    }
    
    processPredictionForTransparency(mlPrediction) {
        // Convert ML prediction to transparency system format
        const topPrediction = mlPrediction.predictions[0];
        
        return {
            // Core behavioral prediction
            behavior: {
                primary: topPrediction.behavior,
                probability: topPrediction.probability,
                confidence: topPrediction.confidence,
                feeding_strategy: topPrediction.feeding_strategy,
                success_probability: topPrediction.success_probability
            },
            
            // Interpretability data
            explanation: {
                interpretation: mlPrediction.explanation.interpretation,
                feature_importance: mlPrediction.feature_importance,
                model_confidence: mlPrediction.model_confidence,
                processing_time_ms: mlPrediction.processing_time_ms
            },
            
            // All predictions for transparency
            all_predictions: mlPrediction.predictions,
            
            // Metadata
            sighting_id: mlPrediction.sighting_id,
            timestamp: new Date().toISOString(),
            model_version: mlPrediction.explanation.model_version
        };
    }
    
    async storePrediction(prediction) {
        // Store prediction in database for analysis
        try {
            await fetch('/api/predictions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ...prediction,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            console.error('Failed to store prediction:', error);
        }
    }

    async storeClassification(classification) {
        // Store classification in database for analysis
        try {
            await fetch('/api/classifications', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ...classification,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            console.error('Failed to store classification:', error);
        }
    }
    
    // === INTEGRATION WITH TRANSPARENCY SYSTEM ===
    
    enhanceTransparencyWithBehavior(transparencyData, behavioralPrediction) {
        // Add behavioral insights to transparency explanations
        const enhancedData = { ...transparencyData };
        
        // Add behavioral context to primary factors
        enhancedData.explanation.primaryFactors.push({
            factor: 'Predicted Behavior',
            influence: `${behavioralPrediction.behavior.primary} (${Math.round(behavioralPrediction.behavior.probability * 100)}% probability)`,
            weight: 'high',
            transparency: 'full',
            explanation: behavioralPrediction.explanation.interpretation
        });
        
        // Add behavioral feature importance
        enhancedData.explanation.behavioralFactors = behavioralPrediction.explanation.feature_importance.map(feature => ({
            factor: feature.feature.replace('_', ' '),
            importance: feature.importance,
            explanation: feature.explanation,
            transparency: 'partial'
        }));
        
        // Add feeding strategy if available
        if (behavioralPrediction.behavior.feeding_strategy) {
            enhancedData.explanation.feedingStrategy = {
                strategy: behavioralPrediction.behavior.feeding_strategy,
                success_probability: behavioralPrediction.behavior.success_probability,
                explanation: this.getFeedingStrategyExplanation(behavioralPrediction.behavior.feeding_strategy)
            };
        }
        
        // Enhance confidence calculation
        enhancedData.confidence.components.behavioral = {
            score: behavioralPrediction.behavior.confidence,
            explanation: 'Based on ML behavioral pattern recognition',
            transparency: 'limited'
        };
        
        return enhancedData;
    }
    
    getFeedingStrategyExplanation(strategy) {
        const explanations = {
            'carousel': 'Orcas swim in circles around prey to concentrate them into a tight ball',
            'surface_feeding': 'Orcas feed on prey near the water surface',
            'deep_diving': 'Orcas dive deep to hunt for prey at lower depths',
            'beach_rubbing': 'Orcas use shallow areas and beaches to stun or catch prey',
            'cooperative_hunting': 'Multiple orcas coordinate their hunting efforts'
        };
        
        return explanations[strategy] || 'Specialized feeding behavior based on environmental conditions';
    }
    
    // === INTEGRATION WITH FEEDING ZONE DYNAMICS ===
    
    async enhanceFeedingZoneWithBehavior(feedingZoneData, year) {
        // Add behavioral predictions to feeding zone analysis
        const enhancedZones = { ...feedingZoneData };
        
        // Get behavioral predictions for each feeding zone
        for (const zone of enhancedZones.feeding_zones.zones) {
            const zoneCenter = zone.center;
            
            // Predict behavior for zone center
            const behavioralPrediction = await this.predictBehavior({
                latitude: zoneCenter.lat,
                longitude: zoneCenter.lng,
                pod_size: 5, // Average pod size
                timestamp: new Date().toISOString()
            });
            
            // Add behavioral insights to zone
            zone.behavioral_insights = {
                predicted_behavior: behavioralPrediction.behavior.primary,
                feeding_probability: behavioralPrediction.behavior.probability,
                feeding_strategy: behavioralPrediction.behavior.feeding_strategy,
                success_probability: behavioralPrediction.behavior.success_probability,
                confidence: behavioralPrediction.behavior.confidence
            };
            
            // Add behavioral explanation
            zone.behavioral_explanation = behavioralPrediction.explanation.interpretation;
        }
        
        return enhancedZones;
    }
    
    // === REAL-TIME SIGHTING CLASSIFICATION ===
    
    async classifyNewSighting(sightingData) {
        // Classify behavior when new sighting is recorded
        const behavioralPrediction = await this.predictBehavior(sightingData);
        
        // Store in BigQuery for training data
        await this.storeSightingWithBehavior(sightingData, behavioralPrediction);
        
        // Update UI with behavioral insights
        this.updateSightingUI(sightingData, behavioralPrediction);
        
        // Trigger transparency update
        if (window.transparencyUI) {
            window.transparencyUI.updateWithBehavioralInsights(behavioralPrediction);
        }
        
        return behavioralPrediction;
    }
    
    async storeSightingWithBehavior(sightingData, behavioralPrediction) {
        // Store enriched sighting data in BigQuery
        try {
            const enrichedSighting = {
                sighting_id: behavioralPrediction.sighting_id,
                timestamp: sightingData.timestamp,
                location: `POINT(${sightingData.longitude} ${sightingData.latitude})`,
                latitude: sightingData.latitude,
                longitude: sightingData.longitude,
                pod_size: sightingData.pod_size,
                behavior_primary: behavioralPrediction.behavior.primary,
                behavior_confidence: behavioralPrediction.behavior.confidence,
                feeding_details: behavioralPrediction.behavior.feeding_strategy ? {
                    hunting_strategy: behavioralPrediction.behavior.feeding_strategy,
                    success_probability: behavioralPrediction.behavior.success_probability
                } : null,
                environmental_context: sightingData.environmental_context,
                data_source: 'orcast_app',
                observer_expertise: 'automated_ml',
                data_quality_score: sightingData.data_quality_score || 0.8
            };
            
            // This would be sent to BigQuery via backend API
            console.log('Enriched sighting for BigQuery:', enrichedSighting);
            
        } catch (error) {
            console.error('Error storing sighting with behavior:', error);
        }
    }
    
    updateSightingUI(sightingData, behavioralPrediction) {
        // Update UI elements with behavioral insights
        const sightingElement = document.getElementById(`sighting-${behavioralPrediction.sighting_id}`);
        if (sightingElement) {
            // Add behavioral indicators
            const behaviorIndicator = document.createElement('div');
            behaviorIndicator.className = 'behavioral-indicator';
            behaviorIndicator.innerHTML = `
                <div class="behavior-primary">
                    <span class="behavior-icon">${this.getBehaviorIcon(behavioralPrediction.behavior.primary)}</span>
                    <span class="behavior-text">${behavioralPrediction.behavior.primary}</span>
                    <span class="behavior-probability">${Math.round(behavioralPrediction.behavior.probability * 100)}%</span>
                </div>
                ${behavioralPrediction.behavior.feeding_strategy ? `
                    <div class="feeding-strategy">
                        <span class="strategy-text">${behavioralPrediction.behavior.feeding_strategy}</span>
                        <span class="success-probability">${Math.round(behavioralPrediction.behavior.success_probability * 100)}% success</span>
                    </div>
                ` : ''}
            `;
            
            sightingElement.appendChild(behaviorIndicator);
        }
    }
    
    getBehaviorIcon(behavior) {
        const icons = {
            'feeding': 'FEED',
            'traveling': 'TRAVEL',
            'socializing': 'SOCIAL',
            'resting': 'REST',
            'playing': 'PLAY',
            'unknown': 'UNKNOWN'
        };
        return icons[behavior] || icons['unknown'];
    }
    
    // === FEATURE IMPORTANCE ANALYSIS ===
    
    async getGlobalFeatureImportance() {
        try {
            const response = await fetch(`${this.mlServiceUrl}/features/importance`);
            const data = await response.json();
            
            return data.feature_importance;
        } catch (error) {
            console.error('Error getting feature importance:', error);
            return [];
        }
    }
    
    // === UTILITY FUNCTIONS ===
    
    generateCacheKey(sightingData) {
        return `${sightingData.latitude.toFixed(3)}_${sightingData.longitude.toFixed(3)}_${sightingData.pod_size}_${Math.floor(Date.now() / 300000)}`;
    }
    
    estimateWaterDepth(lat, lng) {
        // Simplified depth estimation based on distance from shore
        const distanceFromShore = Math.min(Math.abs(lat - 48.5), Math.abs(lng + 123.0)) * 111.0;
        return Math.min(200, Math.max(10, distanceFromShore * 20));
    }
    
    estimateChlorophyll(lat, lng) {
        // Simplified chlorophyll estimation
        return Math.random() * 2 + 0.5; // 0.5 to 2.5 mg/m³
    }
    
    // === PUBLIC API ===
    
    async trainModel() {
        try {
            const response = await fetch(`${this.mlServiceUrl}/train`, {
                method: 'POST'
            });
            
            const result = await response.json();
            console.log('Model training initiated:', result);
            
            // Update UI to show training status
            this.updateMLStatusIndicator();
            
            return result;
        } catch (error) {
            console.error('Error initiating model training:', error);
            throw error;
        }
    }
    
    async getBehavioralInsights(location) {
        // Get behavioral insights for a specific location
        const behavioralPrediction = await this.predictBehavior({
            latitude: location.lat,
            longitude: location.lng,
            pod_size: 3,
            timestamp: new Date().toISOString()
        });
        
        return {
            location: location,
            predicted_behavior: behavioralPrediction.behavior.primary,
            probability: behavioralPrediction.behavior.probability,
            confidence: behavioralPrediction.behavior.confidence,
            feeding_strategy: behavioralPrediction.behavior.feeding_strategy,
            success_probability: behavioralPrediction.behavior.success_probability,
            explanation: behavioralPrediction.explanation.interpretation,
            feature_importance: behavioralPrediction.explanation.feature_importance
        };
    }
    
    // === INTEGRATION WITH EXISTING SYSTEMS ===
    
    integrateWithTransparencySystem() {
        // Extend transparency system with behavioral insights
        if (window.transparencyUI) {
            const originalUpdateForecast = window.transparencyUI.updateForecastForLocation;
            
            window.transparencyUI.updateForecastForLocation = async function(location) {
                // Get original forecast
                const originalForecast = await originalUpdateForecast.call(this, location);
                
                // Add behavioral insights
                const behavioralPrediction = await behavioralML.predictBehavior({
                    latitude: location.lat,
                    longitude: location.lng,
                    pod_size: 3,
                    timestamp: new Date().toISOString()
                });
                
                // Enhance transparency data
                const enhancedForecast = behavioralML.enhanceTransparencyWithBehavior(
                    originalForecast, 
                    behavioralPrediction
                );
                
                return enhancedForecast;
            };
        }
    }
    
    integrateWithFeedingZoneSystem() {
        // Extend feeding zone system with behavioral insights
        if (window.feedingZoneUI) {
            const originalUpdateVisualization = window.feedingZoneUI.updateVisualization;
            
            window.feedingZoneUI.updateVisualization = async function() {
                // Get original visualization
                await originalUpdateVisualization.call(this);
                
                // Add behavioral insights to feeding zones
                if (this.visualizationMode === 'zones') {
                    const feedingZoneData = await window.feedingZoneDynamics.getFeedingZoneSnapshot(this.selectedYear);
                    const enhancedData = await behavioralML.enhanceFeedingZoneWithBehavior(feedingZoneData, this.selectedYear);
                    
                    // Update visualization with behavioral insights
                    this.renderBehavioralInsights(enhancedData);
                }
            };
        }
    }
}

// Initialize behavioral ML integration
const behavioralML = new BehavioralMLIntegration();

// Export for use in other modules
window.behavioralML = behavioralML;

// Auto-integrate with existing systems when they're ready
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        behavioralML.integrateWithTransparencySystem();
        behavioralML.integrateWithFeedingZoneSystem();
    }, 2000);
});

// Add CSS for behavioral indicators
const behavioralCSS = `
<style>
.ml-status-indicator {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.3rem 0.8rem;
    border-radius: 15px;
    font-size: 0.8rem;
    backdrop-filter: blur(5px);
}

.ml-status-indicator.active {
    background: rgba(76, 175, 80, 0.2);
    border: 1px solid rgba(76, 175, 80, 0.5);
    color: #4CAF50;
}

.ml-status-indicator.inactive {
    background: rgba(255, 152, 0, 0.2);
    border: 1px solid rgba(255, 152, 0, 0.5);
    color: #FF9800;
}

.behavioral-indicator {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 0.5rem;
    margin-top: 0.5rem;
    border-left: 3px solid #2196F3;
}

.behavior-primary {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.3rem;
}

.behavior-icon {
    font-size: 1.2rem;
}

.behavior-text {
    font-weight: bold;
    color: white;
    text-transform: capitalize;
}

.behavior-probability {
    background: rgba(33, 150, 243, 0.8);
    color: white;
    padding: 0.1rem 0.4rem;
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: bold;
}

.feeding-strategy {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8rem;
    color: rgba(255, 255, 255, 0.8);
}

.strategy-text {
    text-transform: capitalize;
}

.success-probability {
    background: rgba(76, 175, 80, 0.8);
    color: white;
    padding: 0.1rem 0.4rem;
    border-radius: 10px;
    font-size: 0.7rem;
    font-weight: bold;
}
</style>
`;

// Inject CSS
document.head.insertAdjacentHTML('beforeend', behavioralCSS); 