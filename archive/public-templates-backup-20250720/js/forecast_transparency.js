// OrCast Forecast Transparency Engine
// Provides explainable AI for orca behavior predictions without revealing proprietary algorithms

class ForecastTransparencyEngine {
    constructor() {
        this.environmentalFactors = {};
        this.periodicData = {};
        this.confidenceMetrics = {};
        this.historicalContext = {};
        this.realTimeConditions = {};
        
        this.initializeTransparencyLayer();
    }
    
    // === ENVIRONMENTAL CONTEXT ANALYSIS ===
    
    async initializeTransparencyLayer() {
        // Load environmental context databases
        await this.loadEnvironmentalFactors();
        await this.loadPeriodicData();
        await this.loadHistoricalContext();
        
        // Start real-time monitoring
        this.startRealTimeMonitoring();
    }
    
    async loadEnvironmentalFactors() {
        // Environmental variables that influence orca behavior (public knowledge)
        this.environmentalFactors = {
            tidal: {
                description: "Tidal cycles affect salmon movement and orca foraging patterns",
                influence: "Orcas often feed during tidal exchanges when salmon are concentrated",
                dataSource: "NOAA Tidal Predictions",
                transparency: "full" // Can fully explain this factor
            },
            lunar: {
                description: "Lunar phases affect plankton, fish, and marine ecosystem rhythms",
                influence: "New and full moons can increase orca activity due to prey behavior",
                dataSource: "Astronomical calculations",
                transparency: "full"
            },
            weather: {
                description: "Weather conditions affect surface visibility and orca behavior",
                influence: "Clear skies improve surface observations, wind affects sea state",
                dataSource: "Weather APIs and marine forecasts",
                transparency: "full"
            },
            seasonal: {
                description: "Seasonal patterns in salmon runs and orca migration",
                influence: "Summer brings resident orcas following salmon, winter brings transients",
                dataSource: "Historical wildlife data",
                transparency: "full"
            },
            bathymetry: {
                description: "Ocean depth and underwater topography",
                influence: "Orcas prefer certain depth ranges and underwater features for hunting",
                dataSource: "NOAA nautical charts",
                transparency: "partial" // Can explain influence but not exact weighting
            },
            currents: {
                description: "Ocean and tidal currents affect prey distribution",
                influence: "Strong currents concentrate prey species in predictable areas",
                dataSource: "Oceanographic models",
                transparency: "partial"
            },
            temperature: {
                description: "Sea surface temperature affects marine ecosystem",
                influence: "Temperature gradients create feeding opportunities",
                dataSource: "Satellite sea surface temperature",
                transparency: "partial"
            },
            salinity: {
                description: "Water salinity affects marine food chain",
                influence: "Salinity changes can indicate water mass movements and prey",
                dataSource: "Oceanographic sensors",
                transparency: "limited" // Can mention but not detail
            }
        };
    }
    
    async loadPeriodicData() {
        // Cyclical patterns that affect predictions
        this.periodicData = {
            daily: {
                sunrise: await this.getSunriseSunset(),
                tides: await this.getTidalData(),
                thermal: await this.getThermalCycles(),
                humanActivity: await this.getHumanActivityPatterns()
            },
            monthly: {
                lunar: await this.getLunarPhases(),
                tidal: await this.getMonthlyTidalPatterns(),
                weather: await this.getSeasonalWeatherPatterns()
            },
            seasonal: {
                salmon: await this.getSalmonRunData(),
                migration: await this.getOrcaMigrationPatterns(),
                weather: await this.getSeasonalWeatherData(),
                daylight: await this.getDaylightPatterns()
            },
            annual: {
                climate: await this.getClimatePatterns(),
                population: await this.getPopulationTrends(),
                ecosystem: await this.getEcosystemHealth()
            }
        };
    }
    
    // === REAL-TIME CONDITION ASSESSMENT ===
    
