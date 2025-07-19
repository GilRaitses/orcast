-- OrCast BigQuery Schema for Behavioral ML Pipeline
-- Comprehensive data warehouse for orca behavioral analysis and prediction

-- === CORE SIGHTING DATA ===

CREATE TABLE `orca-904de.orca_data.sightings` (
    sighting_id STRING NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    location GEOGRAPHY NOT NULL,
    latitude FLOAT64 NOT NULL,
    longitude FLOAT64 NOT NULL,
    
    -- Pod Information
    pod_id STRING,
    pod_size INT64,
    pod_composition STRUCT<
        adult_males INT64,
        adult_females INT64,
        juveniles INT64,
        calves INT64,
        unknown_age INT64
    >,
    
    -- Behavioral Classification (ML Target)
    behavior_primary STRING, -- 'feeding', 'traveling', 'socializing', 'resting', 'unknown'
    behavior_secondary STRING, -- 'cooperative_hunting', 'play', 'mating', 'teaching', etc.
    behavior_confidence FLOAT64, -- 0.0 to 1.0
    
    -- Feeding-specific data
    feeding_details STRUCT<
        prey_species STRING, -- 'chinook_salmon', 'coho_salmon', 'steelhead', 'herring'
        hunting_strategy STRING, -- 'carousel', 'beach_rubbing', 'deep_diving', 'surface_feeding'
        success_observed BOOLEAN,
        duration_minutes INT64,
        group_coordination BOOLEAN
    >,
    
    -- Environmental context at time of sighting
    environmental_context STRUCT<
        tidal_height FLOAT64,
        tidal_phase STRING, -- 'flood', 'ebb', 'slack_high', 'slack_low'
        tidal_strength STRING, -- 'weak', 'moderate', 'strong'
        
        weather_conditions STRUCT<
            cloud_cover_percent INT64,
            visibility_km FLOAT64,
            wind_speed_knots FLOAT64,
            wave_height_m FLOAT64,
            precipitation STRING
        >,
        
        marine_conditions STRUCT<
            sea_surface_temp_c FLOAT64,
            salinity_ppt FLOAT64,
            current_speed_knots FLOAT64,
            current_direction_degrees INT64,
            water_depth_m FLOAT64
        >,
        
        lunar_phase STRUCT<
            phase_name STRING, -- 'new', 'waxing_crescent', 'first_quarter', etc.
            illumination_percent FLOAT64,
            days_since_new FLOAT64
        >
    >,
    
    -- Data source and quality
    data_source STRING, -- 'citizen_science', 'research_vessel', 'whale_watch_tour', 'hydrophone'
    observer_expertise STRING, -- 'expert', 'experienced', 'novice', 'automated'
    data_quality_score FLOAT64, -- 0.0 to 1.0
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp)
CLUSTER BY pod_id, behavior_primary, data_source;

-- === BEHAVIORAL FEATURES FOR ML ===

CREATE TABLE `orca-904de.orca_data.behavioral_features` (
    feature_id STRING NOT NULL,
    sighting_id STRING NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    
    -- Spatial features
    distance_to_shore_km FLOAT64,
    water_depth_m FLOAT64,
    distance_to_feeding_zone_km FLOAT64,
    bathymetry_gradient FLOAT64,
    
    -- Temporal features
    hour_of_day INT64,
    day_of_week INT64,
    day_of_year INT64,
    season STRING, -- 'spring', 'summer', 'fall', 'winter'
    
    -- Environmental features
    tidal_height_normalized FLOAT64, -- -1 to 1
    tidal_velocity_ms FLOAT64,
    sst_anomaly_c FLOAT64, -- deviation from seasonal mean
    chlorophyll_concentration FLOAT64,
    
    -- Prey availability features
    salmon_abundance_index FLOAT64,
    herring_abundance_index FLOAT64,
    prey_diversity_index FLOAT64,
    
    -- Historical context features
    recent_sightings_24h INT64,
    recent_feeding_events_24h INT64,
    days_since_last_feeding INT64,
    
    -- Social features
    pod_cohesion_index FLOAT64, -- 0.0 to 1.0
    inter_pod_distance_m FLOAT64,
    social_activity_level INT64, -- 1 to 5
    
    -- Behavioral sequence features
    previous_behavior STRING,
    behavior_transition_probability FLOAT64,
    time_since_behavior_change_minutes INT64,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp)
CLUSTER BY sighting_id, hour_of_day, season;

-- === PREY DENSITY DATA ===

