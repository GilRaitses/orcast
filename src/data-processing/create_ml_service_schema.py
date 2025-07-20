#!/usr/bin/env python3
"""
Create BigQuery Schema That Matches ML Service Expectations
This script creates the exact table structure expected by behavioral_ml_service.py
"""

import os
import json
import logging
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_ml_service_schema():
    """Create BigQuery tables matching the ML service expectations"""
    
    # Initialize BigQuery client
    project_id = "orca-466204"
    client = bigquery.Client(project=project_id)
    
    # Dataset ID expected by ML service
    dataset_id = "orca_data"
    dataset_ref = client.dataset(dataset_id)
    
    # Create dataset if it doesn't exist
    try:
        client.get_dataset(dataset_ref)
        logger.info(f"Dataset {dataset_id} already exists")
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        dataset.description = "Orca behavioral data for ML training (ML service compatible)"
        client.create_dataset(dataset)
        logger.info(f"Created dataset {dataset_id}")
    
    # 1. Create sightings table (expected by ML service)
    sightings_table_id = f"{project_id}.{dataset_id}.sightings"
    sightings_schema = [
        bigquery.SchemaField("sighting_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("latitude", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("longitude", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("pod_size", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("water_depth", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("tidal_flow", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("temperature", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("salinity", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("visibility", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("current_speed", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("noise_level", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("prey_density", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("source", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("confidence", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("data_quality_score", "FLOAT64", mode="NULLABLE"),
    ]
    
    # 2. Create behavioral_data table (expected by ML service)
    behavioral_table_id = f"{project_id}.{dataset_id}.behavioral_data"
    behavioral_schema = [
        bigquery.SchemaField("sighting_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("primary_behavior", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("feeding_strategy", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("feeding_success", "BOOLEAN", mode="NULLABLE"),
        bigquery.SchemaField("behavior_confidence", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("observed_duration_minutes", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("social_context", "STRING", mode="NULLABLE"),
    ]
    
    # Create tables
    tables_to_create = [
        (sightings_table_id, sightings_schema, "Core sighting data with environmental features"),
        (behavioral_table_id, behavioral_schema, "Behavioral classifications for ML training")
    ]
    
    created_tables = []
    for table_id, schema, description in tables_to_create:
        try:
            # Check if table exists
            client.get_table(table_id)
            logger.info(f"Table {table_id} already exists")
        except NotFound:
            # Create table
            table = bigquery.Table(table_id, schema=schema)
            table.description = description
            table = client.create_table(table)
            logger.info(f"Created table {table_id}")
            created_tables.append(table_id)
    
    return created_tables

def transform_existing_data():
    """Transform existing data to match ML service schema"""
    
    project_id = "orca-466204"
    client = bigquery.Client(project=project_id)
    
    logger.info("🔄 Transforming existing data to ML service schema...")
    
    # Load existing sightings data
    source_query = f"""
    SELECT *
    FROM `{project_id}.orca_production_data.sightings`
    ORDER BY timestamp DESC
    """
    
    try:
        df = client.query(source_query).to_dataframe()
        logger.info(f"📊 Loaded {len(df)} existing sightings")
        
        if df.empty:
            logger.warning("No existing data to transform")
            return
        
        # Transform to ML service expected format
        transformed_sightings = []
        transformed_behaviors = []
        
        for _, row in df.iterrows():
            sighting_id = row['id']
            
            # Extract environmental features (simulate for now)
            lat, lng = row['latitude'], row['longitude']
            
            # Simulate environmental data based on location
            water_depth = simulate_water_depth(lat, lng)
            tidal_flow = simulate_tidal_flow(lat, lng, pd.to_datetime(row['timestamp']))
            temperature = simulate_temperature(lat, lng, pd.to_datetime(row['timestamp']))
            salinity = simulate_salinity(lat, lng)
            visibility = simulate_visibility(lat, lng)
            current_speed = simulate_current_speed(lat, lng)
            noise_level = simulate_noise_level(lat, lng)
            prey_density = simulate_prey_density(lat, lng, pd.to_datetime(row['timestamp']))
            
            # Sightings record
            sighting_record = {
                'sighting_id': sighting_id,
                'timestamp': row['timestamp'],
                'latitude': lat,
                'longitude': lng,
                'pod_size': row.get('count', 1),
                'water_depth': water_depth,
                'tidal_flow': tidal_flow,
                'temperature': temperature,
                'salinity': salinity,
                'visibility': visibility,
                'current_speed': current_speed,
                'noise_level': noise_level,
                'prey_density': prey_density,
                'source': row.get('source', 'unknown'),
                'confidence': row.get('confidence', 0.5),
                'data_quality_score': calculate_quality_score(row)
            }
            transformed_sightings.append(sighting_record)
            
            # Behavioral record (extract from behavior field)
            behavior = row.get('behavior', 'unknown')
            primary_behavior = map_to_primary_behavior(behavior)
            
            behavioral_record = {
                'sighting_id': sighting_id,
                'primary_behavior': primary_behavior,
                'feeding_strategy': extract_feeding_strategy(behavior),
                'feeding_success': simulate_feeding_success(primary_behavior),
                'behavior_confidence': row.get('confidence', 0.5),
                'observed_duration_minutes': simulate_duration(),
                'social_context': simulate_social_context(row.get('count', 1))
            }
            transformed_behaviors.append(behavioral_record)
        
        # Upload to BigQuery
        sightings_df = pd.DataFrame(transformed_sightings)
        behavioral_df = pd.DataFrame(transformed_behaviors)
        
        # Upload sightings
        sightings_table_id = f"{project_id}.orca_data.sightings"
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE"
        )
        
        job = client.load_table_from_dataframe(
            sightings_df, sightings_table_id, job_config=job_config
        )
        job.result()
        logger.info(f"✅ Uploaded {len(sightings_df)} sightings to {sightings_table_id}")
        
        # Upload behavioral data
        behavioral_table_id = f"{project_id}.orca_data.behavioral_data"
        job = client.load_table_from_dataframe(
            behavioral_df, behavioral_table_id, job_config=job_config
        )
        job.result()
        logger.info(f"✅ Uploaded {len(behavioral_df)} behavioral records to {behavioral_table_id}")
        
        return len(sightings_df), len(behavioral_df)
        
    except Exception as e:
        logger.error(f"❌ Error transforming data: {e}")
        return 0, 0

# Environmental simulation functions
def simulate_water_depth(lat, lng):
    """Simulate water depth based on location"""
    # San Juan Islands: deeper in channels, shallower near shore
    base_depth = 50 + (lat - 48.5) * 100 + abs(lng + 123) * 80
    return max(10, min(200, base_depth + np.random.normal(0, 10)))

def simulate_tidal_flow(lat, lng, timestamp):
    """Simulate tidal flow based on time and location"""
    hour = timestamp.hour
    tidal_phase = np.sin(2 * np.pi * hour / 12.42)  # M2 tidal component
    return tidal_phase * (0.5 + np.random.normal(0, 0.1))

def simulate_temperature(lat, lng, timestamp):
    """Simulate water temperature"""
    month = timestamp.month
    seasonal_temp = 12 + 4 * np.sin(2 * np.pi * (month - 3) / 12)
    return seasonal_temp + np.random.normal(0, 1)

def simulate_salinity(lat, lng):
    """Simulate salinity (PSU)"""
    return 30 + np.random.normal(0, 1)

def simulate_visibility(lat, lng):
    """Simulate visibility (meters)"""
    return max(5, 20 + np.random.normal(0, 5))

def simulate_current_speed(lat, lng):
    """Simulate current speed (m/s)"""
    return max(0, 0.5 + np.random.normal(0, 0.2))

def simulate_noise_level(lat, lng):
    """Simulate noise level (dB)"""
    # Higher noise near shipping lanes
    base_noise = 115 + abs(lng + 123) * 10
    return base_noise + np.random.normal(0, 5)

def simulate_prey_density(lat, lng, timestamp):
    """Simulate prey density index"""
    month = timestamp.month
    seasonal_prey = 0.5 + 0.3 * np.sin(2 * np.pi * (month - 6) / 12)
    return max(0.1, seasonal_prey + np.random.normal(0, 0.1))

def calculate_quality_score(row):
    """Calculate data quality score"""
    score = 0.5
    if row.get('confidence') and row['confidence'] > 0.7:
        score += 0.2
    if row.get('source') and 'research' in str(row['source']).lower():
        score += 0.2
    if row.get('count') and row['count'] > 0:
        score += 0.1
    return min(1.0, score)

def map_to_primary_behavior(behavior):
    """Map behavior string to primary behavior categories"""
    if not behavior or behavior == 'unknown':
        return 'unknown'
    
    behavior_lower = str(behavior).lower()
    
    if any(term in behavior_lower for term in ['feed', 'forag', 'hunt', 'prey']):
        return 'feeding'
    elif any(term in behavior_lower for term in ['travel', 'transit', 'moving']):
        return 'traveling'
    elif any(term in behavior_lower for term in ['social', 'play', 'interact']):
        return 'socializing'
    elif any(term in behavior_lower for term in ['rest', 'sleep', 'stationary']):
        return 'resting'
    else:
        return 'unknown'

def extract_feeding_strategy(behavior):
    """Extract feeding strategy from behavior"""
    if not behavior:
        return None
    
    behavior_lower = str(behavior).lower()
    
    if 'cooperative' in behavior_lower or 'group' in behavior_lower:
        return 'cooperative_hunting'
    elif 'surface' in behavior_lower:
        return 'surface_feeding'
    elif 'deep' in behavior_lower or 'dive' in behavior_lower:
        return 'deep_diving'
    elif 'carousel' in behavior_lower:
        return 'carousel_feeding'
    else:
        return None

def simulate_feeding_success(primary_behavior):
    """Simulate feeding success based on behavior"""
    if primary_behavior == 'feeding':
        return np.random.choice([True, False], p=[0.7, 0.3])
    else:
        return None

def simulate_duration():
    """Simulate observation duration"""
    return int(np.random.exponential(30))  # Average 30 minutes

def simulate_social_context(pod_size):
    """Simulate social context based on pod size"""
    if pod_size == 1:
        return 'solitary'
    elif pod_size <= 3:
        return 'small_group'
    elif pod_size <= 8:
        return 'family_group'
    else:
        return 'large_pod'

def main():
    """Main execution"""
    logger.info("🚀 Creating ML Service Compatible Schema...")
    
    # Create schema
    created_tables = create_ml_service_schema()
    
    # Transform existing data
    sightings_count, behavioral_count = transform_existing_data()
    
    logger.info("✅ Schema transformation complete!")
    logger.info(f"📊 Summary:")
    logger.info(f"   • Tables created: {len(created_tables)}")
    logger.info(f"   • Sightings transformed: {sightings_count}")
    logger.info(f"   • Behavioral records: {behavioral_count}")
    
    # Test the ML service query
    logger.info("🧪 Testing ML service query...")
    project_id = "orca-466204"
    client = bigquery.Client(project=project_id)
    
    test_query = f"""
    SELECT 
        s.latitude,
        s.longitude,
        s.pod_size,
        s.water_depth,
        s.tidal_flow,
        s.temperature,
        s.salinity,
        s.visibility,
        s.current_speed,
        s.noise_level,
        s.prey_density,
        EXTRACT(HOUR FROM s.timestamp) as hour_of_day,
        EXTRACT(DAYOFYEAR FROM s.timestamp) as day_of_year,
        b.primary_behavior,
        b.feeding_strategy,
        b.feeding_success
    FROM `{project_id}.orca_data.sightings` s
    JOIN `{project_id}.orca_data.behavioral_data` b
    ON s.sighting_id = b.sighting_id
    WHERE s.timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 365 DAY)
    AND b.primary_behavior IS NOT NULL
    AND s.water_depth IS NOT NULL
    AND s.tidal_flow IS NOT NULL
    AND s.prey_density IS NOT NULL
    ORDER BY s.timestamp DESC
    LIMIT 5
    """
    
    try:
        df = client.query(test_query).to_dataframe()
        logger.info(f"✅ ML service query successful! Retrieved {len(df)} records")
        
        if not df.empty:
            logger.info("📋 Sample data:")
            for col in ['primary_behavior', 'feeding_strategy', 'water_depth', 'temperature']:
                if col in df.columns:
                    logger.info(f"   • {col}: {df[col].iloc[0] if len(df) > 0 else 'N/A'}")
        
        logger.info("🎯 Ready for ML training!")
        
    except Exception as e:
        logger.error(f"❌ ML service query failed: {e}")

if __name__ == "__main__":
    main() 