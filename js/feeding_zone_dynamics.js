// OrCast Feeding Zone Dynamics System
// Visualizes marine ecosystem dynamics underlying orca behavior predictions

class FeedingZoneDynamicsEngine {
    constructor() {
        this.currentYear = new Date().getFullYear();
        this.historicalRange = { start: 2010, end: this.currentYear };
        this.forecastRange = { start: this.currentYear + 1, end: this.currentYear + 5 };
        
        this.feedingZones = {};
        this.bathymetryData = {};
        this.foodDensityData = {};
        this.historicalTrends = {};
        this.climateProjections = {};
        
        this.initializeEcosystemData();
    }
    
    // === CORE ECOSYSTEM DATA ===
    
    async initializeEcosystemData() {
        // Load multi-source ecosystem data
        await this.loadBathymetryData();
        await this.loadFeedingZoneData();
        await this.loadFoodDensityData();
        await this.loadHistoricalTrends();
        await this.loadClimateProjections();
        
        console.log('Feeding Zone Dynamics Engine initialized');
    }
    
    async loadBathymetryData() {
        // NOAA bathymetry data - fully transparent
        this.bathymetryData = {
            source: "NOAA National Bathymetric Data",
            resolution: "1 arc-minute",
            transparency: "full",
            
            // San Juan Islands key bathymetric features
            features: {
                hankoReef: {
                    location: { lat: 48.545, lng: -123.155 },
                    depth: 15, // meters
                    significance: "Shallow reef concentrates prey fish",
                    orcaRelevance: "High - frequent foraging area",
                    type: "underwater ridge"
                },
                
                rosarioStrait: {
                    location: { lat: 48.65, lng: -122.95 },
                    depth: 85,
                    significance: "Deep channel with strong currents",
                    orcaRelevance: "High - salmon migration pathway",
                    type: "tidal channel"
                },
                
                presidentialChannel: {
                    location: { lat: 48.5, lng: -123.0 },
                    depth: 120,
                    significance: "Major shipping channel with prey aggregation",
                    orcaRelevance: "Medium - vessel traffic affects usage",
                    type: "shipping channel"
                },
                
                lopezPass: {
                    location: { lat: 48.48, lng: -122.88 },
                    depth: 35,
                    significance: "Narrow pass with tidal acceleration",
                    orcaRelevance: "High - tidal prey concentration",
                    type: "tidal pass"
                }
            }
        };
    }
    