CREATE TABLE `orca-904de.orca_data.prey_density` (
    measurement_id STRING NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    location GEOGRAPHY NOT NULL,
    
    -- Prey species densities
    chinook_salmon STRUCT<
        density_per_km2 FLOAT64,
        biomass_kg_per_km2 FLOAT64,
        avg_size_cm FLOAT64,
        age_distribution ARRAY<STRUCT<age_years INT64, proportion FLOAT64>>
    >,
    
    coho_salmon STRUCT<
        density_per_km2 FLOAT64,
        biomass_kg_per_km2 FLOAT64,
        avg_size_cm FLOAT64,
        age_distribution ARRAY<STRUCT<age_years INT64, proportion FLOAT64>>
    >,
    
    pacific_herring STRUCT<
        density_per_km2 FLOAT64,
        biomass_kg_per_km2 FLOAT64,
        school_size_avg INT64,
        spawning_activity BOOLEAN
    >,
    
    -- Environmental context
    water_temperature_c FLOAT64,
    salinity_ppt FLOAT64,
    dissolved_oxygen_ppm FLOAT64,
    
    -- Data source
    measurement_method STRING, -- 'acoustic_survey', 'net_sampling', 'visual_count', 'hydroacoustic'
    data_confidence FLOAT64,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp)
CLUSTER BY measurement_method;

-- === FEEDING ZONE ANALYSIS ===