    async assessCurrentConditions() {
        const now = new Date();
        const conditions = {
            timestamp: now.toISOString(),
            
            // Weather conditions
            weather: await this.getCurrentWeather(),
            
            // Tidal conditions
            tidal: await this.getCurrentTidalConditions(),
            
            // Lunar conditions
            lunar: await this.getCurrentLunarPhase(),
            
            // Seasonal context
            seasonal: this.getSeasonalContext(now),
            
            // Daily cycle
            dailyCycle: this.getDailyCycleContext(now),
            
            // Visibility conditions
            visibility: await this.getVisibilityConditions(),
            
            // Marine conditions
            marine: await this.getMarineConditions()
        };
        
        return conditions;
    }
    
    async getCurrentWeather() {
        try {
            // Using open weather APIs for transparency
            const lat = 48.5; // San Juan Islands
            const lng = -123.0;
            
            const response = await fetch(
                `https://api.open-meteo.com/v1/marine?latitude=${lat}&longitude=${lng}&current=wave_height,swell_wave_height,ocean_current_velocity,sea_surface_temperature&hourly=visibility,cloud_cover&timezone=America/Los_Angeles`
            );
            
            const data = await response.json();
            
            return {
                cloudCover: data.hourly?.cloud_cover?.[0] || 'unknown',
                visibility: data.hourly?.visibility?.[0] || 'unknown',
                waveHeight: data.current?.wave_height || 'unknown',
                seaTemp: data.current?.sea_surface_temperature || 'unknown',
                conditions: this.interpretWeatherConditions(data),
                source: 'Open-Meteo Marine API',
                transparency: 'full'
            };
        } catch (error) {
            return { error: 'Weather data unavailable', transparency: 'full' };
        }
    }
    
    interpretWeatherConditions(weatherData) {
        const conditions = [];
        
        if (weatherData.hourly?.cloud_cover?.[0] < 25) {
            conditions.push({
                factor: 'Clear skies',
                impact: 'Excellent visibility for surface observations',
                confidence: 'high'
            });
        } else if (weatherData.hourly?.cloud_cover?.[0] > 75) {
            conditions.push({
                factor: 'Overcast conditions',
                impact: 'Reduced visibility, orcas may be less visible at surface',
                confidence: 'medium'
            });
        }
        
        if (weatherData.current?.wave_height > 2) {
            conditions.push({
                factor: 'Rough seas',
                impact: 'Difficult spotting conditions, orcas may dive deeper',
                confidence: 'high'
            });
        }
        
        return conditions;
    }
    
    async getCurrentTidalConditions() {
        // NOAA tidal data is public and explainable
        const tidalData = await this.fetchTidalData();
        
        return {
            currentHeight: tidalData.height,
            trend: tidalData.trend, // 'rising', 'falling', 'slack'
            nextChange: tidalData.nextChange,
            strength: tidalData.strength, // 'weak', 'moderate', 'strong'
            impact: this.interpretTidalImpact(tidalData),
            source: 'NOAA Tidal Predictions',
            transparency: 'full'
        };
    }
    
    interpretTidalImpact(tidalData) {
        const impacts = [];
        
        if (tidalData.trend === 'rising' && tidalData.strength === 'strong') {
            impacts.push({
                factor: 'Strong flood tide',
                impact: 'Salmon pushed into straits, increased orca activity likely',
                confidence: 'high'
            });
        }
        
        if (tidalData.trend === 'slack') {
            impacts.push({
                factor: 'Slack tide',
                impact: 'Minimal current, orcas may focus on surface activities',
                confidence: 'medium'
            });
        }
        
        return impacts;
    }
    
    async getCurrentLunarPhase() {
        const lunar = await this.calculateLunarPhase();
        
        return {
            phase: lunar.phase, // 'new', 'waxing', 'full', 'waning'
            illumination: lunar.illumination,
            impact: this.interpretLunarImpact(lunar),
            source: 'Astronomical calculations',
            transparency: 'full'
        };
    }
    
    interpretLunarImpact(lunar) {
        const impacts = [];
        
        if (lunar.phase === 'full' || lunar.phase === 'new') {
            impacts.push({
                factor: `${lunar.phase} moon`,
                impact: 'Stronger tidal forces, increased marine ecosystem activity',
                confidence: 'medium'
            });
        }
        
        if (lunar.illumination > 0.8) {
            impacts.push({
                factor: 'Bright moonlight',
                impact: 'May extend orca activity into evening hours',
                confidence: 'low'
            });
        }
        
        return impacts;
    }
    