    async loadFeedingZoneData() {
        // Integration of multiple data sources for feeding zones
        this.feedingZones = {
            
            // Primary feeding zones based on historical observations
            zones: {
                westSideFeeding: {
                    id: "zone_001",
                    name: "West Side Feeding Complex",
                    center: { lat: 48.52, lng: -123.15 },
                    radius: 2.5, // km
                    depth_range: [10, 50],
                    
                    characteristics: {
                        prey_species: ["Chinook salmon", "Coho salmon", "Rockfish"],
                        peak_activity: "June-September",
                        tidal_dependency: "High - flood tide optimal",
                        success_rate: 0.78,
                        
                        seasonal_patterns: {
                            spring: { activity: 0.3, explanation: "Early salmon runs beginning" },
                            summer: { activity: 0.9, explanation: "Peak salmon abundance" },
                            fall: { activity: 0.6, explanation: "Late salmon runs" },
                            winter: { activity: 0.2, explanation: "Transient orcas hunting marine mammals" }
                        }
                    },
                    
                    transparency: "partial" // Location public, success rates proprietary
                },
                
                eastSoundFeeding: {
                    id: "zone_002", 
                    name: "East Sound Foraging Area",
                    center: { lat: 48.65, lng: -122.88 },
                    radius: 1.8,
                    depth_range: [20, 80],
                    
                    characteristics: {
                        prey_species: ["Chinook salmon", "Lingcod", "Herring"],
                        peak_activity: "July-August",
                        tidal_dependency: "Medium - both tides productive",
                        success_rate: 0.65,
                        
                        seasonal_patterns: {
                            spring: { activity: 0.4, explanation: "Herring spawning attracts salmon" },
                            summer: { activity: 0.8, explanation: "Concentrated salmon runs" },
                            fall: { activity: 0.5, explanation: "Dispersed feeding" },
                            winter: { activity: 0.1, explanation: "Minimal resident activity" }
                        }
                    },
                    
                    transparency: "partial"
                },
                
                spineChannelFeeding: {
                    id: "zone_003",
                    name: "Spyne Channel Hunting Grounds", 
                    center: { lat: 48.58, lng: -123.05 },
                    radius: 3.2,
                    depth_range: [15, 120],
                    
                    characteristics: {
                        prey_species: ["Chinook salmon", "Chum salmon", "Steelhead"],
                        peak_activity: "May-October",
                        tidal_dependency: "Very High - tide timing critical",
                        success_rate: 0.82,
                        
                        seasonal_patterns: {
                            spring: { activity: 0.6, explanation: "Early Chinook runs" },
                            summer: { activity: 0.9, explanation: "Multiple salmon species" },
                            fall: { activity: 0.7, explanation: "Late fall salmon runs" },
                            winter: { activity: 0.3, explanation: "Steelhead and winter fish" }
                        }
                    },
                    
                    transparency: "partial"
                }
            },
            
            data_sources: [
                "Orca Network sighting database",
                "NOAA fisheries salmon data", 
                "Washington State fish tracking",
                "Marine mammal research stations",
                "Citizen science observations"
            ],
            
            methodology: {
                transparent: [
                    "Historical sighting pattern analysis",
                    "Prey species distribution mapping",
                    "Seasonal migration route correlation"
                ],
                proprietary: [
                    "Behavioral success rate modeling",
                    "Predictive zone boundary algorithms",
                    "Multi-species interaction dynamics"
                ]
            }
        };
    }
    
    async loadFoodDensityData() {
        // Food web and prey density modeling
        this.foodDensityData = {
            source: "Multi-agency marine ecosystem monitoring",
            
            // Prey species tracking
            species: {
                chinook_salmon: {
                    scientific_name: "Oncorhynchus tshawytscha",
                    orca_preference: "Primary prey - 80% of diet",
                    
                    density_by_zone: {
                        "zone_001": { current: 145, unit: "fish/km²", confidence: 0.75 },
                        "zone_002": { current: 89, unit: "fish/km²", confidence: 0.68 },
                        "zone_003": { current: 167, unit: "fish/km²", confidence: 0.81 }
                    },
                    
                    temporal_patterns: {
                        daily: "Dawn and dusk activity peaks",
                        tidal: "Concentrated during tidal changes",
                        seasonal: "Peak June-August, minimal December-February",
                        annual: "Declining trend: -2.3% per year (2010-2024)"
                    },
                    
                    environmental_drivers: {
                        temperature: { optimal: "12-15°C", impact: "High" },
                        currents: { preference: "Moderate flow", impact: "Medium" },
                        depth: { range: "10-50m", impact: "Medium" },
                        salinity: { range: "28-32 ppt", impact: "Low" }
                    }
                },
                
                coho_salmon: {
                    scientific_name: "Oncorhynchus kisutch",
                    orca_preference: "Secondary prey - 15% of diet",
                    
                    density_by_zone: {
                        "zone_001": { current: 78, unit: "fish/km²", confidence: 0.62 },
                        "zone_002": { current: 52, unit: "fish/km²", confidence: 0.58 },
                        "zone_003": { current: 94, unit: "fish/km²", confidence: 0.71 }
                    },
                    
                    temporal_patterns: {
                        daily: "Midday feeding activity",
                        tidal: "Less tidal-dependent than Chinook",
                        seasonal: "Peak July-September",
                        annual: "Stable trend: +0.5% per year (2010-2024)"
                    }
                },
                
                pacific_herring: {
                    scientific_name: "Clupea pallasii",
                    orca_preference: "Occasional prey - 3% of diet",
                    
                    density_by_zone: {
                        "zone_001": { current: 1250, unit: "fish/km²", confidence: 0.45 },
                        "zone_002": { current: 2100, unit: "fish/km²", confidence: 0.52 },
                        "zone_003": { current: 890, unit: "fish/km²", confidence: 0.41 }
                    },
                    
                    temporal_patterns: {
                        daily: "School formation varies",
                        tidal: "Strong tidal influence on schooling",
                        seasonal: "Spawning aggregations February-April",
                        annual: "Highly variable: ±15% year-to-year"
                    }
                }
            },
            
            // Environmental factors affecting food density
            environmental_correlations: {
                sea_surface_temperature: {
                    impact: "High",
                    explanation: "Temperature affects salmon metabolism and distribution",
                    optimal_range: "12-15°C for Chinook feeding",
                    current_trend: "+0.8°C per decade"
                },
                
                chlorophyll_concentration: {
                    impact: "Medium",
                    explanation: "Indicates plankton productivity supporting food web",
                    measurement: "Satellite-derived chlorophyll-a",
                    seasonal_pattern: "Peak spring bloom, secondary fall bloom"
                },
                
                upwelling_intensity: {
                    impact: "High",
                    explanation: "Brings nutrients to surface, supporting entire food web",
                    measurement: "Coastal upwelling index",
                    climate_sensitivity: "Weakening with climate change"
                }
            }
        };
    }
    
