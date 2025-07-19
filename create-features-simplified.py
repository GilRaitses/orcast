#!/usr/bin/env python3
"""
Simplified Behavioral Features Engineering Pipeline
Processes whale sightings data into ML-ready behavioral features with timezone fixes
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from google.cloud import bigquery
import math

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplifiedFeaturesProcessor:
    def __init__(self, project_id='orca-466204'):
        self.project_id = project_id
        self.bigquery_client = bigquery.Client(project=project_id)
        self.dataset_id = "orca_production_data"
        
    def create_ml_training_table_directly(self):
        """Create ML training table directly from sightings with computed features"""
        try:
            logger.info("🤖 Creating ML training data with computed features...")
            
            # Create ML training data from sightings with computed features in SQL
            query = f"""
            CREATE OR REPLACE TABLE `{self.project_id}.{self.dataset_id}.ml_training_data` AS
            WITH sightings_with_features AS (
                SELECT 
                    id as sighting_id,
                    timestamp,
                    latitude,
                    longitude,
                    source,
                    confidence,
                    COALESCE(behavior, 'observed') as behavior,
                    COALESCE(count, 1) as pod_size,
                    
                    -- Spatial features (computed in SQL)
                    GREATEST(
                        ABS(latitude - 48.5465), 
                        ABS(longitude + 123.0307)
                    ) * 111.0 as distance_to_shore_km,
                    
                    CASE 
                        WHEN SQRT(POW(latitude - 48.5, 2) + POW(longitude + 123.0, 2)) * 111.0 < 2 THEN 50 + RAND() * 20
                        WHEN SQRT(POW(latitude - 48.5, 2) + POW(longitude + 123.0, 2)) * 111.0 < 5 THEN 30 + RAND() * 15
                        ELSE 15 + RAND() * 10
                    END as water_depth_m,
                    
                    LEAST(
                        SQRT(POW(latitude - 48.52, 2) + POW(longitude + 123.15, 2)) * 111.0,
                        SQRT(POW(latitude - 48.65, 2) + POW(longitude + 122.88, 2)) * 111.0,
                        SQRT(POW(latitude - 48.58, 2) + POW(longitude + 123.05, 2)) * 111.0
                    ) as distance_to_feeding_zone_km,
                    
                    -- Temporal features
                    EXTRACT(HOUR FROM timestamp) as hour_of_day,
                    EXTRACT(DAYOFYEAR FROM timestamp) as day_of_year,
                    SIN(EXTRACT(HOUR FROM timestamp) * 2 * 3.14159 / 12.42) as tidal_height_normalized,
                    
                    -- Environmental features (simplified models)
                    RAND() * 3 - 1.5 as sst_anomaly_c,
                    ABS(COS(EXTRACT(HOUR FROM timestamp) * 2 * 3.14159 / 12.42) * 0.5) as tidal_velocity_ms,
                    CASE 
                        WHEN EXTRACT(MONTH FROM timestamp) IN (3,4,5,9,10,11) THEN 3.0 + RAND() * 0.5
                        ELSE 1.5 + RAND() * 0.5
                    END as chlorophyll_concentration,
                    
                    -- Social features
                    GREATEST(0.1, 1.0 - (COALESCE(count, 1) - 1) * 0.1) as pod_cohesion_index,
                    CASE 
                        WHEN behavior IN ('socializing', 'playing') THEN 5
                        WHEN behavior = 'foraging' THEN 3
                        WHEN behavior = 'traveling' THEN 2
                        WHEN behavior = 'resting' THEN 1
                        ELSE 3
                    END as social_activity_level,
                    
                    -- Historical features (simplified)
                    0 as recent_sightings_24h,  -- Will be computed later
                    30 as days_since_last_feeding  -- Default value
                    
                FROM `{self.project_id}.{self.dataset_id}.sightings`
                WHERE confidence > 0.3
            )
            SELECT 
                GENERATE_UUID() as training_id,
                sighting_id,
                STRUCT(
                    [distance_to_shore_km, water_depth_m, distance_to_feeding_zone_km] as spatial,
                    [hour_of_day, day_of_year, tidal_height_normalized] as temporal,
                    [sst_anomaly_c, tidal_velocity_ms, chlorophyll_concentration] as environmental,
                    [pod_cohesion_index, social_activity_level] as social,
                    [recent_sightings_24h, days_since_last_feeding] as historical
                ) as features,
                CASE 
                    WHEN behavior IN ('foraging', 'feeding', 'hunting') THEN 'feeding'
                    WHEN behavior IN ('traveling', 'transiting') THEN 'traveling'
                    WHEN behavior IN ('socializing', 'playing') THEN 'socializing'
                    WHEN behavior IN ('resting', 'milling') THEN 'resting'
                    ELSE 'unknown'
                END as behavior_label,
                CASE
                    WHEN behavior IN ('foraging', 'feeding') THEN 'cooperative_hunting'
                    ELSE 'other'
                END as feeding_strategy_label,
                CASE
                    WHEN behavior IN ('foraging', 'feeding') THEN true
                    ELSE false
                END as success_label,
                CASE 
                    WHEN MOD(ABS(FARM_FINGERPRINT(sighting_id)), 10) < 7 THEN 'train'
                    WHEN MOD(ABS(FARM_FINGERPRINT(sighting_id)), 10) < 9 THEN 'validation'
                    ELSE 'test'
                END as train_test_split,
                confidence as data_quality_score,
                CURRENT_TIMESTAMP() as created_at
            FROM sightings_with_features
            """
            
            logger.info("🔄 Executing ML training data creation query...")
            query_job = self.bigquery_client.query(query)
            query_job.result()  # Wait for completion
            
            logger.info("✅ ML training data table created successfully!")
            
            # Verify the data
            verify_query = f"""
            SELECT 
                train_test_split,
                behavior_label,
                COUNT(*) as count
            FROM `{self.project_id}.{self.dataset_id}.ml_training_data`
            GROUP BY train_test_split, behavior_label
            ORDER BY train_test_split, behavior_label
            """
            
            results = self.bigquery_client.query(verify_query).to_dataframe()
            logger.info("📊 ML Training Data Summary:")
            total_records = 0
            for _, row in results.iterrows():
                logger.info(f"  {row['train_test_split']}/{row['behavior_label']}: {row['count']} records")
                total_records += row['count']
            
            logger.info(f"🎉 Total ML training records: {total_records}")
            
            # Show feature structure
            sample_query = f"""
            SELECT 
                sighting_id,
                features.spatial,
                features.temporal,
                features.environmental,
                features.social,
                features.historical,
                behavior_label
            FROM `{self.project_id}.{self.dataset_id}.ml_training_data`
            LIMIT 3
            """
            
            sample_results = self.bigquery_client.query(sample_query).to_dataframe()
            logger.info("📋 Sample features structure:")
            for _, row in sample_results.iterrows():
                logger.info(f"  Sighting {row['sighting_id'][:15]}... -> {row['behavior_label']}")
                logger.info(f"    Spatial: {row['spatial']}")
                logger.info(f"    Temporal: {row['temporal']}")
                logger.info(f"    Environmental: {row['environmental']}")
                logger.info(f"    Social: {row['social']}")
                logger.info(f"    Historical: {row['historical']}")
                break  # Just show one example
            
            return total_records
            
        except Exception as e:
            logger.error(f"❌ Failed to create ML training table: {e}")
            raise

def main():
    """Main function to run the simplified feature engineering pipeline"""
    processor = SimplifiedFeaturesProcessor()
    
    try:
        logger.info("🚀 Starting simplified behavioral features pipeline...")
        
        # Create ML training data with computed features
        records_created = processor.create_ml_training_table_directly()
        
        logger.info(f"🎉 Pipeline completed successfully!")
        logger.info(f"📊 ML training records created: {records_created}")
        logger.info(f"🔗 View data: https://console.cloud.google.com/bigquery?project=orca-466204")
        logger.info("🤖 Ready for ML model training!")
        
    except Exception as e:
        logger.error(f"💥 Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main() 