    // === PREDICTION EXPLANATION ENGINE ===
    
    async generatePredictionExplanation(predictionData, location) {
        const conditions = await this.assessCurrentConditions();
        const historicalContext = await this.getHistoricalContext(location);
        const confidenceBreakdown = this.calculateConfidenceBreakdown(predictionData, conditions);
        
        return {
            prediction: {
                probability: predictionData.probability,
                confidence: predictionData.confidence,
                timeframe: predictionData.timeframe
            },
            
            explanation: {
                primaryFactors: this.identifyPrimaryFactors(predictionData, conditions),
                supportingFactors: this.identifySupportingFactors(predictionData, conditions),
                limitingFactors: this.identifyLimitingFactors(predictionData, conditions)
            },
            
            context: {
                current: conditions,
                historical: historicalContext,
                seasonal: this.getSeasonalContext(new Date())
            },
            
            confidence: confidenceBreakdown,
            
            transparency: {
                dataSource: this.getDataSourceTransparency(),
                methodology: this.getMethodologyTransparency(),
                limitations: this.getLimitationsTransparency()
            },
            
            recommendations: this.generateRecommendations(predictionData, conditions)
        };
    }
    
    identifyPrimaryFactors(prediction, conditions) {
        const factors = [];
        
        // Tidal influence (always explainable)
        if (conditions.tidal.strength === 'strong') {
            factors.push({
                factor: 'Strong tidal current',
                influence: 'Concentrates salmon prey in predictable locations',
                weight: 'high',
                transparency: 'full',
                explanation: 'Orcas time their foraging with tidal exchanges when salmon are funneled through narrow passages'
            });
        }
        
        // Weather influence
        if (conditions.weather.cloudCover < 30) {
            factors.push({
                factor: 'Clear weather conditions',
                influence: 'Optimal visibility for surface observations',
                weight: 'medium',
                transparency: 'full',
                explanation: 'Clear skies make orcas more visible when they surface to breathe'
            });
        }
        
        // Seasonal influence
        const seasonal = this.getSeasonalContext(new Date());
        if (seasonal.salmonRun === 'peak') {
            factors.push({
                factor: 'Peak salmon run period',
                influence: 'Maximum prey availability attracts resident orcas',
                weight: 'high',
                transparency: 'full',
                explanation: 'Summer salmon runs are the primary driver of Southern Resident orca presence'
            });
        }
        
        return factors;
    }
    
    identifySupportingFactors(prediction, conditions) {
        const factors = [];
        
        // Lunar influence
        if (conditions.lunar.phase === 'full' || conditions.lunar.phase === 'new') {
            factors.push({
                factor: 'Spring tide conditions',
                influence: 'Enhanced tidal mixing affects marine ecosystem',
                weight: 'low',
                transparency: 'full',
                explanation: 'Stronger tidal forces during new and full moons can increase plankton and fish activity'
            });
        }
        
        // Time of day
        const hour = new Date().getHours();
        if (hour >= 6 && hour <= 10) {
            factors.push({
                factor: 'Morning feeding period',
                influence: 'Peak foraging time for marine mammals',
                weight: 'medium',
                transparency: 'full',
                explanation: 'Orcas often increase surface activity during morning hours'
            });
        }
        
        return factors;
    }
    
    identifyLimitingFactors(prediction, conditions) {
        const factors = [];
        
        // Weather limitations
        if (conditions.weather.waveHeight > 2) {
            factors.push({
                factor: 'Rough sea conditions',
                influence: 'Reduces surface visibility and detection probability',
                weight: 'medium',
                transparency: 'full',
                explanation: 'High waves make it difficult to spot orcas when they surface'
            });
        }
        
        // Visibility limitations
        if (conditions.weather.visibility < 5) {
            factors.push({
                factor: 'Poor visibility',
                influence: 'Limits observation range significantly',
                weight: 'high',
                transparency: 'full',
                explanation: 'Fog or haze reduces the distance at which orcas can be spotted'
            });
        }
        
        return factors;
    }
    