    async loadHistoricalTrends() {
        // Historical ecosystem changes (2010-2024)
        this.historicalTrends = {
            time_range: "2010-2024",
            data_quality: "High for 2015-2024, moderate for 2010-2014",
            
            feeding_zone_changes: {
                "zone_001": {
                    area_change: -0.12, // 12% reduction
                    productivity_change: -0.18, // 18% decline
                    explanation: "Warming waters shifted salmon distribution northward",
                    
                    yearly_data: {
                        2010: { area: 1.0, productivity: 1.0, salmon_density: 165 },
                        2015: { area: 0.95, productivity: 0.89, salmon_density: 152 },
                        2020: { area: 0.91, productivity: 0.84, salmon_density: 148 },
                        2024: { area: 0.88, productivity: 0.82, salmon_density: 145 }
                    }
                },
                
                "zone_002": {
                    area_change: +0.08, // 8% expansion
                    productivity_change: -0.05, // 5% decline
                    explanation: "Zone expanded but prey density decreased",
                    
                    yearly_data: {
                        2010: { area: 1.0, productivity: 1.0, salmon_density: 98 },
                        2015: { area: 1.02, productivity: 0.97, salmon_density: 95 },
                        2020: { area: 1.05, productivity: 0.96, salmon_density: 92 },
                        2024: { area: 1.08, productivity: 0.95, salmon_density: 89 }
                    }
                },
                
                "zone_003": {
                    area_change: -0.05, // 5% reduction
                    productivity_change: +0.03, // 3% increase
                    explanation: "Smaller but more concentrated feeding area",
                    
                    yearly_data: {
                        2010: { area: 1.0, productivity: 1.0, salmon_density: 158 },
                        2015: { area: 0.98, productivity: 1.01, salmon_density: 161 },
                        2020: { area: 0.96, productivity: 1.02, salmon_density: 164 },
                        2024: { area: 0.95, productivity: 1.03, salmon_density: 167 }
                    }
                }
            },
            
            climate_drivers: {
                ocean_acidification: {
                    trend: "Increasing",
                    impact: "Affects shellfish and small fish populations",
                    rate: "pH declining 0.02 units per decade"
                },
                
                marine_heatwaves: {
                    trend: "More frequent and intense",
                    impact: "Disrupts food web, salmon distribution",
                    notable_events: ["2015-2016 'Blob'", "2019-2020 Northeast Pacific", "2021 Heat dome"]
                },
                
                sea_level_rise: {
                    trend: "Accelerating",
                    impact: "Affects nearshore habitats",
                    rate: "3.2 mm per year locally"
                }
            }
        };
    }
    