CREATE TABLE `orca-904de.orca_data.feeding_zones` (
    zone_id STRING NOT NULL,
    zone_name STRING NOT NULL,
    geometry GEOGRAPHY NOT NULL,
    
    -- Zone characteristics
    avg_depth_m FLOAT64,
    depth_range STRUCT<min_m FLOAT64, max_m FLOAT64>,
    primary_prey_species STRING,
    
    -- Temporal analysis
    analysis_date DATE NOT NULL,
    
    -- Zone productivity metrics
    feeding_events_count INT64,
    success_rate FLOAT64,
    avg_feeding_duration_minutes FLOAT64,
    
    -- Environmental preferences
    preferred_tidal_phase STRING,
    preferred_tidal_strength STRING,
    optimal_conditions STRUCT<
        temperature_range STRUCT<min_c FLOAT64, max_c FLOAT64>,
        salinity_range STRUCT<min_ppt FLOAT64, max_ppt FLOAT64>,
        current_speed_range STRUCT<min_knots FLOAT64, max_knots FLOAT64>
    >,
    
    -- Historical trends
    productivity_trend FLOAT64, -- change per year
    area_change_trend FLOAT64, -- change per year
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY analysis_date
CLUSTER BY zone_id, primary_prey_species;

-- === ML TRAINING DATA ===

CREATE TABLE `orca-904de.orca_data.ml_training_data` (
    training_id STRING NOT NULL,
    sighting_id STRING NOT NULL,
    
    -- Features (input)
    features STRUCT<
        spatial ARRAY<FLOAT64>,
        temporal ARRAY<FLOAT64>,
        environmental ARRAY<FLOAT64>,
        social ARRAY<FLOAT64>,
        historical ARRAY<FLOAT64>
    >,
    
    -- Labels (output)
    behavior_label STRING,
    feeding_strategy_label STRING,
    success_label BOOLEAN,
    
    -- Training metadata
    train_test_split STRING, -- 'train', 'validation', 'test'
    data_quality_score FLOAT64,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
CLUSTER BY behavior_label, train_test_split;

-- === BEHAVIORAL PREDICTIONS ===

CREATE TABLE `orca-904de.orca_data.behavioral_predictions` (
    prediction_id STRING NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    location GEOGRAPHY NOT NULL,
    
    -- Prediction results
    behavior_predictions ARRAY<STRUCT<
        behavior STRING,
        probability FLOAT64,
        confidence FLOAT64
    >>,
    
    feeding_strategy_predictions ARRAY<STRUCT<
        strategy STRING,
        probability FLOAT64,
        environmental_suitability FLOAT64
    >>,
    
    success_probability FLOAT64,
    
    -- Model metadata
    model_version STRING,
    model_confidence FLOAT64,
    
    -- Explanation features
    feature_importance ARRAY<STRUCT<
        feature_name STRING,
        importance_score FLOAT64,
        explanation STRING
    >>,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp)
CLUSTER BY model_version;

-- === VIEWS FOR ANALYSIS ===

-- Behavioral patterns view
CREATE VIEW `orca-904de.orca_data.behavioral_patterns` AS
SELECT 
    DATE(timestamp) as date,
    behavior_primary,
    COUNT(*) as sighting_count,
    AVG(environmental_context.tidal_height) as avg_tidal_height,
    AVG(environmental_context.marine_conditions.sea_surface_temp_c) as avg_sst,
    AVG(pod_size) as avg_pod_size,
    AVG(behavior_confidence) as avg_confidence
FROM `orca-904de.orca_data.sightings`
WHERE behavior_primary IS NOT NULL
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;

-- Feeding success analysis view
CREATE VIEW `orca-904de.orca_data.feeding_success_analysis` AS
SELECT 
    DATE(timestamp) as date,
    feeding_details.prey_species,
    feeding_details.hunting_strategy,
    COUNT(*) as feeding_events,
    AVG(CASE WHEN feeding_details.success_observed THEN 1.0 ELSE 0.0 END) as success_rate,
    AVG(feeding_details.duration_minutes) as avg_duration,
    AVG(environmental_context.tidal_height) as avg_tidal_height
FROM `orca-904de.orca_data.sightings`
WHERE behavior_primary = 'feeding'
    AND feeding_details.prey_species IS NOT NULL
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 4 DESC;

-- Environmental correlation view
CREATE VIEW `orca-904de.orca_data.environmental_correlations` AS
SELECT 
    behavior_primary,
    AVG(environmental_context.tidal_height) as avg_tidal_height,
    AVG(environmental_context.marine_conditions.sea_surface_temp_c) as avg_sst,
    AVG(environmental_context.weather_conditions.wind_speed_knots) as avg_wind_speed,
    AVG(environmental_context.lunar_phase.illumination_percent) as avg_lunar_illumination,
    COUNT(*) as sample_size
FROM `orca-904de.orca_data.sightings`
WHERE behavior_primary IS NOT NULL
GROUP BY 1
ORDER BY 6 DESC;

-- === STORED PROCEDURES FOR ML PIPELINE ===

-- Procedure to prepare training data
CREATE OR REPLACE PROCEDURE `orca-904de.orca_data.prepare_training_data`(
    start_date DATE,
    end_date DATE
)
BEGIN
    -- Clean and prepare features
    DELETE FROM `orca-904de.orca_data.ml_training_data` 
    WHERE DATE(created_at) BETWEEN start_date AND end_date;
    
    -- Insert prepared training data
    INSERT INTO `orca-904de.orca_data.ml_training_data`
    SELECT 
        GENERATE_UUID() as training_id,
        s.sighting_id,
        STRUCT(
            [bf.distance_to_shore_km, bf.water_depth_m, bf.distance_to_feeding_zone_km] as spatial,
            [bf.hour_of_day, bf.day_of_year, bf.tidal_height_normalized] as temporal,
            [bf.sst_anomaly_c, bf.tidal_velocity_ms, bf.chlorophyll_concentration] as environmental,
            [bf.pod_cohesion_index, bf.social_activity_level] as social,
            [bf.recent_sightings_24h, bf.days_since_last_feeding] as historical
        ) as features,
        s.behavior_primary as behavior_label,
        s.feeding_details.hunting_strategy as feeding_strategy_label,
        s.feeding_details.success_observed as success_label,
        CASE 
            WHEN MOD(ABS(FARM_FINGERPRINT(s.sighting_id)), 10) < 7 THEN 'train'
            WHEN MOD(ABS(FARM_FINGERPRINT(s.sighting_id)), 10) < 9 THEN 'validation'
            ELSE 'test'
        END as train_test_split,
        s.data_quality_score,
        CURRENT_TIMESTAMP() as created_at
    FROM `orca-904de.orca_data.sightings` s
    JOIN `orca-904de.orca_data.behavioral_features` bf
        ON s.sighting_id = bf.sighting_id
    WHERE DATE(s.timestamp) BETWEEN start_date AND end_date
        AND s.behavior_primary IS NOT NULL
        AND s.data_quality_score > 0.7;
END;

-- Procedure to update feeding zone analysis
CREATE OR REPLACE PROCEDURE `orca-904de.orca_data.update_feeding_zone_analysis`(
    analysis_date DATE
)
BEGIN
    -- Update feeding zone productivity metrics
    MERGE `orca-904de.orca_data.feeding_zones` AS target
    USING (
        SELECT 
            fz.zone_id,
            COUNT(*) as feeding_events_count,
            AVG(CASE WHEN s.feeding_details.success_observed THEN 1.0 ELSE 0.0 END) as success_rate,
            AVG(s.feeding_details.duration_minutes) as avg_feeding_duration_minutes
        FROM `orca-904de.orca_data.feeding_zones` fz
        JOIN `orca-904de.orca_data.sightings` s
            ON ST_CONTAINS(fz.geometry, s.location)
        WHERE DATE(s.timestamp) = analysis_date
            AND s.behavior_primary = 'feeding'
        GROUP BY fz.zone_id
    ) AS source
    ON target.zone_id = source.zone_id AND target.analysis_date = analysis_date
    WHEN MATCHED THEN
        UPDATE SET 
            feeding_events_count = source.feeding_events_count,
            success_rate = source.success_rate,
            avg_feeding_duration_minutes = source.avg_feeding_duration_minutes
    WHEN NOT MATCHED THEN
        INSERT (zone_id, analysis_date, feeding_events_count, success_rate, avg_feeding_duration_minutes)
        VALUES (source.zone_id, analysis_date, source.feeding_events_count, source.success_rate, source.avg_feeding_duration_minutes);
END; 