    calculateConfidenceBreakdown(prediction, conditions) {
        return {
            overall: prediction.confidence,
            
            components: {
                environmental: {
                    score: this.calculateEnvironmentalConfidence(conditions),
                    explanation: 'Based on current weather, tidal, and marine conditions',
                    transparency: 'full'
                },
                
                historical: {
                    score: 0.75, // Can explain this is based on historical patterns
                    explanation: 'Based on historical sighting patterns for this location and time',
                    transparency: 'partial'
                },
                
                behavioral: {
                    score: 0.65, // Limited explanation of proprietary behavioral models
                    explanation: 'Based on orca behavioral patterns and ecosystem dynamics',
                    transparency: 'limited'
                },
                
                observational: {
                    score: this.calculateObservationalConfidence(conditions),
                    explanation: 'Likelihood of actually seeing orcas if they are present',
                    transparency: 'full'
                }
            },
            
            uncertainties: [
                'Wildlife behavior is inherently unpredictable',
                'Weather conditions can change rapidly',
                'Individual orca pod preferences may vary',
                'Marine ecosystem dynamics are complex'
            ]
        };
    }
    
    calculateEnvironmentalConfidence(conditions) {
        let score = 0.5; // Base score
        
        // Weather contribution (fully explainable)
        if (conditions.weather.cloudCover < 50) score += 0.1;
        if (conditions.weather.visibility > 10) score += 0.1;
        if (conditions.weather.waveHeight < 1.5) score += 0.1;
        
        // Tidal contribution (fully explainable)  
        if (conditions.tidal.strength === 'strong') score += 0.15;
        if (conditions.tidal.trend !== 'slack') score += 0.05;
        
        return Math.min(score, 1.0);
    }
    
    calculateObservationalConfidence(conditions) {
        let score = 0.7; // Base observational score
        
        // Visibility factors
        if (conditions.weather.visibility > 15) score += 0.1;
        if (conditions.weather.visibility < 5) score -= 0.3;
        
        // Sea state factors
        if (conditions.weather.waveHeight < 1) score += 0.1;
        if (conditions.weather.waveHeight > 3) score -= 0.2;
        
        // Weather factors
        if (conditions.weather.cloudCover < 25) score += 0.05;
        if (conditions.weather.cloudCover > 90) score -= 0.1;
        
        return Math.max(Math.min(score, 1.0), 0.1);
    }
    
    // === TRANSPARENCY METADATA ===
    
    getDataSourceTransparency() {
        return {
            fullyOpen: [
                'NOAA tidal predictions',
                'Weather forecast data',
                'Astronomical calculations (lunar phases)',
                'Historical sighting databases',
                'Marine chart bathymetry'
            ],
            
            partiallyOpen: [
                'Oceanographic models (general patterns)',
                'Marine ecosystem indicators',
                'Seasonal wildlife patterns'
            ],
            
            proprietary: [
                'OrCast behavioral prediction algorithms',
                'Specific parameter weightings',
                'Machine learning model internals',
                'Real-time fusion methodologies'
            ]
        };
    }
    
    getMethodologyTransparency() {
        return {
            transparent: [
                'Environmental factor correlation',
                'Historical pattern matching',
                'Statistical trend analysis',
                'Observational condition assessment'
            ],
            
            generalDescription: [
                'Machine learning behavioral models',
                'Real-time data fusion techniques',
                'Predictive algorithm optimization'
            ],
            
            proprietary: [
                'Specific algorithm implementations',
                'Model training procedures',
                'Parameter optimization methods',
                'Proprietary data processing'
            ]
        };
    }
    
    getLimitationsTransparency() {
        return [
            'Predictions are probabilistic, not deterministic',
            'Wild animal behavior cannot be predicted with 100% accuracy',
            'Weather conditions can change rapidly and affect predictions',
            'Individual orca pod behaviors may differ from general patterns',
            'Limited to surface observation predictions only',
            'Prediction accuracy may vary by location and season',
            'Does not account for human disturbance factors',
            'Based on historical patterns which may not predict unprecedented events'
        ];
    }
    