    async loadClimateProjections() {
        // Responsible 5-year ecosystem forecasting
        this.climateProjections = {
            forecast_period: "2025-2030",
            confidence_level: "Medium - based on established climate models",
            
            // Disclaimer about forecast limitations
            limitations: [
                "Marine ecosystems are complex and difficult to predict",
                "Climate change may cause unprecedented changes",
                "Projections assume current trends continue",
                "Local variations may differ from regional trends",
                "Forecast accuracy decreases with time horizon"
            ],
            
            projected_changes: {
                temperature: {
                    change: "+1.2°C by 2030",
                    confidence: "High",
                    source: "IPCC regional climate models",
                    impact_on_orcas: "Northern shift of feeding zones likely"
                },
                
                salmon_populations: {
                    chinook: {
                        trend: "Continued decline",
                        magnitude: "-15% to -25% by 2030",
                        confidence: "Medium",
                        drivers: ["Habitat loss", "Ocean conditions", "Hatchery impacts"]
                    },
                    
                    coho: {
                        trend: "Stable to slight increase",
                        magnitude: "-5% to +10% by 2030",
                        confidence: "Low",
                        drivers: ["More resilient to temperature", "Habitat restoration"]
                    }
                },
                
                feeding_zone_projections: {
                    "zone_001": {
                        area_change: -0.2, // 20% reduction projected
                        productivity_change: -0.3, // 30% decline projected
                        explanation: "Warming waters make southern zones less suitable",
                        confidence: "Medium"
                    },
                    
                    "zone_002": {
                        area_change: -0.1, // 10% reduction projected  
                        productivity_change: -0.15, // 15% decline projected
                        explanation: "Moderate impact from changing conditions",
                        confidence: "Medium"
                    },
                    
                    "zone_003": {
                        area_change: +0.05, // 5% increase projected
                        productivity_change: -0.1, // 10% decline projected
                        explanation: "May become more important as other zones decline",
                        confidence: "Low"
                    }
                }
            },
            
            // Adaptation scenarios for orcas
            behavioral_adaptations: {
                range_expansion: {
                    probability: "High",
                    description: "Orcas may need to travel further north for prey",
                    impact: "Reduced time in San Juan Islands"
                },
                
                prey_switching: {
                    probability: "Medium",
                    description: "Increased reliance on alternative prey species",
                    impact: "Different feeding behaviors and locations"
                },
                
                seasonal_shifts: {
                    probability: "High", 
                    description: "Peak feeding periods may shift earlier/later",
                    impact: "Changes in optimal whale watching times"
                }
            }
        };
    }
    
    // === VISUALIZATION METHODS ===
    
    generateFeedingZoneVisualization(year = this.currentYear) {
        // Create feeding zone visualization for specific year
        const zoneData = this.getFeedingZoneDataForYear(year);
        
        return {
            year: year,
            zones: Object.entries(this.feedingZones.zones).map(([key, zone]) => ({
                id: zone.id,
                name: zone.name,
                center: zone.center,
                radius: this.calculateZoneRadius(zone, year),
                productivity: this.calculateZoneProductivity(zone, year),
                prey_density: this.calculatePreyDensity(zone, year),
                confidence: this.calculateZoneConfidence(zone, year),
                
                visual_properties: {
                    opacity: Math.max(0.3, zone.characteristics.success_rate),
                    color: this.getZoneColor(zone.characteristics.success_rate),
                    border_style: zone.characteristics.tidal_dependency === "High" ? "dashed" : "solid"
                },
                
                tooltip_info: {
                    primary_prey: zone.characteristics.prey_species[0],
                    peak_season: zone.characteristics.peak_activity,
                    success_rate: `${Math.round(zone.characteristics.success_rate * 100)}%`,
                    tidal_dependency: zone.characteristics.tidal_dependency
                }
            }))
        };
    }
    
    generateBathymetryVisualization() {
        // Create bathymetry visualization with feeding zone context
        return {
            features: Object.entries(this.bathymetryData.features).map(([key, feature]) => ({
                name: feature.type,
                location: feature.location,
                depth: feature.depth,
                orca_relevance: feature.orcaRelevance,
                
                visual_properties: {
                    color: this.getDepthColor(feature.depth),
                    size: this.getFeatureSize(feature.significance),
                    icon: this.getFeatureIcon(feature.type)
                },
                
                explanation: feature.significance
            })),
            
            depth_legend: {
                "0-20m": { color: "#87CEEB", description: "Shallow - High prey activity" },
                "20-50m": { color: "#4682B4", description: "Medium - Salmon migration depth" },
                "50-100m": { color: "#191970", description: "Deep - Deeper foraging zones" },
                "100m+": { color: "#000080", description: "Very deep - Transit corridors" }
            }
        };
    }
    
    generateFoodDensityVisualization(year = this.currentYear, species = "chinook_salmon") {
        // Create food density heatmap
        const speciesData = this.foodDensityData.species[species];
        
        return {
            species: species,
            year: year,
            
            density_zones: Object.entries(speciesData.density_by_zone).map(([zoneId, density]) => ({
                zone_id: zoneId,
                zone_name: this.feedingZones.zones[zoneId.replace('zone_', 'zone_')].name,
                current_density: density.current,
                unit: density.unit,
                confidence: density.confidence,
                
                visual_properties: {
                    intensity: Math.min(1.0, density.current / 200), // Normalize to 0-1
                    color: this.getDensityColor(density.current, species),
                    opacity: density.confidence
                }
            })),
            
            species_info: {
                name: species.replace('_', ' '),
                scientific_name: speciesData.scientific_name,
                orca_preference: speciesData.orca_preference,
                temporal_pattern: speciesData.temporal_patterns.seasonal
            }
        };
    }
    
    generateTemporalAnalysis(startYear, endYear) {
        // Generate time-series analysis for feeding zones
        const years = [];
        for (let year = startYear; year <= endYear; year++) {
            years.push(year);
        }
        
        return {
            time_range: { start: startYear, end: endYear },
            
            zone_trends: Object.entries(this.feedingZones.zones).map(([key, zone]) => ({
                zone_id: zone.id,
                zone_name: zone.name,
                
                timeline: years.map(year => ({
                    year: year,
                    area: this.calculateZoneArea(zone, year),
                    productivity: this.calculateZoneProductivity(zone, year),
                    salmon_density: this.calculateSalmonDensity(zone, year),
                    orca_usage: this.calculateOrcaUsage(zone, year),
                    
                    // Annotation for significant events
                    events: this.getSignificantEvents(zone, year)
                }))
            })),
            
            environmental_timeline: years.map(year => ({
                year: year,
                sea_surface_temp: this.getSST(year),
                marine_heatwave: this.getHeatwaveStatus(year),
                salmon_run_strength: this.getSalmonRunStrength(year),
                climate_index: this.getClimateIndex(year)
            }))
        };
    }
    
    // === TEMPORAL CALCULATION METHODS ===
    