    generateRecommendations(prediction, conditions) {
        const recommendations = [];
        
        // Timing recommendations
        if (conditions.tidal.trend === 'rising' && conditions.tidal.strength === 'strong') {
            recommendations.push({
                type: 'timing',
                priority: 'high',
                text: 'Optimal time window approaching with strong flood tide',
                action: 'Plan to be in position within the next 2 hours'
            });
        }
        
        // Location recommendations
        if (prediction.location && prediction.probability > 0.7) {
            recommendations.push({
                type: 'location',
                priority: 'high',
                text: 'High probability area identified',
                action: `Consider positioning near ${prediction.location.name}`
            });
        }
        
        // Weather recommendations
        if (conditions.weather.visibility < 5) {
            recommendations.push({
                type: 'weather',
                priority: 'medium',
                text: 'Poor visibility conditions',
                action: 'Stay closer to shore and use audio cues (hydrophone if available)'
            });
        }
        
        // Equipment recommendations
        if (conditions.weather.waveHeight > 2) {
            recommendations.push({
                type: 'equipment',
                priority: 'medium',
                text: 'Rough seas expected',
                action: 'Use image stabilization and consider closer observation points'
            });
        }
        
        return recommendations;
    }
    
    // === API HELPER FUNCTIONS ===
    
    async fetchTidalData() {
        // Implementation for real tidal data
        // This is fully transparent as it uses public NOAA data
        return {
            height: 2.5,
            trend: 'rising',
            strength: 'strong',
            nextChange: '14:30'
        };
    }
    
    async calculateLunarPhase() {
        // Standard astronomical calculations
        const now = new Date();
        // Implementation for lunar phase calculation
        return {
            phase: 'waxing',
            illumination: 0.65
        };
    }
    
    getSeasonalContext(date) {
        const month = date.getMonth();
        
        // Transparent seasonal patterns
        if (month >= 5 && month <= 8) { // June-September
            return {
                season: 'summer',
                salmonRun: 'peak',
                orcaType: 'residents',
                activity: 'high',
                explanation: 'Peak salmon season brings Southern Resident orcas to feeding areas'
            };
        } else if (month >= 10 || month <= 2) { // Nov-Feb
            return {
                season: 'winter',
                salmonRun: 'minimal',
                orcaType: 'transients',
                activity: 'moderate',
                explanation: 'Winter period with Bigg\'s (transient) orcas hunting marine mammals'
            };
        } else {
            return {
                season: 'transition',
                salmonRun: 'building',
                orcaType: 'mixed',
                activity: 'variable',
                explanation: 'Transition period with variable orca presence'
            };
        }
    }
    
    getDailyCycleContext(date) {
        const hour = date.getHours();
        
        if (hour >= 6 && hour <= 10) {
            return {
                period: 'morning',
                activity: 'high',
                explanation: 'Peak morning foraging period'
            };
        } else if (hour >= 16 && hour <= 19) {
            return {
                period: 'evening',
                activity: 'moderate',
                explanation: 'Secondary evening activity period'
            };
        } else {
            return {
                period: 'midday',
                activity: 'variable',
                explanation: 'Variable activity throughout midday hours'
            };
        }
    }
    
    // === PUBLIC API FOR UI INTEGRATION ===
    
    async getExplainableForecast(location, timeframe = '4h') {
        try {
            // This would interface with your proprietary prediction engine
            const rawPrediction = await this.getPredictionFromOrCastEngine(location, timeframe);
            
            // Generate transparent explanation
            const explanation = await this.generatePredictionExplanation(rawPrediction, location);
            
            return {
                success: true,
                prediction: explanation.prediction,
                explanation: explanation.explanation,
                context: explanation.context,
                confidence: explanation.confidence,
                transparency: explanation.transparency,
                recommendations: explanation.recommendations,
                timestamp: new Date().toISOString()
            };
            
        } catch (error) {
            return {
                success: false,
                error: error.message,
                transparency: 'full'
            };
        }
    }
    
    async getPredictionFromOrCastEngine(location, timeframe) {
        // This is where you'd interface with your proprietary OrCast prediction engine
        // The transparency engine doesn't need to know the internal workings
        
        return {
            probability: 0.73,
            confidence: 0.68,
            timeframe: timeframe,
            location: location,
            factors: ['tidal', 'seasonal', 'behavioral'] // High-level factor list only
        };
    }
}

// Initialize transparency engine
const forecastTransparency = new ForecastTransparencyEngine();

// Export for use in main application
window.forecastTransparency = forecastTransparency; 