    calculateZoneRadius(zone, year) {
        const baseRadius = zone.radius;
        const historicalData = this.historicalTrends.feeding_zone_changes[zone.id];
        
        if (!historicalData) return baseRadius;
        
        // Linear interpolation for historical data
        if (year >= 2010 && year <= 2024) {
            const startData = historicalData.yearly_data[2010];
            const endData = historicalData.yearly_data[2024];
            const progress = (year - 2010) / (2024 - 2010);
            
            const areaMultiplier = startData.area + (endData.area - startData.area) * progress;
            return baseRadius * Math.sqrt(areaMultiplier); // Area to radius conversion
        }
        
        // Future projections
        if (year > 2024 && year <= 2030) {
            const projection = this.climateProjections.projected_changes.feeding_zone_projections[zone.id];
            if (projection) {
                const progress = (year - 2024) / (2030 - 2024);
                const areaChange = 1 + (projection.area_change * progress);
                return baseRadius * Math.sqrt(areaChange);
            }
        }
        
        return baseRadius;
    }
    
    calculateZoneProductivity(zone, year) {
        const baseProductivity = zone.characteristics.success_rate;
        const historicalData = this.historicalTrends.feeding_zone_changes[zone.id];
        
        if (!historicalData) return baseProductivity;
        
        // Historical productivity changes
        if (year >= 2010 && year <= 2024) {
            const startData = historicalData.yearly_data[2010];
            const endData = historicalData.yearly_data[2024];
            const progress = (year - 2010) / (2024 - 2010);
            
            const productivityMultiplier = startData.productivity + (endData.productivity - startData.productivity) * progress;
            return baseProductivity * productivityMultiplier;
        }
        
        // Future projections
        if (year > 2024 && year <= 2030) {
            const projection = this.climateProjections.projected_changes.feeding_zone_projections[zone.id];
            if (projection) {
                const progress = (year - 2024) / (2030 - 2024);
                const productivityChange = 1 + (projection.productivity_change * progress);
                return baseProductivity * productivityChange;
            }
        }
        
        return baseProductivity;
    }
    
    calculateSalmonDensity(zone, year) {
        const historicalData = this.historicalTrends.feeding_zone_changes[zone.id];
        
        if (!historicalData) return 100; // Default density
        
        // Historical density changes
        if (year >= 2010 && year <= 2024) {
            const startData = historicalData.yearly_data[2010];
            const endData = historicalData.yearly_data[2024];
            const progress = (year - 2010) / (2024 - 2010);
            
            return startData.salmon_density + (endData.salmon_density - startData.salmon_density) * progress;
        }
        
        // Future projections based on species trends
        if (year > 2024 && year <= 2030) {
            const chinookProjection = this.climateProjections.projected_changes.salmon_populations.chinook;
            const progress = (year - 2024) / (2030 - 2024);
            
            // Assuming 20% decline by 2030 (middle of range)
            const densityChange = 1 + (-0.2 * progress);
            return historicalData.yearly_data[2024].salmon_density * densityChange;
        }
        
        return historicalData.yearly_data[2024].salmon_density;
    }
    
    // === VISUAL STYLING METHODS ===
    
    getZoneColor(successRate) {
        // Color zones based on productivity
        if (successRate >= 0.8) return "#00FF00"; // Green - high productivity
        if (successRate >= 0.6) return "#FFFF00"; // Yellow - medium productivity  
        if (successRate >= 0.4) return "#FFA500"; // Orange - low productivity
        return "#FF0000"; // Red - very low productivity
    }
    
    getDepthColor(depth) {
        // Color by depth for bathymetry
        if (depth <= 20) return "#87CEEB"; // Light blue - shallow
        if (depth <= 50) return "#4682B4"; // Steel blue - medium
        if (depth <= 100) return "#191970"; // Midnight blue - deep
        return "#000080"; // Navy - very deep
    }
    
    getDensityColor(density, species) {
        // Color by food density
        const maxDensity = species === "chinook_salmon" ? 200 : 
                          species === "coho_salmon" ? 150 : 2500;
        
        const intensity = Math.min(1.0, density / maxDensity);
        
        // Heat map colors: blue (low) to red (high)
        const r = Math.round(255 * intensity);
        const g = Math.round(255 * (1 - intensity) * 0.5);
        const b = Math.round(255 * (1 - intensity));
        
        return `rgb(${r}, ${g}, ${b})`;
    }
    
    getFeatureIcon(type) {
        const iconMap = {
            "underwater ridge": "RIDGE",
            "tidal channel": "CHANNEL",
            "shipping channel": "SHIP",
            "tidal pass": "PASS"
        };
        return iconMap[type] || "FEATURE";
    }
    
    // === PUBLIC API METHODS ===
    
    async getFeedingZoneSnapshot(year = this.currentYear) {
        // Get complete feeding zone snapshot for a specific year
        return {
            year: year,
            feeding_zones: this.generateFeedingZoneVisualization(year),
            bathymetry: this.generateBathymetryVisualization(),
            food_density: this.generateFoodDensityVisualization(year),
            
            metadata: {
                data_quality: this.getDataQuality(year),
                confidence_level: this.getConfidenceLevel(year),
                limitations: this.getLimitations(year)
            }
        };
    }
    
    async getTemporalAnalysis(startYear = 2010, endYear = 2030) {
        // Get temporal analysis across years
        const analysis = this.generateTemporalAnalysis(startYear, endYear);
        
        return {
            ...analysis,
            
            // Responsible forecasting disclaimers
            forecast_disclaimers: {
                historical_period: "2010-2024: High confidence based on observations",
                current_period: "2024-2025: Medium confidence based on trends",
                forecast_period: "2025-2030: Lower confidence, scenario-based projections",
                
                limitations: [
                    "Marine ecosystems are complex and may not follow historical patterns",
                    "Climate change could cause unprecedented ecosystem shifts",
                    "Projections assume continuation of current trends",
                    "Actual outcomes may vary significantly from projections"
                ]
            }
        };
    }
    
    getDataQuality(year) {
        if (year >= 2015 && year <= 2024) return "High";
        if (year >= 2010 && year < 2015) return "Medium";
        if (year > 2024 && year <= 2027) return "Projection - Medium confidence";
        if (year > 2027) return "Projection - Low confidence";
        return "Unknown";
    }
    
    getConfidenceLevel(year) {
        if (year >= 2015 && year <= 2024) return 0.85;
        if (year >= 2010 && year < 2015) return 0.65;
        if (year > 2024 && year <= 2027) return 0.45;
        if (year > 2027) return 0.25;
        return 0.1;
    }
    
    getLimitations(year) {
        const baseLimitations = [
            "Feeding zone boundaries are approximate",
            "Prey density estimates have inherent uncertainty",
            "Orca behavior influenced by many unmeasured factors"
        ];
        
        if (year > 2024) {
            baseLimitations.push(
                "Future projections are scenarios, not predictions",
                "Climate change may cause unprecedented ecosystem changes",
                "Projections become less reliable further into the future"
            );
        }
        
        return baseLimitations;
    }
}

// Helper functions for significant events
function getSignificantEvents(zone, year) {
    const events = [];
    
    // Major marine heatwaves
    if (year >= 2015 && year <= 2016) {
        events.push({
            type: "marine_heatwave",
            description: "Pacific 'Blob' marine heatwave",
            impact: "Reduced salmon abundance, altered distribution"
        });
    }
    
    if (year === 2021) {
        events.push({
            type: "heat_dome",
            description: "Pacific Northwest heat dome",
            impact: "Massive salmon die-offs, ecosystem disruption"
        });
    }
    
    // Salmon population milestones
    if (year === 2018) {
        events.push({
            type: "salmon_decline",
            description: "Chinook salmon population reached historic low",
            impact: "Reduced feeding opportunities for Southern Residents"
        });
    }
    
    return events;
}

// Initialize the feeding zone dynamics engine
const feedingZoneDynamics = new FeedingZoneDynamicsEngine();

// Export for use in main application
window.feedingZoneDynamics = feedingZoneDynamics; 